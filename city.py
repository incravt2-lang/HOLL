"""Group projects live inside the same persisted chat transaction as combat and trade."""
import time
from world import HUNT_IDS, ZONES, encounter_area, faction, level, monster, rank

DAY = 86400
# The order gives every group all six projects before one repeats.
PROJECTS = {
    "roads": ("Обезопасить дороги", "Третий воз пришёл без лошади. Возница сам впрягся в оглобли и дотащил муку до ворот. Разведчики отметили три дороги, на которых берут пошлину ножом.",
              "Под охраной Гусзка", "+8% ко всему получаемому опыту."),
    "wall": ("Починить настил на крепостной стене", "Ночью караульный провалился между балок. Камень ещё держит, но доски сгнили у самых гвоздей. Разберите брошенные подводы и верните железо и верёвку со стоянок налётчиков.",
             "Караул на стене", "У всех торговцев Гусзка покупки дешевле на 5%. Вей платит за хлам на 10% больше."),
    "hospital": ("Материалы для лазарета", "Сестра Агна прислала список на обрывке последней чистой простыни. В лазарете пусты полки, а санитар у ворот уже принимает новых больных. Нужны полотно, склянки и мыло.",
                 "Припасы Ордена Матери", "Лечебные зелья и белильная притирка восстанавливают на 15% больше ХП."),
    "papers": ("Вернуть армейские документы", "Ночью незнакомцы назвали пароль и предъявили настоящую печать покойного сотника. У беглецов осталась часть архива. Если вернуть ведомость, печати и карту, караул разберёт их боевые порядки.",
               "Устав полевого караула", "Первый ответный удар каждого противника наносит отряду на 15% меньше урона."),
    "convoy": ("Поиск обоза", "У брода след колёс уходит в воду. За рощей брошены мешки, а из трубы старой печи поднимается дым. Мартин просит пройти все три следа: юный возница впервые сел на козлы.",
               "Прибыл обоз", "У Мартина пять вещей вместо четырёх, цены ниже на 5%. Дополнительный товар доступен сразу."),
    "fires": ("Зажечь огни на трактах", "Прежде с западной башни были видны три огня до моря. Теперь часовой глядит в темноту. Возьмите у коменданта масло с фитилём, очистите чаши и поднимите фонарь над дорогой.",
              "Огни до самого моря", "Работа обоих ремесленников лагеря дешевле на 10%. До лагеря по-прежнему три перехода."),
}
GOALS = {
    "roads": (("Заслон у первой дороги",10),("Заслон у второй дороги",10),("Заслон у третьей дороги",10)),
    "wall": (("Сухие доски",12),("Железные скобы",10),("Просмолённая верёвка",8)),
    "hospital": (("Чистое полотно",15),("Целые склянки",10),("Куски мыла",5)),
    "papers": (("Караульная ведомость",1),("Лист с печатями",1),("Карта дозорных троп",1)),
    "convoy": (("Вытянуть подводу у брода",1),("Отбить товар у налётчиков",1),("Вывести возницу от старой печи",1)),
    "fires": (("Расчистить и зажечь чашу",1),("Отвоевать и зажечь жаровню",1),("Поднять горящий фонарь",1)),
}
DELIVER = {"wall","hospital","papers"}

def sources(kind, lv):
    hunts = [(z,n) for z in range(len(ZONES)) for n in HUNT_IDS]
    def nearest(pool, used=()):
        return min(pool,key=lambda p:(encounter_area(*p) in used,abs(rank(*p)-lv),rank(*p)))
    bandits = [p for p in hunts if faction(*p) in ("robber","oath")]
    if kind=="papers":
        return [nearest([p for p in bandits if faction(*p)==group]) for group in ("oath","robber")] + [
            nearest([(z,n) for z in range(len(ZONES)) for n in (5,8)])]
    if kind=="roads":
        result=[]
        for _ in range(3):
            result.append(nearest(bandits,[encounter_area(*p) for p in result]))
        return result
    # Distinct trails; supplies can be recovered after clearing the marked site.
    first=nearest(hunts)
    second=nearest(bandits,[encounter_area(*first)])
    third_pool = [(z,n) for z in range(len(ZONES)) for n in (3,6)] if kind=="hospital" else hunts
    return [first,second,nearest(third_pool,[encounter_area(*first),encounter_area(*second)])]

def current(s,now=None):
    now=time.time() if now is None else now
    q=s.get("city_project")
    if q and (not q["until"] or now<q["until"]): return q
    seq=q["seq"]+1 if q else 0
    kind=tuple(PROJECTS)[seq%len(PROJECTS)]
    heroes=s["heroes"].values()
    lv=round(sum(level(h) for h in heroes)/max(1,len(s["heroes"])))
    q=dict(seq=seq,kind=kind,targets=sources(kind,lv),counts=[0,0,0],cargo={},oil={},cleared=False,until=0)
    s["city_project"]=q
    return q

def buff(s):
    q=s.get("city_project",{})
    return q.get("kind") if time.time()<q.get("until",0) else None

