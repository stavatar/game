"""
Система событий - центр коммуникации между системами.
Реализует паттерн Observer/Pub-Sub.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional
from enum import Enum, auto
from datetime import datetime
import uuid


class EventType(Enum):
    """Типы событий в симуляции"""

    # === Жизненный цикл ===
    NPC_BORN = auto()
    NPC_DIED = auto()
    NPC_AGED = auto()

    # === Семья ===
    MARRIAGE = auto()
    DIVORCE = auto()
    CHILD_BORN = auto()

    # === Экономика ===
    RESOURCE_GATHERED = auto()
    RESOURCE_DEPLETED = auto()
    RESOURCE_REGENERATED = auto()
    ITEM_CRAFTED = auto()
    TRADE_COMPLETED = auto()

    # === Собственность ===
    PROPERTY_CLAIMED = auto()
    PROPERTY_TRANSFERRED = auto()
    PROPERTY_LOST = auto()

    # === Технологии ===
    TECHNOLOGY_DISCOVERED = auto()
    KNOWLEDGE_TRANSFERRED = auto()
    TOOL_CREATED = auto()

    # === Социум ===
    CLASS_EMERGED = auto()
    RELATIONSHIP_CHANGED = auto()
    CONFLICT_STARTED = auto()
    CONFLICT_ESCALATED = auto()
    CONFLICT_RESOLVED = auto()
    REBELLION = auto()
    CONSCIOUSNESS_SPREAD = auto()
    INTELLECTUAL_EMERGED = auto()

    # === Культура ===
    BELIEF_FORMED = auto()
    TRADITION_CREATED = auto()
    NORM_ESTABLISHED = auto()
    RITUAL_PERFORMED = auto()

    # === Климат ===
    SEASON_CHANGED = auto()
    WEATHER_EVENT = auto()
    DROUGHT = auto()
    PLAGUE = auto()
    FAMINE = auto()

    # === Мир ===
    DAY_PASSED = auto()
    MONTH_PASSED = auto()
    YEAR_PASSED = auto()
    GENERATION_PASSED = auto()

    # === Общие ===
    CUSTOM = auto()


class EventImportance(Enum):
    """Важность события"""
    TRIVIAL = 1      # Рутинные действия
    MINOR = 2        # Мелкие события
    NOTABLE = 3      # Заметные события
    IMPORTANT = 4    # Важные события
    MAJOR = 5        # Крупные события
    HISTORIC = 6     # Исторические события


@dataclass
class Event:
    """
    Событие в симуляции.

    Каждое событие содержит:
    - Тип и важность
    - Время и место
    - Участники
    - Данные события
    - Описание для лога
    """

    event_type: EventType
    importance: EventImportance = EventImportance.MINOR

    # Время события
    year: int = 0
    month: int = 0
    day: int = 0
    hour: int = 0

    # Место события
    location_id: Optional[str] = None
    x: float = 0.0
    y: float = 0.0

    # Участники
    actor_id: Optional[str] = None       # Кто совершил
    target_id: Optional[str] = None      # На кого направлено
    witness_ids: List[str] = field(default_factory=list)  # Свидетели

    # Данные события
    data: Dict[str, Any] = field(default_factory=dict)

    # Описание
    description: str = ""
    description_template: str = ""  # Шаблон с плейсхолдерами

    # Метаданные
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

    # Для цепочки причин-следствий
    caused_by: Optional[str] = None      # ID события-причины
    causes: List[str] = field(default_factory=list)  # ID вызванных событий

    def format_time(self) -> str:
        """Форматирует время события"""
        return f"Год {self.year}, месяц {self.month}, день {self.day}"

    def format_description(self, npc_names: Dict[str, str] = None) -> str:
        """Форматирует описание с подстановкой имён"""
        if self.description:
            return self.description

        if not self.description_template:
            return f"{self.event_type.name}"

        desc = self.description_template
        if npc_names:
            if self.actor_id and self.actor_id in npc_names:
                desc = desc.replace("{actor}", npc_names[self.actor_id])
            if self.target_id and self.target_id in npc_names:
                desc = desc.replace("{target}", npc_names[self.target_id])

        for key, value in self.data.items():
            desc = desc.replace(f"{{{key}}}", str(value))

        return desc

    def is_historic(self) -> bool:
        """Проверяет, является ли событие историческим"""
        return self.importance.value >= EventImportance.MAJOR.value


class EventBus:
    """
    Шина событий - централизованная система для публикации и подписки.

    Позволяет системам:
    - Публиковать события
    - Подписываться на типы событий
    - Фильтровать события по важности
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._global_subscribers: List[Callable[[Event], None]] = []
        self._event_history: List[Event] = []
        self._max_history: int = 10000

    def subscribe(self,
                  event_type: EventType,
                  callback: Callable[[Event], None]) -> None:
        """Подписывается на определённый тип событий"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[Event], None]) -> None:
        """Подписывается на все события"""
        self._global_subscribers.append(callback)

    def unsubscribe(self,
                    event_type: EventType,
                    callback: Callable[[Event], None]) -> None:
        """Отписывается от типа событий"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event) -> None:
        """Публикует событие"""
        # Сохраняем в историю
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            # Оставляем только важные старые события
            important = [e for e in self._event_history[:self._max_history // 2]
                         if e.is_historic()]
            self._event_history = important + self._event_history[self._max_history // 2:]

        # Уведомляем подписчиков конкретного типа
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                callback(event)

        # Уведомляем глобальных подписчиков
        for callback in self._global_subscribers:
            callback(event)

    def get_history(self,
                    event_type: EventType = None,
                    min_importance: EventImportance = None,
                    actor_id: str = None,
                    limit: int = 100) -> List[Event]:
        """Получает историю событий с фильтрацией"""
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if min_importance:
            events = [e for e in events
                      if e.importance.value >= min_importance.value]

        if actor_id:
            events = [e for e in events if e.actor_id == actor_id]

        return events[-limit:]

    def get_historic_events(self, limit: int = 50) -> List[Event]:
        """Получает только исторические события"""
        return [e for e in self._event_history if e.is_historic()][-limit:]

    def clear_history(self) -> None:
        """Очищает историю (кроме исторических)"""
        self._event_history = [e for e in self._event_history if e.is_historic()]


# Глобальная шина событий
event_bus = EventBus()


# === Вспомогательные функции для создания событий ===

def create_birth_event(npc_id: str, mother_id: str, father_id: str,
                       year: int, location_id: str = None) -> Event:
    """Создаёт событие рождения"""
    return Event(
        event_type=EventType.NPC_BORN,
        importance=EventImportance.NOTABLE,
        year=year,
        actor_id=npc_id,
        location_id=location_id,
        data={"mother_id": mother_id, "father_id": father_id},
        description_template="{actor} родился у {mother} и {father}"
    )


def create_death_event(npc_id: str, cause: str, age: int,
                       year: int, location_id: str = None) -> Event:
    """Создаёт событие смерти"""
    importance = EventImportance.NOTABLE
    if age < 5:
        importance = EventImportance.MINOR
    elif age > 60:
        importance = EventImportance.NOTABLE

    return Event(
        event_type=EventType.NPC_DIED,
        importance=importance,
        year=year,
        actor_id=npc_id,
        location_id=location_id,
        data={"cause": cause, "age": age},
        description_template="{actor} умер в возрасте {age} лет ({cause})"
    )


def create_technology_event(discoverer_id: str, tech_name: str,
                            year: int, location_id: str = None) -> Event:
    """Создаёт событие открытия технологии"""
    return Event(
        event_type=EventType.TECHNOLOGY_DISCOVERED,
        importance=EventImportance.MAJOR,
        year=year,
        actor_id=discoverer_id,
        location_id=location_id,
        data={"technology": tech_name},
        description_template="{actor} открыл {technology}!"
    )


def create_class_emergence_event(class_name: str, members: List[str],
                                 year: int) -> Event:
    """Создаёт событие возникновения класса"""
    return Event(
        event_type=EventType.CLASS_EMERGED,
        importance=EventImportance.HISTORIC,
        year=year,
        data={"class_name": class_name, "member_count": len(members)},
        description=f"Возник новый социальный класс: {class_name} ({len(members)} чел.)"
    )


def create_conflict_started_event(
    conflict_id: str,
    conflict_type: str,
    oppressed_class: str,
    ruling_class: str,
    cause: str,
    year: int
) -> Event:
    """Создаёт событие начала классового конфликта"""
    return Event(
        event_type=EventType.CONFLICT_STARTED,
        importance=EventImportance.MAJOR,
        year=year,
        data={
            "conflict_id": conflict_id,
            "conflict_type": conflict_type,
            "oppressed_class": oppressed_class,
            "ruling_class": ruling_class,
            "cause": cause
        },
        description=(
            f"Начался {conflict_type}: {oppressed_class} против {ruling_class}. "
            f"Причина: {cause}"
        )
    )


def create_conflict_escalated_event(
    conflict_id: str,
    new_stage: str,
    new_type: str,
    intensity: float,
    year: int
) -> Event:
    """Создаёт событие эскалации конфликта"""
    return Event(
        event_type=EventType.CONFLICT_ESCALATED,
        importance=EventImportance.IMPORTANT,
        year=year,
        data={
            "conflict_id": conflict_id,
            "new_stage": new_stage,
            "new_type": new_type,
            "intensity": intensity
        },
        description=f"Конфликт обострился: {new_type} (интенсивность: {intensity:.0%})"
    )


def create_conflict_resolved_event(
    conflict_id: str,
    outcome: str,
    consequences: List[str],
    year: int
) -> Event:
    """Создаёт событие разрешения конфликта"""
    importance = EventImportance.MAJOR
    if outcome in ["революция", "победа"]:
        importance = EventImportance.HISTORIC

    return Event(
        event_type=EventType.CONFLICT_RESOLVED,
        importance=importance,
        year=year,
        data={
            "conflict_id": conflict_id,
            "outcome": outcome,
            "consequences": consequences
        },
        description=f"Конфликт завершён: {outcome}. " + "; ".join(consequences[:3])
    )


def create_consciousness_spread_event(
    from_npc_id: str,
    to_npc_id: str,
    class_name: str,
    amount: float,
    year: int
) -> Event:
    """Создаёт событие распространения классового сознания"""
    return Event(
        event_type=EventType.CONSCIOUSNESS_SPREAD,
        importance=EventImportance.MINOR,
        year=year,
        actor_id=from_npc_id,
        target_id=to_npc_id,
        data={
            "class_name": class_name,
            "amount": amount
        },
        description_template="{actor} повлиял на классовое сознание {target}"
    )


def create_intellectual_emerged_event(
    npc_id: str,
    class_name: str,
    year: int
) -> Event:
    """Создаёт событие появления органического интеллектуала"""
    return Event(
        event_type=EventType.INTELLECTUAL_EMERGED,
        importance=EventImportance.NOTABLE,
        year=year,
        actor_id=npc_id,
        data={"class_name": class_name},
        description_template=(
            "{actor} стал органическим интеллектуалом класса {class_name}"
        )
    )


def create_rebellion_event(
    leader_ids: List[str],
    oppressed_class: str,
    participant_count: int,
    year: int
) -> Event:
    """Создаёт событие революции/восстания"""
    return Event(
        event_type=EventType.REBELLION,
        importance=EventImportance.HISTORIC,
        year=year,
        data={
            "leaders": leader_ids,
            "oppressed_class": oppressed_class,
            "participant_count": participant_count
        },
        description=(
            f"Революция! Класс {oppressed_class} восстал. "
            f"Участников: {participant_count}"
        )
    )
