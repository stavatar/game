"""
Система производства - преобразование труда и ресурсов в продукт.

Ключевые понятия:
- Труд - источник стоимости
- Орудия труда - повышают производительность
- Прибавочный продукт - излишек сверх необходимого
- Эксплуатация - присвоение прибавочного продукта
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto
import random

from .resources import ResourceType, Resource, Inventory


class LaborType(Enum):
    """Типы труда"""
    GATHERING = "собирательство"
    HUNTING = "охота"
    FISHING = "рыболовство"
    FARMING = "земледелие"
    HERDING = "скотоводство"
    CRAFTING = "ремесло"
    BUILDING = "строительство"
    COOKING = "приготовление пищи"
    MINING = "добыча руды"


@dataclass
class ProductionMethod:
    """
    Способ производства - рецепт преобразования ресурсов.

    Определяет:
    - Какие ресурсы нужны
    - Какие орудия используются
    - Что получается на выходе
    - Сколько труда требуется
    """
    id: str
    name: str
    labor_type: LaborType

    # Входные ресурсы (тип -> количество)
    inputs: Dict[str, float] = field(default_factory=dict)

    # Выходные ресурсы (тип -> количество)
    outputs: Dict[str, float] = field(default_factory=dict)

    # Требуемые орудия (бонус к производительности)
    required_tools: List[str] = field(default_factory=list)
    tool_bonus: float = 0.5            # Бонус от орудий

    # Время и сложность
    base_hours: float = 4.0            # Базовое время в часах
    skill_requirement: int = 0         # Требуемый уровень навыка

    # Требуемые технологии
    required_technologies: List[str] = field(default_factory=list)

    # Условия
    requires_water: bool = False
    requires_fire: bool = False
    seasonal: List[str] = field(default_factory=list)  # В какие сезоны доступно


# === Определяем методы производства ===

PRODUCTION_METHODS: Dict[str, ProductionMethod] = {}


def _register_method(method: ProductionMethod) -> None:
    PRODUCTION_METHODS[method.id] = method


# Собирательство
_register_method(ProductionMethod(
    id="gather_berries",
    name="сбор ягод",
    labor_type=LaborType.GATHERING,
    outputs={"berries": 3.0},
    base_hours=2.0,
    seasonal=["весна", "лето", "осень"],
))

_register_method(ProductionMethod(
    id="gather_mushrooms",
    name="сбор грибов",
    labor_type=LaborType.GATHERING,
    outputs={"mushrooms": 2.0},
    base_hours=3.0,
    seasonal=["лето", "осень"],
))

_register_method(ProductionMethod(
    id="gather_fiber",
    name="сбор волокон",
    labor_type=LaborType.GATHERING,
    outputs={"fiber": 2.0},
    base_hours=4.0,
    seasonal=["лето", "осень"],
))

_register_method(ProductionMethod(
    id="gather_wood",
    name="сбор дров",
    labor_type=LaborType.GATHERING,
    outputs={"wood": 3.0},
    required_tools=["stone_tool", "axe"],
    tool_bonus=1.0,
    base_hours=4.0,
))

# Охота
_register_method(ProductionMethod(
    id="hunt_small",
    name="охота на мелкую дичь",
    labor_type=LaborType.HUNTING,
    outputs={"meat": 2.0, "leather": 0.5},
    required_tools=["spear", "bow"],
    tool_bonus=0.8,
    base_hours=6.0,
    required_technologies=["basic_hunting"],
))

_register_method(ProductionMethod(
    id="hunt_large",
    name="охота на крупную дичь",
    labor_type=LaborType.HUNTING,
    outputs={"meat": 8.0, "leather": 2.0, "bone": 3.0},
    required_tools=["spear", "bow"],
    tool_bonus=1.0,
    base_hours=10.0,
    skill_requirement=3,
    required_technologies=["basic_hunting"],
))

# Рыболовство
_register_method(ProductionMethod(
    id="fish_basic",
    name="рыбная ловля",
    labor_type=LaborType.FISHING,
    outputs={"fish": 3.0},
    requires_water=True,
    base_hours=4.0,
    required_technologies=["fishing"],
))

# Земледелие
_register_method(ProductionMethod(
    id="plant_grain",
    name="посев зерна",
    labor_type=LaborType.FARMING,
    inputs={"grain": 1.0},   # Семена
    outputs={"grain": 6.0},  # Урожай
    required_tools=["stone_tool", "wooden_tool"],
    tool_bonus=0.5,
    base_hours=8.0,
    seasonal=["весна"],
    required_technologies=["agriculture_basic"],
))

_register_method(ProductionMethod(
    id="harvest",
    name="сбор урожая",
    labor_type=LaborType.FARMING,
    outputs={"grain": 10.0},
    required_tools=["stone_tool"],
    tool_bonus=0.3,
    base_hours=6.0,
    seasonal=["осень"],
    required_technologies=["agriculture_basic"],
))

# Ремесло
_register_method(ProductionMethod(
    id="make_stone_tool",
    name="изготовление каменного орудия",
    labor_type=LaborType.CRAFTING,
    inputs={"stone": 2.0, "wood": 1.0},
    outputs={"stone_tool": 1.0},
    base_hours=3.0,
    required_technologies=["stone_knapping"],
))

_register_method(ProductionMethod(
    id="make_spear",
    name="изготовление копья",
    labor_type=LaborType.CRAFTING,
    inputs={"wood": 2.0, "stone": 1.0},
    outputs={"spear": 1.0},
    base_hours=4.0,
    required_technologies=["stone_knapping", "basic_hunting"],
))

_register_method(ProductionMethod(
    id="make_bow",
    name="изготовление лука",
    labor_type=LaborType.CRAFTING,
    inputs={"wood": 3.0, "fiber": 2.0},
    outputs={"bow": 1.0},
    base_hours=6.0,
    skill_requirement=2,
    required_technologies=["bow_arrow"],
))

_register_method(ProductionMethod(
    id="make_pottery",
    name="гончарное дело",
    labor_type=LaborType.CRAFTING,
    inputs={"clay": 3.0},
    outputs={"pottery": 2.0},
    requires_fire=True,
    base_hours=5.0,
    required_technologies=["pottery"],
))

_register_method(ProductionMethod(
    id="make_cloth",
    name="ткачество",
    labor_type=LaborType.CRAFTING,
    inputs={"fiber": 4.0},
    outputs={"cloth": 1.0},
    base_hours=8.0,
    required_technologies=["weaving"],
))

_register_method(ProductionMethod(
    id="smelt_bronze",
    name="выплавка бронзы",
    labor_type=LaborType.CRAFTING,
    inputs={"ore": 5.0, "wood": 3.0},
    outputs={"bronze": 2.0},
    requires_fire=True,
    base_hours=10.0,
    skill_requirement=4,
    required_technologies=["bronze_working"],
))

# Приготовление пищи
_register_method(ProductionMethod(
    id="cook_meat",
    name="приготовление мяса",
    labor_type=LaborType.COOKING,
    inputs={"meat": 2.0},
    outputs={"meat": 2.5},  # Готовое мясо ценнее
    requires_fire=True,
    base_hours=1.0,
    required_technologies=["fire_making"],
))


@dataclass
class ProductionResult:
    """Результат производства"""
    success: bool
    resources_produced: Dict[str, float] = field(default_factory=dict)
    resources_consumed: Dict[str, float] = field(default_factory=dict)
    hours_spent: float = 0.0
    efficiency: float = 1.0
    experience_gained: int = 0


@dataclass
class Production:
    """
    Система производства.

    Обрабатывает производственные процессы,
    вычисляет эффективность и результаты труда.

    Climate -> Production Link:
    Климат влияет на продуктивность всех типов производства:
    - Сезон определяет базовую доступность (некоторые активности сезонны)
    - Погодные условия модифицируют эффективность
    - Катаклизмы могут полностью блокировать производство

    Territory -> Economics Link:
    Территория влияет на экономическую деятельность:
    - Плодородность тайла влияет на земледелие и собирательство
    - Тип территории определяет доступные ресурсы
    - Наличие воды влияет на рыболовство
    - Лес улучшает охоту и собирательство
    """

    # Бонусы от технологий
    tech_bonuses: Dict[str, float] = field(default_factory=dict)

    # Статистика производства
    total_production_hours: float = 0.0
    total_resources_produced: Dict[str, float] = field(default_factory=dict)
    total_resources_consumed: Dict[str, float] = field(default_factory=dict)

    # Текущий сезон (устанавливается симуляцией)
    current_season: str = ""

    # Климатические модификаторы по типам деятельности
    # Обновляются симуляцией из ClimateSystem.get_season_productivity()
    climate_modifiers: Dict[str, float] = field(default_factory=lambda: {
        "farming": 1.0,
        "hunting": 1.0,
        "gathering": 1.0,
        "fishing": 1.0,
    })

    # Маппинг типов труда на климатические категории
    _LABOR_TO_CLIMATE: Dict[LaborType, str] = field(default=None, repr=False)

    # Territory -> Economics: маппинг типов территории на модификаторы производства
    # Формат: {terrain_name: {labor_type: modifier}}
    _TERRAIN_MODIFIERS: Dict[str, Dict[str, float]] = field(default=None, repr=False)

    def __post_init__(self):
        """Инициализация после создания"""
        # Маппинг типов труда на климатические категории
        self._LABOR_TO_CLIMATE = {
            LaborType.GATHERING: "gathering",
            LaborType.HUNTING: "hunting",
            LaborType.FISHING: "fishing",
            LaborType.FARMING: "farming",
            LaborType.HERDING: "farming",  # Скотоводство зависит от климата как фермерство
            LaborType.CRAFTING: None,      # Ремесло не зависит напрямую от погоды
            LaborType.BUILDING: None,      # Строительство слабо зависит от погоды
            LaborType.COOKING: None,       # Готовка не зависит от погоды
            LaborType.MINING: None,        # Добыча руды не зависит от погоды
        }

        # Territory -> Economics: модификаторы по типам территории
        # Ключ - название территории (из TerrainType), значение - {labor_type: modifier}
        self._TERRAIN_MODIFIERS = {
            "WATER": {
                "gathering": 0.0,   # Нельзя собирать в воде
                "hunting": 0.0,     # Нельзя охотиться в воде
                "fishing": 2.0,     # Отличная рыбалка
                "farming": 0.0,     # Нельзя фермить в воде
                "mining": 0.0,      # Нельзя добывать в воде
            },
            "GRASSLAND": {
                "gathering": 1.0,   # Базовое собирательство
                "hunting": 1.2,     # Хорошая охота (видно добычу)
                "fishing": 0.0,     # Нет воды
                "farming": 1.3,     # Отличное фермерство
                "mining": 0.5,      # Мало камней
            },
            "FOREST": {
                "gathering": 1.5,   # Богатое собирательство (ягоды, грибы)
                "hunting": 1.3,     # Хорошая охота (много дичи)
                "fishing": 0.0,     # Нет воды
                "farming": 0.6,     # Слабое фермерство (тень)
                "mining": 0.3,      # Мало камней
            },
            "DENSE_FOREST": {
                "gathering": 1.8,   # Очень богатое собирательство
                "hunting": 1.0,     # Обычная охота (сложно преследовать)
                "fishing": 0.0,     # Нет воды
                "farming": 0.2,     # Почти невозможно фермить
                "mining": 0.2,      # Очень мало камней
            },
            "HILL": {
                "gathering": 0.7,   # Слабое собирательство
                "hunting": 0.9,     # Немного хуже охота
                "fishing": 0.0,     # Нет воды
                "farming": 0.5,     # Терассное земледелие сложнее
                "mining": 1.5,      # Хорошая добыча (камни, руда)
            },
            "MOUNTAIN": {
                "gathering": 0.3,   # Очень слабое собирательство
                "hunting": 0.5,     # Сложная охота
                "fishing": 0.0,     # Нет воды
                "farming": 0.0,     # Невозможно фермить
                "mining": 2.0,      # Отличная добыча
            },
            "SWAMP": {
                "gathering": 1.2,   # Хорошее собирательство (ягоды, травы)
                "hunting": 0.6,     # Сложная охота
                "fishing": 1.3,     # Хорошая рыбалка
                "farming": 0.1,     # Почти невозможно фермить
                "mining": 0.0,      # Нельзя добывать
            },
            "DESERT": {
                "gathering": 0.4,   # Слабое собирательство
                "hunting": 0.8,     # Охота возможна (кочевники)
                "fishing": 0.0,     # Нет воды
                "farming": 0.3,     # Сложное фермерство (нет воды)
                "mining": 0.8,      # Есть камни
            },
        }

    def update_climate_modifiers(self, modifiers: Dict[str, float]) -> None:
        """
        Обновляет климатические модификаторы из ClimateSystem.

        Вызывается симуляцией при обновлении климата.

        Args:
            modifiers: Словарь {тип_деятельности: модификатор}
                      из ClimateSystem.get_season_productivity()
        """
        self.climate_modifiers.update(modifiers)

    def get_climate_modifier(self, labor_type: LaborType) -> float:
        """
        Возвращает климатический модификатор для типа труда.

        Args:
            labor_type: Тип труда

        Returns:
            Модификатор производительности (0.0-2.0+)
            1.0 = нормальные условия
            <1.0 = неблагоприятные условия
            >1.0 = благоприятные условия
        """
        climate_category = self._LABOR_TO_CLIMATE.get(labor_type)
        if climate_category is None:
            # Этот тип труда не зависит от климата
            return 1.0

        return self.climate_modifiers.get(climate_category, 1.0)

    def get_terrain_modifier(
        self,
        terrain_name: str,
        labor_type: LaborType,
        fertility: float = 1.0
    ) -> float:
        """
        Territory -> Economics Link:
        Возвращает модификатор производительности для типа территории.

        Модификатор зависит от:
        - Базового модификатора для данного типа территории и труда
        - Плодородности тайла (для земледелия и собирательства)

        Args:
            terrain_name: Название типа территории (из TerrainType.name)
            labor_type: Тип труда
            fertility: Плодородность тайла (0.0-1.0)

        Returns:
            Модификатор производительности (0.0-2.0+)
            0.0 = деятельность невозможна на этой территории
            1.0 = нормальные условия
            >1.0 = благоприятные условия
        """
        # Получаем модификаторы для этого типа территории
        terrain_mods = self._TERRAIN_MODIFIERS.get(terrain_name, {})

        # Определяем категорию труда для поиска модификатора
        labor_category = self._LABOR_TO_CLIMATE.get(labor_type)
        if labor_category is None:
            # Этот тип труда (ремесло, готовка и т.п.) не зависит от территории
            return 1.0

        # Базовый модификатор территории
        base_modifier = terrain_mods.get(labor_category, 1.0)

        # Плодородность влияет на земледелие и собирательство
        if labor_type in [LaborType.FARMING, LaborType.GATHERING]:
            # Применяем модификатор плодородности
            # fertility 0.0 -> 0.5x, fertility 1.0 -> 1.5x
            fertility_modifier = 0.5 + fertility
            base_modifier *= fertility_modifier

        return base_modifier

    def get_terrain_resources(self, terrain_name: str) -> List[str]:
        """
        Territory -> Economics Link:
        Возвращает список доступных ресурсов для данного типа территории.

        Args:
            terrain_name: Название типа территории

        Returns:
            Список названий ресурсов, доступных на этой территории
        """
        # Маппинг типов территории на доступные ресурсы
        # Основано на base_resources из TerrainProperties
        terrain_resources = {
            "WATER": ["fish", "water"],
            "GRASSLAND": ["berries", "meat", "fiber"],
            "FOREST": ["wood", "meat", "berries", "mushrooms"],
            "DENSE_FOREST": ["wood", "meat", "berries", "mushrooms", "honey"],
            "HILL": ["stone", "ore", "berries"],
            "MOUNTAIN": ["stone", "ore", "gems"],
            "SWAMP": ["berries", "herbs", "fish"],
            "DESERT": ["meat", "fiber"],
        }

        return terrain_resources.get(terrain_name, ["berries"])

    def is_resource_available(self, terrain_name: str, resource_name: str) -> bool:
        """
        Territory -> Economics Link:
        Проверяет, доступен ли ресурс на данной территории.

        Args:
            terrain_name: Название типа территории
            resource_name: Название ресурса (в нижнем регистре)

        Returns:
            True если ресурс доступен на этой территории
        """
        available = self.get_terrain_resources(terrain_name)
        return resource_name.lower() in available

    def update(self, delta_hours: float = 1.0) -> List[str]:
        """
        Обновляет систему производства.

        Вызывается из главного цикла симуляции.
        Обрабатывает глобальные производственные процессы.

        Args:
            delta_hours: Количество часов с последнего обновления

        Returns:
            Список событий производства
        """
        events = []

        # Учитываем время производства
        self.total_production_hours += delta_hours

        return events

    def record_production(self, result: 'ProductionResult') -> None:
        """
        Записывает результат производства в статистику.

        Args:
            result: Результат производства
        """
        if not result.success:
            return

        for resource, amount in result.resources_produced.items():
            self.total_resources_produced[resource] = (
                self.total_resources_produced.get(resource, 0.0) + amount
            )

        for resource, amount in result.resources_consumed.items():
            self.total_resources_consumed[resource] = (
                self.total_resources_consumed.get(resource, 0.0) + amount
            )

    def get_statistics(self) -> Dict:
        """
        Возвращает статистику производства.

        Returns:
            Словарь со статистикой
        """
        return {
            "total_hours": self.total_production_hours,
            "produced": dict(self.total_resources_produced),
            "consumed": dict(self.total_resources_consumed),
            "tech_bonuses": dict(self.tech_bonuses),
        }

    def calculate_productivity(self,
                               method: ProductionMethod,
                               worker_skill: int = 0,
                               has_tool: bool = False,
                               tool_quality: float = 1.0,
                               weather_modifier: float = None,
                               terrain_name: str = None,
                               terrain_fertility: float = None) -> float:
        """
        Вычисляет производительность труда.

        Climate -> Production Link:
        Если weather_modifier не указан явно, берётся из climate_modifiers
        на основе типа труда (labor_type) метода производства.

        Territory -> Economics Link:
        Если terrain_name указан, применяется модификатор территории.
        terrain_fertility используется для земледелия и собирательства.

        Args:
            method: Метод производства
            worker_skill: Уровень навыка работника (0-100)
            has_tool: Есть ли подходящий инструмент
            tool_quality: Качество инструмента (0.0-1.0)
            weather_modifier: Явный модификатор погоды (если None - из climate_modifiers)
            terrain_name: Название типа территории (если None - не применяется)
            terrain_fertility: Плодородность тайла (0.0-1.0, если None - 0.5)

        Returns:
            Множитель к базовому выходу (1.0 = 100% эффективности)
        """
        productivity = 1.0

        # Бонус от навыка
        skill_bonus = 1.0 + (worker_skill * 0.1)
        productivity *= skill_bonus

        # Бонус от орудий
        if has_tool and method.required_tools:
            tool_multiplier = 1.0 + (method.tool_bonus * tool_quality)
            productivity *= tool_multiplier

        # Climate -> Production: климатический модификатор
        # Если не передан явно, получаем из climate_modifiers на основе типа труда
        if weather_modifier is None:
            weather_modifier = self.get_climate_modifier(method.labor_type)
        productivity *= weather_modifier

        # Territory -> Economics: модификатор территории
        if terrain_name is not None:
            fertility = terrain_fertility if terrain_fertility is not None else 0.5
            terrain_modifier = self.get_terrain_modifier(
                terrain_name, method.labor_type, fertility
            )
            productivity *= terrain_modifier

        # Технологические бонусы
        for tech in method.required_technologies:
            if tech in self.tech_bonuses:
                productivity *= (1.0 + self.tech_bonuses[tech])

        return productivity

    def can_produce(self,
                    method: ProductionMethod,
                    inventory: Inventory,
                    known_technologies: set,
                    season: str = None,
                    has_fire: bool = False,
                    near_water: bool = False,
                    terrain_name: str = None,
                    terrain_fertility: float = None) -> Tuple[bool, str]:
        """
        Проверяет, можно ли произвести.

        Climate -> Production Link:
        - Сезонные ограничения проверяются через current_season
        - Климатический модификатор проверяется: если 0, производство невозможно

        Territory -> Economics Link:
        - Тип территории может блокировать производство
        - Например: рыбалка требует воды, фермерство требует плодородной земли

        Возвращает (возможно, причина_если_нет)
        """
        # Проверяем технологии
        for tech in method.required_technologies:
            if tech not in known_technologies:
                return False, f"требуется технология: {tech}"

        # Проверяем входные ресурсы
        for resource_name, amount in method.inputs.items():
            try:
                res_type = ResourceType[resource_name.upper()]
                if not inventory.has_enough(res_type, amount):
                    return False, f"недостаточно {resource_name}"
            except KeyError:
                pass

        # Проверяем сезон (используем переданный или current_season)
        check_season = season or self.current_season
        if method.seasonal and check_season:
            if check_season not in method.seasonal:
                return False, f"только в сезоны: {', '.join(method.seasonal)}"

        # Climate -> Production: проверяем, позволяет ли климат
        climate_mod = self.get_climate_modifier(method.labor_type)
        if climate_mod <= 0.0:
            # Климатические условия полностью блокируют этот тип работы
            climate_category = self._LABOR_TO_CLIMATE.get(method.labor_type, "работу")
            return False, f"погода не позволяет {climate_category}"

        # Territory -> Economics: проверяем, позволяет ли территория
        if terrain_name is not None:
            fertility = terrain_fertility if terrain_fertility is not None else 0.5
            terrain_mod = self.get_terrain_modifier(
                terrain_name, method.labor_type, fertility
            )
            if terrain_mod <= 0.0:
                # Территория не позволяет этот тип работы
                labor_name = method.labor_type.value
                terrain_readable = terrain_name.lower().replace("_", " ")
                return False, f"{labor_name} невозможно на территории: {terrain_readable}"

        # Проверяем условия
        if method.requires_fire and not has_fire:
            return False, "требуется огонь"

        if method.requires_water and not near_water:
            return False, "требуется вода рядом"

        return True, ""

    def produce(self,
                method: ProductionMethod,
                inventory: Inventory,
                worker_skill: int = 0,
                tool: Optional[Resource] = None,
                weather_modifier: float = 1.0,
                hours_available: float = 8.0) -> ProductionResult:
        """
        Выполняет производство.

        Возвращает результат с произведёнными ресурсами.
        """
        result = ProductionResult(success=False)

        # Проверяем время
        if hours_available < method.base_hours * 0.5:
            return result

        # Потребляем входные ресурсы
        for resource_name, amount in method.inputs.items():
            try:
                res_type = ResourceType[resource_name.upper()]
                taken = inventory.remove(res_type, amount)
                if taken:
                    result.resources_consumed[resource_name] = amount
                else:
                    # Откатываем
                    for r_name, r_amount in result.resources_consumed.items():
                        rt = ResourceType[r_name.upper()]
                        inventory.add(Resource(rt, r_amount))
                    return result
            except KeyError:
                pass

        # Вычисляем производительность
        has_tool = tool is not None
        tool_quality = tool.quality if tool else 0.0

        productivity = self.calculate_productivity(
            method, worker_skill, has_tool, tool_quality, weather_modifier
        )

        # Вычисляем время работы
        actual_hours = min(hours_available, method.base_hours)
        time_efficiency = actual_hours / method.base_hours

        # Финальная эффективность
        efficiency = productivity * time_efficiency

        # Добавляем случайность (±20%)
        efficiency *= random.uniform(0.8, 1.2)

        result.efficiency = efficiency
        result.hours_spent = actual_hours

        # Производим ресурсы
        for resource_name, base_amount in method.outputs.items():
            produced_amount = base_amount * efficiency

            try:
                res_type = ResourceType[resource_name.upper()]
                resource = Resource(
                    resource_type=res_type,
                    quantity=produced_amount,
                    quality=min(1.0, 0.5 + worker_skill * 0.1),
                )
                inventory.add(resource)
                result.resources_produced[resource_name] = produced_amount
            except KeyError:
                pass

        # Износ орудия
        if tool:
            tool.durability -= 0.02 * actual_hours

        # Опыт
        result.experience_gained = int(actual_hours * (1 + method.skill_requirement * 0.5))

        result.success = True
        return result

    def get_available_methods(self,
                              known_technologies: set,
                              season: str = None) -> List[ProductionMethod]:
        """Возвращает доступные методы производства"""
        available = []

        for method in PRODUCTION_METHODS.values():
            # Проверяем технологии
            if all(t in known_technologies for t in method.required_technologies):
                # Проверяем сезон
                if not method.seasonal or season in method.seasonal:
                    available.append(method)

        return available

    def calculate_surplus(self,
                          produced: Dict[str, float],
                          consumed_for_survival: Dict[str, float]) -> Dict[str, float]:
        """
        Вычисляет прибавочный продукт.

        Прибавочный продукт = произведённое - необходимое для выживания
        """
        surplus = {}

        for resource, amount in produced.items():
            needed = consumed_for_survival.get(resource, 0)
            if amount > needed:
                surplus[resource] = amount - needed

        return surplus

    def calculate_exploitation_rate(self,
                                    total_produced: float,
                                    worker_keeps: float) -> float:
        """
        Вычисляет норму эксплуатации.

        По Марксу: m' = m / v
        где m = прибавочная стоимость, v = необходимый продукт

        Возвращает долю отчуждённого продукта (0-1)
        """
        if total_produced <= 0:
            return 0.0

        surplus = total_produced - worker_keeps
        if surplus <= 0:
            return 0.0

        return surplus / total_produced
