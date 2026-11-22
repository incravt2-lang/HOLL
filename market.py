"""Per-hero economy. Buttons bind purchases to the customer and wallet revision."""
from cargo import free
from city import price
import random
import time
from world import class_power, trade_value, tier_name,bonus_label,CODE_ITEMS, ITEM_TRAITS, STAT_NAMES, SLOTS, gear_slot, gear_stat
from world import SEAM_SHIELD, wear_level, level, BANDS, VAULTS, SCRAPS, gear_names, strength

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

def wares(hour,active=None):
    # Keep the usual four listings when the city unlocks the fifth.
    pool = sorted(code for code,name in CODE_ITEMS.items() if name!=SEAM_SHIELD)[hour%2::2]
    rng = random.Random(f"guszk-armourer-{hour}")
    stock = rng.sample(pool,4)
    if active=="convoy": stock.append(rng.choice([code for code in pool if code not in stock]))
    return stock

def asking_price(z,k):
    return 90+18*trade_value(z,k)

def setup(h):
    if "wallet" not in h:
        h.update(wallet=12,pack=0,junk={},potions={},keys={},shop_rev=0)

def capacity(h):
    return BAGS[h["pack"]][0]

def units(h,needed=None):
    return sum(free(h,k,needed or {}) for k in h["junk"])

def material_name(key):
    z,n=map(int,key.split("."))
    return CURIOS[z] if n==99 else SCRAPS[z][n]

def scrap_value(z,n):
    if (z,n)==(6,98): return 12
    if n==99: return 18+4*BANDS[z]
    return 3+BANDS[z]+n//3

def key_price(z):
    return 24+12*BANDS[z]

def collect(h,z,n,roll,needed=None):
    if roll>=0.6: return ""
    if roll<0.06: n=99
    key = f"{z}.{n}"
    needed=needed or {}
    if h["junk"].get(key,0)>=needed.get(key,0) and units(h,needed)>=capacity(h): return "сумка полна"
    h["junk"][key] = h["junk"].get(key,0)+1
    return CURIOS[z] if n==99 else SCRAPS[z][n]

def purchase(cost,section,active):
    return price(cost,5) if active=="wall" or (active=="convoy" and section=="armourer") else cost

def revision(h,active):
    return str(h["shop_rev"])+(active if active in ("wall","convoy") else "")

def junk_payment(h,active,needed=None):
    base=sum(free(h,key,needed or {})*scrap_value(*map(int,key.split("."))) for key in h["junk"])
    return scrap_payment(h,base,active)

def scrap_payment(h,base,active):
    if active!="wall": return base,h.get("sale_tenths",0)
    extra,remainder=divmod(base+h.get("sale_tenths",0),10)
    return base+extra,remainder

