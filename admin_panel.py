"""Private Telegram administration for the shared campaign."""
import hashlib
import localchat
import os
import re
import time
from datetime import datetime, timezone, timedelta

import alpha
import city
import game

PAGE_SIZE = 8
MOSCOW = timezone(timedelta(hours=3))


def allowed(uid):
    return str(uid) in os.environ.get("ADMIN_IDS", "").replace(",", " ").split()


def stamp(value):
    if not value:
        return "нет данных"
    return datetime.fromtimestamp(value, MOSCOW).strftime("%d.%m.%Y %H:%M МСК")


def button(text, action):
    return game.btn(text, "adm:" + action)


def pager(page, count, prefix):
    return [button(label, f"{prefix}:{n}") for label,n in (("‹ Назад",page-1),("Далее ›",page+1))
            if 0 <= n and n*PAGE_SIZE < count]


def chat_archive(db,parts,state):
    cutoff=time.time()-localchat.CHAT_TTL
    rooms=db.execute("""SELECT room,label,COUNT(*),MAX(id) FROM location_messages
        WHERE created>? GROUP BY room ORDER BY MAX(id) DESC""",(cutoff,)).fetchall()
    known={h.get("talk_room"):h.get("talk_label") for h in state["heroes"].values()}
    known.update({"town":"Торговая площадь Гусзка","camp":"Лагерь «У моря»"})
    for step,label in enumerate(("За городскими воротами","Верстовой столб","Рыбная дорога","Костры над отмелью")):
        known[f"road/{step}"]=label
    directory={}
    for room,label,count,_ in rooms:
        key=hashlib.sha256(room.encode()).hexdigest()[:24]
        title=label or known.get(room) or room.removeprefix("hunt/")
        if room.startswith(("party/","vault/")):
            title=title.split(" · ")[0] if label or known.get(room) else "Поход"
            title+=" · "+room.split("/",1)[1]
        directory[key]=(room,title,count)
    home=[button("‹ Панель","home")]
    if parts[0]=="chats":
        page=int(parts[1]) if len(parts)==2 and re.fullmatch(r"[0-9]{1,6}",parts[1]) else 0
        page=min(page,max(0,(len(rooms)-1)//PAGE_SIZE))
        rows=[[button(f"{title} · {count}",f"room:{key}")] for key,(_,title,count)
              in list(directory.items())[page*PAGE_SIZE:(page+1)*PAGE_SIZE]]
        nav=pager(page,len(rooms),"chats")
        if nav:rows.append(nav)
        rows.extend([[button("Обновить","chats")],home])
        return ("Чаты локаций · последние 24 часа" if rooms else "За последние 24 часа сообщений нет."),rows
    back=[button("‹ Чаты локаций","chats")]
    if len(parts) not in (2,3) or parts[1] not in directory:
        return "За последние 24 часа в этой комнате сообщений нет.",[back,home]
    key=parts[1]
    room,title,_=directory[key]
    before=int(parts[2]) if len(parts)==3 and re.fullmatch(r"[0-9]{1,18}",parts[2]) else 2**63-1
    messages=db.execute("""SELECT id,nick,body,created FROM location_messages
        WHERE room=? AND created>? AND id<? ORDER BY id DESC LIMIT 4""",(room,cutoff,before)).fetchall()
    lines=[title+" · последние 24 часа"]
    for _,nick,body,created in reversed(messages[:3]):
        lines.append(f"{stamp(created)} · {nick}\n{body}")
    if not messages:lines.append("Эти сообщения уже вышли из архива.")
    nav=[button("Обновить · последние",f"room:{key}")]
    if len(messages)>3:nav.insert(0,button("‹ Раньше",f"room:{key}:{messages[2][0]}"))
    return "\n\n".join(lines),[nav,back,home]


def render(db, actor, command):
    state = alpha.load(db)
    heroes = state["heroes"]
    names = dict(db.execute("SELECT uid,name FROM alpha_names"))
    def name(uid):
        return names.get(uid) or heroes[uid].get("name") or uid

    now = int(time.time())
    seen = dict(state.get("seen", {}))
    for uid, when in db.execute("SELECT uid,stamp FROM chat_seen"):
        seen[uid] = max(when, seen.get(uid,0))
    fights = state.get("fights", {})
    active = {uid:r for r in fights.values() for uid in r["party"]}
    def online(uid):
        return seen.get(uid,0) > now-600

    home = [button("‹ Панель", "home")]
    parts = command.split(":")
    action = parts[0]
    if action in ("chats","room"):
        return chat_archive(db,parts,state)
    if action == "find":
        query = ":".join(parts[1:]).strip().casefold()
        if query:
            uid = next((i for i in heroes if query in (i,name(i).casefold())),None)
            if uid:
                parts=["hero",uid]
                action="hero"
            else:
                return "Герой с таким ником или ID не найден.", [home]
        else:
            return "Отправь /find и через пробел полный игровой ник или Telegram ID. Например, /find Jambik.", [home]
    if action in ("all","online","fights","log"):
        page = int(parts[1]) if len(parts)==2 and re.fullmatch(r"[0-9]{1,6}",parts[1]) else 0
        if action in ("all","online"):
            ids=sorted((uid for uid in heroes if action=="all" or online(uid)),
                       key=lambda i:(-seen.get(i,0),name(i).casefold(),i))
            entries=[(f"{'🟢' if online(i) else '⚪'} {name(i)} · ур. {game.level(heroes[i])}", "hero:"+i) for i in ids]
            heading="Все герои" if action=="all" else "Онлайн за 10 минут"
        elif action=="fights":
            heading="Сборы и бои"
            entries=[(f"{game.title(r)} · "+(f"раунд {r['round']}" if r["round"] else "сбор")+
                      f" · {len(r['party'])} уч.", "fight:"+k) for k,r in fights.items()]
        else:
            heading="Журнал модерации"
            count=db.execute("SELECT COUNT(*) FROM admin_audit").fetchone()[0]
            page=min(page,max(0,(count-1)//PAGE_SIZE))
            rows=db.execute("SELECT ts,actor,uid,muted FROM admin_audit ORDER BY id DESC LIMIT ? OFFSET ?",
                            (PAGE_SIZE,page*PAGE_SIZE)).fetchall()
            lines=[f"{stamp(t)} · {a} · {names.get(i,i)} · "+("мут на час" if muted else "мут снят") for t,a,i,muted in rows]
            nav=pager(page,count,action)
            return "\n".join([heading,*lines] if lines else [heading,"Записей пока нет."]), ([nav] if nav else [])+[home]
        page=min(page,max(0,(len(entries)-1)//PAGE_SIZE))
        rows=[[button(label,key)] for label,key in entries[page*PAGE_SIZE:(page+1)*PAGE_SIZE]]
        nav=pager(page,len(entries),action)
        return f"{heading} · {len(entries)}",rows+([nav] if nav else [])+[home]
    if action=="fight" and len(parts)==2 and parts[1] in fights:
        r=fights[parts[1]]
        return game.title(r)+"\nУчастники отряда",[[button(name(i),"hero:"+i)] for i in r["party"]]+[home]
    if action in ("hero","confirm","apply") and len(parts)>=2 and parts[1] in heroes:
        uid=parts[1]
        h=heroes[uid]
        row=db.execute("SELECT until,rev FROM admin_mutes WHERE uid=?",(uid,)).fetchone()
        until,rev=row or (0,0)
        muted=until>now
        verb="Снять мут" if muted else "Мут чата на 1 час"
        args=f"{uid}:{int(not muted)}:{rev}"
        if action in ("confirm","apply") and ":".join(parts[1:])==args:
            if action=="confirm":
                return f"{verb} · {name(uid)}?",[[button("Подтвердить","apply:"+args)],[button("Отмена","hero:"+uid)]]
            until=0 if muted else now+3600
            db.execute("INSERT OR REPLACE INTO admin_mutes VALUES(?,?,?)",(uid,until,rev+1))
            db.execute("INSERT INTO admin_audit(ts,actor,uid,muted) VALUES(?,?,?,?)",(now,actor,uid,int(not muted)))
            muted=not muted
            verb="Снять мут" if muted else "Мут чата на 1 час"
            args=f"{uid}:{int(not muted)}:{rev+1}"
        r=active.get(uid)
        activity=("Бой · "+game.title(r) if r["round"] else "Сбор · "+game.title(r)) if r else h.get("talk_label","Гусзк")
        lo,hi=game.bounds(game.attack(h))
        text=[f"{name(uid)} · ID {uid}",f"{game.CLASSES[h['class']][0]} · ур. {game.level(h)} · опыт {h['xp']}",
              ("Онлайн" if online(uid) else "Офлайн")+" · "+activity,"Последняя активность · "+stamp(seen.get(uid)),
              "",f"Удар {lo}–{hi} · крит {game.crit(h)}%",f"Макс. здоровье {game.health(h)} · запас энергии {game.energy(h)}",
              " · ".join(f"{n} {v}" for n,v in zip(game.STAT_NAMES,game.stats(h))),
              f"Смертей {h.get('deaths',0)} · медяков {h['wallet']} · вещей {len(h['items'])}"]
        if muted:text.append("Мут до "+stamp(until))
        return "\n".join(text),[[button("Обновить","hero:"+uid),button(verb,"confirm:"+args)],home]
    project=state.get("city_project")
    lines=["Админ-панель · "+alpha.RELEASE,f"Героев {len(heroes)} · онлайн за 10 мин {sum(online(i) for i in heroes)}",
           f"Активны за сутки {sum(seen.get(i,0)>now-86400 for i in heroes)}",
           f"Сборов {sum(not r['round'] for r in fights.values())} · боёв {sum(bool(r['round']) for r in fights.values())}"]
    if project:
        lines.extend(["",city.PROJECTS[project["kind"]][0],city.summary(project)])
    return "\n".join(lines),[[button("Все игроки","all"),button("Сейчас онлайн","online")],
           [button("Найти героя","find"),button("Сборы и бои","fights")],
           [button("Чаты локаций","chats"),button("Журнал модерации","log")],[button("Обновить","home")]]
