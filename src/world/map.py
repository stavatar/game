"""
Карта мира - двойное представление (сетка + непрерывные координаты).

Сетка используется для:
- Территорий и биомов
- Ресурсов
- Построек
- Владения землёй

Непрерывные координаты используются для:
- Позиций NPC
- Движения
- Расстояний
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import random
import math

from .terrain import Tile, TerrainType, BiomeType, get_terrain_properties


@dataclass
class Position:
    """Позиция в непрерывном пространстве"""
    x: float
    y: float

    def distance_to(self, other: 'Position') -> float:
        """Расстояние до другой позиции"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def to_grid(self) -> Tuple[int, int]:
        """Конвертирует в координаты сетки"""
        return (int(self.x), int(self.y))

    def move_towards(self, target: 'Position', speed: float) -> 'Position':
        """Перемещается в сторону цели"""
        dist = self.distance_to(target)
        if dist <= speed:
            return Position(target.x, target.y)

        ratio = speed / dist
        new_x = self.x + (target.x - self.x) * ratio
        new_y = self.y + (target.y - self.y) * ratio
        return Position(new_x, new_y)

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return abs(self.x - other.x) < 0.01 and abs(self.y - other.y) < 0.01


class WorldMap:
    """
    Карта мира.

    Поддерживает:
    - Процедурную генерацию
    - Двойное представление (сетка/непрерывное)
    - Поиск пути
    - Запросы по области
    """

    def __init__(self, width: int = 50, height: int = 50, seed: int = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 999999)

        # Сетка тайлов
        self.tiles: Dict[Tuple[int, int], Tile] = {}

        # Индексы для быстрого поиска
        self._water_tiles: Set[Tuple[int, int]] = set()
        self._forest_tiles: Set[Tuple[int, int]] = set()
        self._fertile_tiles: Set[Tuple[int, int]] = set()

        # Генерируем карту
        self._generate()

    def _generate(self) -> None:
        """Процедурная генерация карты"""
        random.seed(self.seed)

        # Генерируем базовую карту с использованием шума
        elevation_map = self._generate_noise_map(scale=0.1)
        moisture_map = self._generate_noise_map(scale=0.08)

        for x in range(self.width):
            for y in range(self.height):
                elevation = elevation_map[x][y]
                moisture = moisture_map[x][y]

                # Определяем тип территории
                terrain = self._get_terrain_from_params(elevation, moisture)

                tile = Tile(
                    x=x, y=y,
                    terrain=terrain,
                    elevation=elevation,
                    moisture=moisture,
                )

                self.tiles[(x, y)] = tile

                # Обновляем индексы
                if terrain == TerrainType.WATER:
                    self._water_tiles.add((x, y))
                elif terrain in [TerrainType.FOREST, TerrainType.DENSE_FOREST]:
                    self._forest_tiles.add((x, y))

                if tile.get_properties().fertility > 0.5:
                    self._fertile_tiles.add((x, y))

        # Добавляем реку
        self._generate_river()

    def _generate_noise_map(self, scale: float = 0.1) -> List[List[float]]:
        """Генерирует карту шума (упрощённый Perlin noise)"""
        noise_map = []

        for x in range(self.width):
            row = []
            for y in range(self.height):
                # Простой шум на основе нескольких октав
                value = 0.0
                amplitude = 1.0
                frequency = scale

                for _ in range(4):  # 4 октавы
                    # Псевдо-случайное значение на основе координат
                    nx = x * frequency
                    ny = y * frequency
                    noise = self._pseudo_noise(nx, ny)
                    value += noise * amplitude
                    amplitude *= 0.5
                    frequency *= 2

                # Нормализуем к 0-1
                value = (value + 1) / 2
                row.append(max(0, min(1, value)))
            noise_map.append(row)

        return noise_map

    def _pseudo_noise(self, x: float, y: float) -> float:
        """Псевдо-случайный шум"""
        # Простая хеш-функция для получения "шума"
        n = int(x * 374761393 + y * 668265263 + self.seed)
        n = (n ^ (n >> 13)) * 1274126177
        return ((n & 0x7fffffff) / 0x7fffffff) * 2 - 1

    def _get_terrain_from_params(self, elevation: float, moisture: float) -> TerrainType:
        """Определяет тип территории по параметрам"""
        # Вода - низкие места с высокой влажностью
        if elevation < 0.3 and moisture > 0.6:
            return TerrainType.WATER

        # Горы - высокие места
        if elevation > 0.85:
            return TerrainType.MOUNTAIN

        # Холмы
        if elevation > 0.7:
            return TerrainType.HILL

        # Болото - низкие места с высокой влажностью
        if elevation < 0.4 and moisture > 0.7:
            return TerrainType.SWAMP

        # Лес - средняя влажность
        if moisture > 0.5:
            if moisture > 0.7:
                return TerrainType.DENSE_FOREST
            return TerrainType.FOREST

        # Степь/пустыня - низкая влажность
        if moisture < 0.3:
            return TerrainType.DESERT

        # По умолчанию - равнина
        return TerrainType.GRASSLAND

    def _generate_river(self) -> None:
        """Генерирует реку от гор к низине"""
        # Находим начальную точку (горы или холмы)
        high_points = [(x, y) for (x, y), tile in self.tiles.items()
                       if tile.terrain in [TerrainType.MOUNTAIN, TerrainType.HILL]]

        if not high_points:
            return

        # Выбираем случайную стартовую точку
        start = random.choice(high_points)
        current = start

        # Течём вниз, пока не дойдём до края или воды
        visited = {current}
        max_steps = self.width + self.height

        for _ in range(max_steps):
            x, y = current

            # Находим соседа с наименьшей высотой
            neighbors = self._get_neighbors(x, y)
            valid_neighbors = [(nx, ny) for nx, ny in neighbors
                               if (nx, ny) not in visited]

            if not valid_neighbors:
                break

            # Выбираем соседа с наименьшей высотой
            next_tile = min(valid_neighbors,
                            key=lambda p: self.tiles[p].elevation)

            # Если дошли до воды - останавливаемся
            if self.tiles[next_tile].terrain == TerrainType.WATER:
                break

            # Превращаем в воду
            self.tiles[next_tile].terrain = TerrainType.WATER
            self._water_tiles.add(next_tile)

            # Увеличиваем влажность вокруг
            for nx, ny in self._get_neighbors(*next_tile):
                if (nx, ny) in self.tiles:
                    self.tiles[(nx, ny)].moisture = min(1.0,
                        self.tiles[(nx, ny)].moisture + 0.2)

            visited.add(next_tile)
            current = next_tile

    def _get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Возвращает соседние клетки"""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny))
        return neighbors

    # === Методы доступа ===

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Возвращает тайл по координатам сетки"""
        return self.tiles.get((x, y))

    def get_tile_at_position(self, pos: Position) -> Optional[Tile]:
        """Возвращает тайл по непрерывной позиции"""
        return self.get_tile(*pos.to_grid())

    def is_valid_position(self, x: float, y: float) -> bool:
        """Проверяет, валидна ли позиция"""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_passable(self, x: int, y: int) -> bool:
        """Можно ли пройти через клетку"""
        tile = self.get_tile(x, y)
        if not tile:
            return False
        return tile.terrain != TerrainType.WATER

    # === Поиск ===

    def find_nearest(self, pos: Position, terrain: TerrainType,
                     max_distance: float = 20) -> Optional[Position]:
        """Находит ближайшую клетку с указанным типом территории"""
        gx, gy = pos.to_grid()
        best_dist = float('inf')
        best_pos = None

        search_radius = int(max_distance) + 1

        for dx in range(-search_radius, search_radius + 1):
            for dy in range(-search_radius, search_radius + 1):
                nx, ny = gx + dx, gy + dy
                tile = self.get_tile(nx, ny)
                if tile and tile.terrain == terrain:
                    tile_pos = Position(nx + 0.5, ny + 0.5)
                    dist = pos.distance_to(tile_pos)
                    if dist < best_dist and dist <= max_distance:
                        best_dist = dist
                        best_pos = tile_pos

        return best_pos

    def find_fertile_land(self, pos: Position, max_distance: float = 15) -> List[Tuple[int, int]]:
        """Находит плодородные земли рядом"""
        gx, gy = pos.to_grid()
        result = []

        for (x, y) in self._fertile_tiles:
            dist = math.sqrt((x - gx) ** 2 + (y - gy) ** 2)
            if dist <= max_distance:
                tile = self.tiles[(x, y)]
                if not tile.owner_id and tile.can_farm():
                    result.append((x, y))

        return sorted(result, key=lambda p: (p[0] - gx) ** 2 + (p[1] - gy) ** 2)

    def find_resources(self, pos: Position, resource_type: str,
                       max_distance: float = 10) -> List[Tuple[int, int]]:
        """Находит клетки с указанным ресурсом"""
        gx, gy = pos.to_grid()
        result = []

        for (x, y), tile in self.tiles.items():
            dist = math.sqrt((x - gx) ** 2 + (y - gy) ** 2)
            if dist <= max_distance:
                if resource_type in tile.get_properties().base_resources:
                    result.append((x, y))

        return sorted(result, key=lambda p: (p[0] - gx) ** 2 + (p[1] - gy) ** 2)

    # === Отображение ===

    def render_ascii(self, center_x: int = None, center_y: int = None,
                     viewport_size: int = 20,
                     npc_positions: Dict[str, Position] = None) -> str:
        """Рендерит ASCII-карту"""
        if center_x is None:
            center_x = self.width // 2
        if center_y is None:
            center_y = self.height // 2

        half = viewport_size // 2
        min_x = max(0, center_x - half)
        max_x = min(self.width, center_x + half)
        min_y = max(0, center_y - half)
        max_y = min(self.height, center_y + half)

        # Создаём словарь позиций NPC для быстрого доступа
        npc_grid = {}
        if npc_positions:
            for npc_id, pos in npc_positions.items():
                grid_pos = pos.to_grid()
                if grid_pos not in npc_grid:
                    npc_grid[grid_pos] = []
                npc_grid[grid_pos].append(npc_id)

        lines = []

        # Заголовок с координатами
        header = "   " + "".join(str(x % 10) for x in range(min_x, max_x))
        lines.append(header)

        for y in range(min_y, max_y):
            row = f"{y:2d} "
            for x in range(min_x, max_x):
                tile = self.get_tile(x, y)
                if (x, y) in npc_grid:
                    # Показываем NPC
                    count = len(npc_grid[(x, y)])
                    row += str(min(count, 9)) if count > 1 else "@"
                elif tile:
                    row += tile.get_symbol()
                else:
                    row += "?"
            lines.append(row)

        return "\n".join(lines)

    def get_legend(self) -> str:
        """Возвращает легенду карты"""
        legend = "Легенда:\n"
        for terrain_type in TerrainType:
            props = get_terrain_properties(terrain_type)
            legend += f"  {props.symbol} - {props.name}\n"
        legend += "  @ - житель\n"
        legend += "  □ - постройка\n"
        return legend

    # === Статистика ===

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику карты"""
        terrain_counts = {}
        for tile in self.tiles.values():
            terrain_counts[tile.terrain.name] = terrain_counts.get(tile.terrain.name, 0) + 1

        owned_tiles = sum(1 for t in self.tiles.values() if t.owner_id)

        return {
            "размер": f"{self.width}x{self.height}",
            "всего_клеток": len(self.tiles),
            "типы_территорий": terrain_counts,
            "водные_клетки": len(self._water_tiles),
            "лесные_клетки": len(self._forest_tiles),
            "плодородные_клетки": len(self._fertile_tiles),
            "занятые_клетки": owned_tiles,
        }
