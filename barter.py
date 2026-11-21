"""Chat-local gifts and trades. Settle both baskets together on acceptance."""
import secrets
from collections import Counter
from cargo import needs,free
from market import capacity,units,material_name
from world import ITEM_CODES,CODE_ITEMS,category

def button(label,cmd):
    return [{"text":label,"callback_data":cmd}]

def label(code):
    if code=="m": return "Медяки"
    if code.startswith("j"): return material_name(code[1:])
    return CODE_ITEMS[code[1:]]

def stock(h,other,reserve):
    result={"m":h["wallet"]}
    result.update({"e"+ITEM_CODES[it]:1 for it in h["items"] if it not in h["gear"] and it not in other["items"]})
    result.update({"j"+k:free(h,k,reserve) for k in h["junk"]})
    return {k:v for k,v in result.items() if v>0}

def basket(data):
    def entry(k,v):
        tag=category(*map(int,k[1:].split("."))) if k.startswith("e") else "Монеты" if k=="m" else "Хлам"
        return f"[{tag}] {label(k)} ×{v}"
    return ", ".join(entry(k,v) for k,v in data.items()) or "ничего"

def terms(o,heroes):
    return "\n".join(f"{heroes[o[person]]['name']} отдаёт · {basket(o[side])}" for person,side in (("from","give"),("to","want")))

def settle(s,o):
    ids=[o["from"],o["to"]]
    hands=[o["give"],o["want"]]
    hs=[s["heroes"][who] for who in ids]
    reserves=[needs(s,who) for who in ids]
    for i,h in enumerate(hs):
        available=stock(h,hs[1-i],reserves[i])
        if any(v<1 or available.get(k,0)<v for k,v in hands[i].items()):
            return "Состав сумок или кошельков изменился. Сделка закрыта."
        future=Counter(h["junk"])
        for sign,hand in ((-1,hands[i]),(1,hands[1-i])):
            for k,v in hand.items():
                if k.startswith("j"): future[k[1:]]+=sign*v
        after=sum(max(0,v-reserves[i].get(k,0)) for k,v in future.items())
        if after>max(capacity(h),units(h,reserves[i])):
            return "У получателя не хватает места в сумке. Сделка закрыта."
    for i,hand in enumerate(hands):
        h,other=hs[i],hs[1-i]
        for k,v in hand.items():
            if k=="m":
                h["wallet"]-=v
                other["wallet"]+=v
            elif k.startswith("j"):
                key=k[1:]
                h["junk"][key]-=v
                if not h["junk"][key]: del h["junk"][key]
                other["junk"][key]=other["junk"].get(key,0)+v
            else:
                item=CODE_ITEMS[k[1:]]
                other["items"][item]=h["items"].pop(item)
            h["shop_rev"]+=1
            other["shop_rev"]+=1
    return "Передача завершена."

def exchange(s,uid,cmd):
    heroes=s["heroes"]; h=heroes[uid]; offers=s.setdefault("offers",{})
    args=cmd.split(":")[1:];home=button("К сделкам","barter")
    busy={i for r in s["fights"].values() if r["round"] for i in r["party"]}
    if not args:
        rows=[button(("Получено · " if o["to"]==uid else "Отправлено · ")+heroes[o["from"] if o["to"]==uid else o["to"]]["name"],"barter:view:"+key) for key,o in offers.items() if uid in (o["from"],o["to"])]
        rows.extend(button("Предложить · "+p["name"],"barter:to:"+i) for i,p in heroes.items() if i!=uid)
        return "Обмен и подарки\nВыбери героя или открой предложение.\n"+h.get("trade_news",""),rows
    if len(args)==2 and args[0] in ("view","yes","no"):
        act,key=args;o=offers.get(key)
        if not o or uid not in (o["from"],o["to"]):return "Предложение закрыто.",[home]
        for side in ("give","want"):
            if isinstance(o[side],str):o[side]={"e"+ITEM_CODES[o[side]]:1}
        desc=terms(o,heroes)
        if act=="view":
            rows=[button("Принять","barter:yes:"+key)] if uid==o["to"] else []
            return desc,rows+[button("Отменить","barter:no:"+key),home]
        if act=="yes":
            if uid!=o["to"]:return "Подтверждает получатель.",[home]
            if busy.intersection((o["from"],o["to"])):return "Завершите бой перед передачей.",[home]
            status=settle(s,o)
        else:status="Предложение отменено."
        del offers[key]
        for who in (o["from"],o["to"]):heroes[who]["trade_news"]=status+"\n"+desc
        return status+"\n"+desc,[home]
    if uid in busy:return "Заверши бой перед сделкой.",[home]
    if len(args)==2 and args[0]=="to" and args[1] in heroes and args[1]!=uid:
        d=dict(id=secrets.token_hex(4),to=args[1],give={},want={},side="give")
        h["trade_draft"]=d;args=["edit",d["id"]]
    d=h.get("trade_draft")
    if not d or len(args)<2 or args[1]!=d["id"]:return "Черновик устарел.",[home]
    act,key,*params=args;other=d["to"]
    if act=="send":
        if not (d["give"] or d["want"]):return "Выбери содержимое предложения.",[home]
        offers[key]={k:d[k] for k in ("give","want","to")}
        offers[key]["from"]=uid
        del h["trade_draft"]
        return "Предложение отправлено.\n"+terms(offers[key],heroes),[home]
    if act=="side" and params in (["give"],["want"]):d["side"]=params[0]
    side=d["side"];a,b=(uid,other) if side=="give" else (other,uid)
    options=stock(heroes[a],heroes[b],needs(s,a))
    prefix=lambda verb:"barter:"+verb+":"+key
    if act in ("qty","set") and len(params)>=2 and params[0]==side:
        code=params[1]
        maximum=options.get(code,0)
        if act=="set" and len(params)==3 and params[2].isascii() and params[2].isdigit():
            v=int(params[2])
            if 0<v<=maximum:
                d[side][code]=v
                d["want" if side=="give" else "give"].pop(code,None)
            if v==0:d[side].pop(code,None)
        if act=="qty" and maximum:
            current=d[side].get(code,0)
            values=sorted({0,1,maximum,min(maximum,current+1),min(maximum,current+10),min(maximum,current+100),max(0,current-1)})
            return f"{label(code)} · доступно {maximum}\nВыбрано {current}. Укажи количество.",[button(str(v),prefix("set")+f":{side}:{code}:{v}") for v in values]+[home]
    page=int(params[0]) if act=="page" and len(params)==1 and params[0].isdigit() else 0
    codes=sorted(set(options)|set(d[side]),key=label)
    page=min(page,max(0,(len(codes)-1)//8))
    rows=[button(("◆ " if code in d[side] else "")+label(code)+f" ×{options.get(code,0)}",prefix("qty")+f":{side}:{code}") if options.get(code) else button("Убрать · "+label(code),prefix("set")+f":{side}:{code}:0") for code in codes[page*8:page*8+8]]
    for n in (page-1,page+1):
        if 0<=n*8<len(codes):rows.append(button(f"Страница {n+1}",prefix("page")+":"+str(n)))
    rows+=[button("Изменить встречную часть" if side=="give" else "Изменить свою часть",prefix("side")+":"+("want" if side=="give" else "give"))]
    if d["give"] or d["want"]:rows.append(button("Отправить предложение",prefix("send")))
    title="Выбери, что отдаёшь" if side=="give" else "Выбери, что просишь"
    return title+"\n\n"+terms(dict(d,**{"from":uid}),heroes)+"\n\nДля подарка оставь одну сторону пустой.",rows+[home]
