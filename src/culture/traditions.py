"""
Система традиций - устойчивые практики общества.

Традиции:
- Закрепляют существующий порядок
- Передаются из поколения в поколение
- Возникают из повторяющихся успешных практик
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto


class TraditionType(Enum):
    """Типы традиций"""
    RITUAL = "ритуал"               # Обряды
    CUSTOM = "обычай"               # Повседневные практики
    CELEBRATION = "праздник"        # Праздники
    TABOO = "табу"                  # Запреты
    INITIATION = "инициация"        # Обряды перехода


@dataclass
class Tradition:
    """Традиция"""
    id: str
    name: str
    tradition_type: TraditionType
    description: str

    # Когда возникла
    year_emerged: int = 0
    origin_event: str = ""          # Событие, породившее традицию

    # Когда выполняется
    trigger: str = ""               # "season:spring", "age:16", "event:birth"

    # Эффекты
    social_cohesion_bonus: float = 0.1
    behavior_effects: Dict[str, float] = field(default_factory=dict)

    # Участники
    participants: Set[str] = field(default_factory=set)


class TraditionSystem:
    """Система управления традициями"""

    def __init__(self):
        self.traditions: Dict[str, Tradition] = {}
        self.scheduled_events: List[tuple] = []  # (day, tradition_id)

    def check_tradition_emergence(self,
                                   repeated_event: str,
                                   success_count: int,
                                   year: int) -> Optional[Tradition]:
        """
        Проверяет возникновение традиции из повторяющейся практики.

        Традиции возникают когда что-то делается регулярно и успешно.
        """
        if success_count < 3:
            return None

        tradition_id = f"tradition_{repeated_event}"
        if tradition_id in self.traditions:
            return None

        # Создаём традицию
        tradition = Tradition(
            id=tradition_id,
            name=f"обычай {repeated_event}",
            tradition_type=TraditionType.CUSTOM,
            description=f"Традиция, возникшая из практики: {repeated_event}",
            year_emerged=year,
            origin_event=repeated_event,
        )

        self.traditions[tradition_id] = tradition
        return tradition

    def add_seasonal_celebration(self, name: str, season: str,
                                 year: int, description: str = "") -> Tradition:
        """Добавляет сезонный праздник"""
        tradition = Tradition(
            id=f"celebration_{season}_{year}",
            name=name,
            tradition_type=TraditionType.CELEBRATION,
            description=description or f"Праздник в честь {season}",
            year_emerged=year,
            trigger=f"season:{season}",
            social_cohesion_bonus=0.2,
        )
        self.traditions[tradition.id] = tradition
        return tradition

    def get_traditions_for_trigger(self, trigger: str) -> List[Tradition]:
        """Возвращает традиции для указанного триггера"""
        return [
            t for t in self.traditions.values()
            if t.trigger == trigger or trigger in t.trigger
        ]

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику"""
        by_type = {}
        for t in self.traditions.values():
            type_name = t.tradition_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        return {
            "total": len(self.traditions),
            "by_type": by_type,
        }
