"""The two workshops and their patterns, in stable save order."""
from loadouts import REGIONS

TRADES = {"forge":"Кузнечное дело","sew":"Портняжное дело"}
RANKS = ("Ученик","Подмастерье","Умелец","Мастер")
# Name, slot, quality, dungeon component, required skill within a band.
PATTERNS = {
    "forge": (("Кованый обруч",2,0,False,0),("Клёпаные наручи",6,1,False,5),
              ("Кольцо с литой печатью",7,2,False,10),("Пластинчатые поножи",12,2,True,13),
              ("Оплечье с замковой пластиной",4,3,True,17)),
    "sew": (("Дорожный кушак",10,0,False,0),("Перчатки на вощёной нити",11,1,False,5),
            ("Стёганая куртка",1,2,False,10),("Плащ дозорной стежки",9,2,True,13),
            ("Сапоги с двойным рантом",13,3,True,17)),
}
def patterns():
    for band,region in enumerate(REGIONS):
        for trade,entries in PATTERNS.items():
            for name,slot,tier,deep,skill in entries:
                yield band,trade,f"{name} {region}",slot,tier,deep,(0 if band==0 and skill==5 else band*20+skill)
