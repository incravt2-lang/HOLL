"""Telegram transport. Run one polling process per token."""
import admin_panel
import hashlib
import alpha
import localchat
import pets
import forks
import city
import zipfile
from functools import lru_cache
import uuid
import getpass
import json
import os
import re
import warnings
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from world import HUNT_IDS
from market import POTIONS, SCROLLS
from game import CLASSES, TITLE, btn, play, board, level, migrate, title, target

COMMANDS = {"town":"Город и торговцы","vault":"Редкие одиночные подземелья","zones":"Карта уровней","book":"Бестиарий и добыча","hunt":"Одиночная или совместная охота","start":"Меню свободной игры","hero":"Лист героя и выбор класса",
            "raid":"Сбор отряда и бой","bag":"Снаряжение","help":"Правила игры"}

class ApiError(Exception):
    def __init__(self, code, description, delay=2, method="API"):
        self.method = method
        self.code = code
        self.delay = delay
        super().__init__(description)

ART_DIR = Path(__file__).with_name("art")
ANIMATED_SCENES = {"gate", "raid", "commandant"}
FILE_IDS = {}

@lru_cache(maxsize=1)
def packed_art():
    archive=Path(__file__).with_name("hunt-art.zip")
    return zipfile.Path(archive) if archive.is_file() else None

def picture_file(art):
    name=art if art.endswith(".mp4") else art+".jpg"
    local=ART_DIR/name
    pack=packed_art()
    if pack is not None and (pack/name).is_file():
        return pack/name
    return local


def api(method, upload=None, **data):
    if upload is None:
        payload = json.dumps(data).encode()
        content_type = "application/json"
    else:
        boundary = uuid.uuid4().hex
        chunks = []
        for key,value in data.items():
            field = value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{field}\r\n'.encode())
        filename = upload.name
        mime = "video/mp4" if filename.endswith(".mp4") else "image/jpeg"
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="picture"; filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
        chunks.extend((upload.read_bytes(),f'\r\n--{boundary}--\r\n'.encode()))
        payload = b"".join(chunks)
        content_type = "multipart/form-data; boundary="+boundary
    request = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}",
                                     data=payload,headers={"Content-Type":content_type})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)["result"]
    except urllib.error.HTTPError as exc:
        try:
            body = json.load(exc)
        except ValueError:
            body = {}
        raise ApiError(exc.code, body.get("description","Telegram API"),
                       body.get("parameters",{}).get("retry_after",2), method) from None

MENU = [
    [("Герой","hero"),("Гусзк","town")],
    [("Карта","zones"),("Подземелья","dungeons"),("Отряды","teams")],
    [("Кодекс","codex")],
]
ACTIONS = {"patha","pathb","pathok","coinok","faceboss","turnback","exitfinish","pits","loft","closevote","join","go","leave","hit","block","skill","finish","heal","healok","ward","fury"} | set(POTIONS)

def init_cards(db):
    db.execute("CREATE TABLE IF NOT EXISTS trade_screen(uid TEXT PRIMARY KEY, view TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS cards(chat INTEGER, slot TEXT, message INTEGER, "
               "topic INTEGER, PRIMARY KEY(chat,slot), UNIQUE(chat,message))")
    db.execute("CREATE TABLE IF NOT EXISTS card_media(chat INTEGER,message INTEGER,art TEXT,view TEXT,PRIMARY KEY(chat,message))")
    # Adopt the most recent personal card per player from earlier, topic-scoped versions.
    with db:
        for chat,slot,msg,topic in db.execute(
                "SELECT * FROM cards WHERE slot LIKE 'personal:%:%' ORDER BY message DESC").fetchall():
            owner = "player:"+slot.rsplit(":",1)[1]
            db.execute("UPDATE OR IGNORE cards SET slot=? WHERE chat=? AND message=?",(owner,chat,msg))

def listing(state):
    rows = []
    for r in state["fights"].values():
        if r["round"] or r["mode"]=="vault" or len(r["party"])>=6: continue
        leader = state["heroes"][r["party"][0]]["name"]
        rows.append([btn(f"{title(r)} · {leader} · {len(r['party'])}/6","join:"+r["id"])])
    return ("Открытые сборы всех групп. Выбери отряд, чтобы вступить." if rows else "Открытых сборов пока нет."),rows

def screen(db,chat,uid,name,topic,text,rows,*,open_here=False):
    slot = "player:"+uid
    record = db.execute("SELECT message,topic FROM cards WHERE chat=? AND slot=?",(chat,slot)).fetchone()
    if open_here and record and (record[1] or 0)!=(topic or 0):
        record = None
    media = db.execute("SELECT art FROM card_media WHERE chat=? AND message=?",(chat,record[0])).fetchone() if record else None
    return dict(chat=chat,slot=slot,previous_art=media[0] if media else None,target=record[0] if record else None,thread=record[1] if record else topic,
                text=f"🎲 {name}\n{text}",rows=rows,notice=False,cb=None)

