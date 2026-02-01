"""
Главный цикл симуляции - объединяет все системы.

Архитектура по Марксу:
1. БАЗИС (экономика) обновляется первым
2. НАДСТРОЙКА (культура) следует за базисом
3. NPC действуют в рамках базиса и надстройки
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import random

from .config import Config
from .events import EventBus, Event, EventType, EventImportance

from ..world.map import WorldMap, Position
from ..world.climate import ClimateSystem, Season

from ..economy.resources import ResourceType, Resource, Inventory
from ..economy.technology import KnowledgeSystem, TECHNOLOGIES
from ..economy.property import OwnershipSystem, PropertyType
from ..economy.production import Production, PRODUCTION_METHODS

from ..society.family import FamilySystem
from ..society.demography import DemographySystem
from ..society.classes import ClassSystem, ClassType

from ..culture.beliefs import BeliefSystem
from ..culture.traditions import TraditionSystem
from ..culture.norms import NormSystem


@dataclass
class NPCState:
    """Состояние NPC в симуляции"""
    id: str
    name: str
    age: int
    is_female: bool
    is_alive: bool = True

    # Позиция
    position: Position = field(default_factory=lambda: Position(25, 25))

    # Ресурсы
    inventory: Inventory = None

    # Характеристики
    health: float = 100.0
    hunger: float = 0.0
    energy: float = 100.0
    happiness: float = 50.0

    # Навыки (0-100)
    skills: Dict[str, int] = field(default_factory=dict)

    # Личность
    traits: List[str] = field(default_factory=list)
    intelligence: int = 10

    # Социальное
    family_id: Optional[str] = None
    spouse_id: Optional[str] = None

    def __post_init__(self):
        if self.inventory is None:
            self.inventory = Inventory(owner_id=self.id)

    def is_adult(self) -> bool:
        return self.age >= 16

    def can_work(self) -> bool:
        return self.is_alive and self.is_adult() and self.health > 20

    @property
    def x(self) -> float:
        """Координата X для UI"""
        return self.position.x

    @property
    def y(self) -> float:
        """Координата Y для UI"""
        return self.position.y


class Simulation:
    """
    Главный класс симуляции.

    Управляет:
    - Временем
    - Всеми подсистемами
    - Циклом обновления
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()

        # Время
        self.year: int = 1
        self.month: int = 1
        self.day: int = 1
        self.hour: int = 6

        # Мир
        self.map = WorldMap(
            width=self.config.map_width,
            height=self.config.map_height,
        )
        self.climate = ClimateSystem()

        # Экономика (БАЗИС)
        self.knowledge = KnowledgeSystem()
        self.ownership = OwnershipSystem()
        self.production = Production()

        # Общество
        self.families = FamilySystem()
        self.demography = DemographySystem()
        self.classes = ClassSystem()

        # Культура (НАДСТРОЙКА)
        self.beliefs = BeliefSystem()
        self.traditions = TraditionSystem()
        self.norms = NormSystem()

        # NPC
        self.npcs: Dict[str, NPCState] = {}

        # События
        self.event_bus = EventBus()
        self.event_log: List[str] = []

        # Статистика
        self.total_days: int = 0
        self.generations: int = 1

        # Кэш для UI
        self._world_map_cache: List[List[str]] = None
        self._world_map_dirty: bool = True

    @property
    def world_map(self) -> List[List[str]]:
        """
        Возвращает 2D массив символов карты для UI.

        Кэшируется для производительности.
        """
        if self._world_map_dirty or self._world_map_cache is None:
            self._world_map_cache = self._build_world_map()
            self._world_map_dirty = False
        return self._world_map_cache

    def _build_world_map(self) -> List[List[str]]:
        """Строит 2D массив символов карты"""
        result = []
        for y in range(self.map.height):
            row = []
            for x in range(self.map.width):
                tile = self.map.get_tile(x, y)
                if tile:
                    # Используем символ из свойств тайла
                    symbol = tile.get_symbol()
                else:
                    symbol = '.'
                row.append(symbol)
            result.append(row)
        return result

    def initialize(self) -> List[str]:
        """Инициализирует мир с начальной популяцией"""
        events = []

        # Создаём начальные семьи
        family_names = ["Волковы", "Медведевы", "Орловы"]

        for i, family_name in enumerate(self.config.initial_families * [None]):
            if i < len(family_names):
                fname = family_names[i]
            else:
                fname = f"Род_{i+1}"

            # Создаём пару (мужчина и женщина)
            for is_female in [False, True]:
                npc = self._create_npc(is_female=is_female, family_name=fname)
                events.append(f"{npc.name} присоединился к общине")

        # Оставшиеся NPC
        remaining = self.config.initial_population - len(self.npcs)
        for _ in range(remaining):
            is_female = random.random() < 0.5
            npc = self._create_npc(is_female=is_female)
            events.append(f"{npc.name} присоединился к общине")

        # Создаём начальные браки
        males = [n for n in self.npcs.values() if not n.is_female and n.is_adult()]
        females = [n for n in self.npcs.values() if n.is_female and n.is_adult()]

        for male, female in zip(males[:len(females)], females):
            self.families.marry(male.id, female.id, self.year)
            male.spouse_id = female.id
            female.spouse_id = male.id
            events.append(f"{male.name} и {female.name} создали семью")

        # Даём начальные знания
        for npc in self.npcs.values():
            self.knowledge.add_knowledge(npc.id, "gathering")
            if random.random() < 0.3:
                self.knowledge.add_knowledge(npc.id, "stone_knapping")

        # Начальные верования
        for npc in self.npcs.values():
            self.beliefs.add_belief_to_npc(npc.id, "animism")

        return events

    def _create_npc(self, is_female: bool = False,
                    family_name: str = None,
                    age: int = None) -> NPCState:
        """Создаёт нового NPC"""
        npc_id = f"npc_{len(self.npcs) + 1}"

        # Имена
        male_names = ["Иван", "Пётр", "Сидор", "Фёдор", "Егор", "Василий", "Григорий", "Алексей"]
        female_names = ["Мария", "Анна", "Ольга", "Елена", "Наталья", "Дарья", "Прасковья", "Варвара"]

        name = random.choice(female_names if is_female else male_names)

        if age is None:
            age = random.randint(
                self.config.starting_age_min,
                self.config.starting_age_max
            )

        npc = NPCState(
            id=npc_id,
            name=name,
            age=age,
            is_female=is_female,
            position=Position(
                self.map.width // 2 + random.randint(-5, 5),
                self.map.height // 2 + random.randint(-5, 5),
            ),
            intelligence=random.randint(7, 14),
            skills={
                "gathering": random.randint(0, 20),
                "hunting": random.randint(0, 15),
                "crafting": random.randint(0, 10),
            },
            traits=random.sample(
                ["curious", "lazy", "hardworking", "aggressive", "peaceful", "greedy", "generous"],
                k=random.randint(1, 3)
            ),
        )

        # Начальные ресурсы
        npc.inventory.add(Resource(ResourceType.BERRIES, quantity=5))

        self.npcs[npc_id] = npc

        # Семья
        if family_name:
            family = self.families.get_npc_family(npc_id)
            if not family:
                self.families.create_family(family_name, npc_id, self.year)

        return npc

    def update(self, hours: int = 1) -> List[str]:
        """
        Обновляет симуляцию на указанное количество часов.

        Порядок обновления важен:
        1. Время и климат
        2. БАЗИС (экономика)
        3. NPC действия
        4. НАДСТРОЙКА (культура)
        5. Демография
        """
        all_events = []

        for _ in range(hours):
            # === 1. Время ===
            self.hour += 1
            if self.hour >= 24:
                self.hour = 0
                self.day += 1
                self.total_days += 1

                # Новый день
                day_events = self._process_new_day()
                all_events.extend(day_events)

                if self.day > self.config.days_per_month:
                    self.day = 1
                    self.month += 1

                    if self.month > self.config.months_per_year:
                        self.month = 1
                        self.year += 1
                        year_events = self._process_new_year()
                        all_events.extend(year_events)

            # === 2. NPC действия (каждый час) ===
            npc_events = self._process_npc_actions()
            all_events.extend(npc_events)

        # Ограничиваем лог
        self.event_log.extend(all_events)
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-500:]

        return all_events

    def _process_new_day(self) -> List[str]:
        """Обрабатывает начало нового дня"""
        events = []

        # Климат
        day_of_year = (self.month - 1) * self.config.days_per_month + self.day
        climate_events = self.climate.update(day_of_year, self.year)
        events.extend(climate_events)

        # Проверяем катаклизмы и их влияние на классовое сознание
        if self.climate.active_disasters:
            for disaster in self.climate.active_disasters:
                crisis_severity = disaster.severity
                consciousness_boost = self.classes.apply_crisis_effect(crisis_severity)
                if consciousness_boost > 0.1:
                    events.append(
                        f"Кризис ({disaster.disaster_type.value}) "
                        f"усилил классовое сознание (+{consciousness_boost:.0%})"
                    )

        # Потребности NPC
        for npc in self.npcs.values():
            if not npc.is_alive:
                continue

            # Голод
            npc.hunger += 10
            if npc.hunger > 100:
                npc.health -= 5
                if npc.health <= 0:
                    npc.is_alive = False
                    events.append(f"{npc.name} умер от голода")

            # Старение (раз в год симулируется здесь для упрощения)
            if self.day == 1 and self.month == 1:
                npc.age += 1

            # Порча еды
            spoiled = npc.inventory.decay_all(1.0)

        # Проверяем возникновение верований
        economic_conditions = {
            "gathering_activity": sum(1 for n in self.npcs.values() if n.can_work()),
            "private_property_exists": self.ownership.private_property_emerged,
            "inequality": self.ownership.calculate_inequality(),
        }
        social_conditions = {
            "deaths_occurred": self.demography.deaths_this_year,
            "classes_emerged": self.classes.classes_emerged,
        }

        new_belief = self.beliefs.check_belief_emergence(
            economic_conditions, social_conditions, self.year
        )
        if new_belief:
            events.append(f"Возникло верование: {new_belief.name}")

        # === КЛАССОВЫЕ КОНФЛИКТЫ ===
        conflict_events = self._process_class_conflicts()
        events.extend(conflict_events)

        return events

    def _process_class_conflicts(self) -> List[str]:
        """
        Обрабатывает классовые конфликты.

        По марксистской теории:
        1. Обновляем существующие конфликты
        2. Проверяем возникновение новых
        3. Распространяем классовое сознание
        """
        events = []

        # Обновляем классы NPC на основе собственности
        self._update_npc_classes()

        # Обновляем существующие конфликты
        conflict_events = self.classes.update_conflicts(
            self.year, self.ownership
        )
        events.extend(conflict_events)

        # Проверяем возникновение нового конфликта
        new_conflict = self.classes.check_for_conflict(self.year)
        if new_conflict:
            events.append(
                f"КОНФЛИКТ! {new_conflict.conflict_type.russian_name}: "
                f"{new_conflict.oppressed_class.russian_name} восстали против "
                f"{new_conflict.ruling_class.russian_name}. "
                f"Причина: {new_conflict.primary_cause}"
            )

        return events

    def _update_npc_classes(self) -> None:
        """Обновляет классовую принадлежность NPC"""
        for npc_id, npc in self.npcs.items():
            if not npc.is_alive:
                continue

            # Определяем владение
            owns_land = self.ownership.owns_land(npc_id)
            owns_tools = self.ownership.owns_tools(npc_id)
            owns_livestock = False  # Упрощённо

            # Богатство (по инвентарю)
            wealth = npc.inventory.total_value()

            # Работает ли на других
            works_for_others = not (owns_land or owns_tools)

            # Определяем класс
            new_class = self.classes.determine_class(
                npc_id=npc_id,
                owns_land=owns_land,
                owns_tools=owns_tools,
                owns_livestock=owns_livestock,
                wealth=wealth,
                works_for_others=works_for_others,
                is_elder=npc.age > 50 and "peaceful" in npc.traits,
                is_chief=npc.age > 30 and "aggressive" in npc.traits and wealth > 100,
                private_property_exists=self.ownership.private_property_emerged
            )

            # Обновляем класс
            changed = self.classes.update_npc_class(npc_id, new_class, self.year)

    def _process_new_year(self) -> List[str]:
        """Обрабатывает начало нового года"""
        events = [f"=== Наступил год {self.year} ==="]

        population = len([n for n in self.npcs.values() if n.is_alive])
        events.append(f"Население: {population}")

        # Демография
        self.demography.record_year_end(self.year, population)

        # Проверяем смены поколений (каждые ~25 лет)
        if self.year % 25 == 0:
            self.generations += 1
            events.append(f"Сменилось поколение! Поколение {self.generations}")

        # Статистика технологий
        tech_stats = self.knowledge.get_statistics()
        events.append(f"Эпоха: {tech_stats['era']}")

        # Классы
        if self.classes.classes_emerged:
            class_dist = self.classes.get_class_distribution()
            events.append(f"Классы: {class_dist}")

        return events

    def _process_npc_actions(self) -> List[str]:
        """Обрабатывает действия NPC"""
        events = []

        for npc in self.npcs.values():
            if not npc.is_alive or not npc.can_work():
                continue

            # Простая логика действий
            action = self._decide_action(npc)
            action_events = self._execute_action(npc, action)
            events.extend(action_events)

        return events

    def _decide_action(self, npc: NPCState) -> str:
        """Решает, что делать NPC"""
        # Приоритет: голод -> работа -> социализация

        if npc.hunger > 70:
            # Ищем еду
            if npc.inventory.get_food_amount() > 0:
                return "eat"
            return "gather_food"

        if npc.energy < 30:
            return "rest"

        # Работа
        season = self.climate.current_season.value
        productivity = self.climate.get_season_productivity()

        if productivity.get("gathering", 0) > 0.5:
            return "gather"
        if productivity.get("hunting", 0) > 0.5 and "hunting" in npc.skills:
            return "hunt"

        return "socialize"

    def _execute_action(self, npc: NPCState, action: str) -> List[str]:
        """Выполняет действие NPC"""
        events = []

        if action == "eat":
            # Едим
            food_types = [ResourceType.BERRIES, ResourceType.MEAT, ResourceType.FISH]
            for food_type in food_types:
                food = npc.inventory.remove(food_type, 1)
                if food:
                    npc.hunger = max(0, npc.hunger - 30)
                    break

        elif action == "gather_food" or action == "gather":
            # Собираем ягоды
            skill = npc.skills.get("gathering", 0)
            amount = 1 + skill / 50 + random.random()

            weather_mod = self.climate.current_weather.gathering_modifier
            amount *= weather_mod

            if amount > 0.5:
                npc.inventory.add(Resource(ResourceType.BERRIES, quantity=amount))
                npc.skills["gathering"] = min(100, skill + 1)
                npc.energy -= 10
                npc.hunger += 5

                # Шанс открыть технологию
                discovery = self.knowledge.try_discovery(
                    npc.id, "gathering", npc.intelligence, self.year
                )
                if discovery:
                    events.append(f"{npc.name} открыл: {discovery.name}!")

        elif action == "hunt":
            skill = npc.skills.get("hunting", 0)
            success = random.random() < (0.3 + skill / 200)

            if success:
                amount = 2 + skill / 30
                npc.inventory.add(Resource(ResourceType.MEAT, quantity=amount))
                npc.skills["hunting"] = min(100, skill + 1)
                events.append(f"{npc.name} добыл дичь")

            npc.energy -= 20
            npc.hunger += 10

        elif action == "rest":
            npc.energy = min(100, npc.energy + 20)

        elif action == "socialize":
            # Общение - распространение знаний и верований
            others = [n for n in self.npcs.values()
                      if n.id != npc.id and n.is_alive
                      and npc.position.distance_to(n.position) < 5]

            if others:
                other = random.choice(others)

                # Передача знаний
                my_knowledge = self.knowledge.get_npc_knowledge(npc.id)
                for tech_id in my_knowledge:
                    if self.knowledge.transfer_knowledge(
                            npc.id, other.id, tech_id, 1.0,
                            npc.skills.get("teaching", 0.5) / 50,
                            other.intelligence
                    ):
                        events.append(f"{npc.name} научил {other.name}: {tech_id}")

                # Распространение верований
                my_beliefs = self.beliefs.npc_beliefs.get(npc.id, set())
                for belief_id in my_beliefs:
                    self.beliefs.spread_belief(belief_id, npc.id, other.id)

        return events

    def get_status(self) -> str:
        """Возвращает статус симуляции"""
        alive = len([n for n in self.npcs.values() if n.is_alive])

        lines = [
            f"=== Год {self.year}, месяц {self.month}, день {self.day} ===",
            f"Сезон: {self.climate.current_season.value}",
            f"Погода: {self.climate.current_weather.describe()}",
            f"",
            f"Население: {alive}",
            f"Эпоха: {self.knowledge.get_current_era().russian_name}",
            f"",
        ]

        # Классы
        if self.classes.classes_emerged:
            lines.append("Классы:")
            for class_name, count in self.classes.get_class_distribution().items():
                lines.append(f"  {class_name}: {count}")
        else:
            lines.append("Классов ещё нет (первобытная община)")

        # Верования
        lines.append("")
        lines.append("Верования:")
        for belief in self.beliefs.beliefs.values():
            lines.append(f"  {belief.name}: {belief.get_adherent_count()} чел.")

        return "\n".join(lines)

    def get_npc_list(self) -> str:
        """Возвращает список NPC"""
        lines = ["=== Жители ==="]

        for npc in sorted(self.npcs.values(), key=lambda n: n.name):
            if not npc.is_alive:
                continue

            status = "♀" if npc.is_female else "♂"
            food = npc.inventory.get_food_amount()
            lines.append(
                f"{npc.name} {status}, {npc.age} лет | "
                f"HP:{npc.health:.0f} Голод:{npc.hunger:.0f} Еда:{food:.1f}"
            )

        return "\n".join(lines)

    def get_map_view(self) -> str:
        """Возвращает вид карты"""
        npc_positions = {
            npc.id: npc.position
            for npc in self.npcs.values()
            if npc.is_alive
        }

        return self.map.render_ascii(
            center_x=self.map.width // 2,
            center_y=self.map.height // 2,
            viewport_size=30,
            npc_positions=npc_positions,
        )
