"""Personal commandant contracts. Progress and entry permits live on the hero."""
import time

from world import BANDS, LIMITS, SCRAPS, VAULTS, encounter_area, level, monster, rank

# Title, brief, hunt goals (zone, target, quantity), proof from the vault.
ORDERS = (
 ("Недостача в соляной ведомости","Перевозчик дважды заплатил за один воз. Достань грош и пряжку сборщика. В подполе хранится старый оттиск заставы — сверим знаки.",((1,14,1),(1,15,1)),"Восковой оттиск заставы"),
 ("Клеймо зимнего стада","Клейма на двух турах выжжены задом наперёд. Принеси оба и матрицу скотника из воскового погреба.",((1,2,2),),"Матрица скотного двора"),
 ("Руки вычеркнутой смены","Колодезник расписался за мёртвую смену ладонью. Принеси два соляных слепка и дощечку с отпечатками из шахты.",((7,15,2),),"Сменная дощечка с отпечатками"),
 ("Мера с двойным дном","До белильни доходит половина отпущенной соли. Нужны донце меры, напёрсток для проверки отверстия и контрольная мерка из шахты.",((2,14,1),(2,15,1)),"Контрольная мерка солеваров"),
 ("Сани без упряжи","Ремни на соляных санях срезали ножом. Подбери нож налётчика, две попонные застёжки и шахтную бирку с номером обоза.",((3,14,1),(3,2,2)),"Приёмная бирка санного обоза"),
 ("Жалованье десятого караула","Беглый десятник получает соль за десятерых. Принеси его цепочку, ножи охраны и расписку из шахтной кладовой.",((3,15,1),(3,14,2)),"Расписка десятого караула"),
 ("Проба на пустую медь","Пробирщик считает своей долей всё, что просыпалось сквозь чашу. Доставь чашу, две пробы руды и поверочную гирьку из шахты.",((4,14,1),(4,2,2)),"Поверочная гирька"),
 ("Свисток сухого причала","По старому свистку выдают багры с опустевшей пристани. Разыщи свисток, метку багра и накладную из Хранилища.",((5,15,1),(5,14,1)),"Накладная сухого причала"),
 ("Печать после смерти","Сотник умер до составления ведомости. Принеси свежий лист, печать сотника и подлинник из Хранилища.",((8,14,1),(8,15,1)),"Подлинник последней ведомости"),
)
POOLS=((0,1),(2,3),(4,5),(6,),(7,8))
INTERVAL=12*3600


def permit(h,z):
    job=h.get("special_order")
    return bool(job and job["vault"]==z and not job["proof"])


def record(h,r,n,xp):
    job=h.get("special_order")
    if not job:return ""
    _,_,goals,proof=ORDERS[job["kind"]]
    if r["mode"]=="vault" and n==11 and permit(h,r["z"]):
        job["proof"]=True
        found=proof
    elif r["mode"]=="hunt":
        for i,(z,target,count) in enumerate(goals):
            if (r["z"],n)==(z,target) and job["counts"][i]<count:
                job["counts"][i]+=1
                found=SCRAPS[z][n]
                break
        else:return ""
    else:return ""
    job["earned"]+=xp
    return "По поручению · "+found


def training_bundle(h):
    from workshops import BY_ID,RECIPES,gear_names,ingredient_costs
    prof=h.get("profession") or {}
    skill=prof.get("skill",0)
    stock=h.get("supplies",{})
    best=None
    for key in prof.get("book",[]):
        if key not in BY_ID:continue
        z,k=BY_ID[key]
        trade,deep,req=RECIPES[z,k]
        item=gear_names(z)[k]
        if trade!=prof.get("trade") or not req<=skill<min(30*(prof["rank"]+1),req+12) or item in h.get("items",{}):continue
        costs=ingredient_costs(stock,z,k)
        missing={a:v-stock.get(a,0) for a,v in costs.items() if v>stock.get(a,0)}
        ordinary={a:v for a,v in missing.items() if a.startswith(("raw/","shop/"))}
        give={}
        for a,v in sorted(ordinary.items(),key=lambda entry:(entry[0].startswith("shop/"),entry[0])):
            qty=min(4-sum(give.values()),v)
            if qty:give[a]=qty
        if not give:continue
        score=(sum(missing.values())-sum(give.values()),-req,key)
        if best is None or score<best[0]:best=(score,item,give)
    return (best[1],best[2]) if best else ("",{})

