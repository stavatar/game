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
from .consistency import validate_state_consistency, ConsistencyLevel

from ..world.map import WorldMap, Position
from ..world.climate import ClimateSystem, Season

from ..economy.resources import ResourceType, Resource, Inventory
from ..economy.technology import KnowledgeSystem, TECHNOLOGIES
from ..economy.property import OwnershipSystem, PropertyType, OwnershipTransition
from ..economy.production import Production, PRODUCTION_METHODS

from ..society.family import FamilySystem
from ..society.demography import DemographySystem
from ..society.classes import ClassSystem, ClassType, SocialClass

from ..culture.beliefs import BeliefSystem
from ..culture.traditions import TraditionSystem
from ..culture.norms import NormSystem

# Unified NPC model imports
from ..npc.character import NPC, Gender, Occupation, Stats, Skills
from ..npc.needs import Need


@dataclass
class SimulationNPC(NPC):
    """
    NPC для симуляции - расширяет базовый NPC класс полями для симуляции.

    Добавляет:
    - position: Координаты на карте
    - inventory: Инвентарь из экономической системы
    - family_id, spouse_id: Прямые ссылки на семью

    Также предоставляет свойства для удобства:
    - is_female, x, y, hunger, energy, happiness
    """

    # Позиция на карте (для симуляции)
    position: Position = field(default_factory=lambda: Position(25, 25))

    # Инвентарь (экономическая система)
    inventory: Inventory = None

    # Прямые ссылки на семью (для совместимости с FamilySystem)
    family_id: Optional[str] = None
    spouse_id: Optional[str] = None

    # Словарь навыков для обратной совместимости с симуляцией
    _skill_dict: Dict[str, int] = field(default_factory=dict)

    # Легаси черты характера (для обратной совместимости)
    _legacy_traits: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Инициализация после создания"""
        # Вызываем родительский __post_init__
        super().__post_init__()

        # Инициализируем инвентарь если не задан
        if self.inventory is None:
            self.inventory = Inventory(owner_id=self.id)

    # === Свойства для удобства доступа ===

    @property
    def is_female(self) -> bool:
        """Совместимость: возвращает True если женщина"""
        return self.gender == Gender.FEMALE

    @property
    def x(self) -> float:
        """Координата X для UI"""
        return self.position.x if self.position else 0.0

    @property
    def y(self) -> float:
        """Координата Y для UI"""
        return self.position.y if self.position else 0.0

    @property
    def hunger(self) -> float:
        """
        Уровень голода (0-100, выше = голоднее).

        ВНИМАНИЕ: Инвертирован относительно Needs системы!
        Needs.HUNGER.value=100 означает сытость,
        а hunger=100 означает сильный голод.
        """
        return 100 - self.needs.get(Need.HUNGER).value

    @hunger.setter
    def hunger(self, value: float):
        """Устанавливает уровень голода (инвертируя для Needs)"""
        self.needs.get(Need.HUNGER).value = 100 - value

    @property
    def energy(self) -> float:
        """Уровень энергии (0-100)"""
        return self.needs.get(Need.ENERGY).value

    @energy.setter
    def energy(self, value: float):
        """Устанавливает уровень энергии"""
        self.needs.get(Need.ENERGY).value = min(100, max(0, value))

    @property
    def happiness(self) -> float:
        """Уровень счастья (0-100)"""
        return self.needs.get_overall_happiness()

    @property
    def traits(self) -> List[str]:
        """
        Возвращает черты характера как список строк.

        Возвращает легаси черты если они есть, иначе черты из Personality.
        """
        if self._legacy_traits:
            return self._legacy_traits

        return [trait.name.lower() for trait in self.personality.traits]

    @traits.setter
    def traits(self, value: List[str]):
        """Устанавливает легаси черты"""
        self._legacy_traits = value

    @property
    def intelligence(self) -> int:
        """Интеллект из Stats"""
        return self.stats.intelligence

    # === Методы для логики симуляции ===

    def is_adult(self) -> bool:
        """Является ли взрослым (16+ лет)"""
        return self.age >= 16

    def can_work(self) -> bool:
        """Может ли работать"""
        return self.is_alive and self.is_adult() and self.health > 20

    def get_skill(self, skill_name: str) -> int:
        """
        Получить значение навыка.
        Сначала проверяет _skill_dict, затем Skills объект.
        """
        # Проверяем словарь навыков (для совместимости)
        if skill_name in self._skill_dict:
            return self._skill_dict[skill_name]

        # Маппинг имён навыков
        skill_mapping = {
            "gathering": "farming",  # Собирательство -> фермерство
            "hunting": "combat",     # Охота -> бой
            "crafting": "crafting",
            "trading": "trading",
            "cooking": "cooking",
            "medicine": "medicine",
        }

        mapped_name = skill_mapping.get(skill_name, skill_name)
        if hasattr(self.skills, mapped_name):
            return getattr(self.skills, mapped_name)

        return 0

    def set_skill(self, skill_name: str, value: int) -> None:
        """Устанавливает значение навыка"""
        self._skill_dict[skill_name] = min(100, max(0, value))

    # Для совместимости с npc.skills.get("name", 0)
    @property
    def skill_dict(self) -> Dict[str, int]:
        """Возвращает словарь навыков для совместимости"""
        return self._skill_dict


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

        # NPC (unified model - SimulationNPC extends NPC)
        self.npcs: Dict[str, SimulationNPC] = {}

        # События
        self.event_bus = EventBus()
        self.event_log: List[str] = []

        # Подписываемся на события
        self._setup_event_subscribers()

        # Статистика
        self.total_days: int = 0
        self.generations: int = 1

        # === Отслеживание практик для традиций ===
        # Практика -> количество успешных выполнений
        self._practice_successes: Dict[str, int] = {}
        # Последний сезон (для обнаружения смены сезона)
        self._last_season: Optional[Season] = None

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

    def _setup_event_subscribers(self) -> None:
        """Настраивает подписчиков на события"""
        # Подписка на события смерти
        self.event_bus.subscribe(EventType.NPC_DIED, self._on_npc_death)

        # Подписка на события собственности
        self.event_bus.subscribe(EventType.PROPERTY_CLAIMED, self._on_property_claimed)
        self.event_bus.subscribe(EventType.PROPERTY_TRANSFERRED, self._on_property_transferred)
        self.event_bus.subscribe(EventType.PROPERTY_LOST, self._on_property_lost)

        # Подписка на события верований
        self.event_bus.subscribe(EventType.BELIEF_FORMED, self._on_belief_formed)

    def _on_npc_death(self, event: Event) -> None:
        """
        Обработчик события смерти NPC (для внешних событий).

        Примечание: основная обработка смерти выполняется в handle_npc_death().
        Этот обработчик используется для:
        - Логирования событий смерти
        - Обработки внешних смертей (если событие пришло не из handle_npc_death)
        """
        npc_id = event.actor_id
        if not npc_id:
            return

        npc = self.npcs.get(npc_id)
        if not npc:
            return

        # Если NPC уже мёртв, значит handle_npc_death() уже обработал смерть
        # Просто логируем событие
        if not npc.is_alive:
            description = event.description or event.format_description()
            if description and description not in self.event_log[-10:]:
                self.event_log.append(description)
            return

        # Если NPC ещё жив, значит событие пришло извне - обрабатываем смерть
        # (например, от внешнего источника событий)
        cause = event.data.get("cause", "unknown")
        self.handle_npc_death(npc_id, cause)

    def _on_property_claimed(self, event: Event) -> None:
        """
        Обработчик события заявки на собственность.

        Выполняет:
        - Создание нормы защиты собственности (при первом захвате)
        - Обновление классовой принадлежности NPC
        - Логирование
        """
        npc_id = event.actor_id
        if not npc_id:
            return

        npc = self.npcs.get(npc_id)
        if not npc:
            return

        # === НОРМЫ: создаём норму защиты собственности при первом захвате ===
        # По Марксу: нормы возникают для защиты интересов собственников
        if event.data.get("as_private") and "property_protection" not in self.norms.norms:
            norm = self.norms.add_property_norm(self.year)
            self.event_log.append(
                f"Возникла норма: {norm.name} - {norm.description}"
            )

        # Обновляем классы при изменении собственности
        self._update_npc_classes()

        # Добавляем в лог событий
        description = event.format_description()
        if description:
            self.event_log.append(description)

    def _on_property_transferred(self, event: Event) -> None:
        """
        Обработчик события передачи собственности.

        Выполняет:
        - Обновление классовой принадлежности обоих NPC
        - Логирование
        """
        from_npc_id = event.actor_id
        to_npc_id = event.target_id

        # Обновляем классы при изменении собственности
        self._update_npc_classes()

        # Добавляем в лог событий
        description = event.format_description()
        if description:
            self.event_log.append(description)

    def _on_property_lost(self, event: Event) -> None:
        """
        Обработчик события потери собственности.

        Выполняет:
        - Обновление классовой принадлежности NPC
        - Логирование
        """
        npc_id = event.actor_id
        if not npc_id:
            return

        npc = self.npcs.get(npc_id)
        if not npc:
            return

        # Обновляем классы при изменении собственности
        self._update_npc_classes()

        # Добавляем в лог событий
        description = event.format_description()
        if description:
            self.event_log.append(description)

    def _on_belief_formed(self, event: Event) -> None:
        """
        Обработчик события формирования верования.

        Выполняет:
        - Обновление доминирующей идеологии
        - Логирование
        """
        belief_id = event.data.get("belief_id")
        belief_name = event.data.get("belief_name", "")

        # Обновляем доминирующую идеологию если есть классы
        if self.classes.classes_emerged:
            class_power = self.classes.get_class_power()
            self.beliefs.update_dominant_ideology(class_power)

        # Добавляем в лог событий
        description = event.format_description()
        if description:
            self.event_log.append(description)

    def _get_economic_conditions(self) -> Dict[str, any]:
        """
        Собирает экономические условия из всех систем.

        Возвращает словарь с ключами:
        - gathering_activity: количество работающих NPC
        - private_property_exists: возникла ли частная собственность
        - inequality: коэффициент Джини для всей собственности
        - surplus_produced: общий произведённый прибавочный продукт
        - exploitation_rate: норма эксплуатации (0-1)
        - land_inequality: неравенство в землевладении
        - non_workers_exist: есть ли не-работающие собственники
        - wage_labor_exists: существует ли наёмный труд
        """
        # Базовые метрики
        workers_count = sum(1 for n in self.npcs.values() if n.is_alive and n.can_work())

        # Собственность и неравенство
        property_inequality = self.ownership.calculate_inequality()

        # Вычисляем неравенство в землевладении отдельно
        land_owners = set()
        all_living_npc_ids = {n.id for n in self.npcs.values() if n.is_alive}
        for prop in self.ownership.properties.values():
            if prop.category.name == "LAND" and prop.owner_id:
                land_owners.add(prop.owner_id)
        landless_count = len(all_living_npc_ids - land_owners)
        land_owner_count = len(land_owners)
        total_count = len(all_living_npc_ids)

        # Неравенство в землевладении: (безземельные / всего)
        land_inequality = landless_count / total_count if total_count > 0 else 0.0

        # Прибавочный продукт из статистики производства
        production_stats = self.production.get_statistics()
        total_produced = sum(production_stats.get("produced", {}).values())
        total_consumed = sum(production_stats.get("consumed", {}).values())
        surplus_produced = max(0.0, total_produced - total_consumed)

        # Норма эксплуатации: проверяем, есть ли эксплуататоры и эксплуатируемые
        exploitation_rate = 0.0
        if self.classes.classes_emerged:
            # Эксплуататоры: землевладельцы и вожди
            exploiters = []
            exploited = []
            for class_type, social_class in self.classes.classes.items():
                if class_type.is_exploiter:
                    exploiters.extend(social_class.members)
                elif class_type.is_exploited:
                    exploited.extend(social_class.members)

            if exploiters and exploited:
                # Вычисляем среднее богатство эксплуататоров vs эксплуатируемых
                exploiter_wealth = sum(
                    self.ownership.calculate_wealth(npc_id) +
                    self.npcs[npc_id].inventory.total_value()
                    for npc_id in exploiters if npc_id in self.npcs
                )
                exploited_wealth = sum(
                    self.ownership.calculate_wealth(npc_id) +
                    self.npcs[npc_id].inventory.total_value()
                    for npc_id in exploited if npc_id in self.npcs
                )
                total_wealth = exploiter_wealth + exploited_wealth
                if total_wealth > 0:
                    # Норма эксплуатации: доля богатства у эксплуататоров
                    exploitation_rate = exploiter_wealth / total_wealth

        # Проверяем, есть ли не-работающие собственники (те, кто владеет средствами производства
        # но сам не работает - живёт за счёт труда других)
        non_workers_exist = False
        means_owners = self.ownership.get_means_of_production_owners()
        for owner_id in means_owners:
            npc = self.npcs.get(owner_id)
            if npc and npc.is_alive:
                # Проверяем, есть ли у него работники
                npc_class = self.classes.npc_class.get(owner_id)
                if npc_class and npc_class.is_exploiter:
                    # Есть эксплуатируемые - значит не работает сам
                    if any(c.is_exploited and len(self.classes.classes.get(c, SocialClass(c)).members) > 0
                           for c in self.classes.classes):
                        non_workers_exist = True
                        break

        # Наёмный труд существует, если есть класс LABORER с членами
        wage_labor_exists = (
            ClassType.LABORER in self.classes.classes and
            self.classes.classes[ClassType.LABORER].get_size() > 0
        )

        return {
            "gathering_activity": workers_count,
            "private_property_exists": self.ownership.private_property_emerged,
            "inequality": property_inequality,
            "surplus_produced": surplus_produced,
            "exploitation_rate": exploitation_rate,
            "land_inequality": land_inequality,
            "non_workers_exist": non_workers_exist,
            "wage_labor_exists": wage_labor_exists,
        }

    def _get_social_conditions(self) -> Dict[str, any]:
        """
        Собирает социальные условия из всех систем.

        Возвращает словарь с ключами:
        - deaths_occurred: количество смертей в этом году
        - births_occurred: количество рождений в этом году
        - classes_emerged: возникли ли классы
        - class_tension: напряжённость между классами (0-1)
        - active_conflicts: количество активных классовых конфликтов
        - active_marriages: количество активных браков
        - total_families: количество семей
        - population: текущее население
        - life_expectancy: ожидаемая продолжительность жизни
        """
        # Население
        living_npcs = [n for n in self.npcs.values() if n.is_alive]
        population = len(living_npcs)

        # Демографические метрики
        deaths_occurred = self.demography.deaths_this_year
        births_occurred = self.demography.births_this_year
        life_expectancy = self.demography.calculate_life_expectancy()

        # Семейные метрики
        family_stats = self.families.get_statistics()
        active_marriages = family_stats.get("active_marriages", 0)
        total_families = family_stats.get("families", 0)

        # Классовые метрики
        classes_emerged = self.classes.classes_emerged
        class_tension = self.classes.check_class_tension() if classes_emerged else 0.0
        active_conflicts = len(self.classes.get_active_conflicts())

        return {
            "deaths_occurred": deaths_occurred,
            "births_occurred": births_occurred,
            "classes_emerged": classes_emerged,
            "class_tension": class_tension,
            "active_conflicts": active_conflicts,
            "active_marriages": active_marriages,
            "total_families": total_families,
            "population": population,
            "life_expectancy": life_expectancy,
        }

    def _find_heir(self, deceased_id: str) -> Optional[str]:
        """
        Находит наследника для умершего NPC.

        Порядок приоритета:
        1. Супруг (если жив)
        2. Дети (старший живой ребёнок)
        3. Братья/сёстры
        4. Другие члены семьи

        Возвращает id наследника или None.
        """
        deceased = self.npcs.get(deceased_id)
        if not deceased:
            return None

        # 1. Супруг
        spouse_id = self.families.get_spouse(deceased_id)
        if spouse_id:
            spouse = self.npcs.get(spouse_id)
            if spouse and spouse.is_alive:
                return spouse_id

        # 2. Дети (старший живой)
        children = self.families.get_children(deceased_id)
        living_children = []
        for child_id in children:
            child = self.npcs.get(child_id)
            if child and child.is_alive:
                living_children.append((child_id, child.age))

        if living_children:
            # Сортируем по возрасту (старший первый)
            living_children.sort(key=lambda x: x[1], reverse=True)
            return living_children[0][0]

        # 3. Братья/сёстры
        siblings = self.families.get_siblings(deceased_id)
        for sibling_id in siblings:
            sibling = self.npcs.get(sibling_id)
            if sibling and sibling.is_alive:
                return sibling_id

        # 4. Любой член семьи
        family = self.families.get_npc_family(deceased_id)
        if family:
            for member_id in family.members:
                if member_id != deceased_id:
                    member = self.npcs.get(member_id)
                    if member and member.is_alive:
                        return member_id

        return None

    def handle_npc_death(self, npc_id: str, cause: str) -> Optional[str]:
        """
        Обрабатывает смерть NPC - централизованный каскад.

        Выполняет полный процесс смерти:
        1. Помечает NPC как мёртвого
        2. Записывает смерть в демографию
        3. Обновляет семейные связи (супруг становится вдовцом)
        4. Обрабатывает наследование собственности
        5. Удаляет из классовой системы
        6. Удаляет из системы верований
        7. Публикует событие смерти

        Args:
            npc_id: ID умершего NPC
            cause: Причина смерти

        Returns:
            Описание события смерти или None если NPC не найден
        """
        npc = self.npcs.get(npc_id)
        if not npc:
            return None

        # Если уже мёртв - ничего не делаем
        if not npc.is_alive:
            return None

        # === 1. ПОМЕЧАЕМ КАК МЁРТВОГО ===
        npc.is_alive = False

        # === 2. ДЕМОГРАФИЯ: записываем смерть ===
        self.demography.record_death(self.year, cause)

        # === 3. СЕМЬЯ: обновляем связи ===
        # Супруг становится вдовцом
        if npc.spouse_id:
            spouse = self.npcs.get(npc.spouse_id)
            if spouse:
                spouse.spouse_id = None

        # Удаляем из семьи
        family = self.families.get_npc_family(npc_id)
        if family:
            family.remove_member(npc_id)

        # === 4. НАСЛЕДОВАНИЕ: передаём собственность ===
        heir_id = self._find_heir(npc_id)
        inheritance_log = None
        if heir_id:
            inherited = self.ownership.process_inheritance(npc_id, heir_id, self.year)
            if inherited:
                heir = self.npcs.get(heir_id)
                heir_name = heir.name if heir else heir_id
                inheritance_log = (
                    f"{heir_name} унаследовал {len(inherited)} объектов "
                    f"собственности от {npc.name}"
                )
                self.event_log.append(inheritance_log)

                # Публикуем событие передачи собственности
                transfer_event = Event(
                    event_type=EventType.PROPERTY_TRANSFERRED,
                    year=self.year,
                    month=self.month,
                    day=self.day,
                    actor_id=npc_id,
                    target_id=heir_id,
                    data={
                        "method": "наследство",
                        "property_count": len(inherited),
                    },
                    importance=EventImportance.NOTABLE,
                )
                self.event_bus.publish(transfer_event)

        # === 5. КЛАССЫ: удаляем из классовой системы ===
        npc_class = self.classes.npc_class.get(npc_id)
        if npc_class and npc_class in self.classes.classes:
            self.classes.classes[npc_class].remove_member(npc_id)
        # Удаляем из словаря npc_class
        if npc_id in self.classes.npc_class:
            del self.classes.npc_class[npc_id]

        # === 6. ВЕРОВАНИЯ: удаляем из последователей ===
        # Удаляем NPC из всех верований
        npc_beliefs = self.beliefs.npc_beliefs.get(npc_id, set()).copy()
        for belief_id in npc_beliefs:
            if belief_id in self.beliefs.beliefs:
                self.beliefs.beliefs[belief_id].adherents.discard(npc_id)
        # Удаляем запись о верованиях NPC
        if npc_id in self.beliefs.npc_beliefs:
            del self.beliefs.npc_beliefs[npc_id]

        # === 7. СОБЫТИЕ: публикуем смерть ===
        death_description = f"{npc.name} умер в возрасте {npc.age} лет ({cause})"
        death_event = Event(
            event_type=EventType.NPC_DIED,
            year=self.year,
            month=self.month,
            day=self.day,
            actor_id=npc_id,
            data={
                "cause": cause,
                "age": npc.age,
                "name": npc.name,
            },
            importance=EventImportance.NOTABLE,
            description=death_description,
        )
        self.event_bus.publish(death_event)

        return death_description

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

        # Начальные верования - сначала создаем базовое верование анимизм
        # (возникает естественно при взаимодействии с природой)
        economic_conditions = self._get_economic_conditions()
        social_conditions = self._get_social_conditions()
        initial_belief = self.beliefs.check_belief_emergence(
            economic_conditions, social_conditions, self.year
        )
        if initial_belief:
            events.append(f"Возникло верование: {initial_belief.name}")

        # Все начальные NPC разделяют базовое верование (анимизм)
        for npc in self.npcs.values():
            if "animism" in self.beliefs.beliefs:
                self.beliefs.add_belief_to_npc(npc.id, "animism")

        return events

    def _create_npc(self, is_female: bool = False,
                    family_name: str = None,
                    age: int = None) -> SimulationNPC:
        """
        Создаёт нового NPC используя унифицированную модель SimulationNPC.

        Args:
            is_female: Пол (True = женщина)
            family_name: Фамилия (для семей)
            age: Возраст (если None - случайный)

        Returns:
            SimulationNPC: Созданный NPC
        """
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

        # Создаём SimulationNPC (расширенный NPC)
        npc = SimulationNPC(
            id=npc_id,
            name=name,
            surname=family_name or "",
            gender=Gender.FEMALE if is_female else Gender.MALE,
            age=age,
            position=Position(
                self.map.width // 2 + random.randint(-5, 5),
                self.map.height // 2 + random.randint(-5, 5),
            ),
            stats=Stats(intelligence=random.randint(7, 14)),
        )

        # Инициализируем навыки (словарь для совместимости)
        npc._skill_dict = {
            "gathering": random.randint(0, 20),
            "hunting": random.randint(0, 15),
            "crafting": random.randint(0, 10),
        }

        # Легаси черты характера (для совместимости с существующим кодом)
        npc._legacy_traits = random.sample(
            ["curious", "lazy", "hardworking", "aggressive", "peaceful", "greedy", "generous"],
            k=random.randint(1, 3)
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

        Порядок обновления по марксистской архитектуре:
        1. Время и климат (окружающая среда)
        2. БАЗИС (экономика): производство, собственность, классы
        3. NPC действия (агенты реагируют на среду и базис)
        4. НАДСТРОЙКА (культура): верования, традиции, нормы
        5. Демография (рождения/смерти, потребности)

        По Марксу: базис определяет надстройку, поэтому экономика
        обновляется ДО культуры. NPC действуют в рамках экономической
        структуры, а культурные изменения следуют за их действиями.
        """
        all_events = []

        for _ in range(hours):
            # ================================================================
            # === 1. ВРЕМЯ И КЛИМАТ (окружающая среда) ===
            # ================================================================
            self.hour += 1
            is_new_day = False
            is_new_year = False

            if self.hour >= 24:
                self.hour = 0
                self.day += 1
                self.total_days += 1
                is_new_day = True

                if self.day > self.config.days_per_month:
                    self.day = 1
                    self.month += 1

                    if self.month > self.config.months_per_year:
                        self.month = 1
                        self.year += 1
                        is_new_year = True

            # Обновляем климат (раз в день)
            if is_new_day:
                climate_events = self._update_climate()
                all_events.extend(climate_events)

            # ================================================================
            # === 2. БАЗИС (экономика) - обновляется ПЕРЕД надстройкой ===
            # ================================================================

            # Производство (каждый час)
            self.production.current_season = self.climate.current_season.value
            production_events = self.production.update(1.0)
            all_events.extend(production_events)

            # Классовые конфликты и отношения (раз в день)
            if is_new_day:
                conflict_events = self._process_class_conflicts()
                all_events.extend(conflict_events)

            # ================================================================
            # === 3. NPC ДЕЙСТВИЯ (каждый час) ===
            # ================================================================
            npc_events = self._process_npc_actions()
            all_events.extend(npc_events)

            # ================================================================
            # === 4. НАДСТРОЙКА (культура) - ПОСЛЕ действий NPC ===
            # ================================================================
            if is_new_day:
                superstructure_events = self._update_superstructure()
                all_events.extend(superstructure_events)

            # ================================================================
            # === 5. ДЕМОГРАФИЯ (потребности, рождения, смерти) ===
            # ================================================================
            if is_new_day:
                demography_events = self._update_demography()
                all_events.extend(demography_events)

            # Обработка нового года (после всех дневных обновлений)
            if is_new_year:
                year_events = self._process_new_year()
                all_events.extend(year_events)

        # Ограничиваем лог
        self.event_log.extend(all_events)
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-500:]

        return all_events

    def _update_climate(self) -> List[str]:
        """
        Обновляет климат и погоду (шаг 1).

        Часть окружающей среды, обновляется первой.
        """
        events = []

        # Обновляем климат
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

        return events

    def _update_superstructure(self) -> List[str]:
        """
        Обновляет надстройку: верования, традиции, нормы (шаг 4).

        По Марксу: надстройка отражает и легитимизирует базис.
        Обновляется ПОСЛЕ действий NPC, чтобы отразить изменения
        в экономических отношениях.
        """
        events = []

        # === ТРАДИЦИИ: проверяем сезонные праздники ===
        celebration_event = self._check_season_celebration()
        if celebration_event:
            events.append(celebration_event)

        # === ТРАДИЦИИ: применяем эффекты существующих традиций ===
        self._apply_tradition_effects()

        # === ВЕРОВАНИЯ: проверяем возникновение новых ===
        economic_conditions = self._get_economic_conditions()
        social_conditions = self._get_social_conditions()

        new_belief = self.beliefs.check_belief_emergence(
            economic_conditions, social_conditions, self.year
        )
        if new_belief:
            events.append(f"Возникло верование: {new_belief.name}")

        return events

    def _update_demography(self) -> List[str]:
        """
        Обновляет демографию: потребности NPC, старение, смерти (шаг 5).

        Обновляется последней, после всех экономических и культурных
        изменений за день.
        """
        events = []

        # Собираем список NPC для обработки (чтобы избежать изменения dict во время итерации)
        npc_ids = list(self.npcs.keys())

        for npc_id in npc_ids:
            npc = self.npcs.get(npc_id)
            if not npc or not npc.is_alive:
                continue

            # Голод нарастает каждый день
            npc.hunger += 10
            if npc.hunger > 100:
                npc.health -= 5
                if npc.health <= 0:
                    # Используем централизованный обработчик смерти
                    death_event = self.handle_npc_death(npc_id, "голод")
                    if death_event:
                        events.append(death_event)
                    continue  # NPC мёртв, пропускаем остальную обработку

            # Старение (раз в год)
            if self.day == 1 and self.month == 1:
                npc.age += 1

                # Проверяем смерть от старости
                if npc.age > 60:
                    # Шанс смерти от старости увеличивается с возрастом
                    death_chance = (npc.age - 60) * 0.05  # 5% за каждый год после 60
                    if random.random() < death_chance:
                        death_event = self.handle_npc_death(npc_id, "старость")
                        if death_event:
                            events.append(death_event)
                        continue

            # Порча еды
            spoiled = npc.inventory.decay_all(1.0)

        return events

    def _process_class_conflicts(self) -> List[str]:
        """
        Обрабатывает классовые конфликты.

        По марксистской теории:
        1. Обновляем классы NPC на основе собственности
        2. Обновляем отношения между классами
        3. Обновляем существующие конфликты
        4. Проверяем возникновение новых
        5. Распространяем классовое сознание
        """
        events = []

        # Обновляем классы NPC на основе собственности
        self._update_npc_classes()

        # Обновляем отношения между классами (антагонизм и пр.)
        self.classes.update_class_relations(self.year)

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
        """
        Обновляет классовую принадлежность NPC на основе отношений собственности.

        По Марксу, класс определяется отношением к средствам производства:
        - Владеет землёй/орудиями → LANDOWNER/CRAFTSMAN (эксплуататор)
        - Не владеет → LABORER/LANDLESS (эксплуатируемый)
        """
        # Собираем данные для статистики классов
        class_wealth: Dict[ClassType, List[float]] = {}
        class_property: Dict[ClassType, List[int]] = {}

        for npc_id, npc in self.npcs.items():
            if not npc.is_alive:
                continue

            # Определяем владение средствами производства
            owns_land = self.ownership.owns_land(npc_id)
            owns_tools = self.ownership.owns_tools(npc_id)
            owns_livestock = self.ownership.owns_livestock(npc_id)

            # Богатство (по инвентарю + собственность)
            inventory_wealth = npc.inventory.total_value()
            property_wealth = self.ownership.calculate_wealth(npc_id)
            wealth = inventory_wealth + property_wealth

            # Работает ли на других (не владеет средствами производства)
            works_for_others = not (owns_land or owns_tools or owns_livestock)

            # Определяем класс на основе производственных отношений
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

            # Обновляем класс NPC
            self.classes.update_npc_class(npc_id, new_class, self.year)

            # Собираем статистику для класса
            if new_class not in class_wealth:
                class_wealth[new_class] = []
                class_property[new_class] = []

            class_wealth[new_class].append(wealth)
            property_count = len(self.ownership.get_owner_properties(npc_id))
            class_property[new_class].append(property_count)

        # Обновляем статистику классов
        self._update_class_statistics(class_wealth, class_property)

    def _update_class_statistics(
        self,
        class_wealth: Dict[ClassType, List[float]],
        class_property: Dict[ClassType, List[int]]
    ) -> None:
        """
        Обновляет статистику классов: среднее богатство, собственность, власть.

        Политическая власть зависит от:
        - Богатства класса
        - Количества средств производства
        - Размера класса (для эксплуатируемых - потенциал восстания)
        """
        for class_type, social_class in self.classes.classes.items():
            if class_type in class_wealth and class_wealth[class_type]:
                # Среднее богатство
                social_class.avg_wealth = sum(class_wealth[class_type]) / len(class_wealth[class_type])

                # Средняя собственность
                if class_type in class_property:
                    social_class.avg_property = sum(class_property[class_type]) / len(class_property[class_type])

                # Политическая власть
                # Эксплуататоры: власть от богатства и собственности
                if class_type.is_exploiter:
                    wealth_power = min(1.0, social_class.avg_wealth / 100)
                    property_power = min(1.0, social_class.avg_property / 5)
                    social_class.political_power = (wealth_power + property_power) / 2
                # Эксплуатируемые: власть от численности и сознания
                elif class_type.is_exploited:
                    size_power = min(0.5, social_class.get_size() / 20)
                    consciousness_power = social_class.class_consciousness * 0.5
                    social_class.political_power = size_power + consciousness_power
                else:
                    # Общинники и прочие
                    social_class.political_power = 0.3

    def update_base_superstructure_chain(self) -> List[str]:
        """
        Обновляет причинную цепочку: Собственность → Класс → Нормы/Идеология.

        По Марксу:
        1. Базис (экономические отношения собственности) определяет
        2. Классовую структуру, которая определяет
        3. Надстройку (нормы, идеология, верования)

        Это центральный механизм марксистской теории:
        - Изменения в собственности → переоценка классов
        - Изменения в классах → обновление норм и доминирующей идеологии
        - Доминирующая идеология → распространяется быстрее
        - Нормы, выгодные господствующему классу → соблюдаются лучше
        """
        events = []

        # Шаг 1: Обновляем классы на основе собственности
        # (вызывается из _process_class_conflicts, но для полноты цепочки)
        self._update_npc_classes()

        # Шаг 2: Обновляем отношения между классами
        self.classes.update_class_relations(self.year)

        # Шаг 2.5: Обновляем нормы на основе классовой власти
        # Нормы, выгодные господствующему классу, соблюдаются лучше
        if self.classes.classes_emerged:
            class_power = self.classes.get_class_power()
            self.norms.update_compliance_from_class_power(class_power)

        # Шаг 3: Обновляем доминирующую идеологию
        if self.classes.classes_emerged:
            # Получаем распределение власти по классам
            class_power = self.classes.get_class_power()

            # Обновляем доминирующую идеологию
            self.beliefs.update_dominant_ideology(class_power)

            # Логируем изменения в идеологии
            if self.beliefs.dominant_beliefs:
                dominant_belief_names = [
                    self.beliefs.beliefs[bid].name
                    for bid in self.beliefs.dominant_beliefs
                    if bid in self.beliefs.beliefs
                ]
                if dominant_belief_names:
                    events.append(
                        f"Доминирующая идеология: {', '.join(dominant_belief_names)}"
                    )

            # Шаг 4: Распространяем доминирующие верования быстрее
            self._spread_dominant_ideology()

        return events

    def _record_practice_success(self, practice_name: str) -> Optional[str]:
        """
        Записывает успешную практику и проверяет возникновение традиции.

        Традиции возникают из повторяющихся успешных действий.
        Когда практика повторяется достаточное количество раз,
        она становится традицией.

        Args:
            practice_name: Название практики (gathering, hunting, trading, etc.)

        Returns:
            Описание события если традиция возникла, иначе None
        """
        # Увеличиваем счётчик успешных выполнений
        self._practice_successes[practice_name] = (
            self._practice_successes.get(practice_name, 0) + 1
        )

        # Проверяем возникновение традиции
        # (требуется минимум 3 успешных повторения)
        tradition = self.traditions.check_tradition_emergence(
            repeated_event=practice_name,
            success_count=self._practice_successes[practice_name],
            year=self.year
        )

        if tradition:
            return f"Возникла традиция: {tradition.name} (из практики {practice_name})"

        return None

    def _check_season_celebration(self) -> Optional[str]:
        """
        Проверяет смену сезона и создаёт сезонный праздник.

        По мере развития общества, смена сезонов становится
        поводом для праздников (урожай, весеннее равноденствие и т.д.)

        Returns:
            Описание события если праздник создан, иначе None
        """
        current_season = self.climate.current_season

        # Проверяем смену сезона
        if self._last_season is None:
            self._last_season = current_season
            return None

        if current_season == self._last_season:
            return None

        # Сезон сменился
        self._last_season = current_season

        # Праздники возникают когда общество достаточно развито
        # и имеет излишки для празднования
        population = len([n for n in self.npcs.values() if n.is_alive])
        if population < 5:
            return None

        # Проверяем наличие традиций для этого сезона
        season_trigger = f"season:{current_season.value}"
        existing = self.traditions.get_traditions_for_trigger(season_trigger)
        if existing:
            # Традиция уже есть
            return None

        # Названия сезонных праздников
        season_celebrations = {
            Season.SPRING: ("Праздник весны", "Праздник пробуждения природы"),
            Season.SUMMER: ("Праздник лета", "Праздник солнца и плодородия"),
            Season.AUTUMN: ("Праздник урожая", "Праздник благодарности за урожай"),
            Season.WINTER: ("Праздник зимы", "Праздник выживания в холода"),
        }

        if current_season not in season_celebrations:
            return None

        # Шанс создать праздник зависит от года и благополучия
        # В ранние годы праздники возникают редко
        celebration_chance = min(0.3, self.year * 0.02)
        if random.random() > celebration_chance:
            return None

        name, description = season_celebrations[current_season]
        tradition = self.traditions.add_seasonal_celebration(
            name=name,
            season=current_season.value,
            year=self.year,
            description=description
        )

        return f"Возник праздник: {tradition.name}"

    def _apply_tradition_effects(self) -> None:
        """
        Применяет эффекты традиций к NPC.

        Традиции укрепляют социальную сплочённость и влияют на поведение.
        Участники традиций получают бонус к счастью и социальным связям.
        """
        for tradition in self.traditions.traditions.values():
            # Применяем бонус социальной сплочённости
            # Все NPC получают небольшой бонус от существующих традиций
            cohesion_bonus = tradition.social_cohesion_bonus * 0.01  # Небольшой эффект

            for npc in self.npcs.values():
                if not npc.is_alive:
                    continue

                # Традиции повышают удовлетворённость социальных потребностей
                from ..npc.needs import Need
                social_need = npc.needs.get(Need.SOCIAL)
                if social_need:
                    social_need.value = min(100, social_need.value + cohesion_bonus)

    def _spread_dominant_ideology(self) -> None:
        """
        Распространяет доминирующую идеологию среди населения.

        По Марксу: идеи господствующего класса становятся
        господствующими идеями эпохи.

        Доминирующие верования распространяются быстрее
        благодаря институциональной поддержке.
        """
        if not self.beliefs.dominant_beliefs:
            return

        # Для каждого NPC, проверяем, приняли ли они доминирующую идеологию
        for npc_id, npc in self.npcs.items():
            if not npc.is_alive:
                continue

            npc_beliefs = self.beliefs.npc_beliefs.get(npc_id, set())

            for belief_id in self.beliefs.dominant_beliefs:
                if belief_id not in npc_beliefs:
                    # Повышенный шанс принять доминирующую идеологию
                    # Модификатор зависит от класса NPC
                    npc_class = self.classes.npc_class.get(npc_id)

                    # Члены господствующего класса легче принимают свою идеологию
                    influence = 0.05  # Базовое влияние 5% за год

                    if npc_class and npc_class.is_exploiter:
                        influence *= 2.0  # Эксплуататоры легко принимают свою идеологию
                    elif npc_class and npc_class.is_exploited:
                        # Проверяем классовое сознание - высокое сознание сопротивляется
                        if npc_class in self.classes.classes:
                            consciousness = self.classes.classes[npc_class].class_consciousness
                            influence *= (1 - consciousness * 0.5)  # Сознание снижает влияние

                    # Пытаемся распространить верование
                    if random.random() < influence:
                        self.beliefs.add_belief_to_npc(npc_id, belief_id)

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

        # === ПРИЧИННАЯ ЦЕПОЧКА: Собственность → Класс → Идеология ===
        # Обновляем надстройку на основе базиса (раз в год)
        chain_events = self.update_base_superstructure_chain()
        events.extend(chain_events)

        # === ПРОВЕРКА СОГЛАСОВАННОСТИ (INT-022) ===
        # Проверяем состояние симуляции раз в год
        consistency_events = self._check_consistency()
        events.extend(consistency_events)

        return events

    def _check_consistency(self) -> List[str]:
        """
        Проверяет согласованность состояния симуляции (INT-022).

        Выполняется ежегодно для обнаружения:
        - Рассинхронизации между системами
        - Нарушений ссылочной целостности
        - Дрейфа состояния

        Возвращает список событий для лога.
        """
        events = []

        # Запускаем полную проверку
        report = validate_state_consistency(self)

        # Логируем только если есть проблемы
        if report.issues:
            # Формируем сводку
            events.append(f"[CONSISTENCY] {report.summary()}")

            # Логируем ошибки и критические проблемы
            for issue in report.issues:
                if issue.level in [ConsistencyLevel.ERROR, ConsistencyLevel.CRITICAL]:
                    events.append(f"[CONSISTENCY:{issue.level.name}] {issue.description}")
                    self.event_log.append(issue.to_log_message())

            # Предупреждения только в event_log (не перегружаем UI)
            for issue in report.get_issues_by_level(ConsistencyLevel.WARNING):
                self.event_log.append(issue.to_log_message())

        return events

    def get_consistency_report(self) -> 'ConsistencyReport':
        """
        Возвращает полный отчёт о согласованности состояния.

        Может использоваться для:
        - Отладки
        - QA-тестирования
        - Мониторинга здоровья симуляции
        """
        from .consistency import validate_state_consistency
        return validate_state_consistency(self)

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

    def _decide_action(self, npc: SimulationNPC) -> str:
        """
        Решает, что делать NPC.

        Решения модифицируются:
        - Верованиями через behavior_modifiers
        - Нормами через constraints (нормы ограничивают поведение)

        Модификаторы верований:
        - work_ethic: повышает приоритет работы
        - sharing: влияет на социализацию
        - respect_nature: влияет на собирательство
        - obedience: влияет на подчинение приказам

        Нормы:
        - mutual_aid: обязывает помогать
        - no_internal_violence: запрещает насилие
        - property_protection: запрещает захват чужого
        """
        # Приоритет: голод -> работа -> социализация

        if npc.hunger > 70:
            # Ищем еду
            if npc.inventory.get_food_amount() > 0:
                return "eat"
            return "gather_food"

        if npc.energy < 30:
            return "rest"

        # === Модификаторы поведения от верований ===
        work_ethic_mod = self.beliefs.get_behavior_modifier(npc.id, "work_ethic")
        respect_nature_mod = self.beliefs.get_behavior_modifier(npc.id, "respect_nature")
        sharing_mod = self.beliefs.get_behavior_modifier(npc.id, "sharing")

        # Работа (базовый приоритет модифицируется work_ethic)
        season = self.climate.current_season.value
        productivity = self.climate.get_season_productivity()

        # work_ethic повышает порог для работы (трудолюбивые работают больше)
        work_threshold = 0.5 - work_ethic_mod * 0.3  # work_ethic=0.3 -> порог 0.41

        # respect_nature увеличивает предпочтение собирательства над охотой
        gathering_bonus = respect_nature_mod * 0.2

        if productivity.get("gathering", 0) + gathering_bonus > work_threshold:
            return "gather"
        if productivity.get("hunting", 0) > work_threshold and npc.get_skill("hunting") > 0:
            return "hunt"

        # === Нормы влияют на социализацию ===
        # Норма взаимопомощи обязывает помогать другим
        npc_class = self.classes.npc_class.get(npc.id)
        class_name = npc_class.name if npc_class else ""
        help_tendency = self.norms.should_help(class_name)

        # sharing_mod положительный -> больше склонность к социализации
        # sharing_mod отрицательный -> меньше склонность
        # help_tendency от норм дополнительно влияет
        socialize_chance = 0.5 + sharing_mod * 0.2 + help_tendency * 0.3
        if random.random() < socialize_chance:
            return "socialize"

        # По умолчанию - собирательство (всегда полезно)
        return "gather"

    def _try_claim_land(self, npc: SimulationNPC) -> Optional[str]:
        """
        Пытается захватить землю как частную собственность.

        Условия для захвата:
        - NPC накопил достаточно ресурсов (излишек)
        - NPC находится на незанятой земле
        - Вероятность зависит от черт характера
        - НОРМЫ: норма property_protection ограничивает захват

        Возвращает описание события или None.
        """
        # === НОРМЫ: проверяем ограничения на захват ===
        npc_class = self.classes.npc_class.get(npc.id)
        class_name = npc_class.name if npc_class else ""

        # Если норма запрещает захват для этого класса - не захватываем
        if not self.norms.can_claim_property(class_name):
            # Нормы запрещают захват чужой собственности
            # Но если собственности ещё нет - норма не применяется
            if self.ownership.private_property_emerged:
                # Проверяем соблюдаемость нормы
                constraint = self.norms.get_action_constraint("claim_land", class_name)
                if random.random() < constraint:
                    return None  # NPC соблюдает норму

        # Проверяем, есть ли излишек ресурсов (признак прибавочного продукта)
        total_food = npc.inventory.get_food_amount()
        total_value = npc.inventory.total_value()

        # Нужен значимый излишек для возникновения частной собственности
        surplus_threshold = 10.0
        if total_food < surplus_threshold and total_value < surplus_threshold * 2:
            return None

        # Вероятность захвата зависит от черт характера
        base_chance = 0.001  # Базовая вероятность за тик

        # Жадные NPC чаще захватывают землю
        if "greedy" in npc.traits:
            base_chance *= 3.0

        # Агрессивные тоже более склонны к захвату
        if "aggressive" in npc.traits:
            base_chance *= 2.0

        # Щедрые реже захватывают
        if "generous" in npc.traits:
            base_chance *= 0.3

        # Больше излишков = больше шанс
        surplus_multiplier = min(3.0, total_value / surplus_threshold)
        base_chance *= surplus_multiplier

        # Проверяем шанс
        if random.random() > base_chance:
            return None

        # Пытаемся захватить землю в текущей позиции NPC
        x, y = int(npc.position.x), int(npc.position.y)

        # Захватываем как частную собственность
        prop = self.ownership.claim_land(
            x=x,
            y=y,
            claimer_id=npc.id,
            year=self.year,
            as_private=True
        )

        if prop:
            # Публикуем событие
            from .events import Event, EventType, EventImportance
            # Первое возникновение частной собственности - историческое событие
            # Последующие - важные, но не исторические
            importance = EventImportance.HISTORIC if not self.ownership.private_property_emerged else EventImportance.NOTABLE
            event = Event(
                event_type=EventType.PROPERTY_CLAIMED,
                year=self.year,
                month=self.month,
                day=self.day,
                actor_id=npc.id,
                data={
                    "property_id": prop.property_id,
                    "category": prop.category.value,
                    "location": (x, y),
                    "as_private": True,
                },
                importance=importance,
            )
            self.event_bus.publish(event)

            return f"{npc.name} захватил землю ({x}, {y}) как частную собственность!"

        return None

    def _try_property_trade(self, npc1: SimulationNPC, npc2: SimulationNPC) -> Optional[str]:
        """
        Пытается совершить торговую сделку собственностью между NPC.

        Условия для торговли:
        - Частная собственность уже возникла
        - У одного из NPC есть передаваемая собственность
        - Есть взаимная выгода (один имеет излишек собственности, другой - ресурсы)

        Возвращает описание события или None.
        """
        # Торговля возможна только после возникновения частной собственности
        if not self.ownership.private_property_emerged:
            return None

        # Базовая вероятность торговли
        base_chance = 0.005  # 0.5% за тик социализации

        # Торговые навыки увеличивают шанс
        trade_skill_1 = npc1.get_skill("trading")
        trade_skill_2 = npc2.get_skill("trading")
        avg_skill = (trade_skill_1 + trade_skill_2) / 2.0
        base_chance *= (1 + avg_skill / 50)

        # Жадные NPC чаще торгуют
        if "greedy" in npc1.traits or "greedy" in npc2.traits:
            base_chance *= 1.5

        # Проверяем шанс
        if random.random() > base_chance:
            return None

        # Получаем собственность обоих NPC
        props1 = self.ownership.get_owner_properties(npc1.id)
        props2 = self.ownership.get_owner_properties(npc2.id)

        # Фильтруем только передаваемую собственность
        tradeable1 = [p for p in props1 if p.can_transfer]
        tradeable2 = [p for p in props2 if p.can_transfer]

        # Нужна собственность хотя бы у одного
        if not tradeable1 and not tradeable2:
            return None

        # Определяем продавца и покупателя
        # Продавец: тот у кого больше собственности (излишек)
        # Покупатель: тот у кого больше ресурсов
        seller, buyer, seller_props = None, None, None

        if len(tradeable1) > len(tradeable2):
            seller, buyer = npc1, npc2
            seller_props = tradeable1
        elif len(tradeable2) > len(tradeable1):
            seller, buyer = npc2, npc1
            seller_props = tradeable2
        else:
            # Равное количество - выбираем случайно
            if tradeable1 and random.random() < 0.5:
                seller, buyer = npc1, npc2
                seller_props = tradeable1
            elif tradeable2:
                seller, buyer = npc2, npc1
                seller_props = tradeable2
            else:
                return None

        if not seller_props:
            return None

        # Покупатель должен иметь ресурсы для обмена
        buyer_resources = buyer.inventory.total_value()
        if buyer_resources < 5.0:  # Минимальная стоимость для торговли
            return None

        # Выбираем случайную собственность для обмена
        prop_to_trade = random.choice(seller_props)

        # Совершаем обмен
        success = self.ownership.transfer_property(
            property_id=prop_to_trade.property_id,
            new_owner_id=buyer.id,
            year=self.year,
            method=OwnershipTransition.TRADE
        )

        if success:
            # Покупатель отдаёт ресурсы (упрощённо - часть еды)
            trade_cost = min(5.0, buyer_resources * 0.3)
            buyer.inventory.remove(ResourceType.BERRIES, trade_cost)

            # Продавец получает "оплату" (добавляем к счастью и навыку)
            seller.set_skill("trading", seller.get_skill("trading") + 1)
            buyer.set_skill("trading", buyer.get_skill("trading") + 1)

            # Публикуем событие
            trade_event = Event(
                event_type=EventType.PROPERTY_TRANSFERRED,
                year=self.year,
                month=self.month,
                day=self.day,
                actor_id=seller.id,
                target_id=buyer.id,
                data={
                    "property_id": prop_to_trade.property_id,
                    "category": prop_to_trade.category.value,
                    "method": "обмен",
                },
                importance=EventImportance.MINOR,
            )
            self.event_bus.publish(trade_event)

            return (
                f"{seller.name} продал {prop_to_trade.category.value} "
                f"({prop_to_trade.property_id}) {buyer.name}"
            )

        return None

    def _execute_action(self, npc: SimulationNPC, action: str) -> List[str]:
        """
        Выполняет действие NPC.

        Результаты модифицируются верованиями:
        - respect_nature: бонус к собирательству
        - work_ethic: бонус к эффективности труда
        - sharing: влияет на обмен ресурсами
        - theft: влияет на захват собственности
        """
        events = []

        # === Получаем модификаторы поведения от верований ===
        respect_nature_mod = self.beliefs.get_behavior_modifier(npc.id, "respect_nature")
        work_ethic_mod = self.beliefs.get_behavior_modifier(npc.id, "work_ethic")
        sharing_mod = self.beliefs.get_behavior_modifier(npc.id, "sharing")
        theft_mod = self.beliefs.get_behavior_modifier(npc.id, "theft")

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
            skill = npc.get_skill("gathering")
            amount = 1 + skill / 50 + random.random()

            weather_mod = self.climate.current_weather.gathering_modifier
            amount *= weather_mod

            # Верования влияют на собирательство:
            # respect_nature дает бонус (духи благоволят)
            # work_ethic дает бонус к эффективности
            belief_bonus = 1.0 + respect_nature_mod * 0.2 + work_ethic_mod * 0.15
            amount *= belief_bonus

            if amount > 0.5:
                npc.inventory.add(Resource(ResourceType.BERRIES, quantity=amount))
                npc.set_skill("gathering", skill + 1)
                npc.energy -= 10
                npc.hunger += 5

                # === ТРАДИЦИИ: записываем успешную практику ===
                tradition_event = self._record_practice_success("gathering")
                if tradition_event:
                    events.append(tradition_event)

                # Шанс открыть технологию
                discovery = self.knowledge.try_discovery(
                    npc.id, "gathering", npc.intelligence, self.year
                )
                if discovery:
                    events.append(f"{npc.name} открыл: {discovery.name}!")

                # Попытка захватить землю при накоплении излишка (INT-002)
                # theft_mod отрицательный = меньше склонность к захвату
                # (property_sacred верование снижает желание "красть" землю у общины)
                if theft_mod >= -0.3:  # Сильное табу на "кражу" блокирует захват
                    claim_event = self._try_claim_land(npc)
                    if claim_event:
                        events.append(claim_event)

        elif action == "hunt":
            skill = npc.get_skill("hunting")
            # work_ethic повышает шанс успешной охоты
            success_chance = 0.3 + skill / 200 + work_ethic_mod * 0.1
            success = random.random() < success_chance

            if success:
                amount = 2 + skill / 30
                # work_ethic дает бонус к добыче
                amount *= (1.0 + work_ethic_mod * 0.15)
                npc.inventory.add(Resource(ResourceType.MEAT, quantity=amount))
                npc.set_skill("hunting", skill + 1)
                events.append(f"{npc.name} добыл дичь")

                # === ТРАДИЦИИ: записываем успешную практику ===
                tradition_event = self._record_practice_success("hunting")
                if tradition_event:
                    events.append(tradition_event)

                # Попытка захватить землю при накоплении излишка (INT-002)
                # theft_mod влияет на склонность к захвату
                if theft_mod >= -0.3:
                    claim_event = self._try_claim_land(npc)
                    if claim_event:
                        events.append(claim_event)

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
                # respect_elders влияет на передачу традиционных знаний
                respect_elders_mod = self.beliefs.get_behavior_modifier(npc.id, "respect_elders")
                tradition_mod = self.beliefs.get_behavior_modifier(npc.id, "tradition")

                my_knowledge = self.knowledge.get_npc_knowledge(npc.id)
                for tech_id in my_knowledge:
                    teaching_skill = npc.get_skill("teaching") or 25  # Default if not set
                    # Верования влияют на эффективность передачи знаний
                    knowledge_bonus = 1.0 + respect_elders_mod * 0.2 + tradition_mod * 0.1
                    if self.knowledge.transfer_knowledge(
                            npc.id, other.id, tech_id, 1.0,
                            teaching_skill / 50 * knowledge_bonus,
                            other.intelligence
                    ):
                        events.append(f"{npc.name} научил {other.name}: {tech_id}")

                # Распространение верований
                my_beliefs = self.beliefs.npc_beliefs.get(npc.id, set())
                for belief_id in my_beliefs:
                    self.beliefs.spread_belief(belief_id, npc.id, other.id)

                # Распространение классового сознания (если классы возникли)
                if self.classes.classes_emerged:
                    # obedience снижает распространение сознания
                    # rebellion повышает
                    obedience_mod = self.beliefs.get_behavior_modifier(npc.id, "obedience")
                    rebellion_mod = self.beliefs.get_behavior_modifier(npc.id, "rebellion")
                    consciousness_multiplier = 1.0 - obedience_mod * 0.3 + rebellion_mod * 0.3

                    self.classes.spread_consciousness(
                        npc.id,
                        other.id,
                        belief_system=self.beliefs,
                        relationship_strength=0.5 * max(0.1, consciousness_multiplier)
                    )

                # Попытка торговли собственностью
                # sharing_mod влияет на готовность к обмену
                if sharing_mod > -0.5:  # Сильный антиобщественный настрой блокирует торговлю
                    trade_event = self._try_property_trade(npc, other)
                    if trade_event:
                        events.append(trade_event)
                        # === ТРАДИЦИИ: записываем успешную практику ===
                        tradition_event = self._record_practice_success("trading")
                        if tradition_event:
                            events.append(tradition_event)

                # === Возможность поделиться ресурсами ===
                # НОРМЫ: норма mutual_aid обязывает делиться
                # Верования: sharing_mod дополнительно влияет
                npc_class = self.classes.npc_class.get(npc.id)
                class_name = npc_class.name if npc_class else ""
                norm_help = self.norms.should_help(class_name)

                # Базовый шанс от норм + модификатор от верований
                share_chance = norm_help * 0.2 + sharing_mod * 0.2

                other_hungry = other.hunger > 60
                npc_has_food = npc.inventory.get_food_amount() > 3

                if other_hungry and npc_has_food and random.random() < share_chance:
                    # Делимся едой
                    shared = npc.inventory.remove(ResourceType.BERRIES, 1)
                    if shared:
                        other.inventory.add(Resource(ResourceType.BERRIES, quantity=1))
                        events.append(f"{npc.name} поделился едой с {other.name}")
                        # === ТРАДИЦИИ: записываем успешную практику ===
                        tradition_event = self._record_practice_success("sharing")
                        if tradition_event:
                            events.append(tradition_event)

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

        # Традиции
        tradition_stats = self.traditions.get_statistics()
        if tradition_stats["total"] > 0:
            lines.append("")
            lines.append("Традиции:")
            for tradition in self.traditions.traditions.values():
                lines.append(f"  {tradition.name} ({tradition.tradition_type.value})")

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
