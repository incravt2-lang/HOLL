"""Personal loot rolls held by a dungeon until the party returns."""
from copy import deepcopy
from world import ITEM_CODES, trade_value

def carry(hero, bag):
    for key, qty in bag.get("junk", {}).items():
        hero["junk"][key] = hero["junk"].get(key, 0) + qty
    for item, stats in bag.get("items", {}).items():
        if item in hero["items"]:
            z,k = map(int, ITEM_CODES[item].split("."))
            hero["wallet"] += 4*trade_value(z,k)
        else:
            hero["items"][item] = stats
    hero["wallet"] += bag.get("wallet", 0)
    hero.setdefault("spare_drops", {}).update(bag.get("spare_drops", {}))
    notes = hero.setdefault("found_notes", [])
    notes.extend(key for key in bag.get("found_notes", []) if key not in notes)
    coins, hero["sale_tenths"] = divmod(hero.get("sale_tenths",0)+bag.get("tenths",0),10)
    hero["wallet"] += coins

def preview(hero,bag):
    virtual=deepcopy(hero)
    carry(virtual,bag)
    return virtual

def store(bag,before,after):
    for field in ("items","spare_drops"):
        bag.setdefault(field,{}).update({k:v for k,v in after.get(field,{}).items() if k not in before.get(field,{})})
    for k,v in after["junk"].items():
        delta=v-before["junk"].get(k,0)
        if delta:
            counts=bag.setdefault("junk",{})
            counts[k]=counts.get(k,0)+delta
    bag.setdefault("found_notes",[]).extend(k for k in after.get("found_notes",[]) if k not in before.get("found_notes",[]))
    bag["wallet"]=bag.get("wallet",0)+after["wallet"]-before["wallet"]
    bag["tenths"]=bag.get("tenths",0)+after.get("sale_tenths",0)-before.get("sale_tenths",0)

def bank(state,fight):
    for uid,bag in fight.pop("haul",{}).items():
        carry(state["heroes"][uid],bag)
    project=state.get("city_project",{})
    for seq,uid,i in fight.pop("city_finds",[]):
        if project.get("seq")==seq and not project["until"]:
            cargo=project["cargo"].setdefault(uid,[0,0,0])
            cargo[i]+=1
