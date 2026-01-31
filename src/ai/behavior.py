"""
Система AI поведения - определяет, как NPC принимают решения.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from ..npc.character import NPC
    from ..world.world import World

from ..npc.needs import Need
from ..npc.personality import Trait
from ..world.location import LocationType
from ..world.time_system import TimeOfDay


class ActionType(Enum):
    """Типы действий NPC"""
    IDLE = "бездельничает"
    SLEEP = "спит"
    EAT = "ест"
    WORK = "работает"
    SOCIALIZE = "общается"
    RELAX = "отдыхает"
    TRAVEL = "перемещается"
    SHOP = "делает покупки"
    PRAY = "молится"
    TRAIN = "тренируется"
    EXPLORE = "исследует"


@dataclass
class Action:
    """Действие NPC"""
    action_type: ActionType
    target_location_id: Optional[str] = None
    target_npc_id: Optional[str] = None
    duration_hours: float = 1.0
    priority: float = 1.0
    description: str = ""

    def describe(self) -> str:
        return self.description or self.action_type.value


class BehaviorSystem:
    """
    Система принятия решений для NPC.

    Использует:
    - Потребности (приоритет критическим)
    - Время суток (работа днём, сон ночью)
    - Личность (влияет на выбор действий)
    - Отношения (предпочитает друзей)
    - Случайность (для реалистичности)
    """

    def __init__(self, world: 'World'):
        self.world = world

    def decide_action(self, npc: 'NPC') -> Action:
        """Определяет следующее действие для NPC"""
        # Собираем все возможные действия
        possible_actions = self._get_possible_actions(npc)

        if not possible_actions:
            return Action(ActionType.IDLE, description=f"{npc.name} бездельничает")

        # Сортируем по приоритету и выбираем
        possible_actions.sort(key=lambda a: a.priority, reverse=True)

        # Добавляем случайность - не всегда выбираем лучшее
        if len(possible_actions) > 1 and random.random() < 0.2:
            # 20% шанс выбрать случайное из топ-3
            top_actions = possible_actions[:min(3, len(possible_actions))]
            return random.choice(top_actions)

        return possible_actions[0]

    def _get_possible_actions(self, npc: 'NPC') -> List[Action]:
        """Собирает все возможные действия с их приоритетами"""
        actions = []

        time_of_day = self.world.time.get_time_of_day()
        hour = self.world.time.hour

        # === Критические потребности ===
        critical_needs = npc.needs.get_critical_needs()

        if Need.ENERGY in critical_needs or npc.is_sleeping:
            actions.append(self._create_sleep_action(npc))

        if Need.HUNGER in critical_needs:
            actions.append(self._create_eat_action(npc))

        if Need.SAFETY in critical_needs:
            actions.append(self._create_safety_action(npc))

        # === Время суток ===
        if time_of_day == TimeOfDay.NIGHT:
            # Ночью большинство спит
            if not npc.personality.has_trait(Trait.EXTROVERT):
                actions.append(Action(
                    ActionType.SLEEP,
                    target_location_id=npc.home_location_id,
                    duration_hours=6.0,
                    priority=8.0,
                    description=f"{npc.name} идёт спать"
                ))

        elif time_of_day in [TimeOfDay.MORNING, TimeOfDay.NOON, TimeOfDay.AFTERNOON]:
            # Рабочее время
            if npc.work_location_id and self.world.time.is_work_hours():
                work_priority = 7.0
                if npc.personality.has_trait(Trait.HARDWORKING):
                    work_priority += 2.0
                if npc.personality.has_trait(Trait.LAZY):
                    work_priority -= 2.0

                actions.append(Action(
                    ActionType.WORK,
                    target_location_id=npc.work_location_id,
                    duration_hours=4.0,
                    priority=work_priority,
                    description=f"{npc.name} работает ({npc.occupation.value})"
                ))

        # === Потребности (не критические) ===
        low_needs = npc.needs.get_low_needs()

        if Need.SOCIAL in low_needs or npc.personality.has_trait(Trait.EXTROVERT):
            actions.append(self._create_socialize_action(npc))

        if Need.FUN in low_needs:
            actions.append(self._create_fun_action(npc))

        if Need.HUNGER in low_needs:
            eat_action = self._create_eat_action(npc)
            eat_action.priority = 5.0  # Ниже для не-критического
            actions.append(eat_action)

        # === Личностные предпочтения ===
        if npc.personality.has_trait(Trait.CURIOUS):
            actions.append(Action(
                ActionType.EXPLORE,
                target_location_id=self._find_interesting_location(npc),
                duration_hours=2.0,
                priority=3.0,
                description=f"{npc.name} исследует окрестности"
            ))

        if npc.personality.has_trait(Trait.AMBITIOUS):
            actions.append(Action(
                ActionType.TRAIN,
                duration_hours=2.0,
                priority=4.0,
                description=f"{npc.name} совершенствует навыки"
            ))

        # === Базовые действия ===
        actions.append(Action(
            ActionType.IDLE,
            duration_hours=1.0,
            priority=1.0,
            description=f"{npc.name} отдыхает"
        ))

        return actions

    def _create_sleep_action(self, npc: 'NPC') -> Action:
        """Создаёт действие сна"""
        energy = npc.needs.get(Need.ENERGY).value
        priority = 10.0 if energy < 10 else 8.0 if energy < 30 else 5.0

        return Action(
            ActionType.SLEEP,
            target_location_id=npc.home_location_id,
            duration_hours=8.0,
            priority=priority,
            description=f"{npc.name} спит"
        )

    def _create_eat_action(self, npc: 'NPC') -> Action:
        """Создаёт действие приёма пищи"""
        # Ищем место где можно поесть
        eat_locations = [
            loc for loc in self.world.locations.values()
            if "еда" in loc.available_services
            and loc.is_open(self.world.time.hour)
        ]

        target = None
        if eat_locations:
            target = random.choice(eat_locations).id
        elif npc.home_location_id:
            target = npc.home_location_id

        hunger = npc.needs.get(Need.HUNGER).value
        priority = 10.0 if hunger < 10 else 7.0 if hunger < 30 else 5.0

        return Action(
            ActionType.EAT,
            target_location_id=target,
            duration_hours=1.0,
            priority=priority,
            description=f"{npc.name} ест"
        )

    def _create_safety_action(self, npc: 'NPC') -> Action:
        """Создаёт действие поиска безопасности"""
        return Action(
            ActionType.TRAVEL,
            target_location_id=npc.home_location_id,
            duration_hours=0.5,
            priority=10.0,
            description=f"{npc.name} прячется дома"
        )

    def _create_socialize_action(self, npc: 'NPC') -> Action:
        """Создаёт действие социализации"""
        # Ищем место с людьми
        social_locations = [
            LocationType.TAVERN, LocationType.MARKET,
            LocationType.TOWN_SQUARE, LocationType.CHURCH
        ]

        candidates = [
            loc for loc in self.world.locations.values()
            if loc.location_type in social_locations
            and loc.is_open(self.world.time.hour)
            and loc.get_npc_count() > 0
        ]

        if not candidates:
            candidates = [
                loc for loc in self.world.locations.values()
                if loc.location_type in social_locations
                and loc.is_open(self.world.time.hour)
            ]

        target = random.choice(candidates).id if candidates else None

        # Приоритет зависит от личности
        priority = 5.0
        if npc.personality.has_trait(Trait.EXTROVERT):
            priority += 2.0
        if npc.personality.has_trait(Trait.INTROVERT):
            priority -= 2.0
        if npc.personality.has_trait(Trait.FRIENDLY):
            priority += 1.0

        return Action(
            ActionType.SOCIALIZE,
            target_location_id=target,
            duration_hours=2.0,
            priority=priority,
            description=f"{npc.name} ищет компанию"
        )

    def _create_fun_action(self, npc: 'NPC') -> Action:
        """Создаёт действие развлечения"""
        fun_locations = [LocationType.TAVERN, LocationType.FOREST]

        candidates = [
            loc for loc in self.world.locations.values()
            if loc.location_type in fun_locations
            and loc.is_open(self.world.time.hour)
        ]

        target = random.choice(candidates).id if candidates else None

        return Action(
            ActionType.RELAX,
            target_location_id=target,
            duration_hours=2.0,
            priority=4.0,
            description=f"{npc.name} развлекается"
        )

    def _find_interesting_location(self, npc: 'NPC') -> Optional[str]:
        """Находит интересную локацию для исследования"""
        # Исключаем текущую локацию и дом
        exclude = {npc.current_location_id, npc.home_location_id}

        candidates = [
            loc for loc in self.world.locations.values()
            if loc.id not in exclude
        ]

        if candidates:
            return random.choice(candidates).id
        return None

    def execute_action(self, npc: 'NPC', action: Action) -> List[str]:
        """
        Выполняет действие NPC.
        Возвращает список событий.
        """
        events = []

        # Перемещение, если нужно
        if action.target_location_id and action.target_location_id != npc.current_location_id:
            if self.world.move_npc(npc.id, action.target_location_id):
                location = self.world.get_location(action.target_location_id)
                events.append(f"{npc.name} пришёл в {location.name}")

        # Обновляем активность
        npc.current_activity = action.describe()

        # Выполняем действие
        if action.action_type == ActionType.SLEEP:
            npc.is_sleeping = True
            npc.needs.satisfy(Need.ENERGY, 30 * action.duration_hours)
            npc.needs.satisfy(Need.COMFORT, 10)

        elif action.action_type == ActionType.EAT:
            npc.needs.satisfy(Need.HUNGER, 40)
            npc.needs.satisfy(Need.COMFORT, 5)
            npc.wealth -= 2  # Тратим деньги на еду

        elif action.action_type == ActionType.WORK:
            npc.is_sleeping = False
            # Зарабатываем деньги и опыт
            earnings = int(10 * npc.personality.get_work_modifier())
            npc.wealth += earnings
            npc.gain_experience(5)
            npc.needs.satisfy(Need.PURPOSE, 15)
            # Тратим энергию
            npc.needs.get(Need.ENERGY).decay(2)
            events.append(f"{npc.name} заработал {earnings} монет")

        elif action.action_type == ActionType.SOCIALIZE:
            npc.is_sleeping = False
            # Находим кого-то для общения
            others = self.world.get_npcs_at_location(npc.current_location_id)
            others = [o for o in others if o.id != npc.id and o.is_alive and not o.is_sleeping]

            if others:
                other = random.choice(others)
                result = npc.interact_with(other)
                events.extend(result.get("events", []))

        elif action.action_type == ActionType.RELAX:
            npc.is_sleeping = False
            npc.needs.satisfy(Need.FUN, 25)
            npc.needs.satisfy(Need.COMFORT, 10)

        elif action.action_type == ActionType.TRAIN:
            npc.is_sleeping = False
            npc.gain_experience(10)
            # Улучшаем случайный навык
            skill_names = ['combat', 'crafting', 'persuasion', 'stealth']
            skill = random.choice(skill_names)
            npc.skills.improve(skill, 1)
            events.append(f"{npc.name} совершенствует навыки")

        elif action.action_type == ActionType.EXPLORE:
            npc.is_sleeping = False
            npc.needs.satisfy(Need.FUN, 15)
            npc.gain_experience(3)
            # Шанс найти что-то интересное
            if random.random() < 0.1:
                found = random.randint(1, 20)
                npc.wealth += found
                events.append(f"{npc.name} нашёл {found} монет во время исследования!")

        return events

    def simulate_all_npcs(self) -> List[str]:
        """Симулирует поведение всех NPC"""
        all_events = []

        for npc in self.world.get_living_npcs():
            # Спящие NPC не принимают новых решений
            if npc.is_sleeping:
                # Проверяем, не пора ли проснуться
                if self.world.time.hour >= 6 and npc.needs.get(Need.ENERGY).value > 70:
                    npc.is_sleeping = False
                    all_events.append(f"{npc.name} проснулся")
                continue

            # Принимаем решение
            action = self.decide_action(npc)

            # Выполняем действие
            events = self.execute_action(npc, action)
            all_events.extend(events)

        return all_events
