"""
Спрайты для NPC и других игровых объектов.

Каждый NPC отображается как спрайт с:
- Цветом класса
- Индикатором состояния
- Анимацией движения
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, TYPE_CHECKING
from enum import Enum, auto

if TYPE_CHECKING:
    import pygame

from .colors import ClassColors, ConsciousnessColors, RGB


class NPCState(Enum):
    """Состояние NPC для отображения"""
    IDLE = auto()
    MOVING = auto()
    WORKING = auto()
    FIGHTING = auto()
    SPEAKING = auto()
    DYING = auto()


@dataclass
class NPCSprite:
    """
    Спрайт NPC.

    Хранит информацию для отрисовки NPC:
    - Позиция в мире
    - Класс (для цвета)
    - Состояние
    - Анимация
    """
    npc_id: str
    x: float = 0.0
    y: float = 0.0

    # Визуальные характеристики
    class_name: str = "NONE"
    consciousness_level: float = 0.0
    is_leader: bool = False
    is_intellectual: bool = False

    # Состояние
    state: NPCState = NPCState.IDLE
    is_selected: bool = False
    is_hovered: bool = False

    # Анимация
    animation_frame: int = 0
    animation_timer: float = 0.0
    animation_speed: float = 0.2  # секунд на кадр

    # Для плавного движения
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    move_speed: float = 2.0  # тайлов в секунду

    # Размер спрайта
    size: int = 12  # пикселей (без масштаба камеры)

    def update(self, dt: float) -> None:
        """
        Обновляет спрайт.

        Args:
            dt: Время с последнего обновления (секунды)
        """
        # Анимация
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            self.animation_frame = (self.animation_frame + 1) % 4

        # Плавное движение
        if self.target_x is not None and self.target_y is not None:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < 0.05:
                self.x = self.target_x
                self.y = self.target_y
                self.target_x = None
                self.target_y = None
                self.state = NPCState.IDLE
            else:
                self.state = NPCState.MOVING
                move_dist = min(distance, self.move_speed * dt)
                self.x += dx / distance * move_dist
                self.y += dy / distance * move_dist

    def move_to(self, x: float, y: float) -> None:
        """Устанавливает целевую позицию для движения"""
        self.target_x = x
        self.target_y = y

    def set_position(self, x: float, y: float) -> None:
        """Мгновенно перемещает спрайт"""
        self.x = x
        self.y = y
        self.target_x = None
        self.target_y = None

    def get_color(self) -> RGB:
        """Возвращает основной цвет спрайта"""
        return ClassColors.for_class(self.class_name)

    def get_consciousness_color(self) -> RGB:
        """Возвращает цвет индикатора сознания"""
        if self.consciousness_level < 0.1:
            return ConsciousnessColors.NONE
        elif self.consciousness_level < 0.3:
            return ConsciousnessColors.ECONOMIC
        elif self.consciousness_level < 0.5:
            return ConsciousnessColors.CORPORATIVE
        elif self.consciousness_level < 0.7:
            return ConsciousnessColors.POLITICAL
        else:
            return ConsciousnessColors.HEGEMONIC

    def get_render_info(self) -> Dict:
        """
        Возвращает информацию для рендеринга.

        Returns:
            Словарь с параметрами отрисовки
        """
        return {
            'x': self.x,
            'y': self.y,
            'color': self.get_color(),
            'consciousness_color': self.get_consciousness_color(),
            'size': self.size,
            'is_selected': self.is_selected,
            'is_hovered': self.is_hovered,
            'is_leader': self.is_leader,
            'is_intellectual': self.is_intellectual,
            'state': self.state,
            'frame': self.animation_frame,
        }

    def contains_point(self, world_x: float, world_y: float,
                       tile_size: float) -> bool:
        """
        Проверяет, находится ли точка внутри спрайта.

        Args:
            world_x: X в мировых координатах
            world_y: Y в мировых координатах
            tile_size: Размер тайла с учётом масштаба

        Returns:
            True, если точка внутри спрайта
        """
        # Размер спрайта в мировых координатах
        sprite_size = self.size / tile_size

        return (abs(world_x - self.x) < sprite_size / 2 and
                abs(world_y - self.y) < sprite_size / 2)


class NPCSpriteGroup:
    """
    Группа спрайтов NPC.

    Управляет коллекцией спрайтов для эффективного обновления и рендеринга.
    """

    def __init__(self):
        self.sprites: Dict[str, NPCSprite] = {}
        self._selected_id: Optional[str] = None
        self._hovered_id: Optional[str] = None

    def add(self, sprite: NPCSprite) -> None:
        """Добавляет спрайт в группу"""
        self.sprites[sprite.npc_id] = sprite

    def remove(self, npc_id: str) -> None:
        """Удаляет спрайт из группы"""
        if npc_id in self.sprites:
            del self.sprites[npc_id]

    def get(self, npc_id: str) -> Optional[NPCSprite]:
        """Возвращает спрайт по ID"""
        return self.sprites.get(npc_id)

    def update(self, dt: float) -> None:
        """Обновляет все спрайты"""
        for sprite in self.sprites.values():
            sprite.update(dt)

    def update_from_simulation(self, npcs: Dict) -> None:
        """
        Синхронизирует спрайты с данными симуляции.

        Args:
            npcs: Словарь NPC из симуляции
        """
        # Обновляем существующие и добавляем новые
        for npc_id, npc in npcs.items():
            if npc_id not in self.sprites:
                self.sprites[npc_id] = NPCSprite(npc_id=npc_id)

            sprite = self.sprites[npc_id]

            # Обновляем позицию
            if hasattr(npc, 'x') and hasattr(npc, 'y'):
                sprite.move_to(npc.x, npc.y)

            # Обновляем класс
            if hasattr(npc, 'social_class'):
                sprite.class_name = npc.social_class.name if npc.social_class else "NONE"

            # Обновляем сознание
            if hasattr(npc, 'class_consciousness'):
                sprite.consciousness_level = npc.class_consciousness

        # Удаляем мёртвых NPC
        dead_ids = [npc_id for npc_id in self.sprites
                    if npc_id not in npcs]
        for npc_id in dead_ids:
            self.remove(npc_id)

    def get_at_position(self, world_x: float, world_y: float,
                        tile_size: float) -> Optional[NPCSprite]:
        """
        Возвращает спрайт в указанной позиции.

        Args:
            world_x: X в мировых координатах
            world_y: Y в мировых координатах
            tile_size: Размер тайла с учётом масштаба

        Returns:
            Спрайт или None
        """
        for sprite in self.sprites.values():
            if sprite.contains_point(world_x, world_y, tile_size):
                return sprite
        return None

    def select(self, npc_id: Optional[str]) -> None:
        """Выбирает спрайт"""
        # Снимаем старое выделение
        if self._selected_id and self._selected_id in self.sprites:
            self.sprites[self._selected_id].is_selected = False

        # Устанавливаем новое
        self._selected_id = npc_id
        if npc_id and npc_id in self.sprites:
            self.sprites[npc_id].is_selected = True

    def hover(self, npc_id: Optional[str]) -> None:
        """Устанавливает hover на спрайт"""
        # Снимаем старый hover
        if self._hovered_id and self._hovered_id in self.sprites:
            self.sprites[self._hovered_id].is_hovered = False

        # Устанавливаем новый
        self._hovered_id = npc_id
        if npc_id and npc_id in self.sprites:
            self.sprites[npc_id].is_hovered = True

    def get_selected(self) -> Optional[NPCSprite]:
        """Возвращает выбранный спрайт"""
        if self._selected_id:
            return self.sprites.get(self._selected_id)
        return None

    def get_visible(self, left: float, top: float,
                    right: float, bottom: float) -> List[NPCSprite]:
        """
        Возвращает спрайты в видимой области.

        Args:
            left, top, right, bottom: Границы области в мировых координатах

        Returns:
            Список видимых спрайтов
        """
        visible = []
        for sprite in self.sprites.values():
            if left <= sprite.x <= right and top <= sprite.y <= bottom:
                visible.append(sprite)
        return visible

    def get_by_class(self, class_name: str) -> List[NPCSprite]:
        """Возвращает спрайты указанного класса"""
        return [s for s in self.sprites.values() if s.class_name == class_name]

    def clear(self) -> None:
        """Очищает все спрайты"""
        self.sprites.clear()
        self._selected_id = None
        self._hovered_id = None

    def __len__(self) -> int:
        return len(self.sprites)

    def __iter__(self):
        return iter(self.sprites.values())
