"""
Информационные панели UI.

Панели для отображения:
- Статуса симуляции
- Информации о выбранном NPC
- Лога событий
- Статистики
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Callable, TYPE_CHECKING
from enum import Enum, auto

if TYPE_CHECKING:
    import pygame

from .colors import Colors, RGB


@dataclass
class PanelStyle:
    """Стиль панели"""
    bg_color: RGB = Colors.PANEL_BG
    border_color: RGB = Colors.PANEL_BORDER
    border_width: int = 1
    padding: int = 8
    font_size: int = 14
    title_font_size: int = 16
    line_height: int = 20


class PanelPosition(Enum):
    """Позиция панели на экране"""
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()
    TOP_CENTER = auto()
    BOTTOM_CENTER = auto()


@dataclass
class Panel:
    """
    Базовый класс панели.

    Панель - это прямоугольная область с информацией.
    """
    x: int = 0
    y: int = 0
    width: int = 200
    height: int = 150

    visible: bool = True
    title: str = ""
    style: PanelStyle = field(default_factory=PanelStyle)

    # Для pygame
    _surface: Optional['pygame.Surface'] = field(default=None, repr=False)
    _needs_redraw: bool = field(default=True, repr=False)

    def set_position(self, position: PanelPosition,
                     screen_width: int, screen_height: int,
                     margin: int = 10) -> None:
        """Устанавливает позицию панели на экране"""
        if position == PanelPosition.TOP_LEFT:
            self.x = margin
            self.y = margin
        elif position == PanelPosition.TOP_RIGHT:
            self.x = screen_width - self.width - margin
            self.y = margin
        elif position == PanelPosition.BOTTOM_LEFT:
            self.x = margin
            self.y = screen_height - self.height - margin
        elif position == PanelPosition.BOTTOM_RIGHT:
            self.x = screen_width - self.width - margin
            self.y = screen_height - self.height - margin
        elif position == PanelPosition.TOP_CENTER:
            self.x = (screen_width - self.width) // 2
            self.y = margin
        elif position == PanelPosition.BOTTOM_CENTER:
            self.x = (screen_width - self.width) // 2
            self.y = screen_height - self.height - margin

    def invalidate(self) -> None:
        """Помечает панель как требующую перерисовки"""
        self._needs_redraw = True

    def contains_point(self, x: int, y: int) -> bool:
        """Проверяет, находится ли точка внутри панели"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

    def get_rect(self) -> Tuple[int, int, int, int]:
        """Возвращает прямоугольник панели"""
        return (self.x, self.y, self.width, self.height)