def player_action(db,state,chat,uid,name,topic,cmd,cb):
    migrate(state)
    fights = state["fights"]
    heroes = state["heroes"]
    watches = state.setdefault("open_boards",{})
    op,_,key = cmd.partition(":")
    battle_id = key.split(":")[0] if op in ACTIONS else None
    before = list(fights.get(battle_id,{}).get("party",[]))
    previous = fights.get(battle_id,{})
    previous_path_coin=previous.get("path_coin")
    previous_coin=previous.get("exit_coin")
    old_exit=dict(previous["exit_votes"]) if "exit_votes" in previous else None
    old_votes=dict(previous.get("votes",{}))
    previous_route=previous.get("route")
    previous_move = previous.get("moves",{}).get(uid)
    previous_drink = previous.get("drank",{}).get(uid)
    old_round = fights.get(battle_id,{}).get("round")
    mine = next((r for r in fights.values() if uid in r["party"]),None)
    hero = heroes.get(uid)
    event_art = None
    encounter = pets.arrive(hero) if cmd=="town" and hero and not mine else None
    if encounter:
        pet, ticket = encounter
        label, story = pets.PETS[pet]
        msg = label + "\n\n" + story
        rows = [[btn("Погладить", "pet:"+ticket)]]
        event_art = "pet_"+pet
    elif op=="pet":
        if not hero or mine or not pets.stroke(hero, key):
            return dict(chat=chat, cb=cb, notice=True, text="Эта встреча уже закончилась или сейчас идёт поход.")
        msg = ("Добрый знак\n\nСквозь тучи пробивается солнце. Вы поднимаете лицо к свету и на миг закрываете глаза. "
               "Вокруг всё так же скрипят телеги и стучат по камню сапоги, а вы стоите посреди площади и улыбаетесь."
               "\n\n+5% ко всему получаемому опыту на 10 минут.")
        if city.buff(state)=="roads":
            msg += "\nВместе с бонусом города — +13% к опыту."
        rows = [[btn("В город","nav:town")]]
        event_art = "blessing_"+hero["class"]
    elif cmd=="start":
        hero = heroes.get(uid)
        msg = (f"{name} · {CLASSES[hero['class']][0]} · ур. {level(hero)}\n"
               f"Место · {hero.get('talk_label','Торговая площадь Гусзка')}") if hero else f"{TITLE} · выбери класс в разделе «Герой»"
        rows = [[btn(label,"nav:"+dest) for label,dest in row] for row in MENU]
        msg += f"\n\n{alpha.RELEASE} · онлайн за 10 мин: {len(state.get('seen',{}))}"

        if hero and hero.get("coast_trip") and not mine:
            trip=hero["coast_trip"]
            label="К кострам лагеря" if trip["step"]==3 and not trip.get("returning") and not trip.get("waiting") else "Продолжить путь"
            rows.insert(0,[btn(label,"road")])

        if hero and hero.get("last_result"): rows.append([btn("Итоги последнего боя","nav:report")])
        if mine: rows.insert(0,[btn("Вернуться в поход","nav:current")])
    elif cmd=="hero" and hero:
        msg=f"{CLASSES[hero['class']][0]} · ур. {level(hero)}"
        rows=[[btn("Лист персонажа","nav:diary"),btn("Сумка","nav:bag")]]
        if hero.get("profession"):
            trade=hero["profession"]["trade"]
            rows.append([btn("Кузнечное дело" if trade=="forge" else "Портняжное дело","work:"+trade)])
    elif cmd=="codex":
        msg="Кодекс"
        rows=[[btn("Хроника","nav:lore"),btn("Бестиарий","nav:book"),btn("Правила","nav:help")],[btn("Найденные записки","nav:notes")]]
    elif cmd=="dungeons":
        msg="Подземелья"
        rows=[[btn("Групповые","nav:raid"),btn("Одиночные","nav:vault")]]
    elif cmd=="report":
        report = heroes.get(uid,{}).get("last_result","Завершённых боёв пока нет.")
        # Older saves include a command footer after the combat report.
        footer = report.rsplit("\n",1)[-1]
        if footer in ("/bag — снаряжение · /book — бестиарий", "/hunt — новая охота", "/hunt — вернуться на охоту"):
            report = report.rsplit("\n",1)[0]
        msg,rows = report,[]
    elif cmd=="teams" and not mine and uid in heroes:
        msg,rows = listing(state)
        rows.append([btn("Обновить список","nav:teams"),btn("Собрать отряд","nav:raid")])
    elif cmd=="current" and not mine:
        msg,rows = "Сейчас ты в лагере.",[]
    elif cmd in ("teams","current") and mine:
        msg,rows = board(state,mine,uid)
    else:
        msg,rows = play(state,uid,name,"hero" if uid not in heroes and op not in ("class","bio","help","lore","notes") else cmd)
    ended = battle_id and before and battle_id not in fights
    if ended and old_round:
        for who in before: heroes[who]["last_result"] = msg
    if cb and not rows and "\n" not in msg and not ended and cmd!="current":
        return dict(chat=chat,cb=cb,notice=True,text=msg)
    mine = next((r for r in fights.values() if uid in r["party"]),None)
    if op=="leave" and uid in before and not mine:
        msg,rows = "Ты вышел из сбора.",[]
    viewing = mine and any(b["callback_data"].split(":")[0] in ACTIONS and mine["id"] in
                           b["callback_data"].split(":")[1:2] for row in rows for b in row)
    if viewing:
        watches[uid] = {"fight":mine["id"],"chat":chat,"topic":topic}
    else:
        watch=watches.get(uid)
        if not isinstance(watch,dict) or (watch["chat"]==chat and (watch.get("topic") or 0)==(topic or 0)):
            watches.pop(uid,None)
    result_rows=list(rows) if ended else []
    menu = [btn("☰ Меню","nav:start")]
    if op in ("diary","bag") and hero:
        rows=rows+[[btn("‹ Герой","nav:hero")]]
    if cmd in ("lore","book","help"):
        menu.insert(0,btn("‹ Кодекс","nav:codex"))
    elif cmd in ("raid","vault") and not mine:
        menu.insert(0,btn("‹ Подземелья","nav:dungeons"))
    if cmd=="raid" and not mine: rows=[[btn("Открытые сборы","nav:teams")]]+rows
    if cmd!="start" and not event_art: rows = rows+[menu]
    result = screen(db,chat,uid,name,topic,msg,rows,open_here=not cb)
    if cmd=="start" and hero: result["text"]=msg
    result["cb"] = cb
    if event_art:
        result["art"] = event_art
    elif ended and old_round:
        result["art"] = fight_picture(previous)
        for who in before:
            heroes[who]["report_art"] = result["art"]
    elif op=="city" and uid in heroes:
        result["art"]="city_"+state["city_project"]["kind"]
    elif viewing:
        result["art"] = fight_picture(mine)
    else:
        result["art"] = screen_picture(cmd, heroes.get(uid))
    current = fights.get(battle_id,{})
    changed = battle_id and before and (ended or old_round!=current.get("round") or
                                       previous_path_coin!=current.get("path_coin") or previous_coin!=current.get("exit_coin") or old_exit!=current.get("exit_votes") or old_votes!=current.get("votes",{}) or previous_route!=current.get("route") or before!=current.get("party") or previous_move!=current.get("moves",{}).get(uid)
                                       or previous_drink!=current.get("drank",{}).get(uid))
    if changed:
        others = []
        for who in before:
            watch=watches.get(who)
            if isinstance(watch,str):
                # Alpha 0.1 displayed all party cards in the originating group.
                watch={"fight":watch,"chat":previous.get("chat",chat),"topic":previous.get("topic",topic)}
            if who==uid or not watch or watch["fight"]!=battle_id: continue
            if ended:
                other_text,other_rows = msg,result_rows
                watches.pop(who,None)
            else:
                other_text,other_rows = board(state,fights[battle_id],who)
            other=screen(db,watch["chat"],who,heroes[who]["name"],watch["topic"],other_text,other_rows+[menu],open_here=True)
            if other["target"]:
                other["edit_only"]=True
                others.append(other)
        for out in others:
            out["art"] = fight_picture(current or previous)
        result["others"] = others
    return result

