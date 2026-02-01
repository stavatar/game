"""
Камера для управления видимой областью карты.

Поддерживает:
- Прокрутку (scroll) с помощью мыши и клавиатуры
- Масштабирование (zoom)
- Плавное перемещение к точке
- Границы карты
"""
from dataclasses import dataclass, field
from typing import Tuple, Optional
import math


@dataclass
class Camera:
    """
    Камера для просмотра карты.

    Камера определяет, какая часть мира видна на экране.
    Поддерживает scroll и zoom.
    """
    # Размер экрана (в пикселях)
    screen_width: int = 800
    screen_height: int = 600

    # Размер мира (в тайлах)
    world_width: int = 100
    world_height: int = 100

    # Размер тайла (в пикселях)
    tile_size: int = 16

    # Позиция камеры (центр, в мировых координатах)
    x: float = 0.0
    y: float = 0.0

    # Масштаб
    zoom: float = 1.0
    min_zoom: float = 0.5
    max_zoom: float = 3.0

    # Скорость прокрутки (пикселей в секунду)
    scroll_speed: float = 300.0

    # Плавное перемещение
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    move_speed: float = 500.0

    # Границы
    _bound_left: float = field(init=False, default=0.0)
    _bound_right: float = field(init=False, default=0.0)
    _bound_top: float = field(init=False, default=0.0)
    _bound_bottom: float = field(init=False, default=0.0)

    def __post_init__(self):
        """Инициализация после создания"""
        self._update_bounds()

    def _update_bounds(self) -> None:
        """Обновляет границы камеры"""
        # Размер видимой области в мировых координатах
        view_width = self.screen_width / (self.tile_size * self.zoom)
        view_height = self.screen_height / (self.tile_size * self.zoom)

        # Границы - камера не может выйти за пределы мира
        self._bound_left = view_width / 2
        self._bound_right = self.world_width - view_width / 2
        self._bound_top = view_height / 2
        self._bound_bottom = self.world_height - view_height / 2

    def set_world_size(self, width: int, height: int) -> None:
        """Устанавливает размер мира"""
        self.world_width = width
        self.world_height = height
        self._update_bounds()

    def set_screen_size(self, width: int, height: int) -> None:
        """Устанавливает размер экрана"""
        self.screen_width = width
        self.screen_height = height
        self._update_bounds()

    def move(self, dx: float, dy: float) -> None:
        """Перемещает камеру на указанное смещение"""
        self.x = self._clamp_x(self.x + dx)
        self.y = self._clamp_y(self.y + dy)

    def move_to(self, x: float, y: float, smooth: bool = True) -> None:
        """Перемещает камеру к указанной позиции"""
        if smooth:
            self.target_x = self._clamp_x(x)
            self.target_y = self._clamp_y(y)
        else:
            self.x = self._clamp_x(x)
            self.y = self._clamp_y(y)
            self.target_x = None
            self.target_y = None

    def center_on(self, x: float, y: float, smooth: bool = True) -> None:
        """Центрирует камеру на указанной позиции"""
        self.move_to(x, y, smooth)

    def set_zoom(self, zoom: float) -> None:
        """Устанавливает масштаб"""
        self.zoom = max(self.min_zoom, min(self.max_zoom, zoom))
        self._update_bounds()
        # Корректируем позицию с новыми границами
        self.x = self._clamp_x(self.x)
        self.y = self._clamp_y(self.y)

    def zoom_in(self, factor: float = 1.1) -> None:
        """Увеличивает масштаб"""
        self.set_zoom(self.zoom * factor)

    def zoom_out(self, factor: float = 1.1) -> None:
        """Уменьшает масштаб"""
        self.set_zoom(self.zoom / factor)

    def zoom_at(self, screen_x: int, screen_y: int, factor: float) -> None:
        """Масштабирование с центром в указанной точке экрана"""
        # Мировые координаты точки до масштабирования
        world_x, world_y = self.screen_to_world(screen_x, screen_y)

        # Применяем масштаб
        old_zoom = self.zoom
        self.set_zoom(self.zoom * factor)

        if self.zoom != old_zoom:
            # Корректируем позицию, чтобы точка осталась на месте
            new_world_x, new_world_y = self.screen_to_world(screen_x, screen_y)
            self.x += world_x - new_world_x
            self.y += world_y - new_world_y

    def update(self, dt: float) -> None:
        """
        Обновляет камеру.

        Args:
            dt: Время с последнего обновления (в секундах)
        """
        # Плавное перемещение к цели
        if self.target_x is not None and self.target_y is not None:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.1:
                self.x = self.target_x
                self.y = self.target_y
                self.target_x = None
                self.target_y = None
            else:
                move_distance = min(distance, self.move_speed * dt)
                self.x += dx / distance * move_distance
                self.y += dy / distance * move_distance

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """
        Преобразует мировые координаты в экранные.

        Args:
            world_x: X в мировых координатах (тайлах)
            world_y: Y в мировых координатах (тайлах)

        Returns:
            (screen_x, screen_y) в пикселях
        """
        # Смещение относительно центра камеры
        rel_x = world_x - self.x
        rel_y = world_y - self.y

        # Масштабируем и переводим в экранные координаты
        screen_x = int(self.screen_width / 2 + rel_x * self.tile_size * self.zoom)
        screen_y = int(self.screen_height / 2 + rel_y * self.tile_size * self.zoom)

        return screen_x, screen_y

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """
        Преобразует экранные координаты в мировые.

        Args:
            screen_x: X в пикселях
            screen_y: Y в пикселях

        Returns:
            (world_x, world_y) в тайлах
        """
        # Смещение от центра экрана
        rel_x = (screen_x - self.screen_width / 2) / (self.tile_size * self.zoom)
        rel_y = (screen_y - self.screen_height / 2) / (self.tile_size * self.zoom)

        # Добавляем позицию камеры
        world_x = self.x + rel_x
        world_y = self.y + rel_y

        return world_x, world_y

    def get_visible_rect(self) -> Tuple[int, int, int, int]:
        """
        Возвращает видимую область в мировых координатах.

        Returns:
            (left, top, right, bottom) в тайлах
        """
        half_width = self.screen_width / (2 * self.tile_size * self.zoom)
        half_height = self.screen_height / (2 * self.tile_size * self.zoom)

        left = max(0, int(self.x - half_width) - 1)
        top = max(0, int(self.y - half_height) - 1)
        right = min(self.world_width, int(self.x + half_width) + 2)
        bottom = min(self.world_height, int(self.y + half_height) + 2)

        return left, top, right, bottom

    def is_visible(self, world_x: float, world_y: float,
                   margin: float = 1.0) -> bool:
        """
        Проверяет, видна ли точка на экране.

        Args:
            world_x: X в мировых координатах
            world_y: Y в мировых координатах
            margin: Запас в тайлах

        Returns:
            True, если точка видна
        """
        left, top, right, bottom = self.get_visible_rect()
        return (left - margin <= world_x <= right + margin and
                top - margin <= world_y <= bottom + margin)

    def _clamp_x(self, x: float) -> float:
        """Ограничивает X в пределах границ"""
        if self._bound_left >= self._bound_right:
            return self.world_width / 2
        return max(self._bound_left, min(self._bound_right, x))

    def _clamp_y(self, y: float) -> float:
        """Ограничивает Y в пределах границ"""
        if self._bound_top >= self._bound_bottom:
            return self.world_height / 2
        return max(self._bound_top, min(self._bound_bottom, y))

    def get_scaled_tile_size(self) -> float:
        """Возвращает размер тайла с учётом масштаба"""
        return self.tile_size * self.zoom

    def handle_scroll(self, keys_pressed: dict, dt: float) -> None:
        """
        Обрабатывает прокрутку с клавиатуры.

        Args:
            keys_pressed: Словарь с состоянием клавиш
            dt: Время с последнего обновления
        """
        move_amount = self.scroll_speed * dt / (self.tile_size * self.zoom)

        if keys_pressed.get('up') or keys_pressed.get('w'):
            self.move(0, -move_amount)
        if keys_pressed.get('down') or keys_pressed.get('s'):
            self.move(0, move_amount)
        if keys_pressed.get('left') or keys_pressed.get('a'):
            self.move(-move_amount, 0)
        if keys_pressed.get('right') or keys_pressed.get('d'):
            self.move(move_amount, 0)
