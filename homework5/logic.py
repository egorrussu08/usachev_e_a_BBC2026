"""Общая логика расчёта стоимости занятий репетитора.

Этот модуль не зависит от графических библиотек, поэтому его используют
и версия на Tkinter, и версия на Qt.
"""

from dataclasses import dataclass

# Сколько минут в одном часе выбранного типа
MINUTES = {
    "academic": 45,      # академический час
    "astronomic": 60,    # астрономический час
}

HOUR_TYPE_LABELS = {
    "academic": "Академический (45 мин)",
    "astronomic": "Астрономический (60 мин)",
}


class InputError(ValueError):
    """Ошибка проверки поля ввода: хранит название поля для подсветки в окне."""

    def __init__(self, field, message):
        self.field = field
        super().__init__(message)


def _parse_number(text, field, *, integer=False):
    """Превращает текст в число или сообщает, что ввод некорректный."""
    raw = (text or "").strip().replace(",", ".")
    if raw == "":
        raise InputError(field, f"В поле «{field}» введите число.")
    try:
        value = int(raw) if integer else float(raw)
    except ValueError:
        kind = "целое число" if integer else "число"
        raise InputError(field, f"В поле «{field}» введите {kind}.") from None
    if integer and "." in raw:
        raise InputError(field, f"В поле «{field}» введите целое число.")
    return value


def parse_positive(text, field, *, integer=False):
    """Число строго больше нуля (ставка, часы, число занятий)."""
    value = _parse_number(text, field, integer=integer)
    if value <= 0:
        raise InputError(field, f"В поле «{field}» введите число больше нуля.")
    return value


def parse_non_negative(text, field, empty=0.0):
    """Число не меньше нуля; пустое поле считается как empty."""
    if (text or "").strip() == "":
        return empty
    value = _parse_number(text, field, integer=False)
    if value < 0:
        raise InputError(field, f"В поле «{field}» введите число не меньше нуля.")
    return value


def parse_percent(text, field, empty=0.0):
    """Скидка от 0 до 100 процентов; пустое поле = 0."""
    value = parse_non_negative(text, field, empty=empty)
    if value > 100:
        raise InputError(field, f"В поле «{field}» введите число от 0 до 100.")
    return value


def money(value):
    """Округляет сумму до копеек."""
    return round(value + 1e-9, 2)


def format_money(value):
    """Форматирует сумму: 21600.5 -> '21 600,50 руб.'"""
    sign = "−" if value < 0 else ""
    value = money(abs(value))
    integer, frac = f"{value:.2f}".split(".")
    grouped = f"{int(integer):,}".replace(",", " ")
    return f"{sign}{grouped},{frac} руб."


def format_duration(minutes):
    """Переводит минуты в строку вида '2 ч 15 мин'."""
    total = int(round(minutes))
    hours, mins = divmod(total, 60)
    return f"{hours} ч {mins:02d} мин"


@dataclass
class LessonCost:
    """Результат расчёта стоимости занятий."""

    rate: float
    hours: float
    lessons: int
    hour_type: str
    minutes_per_hour: int
    duration_minutes: float
    subtotal: float
    discount_percent: float
    discount_amount: float
    travel: float
    total: float
    paid: float
    balance: float  # > 0 — долг ученика, < 0 — сдача, 0 — рассчитались

    def as_text(self):
        """Текст результата для вывода в окне программы."""
        hour_name = "академических" if self.hour_type == "academic" else "астрономических"
        lines = [
            f"Всего времени: {format_duration(self.duration_minutes)}"
            f" ({self.hours:g} {hour_name} ч × {self.lessons} зан.)",
            f"Стоимость без скидки: {format_money(self.subtotal)}",
        ]
        if self.discount_percent:
            lines.append(
                f"Скидка {self.discount_percent:g} %: −{format_money(self.discount_amount)}"
            )
        if self.travel:
            lines.append(f"Выезд: {format_money(self.travel)}")
        lines.append(f"К оплате: {format_money(self.total)}")
        if self.paid:
            if self.balance > 0:
                lines.append(
                    f"Оплачено {format_money(self.paid)}, осталось внести {format_money(self.balance)}"
                )
            elif self.balance < 0:
                lines.append(
                    f"Оплачено {format_money(self.paid)}, сдача {format_money(-self.balance)}"
                )
            else:
                lines.append(f"Оплачено {format_money(self.paid)}. Расчёт полный.")
        return "\n".join(lines)


def calculate(rate, hours, lessons, discount=0.0, travel=0.0, paid=0.0, hour_type="academic"):
    """Считает стоимость занятий.

    Скидка применяется только к стоимости занятий, выезд добавляется целиком.
    """
    if hour_type not in MINUTES:
        raise ValueError(f"Неизвестный тип часа: {hour_type}")

    minutes_per_hour = MINUTES[hour_type]
    duration_minutes = hours * minutes_per_hour * lessons
    subtotal = money(rate * hours * lessons)
    discount_amount = money(subtotal * discount / 100)
    total = money(subtotal - discount_amount + travel)
    balance = money(total - paid)
    return LessonCost(
        rate=rate,
        hours=hours,
        lessons=int(lessons),
        hour_type=hour_type,
        minutes_per_hour=minutes_per_hour,
        duration_minutes=duration_minutes,
        subtotal=subtotal,
        discount_percent=discount,
        discount_amount=discount_amount,
        travel=money(travel),
        total=total,
        paid=money(paid),
        balance=balance,
    )


def calculate_from_forms(rate, hours, lessons, discount, travel, paid, hour_type):
    """Принимает текст из полей ввода, проверяет его и возвращает расчёт."""
    return calculate(
        rate=parse_positive(rate, "Ставка за час"),
        hours=parse_positive(hours, "Часов за одно занятие"),
        lessons=parse_positive(lessons, "Количество занятий", integer=True),
        discount=parse_percent(discount, "Скидка"),
        travel=parse_non_negative(travel, "Выезд"),
        paid=parse_non_negative(paid, "Уже оплачено"),
        hour_type=hour_type,
    )
