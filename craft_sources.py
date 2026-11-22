"""Named boss parts and hunting sources for the two professions."""
from world import BANDS, HUNT_IDS, RECIPES, VAULTS, ZONES, encounter_area, is_humanoid, monster

PART_NAMES = (
    ("Жерновая втулка", "Судейское коромысло"),
    ("Застёжка двойной присяги", "Руно Сотой овцы"),
    ("Костяное веретено белильни", "Свинцовая печать адресата"),
    ("Скоба перевальной упряжи", "Пряжка ночлежного полога"),
    ("Клеймо откупщика", "Каменная проушина свидетеля"),
    ("Латунный крюк поручителя", "Перламутровый гребень прилива"),
    ("Игла семи швов", "Кромка старого сукна", "Вощёная жила хозяйки"),
    ("Обруч солеварного котла", "Соляная печатка управляющего", "Кристалл каменного сердца"),
    ("Наконечник ходячего отвеса", "Пломба душеприказчика", "Медный зубец поверенного"),
)
BOSS_CHANCE = 0.10
RARE_CHANCE = 0.06
FIELD_CHANCE = 0.55


def boss_key(z,n):
    return f"boss/{z}.{n}"


def boss_id(key):
    return tuple(map(int,key.split("/")[1].split(".")))


def part_name(key):
    z,n=boss_id(key)
    return PART_NAMES[z][(n-5)//3]


def chance(n):
    return BOSS_CHANCE if n==5 else RARE_CHANCE


def build_bills():
    bills={}
    for band in range(6):
        sources=[boss_key(z,n) for z,b in enumerate(BANDS) if b==band
                 for n in ((5,8,11) if z in VAULTS else (5,8))]
        enhanced=sorted((pair for pair,(_,deep,_) in RECIPES.items()
                         if deep and BANDS[pair[0]]==band),key=lambda pair:(RECIPES[pair][2],pair))
        for i,pair in enumerate(enhanced):
            first=sources[i%len(sources)]
            if RECIPES[pair][2]%20==17:
                bills[pair]=(first,sources[(i+1)%len(sources)])
            else:
                bills[pair]=(first,)
    return bills


BILLS=build_bills()


def route(key):
    if key.startswith("boss/"):
        z,n=boss_id(key)
        place=VAULTS[z][0] if n==11 else ZONES[z][2][(n-5)//3][0]
        mode="Одиночный тайник" if n==11 else "Групповое подземелье"
        return f"{mode} · {encounter_area(z,n)} → {place} → {monster(z,n)}, зал 3 · {chance(n):.0%}"
    kind,code=key.split("/")
    trade,band=code.split(".")
    if kind=="shop":
        return "Торговец · Лагерь у Моря → "+("Харитон" if trade=="forge" else "Вея")+" · 8 мед."
    if kind=="part":
        return "Готовая заготовка из запасов. Заменяется двумя единицами сырья."
    places={}
    for z,b in enumerate(BANDS):
        if b!=int(band):continue
        for n in HUNT_IDS:
            if is_humanoid(z,n)==(trade=="forge"):
                places.setdefault(encounter_area(z,n),[]).append(monster(z,n))
    return "Охота · "+f"{FIELD_CHANCE:.0%}"+ "\n"+"\n".join(place+" → "+", ".join(names) for place,names in places.items())
