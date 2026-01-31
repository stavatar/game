"""
Система климата - сезоны, погода, катаклизмы.

Климат влияет на:
- Урожайность
- Доступность ресурсов
- Здоровье NPC
- Долгосрочное развитие
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum, auto
import random
import math


class Season(Enum):
    """Времена года"""
    SPRING = "весна"
    SUMMER = "лето"
    AUTUMN = "осень"
    WINTER = "зима"


class WeatherType(Enum):
    """Типы погоды"""
    CLEAR = "ясно"
    CLOUDY = "облачно"
    RAIN = "дождь"
    HEAVY_RAIN = "ливень"
    STORM = "гроза"
    SNOW = "снег"
    BLIZZARD = "метель"
    FOG = "туман"
    HEAT = "жара"
    FROST = "мороз"


class DisasterType(Enum):
    """Типы катаклизмов"""
    DROUGHT = "засуха"
    FLOOD = "наводнение"
    PLAGUE = "мор"
    FAMINE = "голод"
    FIRE = "пожар"
    HARSH_WINTER = "суровая зима"
    LOCUST = "нашествие саранчи"


@dataclass
class WeatherConditions:
    """Текущие погодные условия"""
    weather_type: WeatherType = WeatherType.CLEAR
    temperature: float = 15.0          # Градусы
    humidity: float = 0.5              # 0-1
    wind_strength: float = 0.2         # 0-1

    # Модификаторы для геймплея
    farming_modifier: float = 1.0       # Влияние на земледелие
    hunting_modifier: float = 1.0       # Влияние на охоту
    gathering_modifier: float = 1.0     # Влияние на собирательство
    travel_modifier: float = 1.0        # Влияние на перемещение
    health_modifier: float = 1.0        # Влияние на здоровье

    def describe(self) -> str:
        """Описание погоды"""
        temp_desc = "холодно" if self.temperature < 5 else \
                    "прохладно" if self.temperature < 15 else \
                    "тепло" if self.temperature < 25 else "жарко"
        return f"{self.weather_type.value}, {temp_desc} ({self.temperature:.0f}°)"


@dataclass
class Disaster:
    """Катаклизм"""
    disaster_type: DisasterType
    severity: float              # 0-1, насколько серьёзно
    duration_days: int           # Длительность в днях
    days_remaining: int          # Осталось дней
    affected_area: List[Tuple[int, int]] = field(default_factory=list)

    # Последствия
    casualties: int = 0          # Жертвы
    resources_lost: Dict[str, float] = field(default_factory=dict)

    def is_active(self) -> bool:
        return self.days_remaining > 0

    def describe(self) -> str:
        severity_desc = "слабый" if self.severity < 0.3 else \
                        "умеренный" if self.severity < 0.6 else "сильный"
        return f"{severity_desc} {self.disaster_type.value} (осталось {self.days_remaining} дней)"


class ClimateSystem:
    """
    Система управления климатом.

    Моделирует:
    - Смену сезонов
    - Ежедневную погоду
    - Катаклизмы
    - Долгосрочные климатические изменения
    """

    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 999999)
        random.seed(self.seed)

        # Текущее состояние
        self.current_season: Season = Season.SPRING
        self.current_weather: WeatherConditions = WeatherConditions()
        self.active_disasters: List[Disaster] = []

        # Долгосрочные тренды
        self.global_temperature_offset: float = 0.0  # Изменение климата
        self.drought_years: int = 0                   # Лет засухи подряд
        self.wet_years: int = 0                       # Лет с повышенными осадками

        # История
        self.disaster_history: List[Disaster] = []

        # Базовые температуры по сезонам
        self._season_temps = {
            Season.SPRING: (5, 18),
            Season.SUMMER: (15, 30),
            Season.AUTUMN: (5, 15),
            Season.WINTER: (-15, 5),
        }

    def update(self, day: int, year: int) -> List[str]:
        """
        Обновляет климат на новый день.
        Возвращает список событий.
        """
        events = []

        # Определяем сезон
        old_season = self.current_season
        self.current_season = self._get_season(day)

        if self.current_season != old_season:
            events.append(f"Наступила {self.current_season.value}")

        # Обновляем погоду
        self._update_weather()

        # Обновляем активные катаклизмы
        for disaster in self.active_disasters[:]:
            disaster.days_remaining -= 1
            if not disaster.is_active():
                self.active_disasters.remove(disaster)
                self.disaster_history.append(disaster)
                events.append(f"{disaster.disaster_type.value.capitalize()} закончился")

        # Проверяем новые катаклизмы
        new_disaster = self._check_for_disaster(day, year)
        if new_disaster:
            self.active_disasters.append(new_disaster)
            events.append(f"Началось бедствие: {new_disaster.describe()}")

        # Долгосрочные изменения (раз в год)
        if day == 1:
            self._update_long_term_trends(year)

        return events

    def _get_season(self, day_of_year: int) -> Season:
        """Определяет сезон по дню года"""
        # 360 дней в году, 90 на сезон
        if day_of_year < 90:
            return Season.SPRING
        elif day_of_year < 180:
            return Season.SUMMER
        elif day_of_year < 270:
            return Season.AUTUMN
        else:
            return Season.WINTER

    def _update_weather(self) -> None:
        """Обновляет погодные условия"""
        min_temp, max_temp = self._season_temps[self.current_season]

        # Базовая температура с вариацией
        base_temp = (min_temp + max_temp) / 2
        variation = (max_temp - min_temp) / 2
        self.current_weather.temperature = base_temp + random.uniform(-variation, variation)

        # Применяем глобальное изменение климата
        self.current_weather.temperature += self.global_temperature_offset

        # Определяем тип погоды
        self.current_weather.weather_type = self._generate_weather_type()

        # Вычисляем модификаторы
        self._calculate_modifiers()

    def _generate_weather_type(self) -> WeatherType:
        """Генерирует тип погоды"""
        temp = self.current_weather.temperature

        # Вероятности зависят от сезона и температуры
        if self.current_season == Season.WINTER:
            if temp < 0:
                weights = {
                    WeatherType.CLEAR: 0.3,
                    WeatherType.CLOUDY: 0.2,
                    WeatherType.SNOW: 0.3,
                    WeatherType.BLIZZARD: 0.1,
                    WeatherType.FROST: 0.1,
                }
            else:
                weights = {
                    WeatherType.CLEAR: 0.3,
                    WeatherType.CLOUDY: 0.4,
                    WeatherType.RAIN: 0.2,
                    WeatherType.FOG: 0.1,
                }
        elif self.current_season == Season.SUMMER:
            if temp > 28:
                weights = {
                    WeatherType.CLEAR: 0.4,
                    WeatherType.HEAT: 0.3,
                    WeatherType.STORM: 0.2,
                    WeatherType.CLOUDY: 0.1,
                }
            else:
                weights = {
                    WeatherType.CLEAR: 0.5,
                    WeatherType.CLOUDY: 0.2,
                    WeatherType.RAIN: 0.2,
                    WeatherType.STORM: 0.1,
                }
        else:  # Весна и осень
            weights = {
                WeatherType.CLEAR: 0.3,
                WeatherType.CLOUDY: 0.3,
                WeatherType.RAIN: 0.25,
                WeatherType.FOG: 0.1,
                WeatherType.HEAVY_RAIN: 0.05,
            }

        # Взвешенный выбор
        types = list(weights.keys())
        probs = list(weights.values())
        return random.choices(types, probs)[0]

    def _calculate_modifiers(self) -> None:
        """Вычисляет модификаторы от погоды"""
        weather = self.current_weather
        w_type = weather.weather_type

        # Сброс к базовым
        weather.farming_modifier = 1.0
        weather.hunting_modifier = 1.0
        weather.gathering_modifier = 1.0
        weather.travel_modifier = 1.0
        weather.health_modifier = 1.0

        # Модификаторы по типу погоды
        modifiers = {
            WeatherType.CLEAR: {},
            WeatherType.CLOUDY: {"farming": 0.9},
            WeatherType.RAIN: {"farming": 1.2, "hunting": 0.7, "travel": 0.8},
            WeatherType.HEAVY_RAIN: {"farming": 0.8, "hunting": 0.4, "travel": 0.5, "health": 0.9},
            WeatherType.STORM: {"farming": 0.5, "hunting": 0.2, "travel": 0.3, "health": 0.8},
            WeatherType.SNOW: {"farming": 0.1, "hunting": 0.6, "travel": 0.6, "health": 0.9},
            WeatherType.BLIZZARD: {"farming": 0.0, "hunting": 0.1, "travel": 0.2, "health": 0.7},
            WeatherType.FOG: {"hunting": 0.5, "travel": 0.7},
            WeatherType.HEAT: {"farming": 0.7, "travel": 0.8, "health": 0.85},
            WeatherType.FROST: {"farming": 0.0, "gathering": 0.3, "health": 0.8},
        }

        mods = modifiers.get(w_type, {})
        if "farming" in mods:
            weather.farming_modifier = mods["farming"]
        if "hunting" in mods:
            weather.hunting_modifier = mods["hunting"]
        if "gathering" in mods:
            weather.gathering_modifier = mods["gathering"]
        if "travel" in mods:
            weather.travel_modifier = mods["travel"]
        if "health" in mods:
            weather.health_modifier = mods["health"]

        # Модификаторы от активных катаклизмов
        for disaster in self.active_disasters:
            if disaster.disaster_type == DisasterType.DROUGHT:
                weather.farming_modifier *= 0.3
            elif disaster.disaster_type == DisasterType.FLOOD:
                weather.farming_modifier *= 0.2
                weather.travel_modifier *= 0.4
            elif disaster.disaster_type == DisasterType.PLAGUE:
                weather.health_modifier *= 0.5
            elif disaster.disaster_type == DisasterType.FAMINE:
                weather.health_modifier *= 0.7

    def _check_for_disaster(self, day: int, year: int) -> Optional[Disaster]:
        """Проверяет, не началось ли бедствие"""
        # Не более одного активного бедствия одного типа
        active_types = {d.disaster_type for d in self.active_disasters}

        # Вероятности бедствий
        disaster_chances = {
            DisasterType.DROUGHT: 0.001 if self.current_season == Season.SUMMER else 0.0001,
            DisasterType.FLOOD: 0.0005 if self.current_season in [Season.SPRING, Season.AUTUMN] else 0.0001,
            DisasterType.PLAGUE: 0.0002,
            DisasterType.FIRE: 0.0003 if self.current_season == Season.SUMMER else 0.0001,
            DisasterType.HARSH_WINTER: 0.002 if self.current_season == Season.WINTER else 0,
            DisasterType.LOCUST: 0.0002 if self.current_season == Season.SUMMER else 0,
        }

        for disaster_type, chance in disaster_chances.items():
            if disaster_type in active_types:
                continue

            # Увеличиваем шанс после нескольких лет без бедствий
            adjusted_chance = chance * (1 + year * 0.01)

            if random.random() < adjusted_chance:
                severity = random.uniform(0.3, 1.0)
                duration = int(10 + severity * 50)

                return Disaster(
                    disaster_type=disaster_type,
                    severity=severity,
                    duration_days=duration,
                    days_remaining=duration,
                )

        return None

    def _update_long_term_trends(self, year: int) -> None:
        """Обновляет долгосрочные климатические тренды"""
        # Небольшие случайные изменения климата
        self.global_temperature_offset += random.uniform(-0.1, 0.15)

        # Ограничиваем изменения
        self.global_temperature_offset = max(-3, min(5, self.global_temperature_offset))

    def get_season_productivity(self) -> Dict[str, float]:
        """Возвращает продуктивность различных занятий в текущий сезон"""
        season_mods = {
            Season.SPRING: {"farming": 0.8, "hunting": 1.0, "gathering": 0.7, "fishing": 1.0},
            Season.SUMMER: {"farming": 1.0, "hunting": 0.9, "gathering": 1.0, "fishing": 0.9},
            Season.AUTUMN: {"farming": 1.2, "hunting": 1.1, "gathering": 1.2, "fishing": 0.8},
            Season.WINTER: {"farming": 0.0, "hunting": 0.7, "gathering": 0.2, "fishing": 0.4},
        }

        base = season_mods[self.current_season].copy()

        # Применяем погодные модификаторы
        base["farming"] *= self.current_weather.farming_modifier
        base["hunting"] *= self.current_weather.hunting_modifier
        base["gathering"] *= self.current_weather.gathering_modifier

        return base

    def get_status_report(self) -> str:
        """Возвращает отчёт о климате"""
        report = [
            f"Сезон: {self.current_season.value}",
            f"Погода: {self.current_weather.describe()}",
        ]

        if self.active_disasters:
            report.append("Активные бедствия:")
            for d in self.active_disasters:
                report.append(f"  - {d.describe()}")

        if abs(self.global_temperature_offset) > 1:
            trend = "потепление" if self.global_temperature_offset > 0 else "похолодание"
            report.append(f"Климатический тренд: {trend}")

        return "\n".join(report)
