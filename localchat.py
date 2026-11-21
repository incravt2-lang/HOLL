"""Telegram Mini App for the hero's current room."""
import hashlib
import hmac
import json
import os
import re
import sqlite3
import threading
import time
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from world import encounter_area, area_name, ZONES, VAULTS

def init(db):
    db.execute("CREATE TABLE IF NOT EXISTS chat_seen(uid TEXT PRIMARY KEY, stamp REAL)")
    db.execute("""CREATE TABLE IF NOT EXISTS location_messages(
        id INTEGER PRIMARY KEY, room TEXT NOT NULL, uid TEXT NOT NULL,
        nick TEXT NOT NULL, body TEXT NOT NULL, created REAL NOT NULL, nonce TEXT NOT NULL,
        UNIQUE(uid,nonce))""")
    db.execute("CREATE INDEX IF NOT EXISTS messages_by_room ON location_messages(room,id)")

def track(state):
    """Commit room transitions in the same transaction as the game action."""
    active={uid:r for r in state.get("fights",{}).values() for uid in r["party"]}
    now=time.time()
    for uid,h in state["heroes"].items():
        r=active.get(uid)
        trip=h.get("coast_trip")
        if r and r["mode"]=="hunt" and "road_level" not in r:
            h["hunting_ground"]=encounter_area(r["z"],r["choice"])
        if r and r["mode"] in ("raid","vault"):
            vault=r["mode"]=="vault"
            h["hunting_ground"]=area_name(r["z"],1 if vault else r["choice"])
            room=("vault/" if vault else "party/")+r["id"]
            place=VAULTS[r["z"]][0] if vault else ZONES[r["z"]][2][r["choice"]][0]
            label=place+(" · сбор" if not r["round"] else f" · зал {r.get('room',0)+1}/3")
        elif trip:
            step=trip["step"]
            if step==3 and not trip.get("waiting") and not r:room,label="camp","Лагерь «У моря»"
            else:
                room=f"road/{step}"
                label=("За городскими воротами","Верстовой столб","Рыбная дорога","Костры над отмелью")[step]
        elif h.get("hunting_ground"):
            label=h["hunting_ground"];room="hunt/"+label
        else:room,label="town","Торговая площадь Гусзка"
        if h.get("talk_room")!=room:
            h.update(talk_room=room,talk_since=now)
        h["talk_label"]=label
    fighting={i for i,r in active.items() if r["round"]}
    for key,o in list(state.get("offers",{}).items()):
        if fighting.intersection((o["from"],o["to"])) or not together(state,o["from"],o["to"],o.get("room")):
            del state["offers"][key]
        else:o["room"]=state["heroes"][o["from"]]["talk_room"]
    for uid,h in state["heroes"].items():
        d=h.get("trade_draft")
        if d and not together(state,uid,d["to"],d.get("room")):h.pop("trade_draft")

def together(state,uid,other,expected=None):
    h=state["heroes"].get(uid,{})
    room=h.get("talk_room")
    return bool(room and uid!=other and room==state["heroes"].get(other,{}).get("talk_room") and expected in (None,room))


class ChatError(Exception):
    def __init__(self,status,msg):
        super().__init__(msg);self.status=status

def identity(raw,token):
    try:
        pairs=parse_qsl(raw,keep_blank_values=True,strict_parsing=True,max_num_fields=32)
        data=dict(pairs)
        if len(data)!=len(pairs):raise ValueError()
        received=data.pop("hash")
        fields="\n".join(f"{k}={data[k]}" for k in sorted(data)).encode()
        key=hmac.digest(b"WebAppData",token.encode(),"sha256")
        expected=hmac.new(key,fields,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected,received):raise ValueError()
        age=time.time()-int(data["auth_date"])
        if not -60<=age<=86400:raise ValueError()
        uid=json.loads(data["user"])["id"]
        if type(uid) is not int or uid<=0:raise ValueError()
        return str(uid)
    except (ValueError,TypeError,KeyError):
        raise ChatError(401,"Закрой окно и открой чат из игровой карточки.")

