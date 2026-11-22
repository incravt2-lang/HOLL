"""Personal trades, transferable ingredients and permanent recipe books."""
import random
import craft_sources as sources
from world import (ITEM_TRAITS, STAT_NAMES, class_power, BANDS, ZONES, HUNT_IDS, ARM_BY_NAME, SCRAPS, RECIPES, tier_name, gear_names,
                   strength, wear_level, gear_stat, item_slot_label, bonus_label, is_humanoid, level)
from workshop_data import RANKS, TRADES
from loadouts import REGIONS

ENTRY_PRICE=600
TUITION=(0,80,120,160)
STORES={"forge":("Харитон","Кузнечный уголь","Заготовка заклёпок","Обломки железной упряжи"),
        "sew":("Вея","Вощёная нить","Стёганая подкладка","Дубильное сырьё")}
BY_ID={f"{z}.{k}":(z,k) for z,k in RECIPES}


SALVAGE_WORDS={"forge":("желез","цеп","гвозд","лезви","ключ","пряж","скоб","медн","жетон","блях","крюк","клин","кольц","петл","шпор","пломб"),
               "sew":("шкур","шерст","руно","шнур","повод","ремеш","лоскут","тесьм","нить","нитк","мех","волок","перо","нашив","повяз","лент")}
def can_salvage(trade,z,n):
    return n in HUNT_IDS and any(w in SCRAPS[z][n].lower() for w in SALVAGE_WORDS[trade])

def name(key):
    kind,code=key.split("/",1)
    if kind=="boss":return sources.part_name(key)
    if kind=="plan":
        z,k=BY_ID[code]
        return ("Чертёж" if RECIPES[z,k][0]=="forge" else "Выкройка")+" · "+gear_names(z)[k]
    trade,band=code.split(".")
    labels={"shop":STORES[trade][1],"part":STORES[trade][2],"raw":STORES[trade][3],
            "deep":"Замковая пластина" if trade=="forge" else "Армированная тесьма",
            "shard":"Зубец пластины" if trade=="forge" else "Прядь тесьмы"}
    return labels[kind]+(" · "+REGIONS[int(band)] if kind!="shop" else "")


def add(h,key,qty=1):
    stock=h.setdefault("supplies",{})
    stock[key]=stock.get(key,0)+qty
    if not stock[key]:del stock[key]


def purpose(h,key):
    prof=h.get("profession",{})
    if key.startswith("plan/"):
        return "Образец"
    for rid in prof.get("book",[]):
        z,k=BY_ID[rid]
        trade,deep,req=RECIPES[z,k]
        costs=requirements(z,k)
        if key in costs:
            return "Для рецепта"
    return "Материал"

def sell_price(key):
    kind,code=key.split("/")
    if kind=="boss":return 12+BANDS[sources.boss_id(key)[0]]
    if kind=="plan":return 20+5*BANDS[BY_ID[code][0]]
    return {"shop":1,"raw":2,"part":4,"shard":3,"deep":9}[kind]+int(code.split(".")[1])

def drops(h,z,n,mode,reserved=None):
    from market import units,capacity
    band=BANDS[z]
    human=is_humanoid(z,n)
    trade="forge" if human else "sew"
    materials=[]
    if mode=="hunt" and random.random()<sources.FIELD_CHANCE:
        materials.append(f"raw/{trade}.{band}")
    boss=mode!="hunt" and n%3==2
    if boss and random.random()<sources.chance(n):
        materials.append(sources.boss_key(z,n))
    if (human or boss) and random.random()<(0.14 if boss else 0.018):
        choices=[key for key,(a,b) in BY_ID.items() if BANDS[a]==band and RECIPES[a,b][2]%20==17]
        materials.append("plan/"+random.choice(choices))
    result=[]
    for key in materials:
        if units(h,reserved)>=capacity(h):
            result.append(name(key)+" · нет места")
        else:
            add(h,key)
            result.append(f"[{purpose(h,key)}] {name(key)}")
    return result


def row(label,*parts):
    return [{"text":label,"callback_data":"work:"+":".join(map(str,parts))}]


def ingredient_costs(stock,z,k):
    trade,deep,req=RECIPES[z,k]
    band=BANDS[z]
    costs=requirements(z,k)
    key=f"part/{trade}.{band}"
    missing=max(0,costs[key]-stock.get(key,0))
    if missing:
        costs[key]-=missing
        if not costs[key]:del costs[key]
        costs[f"raw/{trade}.{band}"]+=missing*2
    return costs


