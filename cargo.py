"""Quantity reserved for active contracts and accepted craft commissions."""
import time
from collections import Counter
from quests import SHIFT

def needs(s,uid):
    counts=Counter()
    board=s["heroes"][uid].get("orders_board",{})
    if board:
        for job in board["jobs"]:
            if job["owner"]==uid and not job["done"] and job["kind"]=="supply":
                counts[f"{job['z']}.{job['n']}"]+=job["need"]
    for order in s["heroes"][uid].get("commissions",{}).values():
        counts.update(order["materials"])
    return counts

def free(h,key,needed):
    return max(0,h["junk"].get(key,0)-needed.get(key,0))