def fight_picture(fight):
    if "votes" in fight: return "fork_"+forks.key(fight)
    mode = fight["mode"]
    if mode == "hunt":
        return hunt_picture(fight)
    if fight["round"]:
        if fight.get("route")=="loft" and fight["room"]==1:
            return "room_tannery_loft"
        return f"room_{fight['z']}_{target(fight)}"
    if mode == "vault":
        return f"vault_{fight['z']}"
    return f"raid_{fight['z']}_{fight['choice']}"

def screen_picture(command, hero):
    op, *args = command.split(":")
    if op=="band" and args: return {"raid":"raid","vault":"vault","book":"book"}.get(args[0],"world")
    if op=="craft": return "coast_veya" if args[:1]==["veya"] else "coast_hariton"
    if op=="road": return "coast_road" if hero and hero.get("coast_trip") else "town"
    if op=="notes": return "lore"
    if op=="codex": return "book"
    if op=="dungeons": return "raid"
    if op == "bio" and args:
        return "hero_" + args[0]
    if op in ("hero", "diary", "class", "skills", "train") or (not hero and op not in ("start","help","lore")):
        return "hero_" + hero["class"] if hero else "teams"
    if op == "report":
        return hero.get("report_art","teams") if hero else "teams"
    if op=="travel" and len(args)==2:return ("upper_" if args[1]=="1" else "zone_")+args[0]
    if op == "area" and len(args) in (2,3):
        mode, zone = args[:2]
        if mode!="vault" and args[2:]==["1"]: return "upper_"+zone
        return ("vault_" if mode=="vault" else "zone_") + zone
    if op in ("entry","loot") and len(args)==2 and args[1].isdigit():
        zone, index = args[0], int(args[1])
        if index in HUNT_IDS:
            return f"beast_{zone}_{index}"
        return f"room_{zone}_{index}"
    if op == "shop" and len(args)==3:
        action = args[-1]
        if action.startswith("buy-"):
            return "scribe" if action[4:] in SCROLLS else "apoth"
        for prefix, scene in (("supply-","sell"),("sellpage","sell"),("gear-","sell"),("cash","sell"),
                              ("key-","keys"),("upgrade","bags"),("stock-","armourer")):
            if action.startswith(prefix):
                return scene
        if action in ("town","armourer","apoth","scribe","sell","bags","keys"):
            return action
    return {"start":"gate","bag":"bag","materials":"bag","spoils":"bag","slot":"bag","off":"bag","dress":"bag",
            "hunt":"world","zones":"world","raid":"raid","vault":"vault","book":"book",
            "orders":"commandant","town":"town","teams":"teams","current":"teams","leave":"teams",
            "barter":"barter","lore":"lore","help":"help"}.get(op,"gate")

