"""Level ten choices, stored on the shared hero."""
from world import level

OPTIONS={
 "guard":(("Щитоносец","Стена щитов сильнее на четверть. После отражённого удара треть защиты стены сохраняется на следующий раунд."),("Дозорный","Удар кромкой наносит обычный удар и даёт лёгкое прикрытие. Сразу после блока урон выше на треть.")),
 "nun":(("Полевая лекарка","После перевязки повязка лечит ещё два раунда по четверти силы перевязки."),("Знаток ран","Болевая точка наносит половину удара и ослабляет следующий ответ цели до 25%. Чем сильнее цель относительно сестры, тем меньше ослабление.")),
 "archer":(("Стрелок","Меткий выстрел по цели с половиной здоровья или меньше сильнее на четверть."),("Силочник","Силок срабатывает после ответа врага и наносит два обычных удара по силе, без крита.")),
 "smith":(("Осадный мастер","Раскол сильнее на треть. Усиливает собственную атаку и атаки союзников в этом раунде."),("Мастер клина","После Раскола следующий собственный атакующий ход получает дополнительную треть обычного удара.")),
 "witch":(("Отравительница","Повторный клинок обновляет яд и повышает силу дозы на четверть, максимум один раз."),("Реагентщица","Едкая смесь наносит обычный удар и немедленно расходует оставшиеся дозы яда с удвоенным эффектом.")),
}
EXTRA={"guard":"Удар кромкой","nun":"Болевая точка","archer":"Силок","witch":"Едкая смесь"}


def pending(h):
    return bool(h and level(h)>=10 and h.get("direction") not in ("a","b"))


def choose(h,cmd,busy=False):
    options=OPTIONS[h["class"]]
    def button(label,key):return {"text":label,"callback_data":"direction:"+key}
    current=h.get("direction")
    if current and (h.get("direction_swapped") or busy):
        return "Направление · "+options[int(current=="b")][0],[[{"text":"Продолжить","callback_data":"nav:resume"}]]
    valid=["direction:"+k+":"+str(current or "first") for k in ("a","b")]
    if cmd in valid:
        pick=valid.index(cmd)
        key=("a","b")[pick]
        if current and key!=current:h["direction_swapped"]=True
        h["direction"]=key
        return "Направление · "+options[pick][0],[[{"text":"Продолжить","callback_data":"nav:resume"}]]
    text="Выбери направление · ур. 10\n\n"+"\n\n".join(name+"\n"+desc for name,desc in options)
    text+="\n\nАктивный приём заменяет ход: 6 ресурса (у Ученицы дополнительный приём — 7), общая перезарядка с основным умением — через раунд. Первая смена вне боя бесплатна."
    return text,[[button(name,("a","b")[i]+":"+str(current or "first"))] for i,(name,_) in enumerate(options)]