def market(h,uid,section="town",note="",active=None,needed=None):
    needed=needed or {}
    def row(label,action):
        return [{"text":label,"callback_data":f"shop:{uid}:{revision(h,active)}:{action}"}]
    shops={"town":"Гусзк","armourer":"Лавка Мартина","apoth":"Аптека Лады","scribe":"Писец Тиш","bags":"Сумочник Уна","keys":"Ключница Рада"}
    text = [shops.get(section,"Скупщик Вей"), f"Кошелёк · {h['wallet']} мед."]
    if section in ("town","bags") or section.startswith("sell"):
        text[1]+=f"  ·  Хлам {units(h,needed)}/{capacity(h)}"
    if active=="wall" and not section.startswith("sell"):
        text.append("Караул на стене · в ценах учтена скидка 5%.")
    if active=="convoy" and section=="armourer":
        text.append("Прибыл обоз · пять вещей со скидкой 5%.")
    if note: text.append(note)
    rows = []
    if section=="town":
        rows.append([{"text":"Дорога к морю","callback_data":"road"}])
        rows.append([{"text":"Комендант · доска поручений","callback_data":"orders"}])
        for label,key in (("Мартин · оружейник","armourer"),("Лада · аптекарь","apoth"),("Тиш · писец","scribe"),("Вей · скупщик","sell"),("Уна · сумочник","bags"),("Рада · ключница","keys")):
            rows.append(row(label,key))
    elif section=="armourer":
        now=int(time.time())
        hour=now//3600
        text.append(f"Новый обоз через {(3600-now%3600+59)//60} мин.")
        for number,code in enumerate(wares(hour,active),1):
            z,k=map(int,code.split("."))
            item=CODE_ITEMS[code]
            power=class_power(h["class"],item,strength(z,k))
            bonus=f"+{power} к удару" if gear_stat(z,k)==0 else f"+{power} к здоровью"
            if item in ITEM_TRAITS:
                idx,value=ITEM_TRAITS[item]
                bonus+=f" · {STAT_NAMES[idx]} +{value}"
            bonus+=" · "+bonus_label(h,item)
            price=purchase(asking_price(z,k),section,active)
            text.append(f"\n{number}. {item}\n{price} мед.  ·  {tier_name(z,k)}  ·  ур. {wear_level(z,k)}\n{SLOTS[gear_slot(z,k)]} · {bonus}")
            if item not in h["items"]:
                rows.append(row(f"Купить №{number} · {price} мед.",f"stock-{hour}-{code}"))
        rows.append(row("Обновить прилавок","armourer"))
    elif section in ("apoth","scribe"):
        text.append("Один расходник за раунд. Один свиток на героя за поход." if section=="scribe"
                    else "Один расходник за раунд. Настои действуют три раунда. Одинаковый тип усиления заменяет прежний.")
        for k,(name,cost) in POTIONS.items():
            if (k in SCROLLS)!=(section=="scribe"): continue
            cost=purchase(cost,section,active)
            req = REQUIREMENT[k]
            text.append(f"\n{name} · {cost} мед.\nУр. {req} · {DESCR[k]}.")
            if level(h)>=req:
                rows.append(row(f"{name} · {cost} мед. · в запасе {h['potions'].get(k,0)}","buy-"+k))
    elif section=="bags":
        if h["pack"]+1<len(BAGS):
            size,price = BAGS[h["pack"]+1]
            price=purchase(price,section,active)
            rows.append(row(f"Купить сумку на {size} · {price} мед.","upgrade"))
        else: text.append("Куплена самая вместительная сумка.")
    elif section=="keys":
        text.append("Один ключ на один вход. Списывается при начале боя. В каждом тайнике три зала для одного героя.")
        for z,v in VAULTS.items():
            rows.append(row(f"{v[0]} · {purchase(key_price(z),section,active)} мед. · ключей {h['keys'].get(str(z),0)}",f"key-{z}"))
    elif section=="sell" or section.startswith("sellpage"):
        page = int(section[8:]) if section.startswith("sellpage") else 0
        entries = []
        for z in range(len(BANDS)):
            for k,item in enumerate(gear_names(z)):
                if item in h["items"] and item not in h["gear"]:
                    number = len(entries) + 1
                    label = f"{number}. {item} · {4*trade_value(z,k)} мед."
                    entries.append((label, row(str(number), f"gear-{z}-{k}")[0]))
        for key,count in h["junk"].items():
            z,n = map(int,key.split("."))
            name = "Связка выделанных шкур" if (z,n)==(6,98) else material_name(key)
            reserved = min(count,needed.get(key,0))
            if reserved:
                entries.append((f"[Задания и ремёсла] {name} ×{reserved} · отложено", None))
            if count > reserved:
                entries.append((f"[Хлам] {name} ×{count-reserved} · по {scrap_value(z,n)} мед.", None))
        page_size = 5
        last_page = max(0, (len(entries)-1)//page_size)
        page = min(page,last_page)
        visible = entries[page*page_size:(page+1)*page_size]
        buttons = [button for _,button in visible if button]
        if buttons:
            text.append("\nВыбери номер вещи для продажи.")
            rows.append(buttons)
        text.extend(label for label,_ in visible)
        total,_ = junk_payment(h,active,needed)
        if total:
            if active=="wall": text.append("Караул на стене · +10% к сумме за хлам.")
            rows.append(row(f"Продать весь хлам · +{total} мед.","cash"))
        if last_page:
            text.append(f"Страница {page+1} из {last_page+1}")
            if page: rows.append(row("‹ Назад",f"sellpage{page-1}"))
            if page<last_page: rows.append(row("Далее ›",f"sellpage{page+1}"))
        if not entries: text.append("Хлама и запасного снаряжения для продажи нет.")
    if section!="town": rows.append(row("К торговой площади","town"))
    return "\n".join(text),rows

def trade(h,uid,p,active=None,needed=None):
    needed=needed or {}
    def view(section,note=""):
        return market(h,uid,section,note,active,needed)
    if len(p)!=4 or p[1]!=uid: return "Открой город в своей карточке.",[]
    if p[2]!=revision(h,active): return "Цены и запасы на этой карточке устарели. Вернись в город через меню.",[]
    action = p[3]
    if action in ("town","apoth","sell","keys","bags","scribe","armourer"): return view(action)
    if action.startswith("sellpage") and action[8:].isascii() and action[8:].isdigit() and len(action[8:]) <= 6: return view(action)
    key = action.split("-")
    delta = 0
    if len(key)==3 and key[0]=="stock":
        hour=int(time.time())//3600
        if key[1]!=str(hour) or key[2] not in wares(hour,active):
            return view("armourer","Обоз сменился. Выбери вещь с нового прилавка.")
        z,k=map(int,key[2].split("."))
        item=CODE_ITEMS[key[2]]
        cost=purchase(asking_price(z,k),"armourer",active)
        if item in h["items"]: return view("armourer","Эта вещь у тебя уже есть.")
        if h["wallet"]<cost: return view("armourer","Не хватает медяков.")
        h["items"][item]=[gear_stat(z,k),strength(z,k)]
        delta,section=-cost,"armourer"
    elif action=="cash":
        delta,h["sale_tenths"] = junk_payment(h,active,needed)
        h["junk"]={k:min(v,needed[k]) for k,v in h["junk"].items() if needed.get(k,0)>0}
        section = "sell"
    elif len(key)==3 and key[0]=="gear" and key[1] in map(str,range(len(BANDS))) and key[2] in map(str,range(len(gear_names(int(key[1]))))):
        z,k = map(int,key[1:])
        if k>=len(gear_names(z)): return "Предмет недоступен.",[]
        item = gear_names(z)[k]
        if item not in h["items"] or item in h["gear"]: return "Предмет сейчас недоступен для продажи.",[]
        del h["items"][item]
        delta,section = 4*trade_value(z,k),"sell"
    else:
        if len(key)==2 and key[0]=="buy" and key[1] in POTIONS:
            if level(h)<REQUIREMENT[key[1]]: return "Сначала повысь уровень.",[]
            section,cost,stock,sku = ("scribe" if key[1] in SCROLLS else "apoth"),POTIONS[key[1]][1],h["potions"],key[1]
        elif len(key)==2 and key[0]=="key" and key[1] in map(str,VAULTS):
            section,cost,stock,sku = "keys",key_price(int(key[1])),h["keys"],key[1]
        elif action=="upgrade" and h["pack"]+1<len(BAGS):
            section,cost = "bags",BAGS[h["pack"]+1][1]
        else: return "Вернись в город через меню.",[]
        cost=purchase(cost,section,active)
        if h["wallet"]<cost: return view(section,"Не хватает медяков.")
        delta = -cost
        if action=="upgrade": h["pack"] += 1
        else: stock[sku] = stock.get(sku,0)+1
    h["wallet"] += delta
    h["shop_rev"] += 1
    return view(section,f"Сделка завершена · {delta:+} мед.")