def hunt_picture(fight):
    # A migrated pre-zone hunt may reference a dungeon inhabitant.
    idx = fight.get("legacy_target",fight["choice"])
    return f"beast_{fight['z']}_{idx}" if idx in HUNT_IDS else f"room_{fight['z']}_{idx}"

def caption_pages(text):
    # Allow for non-BMP characters and keep paragraphs readable on phones.
    pages = []
    while len(text.encode("utf-16-le"))>2000:
        end = 1000
        while len(text[:end].encode("utf-16-le"))>2000: end-=1
        cut = text.rfind("\n",0,end+1)
        if cut<=0: cut=end
        pages.append(text[:cut])
        text=text[cut:].lstrip("\n")
    return pages+[text]

def view_key(r):
    return hashlib.sha256(json.dumps([r["text"],r["rows"]],ensure_ascii=False).encode()).hexdigest()[:12]

def shared_action(db,state,chat,uid,topic,cmd,cb,m,actor):
    chat_id=chat["id"]
    def card(text,rows):
        out=screen(db,chat_id,uid,"Гусзк",topic,text,rows,open_here=True)
        out.update(cb=cb,art="gate")
        return out
    now=time.time()
    seen={i:t for i,t in state.get("seen",{}).items() if t>now-600}
    for other,stamp in db.execute("SELECT uid,stamp FROM chat_seen WHERE stamp>?",(now-600,)):
        seen[other]=max(stamp,seen.get(other,0))
    if uid in state["heroes"] or uid in state.get("choices",{}):seen[uid]=now
    state["seen"]=seen
    choices=state.get("choices",{}).get(uid)
    if choices:
        selected=cmd.partition(":")[2] if cmd.startswith("legacy:") else ""
        if selected not in choices:
            rows=[]
            for source,h in choices.items():
                cls=CLASSES[h["class"]][0]
                rows.append([btn(f"{cls} · ур. {level(h)} · {h['wallet']} мед. · группа {source}","legacy:"+source)])
            return card("Перепись Гусзка · выбери героя\nУ героев поровну опыта. В общий мир перейдёт выбранный герой со своей сумкой.",rows)
        state["heroes"][uid]=choices[selected]
        del state["choices"][uid]
    hero=state["heroes"].get(uid)
    registered=db.execute("SELECT name FROM alpha_names WHERE uid=?",(uid,)).fetchone()
    if hero and not registered:
        reason=""
        if cmd=="name_reply":
            value=m.get("text","")
            if not alpha.NAME.fullmatch(value):reason="Писарь просит переписать имя по правилам."
            else:
                try:db.execute("INSERT INTO alpha_names VALUES(?,?)",(uid,value))
                except sqlite3.IntegrityError:reason="Это имя уже записано за другим героем."
                else:
                    hero["name"]=value
                    db.execute("DELETE FROM alpha_prompt WHERE uid=?",(uid,))
                    return card("В городскую книгу внесён "+value+".",[[btn("Продолжить","nav:resume")]])
        return alpha.prompt(db,uid,chat_id,topic,cb,reason)
    mine=next((r for r in state["fights"].values() if uid in r["party"]),None)
    if mine and cmd.startswith("new:"):
        return card("У тебя уже есть поход. Можно открыть его в этой группе.",
                    [[btn("Открыть поход","nav:current")],[btn("‹ Назад в меню","nav:start")]])
    if cmd=="resume":cmd="current" if mine else "start"
    if cmd.startswith("legacy:"):cmd="start"
    name=registered[0] if registered else actor.get("first_name","Путник")[:32]
    trip=(hero or {}).get("coast_trip",{})
    if not mine and (trip.get("returning") or trip.get("step")==3 and not trip.get("waiting")):
        if cmd.split(":")[0] in {"town","orders","shop","travel","new","join"}:
            cmd="road" if trip.get("returning") else f"road:{trip['id']}:return"
    if hero and not mine and (cmd in ("town","orders") or cmd.startswith(("orders:", "shop:"))):
        hero.pop("hunting_ground",None)
        hero.pop("coast_trip",None)
    result=player_action(db,state,chat_id,uid,name,topic,cmd,cb)
    for r in state["fights"].values():
        if "chat" not in r:
            place=chat.get("title") or str(chat_id)
            if topic:place+=f" · тема {topic}"
            r.update(chat=chat_id,topic=topic,place=place)
    if not registered and uid in state["heroes"]:
        seen[uid]=now
        return alpha.prompt(db,uid,chat_id,topic,cb)
    return result

TRADE_NOTICE="Доступен обмен!"

def recipients(state):
    return {o["to"] for o in state.get("offers",{}).values()}

def trade_banner(card,enabled):
    prefix=TRADE_NOTICE+"\n"
    card["text"]=card["text"].removeprefix(prefix)
    card["rows"]=[row for row in card["rows"] if not any(b.get("callback_data")=="nearby:inbox" for b in row)]
    if enabled:
        card["text"]=prefix+card["text"]
        card["rows"].insert(0,[btn("Посмотреть обмен","nearby:inbox")])
        card["page"]=0

