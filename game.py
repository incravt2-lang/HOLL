from world import SEAM_SHIELD, wear_level, is_humanoid, trade_value
"""Rules for one group's campaign. All identifiers in saved JSON are strings."""
import random
import workshops
from world import ORIGIN, RECIPES
import city
import haul
import forks
from copy import deepcopy
import secrets
import time

CLASSES = {
    "guard": ("Гвардеец Гусзка", "Стена щитов", "защищает отряд"),
    "nun": ("Сестра Ордена Матери", "Полевая перевязка", "лечит отряд"),
    "archer": ("Браконьер", "Меткий выстрел", "наносит усиленный урон"),
    "smith": ("Мастер Гильдии инженеров", "Раскол брони", "в этом раунде усиливает свой удар и удары всех атакующих союзников"),
    "witch": ("Ученица аптекаря", "Отравленный клинок", "ослабляет ответный удар и наносит урон"),
}
HISTORIES = {
 "guard":"Старая гвардия держала ворота Гусзка, когда из-за стены звали по именам. Из того караула выжили немногие. Жалованье кончилось, совет распущен, и принимать присягу теперь некому. Но стоит гвардейцу откинуть плащ и показать потёртый нагрудный знак, как на ратушной лестнице ему уступают место у огня.",
 "nun":"Когда городские лекари запирали двери перед чужими, сёстры Ордена Матери ставили палатки по обе стороны рва. Под их белым полотнищем раненому давали воду до того, как спрашивали имя. Орден держится этого правила до сих пор. В полевой сумке сестры лежат две одинаковые перевязи: для того, кто нанёс удар, и для того, кто его принял.",
 "archer":"До Мора за силок на городском угодье в Ровне клеймили ладонь. Те немногие браконьеры, что пережили мор, жили вдали от рынка и читали следы лучше писем. Когда лисицы перестали брать выброшенную рыбу, охотники тоже оставили её лежать. Теперь судейский двор пуст, и браконьер впервые входит в Гусзк днём, с луком на виду.",
 "smith":"Когда в осаждённом голодом Гусзке лопнула ось мельницы, мастера Гильдии инженеров подняли жернов воротом из трёх тележных колёс. Позже они укрепляли плотину камнем из разобранного суда. Мастер и в поход берёт мерный клин: по звуку металла он находит слабую заклёпку и сам бьёт в раскрывшийся шов и показывает его товарищам.",
 "witch":"В Аптекарском квартале Гусзка ученица должна была приготовить противоядие перед тремя мастерами. До её испытания дожил только один. Город так и не выдал ей свидетельство, зато у её двери выстраиваются носильщики из лазарета. Она знает, какой корень снимает судорогу, а каким достаточно натереть лезвие, чтобы пальцы врага ослабли.",
}
BASE_STATS = {"guard":(4,2,5,2),"nun":(2,2,3,6),"archer":(3,6,2,2),
              "smith":(5,2,4,2),"witch":(2,4,2,5)}
