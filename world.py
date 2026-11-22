"""Ordered zone, encounter and loot catalog. IDs are stable save keys."""
ZONES = [('Гусзкские выселки',
  ('Мельничная дворняга', 'Мучной слепень', 'Гуменный ревун'),
  (('Мельница пустого жернова', 'Мельничный соглядатай', 'Ссыпная тварь', 'Дед Жернов'),
   ('Подвалы съестного суда', 'Солонинный червь', 'Дознаватель с жабрами', 'Судья семи гирь')),
  ('Подвеска с мельничным зубцом',
   'Куртка из мешковины',
   'Медальон мучного старосты',
   'Жилет жернового сторожа',
   'Кольцо с клеймом суда',
   'Кольчуга судебного пристава')),
 ('Бережки Ровни',
  ('Межевой кабан', 'Лозовый полоз', 'Меченый тур'),
  (('Застава двух пошлин', 'Пеший мытарь', 'Обходчик межи', 'Дважды присягнувший'),
   ('Двор овечьего счёта', 'Косматый пастух', 'Стригаль с пустым лицом', 'Сотая овца')),
  ('Межевая бирка Ровни',
   'Нагрудник загонщика туров',
   'Половинка таможенной пломбы',
   'Латы заставного сборщика',
   'Пастуший узелок',
   'Стёганка овечьего двора')),
 ('Луга Мельвы',
  ('Пегая галка', 'Одичалый поводырь', 'Четверорукий косец'),
  (('Белильни Мельвы', 'Щёлочной бродяга', 'Полотняная вдова', 'Хозяин белых рук'),
   ('Дом невручённых писем', 'Голодный гонец', 'Читатель чужих голосов', 'Адресат без имени')),
  ('Галочий оберег',
   'Плащ мельвского гонца',
   'Подвеска с белильным крючком',
   'Нагрудник щёлочника',
   'Печатка невручённых писем',
   'Фартук почтового литейщика')),
 ('Перевалы Стырни',
  ('Снежная куница', 'Перемётный волк', 'Зверь под попоной'),
  (('Перегонный острог', 'Караульный на четвереньках', 'Беглый вьючник', 'Смотритель упряжи'),
   ('Семь зимовий', 'Зимовочный медведь', 'Погонщик без тени', 'Госпожа последнего ночлега')),
  ('Зубец санного полоза',
   'Бригантина перевальщика',
   'Шейная бирка каторжника',
   'Панцирь конвойного',
   'Узел хозяйки зимовья',
   'Мантия семи ночлегов')),
 ('Уступы Вереска',
  ('Рудный хрущ', 'Медноголовый коршун', 'Карьерный жвач'),
  (('Монетный обрез', 'Пробирщик с ожогом', 'Тигельный плясун', 'Откупщик меди'),
   ('Лестница несчастных случаев', 'Штольневой проводник', 'Сбитый десятник', 'Свидетель под камнем')),
  ('Медная птица Вереска',
   'Кираса уступного обходчика',
   'Подвеска пробирщика',
   'Латы монетной стражи',
   'Образок горного свидетеля',
   'Риза лестничного брата')),
 ('Отмели Тарны',
  ('Пляжная лисица', 'Донный скребун', 'Береговой ходок'),
  (('Торги первого улова', 'Посольщик из чана', 'Весовщик первой партии', 'Поручитель свежести'),
   ('Дом нижней воды', 'Служка сухого причала', 'Подражатель прибоя', 'Мать прилива')),
  ('Гладкий камень Тарны',
   'Доспех берегового обходчика',
   'Бирка первой продажи',
   'Плащ поручителя улова',
   'Кольцо нижней воды',
   'Покров отливной матери')),
 ('Огородные рвы Гусзка',
  ('Тенётник гусзкских рвов', 'Рябая землеройка', 'Капустный грызень'),
  (('Кожевни за плетнём', 'Сторож известковой ямы', 'Сшитый подёнщик', 'Мастер семи швов'),
   ('Суконный двор без крыши', 'Бельевой прядильщик', 'Нитяной носильщик', 'Суконная тётка')),
  ('Глазок из огородного янтаря',
   'Кафтан ночного поливальщика',
   'Кольцо семи швов',
   'Бригантина кожевенного двора',
   'Образок штопальщицы',
   'Пелерина суконной тётки')),
 ('Соляницы Лужи',
  ('Рапная жерлянка', 'Ивовый уж', 'Человек в камышах'),
  (('Двор белой чаши', 'Черпальщик рапы', 'Солевой ходулочник', 'Выборный кипятильщик'),
   ('Колодцы вдовьей доли', 'Соляная слепушонка', 'Шахтный шептун', 'Слепок управляющего')),
  ('Шейная мерка соли',
   'Плащ из лужских камышей',
   'Медальон белой чаши',
   'Нагрудник раповара',
   'Лупа колодезного мастера',
   'Кольчуга вдовьей смены')),
 ('Изломы Чекани',
  ('Известковая оса', 'Слюдяная агама', 'Кремнезубый шакал'),
  (('Мастерские мерных стёкол', 'Слюдяной усач', 'Ловец бликов', 'Ходячий отвес'),
   ('Палаты второй записи', 'Костяной посыльный', 'Некромант-переписчик', 'Последний душеприказчик')),
  ('Чеканский кремнёвый клин',
   'Панцирь мерного обходчика',
   'Подвеска поверенного',
   'Латы хранителя отвеса',
   'Шейная бирка покойного',
   'Мантия душеприказчика'))]
TRAITS = (('Разбег', 'Каждый третий раунд наносит усиленный удар.'),
 ('Твёрдый нарост', 'Каждый чётный раунд поглощает часть урона.'),
 ('Предсмертный рывок', 'Ниже половины ХП наносит дополнительный урон.'))
