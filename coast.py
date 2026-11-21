"""Personal coastal journeys and commissions. Stored inside the campaign transaction."""
import city
import random
import secrets
import time

from market import asking_price
from quests import SHIFT, details, progress
from world import encounter_area, BANDS, CLASS_PIECES, HUNT_IDS, SCRAPS, SLOTS, ZONES, faction, gear_stat, level, monster, rank, strength, tier_name

MASTERS={"veya":"Шорница Вея","hariton":"Оружейник Харитон"}
SLOTS_BY_MASTER={"veya":(0,3,5,7,9,10,11,13),"hariton":(1,2,4,6,12,14,15)}
ROAD=(
 ("Верстовой столб","У последнего столба стёрто расстояние до моря. Колеи уходят к камышам."),
 ("Рыбная дорога","По лоткам старого рыбного торга барабанит дождь. Под навесом ещё сухо."),
 ("Костры над отмелью","Сквозь мокрую сеть виден огонь. Часовой приподнимает жердь над тропой."),
)

def row(label,cmd):
    return [{"text":label,"callback_data":cmd}]

def candidates(h,slot):
    band=(level(h)-1)//10
    return [(z,k) for (z,k),p in CLASS_PIECES.items() if BANDS[z]==band and p[1]==slot
            and p[2]==h["class"] and p[3] in (0,1)]

def offer(h,slot):
    lv=level(h)
    targets=sorted(((z,n) for z in range(len(ZONES)) for n in HUNT_IDS),
                   key=lambda pair:abs(rank(*pair)-lv))
    near=[pair for pair in targets if abs(rank(*pair)-lv)<=3]
    rng=random.Random(f"{lv}:{slot}:{h['class']}")
    materials={f"{z}.{n}":i+1 for i,(z,n) in enumerate(rng.sample(near,2))}
    price=min(asking_price(z,k) for z,k in candidates(h,slot))*55//100
    return dict(slot=slot,price=price,materials=materials)

def fee(o,active):
    return city.price(o["price"],10) if active=="fires" else o["price"]

def describe(h,o,active=None):
    lines=[f"Изделие: {SLOTS[o['slot']]} · для твоего класса и уровня при выдаче.",
           f"Работа: {fee(o,active)} мед. · при себе {h['wallet']}"]
    if active=="fires": lines.append("Огни до самого моря · в цене учтена скидка 10%.")
    lines.append("\nМатериалы")
    for key,qty in o["materials"].items():
        z,n=map(int,key.split("."))
        lines.append(f"{SCRAPS[z][n]} · {h['junk'].get(key,0)}/{qty}\n   {monster(z,n)}, ур. {rank(z,n)} · {encounter_area(z,n)}")
    return "\n".join(lines)

def journal(s,uid):
    h=s["heroes"][uid]
    lines=["Поручения коменданта"]
    active=city.buff(s)
    b=s.get("contracts",{})
    if b.get("shift")==int(time.time())//SHIFT:
        for q in b["jobs"]:
            if q["owner"]==uid and not q["done"]:
                label,xp,rare=details(q)
                xp=city.earned(xp,active)
                lines.append(f"{label} · {progress(q,h)}/{q['need']}\nНаграда: {xp} опыта и вещь · редкая {rare}%, иначе обычная.")
    if len(lines)==1: lines.append("Действующих поручений нет.")
    q=city.current(s)
    lines.append("\nОбщее дело Гусзка\n"+city.PROJECTS[q["kind"]][0]+"\n"+city.summary(q))
    lines.append("\nРемесленники лагеря")
    for m,o in h.get("commissions",{}).items():
        lines.append("\n"+MASTERS[m]+"\n"+describe(h,o,active))
    if not h.get("commissions"): lines.append("Принятых заказов нет.")
    return "\n".join(lines)