def price(cost,percent):
    return max(1,cost*(100-percent)//100)

def earned(xp,active):
    return (xp*108+50)//100 if active=="roads" else xp

def restore(amount,active):
    return (amount*115+50)//100 if active=="hospital" else amount

def location(pair):
    z,n=pair
    if n not in HUNT_IDS: return ZONES[z][2][(n-3)//3][0]
    return encounter_area(z,n)

def summary(q):
    kind=q["kind"]
    if q["until"]:
        mins=max(0,int((q["until"]-time.time()+59)//60))
        return f"{PROJECTS[kind][2]} · осталось {mins//60} ч {mins%60} мин.\n{PROJECTS[kind][3]}"
    if kind=="roads":
        return f"Победы {min(45,sum(q['counts']))}/45 · дороги под охраной {sum(n>=10 for n in q['counts'])}/3"
    return "\n".join(f"{label} · {n}/{need}" for n,(label,need) in zip(q["counts"],GOALS[kind]))

def complete(q):
    kind=q["kind"]
    if all(v>=need for v,(_,need) in zip(q["counts"],GOALS[kind])) and (kind!="roads" or sum(q["counts"])>=45):
        q.update(until=int(time.time())+DAY,cargo={},oil={})
        return "Городское дело завершено! "+PROJECTS[kind][2]+" · 24 часа."
    return ""

def victory(s,party,z,n,mode):
    q=current(s)
    if q["until"]: return ""
    kind=q["kind"]
    for i,p in enumerate(q["targets"]):
        if tuple(p)!=(z,n) or mode!=("hunt" if n in HUNT_IDS else "raid"): continue
        label,need=GOALS[kind][i]
        if kind=="roads":
            q["counts"][i]+=1
        elif kind in DELIVER:
            if q["counts"][i]>=need: continue
            for uid in party:
                bag=q["cargo"].setdefault(uid,[0,0,0])
                bag[i]=min(need-q["counts"][i],bag[i]+1)
            return f"[Задания] Для коменданта: {label}. Доставьте находку в город."
        elif i==1 and not q["counts"][i]:
            if kind=="fires":
                q["cleared"]=True
                return "Караулка свободна. Принесите масло к жаровне."
            q["counts"][i]=1
        else: continue
        return complete(q) or "Общее дело · "+summary(q)
    return ""

def button(label,action):
    return [{"text":label,"callback_data":action}]

def card(s,uid,args,busy=False):
    q=current(s)
    kind=q["kind"]
    title,story,reward,effect=PROJECTS[kind]
    prefix=f"city:{q['seq']}:"
    note=""
    if not busy and not q["until"] and args[:1]==[str(q["seq"])]:
        action=args[1:]
        if action==["give"] and kind in DELIVER:
            held=q["cargo"].pop(uid,[0,0,0])
            for i,(_,need) in enumerate(GOALS[kind]):
                q["counts"][i]+=min(held[i],need-q["counts"][i])
            if any(held): note=complete(q) or "Комендант принял груз."
        if action==["oil"] and kind=="fires":
            q["oil"][uid]=True
            note="Получены кувшин масла и фитиль для одной жаровни."
        if len(action)==2 and action[0]=="trail" and action[1] in ("0","1","2") and kind in ("convoy","fires"):
            i=int(action[1])
            if not q["counts"][i] and (i!=1 or q["cleared"]) and (kind!="fires" or q["oil"].get(uid)):
                scenes={
                    "convoy": ("Под ободом чёрная жижа. Возница подложил под колесо плащ, но телега осела ещё глубже.", "", "За печью тёплая зола. Из-под рогожи выглядывает мальчишка. Он берёг лошадь и всю ночь боялся окликнуть прохожих."),
                    "fires": ("Чаша полна дождевой воды. Сквозь прошлогодний пепел пробилась трава.", "У брошенной караулки валяется закопчённая решётка. Теперь можно поставить её на место и запалить фитиль.", "Мачта цела. Верёвка задубела от соли, но блок ещё ходит. С башни ждут света."),
                }
                return location(q["targets"][i])+"\n\n"+scenes[kind][i], [
                    button(GOALS[kind][i][0],prefix+f"site:{i}"),button("К общему делу","city")]
        if len(action)==2 and action[0]=="site" and action[1] in ("0","1","2") and kind in ("fires","convoy"):
            i=int(action[1])
            allowed=(i!=1 or (kind=="fires" and q["cleared"]))
            if allowed and not q["counts"][i] and (kind!="fires" or q["oil"].pop(uid,False)):
                q["counts"][i]=1
                note=complete(q) or GOALS[kind][i][0]+" · выполнено."
    lines=[title,story]
    rows=[]
    if note: lines.append(note)
    if q["until"]:
        lines.append("Дело завершено\n"+summary(q))
    else:
        lines.append("Общий прогресс · без срока"+("\n"+summary(q) if kind=="roads" else ""))
        if kind=="roads": lines.append("Одержите 45 побед суммарно, хотя бы по 10 на каждой дороге.")
        held=q["cargo"].get(uid,[0,0,0])
        for i,((label,need),p) in enumerate(zip(GOALS[kind],q["targets"])):
            z,n=p
            fight=kind in DELIVER or kind=="roads" or i==1
            text=f"{label} · {q['counts'][i]}/{need}" if kind!="roads" else f"{label} · побед {q['counts'][i]}"
            text+="\n"+location(p)
            if fight: text+=f" · {monster(z,n)}, ур. {rank(z,n)}"
            if kind in DELIVER: text+=f" · на руках {held[i]}"
            lines.append(text)
            if busy or (q["counts"][i]>=need and kind!="roads"): continue
            if fight and not (kind=="fires" and i==1 and q["cleared"]):
                cmd=f"new:hunt:{z}:{n}" if n in HUNT_IDS else f"new:raid:{z}:{(n-3)//3}"
                rows.append(button(f"К цели {i+1} · {monster(z,n)}",cmd))
            elif kind!="fires" or q["oil"].get(uid):
                rows.append(button(f"Осмотреть · {location(p)}",prefix+f"trail:{i}"))
        if kind=="fires" and not busy and not q["oil"].get(uid): rows.append(button("Взять масло и фитиль",prefix+"oil"))
        if any(held) and not busy: rows.insert(0,button("Передать груз коменданту",prefix+"give"))
        lines.append("Награда на сутки\n"+reward+" · "+effect)
    rows.append(button("К коменданту","orders"))
    return "\n\n".join(lines),rows