# Append-only encounter IDs preserve kill records, inventory and active contracts.
NEW_HUNTS = (
    (("Крыса мучного ларя","Крысиный резец"),("Амбарная сипуха","Серое маховое перо")),
    (("Камышовая рысь","Камышовый рысьий коготь"),("Баран межевого брода","Обломок витого рога")),
    (("Стоговый хорёк","Полоска хорьковой шкуры"),("Белильная ворона","Выбеленное воронье перо")),
    (("Козерог снежной седловины","Скол ребристого рога"),("Пёс брошенной упряжи","Пряжка старой упряжи")),
    (("Меднопёрый барсук","Медно-рыжая щетина"),("Слепой штольневый кожан","Перепонка кожана")),
    (("Иловая цапля","Иловый клюв"),("Кабан ракушечных отмелей","Ракушечная пластина")),
    (("Крот капустных гряд","Кротовая лапка"),("Хорь плетневых лазов","Клык плетневого хоря")),
    (("Жаба соляной корки","Соляная бородавка"),("Аист рапных болот","Розовое перо аиста")),
    (("Заяц мелового карьера","Меловая заячья шкурка"),("Кремнерогий олень","Осколок чёрного рога")),
)
HUMAN_HUNTS = (
    (("Грабитель хлебных подвод","Срезанный обозный шнур","robber"),("Мельник с мучной коркой","Жетон заражённой мельницы","changed")),
    (("Разбойник камышового брода","Краденый перевозный грош","robber"),("Клятвопреступник двух застав","Перечёркнутая пряжка стражи","oath")),
    (("Сборщица пустой милостыни","Донце дырявой меры","cult"),("Белильщик с вытянутыми руками","Известковый напёрсток","changed")),
    (("Налётчик санного тракта","Нож для санных ремней","robber"),("Беглый десятник перевала","Десятничья цепочка","oath")),
    (("Пробирщик Пустой Меры","Медная чаша без дна","cult"),("Сросшийся каменотёс","Вросший осколок клина","changed")),
    (("Налётчик сухого причала","Метка краденого багра","robber"),("Жаберный зазывала","Вздутый торговый свисток","changed")),
    (("Вор огородной десятины","Надрезанная бирка десятины","robber"),("Клятвопреступник амбарных ворот","Спиленный караульный знак","oath")),
    (("Проповедница соляной чаши","Соляная бусина проповедницы","cult"),("Заросший солью колодезник","Соляной слепок ладони","changed")),
    (("Книгочей Пустой Меры","Лист недостачной книги","cult"),("Клятвопреступник Чеканного двора","Сорванная печать сотника","oath")),
)
HUMAN_IDS = (14,15)
EXTRA_HUNT_IDS = (12,13) + HUMAN_IDS
HUMAN_TRAITS = {
    "robber":("Засада","В первом раунде наносит усиленный ответный удар."),
    "oath":("Караульная стойка","Каждый чётный раунд гасит часть урона щитом."),
    "changed":("Судорога Мора","Ниже половины ХП наносит усиленный ответный удар."),
    "cult":("Счёт недостачи","Каждый третий раунд отнимает у каждого героя 1 энергию, если переживёт удар."),
}
def faction(z,n):
    return HUMAN_HUNTS[z][n-14][2] if n in HUMAN_IDS else None

# Existing encounter IDs by zone, including dungeon and vault inhabitants.
HUMANOID_ENCOUNTERS = (
    {3, 5, 7, 8},
    {3, 4, 5, 6, 7},
    {1, 2, 3, 4, 5, 6, 7, 8},
    {3, 5, 7, 8},
    {3, 4, 5, 6, 7, 8},
    {2, 3, 4, 5, 6, 7, 8},
    {3, 4, 5, 6, 7, 8},
    {2, 3, 4, 5, 7, 8, 9, 10, 11},
    {4, 6, 7, 8, 9, 10, 11},
)

def is_humanoid(z, n):
    return n in HUMAN_IDS or n in HUMANOID_ENCOUNTERS[z]

def encounter_trait(z,n):
    return HUMAN_TRAITS.get(faction(z,n),TRAITS[n%3])

HUNT_IDS = (0,1,2) + EXTRA_HUNT_IDS

