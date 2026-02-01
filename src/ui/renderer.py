"""
Рендерер карты мира.

Отрисовывает:
- Тайлы местности
- NPC (спрайты)
- Ресурсы
- Выделения и маркеры
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
import math

if TYPE_CHECKING:
    import pygame
    from .camera import Camera
    from .sprites import NPCSprite, NPCSpriteGroup

from .colors import TerrainColors, ClassColors, Colors, RGB, darken_color, lighten_color


@dataclass
class MapRenderer:
    """
    Рендерер карты мира.

    Отрисовывает карту с учётом камеры (позиция + масштаб).
    Использует кэширование тайлов для производительности.
    """

    # Pygame объекты (инициализируются позже)
    _surface: Optional['pygame.Surface'] = field(default=None, repr=False)
    _tile_cache: Dict[Tuple[str, int], 'pygame.Surface'] = field(
        default_factory=dict, repr=False
    )

    # Флаги
    _initialized: bool = False
    show_grid: bool = False
    show_resources: bool = True
    show_npc_classes: bool = True

    def initialize(self, pygame_module) -> None:
        """
        Инициализирует рендерер с pygame.

        Args:
            pygame_module: Модуль pygame
        """
        self._pygame = pygame_module
        self._initialized = True
        self._tile_cache.clear()

    def render_map(self,
                   surface: 'pygame.Surface',
                   world_map: List[List[str]],
                   camera: 'Camera') -> None:
        """
        Отрисовывает карту мира.

        Args:
            surface: Поверхность для рисования
            world_map: 2D массив тайлов
            camera: Камера
        """
        if not self._initialized:
            return

        # Получаем видимую область
        left, top, right, bottom = camera.get_visible_rect()
        tile_size = camera.get_scaled_tile_size()

        # Отрисовываем видимые тайлы
        for y in range(top, min(bottom, len(world_map))):
            for x in range(left, min(right, len(world_map[0]) if world_map else 0)):
                tile = world_map[y][x]
                screen_x, screen_y = camera.world_to_screen(x, y)

                # Рисуем тайл
                self._draw_tile(
                    surface, tile,
                    screen_x, screen_y,
                    int(tile_size), int(tile_size)
                )

        # Сетка
        if self.show_grid:
            self._draw_grid(surface, camera, left, top, right, bottom)

    def render_npcs(self,
                    surface: 'pygame.Surface',
                    sprites: 'NPCSpriteGroup',
                    camera: 'Camera') -> None:
        """
        Отрисовывает NPC.

        Args:
            surface: Поверхность для рисования
            sprites: Группа спрайтов NPC
            camera: Камера
        """
        if not self._initialized:
            return

        # Получаем видимую область
        left, top, right, bottom = camera.get_visible_rect()
        tile_size = camera.get_scaled_tile_size()

        # Получаем видимые спрайты
        visible = sprites.get_visible(left - 1, top - 1, right + 1, bottom + 1)

        # Сортируем по Y для правильного порядка отрисовки
        visible.sort(key=lambda s: s.y)

        for sprite in visible:
            self._draw_npc_sprite(surface, sprite, camera, tile_size)

    def _draw_tile(self,
                   surface: 'pygame.Surface',
                   tile: str,
                   x: int, y: int,
                   width: int, height: int) -> None:
        """Отрисовывает один тайл"""
        color = TerrainColors.for_tile(tile)

        # Добавляем немного вариации
        if tile in ['.', 'grass']:
            # Небольшой шум для травы
            variation = ((x * 13 + y * 7) % 20) - 10
            color = (
                max(0, min(255, color[0] + variation)),
                max(0, min(255, color[1] + variation)),
                max(0, min(255, color[2] + variation // 2)),
            )

        self._pygame.draw.rect(surface, color, (x, y, width + 1, height + 1))

        # Декорации для леса
        if tile in ['T', 'forest']:
            self._draw_tree_decoration(surface, x, y, width, height)

        # Декорации для воды
        if tile in ['~', 'water']:
            self._draw_water_decoration(surface, x, y, width, height)

    def _draw_tree_decoration(self, surface, x, y, width, height):
        """Рисует декорацию дерева"""
        if width < 8:
            return

        # Упрощённое дерево
        center_x = x + width // 2
        center_y = y + height // 2

        # Крона
        crown_color = darken_color(TerrainColors.FOREST, 0.1)
        radius = max(2, width // 4)
        self._pygame.draw.circle(surface, crown_color, (center_x, center_y), radius)

    def _draw_water_decoration(self, surface, x, y, width, height):
        """Рисует декорацию воды (волны)"""
        if width < 8:
            return

        # Небольшая волна
        wave_color = lighten_color(TerrainColors.WATER, 0.15)
        wave_y = y + height // 3
        self._pygame.draw.line(
            surface, wave_color,
            (x + 2, wave_y),
            (x + width - 2, wave_y),
            1
        )

    def _draw_grid(self,
                   surface: 'pygame.Surface',
                   camera: 'Camera',
                   left: int, top: int,
                   right: int, bottom: int) -> None:
        """Рисует сетку"""
        grid_color = (50, 50, 60)
        tile_size = camera.get_scaled_tile_size()

        # Вертикальные линии
        for x in range(left, right + 1):
            screen_x, _ = camera.world_to_screen(x, 0)
            self._pygame.draw.line(
                surface, grid_color,
                (screen_x, 0),
                (screen_x, camera.screen_height),
                1
            )

        # Горизонтальные линии
        for y in range(top, bottom + 1):
            _, screen_y = camera.world_to_screen(0, y)
            self._pygame.draw.line(
                surface, grid_color,
                (0, screen_y),
                (camera.screen_width, screen_y),
                1
            )

    def _draw_npc_sprite(self,
                         surface: 'pygame.Surface',
                         sprite: 'NPCSprite',
                         camera: 'Camera',
                         tile_size: float) -> None:
        """Отрисовывает спрайт NPC"""
        info = sprite.get_render_info()

        # Экранные координаты
        screen_x, screen_y = camera.world_to_screen(info['x'], info['y'])

        # Размер с учётом масштаба
        size = int(info['size'] * camera.zoom)
        half_size = size // 2

        # Основной цвет (класс)
        color = info['color']

        # Выделение
        if info['is_selected']:
            # Рисуем круг выделения
            self._pygame.draw.circle(
                surface, Colors.SELECTION,
                (screen_x, screen_y),
                half_size + 4, 2
            )
        elif info['is_hovered']:
            self._pygame.draw.circle(
                surface, Colors.HIGHLIGHT,
                (screen_x, screen_y),
                half_size + 2, 1
            )

        # Тело NPC (круг)
        self._pygame.draw.circle(
            surface, color,
            (screen_x, screen_y),
            half_size
        )

        # Обводка
        border_color = darken_color(color, 0.3)
        self._pygame.draw.circle(
            surface, border_color,
            (screen_x, screen_y),
            half_size, 1
        )

        # Индикатор классового сознания (маленький круг сверху)
        if self.show_npc_classes and sprite.consciousness_level > 0.1:
            consciousness_color = info['consciousness_color']
            indicator_radius = max(2, size // 6)
            indicator_y = screen_y - half_size - indicator_radius - 1
            self._pygame.draw.circle(
                surface, consciousness_color,
                (screen_x, indicator_y),
                indicator_radius
            )

        # Звёздочка для лидеров
        if info['is_leader']:
            self._draw_star(surface, screen_x, screen_y - half_size - 8, 4)

        # Книга для интеллектуалов
        if info['is_intellectual']:
            self._draw_book_icon(surface, screen_x + half_size, screen_y - half_size, 6)

    def _draw_star(self, surface, x: int, y: int, size: int) -> None:
        """Рисует звёздочку (для лидеров)"""
        color = (255, 220, 100)  # Золотой

        # Простая звезда из линий
        points = []
        for i in range(5):
            # Внешние точки
            angle = math.pi / 2 + i * 2 * math.pi / 5
            px = x + int(size * math.cos(angle))
            py = y - int(size * math.sin(angle))
            points.append((px, py))

            # Внутренние точки
            angle += math.pi / 5
            px = x + int(size * 0.4 * math.cos(angle))
            py = y - int(size * 0.4 * math.sin(angle))
            points.append((px, py))

        if len(points) >= 3:
            self._pygame.draw.polygon(surface, color, points)

    def _draw_book_icon(self, surface, x: int, y: int, size: int) -> None:
        """Рисует иконку книги (для интеллектуалов)"""
        color = (200, 180, 100)  # Бежевый

        # Простой прямоугольник-книга
        rect = (x - size // 2, y - size // 2, size, size)
        self._pygame.draw.rect(surface, color, rect)
        self._pygame.draw.rect(surface, darken_color(color, 0.3), rect, 1)

    def render_resources(self,
                         surface: 'pygame.Surface',
                         resources: Dict,
                         camera: 'Camera') -> None:
        """
        Отрисовывает ресурсы на карте.

        Args:
            surface: Поверхность для рисования
            resources: Словарь ресурсов из симуляции
            camera: Камера
        """
        if not self._initialized or not self.show_resources:
            return

        left, top, right, bottom = camera.get_visible_rect()

        for resource_id, resource in resources.items():
            x = getattr(resource, 'x', 0)
            y = getattr(resource, 'y', 0)

            if not (left <= x <= right and top <= y <= bottom):
                continue

            screen_x, screen_y = camera.world_to_screen(x, y)
            amount = getattr(resource, 'amount', 0)
            max_amount = getattr(resource, 'max_amount', 100)

            # Цвет зависит от количества
            if amount > max_amount * 0.5:
                color = TerrainColors.RESOURCE
            else:
                color = TerrainColors.RESOURCE_DEPLETED

            # Размер зависит от количества
            size = max(3, int(8 * (amount / max_amount) * camera.zoom))

            # Рисуем квадратик
            self._pygame.draw.rect(
                surface, color,
                (screen_x - size // 2, screen_y - size // 2, size, size)
            )

    def render_conflict_indicators(self,
                                   surface: 'pygame.Surface',
                                   conflicts: List,
                                   camera: 'Camera') -> None:
        """
        Отрисовывает индикаторы конфликтов.

        Args:
            surface: Поверхность для рисования
            conflicts: Список активных конфликтов
            camera: Камера
        """
        if not self._initialized:
            return

        from .colors import ConflictColors

        for conflict in conflicts:
            if conflict.resolved:
                continue

            # Получаем цвет по стадии
            stage_name = conflict.stage.name
            color = getattr(ConflictColors, stage_name, Colors.TEXT_WARNING)

            # Рисуем индикатор в центре экрана (или где-то ещё)
            # Можно улучшить, рисуя около участников
            intensity = conflict.intensity
            size = int(20 + 30 * intensity)

            x = camera.screen_width // 2
            y = 50  # Верх экрана

            # Пульсирующий эффект
            import time
            pulse = abs(math.sin(time.time() * 3)) * 0.3 + 0.7

            # Рисуем предупреждающий круг
            self._pygame.draw.circle(
                surface,
                color,
                (x, y),
                int(size * pulse),
                3
            )

    def clear(self, surface: 'pygame.Surface') -> None:
        """Очищает поверхность"""
        if self._initialized:
            surface.fill(Colors.BACKGROUND)
