"""Expedition stamina and the tavern at the Guszk square."""
import time
from world import level

CAP=100
COST={"hunt":1,"vault":3,"raid":5}

def balance(h,now=None):
    now=int(time.time()) if now is None else now
    value=h.get("vigor",CAP)
    if "rest_since" in h:
        minutes=max(0,now-h["rest_since"])//60
        value=min(CAP,value+minutes)
        h["rest_since"]+=minutes*60
    h["vigor"]=value
    return value

def leave(h):
    if "rest_since" in h:
        balance(h)
        del h["rest_since"]

def price(h,amount):
    return (amount*(5+level(h))+9)//10

def button(text,cmd):
    return {"text":text,"callback_data":cmd}

def card(h,args):
    now=int(time.time())
    if "rest_since" not in h:
        if args or h.get("coast_trip") or h.get("hunting_ground"):
            return "Войти в таверну можно с площади Гусзка.",[[button("К площади","nav:town")]]
        h["rest_since"]=now
        h["brew_rev"]=h.get("brew_rev",0)+1
    current=balance(h,now)
    rev=h["brew_rev"]
    note=""
    if args and args!=["look"]:
        if len(args)==3 and args[0]=="brew" and args[1]==str(rev) and args[2].isascii() and args[2].isdigit() and len(args[2])<=3:
            target=int(args[2])
            if 0<target<=CAP:
                amount=max(0,target-current)
                cost=price(h,amount)
                if not amount:note="Ты уже восстановил столько Бодрости."
                elif h["wallet"]<cost:note=f"Для взвара нужно {cost} мед."
                else:
                    h["wallet"]-=cost
                    h["vigor"]=current=target
                    h["brew_rev"]=rev=rev+1
                    note=f"Горький взвар согрел тебя. +{amount} Бодрости · −{cost} мед."
        else:note="Заказ уже обработан. Хозяин подвинул к тебе свежий счёт."
    lines=["Таверна Гусзка","У порога пахнет мокрой шерстью. Хозяин снимает с огня закопчённый котелок и кивает на лавку.",f"Бодрость · {current}/{CAP}   Кошелёк · {h['wallet']} мед."]
    rows=[]
    if current<CAP:
        seconds=max(1,60-(now-h["rest_since"]))
        lines.append(f"Следующая единица через {seconds} сек. До полного запаса · {CAP-current} мин.")
        seen=set()
        for target,title in ((5,"До похода"),(min(CAP,current+20),"Горький взвар"),(CAP,"До полной")):
            if target<=current or target in seen:continue
            seen.add(target);qty=target-current
            rows.append([button(f"{title} · +{qty} · {price(h,qty)} мед.",f"inn:brew:{rev}:{target}")])
        rows.append([button("Проверить Бодрость","inn:look")])
    else:lines.append("Ты отдохнул и готов к дороге.")
    if note:lines.append(note)
    return "\n\n".join(lines),rows+[[button("Выйти на площадь","nav:town")]]
