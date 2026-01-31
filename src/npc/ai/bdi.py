"""
BDI-архитектура для автономного поведения NPC.

BDI = Beliefs (Убеждения) + Desires (Желания) + Intentions (Намерения)

Цикл работы:
1. ВОСПРИЯТИЕ: Обновление убеждений на основе окружения
2. ОБДУМЫВАНИЕ: Выбор желаний → формирование намерений
3. ДЕЙСТВИЕ: Выполнение намерений
4. ОБРАТНАЯ СВЯЗЬ: Результат влияет на убеждения

Вдохновлено:
- Классической BDI-архитектурой (Bratman, 1987)
- Игрой Majesty (классовое поведение)
- Пирамидой Маслоу (иерархия потребностей)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum, auto
import random


class BeliefCategory(Enum):
    """Категории убеждений"""
    SELF = "о себе"                  # Здоровье, голод, усталость
    WORLD = "о мире"                 # Погода, время, ресурсы
    SOCIAL = "социальные"            # Об отношениях с другими
    ECONOMIC = "экономические"       # О собственности, богатстве
    LOCATION = "о местах"            # Где что находится
    DANGER = "об опасностях"         # Угрозы
    OPPORTUNITY = "о возможностях"   # Шансы


@dataclass
class Belief:
    """
    Убеждение - единица знания NPC о мире.

    Убеждения могут быть:
    - Истинными или ложными
    - Устаревшими
    - С разной степенью уверенности
    """
    id: str
    category: BeliefCategory
    subject: str                     # О чём убеждение
    content: Any                     # Содержание (значение, объект)
    confidence: float = 1.0          # Уверенность (0-1)
    timestamp: int = 0               # Когда получено (день симуляции)

    # Источник
    source: str = "наблюдение"       # Откуда знание

    def is_stale(self, current_day: int, max_age: int = 30) -> bool:
        """Проверяет, устарело ли убеждение"""
        return (current_day - self.timestamp) > max_age

    def decay_confidence(self, amount: float = 0.1) -> None:
        """Уменьшает уверенность со временем"""
        self.confidence = max(0, self.confidence - amount)


class DesireType(Enum):
    """Типы желаний (по пирамиде Маслоу)"""
    # Физиологические (базовые)
    SURVIVE = ("выжить", 1.0)
    EAT = ("поесть", 0.9)
    DRINK = ("попить", 0.9)
    SLEEP = ("поспать", 0.85)
    WARMTH = ("согреться", 0.8)

    # Безопасность
    SAFETY = ("быть в безопасности", 0.7)
    SHELTER = ("иметь укрытие", 0.65)
    HEALTH = ("быть здоровым", 0.7)

    # Социальные
    BELONG = ("принадлежать группе", 0.5)
    FRIENDSHIP = ("иметь друзей", 0.45)
    FAMILY = ("иметь семью", 0.5)
    INTIMACY = ("близость", 0.4)

    # Уважение
    RESPECT = ("уважение других", 0.4)
    STATUS = ("статус в обществе", 0.35)
    WEALTH = ("богатство", 0.3)
    POWER = ("власть", 0.25)

    # Самореализация
    MASTERY = ("мастерство", 0.3)
    KNOWLEDGE = ("знания", 0.25)
    CREATIVITY = ("творчество", 0.2)
    PURPOSE = ("цель в жизни", 0.2)

    def __init__(self, russian_name: str, base_priority: float):
        self.russian_name = russian_name
        self.base_priority = base_priority


@dataclass
class Desire:
    """
    Желание - цель или потребность NPC.

    Желания имеют:
    - Тип (из иерархии Маслоу)
    - Интенсивность (насколько сильно хочет)
    - Условия удовлетворения
    """
    desire_type: DesireType
    intensity: float = 0.5           # 0-1, насколько сильно
    target: Optional[str] = None     # Конкретная цель (ID объекта/NPC)

    # Условия
    conditions_met: bool = False     # Выполнены ли условия
    blocked_by: List[str] = field(default_factory=list)  # Что мешает

    def get_priority(self) -> float:
        """Вычисляет приоритет желания"""
        return self.desire_type.base_priority * self.intensity

    def is_urgent(self) -> bool:
        """Проверяет, срочное ли желание"""
        return self.intensity > 0.8 and self.desire_type.base_priority > 0.7


class ActionType(Enum):
    """Типы действий"""
    # Базовые
    IDLE = "бездействовать"
    MOVE = "перемещаться"
    REST = "отдыхать"
    SLEEP = "спать"

    # Добыча ресурсов
    GATHER = "собирать"
    HUNT = "охотиться"
    FISH = "рыбачить"
    FARM = "обрабатывать землю"
    HARVEST = "собирать урожай"

    # Производство
    CRAFT = "мастерить"
    BUILD = "строить"
    COOK = "готовить"

    # Социальное
    TALK = "разговаривать"
    TRADE = "торговать"
    HELP = "помогать"
    TEACH = "обучать"
    LEARN = "учиться"

    # Потребление
    EAT = "есть"
    DRINK = "пить"

    # Работа
    WORK = "работать"
    WORK_FOR_OTHER = "работать на другого"


@dataclass
class Action:
    """
    Действие - конкретный шаг для выполнения намерения.
    """
    action_type: ActionType
    target_id: Optional[str] = None  # На что направлено
    location_id: Optional[str] = None  # Где выполнять
    duration: float = 1.0            # Часов на выполнение
    priority: float = 0.5            # Приоритет

    # Результат
    success_chance: float = 0.8      # Вероятность успеха
    energy_cost: float = 10.0        # Стоимость энергии
    expected_reward: Dict[str, float] = field(default_factory=dict)

    def describe(self) -> str:
        """Описание действия"""
        desc = self.action_type.value
        if self.target_id:
            desc += f" (цель: {self.target_id})"
        return desc


@dataclass
class Intention:
    """
    Намерение - выбранный план действий.

    Намерение связывает желание с конкретными действиями.
    """
    id: str
    source_desire: DesireType        # Какое желание удовлетворяет
    actions: List[Action] = field(default_factory=list)  # Последовательность действий
    current_action_index: int = 0    # Текущее действие
    priority: float = 0.5

    # Состояние
    is_active: bool = True
    is_complete: bool = False
    is_failed: bool = False

    # Прогресс
    progress: float = 0.0            # 0-1
    started_at: int = 0              # День начала

    def get_current_action(self) -> Optional[Action]:
        """Возвращает текущее действие"""
        if self.current_action_index < len(self.actions):
            return self.actions[self.current_action_index]
        return None

    def advance(self) -> bool:
        """Переходит к следующему действию. Возвращает True если есть ещё."""
        self.current_action_index += 1
        if self.current_action_index >= len(self.actions):
            self.is_complete = True
            return False
        return True


class BDIAgent:
    """
    BDI-агент - мозг NPC.

    Управляет:
    - Убеждениями о мире
    - Желаниями и целями
    - Планированием и выполнением намерений
    """

    def __init__(self, owner_id: str):
        self.owner_id = owner_id

        # BDI компоненты
        self.beliefs: Dict[str, Belief] = {}
        self.desires: Dict[DesireType, Desire] = {}
        self.intentions: Dict[str, Intention] = {}

        # Активное намерение
        self.current_intention: Optional[str] = None

        # Счётчик для ID
        self._intention_counter = 0

        # Черты характера (влияют на приоритеты)
        self.personality_modifiers: Dict[str, float] = {}

        # Инициализация базовых желаний
        self._init_basic_desires()

    def _init_basic_desires(self) -> None:
        """Инициализирует базовые желания"""
        for desire_type in DesireType:
            self.desires[desire_type] = Desire(
                desire_type=desire_type,
                intensity=0.3  # Начальная интенсивность
            )

    # === УБЕЖДЕНИЯ ===

    def add_belief(self, category: BeliefCategory, subject: str,
                   content: Any, confidence: float = 1.0,
                   current_day: int = 0, source: str = "наблюдение") -> Belief:
        """Добавляет или обновляет убеждение"""
        belief_id = f"{category.name}_{subject}"

        belief = Belief(
            id=belief_id,
            category=category,
            subject=subject,
            content=content,
            confidence=confidence,
            timestamp=current_day,
            source=source,
        )

        self.beliefs[belief_id] = belief
        return belief

    def get_belief(self, category: BeliefCategory, subject: str) -> Optional[Belief]:
        """Получает убеждение"""
        belief_id = f"{category.name}_{subject}"
        return self.beliefs.get(belief_id)

    def get_beliefs_by_category(self, category: BeliefCategory) -> List[Belief]:
        """Получает все убеждения категории"""
        return [b for b in self.beliefs.values() if b.category == category]

    def update_beliefs_from_perception(self, perception_data: Dict[str, Any],
                                       current_day: int) -> None:
        """
        Обновляет убеждения на основе восприятия.

        perception_data может содержать:
        - self_state: состояние самого NPC
        - nearby_npcs: NPC поблизости
        - nearby_resources: ресурсы поблизости
        - weather: погода
        - threats: угрозы
        """
        # Обновляем убеждения о себе
        if "self_state" in perception_data:
            state = perception_data["self_state"]
            for key, value in state.items():
                self.add_belief(BeliefCategory.SELF, key, value,
                               current_day=current_day)

        # Обновляем убеждения о мире
        if "weather" in perception_data:
            self.add_belief(BeliefCategory.WORLD, "погода",
                           perception_data["weather"], current_day=current_day)

        if "time_of_day" in perception_data:
            self.add_belief(BeliefCategory.WORLD, "время_суток",
                           perception_data["time_of_day"], current_day=current_day)

        # Обновляем убеждения о ресурсах
        if "nearby_resources" in perception_data:
            for resource_id, info in perception_data["nearby_resources"].items():
                self.add_belief(BeliefCategory.LOCATION, f"ресурс_{resource_id}",
                               info, current_day=current_day)

        # Обновляем убеждения об угрозах
        if "threats" in perception_data:
            for threat in perception_data["threats"]:
                self.add_belief(BeliefCategory.DANGER, threat["id"],
                               threat, current_day=current_day)

    def decay_old_beliefs(self, current_day: int, max_age: int = 30) -> None:
        """Уменьшает уверенность в старых убеждениях"""
        for belief in self.beliefs.values():
            if belief.is_stale(current_day, max_age):
                belief.decay_confidence(0.1)

    # === ЖЕЛАНИЯ ===

    def update_desire_intensity(self, desire_type: DesireType,
                                intensity: float) -> None:
        """Обновляет интенсивность желания"""
        if desire_type in self.desires:
            self.desires[desire_type].intensity = max(0, min(1, intensity))

    def update_desires_from_needs(self, needs: Dict[str, float]) -> None:
        """
        Обновляет желания на основе потребностей.

        needs: словарь вида {"hunger": 30, "energy": 80, ...}
        Низкие значения = неудовлетворённая потребность
        """
        # Маппинг потребностей на желания
        need_to_desire = {
            "hunger": DesireType.EAT,
            "thirst": DesireType.DRINK,
            "energy": DesireType.SLEEP,
            "health": DesireType.HEALTH,
            "social": DesireType.BELONG,
            "safety": DesireType.SAFETY,
        }

        for need_name, value in needs.items():
            if need_name in need_to_desire:
                desire_type = need_to_desire[need_name]
                # Низкое значение потребности = высокая интенсивность желания
                intensity = 1.0 - (value / 100.0)
                self.update_desire_intensity(desire_type, intensity)

    def get_active_desires(self, min_intensity: float = 0.3) -> List[Desire]:
        """Возвращает активные желания отсортированные по приоритету"""
        active = [d for d in self.desires.values() if d.intensity >= min_intensity]
        active.sort(key=lambda d: d.get_priority(), reverse=True)
        return active

    def get_most_urgent_desire(self) -> Optional[Desire]:
        """Возвращает самое срочное желание"""
        urgent = [d for d in self.desires.values() if d.is_urgent()]
        if urgent:
            return max(urgent, key=lambda d: d.get_priority())

        active = self.get_active_desires()
        return active[0] if active else None

    # === НАМЕРЕНИЯ ===

    def create_intention(self, desire: Desire, actions: List[Action],
                        current_day: int) -> Intention:
        """Создаёт намерение для удовлетворения желания"""
        self._intention_counter += 1
        intention_id = f"int_{self.owner_id}_{self._intention_counter}"

        intention = Intention(
            id=intention_id,
            source_desire=desire.desire_type,
            actions=actions,
            priority=desire.get_priority(),
            started_at=current_day,
        )

        self.intentions[intention_id] = intention
        return intention

    def select_intention(self) -> Optional[Intention]:
        """Выбирает намерение для выполнения"""
        # Фильтруем активные незавершённые намерения
        active = [
            i for i in self.intentions.values()
            if i.is_active and not i.is_complete and not i.is_failed
        ]

        if not active:
            return None

        # Выбираем по приоритету
        return max(active, key=lambda i: i.priority)

    def abandon_intention(self, intention_id: str) -> None:
        """Отказывается от намерения"""
        if intention_id in self.intentions:
            self.intentions[intention_id].is_active = False

    # === ПЛАНИРОВАНИЕ ===

    def plan_for_desire(self, desire: Desire,
                        available_actions: List[ActionType],
                        world_state: Dict[str, Any]) -> List[Action]:
        """
        Создаёт план действий для удовлетворения желания.

        Это упрощённый планировщик. В идеале здесь был бы
        полноценный планировщик (STRIPS, HTN, или GOAP).
        """
        actions = []

        # Простое сопоставление желаний и действий
        desire_actions = {
            DesireType.EAT: [
                (ActionType.GATHER, 0.5),
                (ActionType.HUNT, 0.4),
                (ActionType.COOK, 0.3),
                (ActionType.EAT, 1.0),
            ],
            DesireType.DRINK: [
                (ActionType.MOVE, 0.3),  # К воде
                (ActionType.DRINK, 1.0),
            ],
            DesireType.SLEEP: [
                (ActionType.MOVE, 0.2),  # Домой
                (ActionType.SLEEP, 1.0),
            ],
            DesireType.SAFETY: [
                (ActionType.MOVE, 0.5),  # В безопасное место
                (ActionType.REST, 0.3),
            ],
            DesireType.BELONG: [
                (ActionType.MOVE, 0.3),
                (ActionType.TALK, 0.8),
            ],
            DesireType.WEALTH: [
                (ActionType.WORK, 0.6),
                (ActionType.TRADE, 0.5),
                (ActionType.GATHER, 0.4),
            ],
            DesireType.KNOWLEDGE: [
                (ActionType.LEARN, 0.8),
                (ActionType.TALK, 0.4),
            ],
            DesireType.MASTERY: [
                (ActionType.WORK, 0.7),
                (ActionType.CRAFT, 0.6),
            ],
        }

        # Получаем шаблон плана
        template = desire_actions.get(desire.desire_type, [(ActionType.IDLE, 0.1)])

        for action_type, base_priority in template:
            if action_type in available_actions:
                action = Action(
                    action_type=action_type,
                    priority=base_priority * desire.intensity,
                    target_id=desire.target,
                )
                actions.append(action)

        return actions

    # === ГЛАВНЫЙ ЦИКЛ ===

    def deliberate(self, current_day: int,
                   available_actions: List[ActionType],
                   world_state: Dict[str, Any]) -> Optional[Action]:
        """
        Главный цикл обдумывания.

        Возвращает следующее действие для выполнения.
        """
        # 1. Проверяем текущее намерение
        if self.current_intention:
            intention = self.intentions.get(self.current_intention)
            if intention and intention.is_active and not intention.is_complete:
                action = intention.get_current_action()
                if action:
                    return action

        # 2. Выбираем самое срочное желание
        urgent_desire = self.get_most_urgent_desire()
        if not urgent_desire:
            return Action(action_type=ActionType.IDLE)

        # 3. Создаём план
        actions = self.plan_for_desire(urgent_desire, available_actions, world_state)
        if not actions:
            return Action(action_type=ActionType.IDLE)

        # 4. Создаём намерение
        intention = self.create_intention(urgent_desire, actions, current_day)
        self.current_intention = intention.id

        # 5. Возвращаем первое действие
        return intention.get_current_action()

    def react_to_event(self, event_type: str, event_data: Dict[str, Any],
                      current_day: int) -> Optional[Action]:
        """
        Реакция на внезапное событие.

        Может прервать текущее намерение если событие важное.
        """
        # Опасность - немедленная реакция
        if event_type == "danger":
            # Прерываем текущее намерение
            if self.current_intention:
                self.abandon_intention(self.current_intention)

            # Добавляем убеждение об угрозе
            self.add_belief(BeliefCategory.DANGER, event_data.get("id", "unknown"),
                           event_data, current_day=current_day)

            # Срочное желание безопасности
            self.update_desire_intensity(DesireType.SAFETY, 1.0)

            return Action(
                action_type=ActionType.MOVE,
                priority=1.0,
                target_id=event_data.get("safe_location"),
            )

        # Возможность - можем отложить
        if event_type == "opportunity":
            self.add_belief(BeliefCategory.OPPORTUNITY, event_data.get("id", "unknown"),
                           event_data, current_day=current_day)
            # Не прерываем текущее действие

        return None

    def complete_action(self, action: Action, success: bool,
                       result: Dict[str, Any]) -> None:
        """
        Обрабатывает завершение действия.

        Обновляет намерение и убеждения на основе результата.
        """
        if self.current_intention:
            intention = self.intentions.get(self.current_intention)
            if intention:
                if success:
                    # Переходим к следующему действию
                    if not intention.advance():
                        # План завершён
                        self.current_intention = None
                else:
                    # Действие провалилось
                    intention.is_failed = True
                    self.current_intention = None

    def apply_personality(self, personality_traits: Dict[str, float]) -> None:
        """
        Применяет черты характера к приоритетам желаний.

        Например:
        - Жадность увеличивает приоритет WEALTH
        - Общительность увеличивает BELONG, FRIENDSHIP
        - Амбициозность увеличивает POWER, STATUS
        """
        trait_effects = {
            "greedy": [(DesireType.WEALTH, 0.3)],
            "social": [(DesireType.BELONG, 0.2), (DesireType.FRIENDSHIP, 0.2)],
            "ambitious": [(DesireType.POWER, 0.2), (DesireType.STATUS, 0.2)],
            "curious": [(DesireType.KNOWLEDGE, 0.3)],
            "lazy": [(DesireType.SLEEP, 0.2)],
            "brave": [(DesireType.SAFETY, -0.2)],  # Меньше заботится о безопасности
            "fearful": [(DesireType.SAFETY, 0.3)],
        }

        for trait, value in personality_traits.items():
            if trait in trait_effects:
                for desire_type, modifier in trait_effects[trait]:
                    if desire_type in self.desires:
                        current = self.desires[desire_type].desire_type.base_priority
                        # Модифицируем базовый приоритет
                        self.personality_modifiers[desire_type.name] = modifier * value

    def get_statistics(self) -> Dict[str, Any]:
        """Статистика агента"""
        active_desires = self.get_active_desires()
        active_intentions = [i for i in self.intentions.values() if i.is_active]

        return {
            "total_beliefs": len(self.beliefs),
            "active_desires": len(active_desires),
            "top_desire": active_desires[0].desire_type.russian_name if active_desires else "нет",
            "active_intentions": len(active_intentions),
            "current_intention": self.current_intention,
        }
