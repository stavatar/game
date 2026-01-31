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
    """

    # Бонусы от технологий
    tech_bonuses: Dict[str, float] = field(default_factory=dict)

    def calculate_productivity(self,
                               method: ProductionMethod,
                               worker_skill: int = 0,
                               has_tool: bool = False,
                               tool_quality: float = 1.0,
                               weather_modifier: float = 1.0) -> float:
        """
        Вычисляет производительность труда.

        Возвращает множитель к базовому выходу.
        """
        productivity = 1.0

        # Бонус от навыка
        skill_bonus = 1.0 + (worker_skill * 0.1)
        productivity *= skill_bonus

        # Бонус от орудий
        if has_tool and method.required_tools:
            tool_multiplier = 1.0 + (method.tool_bonus * tool_quality)
            productivity *= tool_multiplier

        # Погодный модификатор
        productivity *= weather_modifier

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
                    near_water: bool = False) -> Tuple[bool, str]:
        """
        Проверяет, можно ли произвести.

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

        # Проверяем сезон
        if method.seasonal and season:
            if season not in method.seasonal:
                return False, f"только в сезоны: {', '.join(method.seasonal)}"

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