def notify_trade(db,result,before,after,state,username):
    cards=[result,*result.get("others",[])]
    shown=set()
    for card in cards:
        slot=card.get("slot","")
        if slot.startswith("player:") and not card.get("notice"):
            who=slot.split(":",1)[1];shown.add(who)
            trade_banner(card,who in after)
    for who in (before^after)-shown:
        row=db.execute("SELECT view FROM trade_screen WHERE uid=?",(who,)).fetchone()
        if row:
            card=json.loads(row[0])
        else:
            # Existing Alpha cards can receive an invitation before the recipient's first new action.
            slot="player:"+who
            old=db.execute("SELECT chat,topic FROM cards WHERE slot=? ORDER BY rowid DESC LIMIT 1",(slot,)).fetchone()
            if not old:continue
            h=state["heroes"][who]
            r=next((r for r in state["fights"].values() if who in r["party"]),None)
            text,rows=board(state,r,who) if r else (h["talk_label"],[])
            rows=rows+[[btn("Игроки рядом","nearby")],[{"text":"Открыть чат","url":f"https://t.me/{username}?startapp=chat"}],[btn("☰ Меню","nav:start")]]
            card=screen(db,old[0],who,h["name"],old[1],text,rows)
            card["art"]=fight_picture(r) if r else card.get("previous_art") or "gate"

        current=db.execute("SELECT message FROM cards WHERE chat=? AND slot=?",(card["chat"],card["slot"])).fetchone()
        if not current or current[0]!=card["target"]:continue
        trade_banner(card,who in after)
        card["edit_only"]=True
        result.setdefault("others",[]).append(card)

def process(db, update, username):
    """Commit the game and the pending response together before sending."""
    key = update["update_id"]
    with db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute("SELECT result FROM pending WHERE id=?", (key,)).fetchone()
        cb = update.get("callback_query", {})
        m = cb.get("message") or update.get("message", {})
        chat = m.get("chat", {})
        actor = cb.get("from") or m.get("from", {})
        if not chat: return
        if existing:
            saved=json.loads(existing[0])
            if not saved.get("private_admin") or (chat.get("type")=="private" and
                    actor.get("id")==chat["id"] and admin_panel.allowed(chat["id"])):
                return saved
        if not cb and m.get("sender_chat") and chat.get("type") in ("group","supergroup"):
            command = (m.get("text") or "").strip().lower()
            if command in ("/start","/start@"+username.lower()):
                return dict(chat=chat["id"],message=m["message_id"],cb=None,notice=False,rows=[],
                            text="Чтобы открыть личную карточку, отправь команду от своего аккаунта. Сейчас отправителем указан чат.",
                            thread=m.get("message_thread_id") if m.get("is_topic_message") else None)
            return
        if not actor or actor.get("is_bot"): return
        if chat["type"]=="private":
            uid=str(actor["id"])
            text="Игра проходит в группах. Открой игровую группу и отправь /start@"+username+"."
            rows=[]
            words=(m.get("text") or "").strip().split(maxsplit=1)
            command=(words[0] if words else "").split("@")[0].lower()
            if not cb and command=="/id":
                text=f"Твой Telegram ID · {uid}"
            elif str(chat["id"])==uid and admin_panel.allowed(uid):
                data=cb.get("data","")
                action=data[4:] if cb and data.startswith("adm:") else "home"
                if not cb and command=="/find":
                    action="find:"+(words[1] if len(words)>1 else "")
                text,rows=admin_panel.render(db,uid,action)
            result=dict(chat=chat["id"],message=m["message_id"],cb=cb.get("id"),notice=False,text=text,rows=rows,thread=None)
            result["private_admin"]=str(chat["id"])==uid and admin_panel.allowed(uid)
            db.execute("INSERT OR REPLACE INTO pending VALUES (?,?)",(key,json.dumps(result)))
            return result
        if cb:
            cmd = cb.get("data", "")
        else:
            word = (m.get("text") or " ").split()
            topic=m.get("message_thread_id") if m.get("is_topic_message") else None
            reply_id=m.get("reply_to_message",{}).get("message_id")
            if reply_id and alpha.is_reply(db,str(actor["id"]),chat["id"],topic,reply_id):
                cmd="name_reply"
            elif word and word[0].startswith("/"):
                cmd, _, mention = word[0][1:].partition("@")
                if cmd not in COMMANDS or (mention and mention.lower()!=username.lower()): return
            else:return
        if cb and cmd.startswith("nav:"):
            cmd = cmd[4:]
        if chat["type"] in ("group","supergroup"):
            uid = str(actor["id"])
            if cb:
                owner = db.execute("SELECT slot FROM cards WHERE chat=? AND message=?",
                                   (chat["id"],m["message_id"])).fetchone()
                if not owner or owner[0]!="player:"+uid:
                    return dict(chat=chat["id"],cb=cb["id"],notice=True,
                                text="Открой свою карточку. Если её ещё нет, отправь /start@"+username+".")
            if cmd.startswith("adm:"): return dict(chat=chat["id"],cb=cb.get("id"),notice=True,text="Кнопка недоступна.")
            state=alpha.load(db)
            if uid in state["heroes"]:
                db.execute("INSERT OR REPLACE INTO chat_seen VALUES(?,?)",(uid,time.time()))
            before_offers=recipients(state)
            if cb and cmd.startswith("page:") and db.execute("SELECT 1 FROM alpha_names WHERE uid=?",(uid,)).fetchone():
                rec = db.execute("SELECT view FROM card_media WHERE chat=? AND message=?",(chat["id"],m["message_id"])).fetchone()
                parts = cmd.split(":")
                view = json.loads(rec[0]) if rec and rec[0] else None
                if view and len(parts)==3 and parts[1]==view_key(view) and parts[2] in map(str,range(len(caption_pages(view["text"])))):
                    view.update(cb=cb["id"],page=int(parts[2]),target=m["message_id"],previous_art=view["art"])
                    return view
                return dict(chat=chat["id"],cb=cb["id"],notice=True,text="Карточка уже обновилась.")
            topic = m.get("message_thread_id") if m.get("is_topic_message") else None
            result=shared_action(db,state,chat,uid,topic,cmd,cb.get("id"),m,actor)
            if cb and not result.get("notice"):
                result["target"]=m["message_id"]
                for other in result.get("others",[]):
                    other["edit_only"]=True
            alpha.save(db,state)
            for card in [result,*result.get("others",[])]:
                slot=card.get("slot","")
                if not slot.startswith("player:") or card.get("notice"):continue
                who=slot.split(":",1)[1]
                h=state["heroes"].get(who,{})
                room=h.get("talk_room")
                if room and db.execute("SELECT 1 FROM alpha_names WHERE uid=?",(who,)).fetchone():
                    label="Чат отряда" if room.startswith("party/") else "Чат локации"
                    if cmd.split(":")[0] in ACTIONS|{"town","road","current","travel","new"}:
                        card["text"]+="\n\nМесто · "+h["talk_label"]
                    art=card.get("art","")
                    party_view=room.startswith(("party/","vault/")) and (art.startswith(("room_","raid_","vault_","fork_")))
                    public_view=(art=="town" or art=="coast_road" or party_view or
                                 (room.startswith("hunt/") and (cmd.startswith("travel:") or art.startswith("beast_"))))
                    if not public_view: continue
                    menus=[row for row in card["rows"] if any(b.get("callback_data")=="nav:start" for b in row)]
                    card["rows"]=[row for row in card["rows"] if row not in menus]
                    if not any(b.get("callback_data") in ("nearby","nav:nearby") for row in card["rows"] for b in row):
                        card["rows"].append([btn("Игроки рядом","nearby")])
                    card["rows"].append([{"text":label,"url":f"https://t.me/{username}?startapp=chat"}])
                    card["rows"].extend(menus)
            notify_trade(db,result,before_offers,recipients(state),state,username)
        else:
            return
        db.execute("INSERT INTO pending VALUES (?,?)", (key,json.dumps(result)))
        return result

