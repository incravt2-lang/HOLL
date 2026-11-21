from world import trade_value
"""Rules for one group's campaign. All identifiers in saved JSON are strings."""
import random
import secrets
import time

CLASSES = {
    "guard": ("Гвардеец Гусзка", "Стена щитов", "защищает отряд"),
    "nun": ("Сестра Ордена Матери", "Полевая перевязка", "лечит отряд"),
    "archer": ("Браконьер", "Меткий выстрел", "наносит усиленный урон"),
    "smith": ("Мастер Гильдии инженеров", "Раскол брони", "усиливает удары союзников"),
    "witch": ("Ученица аптекаря", "Отравленный клинок", "ослабляет ответный удар и наносит урон"),
}
HISTORIES = {
 "guard":"Старая гвардия держала ворота Гусзка, когда из-за стены звали по именам. Из того караула выжили немногие. Жалованье кончилось, совет распущен, и принимать присягу теперь некому. Но стоит гвардейцу откинуть плащ и показать потёртый нагрудный знак, как на ратушной лестнице ему уступают место у огня.",
 "nun":"Когда городские лекари запирали двери перед чужими, сёстры Ордена Матери ставили палатки по обе стороны рва. Под их белым полотнищем раненому давали воду до того, как спрашивали имя. Орден держится этого правила до сих пор. В полевой сумке сестры лежат две одинаковые перевязи: для того, кто нанёс удар, и для того, кто его принял.",
 "archer":"До Плети за силок на городском угодье в Ровне клеймили ладонь. Те немногие браконьеры, что пережили мор, жили вдали от рынка и читали следы лучше писем. Когда лисицы перестали брать выброшенную рыбу, охотники тоже оставили её лежать. Теперь судейский двор пуст, и браконьер впервые входит в Гусзк днём, с луком на виду.",
 "smith":"Когда в осаждённом голодом Гусзке лопнула ось мельницы, мастера Гильдии инженеров подняли жернов воротом из трёх тележных колёс. Позже они укрепляли плотину камнем из разобранного суда. Мастер и в поход берёт мерный клин: по звуку металла он находит слабую заклёпку и показывает товарищам, куда бить.",
 "witch":"В Аптекарском квартале Гусзка ученица должна была приготовить противоядие перед тремя мастерами. До её испытания дожил только один. Город так и не выдал ей свидетельство, зато у её двери выстраиваются носильщики из лазарета. Она знает, какой корень снимает судорогу, а каким достаточно натереть лезвие, чтобы пальцы врага ослабли.",
}
BASE_STATS = {"guard":(4,2,5,2),"nun":(2,2,3,6),"archer":(3,6,2,2),
              "smith":(5,2,4,2),"witch":(2,4,2,5)}
from world import ITEM_TRAITS,STAT_NAMES,outfit_start
from world import worn_bonus,bonus_label
TALENTS = {
    "guard":("Удар в брешь","Стальной строй","Острый клинок"),
    "nun":("Верная рука","Искусство перевязки","Походная выучка"),
    "archer":("Глаз сокола","Натяжение тетивы","Уязвимое место"),
    "smith":("Точный замах","Клин бронника","Тяжёлый молот"),
    "witch":("Точный надрез","Знание ядов","Холодный расчёт"),
}
ROLE_TEXT = {"guard":"+3 защиты отряду при «Стене щитов»","nun":"+3 здоровья отряду при перевязке",
             "archer":"+3 урона меткому выстрелу","smith":"+1 урона каждому атакующему союзнику при расколе",
             "witch":"+2 урона и +1 защиты отравленному клинку"}
def ranks(h):
    return h.get("ranks",[0,0,0])

def points(h):
    peak=max(level(h),h.get("peak",1))
    return 1+(peak-1)//4-sum(ranks(h))

def bonus(h,kind):
    return sum(value for item in h["gear"] if item for key,value in [worn_bonus(h,item)] if key==kind)

def crit(h):
    return min(65,5+2*ranks(h)[0]+bonus(h,"crit"))

def multiplier(h):
    return 150+5*ranks(h)[2]+bonus(h,"severity")