from world import class_power, ITEM_TRAITS,STAT_NAMES,outfit_start
from world import worn_bonus,bonus_label
TALENTS = {
    "guard":("Удар в брешь","Стальной строй","Острый клинок"),
    "nun":("Верная рука","Искусство перевязки","Походная выучка"),
    "archer":("Глаз сокола","Натяжение тетивы","Уязвимое место"),
    "smith":("Точный замах","Клин бронника","Тяжёлый молот"),
    "witch":("Точный надрез","Знание ядов","Холодный расчёт"),
}
ROLE_TEXT = {"guard":"+3 защиты отряду при «Стене щитов»","nun":"+3 здоровья отряду при перевязке",
             "archer":"+3 урона меткому выстрелу","smith":"+1 урона инженеру и каждому атакующему союзнику при расколе",
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
    return 19+2*level(h)+item_bonus(h,1)+3*stats(h)[2]

def energy(h):
    return 4+stats(h)[3]+bonus(h,"reserve")

def attack(h):
    return 5+level(h)+item_bonus(h,0)+stats(h)[0]//2+bonus(h,"strike")

from world import LIMITS, level, required_level
from world import area_name, encounter_area, encounter_trait, faction, HUNT_IDS, EXTRA_HUNT_IDS, ZONES, TRAITS, BANDS, VAULTS, SCRAPS, gear_names, monster, rank, strength
from world import LEFT, RIGHT, two_handed, ARM_BY_NAME, ARMS, arm_start
from world import item_slot_label, SLOTS, SLOT_ORDER, RINGS, gear_slot, gear_stat, original_count
from progression import victory_xp
from quests import desk, record_win
from notes import collection, find_note
from coast import ROAD_ENCOUNTER_CHANCE, craft, journal, road
from trophies import spoils
from cargo import needs
from world import category
from market import material_name,revision
from barter import exchange
from market import CURIOS, HEALS, REQUIREMENT, SCROLLS, equipment_chance, POTIONS, capacity, units, setup, market, trade, collect, scrap_value, scrap_payment

from chronicle import TITLE, CHAPTERS, ZONE_NOTES
from world import CLASS_PIECES, OLD_CODES, CODE_ITEMS, ITEM_CODES, RARITY, TIERS, TIER_WEIGHTS, loot_slots, tier_name
HELP = TITLE + """
Охота — для 1–6 героев. В обычное подземелье идут 2–6 героев, в тайник с ключом — один.\n
Умение тратит 4 энергии; удар восстанавливает 1, блок — 3. У каждого героя свой запас.\nУровни 1–60. Все зоны открыты, диапазон подсказывает сложность. Каждый выбирает ход. Через минуту участник может закрыть раунд, пропустившие блокируют. Поручения приносят опыт и медь. Перед боссом можно уйти с находками двух залов. При гибели добыча похода теряется, штраф — до 5% цены уровня и 5% риска потерять одну надетую вещь. Уровень сохраняется."""
def btn(label, data):
    return {"text": label, "callback_data": data}

def reply(text, rows=()):
    return text, list(rows)

def migrate(s):
    if s.get("version")==12: return
    from_previous=s.get("version")==11
    if s.get("version") not in (7,8,9,10,11): migrate_names(s)
    def refresh(items):
        for name in items:
            z,k=map(int,ITEM_CODES[name].split("."))
            if not from_previous or (z,k) in ORIGIN:
                items[name]=[gear_stat(z,k),strength(z,k)]
    candidates=list(s["heroes"].values())
    for alternatives in s.get("choices",{}).values():candidates.extend(alternatives.values())
    for hero in candidates:
        refresh(hero["items"])
        if not from_previous:enforce_wear_level(hero)
    for fight in s.get("fights",{}).values():
        for bag in fight.get("haul",{}).values():
            refresh(bag.get("items",{}))
    s["version"]=12

def enforce_wear_level(hero):
    for slot,item in enumerate(hero["gear"]):
        if item and level(hero)<wear_level(*map(int,ITEM_CODES[item].split("."))):
            hero["gear"][slot]=None

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
    return class_power(h["class"],item,h["items"][item][1])

def item_bonus(h,slot):
    return sum(effective_power(h,item) for item in h["gear"] if item and h["items"][item][0]==slot)

def death(h):
    lv = level(h)
    h["peak"] = max(lv,h.get("peak",1))
    loss = min(h["xp"]-LIMITS[lv-1],8*(50+10*min(lv,59))//20)
    h["xp"] -= loss
    slots = [j for j,v in enumerate(h["gear"]) if v]
    lost = None
    if slots and random.random()<0.05:
        slot = random.choice(slots)
        lost = h["gear"][slot]
        del h["items"][lost]
        h["gear"][slot] = None
    h["deaths"] = h.get("deaths",0)+1
    if level(h)<lv: enforce_wear_level(h)
    change = f" · уровень {lv} → {level(h)}" if level(h)<lv else ""
    return f"{h['name']}: −{loss} опыта{change} · " + (f"утрачено: {lost}" if lost else "снаряжение цело")

def target(r):
    if r["mode"]=="vault": return 9+r["room"]
    return r.get("legacy_target",r["choice"]) if r["mode"]=="hunt" else 3+3*r["choice"]+r["room"]

def return_route(r):
    if "road_level" in r:
        return [[btn("Продолжить дорогу","road")]]
    z=r["z"]
    if r["mode"]=="hunt":
        half=int((rank(z,target(r))-1)%10>=5)
    else:
        half=1 if r["mode"]=="vault" else r["choice"]
    return [[btn("Вернуться · "+area_name(z,half),f"travel:{z}:{half}")]]

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

ROUTES = {"pits","loft","patha","pathb"}

def vote_route(s,r,uid,op):
    votes=r["votes"]
    choices=forks.options(r)
    if "path_coin" in r:
        if op!="pathok": return board(s,r,uid)
        path=r.pop("path_coin")
    else:
        if op in choices: votes[uid]=op
        elif op!="closevote" or time.time()<r["deadline"] or not votes:
            return board(s,r,uid)
        if len(votes)<len(r["party"]) and op!="closevote": return board(s,r,uid)
        counts={p:list(votes.values()).count(p) for p in choices}
        if len(set(counts.values()))==1:
            r["path_coin"]=random.choice(list(choices))
            return board(s,r,uid)
        path=max(counts,key=counts.get)
    r["route"]=path
    del r["votes"]
    if path=="pits": r["enemy"]+=4*len(r["party"])
    r["log"]=forks.choose(s,r,choices[path])
    r["deadline"]=time.time()+60
    return board(s,r,uid)

def board(s,r,viewer=None):
    key = r["id"]
    risk = "Старый поход: при гибели потерь нет." if r.get("legacy_safe") else "При гибели: до −5% цены уровня без потери уровня и 5% риска потерять одну надетую вещь."
    if r["mode"]!="hunt":
        risk+=" Добыча залов остаётся в походе до выхода. Перед боссом можно уйти с находками."
    if not r["round"]:
        names = ", ".join(s["heroes"][i]["name"] for i in r["party"])
        if r["mode"]=="vault":
            return reply(f"{title(r)} · одиночный тайник · ур. {rank(r['z'],11)}\nТри зала. Зелья продаются у городского аптекаря. Вход расходует один ключ.\n{risk}",
                         [[btn("Войти за ключ",f"go:{key}"),btn("Отменить",f"leave:{key}")]])
        return reply(f"{title(r)} · сбор {len(r['party'])}/6\n{names}\n{risk}",
                     ([[btn("Начать бой",f"go:{key}")],[btn("Выйти из сбора",f"leave:{key}")]] if viewer in r["party"] else [[btn("Вступить в отряд",f"join:{key}")]]))
    z,n = r["z"],target(r)
    suffix = f"{key}:{r['round']}"
    stage = "" if r["mode"]=="hunt" else f" · зал {r['room']+1}/3"
    if "exit_coin" in r:
        forward = r["exit_coin"]=="faceboss"
        result = "Орёл — идём к боссу." if forward else "Решка — возвращаемся с добычей."
        return reply(f"{title(r)} · перед боссом\nОтряд не договорился и выбрал подбросить монету.\n\n{result}",
                     [[btn("Войти" if forward else "Повернуть назад",f"coinok:{suffix}")]])
    if "exit_votes" in r:
        votes=r["exit_votes"]
        rows=[[btn(f"{label} · {list(votes.values()).count(action)}",f"{action}:{suffix}")]
              for action,label in (("turnback","Уйти с добычей"),("faceboss","К боссу"))]
        if len(r["party"])>1: rows.append([btn("Подвести итог через минуту",f"exitfinish:{suffix}")])
        return reply(f"{title(r)} · перед боссом\nОтряд: {r['hp']}/{r['maxhp']} ХП\n"
                     "При отходе каждый унесёт находки двух залов. При гибели вся добыча похода пропадёт. "
                     "При равенстве голосов путь решит монета.\n\n"+r["log"],rows)
    if "votes" in r:
        votes=r["votes"]
        choices=forks.options(r)
        if "path_coin" in r:
            path=r["path_coin"]
            face="Орёл" if path==next(iter(choices)) else "Решка"
            return reply(f"{title(r)} · развилка\nОтряд не договорился и выбрал подбросить монету.\n\n{face} — {choices[path].label}.",
                         [[btn(choices[path].label,f"pathok:{suffix}")]])
        rows=[[btn(choice.label+(f" · {list(votes.values()).count(path)}" if len(r["party"])>1 else ""),f"{path}:{suffix}")] for path,choice in choices.items()]
        text=title(r)+" · развилка\n\n"+forks.PLACES[forks.key(r)][0]
        for path in choices.values():
            text+="\n\n"+path.label+" — "+path.promise
        if len(r["party"])>1:
            rows.append([btn("Подвести итог через минуту",f"closevote:{suffix}")])
            text+="\n\nПри ничьей путь определит монета."
        return reply(text+"\n\n"+r["log"],rows)
    if r.get("route") and r["room"]==1: stage += " · "+forks.options(r)[r["route"]].label
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
    skill_label="Умение · 4 эн."
    stamina_line = ""
    if viewer in r["party"]:
        cap = energy(s["heroes"][viewer])
        skill_label=CLASSES[h["class"]][1]
        remaining=r.get("ready",{}).get(viewer,0)-r["round"]
        status=f"с раунда {r['round']+remaining}" if remaining>0 else ("нужно 4 эн." if r.get("energy",{}).get(viewer,cap)<4 else "готово · 4 эн.")
        stamina_line = f" · твоя энергия: {r.get('energy',{}).get(viewer,cap)}/{cap}\n{skill_label} · {status}"
    if r.get("bell_raised"): effects.append("Поверенный поднял гирю. Один герой может блоком прикрыть отряд от добавочного урона.")
    active = ("\nПеред ходом: "+", ".join(effects)) if effects else ""
    divider = "\n\n────────────\n\n"
    ready = sum(uid in r["moves"] for uid in r["party"])
    log = r.get("log") or ""
    return reply(f"{title(r)}{stage} · раунд {r['round']}\n{monster(z,n)} · ур. {r.get('road_level',rank(z,n))} · {r['enemy']} ХП\n"
                 f"{encounter_trait(z,n)[0]} · {encounter_trait(z,n)[1]}\n\nОтряд: {r['hp']}/{r['maxhp']} ХП{stamina_line}{active}"
                 + (divider + log if log else "") + divider + f"Действия сейчас · {ready}/{len(r['party'])} готовы\n{actions_text(s,r)}",
                 [[btn(t,f"{a}:{suffix}") for t,a in (("Удар","hit"),("Блок","block"),(skill_label,"skill"))],
                  [btn(label,f"{k}:{suffix}") for k,label in (("heal","Лечение"),("fury","Ярость"),("ward","Кожа"))],
                  [btn("Завершить по таймеру",f"finish:{suffix}")]] + supply_rows + confirm)

def roll_equipment(z,n,mode,cls=None):
    pools=equipment_pools(z,n,mode,cls)
    return random.choice(random.choices(list(pools.values()),weights=[TIER_WEIGHTS[mode][t] for t in pools])[0])

def equipment_pools(z,n,mode,cls):
    pools={}
    for k in loot_slots(z,n,cls):
        pools.setdefault(RARITY[z,k],[]).append(k)
    return pools

COIN_CHANCE = 0.35

def loot_description(z,n,mode,cls=None):
    lines=[]
    pools=equipment_pools(z,n,mode,cls)
    total=sum(TIER_WEIGHTS[mode][t] for t in pools)
    for tier,slots in sorted(pools.items()):
        chance=100*equipment_chance(mode,n)*TIER_WEIGHTS[mode][tier]/total
        lines.append(f"{TIERS[tier]} · {chance:.2f}%\n"+"\n".join("• "+gear_names(z)[k] for k in slots))
    lines.append("Материалы ремесла · "+("обломки упряжи" if is_humanoid(z,n) else "шкура"))
    return "\n\n".join(lines)

def resolve(s,r,viewer=None):
    z,n = r["z"],target(r)
    enemy_lv = r.get("road_level",rank(z,n))
    party = [s["heroes"][i] for i in r["party"]]
    dmg = shield = heal = cracks = hits = 0
    effect=r.get("fork_effect")
    boss=r["mode"]!="hunt" and r["room"]==2
    answers=r.get("boss_answers",0)
    rolls = {}
    split_bonus = 0
    poisons = {}
    stamina = r.setdefault("energy",{})
    for i,h in zip(r["party"],party):
        lv = level(h)
        a = r["moves"].get(i,"block")
        cap = energy(h)
        stamina[i] = min(cap,stamina.get(i,cap)+(-4 if a=="skill" else 3 if a=="block" else 1))
        effects = r.get("buffs",{}).get(i,{})
        if effects.get("regen",0)>=r["round"]: heal += city.restore(4+lv//3,city.buff(s))*(110 if forks.active(h,"cup") else 100)//100
        if effects.get("venom",0)>=r["round"]: poisons[i] = 6+lv//3
        if effects.get("iron",0)>=r["round"]: shield += 12+lv
        elif effects.get("ward",0)>=r["round"]: shield += 5+lv//2
        if a=="block":
            if h["gear"][LEFT]==SEAM_SHIELD and i not in r.get("seam_used",[]):
                r.setdefault("seam_ready",{})[i]=True
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
            if c=="guard":
                shield += 9+lv+3*mastery+bonus(h,"guard")
                if h["gear"][LEFT]==SEAM_SHIELD and r.get("seam_ready",{}).pop(i,False):
                    shield+=4
                    r.setdefault("seam_used",[]).append(i)
            elif c=="nun": heal += 10+lv+3*mastery+bonus(h,"medicine")
            elif c=="archer": base += 7+lv+stats(h)[1]//2+3*mastery
            elif c=="smith": split_bonus += 3+lv//2+mastery
            else:
                shield += 5+lv//2+mastery
                base += 4+lv//2+2*mastery
        amount = random.randint(*bounds(base))
        critical = random.randrange(100)<crit(h)+(15 if boss and not answers and effect=="crit" else 0)
        if a=="hit" and not critical and forks.active(h,"measure") and i not in r.get("measured",[]):
            amount=bounds(base)[1]
            r.setdefault("measured",[]).append(i)
        rolls[i]=(amount*multiplier(h)//100 if critical else amount,critical)
    sealed = r.get("sealed",0)==r["round"]
    group = faction(z,n)
    absorbs = group=="oath" or (group is None and n%3==1)
    absorb = (2+enemy_lv//5)*len(party) if not sealed and absorbs and r["round"]%2==0 else 0
    details=[]
    for i in r["party"]:
        amount,critical=rolls.get(i,(0,False))
        if i in rolls: amount+=split_bonus
        amount+=poisons.get(i,0)
        gap=max(0,enemy_lv-level(s["heroes"][i])-1)
        amount=amount*100//(100+10*gap)
        dmg+=amount
        if r["moves"].get(i)=="skill" and s["heroes"][i]["class"]=="archer":
            details.append(f"Меткий выстрел · {s['heroes'][i]['name']} нанёс {amount} урона до поглощения.")
        if critical:
            details.append(f"Критический удар · {s['heroes'][i]['name']}")
    if split_bonus: details.append(f"Раскол брони · +{split_bonus} к каждому удару до поправки на уровень.")
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
        dungeon = r["mode"]!="hunt"
        city_news = city.victory(s,r["party"],z,n,r["mode"],fight=r if dungeon else None)
        if dungeon:
            bags=r.setdefault("haul",{})
            projected=[haul.preview(h,bags.setdefault(uid,{})) for uid,h in zip(r["party"],party)]
            originals=deepcopy(projected)
        else:
            projected=party
        scraps = [city_news] if city_news else []
        for who,h in zip(r["party"],projected):
            needed=needs(s,who)
            scraps.extend(f"{h['name']}: {material}" for material in workshops.drops(h,z,n,r["mode"],needed))
            if is_humanoid(z,n) and random.random() < COIN_CHANCE:
                copper = random.randint(1, 3)
                h["wallet"] += copper
                scraps.append(f"{h['name']}: [Монеты] +{copper} мед.")
            note=find_note(h,z,n,r["mode"])
            if note: scraps.append(f"{h['name']}: [Записки] «{note}»")
            roll=random.random()
            material=f"{z}.{99 if roll<0.06 else n}"
            protected=h["junk"].get(material,0)<needed.get(material,0)
            piece = collect(h,z,n,roll,needed)
            if piece:
                tag="" if piece=="сумка полна" else ("[Задания и ремёсла] " if protected else "[Хлам] ")
                scraps.append(f"{h['name']}: {tag}{piece}")
            if random.random()<equipment_chance(r["mode"],n):
                k = roll_equipment(z,n,r["mode"],h["class"])
                item = gear_names(z)[k]
                label = f"[{category(z,k)}] "+tier_name(z,k)+" · "+item+" — "+item_slot_label(z,k)
                if item not in h["items"]:
                    h["items"][item] = [gear_stat(z,k),strength(z,k)]
                elif r["mode"]=="hunt":
                    label += " (уже есть)"
                else:
                    recipients=[i for i,member in zip(r["party"],projected) if item not in member["items"]]
                    if recipients and r["mode"]=="raid":
                        ticket=secrets.token_hex(6)
                        h.setdefault("spare_drops",{})[ticket]=[z,k,recipients]
                        label+=" · повтор на выбор в сумке → Трофеи походов"
                    else:
                        payment = 4*trade_value(z,k)
                        h["wallet"] += payment
                        label += f" (повтор: +{payment} мед.)"
                scraps.append(f"{h['name']}: {label}")
            book = s["heroes"][who].setdefault("book",{})
            key = f"{z}.{n}"
            book[key] = book.get(key,0)+1
        if r.get("route")=="pits" and r["room"]==1:
            for who,h in zip(r["party"],projected):
                if units(h,needs(s,who))<capacity(h):
                    h["junk"]["6.98"]=h["junk"].get("6.98",0)+1
                    scraps.append(h["name"]+": [Хлам] связка выделанных шкур")
                else:
                    payment,h["sale_tenths"]=scrap_payment(h,12,city.buff(s))
                    h["wallet"]+=payment
                    scraps.append(f"{h['name']}: шкуры проданы за {payment} мед. (сумка полна)")
        if dungeon:
            for uid,before,after in zip(r["party"],originals,projected):
                haul.store(bags[uid],before,after)
        if r["mode"]=="hunt" or r["room"]==2:
            del s["fights"][r["id"]]
            for member in party:
                member["returning_from_fight"] = True
            haul.bank(s,r)
            reward=forks.pay(s,r)
            lines = [f"Победа · {title(r)}",msg] + ([reward] if reward else []) + scraps
            completed_at = time.time()
            for h in party:
                if (r["mode"],z,r["choice"])==("raid",6,0):
                    h["buckles"]=h.get("buckles",0)+1
                    lines.append(f"{h['name']}: [Трофеи] пряжка Кожевен · всего {h['buckles']}. Пять принимает мастер у моря.")
                lv = level(h)
                base_xp, source = victory_xp(h,r,enemy_lv,completed_at)
                xp = min(LIMITS[-1]-h["xp"],city.earned(base_xp,city.buff(s),h))
                h["xp"] += xp
                h["peak"] = max(level(h),h.get("peak",1))
                up = f" · уровень {level(h)}!" if level(h)>lv else ""
                lines.append(f"{h['name']}: +{xp} опыта{up}" + (f" · {source}" if source else ""))
            return reply("\n".join(lines),return_route(r))
        if r.get("route")=="loft" and r["room"]==1:
            r["cut_chain"]=True
            msg+=" Отряд сорвал цепь с балки."
        if dungeon and r["room"]==0:
            r["votes"]={}
        r["room"] += 1
        if r["room"]==2:
            r["exit_votes"]={}
            if effect=="energy":
                for uid,h in zip(r["party"],party): stamina[uid]=min(energy(h),stamina[uid]+3)
                msg+=" У печи каждый восстановил до 3 энергии."
        r["enemy"] = maximum(r)
        if (r["mode"],z,r["room"])==("vault",8,2) and effect!="bell": r["bell_raised"]=True
        r["hp"] = min(r["maxhp"],r["hp"]+sum(4+level(h)//2 for h in party))
        msg += " Враг повержен. Отряд перевёл дух."
        if scraps: msg += "\nНаходки до выхода: "+" · ".join(scraps)
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
        if boss and effect:
            r["boss_answers"]=answers+1
            if forks.key(r) in ("0_1","5_0") and answers==(2 if effect=="delay" else 0):
                raw+=4+enemy_lv//3
                msg+=" Босс нанёс тяжёлый удар."
            if forks.key(r)=="3_0" and not answers:
                if effect=="strap": msg+=" Упряжь распалась в руках Смотрителя."
                else:
                    for uid in stamina: stamina[uid]=max(0,stamina[uid]-2)
                    msg+=" Ремни затянулись: −2 энергии."
        gap=max(0,enemy_lv-sum(level(h) for h in party)//len(party)-1)
        raw=raw*(100+12*gap)//100
        if r.pop("bell_raised",False):
            if any(r["moves"].get(i,"block")=="block" for i in r["party"]): msg+=" Удар гири принят на блок."
            else:
                raw+=enemy_lv//2
                msg+=" Гиря ударила с размаху."
        taken = max(0,random.randint(*bounds(raw*len(party)))-shield)
        if boss and effect=="bell" and answers==1:r["bell_raised"]=True
        if boss and not answers:
            if effect=="skip" or (effect=="block" and any(r["moves"].get(i,"block")=="block" for i in r["party"])):
                taken=0
                msg+=" Выбранный путь сорвал ответ босса."
            if effect=="half":taken//=2
        if effect=="roomskip" and r["room"]==1 and not r.get("roomskip_used"):
            taken=0
            r["roomskip_used"]=True
            msg+=" Носильщик ещё выбирается из складок сукна."
        if r.pop("cut_chain",False):
            taken=0
            msg+=" Мастер дёрнул крюк. Оборванная цепь рухнула на пол."
        if taken and r.get("first_hit_room")!=r["room"]:
            r["first_hit_room"]=r["room"]
            if city.buff(s)=="papers":
                taken=taken*85//100
                msg+=" Караульный строй смягчил первый удар."
        if taken and not r.get("rivet_used"):
            owners=sum(forks.active(h,"rivet") for h in party)
            if owners:
                taken=taken*(100*len(party)-20*owners)//(100*len(party))
                r["rivet_used"]=True
        if taken>=r["hp"] and any(forks.active(h,"reprieve") for h in party):
            for h in party:
                if forks.active(h,"reprieve"): h.pop("route_relic",None)
            taken=max(0,r["hp"]-1)
            msg+=" Вторая запись сохранила отряду 1 ХП."
        r["hp"] -= taken
        msg += f" Ответный удар — {taken}."
        if r["hp"]<=0:
            del s["fights"][r["id"]]
            for member in party:
                member["returning_from_fight"] = True
                member.pop("hunting_ground",None)
                member.pop("coast_trip",None)
            if r.get("legacy_safe"):
                return reply("Отряд погиб. В этом перенесённом походе потерь нет.\n"+msg)
            lost=" Добыча этого похода потеряна." if r["mode"]!="hunt" else ""
            return reply("Отряд погиб. Герои вернулись в Гусзк."+lost+"\n"+msg+"\n"+"\n".join(death(h) for h in party))
    r.update(round=r["round"]+1,moves={},used={},heal_requests={},deadline=time.time()+60,log=msg)
    return board(s,r,viewer)

def atlas(mode,h,band=None):
    if band is None:
        bands=sorted({BANDS[z] for z in VAULTS}) if mode=="vault" else range(6)
        buttons=[btn(f"{b*10+1}–{b*10+10}"+(" ◆" if (level(h)-1)//10==b else ""),
                     f"band:{mode}:{b}") for b in bands]
        return reply("Выбери уровни. ◆ — твой диапазон.",[buttons[i:i+2] for i in range(0,len(buttons),2)])
    rows = []
    for z,half in sorted(((z,i) for z in range(len(ZONES)) for i in (0,1)),key=lambda v:(BANDS[v[0]],v[1],v[0])):
        if BANDS[z]!=band: continue
        if mode=="vault" and (z not in VAULTS or not half): continue
        low=required_level(z)+5*half
        mark=" ◆" if low<=level(h)<=low+4 else ""
        rows.append([btn(f"{area_name(z,half)} · {low}–{low+4}{mark}",f"area:{mode}:{z}:{half}")])
    rows.append([btn("‹ Все уровни","nav:"+mode)])
    return reply(f"Локации · уровни {band*10+1}–{band*10+10}",rows)

def area(mode,z,h,half=0):
    name, beasts, raids, items = ZONES[z]
    name=area_name(z,half)
    low=required_level(z)+5*half
    hunts=[n for n in HUNT_IDS if low<=rank(z,n)<=low+4]
    if mode=="book":
        rows = []
        total = 0
        count = 12 if z in VAULTS else 9
        for n in (*range(count),*EXTRA_HUNT_IDS):
            if not low<=rank(z,n)<=low+4: continue
            kills = h.get("book",{}).get(f"{z}.{n}",0)
            total += bool(kills)
            rows.append([btn(f"{monster(z,n)} · {kills} побед",f"entry:{z}:{n}")])
        return reply(f"Бестиарий · {h['name']} · {name} · побеждено видов {total}/{len(rows)}",rows)
    if mode=="vault":
        if z not in VAULTS: return reply("Выбери тайник в разделе «Тайники».")
        return reply(f"{VAULTS[z][0]} · ур. {rank(z,9)}–{rank(z,11)}\nКлючей: {h['keys'].get(str(z),0)} · ключи продаются в городе\nСнаряжение за босса: 50%. Возможные находки: "+", ".join(gear_names(z)[k] for k in loot_slots(z,11,h["class"])),
                     [[btn("Подготовиться ко входу",f"new:vault:{z}:0")]])
    if mode=="zones":
        return reply(f"{name} · уровни {low}–{low+4}\n{ZONE_NOTES[name]}\nОхота: {', '.join(monster(z,n) for n in hunts)}\nПодземелье: {raids[half][0]}",
                     [])
    if mode=="hunt":
        rows = [[btn(f"{monster(z,j)} · ур. {rank(z,j)}",f"new:hunt:{z}:{j}")] for j in sorted(hunts,key=lambda n:rank(z,n))]
    else:
        rows = [[btn(f"{v[0]} · ур. {rank(z,3+3*j)}–{rank(z,5+3*j)}",f"new:raid:{z}:{j}")] for j,v in enumerate(raids) if j==half]
    return reply(f"{name} · выбери цель",rows)

def gear_description(h,z,k,item):
    power=effective_power(h,item)
    unit="к удару" if h["items"][item][0]==0 else "ХП"
    legacy=" · наследие" if (z,k) not in ORIGIN else ""
    lines=[f"{item}{legacy} — {item_slot_label(z,k)}", f"{tier_name(z,k)} · ур. {wear_level(z,k)}"]
    if item in ARM_BY_NAME:
        cls=ARM_BY_NAME[item][0]
        lines[1]+=" · "+CLASSES[cls][0]+(" · ½ силы" if cls!=h["class"] else "")
    bonuses=[f"+{power} {unit}"]
    if item in ITEM_TRAITS:
        idx,value=ITEM_TRAITS[item]
        bonuses.append(f"{STAT_NAMES[idx]} +{value}")
    bonuses.append(bonus_label(h,item))
    return "\n".join(lines+[" · ".join(bonuses)])

def inventory(h,uid,slot=None,page=0,needed=None,active=None):
    needed=needed or {}
    if slot is None:
        rows = []
        buttons = []
        for j in SLOT_ORDER:
            buttons.append(btn(SLOTS[j],f"slot:{uid}:{j}"))
        rows = [buttons[j:j+2] for j in range(0,len(buttons),2)]
        worn=set(h["gear"])
        items=[item for item in reversed(h["items"]) if item not in worn]
        page_size=3
        pages=max(1,(len(items)+page_size-1)//page_size)
        page=min(page,pages-1)
        overview=[]
        for item in items[page*page_size:(page+1)*page_size]:
            z,k=map(int,ITEM_CODES[item].split("."))
            overview.append(gear_description(h,z,k,item))
        if pages>1:
            rows.insert(0,[btn(label,f"bag:{target}") for label,target in
                           (("‹ Новее",page-1),("Старее ›",page+1)) if 0<=target<pages])
        if h.get("buckles") or h.get("spare_drops"): rows.append([btn("Трофеи походов","spoils")])
        rows.append([btn("Хлам и материалы","materials"),btn("Ремесленные запасы","work:forge:materials")])
        stock = [f"{v[0]} ×{h['potions'][k]}" for k,v in POTIONS.items() if h["potions"].get(k)]
        rows.append([btn("Скупщик","shop:"+uid+":"+revision(h,active)+":sell")])
        heading=f"Запасное снаряжение · {len(items)}"
        if pages>1: heading+=f" · стр. {page+1}/{pages}"
        return reply(heading+"\n\n"+("\n\n".join(overview) if overview else "Запасных вещей пока нет.")+
                     f"\n\nСумка {units(h,needed)}/{capacity(h)} · {h['wallet']} мед.\nРасходники: "+(", ".join(stock) or "пусто"),rows)
    worn = h["gear"][slot]
    label_worn = worn
    sources = []
    rows = []
    for z in range(len(ZONES)):
        for k,item in enumerate(gear_names(z)):
            if gear_slot(z,k)!=(7 if slot in RINGS else slot): continue
            if item not in h["items"]:
                if (z,k) in CLASS_PIECES and CLASS_PIECES[z,k][2]!=h["class"]: continue
                idx = next((n for n in (0,5,8,11) if k in loot_slots(z,n,h["class"])),None)
                if idx is None:continue
                if idx==0: idx = min((0,1,2),key=lambda n:abs(rank(z,n)-level(h)))
                sources.append((abs(rank(z,idx)-level(h)),z,idx,item))
                continue
            label=gear_description(h,z,k,item)
            if item!=worn:
                if item in h["gear"]: label += " · "+SLOTS[h["gear"].index(item)]
                rows.append([btn(label,f"dress:{uid}:{slot}:{z}:{k}")])
            else: label_worn = label
    pages=max(1,(len(rows)+2)//3)
    page=min(page,pages-1)
    listed=rows[page*3:page*3+3]
    lines=[f"{3*page+i}. {row[0]['text']}" for i,row in enumerate(listed,1)]
    rows=[[btn(str(3*page+i),row[0]["callback_data"]) for i,row in enumerate(listed,1)]] if listed else []
    if pages>1:
        rows.append([btn(f"Страница {i+1}/{pages}",f"slot:{uid}:{slot}:{i}") for i in (page-1,page+1) if 0<=i<pages])
    if sources:
        _,z,n,item = min(sources)
        rows.append([btn("Где найти · "+item,f"entry:{z}:{n}")])
    if slot==LEFT and two_handed(h["gear"][RIGHT]):
        return reply("Обе руки заняты: "+h["gear"][RIGHT],[[btn("Правая рука",f"slot:{uid}:{RIGHT}")],[btn("К ячейкам","nav:bag")]])
    if worn: rows.append([btn("Снять в сумку",f"off:{uid}:{slot}")])
    rows.append([btn("К ячейкам","nav:bag")])
    return reply(f"{SLOTS[slot]} · "+(label_worn if worn else "пусто")+"\n\n"+("\n\n".join(lines) if lines else "В сумке нет других вещей для этой ячейки."),rows)

def play(s,uid,name,cmd):
    migrate(s)
    heroes,fights = s["heroes"],s["fights"]
    h = heroes.get(uid)
    p = cmd.split(":")
    op = p[0]
    if op=="writ" and h: return forks.lots(s,uid,*p[1:3])
    if op=="notes": return collection(h or {},p[1:])
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
        return reply(f"{CLASSES[h['class']][0]} · ур. {lv}/60\n{xp}\n\nВ бою\n"
                     f"Удар: {bounds(attack(h))[0]}–{bounds(attack(h))[1]} · крит: {crit(h)}% ×{multiplier(h)/100:.2f}\nЗдоровье: {health(h)} · запас энергии: {energy(h)}\n\nХарактеристики\n"+
                     " · ".join(f"{n}: {v}" for n,v in zip(STAT_NAMES,stats(h)))+f"\nСмертей: {h.get('deaths',0)}"+diary,
                     ([[btn("Общее дело Гусзка","city")]]+([[btn("Грамоты походов","writ")]] if h.get("writs") or h.get("writ_news") or any(uid in lot["members"] for lot in s.get("writ_lots",{}).values()) else []) if op=="diary" else [])+[[btn(f"Навыки · {points(h)} очк.","nav:skills")],[btn("История и умение","bio:"+h["class"])]])
    if op=="class" and len(p)==3 and p[2] in CLASSES:
        if uid!=p[1]: return reply("Это чужой лист героя.")
        if h: return reply("Твой герой уже выбрал класс.")
        heroes[uid] = dict(name=name,xp=0,items={},gear=[None]*len(SLOTS),**{"class":p[2]})
        setup(heroes[uid])
        return reply(f"Класс выбран.\n{name} · {CLASSES[p[2]][0]}")
    if not h: return reply("Выбери класс в разделе «Герой».")
    mine = next((r for r in fights.values() if uid in r["party"]),None)
    if op=="work":
        if p[1:]==["camp"]:
            return play(s,uid,name,"road") if h.get("coast_trip") else reply("Лагерь остался позади.")
        if p[1:]==["hero"]:return reply("Герой",[[btn("Лист персонажа","nav:diary"),btn("Сумка","nav:bag")]])
        return workshops.view(h,p[1:],bool(mine),needs(s,uid))
    if op in ("road","roadfight","craft"):
        if mine: return board(s,mine,uid)
        if op=="road":
            returning=h.get("coast_trip",{}).get("returning")
            text,rows=road(h,p[1:])
            if returning and not h.get("coast_trip"):
                return market(h,uid,note="Дорога в Гусзк · 3/3\n"+text,active=city.buff(s),needed=needs(s,uid))
            return text,rows
        if op=="craft": return craft(h,p[1:],city.buff(s))
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
    if op=="city": return city.card(s,uid,p[1:],busy=bool(mine))
    if op=="orders":
        if mine and mine["round"]: return reply("Комендант ждёт тебя в городе после боя.")
        return desk(s,uid,p[1:])
    if op in ("town","shop"):
        if mine:return board(s,mine,uid)
        if op=="town":
            h.pop("coast_trip",None)
            return market(h,uid,active=city.buff(s),needed=needs(s,uid))
        return trade(h,uid,p,city.buff(s),needs(s,uid))
    if op in ("barter","nearby"): return exchange(s,uid,cmd)
    if op=="spoils": return spoils(s,uid,p[1:])
    if op=="materials":
        needed=needs(s,uid)
        lines=[]
        for key,v in h["junk"].items():
            reserved=min(v,needed.get(key,0))
            if reserved:lines.append(f"[Задания и ремёсла] {material_name(key)} ×{reserved}")
            if v>reserved:lines.append(f"[Хлам] {material_name(key)} ×{v-reserved}")
        project=s.get("city_project",{})
        for (label,_),v in zip(city.GOALS.get(project.get("kind"),()),project.get("cargo",{}).get(uid,())):
            if v:lines.append(f"[Задания] {label} ×{v}")
        return reply("\n".join(lines) or "Материалов пока нет.",[[btn("К сумке","nav:bag")]])
    if op=="bag":
        page=int(p[1]) if len(p)==2 and p[1].isascii() and p[1].isdigit() and len(p[1])<=6 else 0
        return inventory(h,uid,page=page,needed=needs(s,uid),active=city.buff(s))
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
            if level(h)<wear_level(z,k): return reply(f"Нужен уровень {wear_level(z,k)}.")
            if slot==LEFT and two_handed(h["gear"][RIGHT]): return reply("Сначала сними двуручное оружие.")
            if two_handed(item) and h["gear"][LEFT]: return reply("Для этого оружия нужны обе руки. Сначала сними предмет с левой руки.")
            if item in h["gear"]: h["gear"][h["gear"].index(item)] = None
            h["gear"][slot] = item
        return inventory(h,uid,slot)
    if op in MODES:
        if mine and op in ("hunt","raid","vault"): return board(s,mine,uid)
        return atlas(op,h)
    if op=="band" and len(p)==3 and p[1] in MODES and p[2] in tuple(map(str,range(6))):
        return atlas(p[1],h,int(p[2]))
    if op in ("travel","journey") and len(p)==3 and p[1] in DIGITS and p[2] in ("0","1"):
        if mine:return board(s,mine,uid)
        z,half=int(p[1]),int(p[2])
        location=area_name(z,half)
        moved=h.get("hunting_ground")!=location or bool(h.get("coast_trip"))
        h.pop("coast_trip",None)
        h["hunting_ground"]=location
        if op=="journey" and moved and random.random()<ROAD_ENCOUNTER_CHANCE:
            candidates=[n for n in HUNT_IDS if encounter_area(z,n)==location]
            enemy=random.choice(candidates)
            key=secrets.token_hex(5)
            fights[key]=dict(id=key,mode="hunt",z=z,choice=enemy,room=0,round=0,party=[uid])
            text,rows=play(s,uid,name,"go:"+key)
            return reply(f"Случайная встреча · {location}\nПуть преграждает {monster(z,enemy)}.\n\n"+text,rows)
        text,_=area("zones",z,h,half)
        rows=[[btn("Охота",f"area:hunt:{z}:{half}"),btn("Подземелья",f"area:raid:{z}:{half}")]]+([[btn(VAULTS[z][0],f"area:vault:{z}:1")]] if z in VAULTS and half else [])
        return reply("Ты на месте. "+text,rows+[[btn("Вернуться в Гусзк","nav:town")]])
    if op=="area" and (len(p)==3 or len(p)==4 and p[3] in ("0","1")) and p[1] in MODES and p[2] in DIGITS:
        z=int(p[2])
        text,rows=area(p[1],z,h,int(p[3]) if len(p)==4 else int(p[1]=="vault"))
        if p[1]=="zones" and not mine:
            half=int(p[3]) if len(p)==4 else 0
            rows.insert(0,[btn("Отправиться сюда",f"journey:{z}:{half}")])
        return text,rows+[[btn("‹ К локациям",f"band:{p[1]}:{BANDS[z]}")]]
    if op in ("entry","loot") and len(p)==3 and p[1] in DIGITS and p[2] in tuple(map(str,range(16))):
        z,n = map(int,p[1:])
        zone = ZONES[z]
        if 9<=n<12 and z not in VAULTS: return reply("Эта запись недоступна.")
        mode = "hunt" if n in HUNT_IDS else "vault" if n>=9 else "raid"
        origin = VAULTS[z][0] if mode=="vault" else "Охота" if mode=="hunt" else zone[2][(n-3)//3][0]
        if op=="loot":
            return reply("Снаряжение · "+monster(z,n)+"\n\n"+loot_description(z,n,mode,h["class"]),[[btn("‹ К противнику",f"entry:{z}:{n}")]])
        return reply(f"{monster(z,n)} · ур. {rank(z,n)}\n{encounter_area(z,n)} · {origin}\n\n{encounter_trait(z,n)[0]}: {encounter_trait(z,n)[1]}\n"
                     f"Победы: {h.get('book',{}).get(f'{z}.{n}',0)}\n" +
                     f"\nДобыча\nХлам: {SCRAPS[z][n]} · {scrap_value(z,n)} мед.\nРедкость: {CURIOS[z]} · 6%\n" + (f"Монеты: 1–3 мед. · {COIN_CHANCE:.0%}\n" if is_humanoid(z,n) else "") + ("За охоту" if mode=="hunt" else f"Зал {n%3+1}") + f" · шанс снаряжения {equipment_chance(mode,n):.0%}",[[btn("Список снаряжения",f"loot:{z}:{n}")],[btn("Назад",f"area:book:{z}:{int((rank(z,n)-1)%10>=5)}")]])
    if op in ("new","separate") and len(p)==4 and p[1] in ("hunt","raid","vault") and p[2] in DIGITS:
        if mine: return board(s,mine,uid)
        mode = p[1]
        if p[3] not in tuple(map(str,HUNT_IDS if mode=="hunt" else (0,1))): return reply("Выбери цель заново.")
        if mode=="vault" and (int(p[2]) not in VAULTS or p[3]!="0"): return reply("Выбери тайник в разделе «Тайники».")
        if op=="new" and mode!="vault":
            available=[r for r in fights.values() if r["mode"]==mode and r["z"]==int(p[2])
                       and r["choice"]==int(p[3]) and not r["round"] and 0<len(r["party"])<6]
            if available:
                rows=[[btn(f"Вступить · {heroes[r['party'][0]]['name']} · {len(r['party'])}/6","join:"+r["id"])] for r in available[:6]]
                rows.append([btn("Создать свой сбор",f"separate:{mode}:{p[2]}:{p[3]}")])
                return reply(title(available[0])+" · идёт сбор. Выбери отряд.",rows)
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
            if len(r["party"])>=6: return reply("В отряде уже шесть героев.")
            h.pop("coast_trip",None)
            r["party"].append(uid)
        elif op=="join" and mine is r:
            return reply("Ты уже в отряде. Для начала нажми «Начать бой».",board(s,r,uid)[1])
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
    if len(p)!=(4 if op=="healok" else 3) or p[2]!=str(r["round"]):
        text,rows=board(s,r,uid)
        return reply("Раунд сменился. Выбери действие для текущего раунда.\n\n"+text,rows)
    if "exit_votes" in r:
        votes=r["exit_votes"]
        if "exit_coin" in r:
            if op!="coinok": return board(s,r,uid)
            decision=r.pop("exit_coin")
        else:
            if op in ("turnback","faceboss"):
                votes[uid]=op
            elif op!="exitfinish" or time.time()<r["deadline"] or not votes:
                return board(s,r,uid)
            if len(votes)<len(r["party"]) and op!="exitfinish": return board(s,r,uid)
            forward=list(votes.values()).count("faceboss")
            if 2*forward==len(votes):
                r["exit_coin"]=random.choice(("faceboss","turnback"))
                return board(s,r,uid)
            decision="faceboss" if 2*forward>len(votes) else "turnback"
        if decision=="turnback":
            haul.bank(s,r)
            reward=forks.pay(s,r)
            del fights[r["id"]]
            for member in r["party"]: heroes[member]["returning_from_fight"]=True
            return reply(f"Отряд вернулся · {title(r)}\nНаходки очищенных залов перенесены в сумки. Зачистка босса не засчитана."+("\n"+reward if reward else ""),return_route(r))
        del r["exit_votes"]
        r.update(deadline=time.time()+60,log="Отряд вошёл в зал босса.")
        return board(s,r,uid)
    if op in ("turnback","faceboss","exitfinish","coinok"): return board(s,r,uid)
    if "votes" in r: return vote_route(s,r,uid,op)
    if op in ROUTES or op in ("closevote","pathok"): return reply("Путь уже выбран.")
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
            healed = min(r["maxhp"]-r["hp"],city.restore(12+2*level(h) if op=="heal" else 35+3*level(h),city.buff(s))*(110 if forks.active(h,"cup") else 100)//100)
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
    if op=="skill" and r["ready"].get(uid,0)>r["round"]: return reply(f"Умение будет доступно в раунде {r['ready'][uid]}.")
    r["moves"][uid] = op
    if len(r["moves"])==len(r["party"]): return resolve(s,r,uid)
    return board(s,r,uid)

MODES = ("hunt","raid","book","zones","vault")
DIGITS = tuple(map(str,range(len(ZONES))))
