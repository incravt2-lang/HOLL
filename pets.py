"""Personal encounters on returning to Guszk."""
import random
import secrets
import time

CHANCE = 0.04
DURATION = 600
BONUS = 5
PETS = {
    "boris": ("Борис", "У самого рынка вам приходится остановиться. Борис трётся щекой о ваш сапог, обходит его кругом и принимается за второй. Мурлыканье слышно даже сквозь гомон площади."),
    "kodi": ("Коди", "Из-под створки выныривает Коди с палочкой в зубах. Заметив вас, он кладёт её поперёк дороги и выжидающе смотрит снизу вверх. Хвост метёт солому у ворот."),
    "pusha": ("Пуша", "Пока вы проходите мимо лавки, кто-то тихонько цепляет лапой край вашего плаща. На подоконнике среди пучков чабреца сидит Пуша. Поймав ваш взгляд, она щурит золотистые глаза и подставляет лоб."),
    "ukrop": ("Укроп", "Укроп лежит поперёк мешка с зерном, выставив светлое брюхо на солнце. При звуке шагов он открывает один глаз, потягивается и свешивает пушистую лапу как раз вам навстречу."),
}


def arrive(hero):
    trip = hero.pop("coast_trip", {})
    eligible = hero.pop("returning_from_fight", False) or trip.get("step") == 3
    if eligible and "pet_encounter" not in hero and random.random() < CHANCE:
        hero["pet_encounter"] = [random.choice(tuple(PETS)), secrets.token_hex(6)]
    return hero.get("pet_encounter")


def stroke(hero, ticket):
    encounter = hero.get("pet_encounter")
    if not encounter or encounter[1] != ticket:
        return False
    del hero["pet_encounter"]
    hero["good_sign_until"] = time.time() + DURATION
    return True
