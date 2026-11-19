"""Equipment-for-equipment offers inside one group, settled in the game's transaction."""
import secrets
from world import ITEM_CODES, CODE_ITEMS

def button(label,data):
    return [{"text":label,"callback_data":data}]

def available(giver,receiver):
    return sorted(item for item in giver["items"] if item not in giver["gear"] and item not in receiver["items"])

def picker(items,prefix,page):
    per_page = 9
    page = max(0,min(page,(len(items)-1)//per_page))
    rows = [button(item,prefix+":pick:"+ITEM_CODES[item]) for item in items[page*per_page:(page+1)*per_page]]
    if page: rows.append(button("← Назад",prefix+":page:"+str(page-1)))
    if (page+1)*per_page<len(items): rows.append(button("Дальше →",prefix+":page:"+str(page+1)))
    return rows

def exchange(s,uid,cmd):
    heroes = s["heroes"]
    offers = s.setdefault("offers",{})
    p = cmd.split(":")
    hub = button("К обменам","barter")
    def busy(who):
        return any(f["round"] and who in f["party"] for f in s["fights"].values())
    def terms(o):
        return f"{heroes[o['from']]['name']} отдаёт {o['give']}\n{heroes[o['to']]['name']} отдаёт {o['want']}"
    def valid(o):
        a,b = heroes[o["from"]],heroes[o["to"]]
        return o["give"] in available(a,b) and o["want"] in available(b,a)
    if cmd=="barter":
        rows = []
        for key,o in offers.items():
            if uid in (o["from"],o["to"]):
                incoming = uid==o["to"]
                partner = o["from"] if incoming else o["to"]
                rows.append(button(("Входящий · " if incoming else "Исходящий · ")+heroes[partner]["name"],"barter:view:"+key))
        rows += [button("Предложить · "+h["name"],"barter:to:"+i) for i,h in heroes.items() if i!=uid]
        return "Обмен снаряжением\nВыберите партнёра или предложение. Участвуют вещи из сумки.\n"+heroes[uid].get("trade_news",""),rows or [button("Обновить","barter")]
    if len(p)>=3 and p[1] in ("view","yes","no"):
        key = p[2]
        o = offers.get(key)
        if not o or uid not in (o["from"],o["to"]): return "Это предложение уже закрыто.",[hub]
        if p[1]=="view":
            rows = [button("Принять обмен","barter:yes:"+key)] if uid==o["to"] else []
            return terms(o),rows+[button("Отклонить" if uid==o["to"] else "Отозвать","barter:no:"+key),hub]
        if p[1]=="yes":
            if uid!=o["to"]: return "Подтвердить может получатель.",[hub]
            if busy(uid) or busy(o["from"]): return "Оба героя должны закончить бой.",[hub]
            if valid(o):
                a,b = heroes[o["from"]],heroes[o["to"]]
                b["items"][o["give"]] = a["items"].pop(o["give"])
                a["items"][o["want"]] = b["items"].pop(o["want"])
                a["shop_rev"] += 1
                b["shop_rev"] += 1
                status = "Обмен завершён."
            else: status = "Обмен закрыт: состав сумок изменился."
        else: status = "Предложение отозвано." if uid==o["from"] else "Предложение отклонено."
        del offers[key]
        note = status+"\n"+terms(o)
        for who in (o["from"],o["to"]): heroes[who]["trade_news"] = note
        return note,[hub]
    if busy(uid): return "Обмен доступен после боя.",[hub]
    draft = heroes[uid].get("barter_draft",{})
    if len(p)==3 and p[1]=="to" and p[2] in heroes and p[2]!=uid:
        draft = {"to":p[2],"id":secrets.token_hex(4)}
        heroes[uid]["barter_draft"] = draft
        stage,verb,value = "give","page","0"
    elif len(p)==5 and p[1] in ("give","want") and p[2]==draft.get("id"):
        stage,verb,value = p[1],p[3],p[4]
    elif len(p)==3 and p[1]=="send" and p[2]==draft.get("id") and "want" in draft:
        o = {k:draft[k] for k in ("to","give","want")}
        o["from"] = uid
        if not valid(o): return "Состав сумок изменился. Собери предложение заново.",[hub]
        if any(v["from"]==uid and v["to"]==o["to"] for v in offers.values()):
            return "У тебя уже есть предложение этому герою. Его можно отозвать.",[hub]
        offers[draft["id"]] = o
        del heroes[uid]["barter_draft"]
        return "Предложение отправлено. Получатель найдёт его в разделе «Обмен».\n"+terms(o),[hub]
    else: return "Открой обмен заново.",[hub]
    other = heroes[draft["to"]]
    a,b = (heroes[uid],other) if stage=="give" else (other,heroes[uid])
    choices = available(a,b)
    if stage=="want" and "give" not in draft: return "Сначала выбери свою вещь.",[hub]
    if verb=="pick":
        item = CODE_ITEMS.get(value)
        if item not in choices: return "Эта вещь уже недоступна.",[hub]
        draft[stage] = item
        if stage=="want":
            return f"Проверка обмена с {other['name']}\nОтдаёшь: {draft['give']}\nПолучаешь: {item}",[
                button("Отправить предложение","barter:send:"+draft["id"]),hub]
        draft.pop("want",None)
        stage,verb,value = "want","page","0"
        choices = available(other,heroes[uid])
    if verb!="page" or not value.isascii() or not value.isdigit(): return "Открой обмен заново.",[hub]
    text = "Выбери, что отдашь." if stage=="give" else "Выбери, что хочешь получить."
    if not choices: text += " Подходящих ненадетых вещей пока нет."
    return text,picker(choices,"barter:"+stage+":"+draft["id"],int(value))+[hub]
