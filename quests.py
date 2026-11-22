"""City contracts shared by the heroes of one Telegram group."""
import city
from progression import contract_xp
import random
import time

from world import ORIGIN,suitable
from world import item_slot_label, category, SEAM_SHIELD, encounter_area, CLASS_PIECES, HUMAN_IDS, faction, HUNT_IDS, EXTRA_HUNT_IDS, trade_value, LIMITS, RARITY, SCRAPS, ZONES, gear_names, gear_stat, level, monster, rank, strength, tier_name

SHIFT = 6 * 3600
KINDS = {
    "hunt": "Дозор просит расчистить дорогу для хлебных подвод.",
    "supply": "Кладовщик примет образцы по счёту. Пустой мешок в ведомость не впишешь.",
    "raid": "За стеной пропал разъезд. Собери людей и проверь последний зал.",
}

def rotation(state, now, uid):
    shift = int(now) // SHIFT
    hero = state["heroes"][uid]
    board = hero.get("orders_board")
    if board and board["shift"] == shift:
        return board
    band=(level(hero)-1)//10
    average=band*10+5
    rng=random.Random(f"alpha:{shift}:{band}")
    pool = []
    for z, zone in enumerate(ZONES):
        for n in (*range(9),*EXTRA_HUNT_IDS):
            lv = rank(z,n)
            first = n if n in HUNT_IDS else 3 + 3*((n-3)//3)
            if lv > band*10+10 or rank(z,first) < band*10+1:
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
    carried=[]
    for i,q in enumerate((board or {}).get("jobs",[])):
        if q["owner"]==uid and not q["done"]:
            q.setdefault("ticket",f"{board['shift']}:{i}")
            carried.append(q)
    active={(q["kind"],q["z"],q["n"]) for q in carried}
    chosen=[entry for entry in chosen if entry[:3] not in active]
    board = {"shift":shift,"level":average,"jobs":[dict(kind=t,z=z,n=n,need=v,progress=0,owner=None,done=False)
                                                  for t,z,n,v in chosen]}
    for i,q in enumerate(board["jobs"]):q["ticket"]=f"{shift}:{i}"
    board["jobs"]=carried+board["jobs"]
    hero["orders_board"] = board
    return board

def record_win(state,party,z,n,mode):
    for uid in party:
        board=state["heroes"][uid].get("orders_board",{})
        for job in board.get("jobs",[]):
            if job["done"] or job["owner"]!=uid or (job["z"],job["n"])!=(z,n):continue
            if job["kind"]=="hunt" or (job["kind"]=="raid" and mode=="raid"):
                job["progress"]=min(job["need"],job["progress"]+1)

def details(q, hero=None, commit=False):
    z,n,kind = q["z"],q["n"],q["kind"]
    if kind=="raid":
        label = "Зачистить · "+ZONES[z][2][(n-3)//3][0]
    elif kind=="hunt":
        label = f"Устранить · {monster(z,n)} ×{q['need']}"
    else:
        label = f"Доставить · {SCRAPS[z][n]} ×{q['need']}"
    hard = kind=="raid" or n not in HUNT_IDS
    xp = (28+rank(z,n)*3)*(3 if kind=="raid" else 2 if hard else 1)
    xp *= 3 if kind=="raid" else q["need"]
    if hero is not None:
        xp=contract_xp(hero,q,xp,commit)
    if hard:
        label="🏰 "+label
    return label,xp,(15 if kind=="raid" else 7 if hard else 2)

def copper(q):
    effort = 5 if q["kind"]=="raid" else q["need"]
    return (3 + rank(q["z"],q["n"])//3)*effort

def progress(q,h):
    if q["kind"]=="supply":
        return min(q["need"],h["junk"].get(f"{q['z']}.{q['n']}",0))
    return q["progress"]

def payout(q,h,active=None):
    z=q["z"]
    _,xp,rare=details(q,h,commit=True)
    xp=min(city.earned(xp,active,h),LIMITS[-1]-h["xp"])
    h["xp"]+=xp
    h["wallet"]+=copper(q)
    h["peak"]=max(level(h),h.get("peak",1))
    tier=int(random.randrange(100)<rare)
    names=gear_names(z)
    pool=[k for k in range(len(names)) if ORIGIN.get((z,k))=="quest" and RARITY[z,k]==tier and suitable(z,k,h["class"])]
    k=random.choice([k for k in pool if names[k] not in h["items"]] or pool)
    item=names[k]
    if item in h["items"]:
        coins=4*trade_value(z,k)
        h["wallet"]+=coins
        award=f"{item} уже есть · +{coins} мед."
    else:
        h["items"][item]=[gear_stat(z,k),strength(z,k)]
        award=f"[{category(z,k)}] "+tier_name(z,k)+" · "+item+" — "+item_slot_label(z,k)
    return f"Комендант поставил печать. +{xp} опыта · +{copper(q)} мед. · {award}"

def desk(state,uid,args):
    now=time.time()
    board=rotation(state,now,uid)
    shift=board["shift"]
    jobs=board["jobs"]
    h=state["heroes"][uid]
    def button(label,action):
        return [{"text":label,"callback_data":action}]
    home=button("К доске","orders")
    note=""
    tickets={q.get("ticket",f"{shift}:{i}"):q for i,q in enumerate(jobs)}
    ticket=":".join(args[:2])
    if len(args)==3 and ticket in tickets:
        q=tickets[ticket]
        prefix=f"orders:{ticket}:"
        act=args[2]
        if not q["done"]:
            if act=="take" and q["owner"] is None:
                q["owner"]=uid
            elif act=="leave" and q["owner"]==uid:
                q.update(owner=None,progress=0)
                if not ticket.startswith(f"{shift}:"):q["done"]=True
            elif act=="turn" and q["owner"]==uid and progress(q,h)>=q["need"]:
                if q["kind"]=="supply":
                    key=f"{q['z']}.{q['n']}"
                    h["junk"][key]-=q["need"]
                    if not h["junk"][key]: del h["junk"][key]
                note=payout(q,h,city.buff(state))
                q["done"]=True
            if not q["done"]:
                label,xp,rare=details(q,h)
                xp=city.earned(xp,city.buff(state),h)
                z,n=q["z"],q["n"]
                site=encounter_area(z,n)
                if n not in HUNT_IDS:
                    dungeon,room=divmod(n-3,3)
                    site+=f"\n🏰 Подземелье · {ZONES[z][2][dungeon][0]} · зал {room+1}/3"
                orders={"robber":"Обозчики опознали налётчиков. Возврати дорогу подводам.",
                        "oath":"Старый караульный список сходится. Беглец снова берёт пошлину оружием.",
                        "cult":"У амбара опять собирают десятину в чашу без дна. Разберись со сборщиками.",
                        "changed":"В списке дворов он ещё числится живым. Дозор подтверждает следы Мора."}
                text=[label+"\n",orders.get(faction(z,n),KINDS[q["kind"]]),"\nГде искать\n"+site+f" · ур. {rank(z,n)}"]
                if q["kind"]=="supply": text.append("Источник: "+monster(z,n))
                text.append(f"\nНаграда\n{xp} опыта, {copper(q)} мед. и вещь · редкая {rare}%, иначе обычная.")
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
          f"Доска уровней {(board['level']-1)//10*10+1}–{(board['level']-1)//10*10+10} · до смены доски {minutes//60} ч {minutes%60} мин."]
    text.append("🏰 — цель в подземелье. Без метки — на обычной охоте.")
    if note: text.append(note)
    rows=[]
    for ticket,q in tickets.items():
        if q["done"]: continue
        mark="◆ " if q["owner"]==uid else "🔒 " if q["owner"] else ""
        if q["owner"]==uid and progress(q,h)>=q["need"]:mark="✅ "
        rows.append(button(mark+details(q)[0],f"orders:{ticket}:view"))
    page=int(args[1]) if len(args)==2 and args[0]=="page" and args[1].isascii() and args[1].isdigit() and len(args[1])<5 else 0
    pages=max(1,(len(rows)+9)//10)
    page=min(page,pages-1)
    rows=rows[page*10:page*10+10]
    if pages>1:
        rows.append([button(label,f"orders:page:{i}")[0] for label,i in (("‹ Назад",page-1),("Далее ›",page+1)) if 0<=i<pages])
    if not rows: text.append("Все записи погашены. Новые прибьют со сменой караула.")
    project=city.current(state)
    rows.insert(0,button("Общее дело · "+city.PROJECTS[project["kind"]][0],"city"))
    return "\n\n".join(text),rows+[button("К торговой площади","nav:town")]
