"""Alpha 0.1 shared campaign, legacy import and character registration."""
import json
import re
import secrets
import time
from copy import deepcopy

import forks
import game
import haul
import localchat
from quests import SHIFT

RELEASE = "Alpha 0.2.4"
NAME = re.compile(r"[A-Z][a-z]{2,17}")
RULE = "Имя героя · 3–18 английских букв. Первая заглавная, остальные строчные. Например, Aldric."

def init(db):
    localchat.init(db)
    db.execute("CREATE TABLE IF NOT EXISTS alpha_world(id INTEGER PRIMARY KEY CHECK(id=1),state TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS alpha_prompt(uid TEXT PRIMARY KEY, chat INTEGER, topic INTEGER, ticket TEXT, message INTEGER)")
    db.execute("CREATE TABLE IF NOT EXISTS alpha_names(uid TEXT PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE)")

def save(db,s):
    localchat.track(s)
    db.execute("INSERT OR REPLACE INTO alpha_world VALUES(1,?)",(json.dumps(s,ensure_ascii=False),))

def load(db):
    row=db.execute("SELECT state FROM alpha_world WHERE id=1").fetchone()
    if row:return json.loads(row[0])
    states={}
    copies={}
    for chat,data in db.execute("SELECT chat,state FROM games ORDER BY chat"):
        old=json.loads(data)
        game.migrate(old)
        states[chat]=old
        for uid,h in old["heroes"].items(): copies.setdefault(uid,[]).append((chat,h))
    s={"heroes":{},"fights":{},"version":11,"choices":{}}
    winners={}
    for uid,entries in copies.items():
        best=max(h["xp"] for _,h in entries)
        top=[chat for chat,h in entries if h["xp"]==best]
        if len(top)==1:winners[uid]=top[0]
        else:s["choices"][uid]={str(chat):states[chat]["heroes"][uid] for chat in top}
    projects=[]
    for chat,old in states.items():
        for key,r in old["fights"].items():
            if all(winners.get(uid)==chat for uid in r["party"]) and key not in s["fights"]:
                r.update(chat=chat,place="исходная группа")
                s["fights"][key]=r
            else:
                haul.bank(old,r)
                forks.pay(old,r)
                if r["mode"]=="vault" and r["round"]:
                    h=old["heroes"][r["party"][0]]
                    zone=str(r["z"])
                    h["keys"][zone]=h["keys"].get(zone,0)+1
        for uid,h in old["heroes"].items():
            h.pop("trade_draft",None)
            board=old.get("contracts",{})
            if any(q.get("owner")==uid for q in board.get("jobs",[])):
                # Honour already signed pages until the old shift expires.
                personal=deepcopy(board)
                for q in personal["jobs"]:
                    if q["owner"]!=uid:q.update(owner=None,done=False,progress=0)
                h["orders_board"]=personal
            if winners.get(uid)==chat:s["heroes"][uid]=h
        for key,o in old.get("offers",{}).items():
            if all(winners.get(o[k])==chat for k in ("from","to")):
                s.setdefault("offers",{})[key]=o
        for key,lot in old.get("writ_lots",{}).items():
            members=[i for i in lot["members"] if winners.get(i)==chat]
            if members:
                lot.update(members=members,votes={i:v for i,v in lot["votes"].items() if i in members})
                s.setdefault("writ_lots",{})[key]=lot
        q=old.get("city_project")
        if q:projects.append((chat,q))
    if projects:
        chat,q=max(projects,key=lambda p:(p[1]["until"]>time.time(),p[1]["seq"],p[1]["until"],sum(p[1]["counts"])))
        s["city_project"]=q
        for field in ("cargo","oil"):
            q[field]={i:v for i,v in q.get(field,{}).items() if winners.get(i)==chat}
        for r in s["fights"].values():
            if r["chat"]!=chat:r.pop("city_finds",None)
    save(db,s)
    return s

def prompt(db,uid,chat,topic,cb,reason=""):
    ticket=secrets.token_hex(6)
    db.execute("INSERT OR REPLACE INTO alpha_prompt VALUES(?,?,?,?,NULL)",(uid,chat,topic or 0,ticket))
    return dict(prompt=ticket,uid=uid,chat=chat,thread=topic,cb=cb,notice=False,rows=[],
                text="Путник, назови себя.\n\n"+(reason+"\n\n" if reason else "")+RULE+"\nОтветь на это сообщение.")

def is_reply(db,uid,chat,topic,message):
    return db.execute("SELECT 1 FROM alpha_prompt WHERE uid=? AND chat=? AND topic=? AND message=?",
                      (uid,chat,topic or 0,message)).fetchone() is not None
