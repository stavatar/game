"""
Система ресурсов - материальная основа экономики.

Ресурсы делятся на:
- Природные (добываются из мира)
- Произведённые (создаются трудом)
- Средства производства (используются для создания других ресурсов)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto


class ResourceCategory(Enum):
    """Категории ресурсов"""
    NATURAL = "природный"              # Добывается из природы
    FOOD = "еда"                       # Потребляется для выживания
    MATERIAL = "материал"              # Используется для производства
    TOOL = "орудие"                    # Средство производства
    LUXURY = "роскошь"                 # Престижный товар
    KNOWLEDGE = "знание"               # Нематериальный ресурс


class ResourceType(Enum):
    """Типы ресурсов"""
    # === Природные ресурсы ===
    WATER = ("вода", ResourceCategory.NATURAL, True)
    WOOD = ("древесина", ResourceCategory.MATERIAL, True)
    STONE = ("камень", ResourceCategory.MATERIAL, True)
    CLAY = ("глина", ResourceCategory.MATERIAL, True)
    ORE = ("руда", ResourceCategory.MATERIAL, False)
    FLINT = ("кремень", ResourceCategory.MATERIAL, False)

    # === Еда ===
    BERRIES = ("ягоды", ResourceCategory.FOOD, True)
    MUSHROOMS = ("грибы", ResourceCategory.FOOD, True)
    MEAT = ("мясо", ResourceCategory.FOOD, False)
    FISH = ("рыба", ResourceCategory.FOOD, True)
    GRAIN = ("зерно", ResourceCategory.FOOD, False)
    VEGETABLES = ("овощи", ResourceCategory.FOOD, False)
    HONEY = ("мёд", ResourceCategory.FOOD, True)
    MILK = ("молоко", ResourceCategory.FOOD, False)

    # === Материалы ===
    LEATHER = ("кожа", ResourceCategory.MATERIAL, False)
    BONE = ("кость", ResourceCategory.MATERIAL, False)
    FIBER = ("волокно", ResourceCategory.MATERIAL, True)
    IRON = ("железо", ResourceCategory.MATERIAL, False)
    BRONZE = ("бронза", ResourceCategory.MATERIAL, False)
    CLOTH = ("ткань", ResourceCategory.MATERIAL, False)
    POTTERY = ("керамика", ResourceCategory.MATERIAL, False)

    # === Орудия труда ===
    STONE_TOOL = ("каменное орудие", ResourceCategory.TOOL, False)
    BONE_TOOL = ("костяное орудие", ResourceCategory.TOOL, False)
    WOODEN_TOOL = ("деревянное орудие", ResourceCategory.TOOL, False)
    BRONZE_TOOL = ("бронзовое орудие", ResourceCategory.TOOL, False)
    IRON_TOOL = ("железное орудие", ResourceCategory.TOOL, False)

    # === Оружие ===
    SPEAR = ("копьё", ResourceCategory.TOOL, False)
    BOW = ("лук", ResourceCategory.TOOL, False)
    AXE = ("топор", ResourceCategory.TOOL, False)
    SWORD = ("меч", ResourceCategory.TOOL, False)

    # === Роскошь ===
    JEWELRY = ("украшения", ResourceCategory.LUXURY, False)
    FINE_CLOTHES = ("дорогая одежда", ResourceCategory.LUXURY, False)
    ART = ("предмет искусства", ResourceCategory.LUXURY, False)

    def __init__(self, russian_name: str, category: ResourceCategory, renewable: bool):
        self.russian_name = russian_name
        self.category = category
        self.renewable = renewable

    @classmethod
    def get_by_category(cls, category: ResourceCategory) -> List['ResourceType']:
        """Возвращает ресурсы указанной категории"""
        return [r for r in cls if r.category == category]

    @classmethod
    def get_food_types(cls) -> List['ResourceType']:
        """Возвращает типы еды"""
        return cls.get_by_category(ResourceCategory.FOOD)

    @classmethod
    def get_tools(cls) -> List['ResourceType']:
        """Возвращает типы орудий"""
        return cls.get_by_category(ResourceCategory.TOOL)


@dataclass
class Resource:
    """
    Экземпляр ресурса.

    Каждый ресурс имеет:
    - Тип и количество
    - Качество (влияет на эффективность)
    - Историю (кто создал, когда)
    """
    resource_type: ResourceType
    quantity: float = 1.0
    quality: float = 1.0              # 0-1, влияет на эффективность

    # История ресурса
    creator_id: Optional[str] = None   # Кто создал/добыл
    creation_year: int = 0
    origin_location: Optional[tuple] = None

    # Состояние
    durability: float = 1.0           # Для орудий: износ
    spoilage: float = 0.0             # Для еды: порча (0-1)

    def get_name(self) -> str:
        return self.resource_type.russian_name

    def is_food(self) -> bool:
        return self.resource_type.category == ResourceCategory.FOOD

    def is_tool(self) -> bool:
        return self.resource_type.category == ResourceCategory.TOOL

    def is_usable(self) -> bool:
        """Можно ли использовать ресурс"""
        if self.is_food():
            return self.spoilage < 0.8
        if self.is_tool():
            return self.durability > 0.1
        return self.quantity > 0

    def get_effective_value(self) -> float:
        """Эффективная ценность с учётом качества и состояния"""
        value = self.quantity * self.quality
        if self.is_food():
            value *= (1 - self.spoilage)
        if self.is_tool():
            value *= self.durability
        return value

    def use(self, amount: float = 1.0) -> float:
        """Использует ресурс, возвращает реально использованное количество"""
        used = min(amount, self.quantity)
        self.quantity -= used

        # Износ орудий
        if self.is_tool():
            self.durability -= 0.01 * used

        return used

    def decay(self, days: float = 1.0) -> None:
        """Порча ресурса со временем"""
        if self.is_food():
            # Разная скорость порчи
            decay_rates = {
                ResourceType.MEAT: 0.1,
                ResourceType.FISH: 0.15,
                ResourceType.MILK: 0.2,
                ResourceType.BERRIES: 0.08,
                ResourceType.GRAIN: 0.01,
                ResourceType.HONEY: 0.001,
            }
            rate = decay_rates.get(self.resource_type, 0.05)
            self.spoilage = min(1.0, self.spoilage + rate * days)

    def merge_with(self, other: 'Resource') -> bool:
        """Объединяет с другим ресурсом того же типа"""
        if self.resource_type != other.resource_type:
            return False

        total_qty = self.quantity + other.quantity
        # Средневзвешенное качество
        self.quality = (self.quality * self.quantity +
                        other.quality * other.quantity) / total_qty
        self.quantity = total_qty

        # Средняя порча
        if self.is_food():
            self.spoilage = (self.spoilage * self.quantity +
                             other.spoilage * other.quantity) / total_qty

        return True


@dataclass
class Inventory:
    """
    Инвентарь - хранилище ресурсов.

    Используется для:
    - Личных запасов NPC
    - Общинных хранилищ
    - Торговли
    """
    owner_id: str
    resources: Dict[ResourceType, Resource] = field(default_factory=dict)
    capacity: float = 100.0            # Максимальная вместимость

    def add(self, resource: Resource) -> bool:
        """Добавляет ресурс в инвентарь"""
        current_amount = self.get_total_amount()
        if current_amount + resource.quantity > self.capacity:
            return False

        if resource.resource_type in self.resources:
            self.resources[resource.resource_type].merge_with(resource)
        else:
            self.resources[resource.resource_type] = resource

        return True

    def remove(self, resource_type: ResourceType, amount: float) -> Optional[Resource]:
        """Забирает ресурс из инвентаря"""
        if resource_type not in self.resources:
            return None

        resource = self.resources[resource_type]
        if resource.quantity < amount:
            return None

        # Создаём копию с нужным количеством
        taken = Resource(
            resource_type=resource_type,
            quantity=amount,
            quality=resource.quality,
            creator_id=resource.creator_id,
            creation_year=resource.creation_year,
        )

        resource.quantity -= amount
        if resource.quantity <= 0:
            del self.resources[resource_type]

        return taken

    def get(self, resource_type: ResourceType) -> Optional[Resource]:
        """Возвращает ресурс (не забирая)"""
        return self.resources.get(resource_type)

    def get_amount(self, resource_type: ResourceType) -> float:
        """Возвращает количество ресурса"""
        resource = self.resources.get(resource_type)
        return resource.quantity if resource else 0.0

    def get_total_amount(self) -> float:
        """Возвращает общее количество ресурсов"""
        return sum(r.quantity for r in self.resources.values())

    def get_food_amount(self) -> float:
        """Возвращает количество еды"""
        return sum(r.quantity for r in self.resources.values() if r.is_food())

    def get_best_tool(self, for_activity: str = None) -> Optional[Resource]:
        """Возвращает лучшее орудие"""
        tools = [r for r in self.resources.values() if r.is_tool() and r.is_usable()]
        if not tools:
            return None

        # Приоритет по качеству материала
        tool_priority = {
            ResourceType.IRON_TOOL: 5,
            ResourceType.BRONZE_TOOL: 4,
            ResourceType.STONE_TOOL: 2,
            ResourceType.BONE_TOOL: 1,
            ResourceType.WOODEN_TOOL: 1,
        }

        return max(tools, key=lambda t: tool_priority.get(t.resource_type, 0) * t.quality)

    def has_enough(self, resource_type: ResourceType, amount: float) -> bool:
        """Проверяет, достаточно ли ресурса"""
        return self.get_amount(resource_type) >= amount

    def decay_all(self, days: float = 1.0) -> List[str]:
        """Применяет порчу ко всем ресурсам"""
        spoiled = []
        for resource in list(self.resources.values()):
            old_usable = resource.is_usable()
            resource.decay(days)
            if old_usable and not resource.is_usable():
                spoiled.append(resource.get_name())
                del self.resources[resource.resource_type]
        return spoiled

    def get_summary(self) -> str:
        """Возвращает краткое описание содержимого"""
        if not self.resources:
            return "пусто"

        items = []
        for r in sorted(self.resources.values(),
                        key=lambda x: x.quantity, reverse=True):
            items.append(f"{r.get_name()}: {r.quantity:.1f}")

        return ", ".join(items[:5])

    def get_wealth_value(self) -> float:
        """Оценивает общую ценность ресурсов"""
        # Базовые ценности ресурсов
        values = {
            ResourceType.GRAIN: 1.0,
            ResourceType.MEAT: 2.0,
            ResourceType.LEATHER: 3.0,
            ResourceType.IRON: 10.0,
            ResourceType.IRON_TOOL: 20.0,
            ResourceType.JEWELRY: 50.0,
        }

        total = 0.0
        for r in self.resources.values():
            base_value = values.get(r.resource_type, 1.0)
            total += r.get_effective_value() * base_value

        return total