@dataclass
class StatusBar(Panel):
    """
    Статусная строка в верхней части экрана.

    Отображает:
    - Текущий год и сезон
    - Население
    - Эпоху развития
    - Скорость симуляции
    """
    year: int = 0
    month: int = 1
    population: int = 0
    era: str = "Первобытная община"
    speed: int = 1
    is_paused: bool = False

    def __post_init__(self):
        self.height = 32
        self.title = ""

    def update_data(self, simulation) -> None:
        """Обновляет данные из симуляции"""
        self.year = simulation.year
        self.month = simulation.month
        self.population = len(simulation.npcs) if hasattr(simulation, 'npcs') else 0

        if hasattr(simulation, 'knowledge'):
            era = simulation.knowledge.get_current_era()
            self.era = era.russian_name if era else "Неизвестно"

        self.invalidate()

    def get_text(self) -> str:
        """Возвращает текст статусной строки"""
        months = [
            "Январь", "Февраль", "Март", "Апрель",
            "Май", "Июнь", "Июль", "Август",
            "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        month_name = months[self.month - 1] if 1 <= self.month <= 12 else "?"

        pause_text = " [ПАУЗА]" if self.is_paused else ""
        speed_text = f"x{self.speed}" if not self.is_paused else ""

        return (f"Год {self.year}, {month_name} | "
                f"Население: {self.population} | "
                f"{self.era} | {speed_text}{pause_text}")


@dataclass
class InfoPanel(Panel):
    """
    Панель информации о выбранном объекте.

    Отображает детали о NPC или локации.
    """
    # Данные о выбранном объекте
    selected_id: Optional[str] = None
    selected_type: str = "none"  # "npc", "location", "resource"

    # Данные NPC
    npc_name: str = ""
    npc_age: int = 0
    npc_class: str = ""
    npc_wealth: float = 0.0
    npc_consciousness: float = 0.0
    npc_traits: List[str] = field(default_factory=list)
    npc_relations: List[Tuple[str, str, float]] = field(default_factory=list)

    def __post_init__(self):
        self.width = 250
        self.height = 300
        self.title = "Информация"

    def set_selected_npc(self, npc_id: str, npc) -> None:
        """Устанавливает выбранного NPC"""
        self.selected_id = npc_id
        self.selected_type = "npc"

        self.npc_name = getattr(npc, 'name', npc_id)
        self.npc_age = getattr(npc, 'age', 0)

        if hasattr(npc, 'social_class') and npc.social_class:
            self.npc_class = npc.social_class.russian_name
        else:
            self.npc_class = "Нет класса"

        self.npc_wealth = getattr(npc, 'wealth', 0.0)
        self.npc_consciousness = getattr(npc, 'class_consciousness', 0.0)

        if hasattr(npc, 'personality'):
            self.npc_traits = [
                f"{k}: {v}" for k, v in npc.personality.__dict__.items()
            ][:5]
        else:
            self.npc_traits = []

        self.invalidate()

    def clear_selection(self) -> None:
        """Снимает выделение"""
        self.selected_id = None
        self.selected_type = "none"
        self.invalidate()

    def get_lines(self) -> List[Tuple[str, RGB]]:
        """Возвращает строки для отрисовки"""
        if self.selected_type == "none":
            return [("Нажмите на NPC", Colors.TEXT_SECONDARY)]

        if self.selected_type == "npc":
            lines = [
                (f"Имя: {self.npc_name}", Colors.TEXT_PRIMARY),
                (f"Возраст: {self.npc_age} лет", Colors.TEXT_PRIMARY),
                ("", Colors.TEXT_PRIMARY),
                (f"Класс: {self.npc_class}", Colors.TEXT_ACCENT),
                (f"Богатство: {self.npc_wealth:.0f}", Colors.TEXT_PRIMARY),
                (f"Сознание: {self.npc_consciousness:.0%}", Colors.TEXT_PRIMARY),
            ]

            if self.npc_traits:
                lines.append(("", Colors.TEXT_PRIMARY))
                lines.append(("Черты:", Colors.TEXT_SECONDARY))
                for trait in self.npc_traits[:3]:
                    lines.append((f"  {trait}", Colors.TEXT_PRIMARY))

            return lines

        return []


@dataclass
class EventLog(Panel):
    """
    Лог событий.

    Отображает последние события симуляции.
    """
    events: List[Tuple[str, RGB]] = field(default_factory=list)
    max_events: int = 20
    scroll_offset: int = 0

    def __post_init__(self):
        self.width = 350
        self.height = 200
        self.title = "События"

    def add_event(self, text: str, color: RGB = Colors.TEXT_PRIMARY) -> None:
        """Добавляет событие в лог"""
        self.events.append((text, color))
        if len(self.events) > self.max_events:
            self.events.pop(0)
        self.invalidate()

    def add_events_from_simulation(self, events: List[str]) -> None:
        """Добавляет события из симуляции"""
        for event in events:
            # Определяем цвет по типу события
            color = Colors.TEXT_PRIMARY
            if "конфликт" in event.lower() or "восстание" in event.lower():
                color = Colors.TEXT_WARNING
            elif "революция" in event.lower():
                color = Colors.TEXT_DANGER
            elif "родился" in event.lower() or "рождение" in event.lower():
                color = Colors.TEXT_SUCCESS
            elif "умер" in event.lower() or "смерть" in event.lower():
                color = Colors.TEXT_SECONDARY

            self.add_event(event, color)

    def clear(self) -> None:
        """Очищает лог"""
        self.events.clear()
        self.scroll_offset = 0
        self.invalidate()

    def scroll_up(self) -> None:
        """Прокручивает вверх"""
        self.scroll_offset = max(0, self.scroll_offset - 1)
        self.invalidate()

    def scroll_down(self) -> None:
        """Прокручивает вниз"""
        max_scroll = max(0, len(self.events) - 8)  # 8 видимых строк
        self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
        self.invalidate()

    def get_visible_events(self) -> List[Tuple[str, RGB]]:
        """Возвращает видимые события"""
        start = self.scroll_offset
        end = start + 8  # Примерно 8 строк помещается
        return self.events[start:end]


@dataclass
class StatisticsPanel(Panel):
    """
    Панель статистики.

    Отображает:
    - Распределение по классам
    - Уровень неравенства
    - Активные конфликты
    - Технологии
    """
    class_distribution: Dict[str, int] = field(default_factory=dict)
    inequality: float = 0.0
    tension: float = 0.0
    active_conflicts: int = 0
    technologies_count: int = 0

    def __post_init__(self):
        self.width = 200
        self.height = 250
        self.title = "Статистика"

    def update_from_simulation(self, simulation) -> None:
        """Обновляет статистику из симуляции"""
        if hasattr(simulation, 'classes'):
            self.class_distribution = simulation.classes.get_class_distribution()
            self.tension = simulation.classes.check_class_tension()
            self.active_conflicts = len(simulation.classes.get_active_conflicts())

        if hasattr(simulation, 'ownership'):
            self.inequality = simulation.ownership.calculate_inequality()

        if hasattr(simulation, 'knowledge'):
            self.technologies_count = len(simulation.knowledge.discovered_technologies)

        self.invalidate()

    def get_lines(self) -> List[Tuple[str, RGB]]:
        """Возвращает строки для отрисовки"""
        lines = []

        # Классы
        lines.append(("Классы:", Colors.TEXT_ACCENT))
        for class_name, count in self.class_distribution.items():
            lines.append((f"  {class_name}: {count}", Colors.TEXT_PRIMARY))

        lines.append(("", Colors.TEXT_PRIMARY))

        # Показатели
        lines.append((f"Неравенство: {self.inequality:.2f}", Colors.TEXT_PRIMARY))

        tension_color = Colors.TEXT_PRIMARY
        if self.tension > 0.7:
            tension_color = Colors.TEXT_DANGER
        elif self.tension > 0.4:
            tension_color = Colors.TEXT_WARNING
        lines.append((f"Напряжённость: {self.tension:.0%}", tension_color))

        if self.active_conflicts > 0:
            lines.append((f"Конфликтов: {self.active_conflicts}", Colors.TEXT_WARNING))
        else:
            lines.append(("Конфликтов: 0", Colors.TEXT_SUCCESS))

        lines.append(("", Colors.TEXT_PRIMARY))
        lines.append((f"Технологий: {self.technologies_count}", Colors.TEXT_ACCENT))

        return lines


@dataclass
class Button:
    """Кнопка UI"""
    x: int = 0
    y: int = 0
    width: int = 100
    height: int = 30
    text: str = "Button"
    enabled: bool = True
    is_hovered: bool = False
    is_pressed: bool = False
    on_click: Optional[Callable] = None

    def contains_point(self, px: int, py: int) -> bool:
        """Проверяет, находится ли точка внутри кнопки"""
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

    def get_color(self) -> RGB:
        """Возвращает текущий цвет кнопки"""
        if not self.enabled:
            return Colors.BUTTON_DISABLED
        if self.is_pressed:
            return Colors.BUTTON_PRESSED
        if self.is_hovered:
            return Colors.BUTTON_HOVER
        return Colors.BUTTON_NORMAL

    def click(self) -> None:
        """Вызывает обработчик клика"""
        if self.enabled and self.on_click:
            self.on_click()


@dataclass
class SpeedControls:
    """Контроллер скорости симуляции"""
    x: int = 0
    y: int = 0

    buttons: List[Button] = field(default_factory=list)
    current_speed: int = 1
    is_paused: bool = False

    on_speed_change: Optional[Callable[[int], None]] = None
    on_pause: Optional[Callable[[bool], None]] = None

    def __post_init__(self):
        self._create_buttons()

    def _create_buttons(self) -> None:
        """Создаёт кнопки управления скоростью"""
        button_width = 40
        spacing = 5

        # Кнопка паузы
        self.buttons = [
            Button(
                x=self.x, y=self.y,
                width=button_width, height=25,
                text="||" if not self.is_paused else ">",
                on_click=self._toggle_pause
            ),
        ]

        # Кнопки скорости
        for i, speed in enumerate([1, 2, 5, 10]):
            self.buttons.append(Button(
                x=self.x + (i + 1) * (button_width + spacing),
                y=self.y,
                width=button_width, height=25,
                text=f"x{speed}",
                on_click=lambda s=speed: self._set_speed(s)
            ))

    def _toggle_pause(self) -> None:
        """Переключает паузу"""
        self.is_paused = not self.is_paused
        self.buttons[0].text = ">" if self.is_paused else "||"
        if self.on_pause:
            self.on_pause(self.is_paused)

    def _set_speed(self, speed: int) -> None:
        """Устанавливает скорость"""
        self.current_speed = speed
        if self.on_speed_change:
            self.on_speed_change(speed)

    def set_position(self, x: int, y: int) -> None:
        """Перемещает контроллер"""
        dx = x - self.x
        dy = y - self.y
        self.x = x
        self.y = y
        for button in self.buttons:
            button.x += dx
            button.y += dy

    def handle_click(self, x: int, y: int) -> bool:
        """Обрабатывает клик"""
        for button in self.buttons:
            if button.contains_point(x, y):
                button.click()
                return True
        return False
