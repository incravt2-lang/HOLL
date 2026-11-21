"""Telegram transport. Run one polling process per token."""
import hashlib
import pets
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
from game import TITLE, btn, play, board, level, migrate, title, target

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
    [("Дневник","diary"),("Сумка","bag"),("Гусзк","town")],
    [("Охота","hunt"),("Подземелья","dungeons"),("Отряды","teams")],
    [("Карта","zones"),("Обмен","barter"),("Кодекс","codex")],
]
ACTIONS = {"pits","loft","closevote","join","go","leave","hit","block","skill","finish","heal","healok","ward","fury"} | set(POTIONS)

def init_cards(db):
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
    return ("Выбери отряд, чтобы вступить." if rows else "Открытых сборов пока нет."),rows

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
        msg = f"{TITLE} · уровень {level(hero)}" if hero else f"{TITLE} · выбери класс в разделе «Дневник»"
        rows = [[btn(label,"nav:"+dest) for label,dest in row] for row in MENU]
        incoming = sum(o["to"]==uid for o in state.get("offers",{}).values())
        if hero and hero.get("coast_trip") and not mine: rows.insert(0,[btn("Дорога к морю","road")])
        if incoming: msg += f"\nПредложений обмена: {incoming}"
        if hero and hero.get("last_result"): rows.append([btn("Итоги последнего боя","nav:report")])
        if mine: rows.insert(0,[btn("Вернуться в поход","nav:current")])
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
    if viewing: watches[uid] = mine["id"]
    else: watches.pop(uid,None)
    menu = [btn("☰ Меню","nav:start")]
    if cmd in ("lore","book","help"):
        menu.insert(0,btn("‹ Кодекс","nav:codex"))
    elif cmd in ("raid","vault") and not mine:
        menu.insert(0,btn("‹ Подземелья","nav:dungeons"))
    if cmd!="start" and not event_art: rows = rows+[menu]
    result = screen(db,chat,uid,name,topic,msg,rows,open_here=not cb)
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
                                       old_votes!=current.get("votes",{}) or previous_route!=current.get("route") or before!=current.get("party") or previous_move!=current.get("moves",{}).get(uid)
                                       or previous_drink!=current.get("drank",{}).get(uid))
    if changed:
        others = []
        for who in before:
            if who==uid or watches.get(who)!=battle_id: continue
            if ended:
                other_text,other_rows = msg,[]
                watches.pop(who,None)
            else:
                other_text,other_rows = board(state,fights[battle_id],who)
            others.append(screen(db,chat,who,heroes[who]["name"],topic,other_text,other_rows+[menu]))
        for out in others:
            out["art"] = fight_picture(current or previous)
        result["others"] = others
    return result

