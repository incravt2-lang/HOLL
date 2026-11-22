"""Base experience before city and pet bonuses. One ledger per hero."""
from world import HUNT_IDS, LIMITS, level, rank

# The agreed reference awards at level 30, scaled by 1.3.
# Use thirds because field contracts can require two, three or four targets.
DENOMINATOR = 2800 * 10 * 3
DAY = 86400


def scaled(hero, target_level, shares, commit):
    lv = level(hero)
    if lv >= len(LIMITS):
        return 0
    cost = LIMITS[lv] - LIMITS[lv - 1]
    gap = 1 + max(0, lv - target_level - 4)
    units = max(DENOMINATOR, cost * 13 * shares // gap)
    total = units + hero.get("xp_fraction", DENOMINATOR // 2)
    award, remainder = divmod(total, DENOMINATOR)
    if commit:
        hero["xp_fraction"] = remainder
    return award


def contract_xp(hero, job, original, commit=False):
    if level(hero) < 10:
        return original
    if job["kind"] == "raid":
        shares = 140 * 3
    elif job["kind"] == "hunt" and job["n"] in HUNT_IDS:
        shares = 56 * job["need"]
    else:
        return original
    return scaled(hero, rank(job["z"], job["n"]), shares, commit)


def victory_xp(hero, fight, enemy_level, now):
    lv = level(hero)
    mode = fight["mode"]
    carried = mode == "raid" and lv < 10 and enemy_level >= lv + 6
    elite = fight.get("elite", False)
    if (lv < 10 and not carried) or mode == "vault":
        base = 16 + min(enemy_level, lv + 4) * 2
        factor = 162 if mode == "raid" else 12
        gap = 1 + max(0, lv - enemy_level - 4)
        xp = max(1, factor * base // (10 * gap))
        if elite:
            xp = (xp * (150 if mode == "hunt" else 120) + 50) // 100
        return xp, ""
    if mode == "hunt":
        return scaled(hero, enemy_level, (81 if elite else 54) * 3, True), ""
    dungeon = f"{fight['z']}.{fight['choice']}"
    resets = hero.setdefault("raid_xp_resets", {})
    first = resets.get(dungeon, 0) <= now
    if first:
        resets[dungeon] = now + DAY
    shares = 336 if first else 168
    label = "первая зачистка за сутки" if first else "повторная зачистка"
    xp = scaled(hero, enemy_level, shares * 3, True)
    if elite and not carried:
        xp = (xp * 120 + 50) // 100
    return xp, label