def road(h,args):
    trip=h.get("coast_trip")
    if not trip:
        trip=h["coast_trip"]=dict(id=secrets.token_hex(3),step=0,
                ambush=random.randrange(1,4) if random.random()<0.12 else 0)
    if len(args)==2 and args==[trip["id"],str(trip["step"])] and trip["step"]<3 and not trip.get("waiting"):
        trip["step"]+=1
        if trip["step"]==trip["ambush"]: trip["waiting"]=True
    if trip.get("waiting"):
        return "Поперёк дороги лежит подвода. Из-под брезента поднимается вооружённый человек. Засада!",[row("Принять бой","roadfight:"+trip["id"]),row("Отступить в Гусзк","nav:town")]
    if trip["step"]==3:
        return ROAD[2][1]+"\nЛагерь разведчиков «У моря»", [row(name,"craft:"+m) for m,name in MASTERS.items()]+[row("Вернуться в Гусзк","nav:town")]
    label,text=ROAD[trip["step"]-1] if trip["step"] else ("За городскими воротами","До лагеря разведчиков три перехода.")
    return f"Дорога к морю · {trip['step']}/3\n{label}\n{text}",[row("Идти дальше",f"road:{trip['id']}:{trip['step']}")]

def craft(h,args,active=None):
    trip=h.get("coast_trip",{})
    if trip.get("step")!=3 or trip.get("waiting") or not args or args[0] not in MASTERS:
        return "Мастер принимает в лагере у моря.",[]
    m=args[0];prefix="craft:"+m
    orders=h.setdefault("commissions",{});order=orders.get(m)
    now=int(time.time());timers=h.setdefault("craft_ready",{});wait=max(0,timers.get(m,0)-now)
    back=row("К мастеру",prefix)
    note=""
    if len(args)==3 and args[1] in ("preview","take") and args[2].isdigit() and int(args[2]) in SLOTS_BY_MASTER[m] and not order:
        slot=int(args[2])
        if args[1]=="preview":
            o=offer(h,slot);h.setdefault("craft_quotes",{})[m]=o
            return MASTERS[m]+"\n"+describe(h,o,active),[row("Договориться",prefix+":take:"+str(slot)),back]
        o=h.get("craft_quotes",{}).pop(m,None)
        if o and o["slot"]==slot:
            order=orders[m]=dict(o,id=secrets.token_hex(4))
    if order and len(args)==3 and args[2]==order["id"]:
        if args[1]=="cancel":
            return "Отказаться от заказа? Материалы останутся в сумке.",[row("Да, отказаться",prefix+":drop:"+order["id"]),back]
        if args[1]=="drop":
            del orders[m];order=None
        elif args[1]=="finish":
            if wait: note="Мастер ещё занят."
            elif order.get("quoted_fee",order["price"])!=fee(order,active): note="Стоимость работы изменилась. Проверь цену и подтверди выдачу."
            elif h["wallet"]<fee(order,active) or any(h["junk"].get(k,0)<v for k,v in order["materials"].items()):
                note="Для заказа ещё нужны материалы или медь."
            else:
                pool=[(z,k) for z,k in candidates(h,order["slot"]) if CLASS_PIECES[z,k][0] not in h["items"]]
                if not pool: note="У тебя уже есть все варианты этого изделия. Можно отменить заказ."
                else:
                    tier=int(random.random()<0.2)
                    z,k=random.choice([p for p in pool if CLASS_PIECES[p][3]==tier] or pool)
                    item=CLASS_PIECES[z,k][0]
                    h["items"][item]=[gear_stat(z,k),strength(z,k)]
                    for key,v in order["materials"].items():
                        h["junk"][key]-=v
                        if not h["junk"][key]: del h["junk"][key]
                    h["wallet"]-=fee(order,active);timers[m]=now+900;wait=900
                    del orders[m];order=None
                    note="Получено: "+tier_name(z,k)+" · "+item
    lines=[MASTERS[m]]
    if note: lines.append(note)
    if wait: lines.append(f"До следующей выдачи: {wait//60}:{wait%60:02d}")
    if order:
        order["quoted_fee"]=fee(order,active)
        lines.append(describe(h,order,active))
        rows=[row("Передать материалы",prefix+":finish:"+order["id"]),row("Отказаться от заказа",prefix+":cancel:"+order["id"])]
    else:
        lines.append("Выбери ячейку для изделия. Оба кольца подходят для любой кольцевой ячейки.")
        rows=[row(SLOTS[i] if i!=7 else "Кольцо",prefix+":preview:"+str(i)) for i in SLOTS_BY_MASTER[m]]
    return "\n".join(lines),rows+[row("К кострам","road")]