def view(h,args,busy=False,reserved=None):
    from market import units,capacity
    reserved=reserved or {}
    prof=h.get("profession")
    stock=h.get("supplies",{})
    camp=h.get("coast_trip",{})
    at_camp=camp.get("step")==3 and not camp.get("waiting") and not camp.get("returning") and not busy
    trade=args[0] if args else ""
    if trade not in TRADES:return "Выбери наставника в лагере.",[]
    act=args[1] if len(args)>1 else "home"
    master,supply,_,_=STORES[trade]
    own=prof and prof["trade"]==trade
    rank=prof["rank"] if own else 0
    skill=prof["skill"] if own else 0
    cap=30*(rank+1)
    rev=h.get("work_rev",0)
    def buy(label,action,*ids):return row(label,trade,action,*ids,rev)
    book=row("К книге",trade,"home")
    back=[{"text":"К кострам","callback_data":"road"}] if at_camp else [{"text":"К герою","callback_data":"nav:hero"}]
    merchant=row("К наставнику",trade,"master")
    if act=="master":
        if not at_camp:return "Наставник принимает в лагере у моря.",[back]
        rows=[]
        if not prof:rows.append(buy(f"Обучиться · {ENTRY_PRICE} мед.","enroll"))
        if own:
            rows.append(row("Уроки наставника",trade,"lessons"))
            if rank<3 and skill==cap:rows.append(buy(f"Следующая ступень · {TUITION[rank+1]} мед.","promote"))
        rows.append([buy(f"Купить ×{q}","buy",q)[0] for q in (1,5)])
        return f"{master} · {TRADES[trade]}\n{supply} · 8 мед. за штуку\nКошелёк · {h['wallet']} мед.",rows+[back]

    def listings(title,entries,page,section):
        page=min(page,max(0,(len(entries)-1)//5))
        lines=[title]
        buttons=[]
        for i,(label,key) in enumerate(entries[page*5:page*5+5],page*5+1):
            z,k=BY_ID[key]
            _,deep,req=RECIPES[z,k]
            costs=ingredient_costs(stock,z,k)
            ready=all(stock.get(a,0)>=v for a,v in costs.items())
            status="уже есть" if label in h["items"] else "материалы собраны" if ready else "не хватает материалов"
            stat="к удару" if gear_stat(z,k)==0 else "ХП"
            power=class_power(h["class"],label,strength(z,k))
            lines.append(f"{i}. {label} — {item_slot_label(z,k)}\n{tier_name(z,k)} · ур. {wear_level(z,k)} · +{power} {stat} · {bonus_label(h,label)}\n{status}")
            buttons.extend(row(str(i),trade,"recipe",key))
        if not buttons:lines.append("Список пока пуст.")
        rows=[buttons] if buttons else []
        rows.extend(row(label,trade,section,i) for label,i in (("‹ Назад",page-1),("Ещё ›",page+1)) if 0<=5*i<len(entries))
        return "\n\n".join(lines),rows+[book,back]
    note=""
    plans=[(key,z,k,deep,req) for key,(z,k) in BY_ID.items()
           for t,deep,req in [RECIPES[z,k]] if t==trade]
    if act=="home" and own:act="known"
    if act=="recipe" and len(args)==3 and args[2] in BY_ID:
        key=args[2];z,k=BY_ID[key];t,deep,req=RECIPES[z,k]
        if t!=trade:return "Рецепт другого ремесла.",[book]
        band=BANDS[z];item=gear_names(z)[k]
        text=[item+" — "+item_slot_label(z,k),f"{tier_name(z,k)} · ур. {wear_level(z,k)} · навык {req}",
              f"+{class_power(h['class'],item,strength(z,k))} {'к удару' if gear_stat(z,k)==0 else 'ХП'} · "+bonus_label(h,item)]
        if item in ITEM_TRAITS:
            stat,value=ITEM_TRAITS[item]
            text.append(f"{STAT_NAMES[stat]} +{value}")
        cost=ingredient_costs(stock,z,k)
        text+=["","Материалы"]
        for material,count in cost.items():
            text.extend([f"{name(material)} · {stock.get(material,0)}/{count}",sources.route(material),""])
        arm=ARM_BY_NAME.get(item)
        if arm:text.append("Класс · "+{"guard":"Гвардеец","archer":"Браконьер","smith":"Инженер","nun":"Сестра Ордена","witch":"Ученица аптекаря"}[arm[0]])
        rows=[]
        if own and key in prof["book"]:
            text.append("При изготовлении: +1 к навыку." if skill<min(cap,req+12) else "Освоенный рецепт.")
            rows.append(buy("Изготовить","make",key))
        elif req%20==17:
            text.append("Образец выпадает с гуманоидов и боссов этой десятки.")
            if stock.get("plan/"+key):rows.append(buy("Изучить образец","study",key))
        elif at_camp:rows.append(buy(f"Выучить · {10+band*4} мед.","teach",key))
        return "\n".join(text),rows+[book,back]
    page=int(args[2]) if len(args)==3 and args[2].isdigit() and len(args[2])<5 else 0
    if act in ("known","lessons","patterns"):
        options=[]
        for key,z,k,deep,req in plans:
            learned=own and key in prof["book"]
            if (act=="known" and learned or act=="lessons" and at_camp and own and not learned and req<=skill and req%20!=17
                or act=="patterns" and stock.get("plan/"+key)):
                options.append((gear_names(z)[k],key))
        if act=="known":
            def available(entry):
                label,key=entry
                z,k=BY_ID[key]
                _,deep,req=RECIPES[z,k]
                costs=ingredient_costs(stock,z,k)
                return label not in h["items"] and all(stock.get(a,0)>=v for a,v in costs.items())
            options.sort(key=lambda entry:not available(entry))
            heading=f"{TRADES[trade]} · {RANKS[rank]} · навык {skill}/{cap}\nКнига рецептов"
        else:
            heading="Доступные уроки" if act=="lessons" else "Найденные образцы"
        text,rows=listings(heading+f" · {len(options)}",options,page,act)
        if act=="known":
            rows.remove(book)
            if any(stock.get("plan/"+key) for key,*_ in plans):
                rows.insert(-1,row("Найденные образцы",trade,"patterns"))
            rows[-1]=[{"text":"К герою","callback_data":"nav:hero"}]
        return text,rows
    if act=="materials":
        goods=sorted(stock,key=name)
        page=min(page,max(0,(len(goods)-1)//8))
        lines=[f"[{purpose(h,key)}] {name(key)} ×{stock[key]}" for key in goods[page*8:page*8+8]]
        nav=[row(label,trade,"materials",i) for label,i in (("‹ Назад",page-1),("Ещё ›",page+1)) if 0<=i*8<len(goods)]
        return "\n".join(["Материалы ремесла",*(lines or ["Пока пусто."])]),nav+[back]
    if act=="salvage":
        options=[]
        for key,qty in h["junk"].items():
            z,n=map(int,key.split("."))
            if n not in HUNT_IDS or qty<=reserved.get(key,0):continue
            if can_salvage(trade,z,n):
                options.append(buy(f"{SCRAPS[z][n]} · {qty-reserved.get(key,0)}","recover",key))
        page=min(page,max(0,(len(options)-1)//6))
        nav=[row(label,trade,"salvage",i) for label,i in (("‹ Назад",page-1),("Ещё ›",page+1)) if 0<=i*6<len(options)]
        return "Разобрать трофей на сырьё. По одному предмету за раз.",options[page*6:page*6+6]+nav+[book]
    if act in ("prep","joinparts"):
        rows=[]
        for band,region in enumerate(REGIONS):
            key=("raw" if act=="prep" else "shard")+f"/{trade}.{band}"
            if stock.get(key,0):
                rows.append(buy(f"{region} · при себе {stock[key]}","prepare" if act=="prep" else "combine",band))
        return ("Заготовка из двух единиц сырья" if act=="prep" else "Деталь из трёх фрагментов"),rows+[book]
    mutations={"enroll","promote","buy","teach","study","make","prepare","combine","recover"}
    if act in mutations:
        if busy or args[-1]!=str(rev):return "Карточка устарела или герой занят боем.",[book]
        if act=="enroll" and at_camp and not prof and h["wallet"]>=ENTRY_PRICE:
            prof=h["profession"]=dict(trade=trade,rank=0,skill=0,book=[q[0] for q in sorted(plans,key=lambda q:q[-1])[:2]])
            h["wallet"]-=ENTRY_PRICE;note="Обучение завершено. В книге два рецепта."
        elif act=="promote" and at_camp and own and rank<3 and skill==cap and h["wallet"]>=TUITION[rank+1]:
            h["wallet"]-=TUITION[rank+1];prof["rank"]+=1;note="Наставник присвоил новую ступень."
        elif act=="buy" and at_camp and len(args)==4 and args[2] in ("1","5") and h["wallet"]>=8*int(args[2]):
            if units(h,reserved)+int(args[2])>capacity(h):return "Не хватает места в сумке.",[book,back]
            qty=int(args[2]);h["wallet"]-=8*qty;add(h,f"shop/{trade}.0",qty);note="Приобретено: "+supply
        elif own and act=="recover" and len(args)==4 and args[2] in h["junk"]:
            key=args[2];z,n=map(int,key.split("."))
            if can_salvage(trade,z,n) and h["junk"][key]>reserved.get(key,0):
                h["junk"][key]-=1
                if not h["junk"][key]:del h["junk"][key]
                add(h,f"raw/{trade}.{BANDS[z]}")
                h["shop_rev"]+=1
                note="Получено сырьё."
        elif own and act in ("prepare","combine") and len(args)==4 and args[2] in tuple(map(str,range(6))):
            band=int(args[2]);src,dest,count=("raw","part",2) if act=="prepare" else ("shard","deep",3)
            key=f"{src}/{trade}.{band}"
            if stock.get(key,0)>=count:
                add(h,key,-count);add(h,f"{dest}/{trade}.{band}")
                if act=="prepare" and skill<min(cap,band*20+12):prof["skill"]+=1
                note="Получено: "+name(f"{dest}/{trade}.{band}")
        elif own and act in ("teach","study","make") and len(args)==4 and args[2] in BY_ID:
            key=args[2];z,k=BY_ID[key];t,deep,req=RECIPES[z,k];band=BANDS[z];price=10+4*band
            if t==trade and (skill>=req or key in prof["book"]):
                if key not in prof["book"]:
                    if act=="teach" and at_camp and req%20!=17 and h["wallet"]>=price:
                        h["wallet"]-=price;prof["book"].append(key);note="Наставник показал новый приём."
                    elif act=="study" and req%20==17 and stock.get("plan/"+key,0)>0:
                        add(h,"plan/"+key,-1);prof["book"].append(key);note="Образец изучен."
                elif act=="make":
                    costs=ingredient_costs(stock,z,k);item=gear_names(z)[k]
                    if item in h["items"]:note="Такое изделие уже в сумке. Его можно продать или передать."
                    elif all(stock.get(a,0)>=v for a,v in costs.items()):
                        for a,v in costs.items():add(h,a,-v)
                        h["items"][item]=[gear_stat(z,k),strength(z,k)]
                        if skill<min(cap,req+12):prof["skill"]+=1
                        note="Изготовлено: "+item
        if not note:return "Не хватает навыка, материалов или меди. Обучение и покупка расходников доступны у наставника.",[book,back]
        h["work_rev"]=rev+1
        text,rows=view(h,[trade,"master" if act in ("promote","enroll","buy","teach") else "known"],busy,reserved)
        return note+"\n\n"+text,rows
    rows=[]
    text=[TRADES[trade]]
    if own:
        text.append(f"{RANKS[rank]} · навык {skill}/{cap}")
        if rank<3 and skill==cap:text.append(f"Следующая ступень · {master}, лагерь у моря · {TUITION[rank+1]} мед.")
        text.append(f"Изучено рецептов · {len(prof['book'])}")
        rows.append(row("Чертежи" if trade=="forge" else "Выкройки",trade,"known"))
        if any(stock.get("plan/"+key) for key,*_ in plans):
            rows.append(row("Найденные образцы",trade,"patterns"))
    rows.append(back)
    return "\n".join(text),rows


def requirements(z,k):
    trade,deep,req=RECIPES[z,k]
    band=BANDS[z]
    costs={f"part/{trade}.{band}":1+int(req%20>=10),f"raw/{trade}.{band}":1+(req%20)//9,f"shop/{trade}.0":1}
    if req%20>=10:
        other="forge" if trade=="sew" else "sew"
        costs[f"raw/{other}.{band}"]=1
    for key in sources.BILLS.get((z,k),()):costs[key]=1
    return costs