def fight_picture(fight):
    if "votes" in fight: return "tannery_fork"
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
    if op=="road": return "coast_road"
    if op=="notes": return "lore"
    if op=="codex": return "book"
    if op=="dungeons": return "raid"
    if op == "bio" and args:
        return "hero_" + args[0]
    if op in ("hero", "diary", "class", "skills", "train") or (not hero and op not in ("start","help","lore")):
        return "hero_" + hero["class"] if hero else "teams"
    if op == "report":
        return hero.get("report_art","teams") if hero else "teams"
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
        for prefix, scene in (("sellpage","sell"),("gear-","sell"),("cash","sell"),
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

def process(db, update, username):
    """Commit the game and the pending response together before sending."""
    key = update["update_id"]
    with db:
        existing = db.execute("SELECT result FROM pending WHERE id=?", (key,)).fetchone()
        if existing: return json.loads(existing[0])
        cb = update.get("callback_query", {})
        m = cb.get("message") or update.get("message", {})
        chat = m.get("chat", {})
        actor = cb.get("from") or m.get("from", {})
        if not chat: return
        if not cb and m.get("sender_chat") and chat.get("type") in ("group","supergroup"):
            command = (m.get("text") or "").strip().lower()
            if command in ("/start","/start@"+username.lower()):
                return dict(chat=chat["id"],message=m["message_id"],cb=None,notice=False,rows=[],
                            text="Чтобы открыть личную карточку, отправь команду от своего аккаунта. Сейчас отправителем указан чат.",
                            thread=m.get("message_thread_id") if m.get("is_topic_message") else None)
            return
        if not actor or actor.get("is_bot"): return
        if cb:
            cmd = cb.get("data", "")
        else:
            word = (m.get("text") or " ").split()
            if not word or not word[0].startswith("/"): return
            cmd, _, mention = word[0][1:].partition("@")
            if cmd not in COMMANDS or (mention and mention.lower()!=username.lower()): return
        if cb and cmd.startswith("nav:"):
            cmd = cmd[4:]
        if chat["type"]=="private":
            result = dict(chat=chat["id"],message=m["message_id"],cb=cb.get("id"),notice=False,
                          text="Открой группу и отправь /start@"+username+".",rows=[],thread=None)
        elif chat["type"] in ("group","supergroup"):
            uid = str(actor["id"])
            if cb:
                owner = db.execute("SELECT slot FROM cards WHERE chat=? AND message=?",
                                   (chat["id"],m["message_id"])).fetchone()
                if not owner or owner[0]!="player:"+uid:
                    return dict(chat=chat["id"],cb=cb["id"],notice=True,
                                text="Открой свою карточку. Если её ещё нет, отправь /start@"+username+".")
            if cb and cmd.startswith("page:"):
                rec = db.execute("SELECT view FROM card_media WHERE chat=? AND message=?",(chat["id"],m["message_id"])).fetchone()
                parts = cmd.split(":")
                view = json.loads(rec[0]) if rec and rec[0] else None
                if view and len(parts)==3 and parts[1]==view_key(view) and parts[2] in map(str,range(len(caption_pages(view["text"])))):
                    view.update(cb=cb["id"],page=int(parts[2]),target=m["message_id"],previous_art=view["art"])
                    return view
                return dict(chat=chat["id"],cb=cb["id"],notice=True,text="Карточка уже обновилась.")
            stored = db.execute("SELECT state FROM games WHERE chat=?", (chat["id"],)).fetchone()
            state = json.loads(stored[0]) if stored else {}
            name = " ".join(actor.get("first_name","Странник").split())[:32] or "Странник"
            topic = m.get("message_thread_id") if m.get("is_topic_message") else None
            if cmd=="start" and not cb:
                print(f"Получена команда входа · тема {topic or 'общая'}.",flush=True)
            result = player_action(db,state,chat["id"],uid,name,topic,cmd,cb.get("id"))
            if cb and not result.get("notice"):
                result["target"]=m["message_id"]
                for other in result.get("others",[]):
                    other["edit_only"]=True
            db.execute("INSERT OR REPLACE INTO games VALUES (?,?)",(chat["id"],json.dumps(state)))
        else:
            return
        db.execute("INSERT INTO pending VALUES (?,?)", (key,json.dumps(result)))
        return result

def combat_entities(text):
    patterns = (
        ("bold",r"\[(Оружие|Броня|Аксессуары|Задания и ремёсла|Задания|Записки|Монеты|Трофеи|Хлам)\]"),
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
            buttons.append(nav)
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
    db.executescript("CREATE TABLE IF NOT EXISTS games(chat INTEGER PRIMARY KEY,state TEXT);"
                     "CREATE TABLE IF NOT EXISTS pending(id INTEGER PRIMARY KEY,result TEXT);")
    db.execute("CREATE TABLE IF NOT EXISTS cursor_state(slot INTEGER PRIMARY KEY, value INTEGER, saved REAL)")
    cursor = db.execute("SELECT value,saved FROM cursor_state WHERE slot=1").fetchone()
    offset = cursor[0] if cursor and time.time()-cursor[1]<6*86400 else None
    db.execute("CREATE TABLE IF NOT EXISTS profile_state(key TEXT PRIMARY KEY,applied TEXT,retry REAL)")
    next_profile = 0
    username = None
    while True:
        try:
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
