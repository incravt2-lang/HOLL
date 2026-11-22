"""Personal coastal journeys and commissions. Stored inside the campaign transaction."""
import city
import forks
import random
import secrets
import time

from market import asking_price
from quests import copper, SHIFT, details, progress
from world import item_slot_label, category, SEAM_SHIELD, encounter_area, BANDS, CLASS_PIECES, HUNT_IDS, SCRAPS, SLOTS, ZONES, faction, gear_stat, level, monster, rank, strength, tier_name

MASTERS={"veya":"Шорница Вея","hariton":"Оружейник Харитон"}
SLOTS_BY_MASTER={"veya":(0,3,5,7,9,10,11,13),"hariton":(1,2,4,6,12,14,15)}
ROAD=(
 ("Верстовой столб","За воротами колёса продавили глину до белого щебня. На верстовом столбе ещё видна зарубка дозора. От неё к камышам тянется след узкой тележки."),
 ("Рыбная дорога","Дождь стучит по опрокинутым лоткам старого торга. Вода бежит под досками к морю. На сухой стороне навеса кто-то развесил для просушки сеть."),
 ("Костры над отмелью","За дюной пахнет смолой. Часовой поднимает жердь, и сквозь дым уже видно, как у костра шорница вытягивает из кожи длинный ремень."),
)
RETURN_ROAD=(
 ("Рыбная дорога","Море скрылось за насыпью, но в спину ещё дует солёный ветер. На пустом рыбном торгу скрипит вывеска. Под навесом разведчик чинит сеть и кивает вам вслед."),
 ("Верстовой столб","У столба дорога раздваивается. Камышовая тропа уходит в топь, а в глубокой колее поблёскивает свежий подковный гвоздь. За полями уже видны зубцы городской стены."),
 ("Ворота Гусзка","Стражник отводит засов. Под аркой запах тины уступает дыму пекарни. Телега гремит по разбитой мостовой, и следом за ней вы выходите на торговую площадь."),
)

def row(label,cmd):
    return [{"text":label,"callback_data":cmd}]

def candidates(h,slot):
    band=(level(h)-1)//10
    return [(z,k) for (z,k),p in CLASS_PIECES.items() if BANDS[z]==band and p[1]==slot
            and p[0]!=SEAM_SHIELD and p[2]==h["class"] and p[3] in (0,1)]

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

def source_line(z,n):
    where=encounter_area(z,n)
    if n not in HUNT_IDS:
        dungeon,room=divmod(n-3,3)
        where+=f" · {ZONES[z][2][dungeon][0]} · зал {room+1}/3"
    return f"{monster(z,n)}, ур. {rank(z,n)} · {where}"

def describe(h,o,active=None):
    lines=[f"Изделие: {SLOTS[o['slot']]} · для твоего класса и уровня при выдаче.",
           f"Работа: {fee(o,active)} мед. · при себе {h['wallet']}"]
    if active=="fires": lines.append("Огни до самого моря · в цене учтена скидка 10%.")
    lines.append("\nМатериалы")
    for key,qty in o["materials"].items():
        z,n=map(int,key.split("."))
        lines.append(f"{SCRAPS[z][n]} · {h['junk'].get(key,0)}/{qty}\n   {source_line(z,n)}")
    return "\n".join(lines)

def journal(s,uid):
    h=s["heroes"][uid]
    lines=["Поручения коменданта"]
    active=city.buff(s)
    b=s["heroes"][uid].get("orders_board",{})
    if b.get("shift")==int(time.time())//SHIFT:
        for q in b["jobs"]:
            if q["owner"]==uid and not q["done"]:
                label,xp,rare=details(q)
                xp=city.earned(xp,active,h)
                if len(lines)>1: lines.append("")
                source=source_line(q["z"],q["n"])
                lines.append(f"{label} · {progress(q,h)}/{q['need']}\n   {source}\nНаграда: {xp} опыта, {copper(q)} мед. и вещь · редкая {rare}%, иначе обычная.")
    if len(lines)==1: lines.append("Действующих поручений нет.")
    q=city.current(s)
    lines.append("\nОбщее дело Гусзка\n"+city.PROJECTS[q["kind"]][0]+"\n"+city.summary(q))
    relic=h.get("route_relic")
    if relic and forks.active(h,relic):
        lines.append(f"\n{forks.RELICS[relic]} · осталось {int((h['route_until']-time.time()+59)//60)} мин.")
    if h.get("safe_trail"):lines.append("Известна тропа для обхода одной засады.")
    lines.append("\nРемесленники лагеря")
    for m,o in h.get("commissions",{}).items():
        lines.append("\n"+MASTERS[m]+"\n"+describe(h,o,active))
    if not h.get("commissions"): lines.append("Принятых заказов нет.")
    return "\n".join(lines)

