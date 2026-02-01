"""
Главное окно игры с игровым циклом.

Реализует:
- Fixed time step для симуляции
- Variable rendering (рендеринг с максимальным FPS)
- Event handling (мышь, клавиатура)
- Интеграция UI панелей
"""
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from ..core.simulation import Simulation
    from ..persistence import SaveManager

# Импортируем pygame при инициализации
pygame = None


@dataclass
class GameWindow:
    """
    Главное окно игры.

    Управляет:
    - Игровым циклом
    - Рендерингом
    - Обработкой ввода
    - Панелями UI
    """

    # Размеры окна
    width: int = 1280
    height: int = 720
    title: str = "Базис и Надстройка"

    # Симуляция
    simulation: Optional['Simulation'] = None

    # FPS и тайминг
    target_fps: int = 60
    simulation_speed: int = 1  # Множитель скорости
    is_paused: bool = False

    # Fixed time step для симуляции (часов симуляции в секунду реального времени)
    hours_per_second: float = 24.0  # 1 день = 1 секунда при speed=1

    # Состояние
    running: bool = False
    _initialized: bool = False

    # Pygame объекты
    _screen: Optional[object] = field(default=None, repr=False)
    _clock: Optional[object] = field(default=None, repr=False)

    # Компоненты UI
    _camera: Optional[object] = field(default=None, repr=False)
    _renderer: Optional[object] = field(default=None, repr=False)
    _sprites: Optional[object] = field(default=None, repr=False)

    # Панели
    _status_bar: Optional[object] = field(default=None, repr=False)
    _info_panel: Optional[object] = field(default=None, repr=False)
    _event_log: Optional[object] = field(default=None, repr=False)
    _stats_panel: Optional[object] = field(default=None, repr=False)
    _speed_controls: Optional[object] = field(default=None, repr=False)

    # Шрифты
    _font: Optional[object] = field(default=None, repr=False)
    _font_small: Optional[object] = field(default=None, repr=False)
    _font_title: Optional[object] = field(default=None, repr=False)

    # Состояние ввода
    _keys_pressed: Dict[str, bool] = field(default_factory=dict)
    _mouse_dragging: bool = False
    _last_mouse_pos: tuple = (0, 0)

    # Save Manager
    _save_manager: Optional['SaveManager'] = field(default=None, repr=False)
    _save_message: str = ""
    _save_message_time: float = 0.0

    def initialize(self) -> bool:
        """
        Инициализирует pygame и создаёт окно.

        Returns:
            True если успешно
        """
        global pygame
        try:
            import pygame as pg
            pygame = pg
        except ImportError:
            print("Ошибка: pygame не установлен.")
            print("Установите: pip install pygame")
            return False

        # Инициализируем pygame
        pygame.init()
        pygame.font.init()

        # Создаём окно
        self._screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE
        )
        pygame.display.set_caption(self.title)

        # Часы для FPS
        self._clock = pygame.time.Clock()

        # Шрифты (используем системные или встроенные)
        try:
            self._font = pygame.font.SysFont("Arial", 14)
            self._font_small = pygame.font.SysFont("Arial", 12)
            self._font_title = pygame.font.SysFont("Arial", 16, bold=True)
        except:
            self._font = pygame.font.Font(None, 18)
            self._font_small = pygame.font.Font(None, 14)
            self._font_title = pygame.font.Font(None, 22)

        # Инициализируем компоненты
        self._init_components()

        self._initialized = True
        return True

    def _init_components(self) -> None:
        """Инициализирует компоненты UI"""
        from .camera import Camera
        from .renderer import MapRenderer
        from .sprites import NPCSpriteGroup
        from .panels import (
            StatusBar, InfoPanel, EventLog,
            StatisticsPanel, SpeedControls, PanelPosition
        )

        # Камера
        self._camera = Camera(
            screen_width=self.width,
            screen_height=self.height,
            tile_size=16
        )

        # Если есть симуляция, настраиваем камеру
        if self.simulation and hasattr(self.simulation, 'config'):
            self._camera.set_world_size(
                self.simulation.config.map_width,
                self.simulation.config.map_height
            )
            # Центрируем камеру
            self._camera.center_on(
                self.simulation.config.map_width / 2,
                self.simulation.config.map_height / 2,
                smooth=False
            )

        # Рендерер
        self._renderer = MapRenderer()
        self._renderer.initialize(pygame)

        # Спрайты NPC
        self._sprites = NPCSpriteGroup()

        # Панели
        self._status_bar = StatusBar()
        self._status_bar.width = self.width
        self._status_bar.set_position(PanelPosition.TOP_LEFT, self.width, self.height, 0)

        self._info_panel = InfoPanel()
        self._info_panel.set_position(PanelPosition.TOP_RIGHT, self.width, self.height)

        self._event_log = EventLog()
        self._event_log.set_position(PanelPosition.BOTTOM_LEFT, self.width, self.height)

        self._stats_panel = StatisticsPanel()
        self._stats_panel.set_position(PanelPosition.BOTTOM_RIGHT, self.width, self.height)

        # Контроллер скорости
        self._speed_controls = SpeedControls(
            x=self.width // 2 - 100,
            y=self.height - 35,
            on_speed_change=self._on_speed_change,
            on_pause=self._on_pause
        )

    def _on_speed_change(self, speed: int) -> None:
        """Обработчик изменения скорости"""
        self.simulation_speed = speed

    def _on_pause(self, is_paused: bool) -> None:
        """Обработчик паузы"""
        self.is_paused = is_paused

    def set_simulation(self, simulation: 'Simulation') -> None:
        """Устанавливает симуляцию"""
        self.simulation = simulation

        if self._initialized and self._camera:
            self._camera.set_world_size(
                simulation.config.map_width,
                simulation.config.map_height
            )
            self._camera.center_on(
                simulation.config.map_width / 2,
                simulation.config.map_height / 2,
                smooth=False
            )

    def set_save_manager(self, save_manager: 'SaveManager') -> None:
        """Устанавливает менеджер сохранений"""
        self._save_manager = save_manager

    def _show_message(self, message: str) -> None:
        """Показывает временное сообщение"""
        self._save_message = message
        self._save_message_time = time.time()

    def run(self) -> None:
        """
        Запускает главный игровой цикл.

        Использует fixed time step для симуляции:
        - Симуляция обновляется с фиксированным шагом
        - Рендеринг происходит с максимальным FPS
        """
        if not self._initialized:
            if not self.initialize():
                return

        self.running = True
        last_time = time.time()
        accumulator = 0.0

        # Фиксированный шаг симуляции (в секундах реального времени)
        fixed_dt = 1.0 / 30.0  # 30 обновлений в секунду

        while self.running:
            # Время кадра
            current_time = time.time()
            frame_time = current_time - last_time
            last_time = current_time

            # Ограничиваем frame_time (защита от лагов)
            frame_time = min(frame_time, 0.25)

            # Обработка событий
            self._handle_events()

            if not self.running:
                break

            # Обновление камеры (всегда)
            self._camera.update(frame_time)
            self._camera.handle_scroll(self._keys_pressed, frame_time)

            # Fixed time step для симуляции
            if not self.is_paused:
                accumulator += frame_time

                while accumulator >= fixed_dt:
                    # Вычисляем сколько игровых часов прошло
                    hours = self.hours_per_second * self.simulation_speed * fixed_dt
                    hours = int(hours) if hours >= 1 else 1

                    # Обновляем симуляцию
                    events = self._update_simulation(hours)

                    # Добавляем события в лог
                    if events:
                        self._event_log.add_events_from_simulation(events[-5:])

                    accumulator -= fixed_dt

            # Обновляем спрайты (анимация)
            self._sprites.update(frame_time)

            # Синхронизируем спрайты с симуляцией
            if self.simulation:
                self._sync_sprites()

            # Рендеринг
            self._render()

            # FPS control
            self._clock.tick(self.target_fps)

        # Очистка
        pygame.quit()

    def _update_simulation(self, hours: int) -> List[str]:
        """
        Обновляет симуляцию.

        Args:
            hours: Количество игровых часов

        Returns:
            Список событий
        """
        if not self.simulation:
            return []

        events = self.simulation.update(hours)

        # Обновляем панели
        self._status_bar.update_data(self.simulation)
        self._stats_panel.update_from_simulation(self.simulation)

        return events

    def _sync_sprites(self) -> None:
        """Синхронизирует спрайты с данными симуляции"""
        if not self.simulation:
            return

        # Обновляем существующие спрайты
        for npc_id, npc in self.simulation.npcs.items():
            sprite = self._sprites.get(npc_id)

            if sprite is None:
                from .sprites import NPCSprite
                sprite = NPCSprite(npc_id=npc_id)
                self._sprites.add(sprite)

            # Позиция
            if hasattr(npc, 'x') and hasattr(npc, 'y'):
                if sprite.target_x is None:
                    sprite.set_position(npc.x, npc.y)
                else:
                    sprite.move_to(npc.x, npc.y)

            # Класс
            if hasattr(self.simulation, 'classes'):
                npc_class = self.simulation.classes.npc_class.get(npc_id)
                if npc_class:
                    sprite.class_name = npc_class.name

                    # Сознание
                    if npc_class in self.simulation.classes.classes:
                        sprite.consciousness_level = \
                            self.simulation.classes.classes[npc_class].class_consciousness

                    # Лидер/интеллектуал
                    sprite.is_intellectual = npc_id in \
                        self.simulation.classes.consciousness_system.organic_intellectuals

                    # Проверяем лидерство в активных конфликтах
                    for conflict in self.simulation.classes.get_active_conflicts():
                        if npc_id in conflict.leaders:
                            sprite.is_leader = True
                            break
                    else:
                        sprite.is_leader = False

        # Удаляем мёртвых NPC
        dead_ids = [npc_id for npc_id in list(self._sprites.sprites.keys())
                    if npc_id not in self.simulation.npcs]
        for npc_id in dead_ids:
            self._sprites.remove(npc_id)

    def _handle_events(self) -> None:
        """Обрабатывает события pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self._on_resize(event.w, event.h)

            elif event.type == pygame.KEYDOWN:
                self._on_key_down(event)

            elif event.type == pygame.KEYUP:
                self._on_key_up(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._on_mouse_down(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                self._on_mouse_up(event)

            elif event.type == pygame.MOUSEMOTION:
                self._on_mouse_motion(event)

            elif event.type == pygame.MOUSEWHEEL:
                self._on_mouse_wheel(event)

    def _on_resize(self, width: int, height: int) -> None:
        """Обработчик изменения размера окна"""
        self.width = width
        self.height = height

        self._screen = pygame.display.set_mode(
            (width, height),
            pygame.RESIZABLE
        )

        self._camera.set_screen_size(width, height)

        # Перепозиционируем панели
        from .panels import PanelPosition
        self._status_bar.width = width
        self._status_bar.set_position(PanelPosition.TOP_LEFT, width, height, 0)
        self._info_panel.set_position(PanelPosition.TOP_RIGHT, width, height)
        self._event_log.set_position(PanelPosition.BOTTOM_LEFT, width, height)
        self._stats_panel.set_position(PanelPosition.BOTTOM_RIGHT, width, height)
        self._speed_controls.set_position(width // 2 - 100, height - 35)

    def _on_key_down(self, event) -> None:
        """Обработчик нажатия клавиши"""
        key = event.key

        # Движение камеры
        if key == pygame.K_UP or key == pygame.K_w:
            self._keys_pressed['up'] = True
            self._keys_pressed['w'] = True
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self._keys_pressed['down'] = True
            self._keys_pressed['s'] = True
        elif key == pygame.K_LEFT or key == pygame.K_a:
            self._keys_pressed['left'] = True
            self._keys_pressed['a'] = True
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self._keys_pressed['right'] = True
            self._keys_pressed['d'] = True

        # Пауза
        elif key == pygame.K_SPACE:
            self.is_paused = not self.is_paused
            self._speed_controls.is_paused = self.is_paused
            self._speed_controls.buttons[0].text = ">" if self.is_paused else "||"

        # Скорость
        elif key == pygame.K_1:
            self.simulation_speed = 1
        elif key == pygame.K_2:
            self.simulation_speed = 2
        elif key == pygame.K_3:
            self.simulation_speed = 5
        elif key == pygame.K_4:
            self.simulation_speed = 10

        # Сетка
        elif key == pygame.K_g:
            self._renderer.show_grid = not self._renderer.show_grid

        # Быстрое сохранение (F5)
        elif key == pygame.K_F5:
            self._quick_save()

        # Быстрая загрузка (F9)
        elif key == pygame.K_F9:
            self._quick_load()

        # Автосохранение (F6)
        elif key == pygame.K_F6:
            self._autosave()

        # Выход
        elif key == pygame.K_ESCAPE:
            self.running = False

    def _quick_save(self) -> None:
        """Выполняет быстрое сохранение"""
        if not self._save_manager or not self.simulation:
            self._show_message("Сохранение недоступно")
            return

        try:
            from ..persistence import SaveError
            filepath = self._save_manager.quick_save(self.simulation)
            self._show_message(f"Сохранено: quicksave")
        except Exception as e:
            self._show_message(f"Ошибка: {e}")

    def _quick_load(self) -> None:
        """Загружает быстрое сохранение"""
        if not self._save_manager or not self.simulation:
            self._show_message("Загрузка недоступна")
            return

        if not self._save_manager.has_quicksave():
            self._show_message("Нет быстрого сохранения")
            return

        try:
            from ..persistence import LoadError
            self._save_manager.quick_load(self.simulation)
            self._show_message(f"Загружено: год {self.simulation.year}")
            # Сбрасываем спрайты
            self._sprites.clear()
        except Exception as e:
            self._show_message(f"Ошибка: {e}")

    def _autosave(self) -> None:
        """Выполняет автосохранение"""
        if not self._save_manager or not self.simulation:
            return

        try:
            self._save_manager.autosave(self.simulation)
            self._show_message("Автосохранение выполнено")
        except Exception as e:
            self._show_message(f"Ошибка автосохранения: {e}")

    def _on_key_up(self, event) -> None:
        """Обработчик отпускания клавиши"""
        key = event.key

        if key == pygame.K_UP:
            self._keys_pressed['up'] = False
        elif key == pygame.K_w:
            self._keys_pressed['w'] = False
        elif key == pygame.K_DOWN:
            self._keys_pressed['down'] = False
        elif key == pygame.K_s:
            self._keys_pressed['s'] = False
        elif key == pygame.K_LEFT:
            self._keys_pressed['left'] = False
        elif key == pygame.K_a:
            self._keys_pressed['a'] = False
        elif key == pygame.K_RIGHT:
            self._keys_pressed['right'] = False
        elif key == pygame.K_d:
            self._keys_pressed['d'] = False

    def _on_mouse_down(self, event) -> None:
        """Обработчик нажатия кнопки мыши"""
        x, y = event.pos

        # Левая кнопка
        if event.button == 1:
            # Проверяем клик по панелям
            if self._speed_controls.handle_click(x, y):
                return

            # Проверяем клик по NPC
            world_x, world_y = self._camera.screen_to_world(x, y)
            tile_size = self._camera.get_scaled_tile_size()
            sprite = self._sprites.get_at_position(world_x, world_y, tile_size)

            if sprite:
                self._sprites.select(sprite.npc_id)

                # Обновляем панель информации
                if self.simulation and sprite.npc_id in self.simulation.npcs:
                    npc = self.simulation.npcs[sprite.npc_id]
                    self._info_panel.set_selected_npc(sprite.npc_id, npc)
            else:
                self._sprites.select(None)
                self._info_panel.clear_selection()

        # Средняя кнопка - начинаем перетаскивание
        elif event.button == 2:
            self._mouse_dragging = True
            self._last_mouse_pos = event.pos

        # Правая кнопка
        elif event.button == 3:
            # Снимаем выделение
            self._sprites.select(None)
            self._info_panel.clear_selection()

    def _on_mouse_up(self, event) -> None:
        """Обработчик отпускания кнопки мыши"""
        if event.button == 2:
            self._mouse_dragging = False

    def _on_mouse_motion(self, event) -> None:
        """Обработчик движения мыши"""
        x, y = event.pos

        # Перетаскивание камеры
        if self._mouse_dragging:
            dx = (self._last_mouse_pos[0] - x) / self._camera.get_scaled_tile_size()
            dy = (self._last_mouse_pos[1] - y) / self._camera.get_scaled_tile_size()
            self._camera.move(dx, dy)
            self._last_mouse_pos = event.pos
        else:
            # Hover для NPC
            world_x, world_y = self._camera.screen_to_world(x, y)
            tile_size = self._camera.get_scaled_tile_size()
            sprite = self._sprites.get_at_position(world_x, world_y, tile_size)

            if sprite:
                self._sprites.hover(sprite.npc_id)
            else:
                self._sprites.hover(None)

    def _on_mouse_wheel(self, event) -> None:
        """Обработчик колеса мыши"""
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if event.y > 0:
            self._camera.zoom_at(mouse_x, mouse_y, 1.1)
        elif event.y < 0:
            self._camera.zoom_at(mouse_x, mouse_y, 0.9)

    def _render(self) -> None:
        """Рендерит текущий кадр"""
        # Очищаем экран
        self._renderer.clear(self._screen)

        # Рендерим карту
        if self.simulation and hasattr(self.simulation, 'world_map'):
            self._renderer.render_map(
                self._screen,
                self.simulation.world_map,
                self._camera
            )

        # Рендерим ресурсы
        if self.simulation and hasattr(self.simulation, 'resources'):
            self._renderer.render_resources(
                self._screen,
                self.simulation.resources.resources,
                self._camera
            )

        # Рендерим NPC
        self._renderer.render_npcs(
            self._screen,
            self._sprites,
            self._camera
        )

        # Рендерим индикаторы конфликтов
        if self.simulation and hasattr(self.simulation, 'classes'):
            conflicts = self.simulation.classes.get_active_conflicts()
            if conflicts:
                self._renderer.render_conflict_indicators(
                    self._screen,
                    conflicts,
                    self._camera
                )

        # Рендерим UI панели
        self._render_panels()

        # FPS
        fps = int(self._clock.get_fps())
        fps_text = self._font_small.render(f"FPS: {fps}", True, (100, 100, 100))
        self._screen.blit(fps_text, (self.width - 60, 5))

        # Сообщение о сохранении/загрузке
        if self._save_message and time.time() - self._save_message_time < 3.0:
            msg_surface = self._font.render(self._save_message, True, (255, 255, 100))
            msg_x = (self.width - msg_surface.get_width()) // 2
            self._screen.blit(msg_surface, (msg_x, 50))

        # Обновляем дисплей
        pygame.display.flip()

    def _render_panels(self) -> None:
        """Рендерит все UI панели"""
        # Статусная строка
        self._render_status_bar()

        # Панель информации
        self._render_info_panel()

        # Лог событий
        self._render_event_log()

        # Статистика
        self._render_stats_panel()

        # Контроллер скорости
        self._render_speed_controls()

    def _render_status_bar(self) -> None:
        """Рендерит статусную строку"""
        bar = self._status_bar
        if not bar.visible:
            return

        # Фон
        pygame.draw.rect(
            self._screen,
            bar.style.bg_color,
            (bar.x, bar.y, bar.width, bar.height)
        )

        # Текст
        bar.is_paused = self.is_paused
        text = bar.get_text()
        text_surface = self._font.render(text, True, (240, 240, 240))
        self._screen.blit(text_surface, (bar.x + 10, bar.y + 8))

    def _render_info_panel(self) -> None:
        """Рендерит панель информации"""
        self._render_panel_with_lines(self._info_panel)

    def _render_event_log(self) -> None:
        """Рендерит лог событий"""
        panel = self._event_log
        if not panel.visible:
            return

        # Фон
        pygame.draw.rect(
            self._screen,
            panel.style.bg_color,
            panel.get_rect()
        )
        pygame.draw.rect(
            self._screen,
            panel.style.border_color,
            panel.get_rect(),
            panel.style.border_width
        )

        # Заголовок
        title_surface = self._font_title.render(panel.title, True, (200, 200, 200))
        self._screen.blit(title_surface, (panel.x + 8, panel.y + 5))

        # События
        events = panel.get_visible_events()
        y_offset = 28

        for text, color in events:
            # Обрезаем длинный текст
            if len(text) > 45:
                text = text[:42] + "..."

            text_surface = self._font_small.render(text, True, color)
            self._screen.blit(text_surface, (panel.x + 8, panel.y + y_offset))
            y_offset += 18

    def _render_stats_panel(self) -> None:
        """Рендерит панель статистики"""
        self._render_panel_with_lines(self._stats_panel)

    def _render_panel_with_lines(self, panel) -> None:
        """Рендерит панель со списком строк"""
        if not panel.visible:
            return

        # Фон
        pygame.draw.rect(
            self._screen,
            panel.style.bg_color,
            panel.get_rect()
        )
        pygame.draw.rect(
            self._screen,
            panel.style.border_color,
            panel.get_rect(),
            panel.style.border_width
        )

        # Заголовок
        title_surface = self._font_title.render(panel.title, True, (200, 200, 200))
        self._screen.blit(title_surface, (panel.x + 8, panel.y + 5))

        # Строки
        lines = panel.get_lines()
        y_offset = 28

        for text, color in lines:
            if not text:
                y_offset += 8
                continue

            text_surface = self._font_small.render(text, True, color)
            self._screen.blit(text_surface, (panel.x + 8, panel.y + y_offset))
            y_offset += 18

    def _render_speed_controls(self) -> None:
        """Рендерит контроллер скорости"""
        controls = self._speed_controls

        for button in controls.buttons:
            color = button.get_color()

            # Фон кнопки
            pygame.draw.rect(
                self._screen,
                color,
                (button.x, button.y, button.width, button.height)
            )

            # Обводка
            pygame.draw.rect(
                self._screen,
                (80, 80, 100),
                (button.x, button.y, button.width, button.height),
                1
            )

            # Текст
            text_surface = self._font_small.render(button.text, True, (220, 220, 220))
            text_x = button.x + (button.width - text_surface.get_width()) // 2
            text_y = button.y + (button.height - text_surface.get_height()) // 2
            self._screen.blit(text_surface, (text_x, text_y))

    def stop(self) -> None:
        """Останавливает игровой цикл"""
        self.running = False
