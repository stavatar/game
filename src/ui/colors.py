"""
Цветовая палитра для UI.

Определяет цвета для:
- Типов местности
- Классов NPC
- UI элементов
"""
from dataclasses import dataclass
from typing import Tuple

# RGB тип
RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]


@dataclass(frozen=True)
class Colors:
    """Базовые цвета UI"""
    # Фон
    BACKGROUND: RGB = (20, 20, 30)
    PANEL_BG: RGB = (30, 30, 45)
    PANEL_BORDER: RGB = (60, 60, 80)

    # Текст
    TEXT_PRIMARY: RGB = (240, 240, 240)
    TEXT_SECONDARY: RGB = (180, 180, 180)
    TEXT_ACCENT: RGB = (100, 200, 255)
    TEXT_WARNING: RGB = (255, 200, 100)
    TEXT_DANGER: RGB = (255, 100, 100)
    TEXT_SUCCESS: RGB = (100, 255, 150)

    # Кнопки
    BUTTON_NORMAL: RGB = (60, 60, 80)
    BUTTON_HOVER: RGB = (80, 80, 100)
    BUTTON_PRESSED: RGB = (40, 40, 60)
    BUTTON_DISABLED: RGB = (40, 40, 50)

    # Прогресс-бары
    PROGRESS_BG: RGB = (40, 40, 50)
    PROGRESS_FILL: RGB = (100, 180, 255)

    # Выделение
    SELECTION: RGB = (255, 255, 100)
    HIGHLIGHT: RGB = (100, 200, 255)


@dataclass(frozen=True)
class TerrainColors:
    """Цвета типов местности"""
    # Базовые
    GRASS: RGB = (80, 140, 80)
    GRASS_LIGHT: RGB = (100, 160, 100)
    GRASS_DARK: RGB = (60, 120, 60)

    # Вода
    WATER: RGB = (60, 100, 180)
    WATER_DEEP: RGB = (40, 70, 140)
    WATER_SHALLOW: RGB = (80, 130, 200)

    # Лес
    FOREST: RGB = (40, 100, 50)
    FOREST_DENSE: RGB = (30, 80, 40)

    # Горы
    MOUNTAIN: RGB = (120, 110, 100)
    MOUNTAIN_PEAK: RGB = (200, 200, 210)

    # Пустыня
    DESERT: RGB = (200, 180, 120)
    SAND: RGB = (220, 200, 140)

    # Постройки
    BUILDING: RGB = (140, 120, 100)
    ROAD: RGB = (100, 90, 80)

    # Ресурсы
    RESOURCE: RGB = (200, 180, 100)
    RESOURCE_DEPLETED: RGB = (100, 90, 80)

    @classmethod
    def for_tile(cls, tile_type: str) -> RGB:
        """Возвращает цвет для типа тайла"""
        mapping = {
            'grass': cls.GRASS,
            'water': cls.WATER,
            'forest': cls.FOREST,
            'mountain': cls.MOUNTAIN,
            'desert': cls.DESERT,
            'building': cls.BUILDING,
            'road': cls.ROAD,
            '.': cls.GRASS,
            '~': cls.WATER,
            'T': cls.FOREST,
            '^': cls.MOUNTAIN,
            '#': cls.BUILDING,
        }
        return mapping.get(tile_type, cls.GRASS)


@dataclass(frozen=True)
class ClassColors:
    """Цвета для классов NPC (по марксистской теории)"""
    # Эксплуатируемые классы (тёплые тона - активность, борьба)
    LANDLESS: RGB = (200, 100, 80)      # Красноватый - безземельные
    LABORER: RGB = (220, 120, 80)       # Оранжевый - работники

    # Эксплуататорские классы (холодные тона - накопление)
    LANDOWNER: RGB = (80, 120, 180)     # Синий - землевладельцы
    CHIEF: RGB = (100, 80, 160)         # Фиолетовый - вожди

    # Переходные классы
    CRAFTSMAN: RGB = (140, 140, 100)    # Жёлто-зелёный - ремесленники

    # Общинные
    COMMUNAL_MEMBER: RGB = (120, 160, 120)  # Зелёный - общинники
    ELDER: RGB = (160, 160, 180)        # Серо-голубой - старейшины

    # По умолчанию
    NONE: RGB = (128, 128, 128)         # Серый

    @classmethod
    def for_class(cls, class_name: str) -> RGB:
        """Возвращает цвет для класса по имени"""
        mapping = {
            'LANDLESS': cls.LANDLESS,
            'LABORER': cls.LABORER,
            'LANDOWNER': cls.LANDOWNER,
            'CHIEF': cls.CHIEF,
            'CRAFTSMAN': cls.CRAFTSMAN,
            'COMMUNAL_MEMBER': cls.COMMUNAL_MEMBER,
            'ELDER': cls.ELDER,
            'NONE': cls.NONE,
            # Русские названия
            'безземельный': cls.LANDLESS,
            'работник': cls.LABORER,
            'землевладелец': cls.LANDOWNER,
            'вождь': cls.CHIEF,
            'ремесленник': cls.CRAFTSMAN,
            'общинник': cls.COMMUNAL_MEMBER,
            'старейшина': cls.ELDER,
        }
        return mapping.get(class_name, cls.NONE)


@dataclass(frozen=True)
class ConflictColors:
    """Цвета для конфликтов"""
    BREWING: RGB = (180, 180, 100)      # Жёлтый - назревание
    LATENT: RGB = (200, 160, 80)        # Оранжево-жёлтый
    ACTIVE: RGB = (220, 120, 60)        # Оранжевый - активный
    ESCALATING: RGB = (240, 80, 60)     # Красно-оранжевый
    CRISIS: RGB = (255, 50, 50)         # Красный - кризис
    RESOLVED: RGB = (100, 180, 100)     # Зелёный - разрешён


@dataclass(frozen=True)
class ConsciousnessColors:
    """Цвета для уровней классового сознания"""
    NONE: RGB = (100, 100, 100)         # Серый
    ECONOMIC: RGB = (150, 150, 100)     # Бледно-жёлтый
    CORPORATIVE: RGB = (180, 140, 80)   # Оранжевый
    POLITICAL: RGB = (200, 100, 80)     # Красноватый
    HEGEMONIC: RGB = (220, 60, 60)      # Ярко-красный


def blend_colors(color1: RGB, color2: RGB, factor: float) -> RGB:
    """Смешивает два цвета с заданным фактором (0.0 - 1.0)"""
    factor = max(0.0, min(1.0, factor))
    return (
        int(color1[0] * (1 - factor) + color2[0] * factor),
        int(color1[1] * (1 - factor) + color2[1] * factor),
        int(color1[2] * (1 - factor) + color2[2] * factor),
    )


def darken_color(color: RGB, factor: float = 0.2) -> RGB:
    """Затемняет цвет"""
    return (
        int(color[0] * (1 - factor)),
        int(color[1] * (1 - factor)),
        int(color[2] * (1 - factor)),
    )


def lighten_color(color: RGB, factor: float = 0.2) -> RGB:
    """Осветляет цвет"""
    return (
        min(255, int(color[0] + (255 - color[0]) * factor)),
        min(255, int(color[1] + (255 - color[1]) * factor)),
        min(255, int(color[2] + (255 - color[2]) * factor)),
    )