def road(h,args):
    trip=h.get("coast_trip")
    if args and not trip:
        return "Этот переход уже завершён.",[]
    if trip and args==[trip["id"],"return"] and trip["step"]==3 and not trip.get("waiting") and not trip.get("returning"):
        trip=h["coast_trip"]=dict(id=secrets.token_hex(3),step=0,returning=True,
                ambush=random.randrange(1,4) if random.random()<0.12 else 0)
    if not trip:
        trip=h["coast_trip"]=dict(id=secrets.token_hex(3),step=0,
                ambush=random.randrange(1,4) if random.random()<0.12 else 0)
    if len(args)==2 and args==[trip["id"],str(trip["step"])] and trip["step"]<3 and not trip.get("waiting"):
        trip["step"]+=1
        if trip["step"]==trip["ambush"]: trip["waiting"]=True
    if trip.get("waiting") and args==[trip["id"],"bypass"] and h.pop("safe_trail",False):
        trip["waiting"]=False
    returning=trip.get("returning",False)
    if returning and trip.get("waiting") and args==[trip["id"],"retreat"]:
        trip=h["coast_trip"]=dict(id=secrets.token_hex(3),step=3,ambush=0)
        returning=False
    if trip.get("waiting"):
        bypass=[row("Обойти по тропе","road:"+trip["id"]+":bypass")] if h.get("safe_trail") else []
        return "Поперёк дороги лежит подвода. Из-под брезента поднимается вооружённый человек. Засада!",[row("Принять бой","roadfight:"+trip["id"]),(row("Отступить в лагерь",f"road:{trip['id']}:retreat") if returning else row("Отступить в Гусзк","nav:town"))]+bypass
    if returning and trip["step"]==3:
        del h["coast_trip"]
        h.pop("hunting_ground",None)
        return RETURN_ROAD[2][1],[]
    if trip["step"]==3:
        return ROAD[2][1]+"\nЛагерь разведчиков «У моря»", [row(name,"craft:"+m) for m,name in MASTERS.items()]+([row("Мастер · пряжки Кожевен","spoils")] if h.get("buckles") else [])+[row("В путь до Гусзка",f"road:{trip['id']}:return")]
    if trip["step"]:
        scenes=RETURN_ROAD if returning else ROAD
        label,text=scenes[trip["step"]-1]
    elif returning:
        label,text="У лагерного костра","Вы поправляете лямку сумки. До городских ворот три перехода."
    else:
        label,text="За городскими воротами","До лагеря разведчиков три перехода."
    direction="Дорога в Гусзк" if returning else "Дорога к морю"
    return f"{direction} · {trip['step']}/3\n{label}\n{text}",[row("Идти дальше",f"road:{trip['id']}:{trip['step']}")]

def craft(h,args,active=None):
    trip=h.get("coast_trip",{})
    if trip.get("step")!=3 or trip.get("waiting") or not args or args[0] not in MASTERS:
        return "Мастер принимает в лагере у моря.",[]
    m=args[0];prefix="craft:"+m
    orders=h.setdefault("commissions",{});order=orders.get(m)
    now=int(time.time());timers=h.setdefault("craft_ready",{});wait=max(0,timers.get(m,0)-now)
    back=row("К мастеру",prefix)
    note=""
    writs=h.get("writs",{})
    if len(args) in (3,4) and args[1]=="writ" and writs.get(args[2]) in (m,"guild"):
        ticket=args[2]
        if len(args)==3:
            return "Грамота покрывает работу и материалы. Выбери ячейку.",[row(SLOTS[i],prefix+":writ:"+ticket+":"+str(i)) for i in SLOTS_BY_MASTER[m]]+[back]
        if args[3].isdigit() and int(args[3]) in SLOTS_BY_MASTER[m]:
            pool=[p for p in candidates(h,int(args[3])) if CLASS_PIECES[p][0] not in h["items"]]
            if wait:note="Мастер ещё занят. Грамота остаётся у тебя."
            elif not pool:note="Все варианты этой ячейки уже есть. Грамота остаётся у тебя."
            else:
                tier=int(random.random()<0.2)
                z,k=random.choice([p for p in pool if CLASS_PIECES[p][3]==tier] or pool)
                item=CLASS_PIECES[z,k][0]
                h["items"][item]=[gear_stat(z,k),strength(z,k)]
                del writs[ticket]
                timers[m]=now+900
                wait=900
                note="Получено по грамоте: "+item+" — "+item_slot_label(z,k)
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
                    note=f"Получено: [{category(z,k)}] "+tier_name(z,k)+" · "+item+" — "+item_slot_label(z,k)
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
    rows.extend(row("Предъявить грамоту",prefix+":writ:"+k) for k,v in writs.items() if v in (m,"guild"))
    return "\n".join(lines),rows+[row("К кострам","road")]