def bounds(base):
    return max(1,base*85//100),(base*115+99)//100

def training(h,uid):
    desc=("+2 п.п. к шансу критического удара",ROLE_TEXT[h["class"]],"+5 п.п. к множителю критического урона")
    lines=[f"Навыки · свободных очков: {points(h)}","Одно очко при создании и по одному на уровнях 5, 9, 13 и далее."]
    rows=[]
    for j,(name,rank) in enumerate(zip(TALENTS[h["class"]],ranks(h))):
        lines.append(f"{name} · {rank}/5 · {desc[j]} за ранг")
        if points(h)>0 and rank<5: rows.append([btn("Улучшить · "+name,f"train:{uid}:{j}:{rank}")])
    rows.append([btn("К герою","nav:hero")])
    return reply("\n".join(lines),rows)

def stats(h):
    values = [v+(level(h)-1)//4 for v in BASE_STATS[h["class"]]]
    for item in h["gear"]:
        if item in ITEM_TRAITS:
            idx,amount=ITEM_TRAITS[item]
            values[idx]+=amount
    return values

def health(h):
    return 19+2*level(h)+2*item_bonus(h,1)+3*stats(h)[2]

def energy(h):
    return 4+stats(h)[3]+bonus(h,"reserve")

def attack(h):
    return 5+level(h)+item_bonus(h,0)+stats(h)[0]//2+bonus(h,"strike")

from world import LIMITS, level, required_level
from world import encounter_trait, faction, HUNT_IDS, EXTRA_HUNT_IDS, ZONES, TRAITS, BANDS, VAULTS, SCRAPS, gear_names, monster, rank, strength
from world import LEFT, RIGHT, two_handed, ARM_BY_NAME, ARMS, arm_start
from world import SLOTS, SLOT_ORDER, RINGS, gear_slot, gear_stat, original_count
from quests import desk, record_win
from coast import craft, journal, road
from barter import exchange
from market import CURIOS, HEALS, REQUIREMENT, SCROLLS, equipment_chance, POTIONS, capacity, units, setup, market, trade, collect, scrap_value

from chronicle import TITLE, CHAPTERS, ZONE_NOTES
from world import CLASS_PIECES, OLD_CODES, CODE_ITEMS, ITEM_CODES, RARITY, TIERS, TIER_WEIGHTS, loot_slots, tier_name
HELP = TITLE + """
Охота — для 1–6 героев. В обычное подземелье идут 2–6 героев, в тайник с ключом — один.\n
Умение тратит 4 энергии; удар восстанавливает 1, блок — 3. У каждого героя свой запас.\nУровни 1–60. Все зоны открыты, диапазон подсказывает сложность. Каждый выбирает ход. Через минуту участник может закрыть раунд, пропустившие блокируют. При гибели теряется опыт и может выпасть надетая вещь."""
def btn(label, data):
    return {"text": label, "callback_data": data}

def reply(text, rows=()):
    return text, list(rows)

def migrate(s):
    if s.get("version")==9: return
    if s.get("version") not in (7,8): migrate_names(s)
    for hero in s["heroes"].values():
        for name in hero["items"]:
            z,k=map(int,ITEM_CODES[name].split("."))
            hero["items"][name]=[gear_stat(z,k),strength(z,k)]
        for slot,item in enumerate(hero["gear"]):
            if item and level(hero) < required_level(int(ITEM_CODES[item].split(".")[0])):
                hero["gear"][slot]=None
    s["version"]=9

def migrate_names(s):
    if s.get("version")==6: return
    def rename(item):
        return CODE_ITEMS[OLD_CODES[item]] if item in OLD_CODES else item
    for h in s.get("heroes",{}).values():
        h["items"] = {rename(item):value for item,value in h["items"].items()}
        h["gear"] = [rename(item) for item in h["gear"]]
        draft = h.get("barter_draft",{})
        for key in ("give","want"):
            if key in draft: draft[key] = rename(draft[key])
    for offer in s.get("offers",{}).values():
        for key in ("give","want"): offer[key] = rename(offer[key])
    migrate_hands(s)
    s["version"] = 6

def migrate_hands(s):
    if s.get("version")==5: return
    if s.get("version")!=4:
        migrate_slots(s)
    for h in s["heroes"].values():
        h["gear"].extend([None]*(len(SLOTS)-len(h["gear"])))
        if h["gear"][1]=="Плащ из лужских камышей":
            if h["gear"][9] is None: h["gear"][9] = "Плащ из лужских камышей"
            h["gear"][1] = None
    s["version"] = 5

def migrate_slots(s):
    if s.get("version")!=3:
        migrate_economy(s)
    for h in s["heroes"].values():
        old = [item for item in h["gear"] if item]
        h["gear"] = [None]*len(SLOTS)
        for z in range(len(ZONES)):
            for k,item in enumerate(gear_names(z)):
                if item in old: h["gear"][gear_slot(z,k)] = item
    s["version"] = 4

def migrate_economy(s):
    migrate_old(s)
    for h in s["heroes"].values():
        h["xp"] = min(LIMITS[-1],8*h["xp"])
        setup(h)
    s["version"] = 3

def migrate_old(s):
    if s.get("version")==2:
        return
    for h in s.setdefault("heroes",{}).values():
        lv = min(60, 1+h["xp"]//60)
        rem = h["xp"]%60
        h["xp"] = LIMITS[lv-1]//8+(rem*(50+10*lv)//60 if lv<60 else 0)
        for z, zone in enumerate(ZONES):
            for k,item in enumerate(zone[3]):
                if item in h["items"]:
                    h["items"][item] = [gear_stat(z,k),strength(z,k)]
    fights = {}
    active = list(s.pop("hunts",{}).values())
    raid = s.pop("raid",None)
    if raid:
        active.append(raid)
    for r in active:
        old = r.pop("place")
        z, dungeon = ((0,0),(0,1),(1,0))[old]
        hunt = r.pop("hunt",False)
        r.update(z=z, choice=dungeon, mode="hunt" if hunt else "raid")
        r.setdefault("room",0)
        if hunt:
            r["legacy_target"] = (0,6,3)[old]
        # Existing parties accepted the earlier death rules.
        r["legacy_safe"] = True
        fights[r["id"]] = r
    s.update(version=2,fights=fights)

def effective_power(h,item):
    power = h["items"][item][1]
    if item in ARM_BY_NAME and ARM_BY_NAME[item][0]!=h["class"]:
        return max(1,power//2)
    return power

def item_bonus(h,slot):
    return sum(effective_power(h,item) for item in h["gear"] if item and h["items"][item][0]==slot)

def death(h):
    lv = level(h)
    h["peak"] = max(lv,h.get("peak",1))
    loss = min(h["xp"],8*(50+10*min(lv,59))//5)
    h["xp"] -= loss
    slots = [j for j,v in enumerate(h["gear"]) if v]
    lost = None
    if slots and random.random()<0.35:
        slot = random.choice(slots)
        lost = h["gear"][slot]
        del h["items"][lost]
        h["gear"][slot] = None
    h["deaths"] = h.get("deaths",0)+1
    change = f" · уровень {lv} → {level(h)}" if level(h)<lv else ""
    return f"{h['name']}: −{loss} опыта{change} · " + (f"утрачено: {lost}" if lost else "снаряжение цело")

def target(r):
    if r["mode"]=="vault": return 9+r["room"]
    return r.get("legacy_target",r["choice"]) if r["mode"]=="hunt" else 3+3*r["choice"]+r["room"]

def maximum(r):
    n = target(r)
    if r["mode"]=="vault": return 25+3*rank(r["z"],n)
    if r["mode"]=="hunt": return len(r["party"])*(24+4*r.get("road_level",rank(r["z"],n)))
    return len(r["party"])*(14+2*rank(r["z"],n)+(5 if n>=3 else 0))

def title(r):
    z = r["z"]
    if r["mode"]=="vault": return VAULTS[z][0]
    return monster(z,target(r)) if r["mode"]=="hunt" else ZONES[z][2][r["choice"]][0]

def actions_text(s,r,finished=False):
    lines = []
    for uid in r["party"]:
        h = s["heroes"][uid]
        move = r["moves"].get(uid)
        action = {"hit":"удар","block":"блок","skill":CLASSES[h["class"]][1]}.get(move)
        if action is None:
            action = "автоблок" if finished else "выбирает ход"
        marker = "" if finished else ("✓ " if move else "⏳ ")
        lines.append(f"{marker}{h['name']} — {action}")
    for uid in r["party"]:
        potion = r.get("used",{}).get(uid)
        if potion:
            kind, amount = potion
            icon = "📜" if kind in SCROLLS else "🧪"
            gain = f" · отряд +{amount} ХП" if kind in HEALS else ""
            lines.append(f"{icon} {s['heroes'][uid]['name']} — {POTIONS[kind][0]}{gain}")
        elif r.get("drank",{}).get(uid)==r["round"]:
            lines.append(f"🧪 {s['heroes'][uid]['name']} — выпито зелье")
    return "\n".join(lines)

def heal_count(r):
    return sum(p[0] in HEALS for p in r.get("used",{}).values())

ROUTES = {"pits":"Известковые ямы","loft":"Сушильня"}

def vote_route(s,r,uid,op):
    votes=r["votes"]
    if op in ROUTES:
        votes[uid]=op
    elif op!="closevote" or time.time()<r["deadline"] or not votes:
        return reply("Выберите путь. Через минуту можно подвести итог по поданным голосам.")
    if len(votes)==len(r["party"]) or op=="closevote":
        counts={path:list(votes.values()).count(path) for path in ROUTES}
        highest=max(counts.values())
        # Party order starts with the leader and also resolves a timed tie in their absence.
        path=next(votes[i] for i in r["party"] if i in votes and counts[votes[i]]==highest)
        r["route"]=path
        del r["votes"]
        if path=="pits": r["enemy"]+=4*len(r["party"])
        r["log"]="Отряд выбрал путь: "+ROUTES[path]+"."
        r["deadline"]=time.time()+60
    return board(s,r,uid)

def board(s,r,viewer=None):
    key = r["id"]
    risk = "Старый поход: при гибели потерь нет." if r.get("legacy_safe") else "При гибели: −20% цены уровня и 35% риска потерять одну надетую вещь."
    if not r["round"]:
        names = ", ".join(s["heroes"][i]["name"] for i in r["party"])
        if r["mode"]=="vault":
            return reply(f"{title(r)} · одиночный тайник · ур. {rank(r['z'],11)}\nТри зала. Зелья продаются у городского аптекаря. Вход расходует один ключ.\n{risk}",
                         [[btn("Войти за ключ",f"go:{key}"),btn("Отменить",f"leave:{key}")]])
        return reply(f"{title(r)} · сбор {len(r['party'])}/6\n{names}\n{risk}",
                     [[btn("Войти",f"join:{key}"),btn("Выйти",f"leave:{key}")],[btn("Начать бой",f"go:{key}")]])
    z,n = r["z"],target(r)
    suffix = f"{key}:{r['round']}"
    stage = "" if r["mode"]=="hunt" else f" · зал {r['room']+1}/3"
    if "votes" in r:
        votes=r["votes"]
        rows=[[btn(f"{label} · {list(votes.values()).count(path)}",f"{path}:{suffix}")] for path,label in ROUTES.items()]
        rows.append([btn("Завершить голосование по таймеру",f"closevote:{suffix}")])
        text=(f"{title(r)} · развилка после первого зала\nОтряд: {r['hp']}/{r['maxhp']} ХП\n\n"
              "Известковые ямы — у противника больше ХП, его удары сильнее. За победу каждый получит связку шкур (12 мед.).\n"
              "Сушильня — здесь можно сорвать цепь. Босс пропустит первый ответный удар.\n\n"
              "Большинство выбирает путь. При равенстве решает предводитель; если он не голосовал — первый проголосовавший по списку отряда.")
        return reply(text+"\n\n"+r["log"],rows)
    if r.get("route") and r["room"]==1: stage += " · "+ROUTES[r["route"]]
    confirm = []
    count = heal_count(r)
    if count and viewer and r.get("heal_requests",{}).get(viewer)==count:
        confirm = [[btn("Подтвердить ещё одно лечение",f"healok:{suffix}:{count}")]]
    supplies = []
    if viewer:
        h = s["heroes"][viewer]
        supplies = [btn(v[0],f"{k}:{suffix}") for k,v in POTIONS.items()
                    if k not in ("heal","fury","ward") and h["potions"].get(k,0)>0 and level(h)>=REQUIREMENT[k]]
    supply_rows = [supplies[j:j+2] for j in range(0,len(supplies),2)]
    effects = []
    for uid,values in r.get("buffs",{}).items():
        for k,end in values.items():
            if end>=r["round"]: effects.append(f"{s['heroes'][uid]['name']} · {POTIONS[k][0]} ({end-r['round']+1})")
    stamina_line = ""
    if viewer in r["party"]:
        cap = energy(s["heroes"][viewer])
        stamina_line = f" · твоя энергия: {r.get('energy',{}).get(viewer,cap)}/{cap}"
    active = ("\nНастои: "+", ".join(effects)) if effects else ""
    divider = "\n\n────────────\n\n"
    ready = sum(uid in r["moves"] for uid in r["party"])
    log = r.get("log") or ""
    return reply(f"{title(r)}{stage} · раунд {r['round']}\n{monster(z,n)} · ур. {r.get('road_level',rank(z,n))} · {r['enemy']} ХП\n"
                 f"{encounter_trait(z,n)[0]} · {encounter_trait(z,n)[1]}\n\nОтряд: {r['hp']}/{r['maxhp']} ХП{stamina_line}{active}"
                 + (divider + log if log else "") + divider + f"Действия сейчас · {ready}/{len(r['party'])} готовы\n{actions_text(s,r)}",
                 [[btn(t,f"{a}:{suffix}") for t,a in (("Удар","hit"),("Блок","block"),("Умение · 4 эн.","skill"))],
                  [btn(label,f"{k}:{suffix}") for k,label in (("heal","Лечение"),("fury","Ярость"),("ward","Кожа"))],
                  [btn("Завершить по таймеру",f"finish:{suffix}")]] + supply_rows + confirm)

def roll_equipment(z,n,mode,cls=None):
    tier=random.choices(range(5),weights=TIER_WEIGHTS[mode])[0]
    return random.choice([k for k in loot_slots(z,n,cls) if RARITY[z,k]==tier])

def loot_description(z,n,mode,cls=None):
    lines=[]
    for tier,weight in enumerate(TIER_WEIGHTS[mode]):
        names=", ".join(gear_names(z)[k] for k in loot_slots(z,n,cls) if RARITY[z,k]==tier)
        pct=f"{equipment_chance(mode,n)*weight/10:.3f}".rstrip("0").rstrip(".").replace(".",",")
        lines.append(f"{TIERS[tier]} · {pct}% · {names}")
    return "\n".join(lines)

def resolve(s,r,viewer=None):
    z,n = r["z"],target(r)
    enemy_lv = r.get("road_level",rank(z,n))
    party = [s["heroes"][i] for i in r["party"]]
    dmg = shield = heal = cracks = hits = 0
    rolls = {}
    split_bonus = {}
    poisons = {}
    stamina = r.setdefault("energy",{})
    for i,h in zip(r["party"],party):
        lv = level(h)
        a = r["moves"].get(i,"block")
        cap = energy(h)
        stamina[i] = min(cap,stamina.get(i,cap)+(-4 if a=="skill" else 3 if a=="block" else 1))
        effects = r.get("buffs",{}).get(i,{})
        if effects.get("regen",0)>=r["round"]: heal += 4+lv//3
        if effects.get("venom",0)>=r["round"]: poisons[i] = 6+lv//3
        if effects.get("iron",0)>=r["round"]: shield += 12+lv
        elif effects.get("ward",0)>=r["round"]: shield += 5+lv//2
        if a=="block":
            shield += 6+lv+stats(h)[1]//2+bonus(h,"guard")
            continue
        hits += 1
        base = attack(h)
        mastery = ranks(h)[1]
        if effects.get("rage",0)>=r["round"]: base += 12+lv
        elif effects.get("fury",0)>=r["round"]: base += 5+lv//2
        if a=="skill":
            r["ready"][i] = r["round"]+2
            c = h["class"]
            if c=="guard": shield += 9+lv+3*mastery+bonus(h,"guard")
            elif c=="nun": heal += 10+lv+3*mastery+bonus(h,"medicine")
            elif c=="archer": base += 7+lv+stats(h)[1]//2+3*mastery
            elif c=="smith": split_bonus[i] = 3+lv//2+mastery
            else:
                shield += 5+lv//2+mastery
                base += 4+lv//2+2*mastery
        amount = random.randint(*bounds(base))
        critical = random.randrange(100)<crit(h)
        rolls[i]=(amount*multiplier(h)//100 if critical else amount,critical)
    sealed = r.get("sealed",0)==r["round"]
    group = faction(z,n)
    absorbs = group=="oath" or (group is None and n%3==1)
    absorb = (2+enemy_lv//5)*len(party) if not sealed and absorbs and r["round"]%2==0 else 0
    details=[]
    for i in r["party"]:
        amount,critical=rolls.get(i,(0,False))
        if i in rolls: amount+=sum(v for who,v in split_bonus.items() if who!=i)
        amount+=poisons.get(i,0)
        gap=max(0,enemy_lv-level(s["heroes"][i])-1)
        amount=amount*100//(100+10*gap)
        dmg+=amount
        if critical:
            details.append(f"Критический удар · {s['heroes'][i]['name']}")
    absorbed=min(absorb,dmg)
    dmg-=absorbed
    if absorbed: details.append(f"Защита врага поглотила {absorbed}.")
    r["enemy"] -= dmg
    r["hp"] = min(r["maxhp"],r["hp"]+heal)
    summary = f"Итоги раунда {r['round']}:\n"+actions_text(s,r,finished=True)
    if details: summary += "\n"+" · ".join(details)
    msg = f"{summary}\nОтряд нанёс {dmg} урона."
    if r["enemy"]<=0:
        record_win(s,r["party"],z,n,r["mode"])
        scraps = []
        for h in party:
            piece = collect(h,z,n,random.random())
            if piece: scraps.append(f"{h['name']}: {piece}")
            if random.random()<equipment_chance(r["mode"],n):
                k = roll_equipment(z,n,r["mode"],h["class"])
                item = gear_names(z)[k]
                label = tier_name(z,k)+" · "+item
                if item not in h["items"]:
                    h["items"][item] = [gear_stat(z,k),strength(z,k)]
                elif r["mode"]=="hunt":
                    label += " (уже есть)"
                else:
                    payment = 4*trade_value(z,k)
                    h["wallet"] += payment
                    label += f" (повтор: +{payment} мед.)"
                scraps.append(f"{h['name']}: {label}")
            book = h.setdefault("book",{})
            key = f"{z}.{n}"
            book[key] = book.get(key,0)+1
        if r["mode"]=="hunt" or r["room"]==2:
            del s["fights"][r["id"]]
            lines = [f"Победа · {title(r)}",msg] + scraps
            for h in party:
                lv = level(h)
                base = (16+min(enemy_lv,lv+4)*2)*(1 if r["mode"]=="hunt" else 3)
                xp = min(LIMITS[-1]-h["xp"],max(1,27*base//(10*(1+max(0,lv-enemy_lv-4)))))
                h["xp"] += xp
                h["peak"] = max(level(h),h.get("peak",1))
                up = f" · уровень {level(h)}!" if level(h)>lv else ""
                lines.append(f"{h['name']}: +{xp} опыта{up}")
            return reply("\n".join(lines),[[btn("Продолжить дорогу","road")]] if "road_level" in r else [])
        if r.get("route")=="pits" and r["room"]==1:
            for h in party:
                if units(h)<capacity(h):
                    h["junk"]["6.98"]=h["junk"].get("6.98",0)+1
                    scraps.append(h["name"]+": связка выделанных шкур")
                else:
                    h["wallet"]+=12
                    scraps.append(h["name"]+": шкуры проданы за 12 мед. (сумка полна)")
        if r.get("route")=="loft" and r["room"]==1:
            r["cut_chain"]=True
            msg+=" Отряд сорвал цепь с балки."
        if r["mode"]=="raid" and r["z"]==6 and r["choice"]==0 and r["room"]==0:
            r["votes"]={}
        r["room"] += 1
        r["enemy"] = maximum(r)
        r["hp"] = min(r["maxhp"],r["hp"]+sum(4+level(h)//2 for h in party))
        msg += " Враг повержен. Отряд перевёл дух."
        if scraps: msg += "\n"+" · ".join(scraps)
    else:
        raw = 3+enemy_lv+(4+enemy_lv//4 if r["mode"]=="vault" else 0)
        if r["mode"]=="hunt": raw -= max(0,enemy_lv-10)//2
        if group=="cult" and not sealed and r["round"]%3==0:
            for uid in r["party"]: stamina[uid]=max(0,stamina[uid]-1)
            msg += " Счёт недостачи: −1 энергия каждому."
        rush = (group=="robber" and r["round"]==1) or (group is None and n%3==0 and r["round"]%3==0)
        wounded = group=="changed" or (group is None and n%3==2)
        if not sealed and (rush or (wounded and 2*r["enemy"]<maximum(r))):
            raw += 4+enemy_lv//3
        if r.get("route")=="pits" and r["room"]==1: raw+=2
        gap=max(0,enemy_lv-sum(level(h) for h in party)//len(party)-1)
        raw=raw*(100+12*gap)//100
        taken = max(0,random.randint(*bounds(raw*len(party)))-shield)
        if r.pop("cut_chain",False):
            taken=0
            msg+=" Мастер дёрнул крюк. Оборванная цепь рухнула на пол."
        r["hp"] -= taken
        msg += f" Ответный удар — {taken}."
        if r["hp"]<=0:
            del s["fights"][r["id"]]
            if "road_level" in r: party[0].pop("coast_trip",None)
            if r.get("legacy_safe"):
                return reply("Отряд погиб. В этом перенесённом походе потерь нет.\n"+msg)
            return reply("Отряд погиб. Герои возродились в лагере.\n"+msg+"\n"+"\n".join(death(h) for h in party))
    r.update(round=r["round"]+1,moves={},used={},heal_requests={},deadline=time.time()+60,log=msg)
    return board(s,r,viewer)

def atlas(mode,h):
    rows = []
    for z,zone in sorted(enumerate(ZONES),key=lambda pair:BANDS[pair[0]]):
        if mode=="vault" and z not in VAULTS: continue
        low = 1+10*BANDS[z]
        mark = " ◆" if low<=level(h)<=low+9 else ""
        rows.append([btn(f"{zone[0]} · {low}–{low+9}{mark}",f"area:{mode}:{z}")])
    return reply("Выбери зону. ◆ — рекомендована для твоего уровня.",rows)

def area(mode,z,h):
    name, beasts, raids, items = ZONES[z]
    if mode=="book":
        rows = []
        total = 0
        count = 12 if z in VAULTS else 9
        for n in (*range(count),*EXTRA_HUNT_IDS):
            kills = h.get("book",{}).get(f"{z}.{n}",0)
            total += bool(kills)
            rows.append([btn(f"{monster(z,n)} · {kills} побед",f"entry:{z}:{n}")])
        return reply(f"Бестиарий · {h['name']} · {name} · побеждено видов {total}/{count+len(EXTRA_HUNT_IDS)}",rows)
    if mode=="vault":
        if z not in VAULTS: return reply("Выбери тайник в разделе «Тайники».")
        return reply(f"{VAULTS[z][0]} · ур. {rank(z,9)}–{rank(z,11)}\nКлючей: {h['keys'].get(str(z),0)} · ключи продаются в городе\nСнаряжение за босса: 50%. Возможные находки: "+", ".join(gear_names(z)[k] for k in loot_slots(z,11,h["class"])),
                     [[btn("Подготовиться ко входу",f"new:vault:{z}:0")]])
    if mode=="zones":
        return reply(f"{name} · уровни {10*BANDS[z]+1}–{10*BANDS[z]+10}\n{ZONE_NOTES[z]}\nОхота: {', '.join(monster(z,n) for n in HUNT_IDS)}\nПодземелья: {raids[0][0]}, {raids[1][0]}",
                     [[btn("Охота",f"area:hunt:{z}"),btn("Подземелья",f"area:raid:{z}")]]+([[btn(VAULTS[z][0],f"area:vault:{z}")]] if z in VAULTS else []))
    if mode=="hunt":
        rows = [[btn(f"{monster(z,j)} · ур. {rank(z,j)}",f"new:hunt:{z}:{j}")] for j in sorted(HUNT_IDS,key=lambda n:rank(z,n))]
    else:
        rows = [[btn(f"{v[0]} · ур. {rank(z,3+3*j)}–{rank(z,5+3*j)}",f"new:raid:{z}:{j}")] for j,v in enumerate(raids)]
    return reply(f"{name} · выбери цель",rows)

def inventory(h,uid,slot=None,page=0):
    if slot is None:
        rows = []
        buttons = []
        for j in SLOT_ORDER:
            display = h["gear"][j] or ("двуручное оружие" if j==LEFT and two_handed(h["gear"][RIGHT]) else "—")
            buttons.append(btn(SLOTS[j]+" · "+display,f"slot:{uid}:{j}"))
        rows = [buttons[j:j+2] for j in range(0,len(buttons),2)]
        stock = [f"{v[0]} ×{h['potions'][k]}" for k,v in POTIONS.items() if h["potions"].get(k)]
        rows.append([btn("Обмен вещами","barter"),btn("Скупщик","shop:"+uid+":"+str(h["shop_rev"])+":sell")])
        return reply(f"Снаряжение · {h['name']}\nВыбери ячейку, чтобы примерить или снять вещь.\n"
                     f"Хлам {units(h)}/{capacity(h)} · {h['wallet']} мед.\nРасходники: "+(", ".join(stock) or "пусто"),rows)
    worn = h["gear"][slot]
    label_worn = worn
    sources = []
    rows = []
    for z in range(len(ZONES)):
        for k,item in enumerate(gear_names(z)):
            if gear_slot(z,k)!=(7 if slot in RINGS else slot): continue
            if item not in h["items"]:
                if (z,k) in CLASS_PIECES and CLASS_PIECES[z,k][2]!=h["class"]: continue
                idx = next(n for n in (0,5,8,11) if k in loot_slots(z,n))
                if idx==0: idx = min((0,1,2),key=lambda n:abs(rank(z,n)-level(h)))
                sources.append((abs(rank(z,idx)-level(h)),z,idx,item))
                continue
            stat = h["items"][item][0]
            power = effective_power(h,item)
            label = f"{item} · +{power} удар" if stat==0 else f"{item} · +{2*power} ХП"
            label += f" · ур. {required_level(z)}"
            if item in ITEM_TRAITS:
                idx,value=ITEM_TRAITS[item]
                label += f" · {STAT_NAMES[idx]} +{value}"
            if item in ARM_BY_NAME:
                cls = ARM_BY_NAME[item][0]
                label += " · "+CLASSES[cls][0]+(" · ½" if cls!=h["class"] else "")
                if two_handed(item): label += " · 2 руки"
            label = tier_name(z,k)+" · "+label
            label += " · "+bonus_label(h,item)
            if item!=worn:
                if item in h["gear"]: label += " · "+SLOTS[h["gear"].index(item)]
                rows.append([btn(label,f"dress:{uid}:{slot}:{z}:{k}")])
            else: label_worn = label
    pages=max(1,(len(rows)+11)//12)
    page=min(page,pages-1)
    rows=rows[12*page:12*(page+1)]
    if pages>1:
        rows.append([btn(f"Страница {i+1}/{pages}",f"slot:{uid}:{slot}:{i}") for i in (page-1,page+1) if 0<=i<pages])
    if sources:
        _,z,n,item = min(sources)
        rows.append([btn("Где найти · "+item,f"entry:{z}:{n}")])
    if slot==LEFT and two_handed(h["gear"][RIGHT]):
        return reply("Обе руки заняты: "+h["gear"][RIGHT],[[btn("Правая рука",f"slot:{uid}:{RIGHT}")],[btn("К ячейкам","nav:bag")]])
    if worn: rows.append([btn("Снять в сумку",f"off:{uid}:{slot}")])
    rows.append([btn("К ячейкам","nav:bag")])
    return reply(f"{SLOTS[slot]} · "+(label_worn if worn else "пусто"),rows)

def play(s,uid,name,cmd):
    migrate(s)
    heroes,fights = s["heroes"],s["fights"]
    h = heroes.get(uid)
    p = cmd.split(":")
    op = p[0]
    if op=="lore":
        if len(p)==2 and p[1] in tuple(map(str,range(len(CHAPTERS)))):
            heading,body = CHAPTERS[int(p[1])]
            return reply(heading+"\n\n"+body,[[btn("К оглавлению","nav:lore")]])
        return reply("Гусзкские записи",[[btn(ch[0],f"lore:{j}")] for j,ch in enumerate(CHAPTERS)])
    if op in ("start","help"): return reply(HELP)
    if op=="bio" and len(p)==2 and p[1] in CLASSES:
        c = p[1]
        rows = [[btn("Выбрать этот класс",f"class:{uid}:{c}"),btn("Все классы","nav:hero")]] if not h else []
        return reply(f"{CLASSES[c][0]}\n\n{HISTORIES[c]}\n\n{CLASSES[c][1]} — {CLASSES[c][2]}.",rows)
    if op in ("hero","diary"):
        if h is None:
            return reply("Выбери класс героя. Умения усиливаются с уровнем.\n"+
                         "\n".join(f"{c[0]} · {c[1]}: {c[2]}" for c in CLASSES.values()),
                         [[btn(c[0],f"bio:{k}")] for k,c in CLASSES.items()])
        h["name"] = name
        lv = level(h)
        xp = "Достигнут предел уровней." if lv==60 else f"До уровня {lv+1}: {LIMITS[lv]-h['xp']} опыта."
        diary="\n\n"+journal(s,uid) if op=="diary" else ""
        return reply(f"{name} · {CLASSES[h['class']][0]} · ур. {lv}/60\n{xp}\n"
                     f"Удар: {bounds(attack(h))[0]}–{bounds(attack(h))[1]} · крит: {crit(h)}% ×{multiplier(h)/100:.2f}\nЗдоровье: {health(h)} · запас энергии: {energy(h)}\n"+
                     " · ".join(f"{n}: {v}" for n,v in zip(STAT_NAMES,stats(h)))+f"\nСмертей: {h.get('deaths',0)}"+diary,
                     [[btn(f"Навыки · {points(h)} очк.","nav:skills")],[btn("История и умение","bio:"+h["class"])]])
    if op=="class" and len(p)==3 and p[2] in CLASSES:
        if uid!=p[1]: return reply("Это чужой лист героя.")
        if h: return reply("Твой герой уже выбрал класс.")
        heroes[uid] = dict(name=name,xp=0,items={},gear=[None]*len(SLOTS),**{"class":p[2]})
        setup(heroes[uid])
        return reply(f"Класс выбран.\n{name} · {CLASSES[p[2]][0]}")
    if not h: return reply("Выбери класс в разделе «Мой герой».")
    mine = next((r for r in fights.values() if uid in r["party"]),None)
    if op in ("road","roadfight","craft"):
        if mine: return board(s,mine,uid)
        if op=="road": return road(h,p[1:])
        if op=="craft": return craft(h,p[1:])
        trip=h.get("coast_trip",{})
        if not trip.get("waiting") or p[1:]!=[trip.get("id")]: return reply("Засада уже позади.")
        z,n=min(((z,n) for z in range(len(ZONES)) for n in HUNT_IDS if faction(z,n) in ("robber","oath")),
                key=lambda pair:abs(rank(*pair)-level(h)))
        key=secrets.token_hex(5)
        fights[key]=dict(id=key,mode="hunt",z=z,choice=n,room=0,round=0,party=[uid],road_level=level(h))
        trip.pop("waiting")
        return play(s,uid,name,"go:"+key)
    if op=="skills": return training(h,uid)
    if op=="train":
        if mine and mine["round"]: return reply("Навыки развиваются между боями.")
        if len(p)==4 and p[1]==uid and p[2] in ("0","1","2"):
            j=int(p[2])
            values=h.setdefault("ranks",[0,0,0])
            if str(values[j])==p[3] and values[j]<5 and points(h)>0:
                h["peak"]=max(level(h),h.get("peak",1))
                values[j]+=1
        return training(h,uid)
    if op=="orders":
        if mine and mine["round"]: return reply("Комендант ждёт тебя в городе после боя.")
        return desk(s,uid,p[1:])
    if op in ("town","shop"):
        if mine and mine["round"]: return reply("Ты в бою. Прилавки откроются после возвращения.")
        if op=="town":
            h.pop("coast_trip",None)
            return market(h,uid)
        return trade(h,uid,p)
    if op=="barter": return exchange(s,uid,cmd)
    if op=="bag": return inventory(h,uid)
    if op in ("slot","off","dress") and len(p)>=3 and p[1]==uid and p[2] in tuple(map(str,range(len(SLOTS)))):
        slot = int(p[2])
        if op=="slot": return inventory(h,uid,slot,int(p[3]) if len(p)==4 and p[3].isascii() and p[3].isdigit() and len(p[3])<6 else 0)
        if mine and mine["round"]: return reply("Экипировку можно менять между боями.")
        if op=="off": h["gear"][slot] = None
        elif len(p)==5 and p[3] in DIGITS and p[4] in tuple(map(str,range(len(gear_names(int(p[3])))))):
            z,k = map(int,p[3:])
            item = gear_names(z)[k]
            if item not in h["items"] or gear_slot(z,k)!=(7 if slot in RINGS else slot):
                return reply("Для этой ячейки предмет недоступен.")
            if level(h)<required_level(z): return reply(f"Нужен уровень {required_level(z)}.")
            if slot==LEFT and two_handed(h["gear"][RIGHT]): return reply("Сначала сними двуручное оружие.")
            if two_handed(item) and h["gear"][LEFT]: return reply("Для этого оружия нужны обе руки. Сначала сними предмет с левой руки.")
            if item in h["gear"]: h["gear"][h["gear"].index(item)] = None
            h["gear"][slot] = item
        return inventory(h,uid,slot)
    if op in MODES:
        if mine and op in ("hunt","raid","vault"): return board(s,mine,uid)
        return atlas(op,h)
    if op=="area" and len(p)==3 and p[1] in MODES and p[2] in DIGITS:
        return area(p[1],int(p[2]),h)
    if op=="entry" and len(p)==3 and p[1] in DIGITS and p[2] in tuple(map(str,range(16))):
        z,n = map(int,p[1:])
        zone = ZONES[z]
        if 9<=n<12 and z not in VAULTS: return reply("Эта запись недоступна.")
        mode = "hunt" if n in HUNT_IDS else "vault" if n>=9 else "raid"
        origin = VAULTS[z][0] if mode=="vault" else "Охота" if mode=="hunt" else zone[2][(n-3)//3][0]
        loot = loot_description(z,n,mode,h["class"])
        return reply(f"{monster(z,n)} · ур. {rank(z,n)}\n{zone[0]} · {origin}\n{encounter_trait(z,n)[0]}: {encounter_trait(z,n)[1]}\n"
                     f"Победы: {h.get('book',{}).get(f'{z}.{n}',0)}\n" +
                     f"Хлам: {SCRAPS[z][n]} · {scrap_value(z,n)} мед.\nРедкость: {CURIOS[z]} · 6%\n" + ("За охоту" if mode=="hunt" else f"Зал {n%3+1}") + f" · шанс снаряжения {equipment_chance(mode,n):.0%}\n"+loot,[[btn("Назад",f"area:book:{z}")]])
    if op=="new" and len(p)==4 and p[1] in ("hunt","raid","vault") and p[2] in DIGITS:
        if mine: return board(s,mine,uid)
        mode = p[1]
        if p[3] not in tuple(map(str,HUNT_IDS if mode=="hunt" else (0,1))): return reply("Выбери цель заново.")
        if mode=="vault" and (int(p[2]) not in VAULTS or p[3]!="0"): return reply("Выбери тайник в разделе «Тайники».")
        key = secrets.token_hex(5)
        r = dict(id=key,mode=mode,z=int(p[2]),choice=int(p[3]),room=0,round=0,party=[uid])
        h.pop("coast_trip",None)
        fights[key] = r
        return board(s,r,uid)
    r = fights.get(p[1]) if len(p)>1 else None
    if not r: return reply("Эта карточка устарела. Открой текущий бой из меню.")
    if not r["round"]:
        if op=="join" and r["mode"]=="vault": return reply("Этот тайник рассчитан на одного героя.")
        if op=="join" and not mine:
            h.pop("coast_trip",None)
            if len(r["party"])>=6: return reply("В отряде уже шесть героев.")
            r["party"].append(uid)
        elif op=="join" and mine is not r: return reply("Ты уже в другом отряде.")
        if op=="leave" and uid in r["party"]:
            r["party"].remove(uid)
            if not r["party"]:
                del fights[r["id"]]
                return reply("Сбор закрыт.")
        if op=="go":
            if uid not in r["party"]: return reply("Сначала войди в отряд.")
            if r["mode"]=="raid" and len(r["party"])<2: return reply("В подземелье нужны хотя бы двое.")
            if r["mode"]=="vault":
                zone_key = str(r["z"])
                if h["keys"].get(zone_key,0)<1: return reply("Нужен ключ от этого тайника. Купи его у ключницы в городе.")
                h["keys"][zone_key] -= 1
            hp = sum(health(heroes[i]) for i in r["party"])
            for member in r["party"]:
                heroes[member]["shop_rev"] += 1
            r.update(round=1,enemy=maximum(r),hp=hp,maxhp=hp,moves={},ready={},deadline=time.time()+60,log="Начало боя.")
        return board(s,r,uid)
    if uid not in r["party"]: return reply("Ты наблюдаешь за этим боем.")
    if len(p)!=(4 if op=="healok" else 3) or p[2]!=str(r["round"]): return reply("Ход уже прошёл. Открой актуальную карточку.")
    if "votes" in r: return vote_route(s,r,uid,op)
    if op in ROUTES or op=="closevote": return reply("Путь уже выбран.")
    confirmed = op=="healok"
    if confirmed:
        count = heal_count(r)
        if not count or r.get("heal_requests",{}).get(uid)!=count or p[3]!=str(count):
            return reply("Ситуация изменилась. Проверь силы отряда и выбери лечение заново.")
        op = r.get("heal_kind",{}).get(uid,"heal")
    if op in POTIONS:
        if level(h)<REQUIREMENT[op]: return reply(f"Нужен уровень {REQUIREMENT[op]}.")
        if r.setdefault("drank",{}).get(uid)==r["round"]: return reply("В этом раунде ты уже использовал расходник.")
        if not h["potions"].get(op): return reply("Этого зелья нет. Запас можно пополнить в городе.")
        if op in HEALS:
            if r["hp"]==r["maxhp"]: return reply("У отряда полный запас сил.")
            if heal_count(r) and not confirmed:
                r.setdefault("heal_kind",{})[uid] = op
                r.setdefault("heal_requests",{})[uid] = heal_count(r)
                text,rows = board(s,r,uid)
                return reply(text+"\nВ этом раунде отряд уже лечили. Потратить ещё одно зелье?",rows)
            healed = min(r["maxhp"]-r["hp"],(12+2*level(h)) if op=="heal" else (35+3*level(h)))
            r["hp"] += healed
        elif op in SCROLLS:
            if uid in r.get("scroll_users",[]): return reply("Ты уже читал свиток в этом походе.")
            if op=="seal":
                if r.get("sealed",0)==r["round"]: return reply("Враг уже скован печатью.")
                r["sealed"] = r["round"]
            else:
                if r["ready"].get(uid,0)<=r["round"]: return reply("Твоё умение уже готово.")
                r["ready"][uid] = r["round"]
            r.setdefault("scroll_users",[]).append(uid)
        else:
            buffs = r.setdefault("buffs",{}).setdefault(uid,{})
            competing = {"iron":"ward","ward":"iron","rage":"fury","fury":"rage"}.get(op)
            if competing: buffs.pop(competing,None)
            buffs[op] = r["round"]+2
        h["potions"][op] -= 1
        r["drank"][uid] = r["round"]
        r.setdefault("used",{})[uid] = [op,healed if op in HEALS else 0]
        r.get("heal_requests",{}).pop(uid,None)
        return board(s,r,uid)
    if op=="finish":
        if time.time()<r["deadline"]: return reply("Минута ещё не прошла.")
        return resolve(s,r,uid)
    if op not in ("hit","block","skill"): return reply("Выбери действие на карточке боя.")
    if op=="skill" and r.get("energy",{}).get(uid,energy(h))<4: return reply("Нужно 4 энергии. Удар вернёт 1, блок — 3.")
    if op=="skill" and r["ready"].get(uid,0)>r["round"]: return reply("Умение восстанавливается.")
    r["moves"][uid] = op
    if len(r["moves"])==len(r["party"]): return resolve(s,r,uid)
    return board(s,r,uid)

MODES = ("hunt","raid","book","zones","vault")
DIGITS = tuple(map(str,range(len(ZONES))))
