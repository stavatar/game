"""
Типы территорий и биомы.
"""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional


class TerrainType(Enum):
    """Базовые типы территории"""
    WATER = auto()          # Вода (река, озеро)
    GRASSLAND = auto()      # Луг, равнина
    FOREST = auto()         # Лес
    DENSE_FOREST = auto()   # Густой лес
    HILL = auto()           # Холмы
    MOUNTAIN = auto()       # Горы
    SWAMP = auto()          # Болото
    DESERT = auto()         # Пустыня/степь


class BiomeType(Enum):
    """Биомы - определяют климат и ресурсы"""
    TEMPERATE = auto()      # Умеренный
    BOREAL = auto()         # Северный (тайга)
    TROPICAL = auto()       # Тропический
    ARID = auto()           # Засушливый
    TUNDRA = auto()         # Тундра


@dataclass
class TerrainProperties:
    """Свойства типа территории"""
    name: str
    symbol: str                    # Символ для ASCII-карты
    color: str                     # Цвет для отображения
    movement_cost: float           # Стоимость перемещения (1.0 = норма)
    fertility: float               # Плодородность (0-1)
    building_allowed: bool         # Можно ли строить
    base_resources: List[str]      # Базовые ресурсы

    # Влияние на жителей
    shelter_value: float = 0.0     # Насколько укрывает от стихии
    danger_level: float = 0.0      # Уровень опасности


# Свойства каждого типа территории
TERRAIN_PROPERTIES: Dict[TerrainType, TerrainProperties] = {
    TerrainType.WATER: TerrainProperties(
        name="вода",
        symbol="~",
        color="blue",
        movement_cost=5.0,        # Сложно пересечь
        fertility=0.0,
        building_allowed=False,
        base_resources=["рыба", "вода"],
        danger_level=0.3,
    ),
    TerrainType.GRASSLAND: TerrainProperties(
        name="равнина",
        symbol=".",
        color="green",
        movement_cost=1.0,
        fertility=0.7,
        building_allowed=True,
        base_resources=["трава", "дичь"],
    ),
    TerrainType.FOREST: TerrainProperties(
        name="лес",
        symbol="♠",
        color="dark_green",
        movement_cost=1.5,
        fertility=0.4,
        building_allowed=True,
        base_resources=["древесина", "дичь", "ягоды", "грибы"],
        shelter_value=0.3,
        danger_level=0.2,
    ),
    TerrainType.DENSE_FOREST: TerrainProperties(
        name="густой лес",
        symbol="♣",
        color="dark_green",
        movement_cost=2.5,
        fertility=0.2,
        building_allowed=False,
        base_resources=["древесина", "дичь", "ягоды", "мёд"],
        shelter_value=0.5,
        danger_level=0.4,
    ),
    TerrainType.HILL: TerrainProperties(
        name="холмы",
        symbol="∩",
        color="brown",
        movement_cost=2.0,
        fertility=0.3,
        building_allowed=True,
        base_resources=["камень", "руда"],
        shelter_value=0.2,
    ),
    TerrainType.MOUNTAIN: TerrainProperties(
        name="горы",
        symbol="▲",
        color="gray",
        movement_cost=4.0,
        fertility=0.0,
        building_allowed=False,
        base_resources=["камень", "руда", "драгоценности"],
        shelter_value=0.4,
        danger_level=0.3,
    ),
    TerrainType.SWAMP: TerrainProperties(
        name="болото",
        symbol="≈",
        color="dark_cyan",
        movement_cost=3.0,
        fertility=0.1,
        building_allowed=False,
        base_resources=["торф", "ягоды", "лекарственные травы"],
        danger_level=0.4,
    ),
    TerrainType.DESERT: TerrainProperties(
        name="степь",
        symbol=":",
        color="yellow",
        movement_cost=1.2,
        fertility=0.2,
        building_allowed=True,
        base_resources=["трава", "дичь"],
        danger_level=0.1,
    ),
}


def get_terrain_properties(terrain: TerrainType) -> TerrainProperties:
    """Возвращает свойства территории"""
    return TERRAIN_PROPERTIES.get(terrain, TERRAIN_PROPERTIES[TerrainType.GRASSLAND])


@dataclass
class Tile:
    """
    Одна клетка карты.
    Содержит информацию о территории и её состоянии.
    """
    x: int
    y: int
    terrain: TerrainType
    biome: BiomeType = BiomeType.TEMPERATE

    # Высота (влияет на климат и реки)
    elevation: float = 0.5       # 0-1, где 0.5 = уровень моря

    # Влажность
    moisture: float = 0.5        # 0-1

    # Текущее состояние
    fertility_modifier: float = 1.0   # Множитель плодородия
    is_flooded: bool = False          # Затоплено
    is_burning: bool = False          # Горит (лесной пожар)

    # Владение
    owner_id: Optional[str] = None    # Кто владеет этой землёй
    claimed_by: Optional[str] = None  # Кто претендует

    # Постройки
    building_id: Optional[str] = None

    def get_properties(self) -> TerrainProperties:
        """Возвращает свойства территории"""
        return get_terrain_properties(self.terrain)

    def get_effective_fertility(self, season: str = "лето") -> float:
        """Возвращает эффективную плодородность с учётом модификаторов"""
        base = self.get_properties().fertility * self.fertility_modifier

        # Влияние сезона
        season_modifiers = {
            "весна": 0.8,
            "лето": 1.0,
            "осень": 0.6,
            "зима": 0.1,
        }
        base *= season_modifiers.get(season, 1.0)

        # Влияние влажности
        if self.moisture < 0.2:
            base *= 0.5  # Засуха
        elif self.moisture > 0.8:
            base *= 0.8  # Переувлажнение

        return max(0, min(1, base))

    def get_symbol(self) -> str:
        """Возвращает символ для отображения"""
        if self.building_id:
            return "□"  # Постройка
        if self.is_burning:
            return "🔥"
        if self.is_flooded:
            return "≋"
        return self.get_properties().symbol

    def can_build(self) -> bool:
        """Можно ли строить на этой клетке"""
        props = self.get_properties()
        return (props.building_allowed and
                not self.is_flooded and
                not self.building_id)

    def can_farm(self) -> bool:
        """Можно ли заниматься земледелием"""
        return (self.get_effective_fertility() > 0.3 and
                not self.is_flooded and
                self.terrain in [TerrainType.GRASSLAND, TerrainType.FOREST])
