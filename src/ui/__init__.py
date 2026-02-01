"""
Графический интерфейс для симулятора "Базис и Надстройка".

Модуль предоставляет:
- GameWindow: главное окно с игровым циклом
- MapRenderer: рендеринг карты мира
- NPCSprite: спрайты NPC с индикаторами класса
- InfoPanel: панели информации
- Camera: управление камерой (scroll/zoom)

Использует pygame для рендеринга.

Архитектура:
- Fixed time step для симуляции (независимо от FPS)
- Game Loop: poll events → update simulation → render
- Separation of concerns: логика отделена от рендеринга

Источники:
- https://gameprogrammingpatterns.com/game-loop.html
- https://www.pygame.org/docs/tut/newbieguide.html
- https://pygame-gui.readthedocs.io/
"""
from .window import GameWindow
from .renderer import MapRenderer
from .sprites import NPCSprite, NPCSpriteGroup
from .panels import InfoPanel, StatusBar, EventLog
from .camera import Camera
from .colors import Colors, ClassColors, TerrainColors

__all__ = [
    'GameWindow',
    'MapRenderer',
    'NPCSprite',
    'NPCSpriteGroup',
    'InfoPanel',
    'StatusBar',
    'EventLog',
    'Camera',
    'Colors',
    'ClassColors',
    'TerrainColors',
]
