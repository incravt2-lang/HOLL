"""City contracts shared by the heroes of one Telegram group."""
import city
import random
import time

from world import category, SEAM_SHIELD, encounter_area, CLASS_PIECES, HUMAN_IDS, faction, HUNT_IDS, EXTRA_HUNT_IDS, trade_value, LIMITS, RARITY, SCRAPS, ZONES, gear_names, gear_stat, level, monster, rank, strength, tier_name

SHIFT = 6 * 3600
KINDS = {
    "hunt": "Дозор просит расчистить дорогу для хлебных подвод.",
    "supply": "Кладовщик примет образцы по счёту. Пустой мешок в ведомость не впишешь.",
    "raid": "За стеной пропал разъезд. Собери людей и проверь последний зал.",
}

def rotation(state, now):
    shift = int(now) // SHIFT
    board = state.get("contracts")
    if board and board["shift"] == shift:
        return board
    heroes = state["heroes"]
    average = round(sum(level(h) for h in heroes.values()) / len(heroes))
    rng = random.Random(f"{shift}:{','.join(sorted(heroes))}")
    pool = []
    for z, zone in enumerate(ZONES):
        for n in (*range(9),*EXTRA_HUNT_IDS):
            lv = rank(z,n)
            first = n if n in HUNT_IDS else 3 + 3*((n-3)//3)
            if lv > average+5 or rank(z,first) < average-5:
                continue
            for kind in ("hunt","supply"):
                pool.append((kind,z,n,rng.randint(2,4)))
            if n in (5,8):
                pool.append(("raid",z,n,1))
    rng.shuffle(pool)
    count = min(len(pool),rng.randint(5,10))
    chosen = []
    for kind in KINDS:
        match = next((q for q in pool if q[0]==kind and q[2] in HUMAN_IDS),None)
        if match is None: match = next((q for q in pool if q[0]==kind),None)
        if match:
            chosen.append(match)
            pool.remove(match)
    chosen.extend(pool[:count-len(chosen)])
    board = {"shift":shift,"level":average,"jobs":[dict(kind=t,z=z,n=n,need=v,progress=0,owner=None,done=False)
                                                  for t,z,n,v in chosen]}
    state["contracts"] = board
    return board

def record_win(state,party,z,n,mode):
    board = state.get("contracts")
    if not board or board["shift"] != int(time.time())//SHIFT:
        return
    for job in board["jobs"]:
        if job["done"] or job["owner"] not in party or (job["z"],job["n"])!=(z,n):
            continue
        if job["kind"]=="hunt" or (job["kind"]=="raid" and mode=="raid"):
            job["progress"] = min(job["need"],job["progress"]+1)

def details(q):
    z,n,kind = q["z"],q["n"],q["kind"]
    if kind=="raid":
        label = "Зачистить · "+ZONES[z][2][(n-3)//3][0]
    elif kind=="hunt":
        label = f"Устранить · {monster(z,n)} ×{q['need']}"
    else:
        label = f"Доставить · {SCRAPS[z][n]} ×{q['need']}"
    hard = kind=="raid" or n not in HUNT_IDS
    xp = (28+rank(z,n)*3)*(3 if kind=="raid" else 2 if hard else 1)
    return label,xp,(15 if kind=="raid" else 7 if hard else 2)

def progress(q,h):
    if q["kind"]=="supply":
        return min(q["need"],h["junk"].get(f"{q['z']}.{q['n']}",0))
    return q["progress"]

def payout(q,h,active=None):
    z=q["z"]
    _,xp,rare=details(q)
    xp=min(city.earned(xp,active,h),LIMITS[-1]-h["xp"])
    h["xp"]+=xp
    h["peak"]=max(level(h),h.get("peak",1))
    tier=int(random.randrange(100)<rare)
    names=gear_names(z)
    pool=[k for k in range(len(names)) if names[k]!=SEAM_SHIELD and RARITY[z,k]==tier and ((z,k) not in CLASS_PIECES or CLASS_PIECES[z,k][2]==h["class"])]
    k=random.choice([k for k in pool if names[k] not in h["items"]] or pool)
    item=names[k]
    if item in h["items"]:
        coins=4*trade_value(z,k)
        h["wallet"]+=coins
        award=f"{item} уже есть · +{coins} мед."
    else:
        h["items"][item]=[gear_stat(z,k),strength(z,k)]
        award=f"[{category(z,k)}] "+tier_name(z,k)+" · "+item
    return f"Комендант поставил печать. +{xp} опыта · {award}"

def desk(state,uid,args):
    now=time.time()
    board=rotation(state,now)
    shift=board["shift"]
    jobs=board["jobs"]
    h=state["heroes"][uid]
    def button(label,action):
        return [{"text":label,"callback_data":action}]
    home=button("К доске","orders")
    note=""
    if len(args)==3 and args[0]==str(shift) and args[1].isdigit() and int(args[1])<len(jobs):
        i=int(args[1])
        q=jobs[i]
        prefix=f"orders:{shift}:{i}:"
        act=args[2]
        if not q["done"]:
            if act=="take" and q["owner"] is None:
                q["owner"]=uid
            elif act=="leave" and q["owner"]==uid:
                q.update(owner=None,progress=0)
            elif act=="turn" and q["owner"]==uid and progress(q,h)>=q["need"]:
                if q["kind"]=="supply":
                    key=f"{q['z']}.{q['n']}"
                    h["junk"][key]-=q["need"]
                    if not h["junk"][key]: del h["junk"][key]
                note=payout(q,h,city.buff(state))
                q["done"]=True
            if not q["done"]:
                label,xp,rare=details(q)
                xp=city.earned(xp,city.buff(state),h)
                z,n=q["z"],q["n"]
                site=encounter_area(z,n)
                if n not in HUNT_IDS: site+=" · "+ZONES[z][2][(n-3)//3][0]
                orders={"robber":"Обозчики опознали налётчиков. Возврати дорогу подводам.",
                        "oath":"Старый караульный список сходится. Беглец снова берёт пошлину оружием.",
                        "cult":"У амбара опять собирают десятину в чашу без дна. Разберись со сборщиками.",
                        "changed":"В списке дворов он ещё числится живым. Дозор подтверждает следы Плети."}
                text=[label+"\n",orders.get(faction(z,n),KINDS[q["kind"]]),"\nГде искать\n"+site+f" · ур. {rank(z,n)}"]
                if q["kind"]=="supply": text.append("Источник: "+monster(z,n))
                text.append(f"\nНаграда\n{xp} опыта и вещь · редкая {rare}%, иначе обычная.")
                rows=[]
                if q["owner"] is None: rows.append(button("Взять поручение",prefix+"take"))
                elif q["owner"]==uid:
                    p=progress(q,h)
                    text.append(f"Выполнено: {p}/{q['need']}")
                    if p==q["need"]: rows.append(button("Сдать коменданту",prefix+"turn"))
                    rows.append(button("Вернуть поручение на доску",prefix+"leave"))
                else: text.append("Исполнитель: "+state["heroes"][q["owner"]]["name"])
                return "\n".join(text),rows+[home]
        note=note or "Поручение уже закрыто."
    minutes=max(1,int(((shift+1)*SHIFT-now+59)//60))
    text=["Комендант Гусзка · караульная книга",
          "«Пока амбары полны, ворота держатся. Бери запись — и распишись по возвращении».",
          f"Средний уровень: {board['level']} · до смены доски {minutes//60} ч {minutes%60} мин."]
    if note: text.append(note)
    rows=[]
    for i,q in enumerate(jobs):
        if q["done"]: continue
        mark="◆ " if q["owner"]==uid else "🔒 " if q["owner"] else ""
        rows.append(button(mark+details(q)[0],f"orders:{shift}:{i}:view"))
    if not rows: text.append("Все записи погашены. Новые прибьют со сменой караула.")
    project=city.current(state)
    rows.insert(0,button("Общее дело · "+city.PROJECTS[project["kind"]][0],"city"))
    return "\n\n".join(text),rows+[button("К торговой площади","nav:town")]
