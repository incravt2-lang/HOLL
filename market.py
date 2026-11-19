"""Per-hero economy. Buttons bind purchases to the customer and wallet revision."""
import random
import time
from world import tier_name,bonus_label,CODE_ITEMS, ITEM_TRAITS, STAT_NAMES, SLOTS, gear_slot, gear_stat
from world import level, BANDS, VAULTS, SCRAPS, gear_names, strength

BAGS = ((8,0),(18,40),(36,110),(64,260))
POTIONS = {"heal":("Малая аптечная мера",6), "fury":("Глоток межевого перца",9), "ward":("Сусло воротного караула",9)}
POTIONS.update({
    "regen":("Белильная притирка",15), "strongheal":("Большая аптечная мера",23),
    "venom":("Лужская горечь",27), "iron":("Медницкая закалка",48),
    "rage":("Настой ночного перегона",48), "seal":("Грамота о запрете",42),
    "recall":("Выпись второй записи",64),
})
REQUIREMENT = dict(heal=1,fury=1,ward=1,regen=10,strongheal=20,venom=20,iron=40,rage=40,seal=10,recall=25)
HEALS = ("heal","strongheal")
SCROLLS = ("seal","recall")
DESCR = dict(heal="сразу +12 + 2 × уровень сил", fury="усиливает удар на 5 + половину уровня",
             ward="защищает на 5 + половину уровня",regen="лечит на 4 + треть уровня за раунд",
             strongheal="сразу +35 + 3 × уровень сил",venom="добавляет 6 + треть уровня урона даже при блоке",
             iron="защищает на 12 + уровень",rage="усиливает удар на 12 + уровень",
             seal="отключает особенность врага на текущий раунд",recall="немедленно восстанавливает твоё классовое умение")
ROOM_DROP = {"raid":(0.10,0.15,0.35),"vault":(0.15,0.22,0.50)}

def equipment_chance(mode,n):
    return 0.03 if mode=="hunt" else ROOM_DROP[mode][n%3]
CURIOS = ("Амбарная гривна","Серебряная охотничья пряжка","Брошь полевой сестры",
          "Янтарная застёжка обоза","Медная цеховая печать","Тарнская жемчужина",
          "Резная костяная игла","Кристалл чистой соли","Старинный чеканский дукат")

def wares(hour):
    # Disjoint pools on adjacent hours guarantee four genuinely new listings.
    pool = sorted(CODE_ITEMS)[hour%2::2]
    return random.Random(f"guszk-armourer-{hour}").sample(pool,4)

def asking_price(z,k):
    return 90+18*strength(z,k)

def setup(h):
    if "wallet" not in h:
        h.update(wallet=12,pack=0,junk={},potions={},keys={},shop_rev=0)

def capacity(h):
    return BAGS[h["pack"]][0]

def units(h):
    return sum(h["junk"].values())

def scrap_value(z,n):
    if n==99: return 18+4*BANDS[z]
    return 3+BANDS[z]+n//3

def key_price(z):
    return 24+12*BANDS[z]

def collect(h,z,n,roll):
    if roll>=0.6: return ""
    if units(h)>=capacity(h): return "сумка полна"
    if roll<0.06: n=99
    key = f"{z}.{n}"
    h["junk"][key] = h["junk"].get(key,0)+1
    return CURIOS[z] if n==99 else SCRAPS[z][n]

