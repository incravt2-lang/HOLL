"""Two named class outfits per level band; each provides two distinct rings."""
REGIONS = ("Гусзка","Ровни","Мельвы","Стырни","Вереска","Тарны")
SLOT_NAMES = ("Подвеска","Куртка","Шапель","Серьги","Наплечники","Рубаха","Наручи",
              "Кольцо","Перстень","Плащ","Пояс","Перчатки","Поножи","Сапоги")
# Outfit name, alternative outfit, their weapons and the class off-hand.
PATTERNS = {
    "guard": ("караульного","десятника","Меч","Топор","Щит","guard"),
    "nun": ("перевязчицы","настоятельницы","Булава","Жезл","Фолиант","medicine"),
    "archer": ("следопыта","ловчего","Тесак","Кинжал","Баклер","crit"),
    "smith": ("подмастерья","мастера","Молот","Топор","Щит","severity"),
    "witch": ("травницы","отравительницы","Серп","Кинжал","Фолиант","reserve"),
}
SPECIAL = {"guard":("Палаш","Булава","Меч"),"nun":("Посох","Булава","Жезл"),
           "archer":("Лук","Тесак","Арбалет"),"smith":("Клевец","Молот","Топор"),
           "witch":("Жезл","Серп","Кинжал")}

def pieces(band):
    for cls,(first,second,weapon,alternative,offhand,bonus) in PATTERNS.items():
        for tier,(title,main) in enumerate(((first,weapon),(second,alternative))):
            for logical,part in enumerate((*SLOT_NAMES,offhand,main)):
                slot=7 if logical==8 else logical
                name=f"{part} {title} {REGIONS[band]}"
                yield name,slot,cls,tier,part,bonus
        for tier,part in enumerate(SPECIAL[cls],2):
            mark=("с медной насечкой","с клеймом гильдии","со старой печатью")[tier-2]
            yield f"{part} {second} {REGIONS[band]} {mark}",15,cls,tier,part,bonus