def combat_entities(text):
    patterns = (
        ("bold",r"^Доступен обмен!$"),
        ("bold",r"\[(Оружие|Броня|Аксессуары|Задания и ремёсла|Задания|Записки|Монеты|Трофеи|Материал|Для рецепта|Образец|Хлам)\]"),
        ("bold", r"^(?:[1-4]\. .+|Лавка Мартина|Аптека Лады|Писец Тиш|В бою|Характеристики|Поручения коменданта|Ремесленники лагеря|Материалы|Где искать|Награда|Добыча)$"),
        ("bold", r"^([0-9]+ мед\.)  ·"),
        ("bold", r"^.+ · раунд [0-9]+$"),
        ("bold", r"^.+ · ур\. [0-9]+ · ([0-9]+ ХП)$"),
        ("italic", r"^(?:Разбег|Предсмертный рывок|Твёрдый нарост|Засада|Караульная стойка|Судорога Плети|Счёт недостачи) · (.+)$"),
        ("bold", r"^(?:Отряд: [0-9]+/[0-9]+ ХП.*|Отряд нанёс .+|Итоги раунда [0-9]+:|Действия сейчас · [0-9]+/[0-9]+ готовы)$"),
    )
    result = []
    for style, pattern in patterns:
        for match in re.finditer(pattern,text,re.MULTILINE):
            start,end = match.span(match.lastindex or 0)
            result.append(dict(type=style,offset=len(text[:start].encode("utf-16-le"))//2,
                               length=len(text[start:end].encode("utf-16-le"))//2))
    return sorted(result,key=lambda entity: entity["offset"])

def deliver(r):
    if not r.get("cb"):
        return deliver_card(r)
    notice=r["text"][:190] if r.get("notice") else ""
    try:
        if not notice:
            return deliver_card(r)
    except ApiError as exc:
        if exc.code not in (400,403): raise
        notice="Не удалось обновить карточку. Открой её командой /start в игровой теме."
        raise
    finally:
        try:
            api("answerCallbackQuery",callback_query_id=r["cb"],text=notice)
        except ApiError as exc:
            if exc.code!=400: raise

def deliver_card(r):
    if r.get("prompt"):
        args=dict(chat_id=r["chat"],text=r["text"],entities=[dict(type="text_mention",offset=0,length=6,user=dict(id=int(r["uid"]),is_bot=False,first_name="Путник"))],
                  reply_markup=dict(force_reply=True,selective=True,input_field_placeholder="Aldric"))
        if r.get("thread"):args["message_thread_id"]=r["thread"]
        return api("sendMessage",**args)["message_id"]
    edit_only=bool(r.get("cb") or r.get("edit_only"))
    args = dict(chat_id=r["chat"],text=r["text"],reply_markup={"inline_keyboard":r["rows"]})
    entities = combat_entities(r["text"])
    if entities: args["entities"] = entities
    target = r.get("target") if "slot" in r else (r["message"] if r["cb"] else None)
    if edit_only and not target: return
    art = r.get("art") or ("world" if r.get("previous_art") else None)
    if art in ANIMATED_SCENES and picture_file(art+".mp4").is_file():
        art += ".mp4"
    if target and r.get("previous_art") and (not art or not picture_file(art).is_file()):
        art=r["previous_art"]
    if art and (picture_file(art).is_file() or (target and art==r.get("previous_art"))):
        r["art"] = art
        pages = caption_pages(r["text"])
        page = min(r.get("page",0),len(pages)-1)
        buttons = list(r["rows"])
        if len(pages)>1:
            nav = []
            for label,number in (("←",page-1),("→",page+1)):
                if 0<=number<len(pages):
                    nav.append(btn(f"{label} {number+1}/{len(pages)}",f"page:{view_key(r)}:{number}"))
            index=next((i for i,row in enumerate(buttons) if any(b.get("callback_data")=="nav:start" for b in row)),len(buttons))
            buttons.insert(index,nav)
        photo_args = dict(chat_id=r["chat"],reply_markup={"inline_keyboard":buttons})
        spans = combat_entities(pages[page])
        if spans: photo_args["caption_entities"] = spans
        if target:
            try:
                if art==r.get("previous_art"):
                    api("editMessageCaption",message_id=target,caption=pages[page],**photo_args)
                else:
                    media_request("editMessageMedia",art,pages[page],message_id=target,**photo_args)
                return target
            except ApiError as exc:
                if "message is not modified" in str(exc): return target
                if edit_only: raise
                if exc.code!=400 or not any(term in str(exc).lower() for term in ("message to edit not found","can't be edited")): raise
        if r.get("thread"): photo_args["message_thread_id"]=r["thread"]
        method = "sendAnimation" if art.endswith(".mp4") else "sendPhoto"
        return media_request(method,art,pages[page],disable_notification=True,**photo_args)["message_id"]
    if target:
        try:
            api("editMessageText",message_id=target,**args)
            return target
        except ApiError as exc:
            if "message is not modified" in str(exc): return target
            if edit_only or exc.code != 400: raise
    if r["thread"]: args["message_thread_id"] = r["thread"]
    return api("sendMessage",disable_notification=True,**args)["message_id"]

def media_request(method,art,caption,**args):
    styles = {"caption_entities":args.pop("caption_entities")} if "caption_entities" in args else {}
    kind = "animation" if art.endswith(".mp4") else "photo"
    cached = FILE_IDS.get(art)
    for ref in ([cached,None] if cached else [None]):
        media = ref or "attach://picture"
        data = dict(media=dict(type=kind,media=media,caption=caption,**styles)) if method=="editMessageMedia" else {kind:media,"caption":caption,**styles}
        try:
            response = api(method,upload=None if ref else picture_file(art),**data,**args)
        except ApiError as exc:
            if ref and exc.code==400 and "file" in str(exc).lower(): continue
            raise
        if kind=="animation" and isinstance(response,dict) and response.get("animation"):
            FILE_IDS[art] = response["animation"]["file_id"]
        elif kind=="photo" and isinstance(response,dict) and response.get("photo"):
            FILE_IDS[art] = response["photo"][-1]["file_id"]
        return response

def remember_card(db,r,message):
    if r.get("prompt"):
        if message:db.execute("UPDATE alpha_prompt SET message=? WHERE uid=? AND ticket=?",(message,r["uid"],r["prompt"]))
        return
    if not message or not r.get("slot"):
        return
    slot = r["slot"]
    if r.get("art"):
        # Only paginated screens need a saved copy of their navigation.
        saved = {k:r[k] for k in ("chat","slot","thread","art","text","rows","notice") } if len(caption_pages(r["text"]))>1 else None
        db.execute("INSERT OR REPLACE INTO card_media VALUES (?,?,?,?)",(r["chat"],message,r["art"],json.dumps(saved) if saved else None))
    if r.get("finished"):
        db.execute("DELETE FROM cards WHERE chat=? AND slot=?",(r["chat"],slot))
        slot = "idle:"+str(message)
    db.execute("INSERT OR REPLACE INTO cards VALUES (?,?,?,?)",(r["chat"],slot,message,r["thread"] or 0))
    if slot.startswith("player:"):
        view={k:r[k] for k in ("chat","slot","thread","text","rows","art","page") if k in r}
        view.update(target=message,previous_art=r.get("art"),notice=False)
        db.execute("INSERT OR REPLACE INTO trade_screen VALUES(?,?)",(slot[7:],json.dumps(view)))

def sync_profile(db,identity):
    settings = {"setMyName":{"name":TITLE},
                "setMyCommands":{"commands":[dict(command=k,description=v) for k,v in COMMANDS.items()]}}
    next_check = float("inf")
    for method,args in settings.items():
        signature = json.dumps(args,sort_keys=True)
        key = str(identity["id"])+":"+method
        row = db.execute("SELECT applied,retry FROM profile_state WHERE key=?",(key,)).fetchone()
        applied,retry = row or ("",0)
        if applied==signature: continue
        if time.time()>=retry:
            try:
                api(method,**args)
                applied,retry = signature,0
            except ApiError as exc:
                if exc.code!=429: raise
                retry = time.time()+max(2,exc.delay)
                print(f"Telegram 429 · {method}: настройка отложена на {max(2,exc.delay)} с. Бот продолжает принимать команды.",flush=True)
            with db:
                db.execute("INSERT OR REPLACE INTO profile_state VALUES (?,?,?)",(key,applied,retry))
        if applied!=signature: next_check = min(next_check,retry)
    return next_check

def main():
    animations = [scene+".mp4" for scene in sorted(ANIMATED_SCENES)]
    present = [name for name in animations if picture_file(name).is_file()]
    print(f"Анимации {len(present)}/{len(animations)} · " + ", ".join(present), flush=True)
    local_db = Path(__file__).with_name("campaign.sqlite3")
    hosted_db = Path("/app/data/campaign.sqlite3")
    database = os.environ.get("CAMPAIGN_DB") or (hosted_db if hosted_db.exists() or
               (not local_db.exists() and hosted_db.parent.is_dir()) else local_db)
    db = sqlite3.connect(database)
    init_cards(db)
    alpha.init(db)
    db.executescript("CREATE TABLE IF NOT EXISTS games(chat INTEGER PRIMARY KEY,state TEXT);"
                     "CREATE TABLE IF NOT EXISTS pending(id INTEGER PRIMARY KEY,result TEXT);")
    db.execute("CREATE TABLE IF NOT EXISTS cursor_state(slot INTEGER PRIMARY KEY, value INTEGER, saved REAL)")
    cursor = db.execute("SELECT value,saved FROM cursor_state WHERE slot=1").fetchone()
    offset = cursor[0] if cursor and time.time()-cursor[1]<6*86400 else None
    db.execute("CREATE TABLE IF NOT EXISTS profile_state(key TEXT PRIMARY KEY,applied TEXT,retry REAL)")
    with db:
        db.execute("BEGIN IMMEDIATE")
        world_state=alpha.load(db)
        migrate(world_state)
        alpha.save(db,world_state)
    localchat.serve(database,TOKEN)
    print(f"Мёртвая мера · {alpha.RELEASE} · общий мир",flush=True)
    next_prune = 0
    next_profile = 0
    username = None
    while True:
        try:
            if time.monotonic()>=next_prune:
                with db:localchat.prune(db)
                next_prune=time.monotonic()+60
            if username is None:
                identity = api("getMe")
                username = identity["username"]
                print("У ворот дежурит @"+username,flush=True)
            if time.time()>=next_profile:
                next_profile = sync_profile(db,identity)
            options = {"offset":offset} if offset is not None else {}
            updates = api("getUpdates",timeout=25,allowed_updates=["message","callback_query"],**options)
            if not updates and offset is not None:
                stamp = db.execute("SELECT saved FROM cursor_state WHERE slot=1").fetchone()
                if stamp and time.time()-stamp[0]>=6*86400: offset = None
            for u in updates:
                result = process(db,u,username)
                if result:
                    screens = [result]+result.get("others",[])
                    for index in range(result.get("sent_count",0),len(screens)):
                        out = screens[index]
                        try:
                            delivered = deliver(out)
                        except ApiError as exc:
                            if exc.code not in (400,403): raise
                            print(f"Доставка в тему {out.get('thread') or 'общая'}: Telegram {exc.code} · {str(exc).replace(TOKEN,'[скрыто]')[:150]}",flush=True)
                            delivered = None
                        with db:
                            remember_card(db,out,delivered)
                            result["sent_count"] = index+1
                            db.execute("UPDATE pending SET result=? WHERE id=?",(json.dumps(result),u["update_id"]))
                offset = u["update_id"]+1
                with db:
                    db.execute("DELETE FROM pending WHERE id=?",(u["update_id"],))
                    db.execute("INSERT OR REPLACE INTO cursor_state VALUES (1,?,?)",(offset,time.time()))
        except ApiError as exc:
            if exc.code in (401,404): sys.exit("Проверь токен от BotFather.")
            if exc.code == 409: sys.exit("Конфликт получения событий. Останови второй экземпляр или отключи прежний webhook.")
            print(f"Telegram {exc.code} · {exc.method}: повтор через {max(2,exc.delay)} с.",flush=True)
            time.sleep(max(2,exc.delay))
        except (OSError,TimeoutError):
            print("Связь прервалась. Повторяем запрос.",flush=True)
            time.sleep(3)

def read_token():
    supplied = os.environ.get("BOT_TOKEN")
    if supplied:
        token = supplied.strip()
        if re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+",token):
            return token
        sys.exit("В BOT_TOKEN неверный формат. Обнови переменную или удали её для скрытого ввода.")
    while True:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error",getpass.GetPassWarning)
                token = getpass.getpass("Вставь токен один раз и нажми Enter (ввод скрыт): ").strip()
        except (EOFError,getpass.GetPassWarning):
            sys.exit("Для скрытого ввода открой PowerShell или терминал.")
        if re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+",token):
            return token
        print("Неверный формат. Скопируй только токен из BotFather и вставь его один раз.")

if __name__=="__main__":
    try:
        TOKEN = read_token()
        main()
    except KeyboardInterrupt:
        print("Фонарь погашен.")
