"""
Система локаций - места в игровом мире.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
import uuid


class LocationType(Enum):
    """Типы локаций"""
    HOME = "дом"
    TAVERN = "таверна"
    MARKET = "рынок"
    SHOP = "магазин"
    BLACKSMITH = "кузница"
    FARM = "ферма"
    CHURCH = "церковь"
    TOWN_SQUARE = "городская площадь"
    BARRACKS = "казармы"
    CASTLE = "замок"
    FOREST = "лес"
    ROAD = "дорога"
    MINE = "шахта"
    LIBRARY = "библиотека"
    HOSPITAL = "лечебница"
    GUILD_HALL = "гильдия"


@dataclass
class Location:
    """
    Локация в игровом мире.

    Каждая локация имеет:
    - Уникальный ID и название
    - Тип и описание
    - Вместимость и текущих посетителей
    - Связи с другими локациями
    - Владельца (опционально)
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Безымянное место"
    location_type: LocationType = LocationType.ROAD
    description: str = ""

    # Вместимость
    capacity: int = 20  # Максимум NPC
    current_npcs: Set[str] = field(default_factory=set)  # ID NPC в локации

    # Связи с другими локациями
    connected_locations: Set[str] = field(default_factory=set)  # ID соседних локаций

    # Владение
    owner_id: Optional[str] = None  # ID владельца-NPC

    # Экономика
    wealth_level: int = 50  # Уровень богатства (0-100)
    prices_modifier: float = 1.0  # Модификатор цен

    # Доступность
    is_public: bool = True  # Могут ли все входить
    open_hours: tuple = (6, 22)  # Часы работы (для заведений)

    # Ресурсы
    available_services: List[str] = field(default_factory=list)
    available_items: Dict[str, int] = field(default_factory=dict)  # item_id: количество

    def add_npc(self, npc_id: str) -> bool:
        """Добавляет NPC в локацию"""
        if len(self.current_npcs) >= self.capacity:
            return False
        self.current_npcs.add(npc_id)
        return True

    def remove_npc(self, npc_id: str) -> bool:
        """Удаляет NPC из локации"""
        if npc_id in self.current_npcs:
            self.current_npcs.remove(npc_id)
            return True
        return False

    def is_full(self) -> bool:
        """Проверяет, заполнена ли локация"""
        return len(self.current_npcs) >= self.capacity

    def get_npc_count(self) -> int:
        """Возвращает количество NPC в локации"""
        return len(self.current_npcs)

    def connect_to(self, other_location_id: str) -> None:
        """Связывает с другой локацией"""
        self.connected_locations.add(other_location_id)

    def is_open(self, hour: int) -> bool:
        """Проверяет, открыта ли локация в данный час"""
        if self.is_public and self.location_type in [
            LocationType.ROAD, LocationType.TOWN_SQUARE,
            LocationType.FOREST, LocationType.FARM
        ]:
            return True

        start, end = self.open_hours
        if start <= end:
            return start <= hour < end
        else:  # Ночное заведение (например, 22-6)
            return hour >= start or hour < end

    def get_service_description(self) -> str:
        """Возвращает описание доступных услуг"""
        if not self.available_services:
            return "Услуги недоступны"
        return "Доступно: " + ", ".join(self.available_services)

    def describe(self) -> str:
        """Возвращает описание локации"""
        parts = [
            f"{self.name} ({self.location_type.value})",
            self.description if self.description else "",
            f"Людей: {self.get_npc_count()}/{self.capacity}",
        ]

        if self.available_services:
            parts.append(self.get_service_description())

        return "\n".join(filter(None, parts))

    @classmethod
    def create_tavern(cls, name: str) -> 'Location':
        """Создаёт таверну"""
        return cls(
            name=name,
            location_type=LocationType.TAVERN,
            description="Уютное место для отдыха и общения",
            capacity=30,
            available_services=["еда", "выпивка", "комната", "слухи"],
            open_hours=(10, 2),  # До 2 ночи
        )

    @classmethod
    def create_market(cls, name: str) -> 'Location':
        """Создаёт рынок"""
        return cls(
            name=name,
            location_type=LocationType.MARKET,
            description="Шумное место торговли",
            capacity=50,
            available_services=["торговля", "новости"],
            open_hours=(7, 18),
        )

    @classmethod
    def create_home(cls, name: str, owner_id: str = None) -> 'Location':
        """Создаёт жилой дом"""
        return cls(
            name=name,
            location_type=LocationType.HOME,
            description="Жилой дом",
            capacity=6,
            is_public=False,
            owner_id=owner_id,
            available_services=["отдых", "еда"],
            open_hours=(0, 24),  # Всегда открыт для хозяина
        )