def view(h,args,reserved=None):
    from market import capacity,units
    from workshops import add
    from game import btn
    lv=level(h)
    back=[btn("К коменданту","orders")]
    now=int(time.time())
    job=h.get("special_order")
    if not job:
        if lv<15:return "Особые поручения доступны с 15-го уровня.",[back]
        wait=h.get("special_next",0)-now
        if wait>0:return f"Следующее поручение через {(wait+59)//60} мин.",[back]
        pool=POOLS[(lv-1)//10-1]
        seq=h.get("special_count",0)
        kind=pool[seq%len(pool)]
        vault=6 if lv<=20 else 7 if lv<=50 else 8
        ticket=f"{lv}.{seq}"
        job=dict(kind=kind,vault=vault,ticket=ticket,price=8*lv,lv=lv,
                 budget=round((LIMITS[lv]-LIMITS[lv-1])*.18) if lv<60 else 0,
                 earned=0,counts=[0]*len(ORDERS[kind][2]),proof=False)
        if args==["take",ticket]:
            if h["wallet"]<job["price"]:return "Для взноса недостаточно меди.",[back]
            h["wallet"]-=job["price"]
            h["special_order"]=job
            h["special_next"]=now+INTERVAL
            h["special_count"]=seq+1
    title,story,goals,proof=ORDERS[job["kind"]]
    z=job["vault"]
    active="special_order" in h
    ready=job["proof"] and all(job["counts"][i]==count for i,(_,_,count) in enumerate(goals))
    due=min(LIMITS[-1]-h["xp"],max(0,job["budget"]-job["earned"]))
    from workshops import name
    item,give=training_bundle(h)
    detail=", ".join(f"{name(a)} ×{v}" for a,v in give.items())
    reward=f"Для изделия «{item}» · {detail}." if give else "Сейчас нет недостающих обычных материалов для знакомого рецепта с ростом навыка."
    if active and ready and len(args)==3 and args[0]=="claim" and args[1]==job["ticket"] and args[2] in ("auto","forge","sew"):
        if give and units(h,reserved)+sum(give.values())>capacity(h):
            return "Освободи места в сумке: "+str(sum(give.values()))+". Поручение сохранено.",[back]
        for a,v in give.items():add(h,a,v)
        h["xp"]+=due
        h["peak"]=max(h.get("peak",1),level(h))
        del h["special_order"]
        return f"Комендант принял поручение. +{due} опыта. "+reward,[back]
    lines=[title,story,"Охота"]
    for i,(area,n,count) in enumerate(goals):
        lines.append(f"{SCRAPS[area][n]} · {job['counts'][i]}/{count}\n{encounter_area(area,n)} → {monster(area,n)}")
    lines+=["Одиночный тайник",f"{VAULTS[z][0]} → {monster(z,11)} · ур. {rank(z,11)}\n{proof} · {int(job['proof'])}/1",
            f"Взнос · {job['price']} мед. · допуск включён\nОпыт за весь маршрут · {job['budget']}. Зачтено в бою · {job['earned']}.",
            "При сдаче · "+reward]
    rows=[]
    if not active:rows.append([btn(f"Принять · {job['price']} мед.","orders:special:take:"+job["ticket"])])
    elif ready:rows.append([btn("Сдать и получить материалы" if give else "Сдать без материалов","orders:special:claim:"+job["ticket"]+":auto")])
    return "\n\n".join(lines),rows+[back]