def exchange(db,uid,req,write):
    now=time.time()
    touched=db.execute("SELECT stamp FROM chat_seen WHERE uid=?",(uid,)).fetchone()
    if not touched or now-touched[0]>=60:
        db.execute("INSERT OR REPLACE INTO chat_seen SELECT uid,? FROM alpha_names WHERE uid=?",(now,uid))
        db.commit()
    db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
    row=db.execute("SELECT state FROM alpha_world WHERE id=1").fetchone()
    h=json.loads(row[0])["heroes"].get(uid) if row else None
    name=db.execute("SELECT name FROM alpha_names WHERE uid=?",(uid,)).fetchone()
    if not h or not name:raise ChatError(403,"Выбери героя и запиши его имя у писаря.")
    room=h.get("talk_room","")
    label=h.get("talk_label","В пути")
    since=h.get("talk_since",0)
    visit=f"{room}|{since}"
    if write:
        if not room or req.get("visit")!=visit:raise ChatError(409,"Герой сменил место. Открой текущий разговор.")
        body=req.get("body");nonce=req.get("nonce")
        if not isinstance(body,str) or not 0<len(body.strip())<=500 or not isinstance(nonce,str) or not re.fullmatch('[a-zA-Z0-9-]{12,64}',nonce):
            raise ChatError(400,"В сообщении должно быть от 1 до 500 знаков.")
        now=time.time()
        sent=db.execute("SELECT room,body FROM location_messages WHERE uid=? AND nonce=?",(uid,nonce)).fetchone()
        if sent and sent!=(room,body.strip()):raise ChatError(409,"Обнови разговор.")
        if not sent:
            last=db.execute("SELECT created FROM location_messages WHERE uid=? ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
            if last and now-last[0]<2:raise ChatError(429,"Подожди пару секунд перед следующей репликой.")
            db.execute("INSERT INTO location_messages(room,uid,nick,body,created,nonce) VALUES(?,?,?,?,?,?)",
                       (room,uid,name[0],body.strip(),now,nonce))
    rows=db.execute("""SELECT id,nick,body,created,uid=? FROM location_messages
        WHERE room=? AND created>=? ORDER BY id DESC LIMIT 50""",(uid,room,since)).fetchall() if room else []
    return dict(title=label,visit=visit,enabled=bool(room),messages=list(reversed(rows)))

def serve(database,token):
    directory=Path(__file__).parent
    assets={p:(directory/f).read_bytes() for p,f in [("/","chat.html"),("/chat.js","chat.js"),("/chat.css","chat.css")]}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,code,body,kind):
            self.send_response(code);self.send_header("Content-Type",kind)
            self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
        def do_GET(self):
            path=urlsplit(self.path).path
            if path not in assets:self.send_error(404);return
            self.send(200,assets[path],{"/":"text/html","/chat.js":"application/javascript","/chat.css":"text/css"}[path]+"; charset=utf-8")
        def do_POST(self):
            try:
                if self.path not in ("/history","/send"):raise ChatError(404,"Страница не найдена.")
                size=int(self.headers.get("Content-Length","0"))
                if not 0<size<=16384:raise ChatError(400,"Некорректный запрос.")
                if self.headers.get_content_type()!="application/json":raise ChatError(415,"Нужен JSON.")
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict):raise ValueError()
                raw=data.get("auth","")
                if not isinstance(raw,str):raise ValueError()
                uid=identity(raw,token)
                with closing(sqlite3.connect(database,timeout=5)) as db,db:
                    result=exchange(db,uid,data,self.path=="/send")
                code=200
            except ChatError as exc:code,result=exc.status,{"error":str(exc)}
            except (ValueError,TypeError):code,result=400,{"error":"Некорректный запрос."}
            except sqlite3.OperationalError:code,result=503,{"error":"Городская книга занята. Попробуй ещё раз."}
            self.send(code,json.dumps(result,ensure_ascii=False).encode(),"application/json; charset=utf-8")
    server=ThreadingHTTPServer(("0.0.0.0",int(os.environ.get("PORT","3000"))),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server
