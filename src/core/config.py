"""
Конфигурация симуляции - настраиваемые параметры.
"""
from dataclasses import dataclass, field
from typing import Dict, Any
from enum import Enum


class SimulationSpeed(Enum):
    """Скорость симуляции"""
    PAUSED = 0
    SLOW = 1       # 1 день = 10 сек реального времени
    NORMAL = 2     # 1 день = 5 сек
    FAST = 3       # 1 день = 1 сек
    VERY_FAST = 4  # 1 день = 0.1 сек


class EventDetailLevel(Enum):
    """Уровень детализации событий"""
    MINIMAL = 1      # Только переломные моменты
    IMPORTANT = 2    # Важные события
    DETAILED = 3     # Все действия


@dataclass
class Config:
    """
    Конфигурация симуляции.
    Все параметры настраиваемы.
    """

    # === Мир ===
    world_name: str = "Первобытная община"
    map_width: int = 50          # Ширина карты в клетках
    map_height: int = 50         # Высота карты

    # === Время ===
    simulation_speed: SimulationSpeed = SimulationSpeed.NORMAL
    hours_per_day: int = 24
    days_per_month: int = 30
    months_per_year: int = 12
    days_per_season: int = 90    # 3 месяца

    # === Начальная популяция ===
    initial_population: int = 12
    initial_families: int = 3    # Несколько семей
    starting_age_min: int = 16
    starting_age_max: int = 45

    # === Демография ===
    max_age: int = 70                    # Максимальный возраст
    fertility_age_min: int = 16          # Минимальный возраст для детей
    fertility_age_max_female: int = 45   # Максимальный для женщин
    fertility_age_max_male: int = 60     # Максимальный для мужчин
    child_mortality_base: float = 0.15   # Базовая детская смертность

    # === Ресурсы ===
    resource_regeneration_rate: float = 0.1   # Скорость восстановления
    resource_depletion_rate: float = 0.05     # Скорость истощения

    # === Климат ===
    enable_seasons: bool = True
    enable_weather_events: bool = True        # Катаклизмы
    enable_climate_change: bool = True        # Долгосрочные изменения
    drought_probability: float = 0.05         # Вероятность засухи в год
    plague_probability: float = 0.02          # Вероятность мора

    # === Экономика ===
    primitive_tool_efficiency: float = 1.0    # Эффективность простых орудий
    technology_discovery_rate: float = 0.01   # Шанс открытия в день работы
    knowledge_transfer_rate: float = 0.1      # Скорость обучения

    # === Социум ===
    enable_property: bool = True              # Возникновение собственности
    enable_classes: bool = True               # Возникновение классов
    enable_conflicts: bool = True             # Конфликты и бунты
    rebellion_threshold: float = 0.7          # Порог недовольства для бунта

    # === Культура ===
    enable_beliefs: bool = True               # Верования
    enable_traditions: bool = True            # Традиции
    belief_influence_on_behavior: float = 0.3 # Влияние верований на поведение

    # === Отображение ===
    event_detail_level: EventDetailLevel = EventDetailLevel.DETAILED
    show_map: bool = True
    show_social_structure: bool = True
    show_relationships: bool = True

    # === Производные настройки ===
    def days_per_year(self) -> int:
        return self.days_per_month * self.months_per_year

    def get_season(self, day_of_year: int) -> str:
        """Возвращает сезон по дню года"""
        if day_of_year < self.days_per_season:
            return "весна"
        elif day_of_year < self.days_per_season * 2:
            return "лето"
        elif day_of_year < self.days_per_season * 3:
            return "осень"
        else:
            return "зима"

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            k: v.value if isinstance(v, Enum) else v
            for k, v in self.__dict__.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Десериализация из словаря"""
        config = cls()
        for k, v in data.items():
            if hasattr(config, k):
                setattr(config, k, v)
        return config


# Пресеты конфигурации
PRESET_REALISTIC = Config(
    simulation_speed=SimulationSpeed.NORMAL,
    technology_discovery_rate=0.001,  # Медленное развитие
    child_mortality_base=0.25,        # Высокая детская смертность
    max_age=50,                       # Короткая жизнь
)

PRESET_ACCELERATED = Config(
    simulation_speed=SimulationSpeed.FAST,
    technology_discovery_rate=0.05,   # Быстрое развитие
    child_mortality_base=0.1,
    max_age=70,
)

PRESET_SANDBOX = Config(
    simulation_speed=SimulationSpeed.VERY_FAST,
    enable_weather_events=False,
    enable_climate_change=False,
    child_mortality_base=0.05,
)