def monster(z, idx):
    if idx in HUMAN_IDS: return HUMAN_HUNTS[z][idx-14][0]
    if idx in EXTRA_HUNT_IDS:
        return NEW_HUNTS[z][idx-12][0]
    zone = ZONES[z]
    if idx >= 9:
        return VAULTS[z][1][idx-9]
    if idx < 3:
        return zone[1][idx]
    return zone[2][(idx-3)//3][1+(idx-3)%3]

def rank(z, idx):
    return 10*BANDS[z]+(1,5,9,3,4,5,7,9,10,8,9,10,3,7,2,8)[idx]

def base_strength(z,k):
    if (z,k) in CLASS_PIECES:
        return (4+2*BANDS[z])*(2 if two_handed(gear_names(z)[k]) else 1) if gear_slot(z,k)==RIGHT else 2+BANDS[z]
    if k>=outfit_start(z): return 2+BANDS[z]
    if k>=arm_start(z):
        power = 4 + 2*BANDS[z] + (3 if z in VAULTS and (k-arm_start(z))%4==3 else 0)
        return power*2 if two_handed(ARMS[z][k-arm_start(z)]) else power
    if k>=original_count(z): return 1+BANDS[z]//2+(k-original_count(z))//4
    return 2*BANDS[z]+(7 if k>=6 else 1+k//2)

BANDS = (0,1,2,3,4,5,0,2,5)
UPPER_AREAS = ("Заливные покосы","Дорога соляных обозов","Чёрные запруды",
               "Пепельные угодья","Сухие верфи","Берег последнего лова",
               "Заброшенные суконные дворы","Вдовьи соляные колодцы","Архив списанных мер")

def area_name(z,half):
    return UPPER_AREAS[z] if half else ZONES[z][0]

def encounter_area(z,n):
    return area_name(z,(rank(z,n)-1)%10>=5)

# Zone id -> vault name, inhabitants and exclusive equipment.
VAULTS = {6: ('Подпол запечатанного улья',
     ('Личинка кладового воска', 'Девятилапый сторож', 'Хозяйка воскового погреба'),
     ('Гусзкская восковая бляха', 'Котта кладового дозора')),
 7: ('Шахта вычеркнутой смены',
     ('Сменщик без бирки', 'Чтец водомерной книги', 'Человек из каменной соли'),
     ('Пломба остановленной клети', 'Риза последней смены')),
 8: ('Хранилище последней меры',
     ('Смотритель часовых стёкол', 'Оценщик прожитых лет', 'Мёртвый поверенный'),
     ('Амулет последней поверки', 'Кираса закрытого счёта'))}
SCRAPS = ['Стёртый собачий зуб|Мучное крылышко|Кусок гуменной шкуры|Половина мельничного пая|Засохший ком сечи|Щербина жернова|Солонинная '
 'оболочка|Жаберная пуговка|Свинцовый довесок',
 'Расщеплённый кабаний резец|Лозовая линька|Жжёное турье клеймо|Медная пошлинка|Межевая зарубка|Половинка присяжной '
 'дощечки|Засаленная бирка овцы|Зуб стригальных ножниц|Пепельное руно',
 'Пёстрое маховое перо|Обрывок поводка|Серповой ноготь|Кусок бельевого мыла|Кромка белёного полотна|Известковая '
 'перчатка|Промокший подорожник|Изжёванный конверт|Сургуч без оттиска',
 'Куний ус|Клок подшёрстка|Попонная застёжка|Острожный жетон|Стёртая подкова|Железный гуж|Медвежий подушечный волос|Осколок '
 'бубенца|Костяной ключ ночлега',
 'Панцирёк хруща|Коршуново очинье|Кусок рудной жвачки|Капля пробной меди|Тигельная окалина|Монетный облой|Бирка штольни|Гвоздь '
 'десятника|Половина протокола',
 'Соляная лисья шерсть|Скребковый зуб|Камень со следом стопы|Щепа посольного чана|Изношенная чашка весов|Обломок печати '
 'свежести|Корабельный костыль|Раковина с гулом|Клок приливного покрывала',
 'Жвала рвового тенётника|Пятнистый хвостик|Погрызенный кочан|Ком гашёной извести|Вощёная дратва|Семишовный лоскут|Сухая нитяная '
 'оболочка|Веретённая заноза|Свалявшийся уток|Мучной опарыш|Надломленный паучий зубец|Шелуха запечатанного гнезда',
 'Рапная икринка|Ивовая линька|Обломок болотной трости|Черпак без ручки|Соль с ходулей|Кипятильный крючок|Зуб '
 'слепушонки|Колодезный жетон|Гипсовый отпечаток|Метка покойной смены|Шнур водомерной книги|Осколок соляной ладони',
 'Осиный известковый ус|Слюдяная пластинка|Кремневый резец|Надкрылье усача|Треснувшая мерная линза|Грузик отвеса|Костяная '
 'адресная бирка|Обломок грифеля|Край завещательной печати|Песчинка из часового стекла|Пластинка с датой смерти|Ключ от пустой '
 'ячейки']
SCRAPS = [row.split("|") for row in SCRAPS]

for z, row in enumerate(SCRAPS):
    SCRAPS[z] = dict(enumerate(row))
    SCRAPS[z].update({n: NEW_HUNTS[z][n-12][1] for n in (12,13)})
    SCRAPS[z].update({n:HUMAN_HUNTS[z][n-14][1] for n in HUMAN_IDS})

SCRAPS[6][98]="Связка выделанных шкур"

def gear_names(z):
    return NAMES[z]

RECIPE_SLOTS = {}

def legacy_names(z):
    return ZONES[z][3]+(VAULTS[z][2] if z in VAULTS else ())+tuple(name for _,name in EXTRA[z])+tuple(ARMS[z])+tuple(name for _,name in OUTFITS[z])

# First two slots retain the familiar neck and body slots for legacy saves.
SLOTS = ("Шея","Нагрудник","Голова","Серьги","Наплечники","Рубаха","Наручи",
         "Кольцо I","Кольцо II","Плащ","Пояс","Перчатки","Поножи","Сапоги","Левая рука","Правая рука")
SLOT_ORDER = (2,3,0,4,1,5,6,9,7,8,10,11,12,13,14,15)
RINGS = (7,8)
EXTRA = [((2, 'Колпак уличного мучника'),
  (3, 'Серьги с полыми зёрнами'),
  (5, 'Рубаха первого помола'),
  (11, 'Рукавицы жерновщика'),
  (13, 'Сапоги амбарной очереди'),
  (7, 'Кольцо с печатью подворья')),
 ((4, 'Наплечники межевого объездчика'),
  (6, 'Наручи стригаля'),
  (10, 'Ремень землемера Ровни'),
  (12, 'Поножи турьего гона'),
  (2, 'Шлем заставного выборного'),
  (3, 'Серьги двойной пошлины')),
 ((5, 'Рубаха мельвской белильщицы'),
  (11, 'Перчатки адресного писца'),
  (13, 'Сапоги почтовой эстафеты'),
  (7, 'Кольцо с обратным адресом'),
  (4, 'Оплечье полотняного двора'),
  (10, 'Пояс ночного курьера')),
 ((3, 'Серьги из зубов куницы'),
  (12, 'Поножи упряжника'),
  (2, 'Малахай первой стоянки'),
  (6, 'Наручи санного конвоя'),
  (5, 'Рубаха зимнего постояльца'),
  (13, 'Сапоги седловинного караула')),
 ((10, 'Ремень пробирного двора'),
  (4, 'Наплечники маркшейдера'),
  (11, 'Перчатки медного съёмщика'),
  (3, 'Серьги со стружкой вересской меди'),
  (7, 'Кольцо несчастного случая'),
  (12, 'Поножи шахтного лазутчика')),
 ((6, 'Наручи рыбного приёмщика'),
  (13, 'Сапоги сухого причала'),
  (5, 'Рубаха разделочного стола'),
  (2, 'Венец нижнего берега'),
  (10, 'Пояс тарнского поручителя'),
  (4, 'Оплечье пустого невода')),
 ((9, 'Плащ обходчика рвов'),
  (10, 'Пояс корневого сторожа'),
  (6, 'Наручи гашёной извести'),
  (12, 'Поножи копателя канав'),
  (4, 'Оплечье рваного сукна'),
  (11, 'Перчатки вдовьей штопки')),
 ((12, 'Поножи на соляных завязках'),
  (2, 'Шляпа сборщика рапы'),
  (5, 'Рубаха белого налёта'),
  (6, 'Наручи подъёмной клети'),
  (7, 'Перстень колодезной доли'),
  (13, 'Сапоги солёного следа')),
 ((11, 'Перчатки поверщика стёкол'),
  (9, 'Плащ слюдяной стражи'),
  (4, 'Наплечники завещательного двора'),
  (10, 'Пояс сверщика мер'),
  (3, 'Серьги с зерном кварца'),
  (2, 'Шлем второй смены'))]
def original_count(z):
    return 8 if z in VAULTS else 6

BASE_SLOTS = [[0, 1, 0, 1, 7, 1], [0, 1, 0, 1, 0, 1], [0, 9, 0, 1, 7, 1], [0, 1, 0, 1, 0, 9], [0, 1, 0, 1, 0, 1], [0, 1, 0, 9, 7, 9], [0, 1, 7, 1, 0, 9, 0, 1], [0, 9, 0, 1, 0, 1, 0, 1], [0, 1, 0, 1, 0, 9, 0, 1]]

def gear_slot(z,k):
    if (z,k) in RECIPE_SLOTS: return RECIPE_SLOTS[z,k]
    if (z,k) in CLASS_PIECES: return CLASS_PIECES[z,k][1]
    if k>=outfit_start(z): return OUTFITS[z][k-outfit_start(z)][0]
    if k>=arm_start(z):
        return LEFT if ARM_BY_NAME[ARMS[z][k-arm_start(z)]][1] in ("Фолиант","Щит") else RIGHT
    if k>=original_count(z): return EXTRA[z][k-original_count(z)][0]
    return BASE_SLOTS[z][k]

def item_slot_label(z,k):
    slot = gear_slot(z,k)
    if slot in RINGS:
        return "Кольцо I или II"
    if slot == RIGHT and two_handed(gear_names(z)[k]):
        return "Правая рука · занимает обе руки"
    return SLOTS[slot]

def gear_stat(z,k):
    return int(gear_slot(z,k) != RIGHT)

def required_level(z):
    return 1+10*BANDS[z]

from bisect import bisect_right
LIMITS = [0]
for lv in range(1,60):
    LIMITS.append(LIMITS[-1]+8*(50+10*lv))

def level(h):
    return bisect_right(LIMITS,h["xp"])


LEFT, RIGHT = 14, 15
# Each tradition has two named sets and six weapon families.
TRADITIONS = (('guard', 'Меч', 'воротного десятка', 'гусзкского засова'),
 ('nun', 'Булава', 'лазаретного круга', 'белильной палаты'),
 ('archer', 'Тесак', 'межевого дозора', 'тарнских следопытов'),
 ('smith', 'Молот', 'ремонтной артели', 'вересских медников'),
 ('witch', 'Серп', 'ровной знахарки', 'лужских солеведок'))
ARMS = [[] for _ in ZONES]
ARM_BY_NAME = {}
for ci,(cls,melee,first,second) in enumerate(TRADITIONS):
    for tier,suffix in enumerate((first,second)):
        for fi,family in enumerate((melee,"Жезл","Фолиант","Лук","Арбалет","Щит")):
            z = ((ci+fi)%3, (ci+fi+1)%3+3)[tier]
            if fi%3==ci%3:
                z = 6+(ci+fi+tier)%3
            item = family+" "+suffix
            ARMS[z].append(item)
            ARM_BY_NAME[item] = (cls,family)
def arm_start(z):
    return original_count(z)+len(EXTRA[z])

def two_handed(item):
    return ARM_BY_NAME.get(item,(None,None))[1] in ("Лук","Арбалет")

# Appended after weapons so earlier item codes stay stable.
OUTFITS = [
 ((2,"Шапель амбарной стражи"),(11,"Рукавицы мукомола"),(7,"Перстень хлебного суда"),(5,"Льняная рубаха обозника")),
 ((6,"Краги ловчего Ровни"),(13,"Сапоги ночного брода"),(9,"Плащ загонщика туров"),(10,"Пояс пограничного егеря")),
 ((3,"Серебряные серьги сестры милосердия"),(5,"Сорочка полевого лекаря"),(0,"Медальон Ордена Матери"),(11,"Перчатки костоправа")),
 ((4,"Наплечники горного проводника"),(12,"Поножи зимнего конвоя"),(1,"Бригантина начальника обоза"),(2,"Шлем перевальной стражи")),
 ((10,"Пояс цехового мастера"),(6,"Наручи мостостроителя"),(0,"Знак Гильдии инженеров"),(13,"Башмаки пробирщика")),
 ((9,"Плащ портового дозора"),(3,"Серьги тарнской вдовы"),(7,"Перстень весовой палаты"),(1,"Кираса берегового рыцаря")),
 ((5,"Рубаха сборщицы трав"),(10,"Пояс аптекарской ученицы"),(4,"Оплечье ночного сторожа"),(11,"Перчатки сборщика корней")),
 ((13,"Сапоги соляной артели"),(2,"Капюшон лужского возчика"),(6,"Наручи колодезника"),(7,"Кольцо соляного старшины")),
 ((12,"Поножи чеканского сержанта"),(0,"Ладанка присяжного мастера"),(3,"Серьги из красного хрусталя"),(9,"Мантия цехового судьи")),
]
def outfit_start(z):
    return arm_start(z)+len(ARMS[z])

from loadouts import pieces
CLASS_PIECES = {}
NAMES = [list(legacy_names(z)) for z in range(len(ZONES))]
SOURCES = {}
for band in range(6):
    zones=[z for z,b in enumerate(BANDS) if b==band]
    for index,piece in enumerate(pieces(band)):
        name,slot,cls,tier,family,bonus=piece
        z=zones[(index//35+index%35)%len(zones)]
        k=len(NAMES[z])
        NAMES[z].append(name)
        CLASS_PIECES[z,k]=piece
        if slot in (LEFT,RIGHT): ARM_BY_NAME[name]=(cls,family)
        # Ordinary outfits are available on hunts, rare outfits in both group dungeons.
        sources=(0,) if tier==0 else (1,2) if tier==1 else tuple(range(3+(z in VAULTS)))
        for source in sources: SOURCES.setdefault((z,source),[]).append(k)

SEAM_SHIELD = "Щит семи швов"
SEAM_INDEX = len(NAMES[6])
NAMES[6].append(SEAM_SHIELD)
CLASS_PIECES[6,SEAM_INDEX]=(SEAM_SHIELD,LEFT,"guard",1,"Щит","guard")
ARM_BY_NAME[SEAM_SHIELD]=("guard","Щит")

STAT_NAMES = ("Сила","Ловкость","Выносливость","Воля")
def legacy_loot_slots(z,n):
    if n in EXTRA_HUNT_IDS: n=0
    source = 0 if n<3 else 1 if n<6 else 2 if n<9 else 3
    pools = 4 if z in VAULTS else 3
    arms = tuple(arm_start(z)+i for i in range(len(ARMS[z])) if i%pools==source)
    outfit = (outfit_start(z)+source,)
    if source==2 and z not in VAULTS: outfit += (outfit_start(z)+3,)
    moved = (original_count(z)+5,) if z in (7,8) else ()
    if n>=9: return (6,7)+arms+outfit+moved
    pair = 0 if n<3 else 2 if n<6 else 4
    extra = original_count(z)+pair
    return tuple(k for k in (pair,pair+1,extra,extra+1)+arms+outfit if k not in moved)

TIERS = ("Обычное","Редкое","Превосходное","Уникальное","Артефакт")
# Weights out of 1000, conditional on equipment dropping.
TIER_WEIGHTS = {"hunt":(820,180,0,0,0),"raid":(0,720,220,50,10),"vault":(0,660,250,75,15)}
RARITY = {}
for z in range(len(ZONES)):
    for n in ((0,5,8,11) if z in VAULTS else (0,5,8)):
        ordered = sorted(legacy_loot_slots(z,n),key=lambda k:(base_strength(z,k),k))
        for position,k in enumerate(ordered):
            RARITY[z,k] = position*4//(len(ordered)-1)

RARITY.update({code:piece[3] for code,piece in CLASS_PIECES.items()})

def historical_loot_slots(z,n,cls=None):
    source=0 if n in HUNT_IDS else n//3
    extra=SOURCES.get((z,source),())
    boss_drop=(SEAM_INDEX,) if (z,n)==(6,5) and cls in (None,"guard") else ()
    return boss_drop+legacy_loot_slots(z,n)+tuple(k for k in extra if cls is None or CLASS_PIECES[z,k][2]==cls)

# Items unique to the upper hunting grounds, second dungeon or vault unlock halfway through a band.
UPPER_GEAR = set()
for zone in range(len(ZONES)):
    early = set(historical_loot_slots(zone,0)) | set(historical_loot_slots(zone,5))
    late = set(historical_loot_slots(zone,8))
    if zone in VAULTS: late.update(historical_loot_slots(zone,11))
    UPPER_GEAR.update((zone,k) for k in late-early)

from workshop_data import patterns

# Codes never move. Inactive models stay readable in inventories and pending loot.
ORIGINAL_RARITY=RARITY.copy()
ORIGIN = {}
RECIPES = {}
for z,names in enumerate(NAMES):
    for k in range(outfit_start(z)+len(OUTFITS[z])):
        if k < original_count(z):
            source,tier=(("hunt",0),("quest",0),("quest",1),("dungeon",1),
                         ("dungeon",2),("dungeon",3),("dungeon",2),("dungeon",4))[k]
        elif arm_start(z)<=k<outfit_start(z):
            continue
        else:
            source,tier=(("hunt",1),("quest",1),("dungeon",1))[(k-original_count(z))%3]
        ORIGIN[z,k]=source
        RARITY[z,k]=tier
for (z,k),(_,slot,cls,tier,family,_) in CLASS_PIECES.items():
    if slot in (LEFT,RIGHT) and tier in (0,1,4):
        ORIGIN[z,k]=("hunt","quest","dungeon")[0 if tier==0 else 1 if tier==1 else 2]
    elif cls=="guard" and tier==0 and slot<LEFT:
        ORIGIN[z,k]="quest" if slot%2 else "hunt"
    if slot==RIGHT and tier==2:
        trade="sew" if cls=="archer" else "forge"
        ORIGIN[z,k]="deep"
        RECIPES[z,k]=(trade,True,20*BANDS[z]+15)
for band in range(6):
    # A poacher can find a bow before obtaining a workshop pattern.
    bow=next(((z,k) for z,items in enumerate(NAMES) if BANDS[z]==band
              for k,item in enumerate(items[:outfit_start(z)]) if ARM_BY_NAME.get(item)==("archer","Лук")),None)
    if bow:
        ORIGIN[bow]="hunt"
        RARITY[bow]=1
ORIGIN[6,SEAM_INDEX]="dungeon"
for band,trade,item,slot,tier,deep,skill in patterns():
    z=BANDS.index(band)
    k=len(NAMES[z])
    NAMES[z].append(item)
    RECIPE_SLOTS[z,k]=slot
    RECIPES[z,k]=(trade,deep,skill)
    ORIGIN[z,k]="deep" if deep else "craft"
    RARITY[z,k]=tier

# Keep a complete wearable wardrobe per decade and a local reward of each
# field/contract quality in every region. Prefer named regional pieces.
wardrobe=set()
for band in range(6):
    options=[p for p,source in ORIGIN.items() if BANDS[p[0]]==band and
             source in ("hunt","quest") and gear_slot(*p)<LEFT]
    for slot in set(range(LEFT))-{8}:
        eligible=sorted((p for p in options if gear_slot(*p)==slot),
                        key=lambda p:(p in UPPER_GEAR,p in CLASS_PIECES,p))
        wardrobe.update(eligible[:2 if slot==7 else 1])
for z in range(len(ZONES)):
    for source in ("hunt","quest"):
        for tier in (0,1):
            local=next((p for p,o in ORIGIN.items() if p[0]==z and o==source and
                        gear_slot(*p)<LEFT and RARITY[p]==tier),None)
            if local:wardrobe.add(local)
for p,source in list(ORIGIN.items()):
    slot=gear_slot(*p)
    if source in ("hunt","quest") and ((slot<LEFT and p not in wardrobe) or (slot==LEFT and source=="quest")):
        del ORIGIN[p]
        RARITY[p]=ORIGINAL_RARITY[p]

def suitable(z,k,cls):
    arm=ARM_BY_NAME.get(NAMES[z][k])
    return cls is None or not arm or arm[0]==cls

from functools import lru_cache
@lru_cache(None)
def loot_slots(z,n,cls=None):
    hunting=n in HUNT_IDS
    return tuple(k for k in range(len(NAMES[z]))
                 if ORIGIN.get((z,k))==("hunt" if hunting else "dungeon") and suitable(z,k,cls)
                 and ((z,k)!=(6,SEAM_INDEX) or n==5)
                 and (RARITY[z,k]<3 or n%3==2))

def wear_level(z,k):
    if (z,k) in RECIPES: return required_level(z)+(7 if RECIPES[z,k][1] else 3)
    return required_level(z) + (5 if (z,k) in UPPER_GEAR else 0)

def tier_name(z,k):
    return TIERS[RARITY[z,k]]

def trade_value(z,k):
    tier=RARITY[z,k]
    if (z,k) in RECIPES: return 5+2*BANDS[z]+tier
    return base_strength(z,k)*(4+tier)//4+tier

# Primary bonuses are stored in displayed units (HP or attack).
# Each ten-level band improves every slot; heavy pieces also improve at mid-band.
SLOT_HP = (2, 5, 4, 2, 4, 2, 2, 2, 2, 3, 2, 2, 4, 3, 2)
BUDGET={"hunt":(90,95),"quest":(100,105),"craft":(104,109,114),
        "deep":(0,113,118,123),"dungeon":(0,116,121,126,130)}
def strength(z,k):
    source=ORIGIN.get((z,k))
    if not source: return legacy_strength(z,k)
    slot=gear_slot(z,k)
    offset=wear_level(z,k)-1
    base=4+offset//5 if slot==RIGHT else SLOT_HP[slot]+offset//(5 if slot in (1,LEFT) else 10)
    power=max(1,(base*BUDGET[source][RARITY[z,k]]+50)//100)
    return power*2 if slot==RIGHT and two_handed(NAMES[z][k]) else power

def legacy_strength(z,k):
    slot = gear_slot(z,k)
    tier = RARITY[z,k]
    level_offset = wear_level(z,k)-1
    item = gear_names(z)[k]
    if slot == RIGHT:
        power = 4 + level_offset//5 + tier//2
        return power*2 if two_handed(item) else power
    shield = ARM_BY_NAME.get(item,(None,None))[1] in ("Щит","Баклер")
    if shield or slot == 1:
        return (4 if shield else SLOT_HP[slot]) + level_offset//5 + tier//2
    return SLOT_HP[slot] + level_offset//10 + tier//2

def class_power(cls,item,power):
    if item in ARM_BY_NAME and ARM_BY_NAME[item][0]!=cls:
        return max(1,power//2)
    return power

# Outfit attributes follow the part of the body the item protects.
OUTFIT_ATTRIBUTE = (3,2,2,3,0,2,1,3,3,2,2,1,2,1,3,0)
ITEM_TRAITS = {name:(OUTFIT_ATTRIBUTE[slot],1+BANDS[z]//3+RARITY[z,outfit_start(z)+idx]//4)
               for z,row in enumerate(OUTFITS) for idx,(slot,name) in enumerate(row)}

ITEM_CODES = {item:f"{z}.{k}" for z in range(len(ZONES)) for k,item in enumerate(gear_names(z))}
CODE_ITEMS = {code:item for item,code in ITEM_CODES.items()}

# Stable inventory codes from saves made before the Frivolous Cities edition.
OLD_CODES = {'Волчий клык': '0.0',
 'Куртка ловчего': '0.1',
 'Костяная печать': '0.2',
 'Рёберный панцирь': '0.3',
 'Перстень утопленника': '0.4',
 'Кольчуга из заводи': '0.5',
 'Капюшон углежога': '0.6',
 'Серьги из вороньих костей': '0.7',
 'Холщовая рубаха сторожа': '0.8',
 'Рукавицы могильщика': '0.9',
 'Сапоги из промасленной кожи': '0.10',
 'Кольцо с серой яшмой': '0.11',
 'Фолиант часовни свечей': '0.12',
 'Щит часовни свечей': '0.13',
 'Жезл лесного дозора': '0.14',
 'Арбалет лесного дозора': '0.15',
 'Фолиант болотной заводи': '0.16',
 'Щит болотной заводи': '0.17',
 'Терновая брошь': '1.0',
 'Вепревый нагрудник': '1.1',
 'Осколок колокола': '1.2',
 'Латы звонаря': '1.3',
 'Олений оберег': '1.4',
 'Мшистый доспех': '1.5',
 'Наплечники егеря': '1.6',
 'Наручи из оленьего рога': '1.7',
 'Терновый ремень': '1.8',
 'Поножи ловчего': '1.9',
 'Шлем загонщика': '1.10',
 'Медные серьги звонаря': '1.11',
 'Жезл палисадной стражи': '1.12',
 'Арбалет палисадной стражи': '1.13',
 'Булава часовни свечей': '1.14',
 'Лук часовни свечей': '1.15',
 'Жезл могильной кузни': '1.16',
 'Арбалет могильной кузни': '1.17',
 'Серп болотной заводи': '1.18',
 'Лук болотной заводи': '1.19',
 'Вороний коготь': '2.0',
 'Плащ карантина': '2.1',
 'Ланцет лекаря': '2.2',
 'Восковой нагрудник': '2.3',
 'Угольная печатка': '2.4',
 'Фартук костожога': '2.5',
 'Рубаха травника': '2.6',
 'Перчатки чумного лекаря': '2.7',
 'Сапоги зольника': '2.8',
 'Кольцо карантинной стражи': '2.9',
 'Оплечье костожога': '2.10',
 'Пояс с кадилом': '2.11',
 'Фолиант палисадной стражи': '2.12',
 'Щит палисадной стражи': '2.13',
 'Тесак лесного дозора': '2.14',
 'Лук лесного дозора': '2.15',
 'Фолиант могильной кузни': '2.16',
 'Щит могильной кузни': '2.17',
 'Клык рыси': '3.0',
 'Медвежья бригантина': '3.1',
 'Ледяной ключ': '3.2',
 'Панцирь надзирателя': '3.3',
 'Серебряный узел': '3.4',
 'Мантия инея': '3.5',
 'Серьги из белого клыка': '3.6',
 'Стёганые поножи': '3.7',
 'Меховая шапка дозорного': '3.8',
 'Наручи надзирателя': '3.9',
 'Рубаха из снежного льна': '3.10',
 'Сапоги курганного стража': '3.11',
 'Фолиант чёрной заставы': '3.12',
 'Щит чёрной заставы': '3.13',
 'Тесак лунной тропы': '3.14',
 'Лук лунной тропы': '3.15',
 'Фолиант пепельного горна': '3.16',
 'Щит пепельного горна': '3.17',
 'Глаз грифа': '4.0',
 'Базальтовая кираса': '4.1',
 'Клеймо горна': '4.2',
 'Латы литейщика': '4.3',
 'Багряная фибула': '4.4',
 'Риза епископа': '4.5',
 'Ремень камнелома': '4.6',
 'Наплечники из базальта': '4.7',
 'Перчатки литейщика': '4.8',
 'Гранатовые серьги': '4.9',
 'Кольцо рубца': '4.10',
 'Поножи певчего': '4.11',
 'Фолиант белой обители': '4.12',
 'Щит белой обители': '4.13',
 'Жезл лунной тропы': '4.14',
 'Арбалет лунной тропы': '4.15',
 'Фолиант терновой ведьмы': '4.16',
 'Щит терновой ведьмы': '4.17',
 'Змеиный камень': '5.0',
 'Доспех пустоты': '5.1',
 'Чёрная закладка': '5.2',
 'Плащ архивариуса': '5.3',
 'Перстень бездны': '5.4',
 'Королевский саван': '5.5',
 'Наручи пепельного писца': '5.6',
 'Сапоги пустого латника': '5.7',
 'Рубаха архивариуса': '5.8',
 'Венец из сажи': '5.9',
 'Пояс знаменосца': '5.10',
 'Оплечье безмолвия': '5.11',
 'Жезл чёрной заставы': '5.12',
 'Арбалет чёрной заставы': '5.13',
 'Булава белой обители': '5.14',
 'Лук белой обители': '5.15',
 'Жезл пепельного горна': '5.16',
 'Арбалет пепельного горна': '5.17',
 'Серп терновой ведьмы': '5.18',
 'Лук терновой ведьмы': '5.19',
 'Янтарный глаз': '6.0',
 'Кафтан дубильщика': '6.1',
 'Резной напёрсток': '6.2',
 'Дублёная бригантина': '6.3',
 'Шёлковый узел': '6.4',
 'Покров пряхи': '6.5',
 'Печать вдовы': '6.6',
 'Хитиновая котта': '6.7',
 'Плащ паутинщика': '6.8',
 'Ремень корнееда': '6.9',
 'Кожаные наручи': '6.10',
 'Поножи из луба': '6.11',
 'Оплечье ткачихи': '6.12',
 'Перчатки шёлкопряда': '6.13',
 'Меч палисадной стражи': '6.14',
 'Лук палисадной стражи': '6.15',
 'Жезл белой обители': '6.16',
 'Арбалет белой обители': '6.17',
 'Молот могильной кузни': '6.18',
 'Лук могильной кузни': '6.19',
 'Жезл терновой ведьмы': '6.20',
 'Арбалет терновой ведьмы': '6.21',
 'Белый зубец': '7.0',
 'Камышовый плащ': '7.1',
 'Соляное клеймо': '7.2',
 'Фартук выпарщика': '7.3',
 'Линза слепца': '7.4',
 'Кристальная кольчуга': '7.5',
 'Соляная реликвия': '7.6',
 'Риза мощевика': '7.7',
 'Поножи солевара': '7.8',
 'Камышовая шляпа': '7.9',
 'Рубаха выпарщика': '7.10',
 'Наручи шахтёра': '7.11',
 'Перстень белой жилы': '7.12',
 'Сапоги топографа': '7.13',
 'Меч чёрной заставы': '7.14',
 'Лук чёрной заставы': '7.15',
 'Фолиант лесного дозора': '7.16',
 'Щит лесного дозора': '7.17',
 'Молот пепельного горна': '7.18',
 'Лук пепельного горна': '7.19',
 'Ониксовый шип': '8.0',
 'Осиный панцирь': '8.1',
 'Зеркальный жетон': '8.2',
 'Латы отражений': '8.3',
 'Литая звезда': '8.4',
 'Мантия архонта': '8.5',
 'Грань легата': '8.6',
 'Алмазная кираса': '8.7',
 'Перчатки стеклодува': '8.8',
 'Плащ с ониксовой застёжкой': '8.9',
 'Зеркальные наплечники': '8.10',
 'Пояс шлифовщика': '8.11',
 'Серьги из чёрного стекла': '8.12',
 'Шлем из дымчатого кварца': '8.13',
 'Жезл часовни свечей': '8.14',
 'Арбалет часовни свечей': '8.15',
 'Фолиант лунной тропы': '8.16',
 'Щит лунной тропы': '8.17',
 'Жезл болотной заводи': '8.18',
 'Арбалет болотной заводи': '8.19'}

BONUS_NAMES = dict(crit="шанс крита", severity="сила крита", guard="сила блока",
                   medicine="лечение умением", strike="сила атаки", reserve="запас энергии")
def secondary(z,k):
    item=gear_names(z)[k]
    slot=gear_slot(z,k)
    arm=ARM_BY_NAME.get(item)
    if arm:
        cls,family=arm
        if family in ("Щит","Баклер"): kind="guard"
        elif family in ("Лук","Арбалет"): kind="crit" if family=="Лук" else "severity"
        elif cls=="guard": kind="guard" if family=="Фолиант" else "strike"
        elif cls=="nun": kind="medicine" if family in ("Фолиант","Жезл") else "strike"
        elif cls=="archer": kind="crit"
        elif cls=="smith": kind="severity"
        else: kind="reserve" if family=="Фолиант" else "strike"
    elif (z,k) in CLASS_PIECES:
        kind=CLASS_PIECES[z,k][5] if slot in (0,3,7,11) else ("reserve" if slot in (5,9,10,13) else "guard")
    elif any(word in item.lower() for word in ("полевого лекаря","милосердия","костоправа","ордена матери")):
        kind="medicine"
    elif any(word in item.lower() for word in ("прицел","ловчего","охотнич","егеря")): kind="crit"
    elif any(word in item.lower() for word in ("гвард","страж","караул","панцирь","кираса")): kind="guard"
    else: kind=("reserve","guard","guard","crit","guard","reserve","strike","severity","severity","reserve","reserve","strike","guard","reserve","guard","strike")[slot]
    scale=1+BANDS[z]//3+(RARITY[z,k]+1)//2
    return kind,3*scale if kind=="severity" else scale

SECONDARY={item:secondary(z,k) for z in range(len(ZONES)) for k,item in enumerate(gear_names(z))}
def worn_bonus(h,item):
    kind,value=SECONDARY[item]
    if item in ARM_BY_NAME and ARM_BY_NAME[item][0]!=h["class"]: value=max(1,value//2)
    return kind,value

def bonus_label(h,item):
    kind,value=worn_bonus(h,item)
    unit=" п.п." if kind in ("crit","severity") else ""
    text=f"{BONUS_NAMES[kind]} +{value}{unit}"
    if item==SEAM_SHIELD: text+=" · после блока следующая Стена щитов даёт +4 защиты, один раз за поход"
    return text


def category(z,k):
    slot=gear_slot(z,k)
    if slot==RIGHT: return "Оружие"
    if slot==LEFT:
        family=ARM_BY_NAME.get(gear_names(z)[k],(None,None))[1]
        return "Броня" if family in ("Щит","Баклер") else "Оружие"
    return "Аксессуары" if slot in (0,3,7,8) else "Броня"