def market(h,uid,section="town",note=""):
    def row(label,action):
        return [{"text":label,"callback_data":f"shop:{uid}:{h['shop_rev']}:{action}"}]
    text = [f"Город Гусзк · {h['name']}", f"{h['wallet']} медяков · хлам {units(h)}/{capacity(h)}"]
    if note: text.append(note)
    rows = []
    if section=="town":
        rows.append([{"text":"Комендант · доска поручений","callback_data":"orders"}])
        for label,key in (("Мартин · оружейник","armourer"),("Лада · аптекарь","apoth"),("Тиш · писец","scribe"),("Вей · скупщик","sell"),("Уна · сумочник","bags"),("Рада · ключница","keys")):
            rows.append(row(label,key))
    elif section=="armourer":
        now=int(time.time())
        hour=now//3600
        text.append(f"Лавка Мартина · новый обоз через {(3600-now%3600+59)//60} мин.")
        for code in wares(hour):
            z,k=map(int,code.split("."))
            item=CODE_ITEMS[code]
            power=strength(z,k)
            bonus=f"+{power} к удару" if gear_stat(z,k)==0 else f"+{4*power} к здоровью"
            if item in ITEM_TRAITS:
                idx,value=ITEM_TRAITS[item]
                bonus+=f" · {STAT_NAMES[idx]} +{value}"
            bonus+=" · "+bonus_label(h,item)
            price=asking_price(z,k)
            text.append(f"{tier_name(z,k)} · {item} · {SLOTS[gear_slot(z,k)]} · {bonus} · {price} мед.")
            if item not in h["items"]:
                rows.append(row("Купить · "+item,f"stock-{hour}-{code}"))
        rows.append(row("Обновить прилавок","armourer"))
    elif section in ("apoth","scribe"):
        text.append("Один расходник за раунд. Один свиток на героя за поход." if section=="scribe"
                    else "Один расходник за раунд. Настои действуют три раунда. Одинаковый тип усиления заменяет прежний.")
        for k,(name,cost) in POTIONS.items():
            if (k in SCROLLS)!=(section=="scribe"): continue
            req = REQUIREMENT[k]
            text.append(f"{name} · ур. {req} · {DESCR[k]}.")
            if level(h)>=req:
                rows.append(row(f"{name} · {cost} мед. · в запасе {h['potions'].get(k,0)}","buy-"+k))
    elif section=="bags":
        if h["pack"]+1<len(BAGS):
            size,price = BAGS[h["pack"]+1]
            rows.append(row(f"Купить сумку на {size} · {price} мед.","upgrade"))
        else: text.append("Куплена самая вместительная сумка.")
    elif section=="keys":
        text.append("Один ключ на один вход. Списывается при начале боя. В каждом тайнике три зала для одного героя.")
        for z,v in VAULTS.items():
            rows.append(row(f"{v[0]} · {key_price(z)} мед. · ключей {h['keys'].get(str(z),0)}",f"key-{z}"))
    elif section=="sell" or section.startswith("sellpage"):
        page = int(section[8:]) if section.startswith("sellpage") else 0
        equipment = []
        total = 0
        for key,count in h["junk"].items():
            z,n = map(int,key.split("."))
            price = scrap_value(z,n)
            text.append(f"{CURIOS[z] if n==99 else SCRAPS[z][n]} ×{count} · по {price} мед.")
            total += count*price
        if total: rows.append(row(f"Продать весь хлам · +{total} мед.","cash"))
        for z in range(len(BANDS)):
            for k,item in enumerate(gear_names(z)):
                if item in h["items"] and item not in h["gear"]:
                    equipment.append(row(f"Продать {item} · +{4*strength(z,k)} мед.",f"gear-{z}-{k}"))
        rows.extend(equipment[page*12:(page+1)*12])
        if page: rows.append(row("Предыдущие вещи",f"sellpage{page-1}"))
        if (page+1)*12<len(equipment): rows.append(row("Следующие вещи",f"sellpage{page+1}"))
        if not rows: text.append("Хлама и запасного снаряжения для продажи нет.")
    if section!="town": rows.append(row("К торговой площади","town"))
    return "\n".join(text),rows

def trade(h,uid,p):
    if len(p)!=4 or p[1]!=uid: return "Открой город в своей карточке.",[]
    if p[2]!=str(h["shop_rev"]): return "Цены и запасы на этой карточке устарели. Вернись в город через меню.",[]
    action = p[3]
    if action in ("town","apoth","sell","keys","bags","scribe","armourer"): return market(h,uid,action)
    if action.startswith("sellpage") and action[8:] in tuple(map(str,range((sum(len(gear_names(z)) for z in range(len(BANDS)))+11)//12))): return market(h,uid,action)
    key = action.split("-")
    delta = 0
    if len(key)==3 and key[0]=="stock":
        hour=int(time.time())//3600
        if key[1]!=str(hour) or key[2] not in wares(hour):
            return market(h,uid,"armourer","Обоз сменился. Выбери вещь с нового прилавка.")
        z,k=map(int,key[2].split("."))
        item=CODE_ITEMS[key[2]]
        cost=asking_price(z,k)
        if item in h["items"]: return market(h,uid,"armourer","Эта вещь у тебя уже есть.")
        if h["wallet"]<cost: return market(h,uid,"armourer","Не хватает медяков.")
        h["items"][item]=[gear_stat(z,k),strength(z,k)]
        delta,section=-cost,"armourer"
    elif action=="cash":
        delta = sum(count*scrap_value(*map(int,k.split("."))) for k,count in h["junk"].items())
        h["junk"].clear()
        section = "sell"
    elif len(key)==3 and key[0]=="gear" and key[1] in map(str,range(len(BANDS))) and key[2] in map(str,range(len(gear_names(int(key[1]))))):
        z,k = map(int,key[1:])
        if k>=len(gear_names(z)): return "Предмет недоступен.",[]
        item = gear_names(z)[k]
        if item not in h["items"] or item in h["gear"]: return "Предмет сейчас недоступен для продажи.",[]
        del h["items"][item]
        delta,section = 4*strength(z,k),"sell"
    else:
        if len(key)==2 and key[0]=="buy" and key[1] in POTIONS:
            if level(h)<REQUIREMENT[key[1]]: return "Сначала повысь уровень.",[]
            section,cost,stock,sku = ("scribe" if key[1] in SCROLLS else "apoth"),POTIONS[key[1]][1],h["potions"],key[1]
        elif len(key)==2 and key[0]=="key" and key[1] in map(str,VAULTS):
            section,cost,stock,sku = "keys",key_price(int(key[1])),h["keys"],key[1]
        elif action=="upgrade" and h["pack"]+1<len(BAGS):
            section,cost = "bags",BAGS[h["pack"]+1][1]
        else: return "Вернись в город через меню.",[]
        if h["wallet"]<cost: return market(h,uid,section,"Не хватает медяков.")
        delta = -cost
        if action=="upgrade": h["pack"] += 1
        else: stock[sku] = stock.get(sku,0)+1
    h["wallet"] += delta
    h["shop_rev"] += 1
    return market(h,uid,section,f"Сделка завершена · {delta:+} мед.")
