"""Personal dungeon rewards and the original party's claim on duplicate drops."""
from world import category, RARITY, gear_names, gear_stat, loot_slots, strength, trade_value

def row(text,cmd):
    return [{"text":text,"callback_data":cmd}]

def spoils(state,uid,args):
    h=state["heroes"][uid]
    spares=h.get("spare_drops",{})
    buckles=h.get("buckles",0)
    offers=[k for k in loot_slots(6,5,h["class"]) if RARITY[6,k]==1][:4]
    trip=h.get("coast_trip",{})
    at_camp=trip.get("step")==3 and not trip.get("waiting") and not any(uid in r["party"] for r in state["fights"].values())
    note=""
    if len(args)==3 and args[0]=="order" and args[1]==str(buckles) and at_camp and buckles>=5:
        k=next((k for k in offers if str(k)==args[2]),None)
        if k is not None and gear_names(6)[k] not in h["items"]:
            item=gear_names(6)[k]
            h["items"][item]=[gear_stat(6,k),strength(6,k)]
            h["buckles"]=buckles=buckles-5
            note=f"Мастер выдал [{category(6,k)}] "+item+"."
    if len(args)==2 and args[0] in spares:
        z,k,party=spares[args[0]]
        item=gear_names(z)[k]
        who=args[1]
        if who=="sell":
            coins=4*trade_value(z,k)
            h["wallet"]+=coins
            note=f"Продано · {coins} мед."
        elif who in party and who in state["heroes"] and item not in state["heroes"][who]["items"]:
            state["heroes"][who]["items"][item]=[gear_stat(z,k),strength(z,k)]
            note="Передано · "+state["heroes"][who]["name"]+" · "+item
        if note: del spares[args[0]]
    lines=["Трофеи походов",f"Пряжки Кожевен · {buckles}. Мастера в лагере у моря принимают пять пряжек за вещь."]
    if note: lines.append(note)
    rows=[]
    for k in offers:
        item=gear_names(6)[k]
        if item not in h["items"]:
            lines.append(item)
            if at_camp and buckles>=5: rows.append(row(item+" · 5 пряжек",f"spoils:order:{buckles}:{k}"))
    if spares:
        ticket=next(iter(spares))
        z,k,party=spares[ticket]
        lines.append(f"Повторы в сумке · {len(spares)}\n"+gear_names(z)[k])
        for who in party:
            if who in state["heroes"] and gear_names(z)[k] not in state["heroes"][who]["items"]:
                rows.append(row("Отдать · "+state["heroes"][who]["name"],f"spoils:{ticket}:{who}"))
        rows.append(row(f"Продать · {4*trade_value(z,k)} мед.",f"spoils:{ticket}:sell"))
    rows.append(row("К сумке","nav:bag"))
    return "\n\n".join(lines),rows
