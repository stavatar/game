"""
Система времени - управляет течением времени в игровом мире.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Callable


class TimeOfDay(Enum):
    """Время суток"""
    DAWN = "рассвет"        # 5-7
    MORNING = "утро"        # 7-12
    NOON = "полдень"        # 12-14
    AFTERNOON = "день"      # 14-18
    EVENING = "вечер"       # 18-21
    NIGHT = "ночь"          # 21-5


class Season(Enum):
    """Сезоны"""
    SPRING = "весна"
    SUMMER = "лето"
    AUTUMN = "осень"
    WINTER = "зима"


class Weather(Enum):
    """Погода"""
    CLEAR = "ясно"
    CLOUDY = "облачно"
    RAINY = "дождливо"
    STORMY = "гроза"
    SNOWY = "снег"
    FOGGY = "туман"


@dataclass
class TimeSystem:
    """
    Система управления игровым временем.

    - 1 игровой день = 24 игровых часа
    - Время можно ускорять/замедлять
    - Сезоны влияют на погоду и поведение NPC
    """

    # Текущее время
    hour: int = 8  # 0-23
    minute: int = 0  # 0-59
    day: int = 1
    month: int = 1  # 1-12
    year: int = 1

    # Погода
    weather: Weather = Weather.CLEAR

    # Скорость времени (минут реального времени = 1 игровой час)
    time_scale: float = 1.0

    # Колбэки на события времени
    _hour_callbacks: List[Callable] = None
    _day_callbacks: List[Callable] = None

    def __post_init__(self):
        if self._hour_callbacks is None:
            self._hour_callbacks = []
        if self._day_callbacks is None:
            self._day_callbacks = []

    def advance(self, minutes: int = 1) -> List[str]:
        """
        Продвигает время вперёд.
        Возвращает список событий.
        """
        events = []

        self.minute += minutes

        # Обработка перехода часов
        while self.minute >= 60:
            self.minute -= 60
            self.hour += 1
            events.extend(self._on_hour_change())

        # Обработка перехода дней
        while self.hour >= 24:
            self.hour -= 24
            self.day += 1
            events.extend(self._on_day_change())

        # Обработка перехода месяцев
        while self.day > 30:  # Упрощённо: 30 дней в месяце
            self.day -= 30
            self.month += 1
            events.extend(self._on_month_change())

        # Обработка перехода лет
        while self.month > 12:
            self.month -= 12
            self.year += 1
            events.append(f"Наступил новый год: {self.year}")

        return events

    def advance_hours(self, hours: int) -> List[str]:
        """Продвигает время на указанное количество часов"""
        return self.advance(hours * 60)

    def _on_hour_change(self) -> List[str]:
        """Вызывается при смене часа"""
        events = []

        # Проверяем смену времени суток
        old_tod = self._get_time_of_day(self.hour - 1 if self.hour > 0 else 23)
        new_tod = self.get_time_of_day()

        if old_tod != new_tod:
            events.append(f"Наступил {new_tod.value}")

        # Вызываем колбэки
        for callback in self._hour_callbacks:
            result = callback(self.hour)
            if result:
                events.extend(result if isinstance(result, list) else [result])

        return events

    def _on_day_change(self) -> List[str]:
        """Вызывается при смене дня"""
        events = [f"Наступил день {self.day}"]

        # Случайно меняем погоду
        self._update_weather()
        events.append(f"Погода: {self.weather.value}")

        # Вызываем колбэки
        for callback in self._day_callbacks:
            result = callback(self.day)
            if result:
                events.extend(result if isinstance(result, list) else [result])

        return events

    def _on_month_change(self) -> List[str]:
        """Вызывается при смене месяца"""
        events = [f"Наступил {self.month}-й месяц, {self.get_season().value}"]
        return events

    def _update_weather(self) -> None:
        """Обновляет погоду на основе сезона"""
        import random

        season = self.get_season()

        if season == Season.SUMMER:
            weights = [0.5, 0.2, 0.2, 0.05, 0, 0.05]
        elif season == Season.WINTER:
            weights = [0.2, 0.3, 0.1, 0.05, 0.3, 0.05]
        elif season == Season.SPRING:
            weights = [0.3, 0.3, 0.25, 0.1, 0.0, 0.05]
        else:  # Autumn
            weights = [0.2, 0.35, 0.3, 0.05, 0.0, 0.1]

        weathers = list(Weather)
        self.weather = random.choices(weathers, weights=weights)[0]

    def _get_time_of_day(self, hour: int) -> TimeOfDay:
        """Определяет время суток по часу"""
        if 5 <= hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 14:
            return TimeOfDay.NOON
        elif 14 <= hour < 18:
            return TimeOfDay.AFTERNOON
        elif 18 <= hour < 21:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT

    def get_time_of_day(self) -> TimeOfDay:
        """Возвращает текущее время суток"""
        return self._get_time_of_day(self.hour)

    def get_season(self) -> Season:
        """Возвращает текущий сезон"""
        if self.month in [3, 4, 5]:
            return Season.SPRING
        elif self.month in [6, 7, 8]:
            return Season.SUMMER
        elif self.month in [9, 10, 11]:
            return Season.AUTUMN
        else:
            return Season.WINTER

    def is_daytime(self) -> bool:
        """Проверяет, сейчас день"""
        return 6 <= self.hour < 20

    def is_nighttime(self) -> bool:
        """Проверяет, сейчас ночь"""
        return not self.is_daytime()

    def is_work_hours(self) -> bool:
        """Проверяет, сейчас рабочее время"""
        return 8 <= self.hour < 18

    def get_formatted_time(self) -> str:
        """Возвращает отформатированное время"""
        return f"{self.hour:02d}:{self.minute:02d}"

    def get_formatted_date(self) -> str:
        """Возвращает отформатированную дату"""
        return f"День {self.day}, месяц {self.month}, год {self.year}"

    def get_full_datetime(self) -> str:
        """Возвращает полную дату и время"""
        tod = self.get_time_of_day()
        season = self.get_season()
        return (
            f"{self.get_formatted_time()}, {tod.value}\n"
            f"{self.get_formatted_date()}, {season.value}\n"
            f"Погода: {self.weather.value}"
        )

    def on_hour(self, callback: Callable) -> None:
        """Регистрирует колбэк на смену часа"""
        self._hour_callbacks.append(callback)

    def on_day(self, callback: Callable) -> None:
        """Регистрирует колбэк на смену дня"""
        self._day_callbacks.append(callback)

    def get_total_hours(self) -> int:
        """Возвращает общее количество прошедших часов"""
        return (
            (self.year - 1) * 12 * 30 * 24 +
            (self.month - 1) * 30 * 24 +
            (self.day - 1) * 24 +
            self.hour
        )
