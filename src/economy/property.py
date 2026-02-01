"""
Система собственности - основа производственных отношений.

По Марксу, отношение к средствам производства определяет классовую принадлежность:
- Владельцы средств производства = эксплуататоры
- Не владеющие = эксплуатируемые

Типы собственности:
- Общинная (всё принадлежит общине)
- Личная (предметы потребления)
- Частная (средства производства)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto
import random


class PropertyType(Enum):
    """Типы собственности"""
    COMMUNAL = "общинная"          # Принадлежит всей общине
    PERSONAL = "личная"            # Личные вещи (не средства производства)
    PRIVATE = "частная"            # Средства производства в частных руках
    FAMILY = "семейная"            # Принадлежит семье


class PropertyCategory(Enum):
    """Категории имущества"""
    LAND = "земля"                 # Земельные участки
    TOOLS = "орудия"               # Орудия труда
    LIVESTOCK = "скот"             # Животные
    BUILDING = "постройка"         # Здания
    RESOURCES = "ресурсы"          # Запасы ресурсов
    KNOWLEDGE = "знания"           # Права на знания/технологии


@dataclass
class PropertyRight:
    """
    Право собственности на объект.

    Определяет:
    - Кто владеет
    - Тип собственности
    - Что можно делать с имуществом
    """
    property_id: str
    category: PropertyCategory

    # Владение
    owner_type: PropertyType = PropertyType.COMMUNAL
    owner_id: Optional[str] = None         # NPC id или family_id
    community_id: Optional[str] = None     # Община (для общинной собственности)

    # Права
    can_use: Set[str] = field(default_factory=set)      # Кто может использовать
    can_transfer: bool = False             # Можно ли передать
    inheritable: bool = True               # Передаётся по наследству

    # Для земли
    location: Optional[Tuple[int, int]] = None
    area: float = 1.0                      # Площадь (для земли)

    # Экономическая ценность
    value: float = 0.0

    # История
    acquisition_year: int = 0
    acquisition_method: str = "захват"     # Как получено: захват, наследство, покупка, дар

    def is_means_of_production(self) -> bool:
        """Является ли средством производства"""
        return self.category in [
            PropertyCategory.LAND,
            PropertyCategory.TOOLS,
            PropertyCategory.LIVESTOCK,
            PropertyCategory.BUILDING,
        ]

    def get_owner_description(self) -> str:
        """Описание владельца"""
        if self.owner_type == PropertyType.COMMUNAL:
            return "община"
        elif self.owner_type == PropertyType.FAMILY:
            return f"семья {self.owner_id}"
        else:
            return self.owner_id or "никто"


class OwnershipTransition(Enum):
    """Типы переходов собственности"""
    CLAIMING = "захват"              # Первоначальный захват
    INHERITANCE = "наследство"       # Передача по наследству
    GIFT = "дар"                     # Подарок
    TRADE = "обмен"                  # Торговля/обмен
    SEIZURE = "отъём"                # Насильственный отъём
    COMMUNALIZATION = "обобществление"  # Переход в общинную


@dataclass
class OwnershipSystem:
    """
    Система управления собственностью.

    Отслеживает:
    - Всё имущество в мире
    - Кто чем владеет
    - Переходы собственности
    - Возникновение неравенства
    """

    # Все права собственности
    properties: Dict[str, PropertyRight] = field(default_factory=dict)

    # Индекс: владелец -> список property_id
    owner_index: Dict[str, Set[str]] = field(default_factory=dict)

    # Индекс: локация -> property_id (для земли)
    location_index: Dict[Tuple[int, int], str] = field(default_factory=dict)

    # История переходов
    transfer_history: List[Tuple[str, str, str, int, OwnershipTransition]] = field(default_factory=list)

    # Флаги развития
    private_property_emerged: bool = False
    first_private_property_year: int = 0

    def register_property(self, prop: PropertyRight) -> None:
        """Регистрирует новое имущество"""
        self.properties[prop.property_id] = prop

        # Обновляем индексы
        if prop.owner_id:
            if prop.owner_id not in self.owner_index:
                self.owner_index[prop.owner_id] = set()
            self.owner_index[prop.owner_id].add(prop.property_id)

        if prop.location:
            self.location_index[prop.location] = prop.property_id

    def claim_land(self, x: int, y: int, claimer_id: str,
                   year: int, as_private: bool = False) -> Optional[PropertyRight]:
        """
        Захват земли.

        Возвращает право собственности или None, если земля уже занята.
        """
        location = (x, y)

        # Проверяем, не занята ли
        if location in self.location_index:
            return None

        # Создаём право собственности
        prop = PropertyRight(
            property_id=f"land_{x}_{y}",
            category=PropertyCategory.LAND,
            owner_type=PropertyType.PRIVATE if as_private else PropertyType.COMMUNAL,
            owner_id=claimer_id if as_private else None,
            location=location,
            acquisition_year=year,
            acquisition_method="захват",
            can_transfer=as_private,
        )

        # Отмечаем возникновение частной собственности
        if as_private and not self.private_property_emerged:
            self.private_property_emerged = True
            self.first_private_property_year = year

        self.register_property(prop)
        return prop

    def transfer_property(self, property_id: str, new_owner_id: str,
                          year: int, method: OwnershipTransition) -> bool:
        """Передаёт собственность новому владельцу"""
        if property_id not in self.properties:
            return False

        prop = self.properties[property_id]
        old_owner = prop.owner_id

        if not prop.can_transfer and method not in [
            OwnershipTransition.INHERITANCE,
            OwnershipTransition.SEIZURE,
            OwnershipTransition.COMMUNALIZATION
        ]:
            return False

        # Удаляем из индекса старого владельца
        if old_owner and old_owner in self.owner_index:
            self.owner_index[old_owner].discard(property_id)

        # Обновляем владельца
        prop.owner_id = new_owner_id
        prop.owner_type = PropertyType.PRIVATE
        prop.acquisition_year = year
        prop.acquisition_method = method.value

        # Добавляем в индекс нового владельца
        if new_owner_id not in self.owner_index:
            self.owner_index[new_owner_id] = set()
        self.owner_index[new_owner_id].add(property_id)

        # Записываем в историю
        self.transfer_history.append((
            property_id, old_owner or "община", new_owner_id, year, method
        ))

        return True

    def get_owner_properties(self, owner_id: str) -> List[PropertyRight]:
        """Возвращает всё имущество владельца"""
        prop_ids = self.owner_index.get(owner_id, set())
        return [self.properties[pid] for pid in prop_ids if pid in self.properties]

    def get_land_at(self, x: int, y: int) -> Optional[PropertyRight]:
        """Возвращает право на землю в указанной локации"""
        prop_id = self.location_index.get((x, y))
        if prop_id:
            return self.properties.get(prop_id)
        return None

    def calculate_wealth(self, owner_id: str) -> float:
        """Вычисляет богатство владельца"""
        properties = self.get_owner_properties(owner_id)
        return sum(p.value for p in properties)

    def get_means_of_production_owners(self) -> Set[str]:
        """Возвращает владельцев средств производства"""
        owners = set()
        for prop in self.properties.values():
            if prop.is_means_of_production() and prop.owner_id:
                if prop.owner_type == PropertyType.PRIVATE:
                    owners.add(prop.owner_id)
        return owners

    def get_landless(self, all_npc_ids: Set[str]) -> Set[str]:
        """Возвращает безземельных NPC"""
        land_owners = set()
        for prop in self.properties.values():
            if prop.category == PropertyCategory.LAND and prop.owner_id:
                land_owners.add(prop.owner_id)
        return all_npc_ids - land_owners

    def owns_land(self, owner_id: str) -> bool:
        """Проверяет, владеет ли NPC землёй"""
        for prop in self.get_owner_properties(owner_id):
            if prop.category == PropertyCategory.LAND:
                return True
        return False

    def owns_tools(self, owner_id: str) -> bool:
        """Проверяет, владеет ли NPC орудиями производства"""
        for prop in self.get_owner_properties(owner_id):
            if prop.category == PropertyCategory.TOOLS:
                return True
        return False

    def owns_livestock(self, owner_id: str) -> bool:
        """Проверяет, владеет ли NPC скотом"""
        for prop in self.get_owner_properties(owner_id):
            if prop.category == PropertyCategory.LIVESTOCK:
                return True
        return False

    def calculate_inequality(self) -> float:
        """
        Вычисляет коэффициент неравенства (0-1).

        0 = полное равенство
        1 = всё принадлежит одному
        """
        if not self.owner_index:
            return 0.0

        wealths = []
        for owner_id in self.owner_index:
            wealths.append(self.calculate_wealth(owner_id))

        if not wealths or sum(wealths) == 0:
            return 0.0

        # Коэффициент Джини
        n = len(wealths)
        if n <= 1:
            return 0.0

        wealths.sort()
        cumulative = 0
        for i, w in enumerate(wealths):
            cumulative += (n - i) * w

        return 1 - (2 * cumulative) / (n * sum(wealths))

    def get_property_distribution(self) -> Dict[str, int]:
        """Возвращает распределение собственности по типам"""
        distribution = {
            "общинная": 0,
            "частная": 0,
            "семейная": 0,
        }

        for prop in self.properties.values():
            if prop.owner_type == PropertyType.COMMUNAL:
                distribution["общинная"] += 1
            elif prop.owner_type == PropertyType.PRIVATE:
                distribution["частная"] += 1
            elif prop.owner_type == PropertyType.FAMILY:
                distribution["семейная"] += 1

        return distribution

    def process_inheritance(self, deceased_id: str, heir_id: str, year: int) -> List[str]:
        """Обрабатывает наследование имущества"""
        inherited = []

        properties = self.get_owner_properties(deceased_id)
        for prop in properties:
            if prop.inheritable:
                self.transfer_property(
                    prop.property_id,
                    heir_id,
                    year,
                    OwnershipTransition.INHERITANCE
                )
                inherited.append(prop.property_id)

        return inherited

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику собственности"""
        distribution = self.get_property_distribution()
        inequality = self.calculate_inequality()

        means_owners = self.get_means_of_production_owners()

        return {
            "total_properties": len(self.properties),
            "distribution": distribution,
            "inequality_gini": round(inequality, 3),
            "private_property_emerged": self.private_property_emerged,
            "first_private_year": self.first_private_property_year,
            "means_of_production_owners": len(means_owners),
            "total_owners": len(self.owner_index),
        }
