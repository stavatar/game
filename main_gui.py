#!/usr/bin/env python3
"""
БАЗИС И НАДСТРОЙКА - Графический интерфейс

Запуск симуляции с визуализацией через pygame.

Управление:
- WASD/Стрелки: перемещение камеры
- Колесо мыши: масштабирование
- Средняя кнопка мыши: перетаскивание
- ЛКМ на NPC: выбор
- ПКМ: снятие выбора
- Пробел: пауза
- 1-4: скорость симуляции
- G: показать/скрыть сетку
- ESC: выход

Запуск:
    python main_gui.py
"""
import sys

# Проверяем pygame (поддерживаем pygame и pygame-ce)
try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame
    except ImportError:
        print("=" * 60)
        print("ОШИБКА: pygame не установлен")
        print("=" * 60)
        print()
        print("Установите pygame командой:")
        print("  pip install pygame")
        print("или:")
        print("  pip install pygame-ce")
        print()
        print("Или используйте текстовый режим:")
        print("  python main.py")
        print()
        sys.exit(1)

from src.core.simulation import Simulation
from src.core.config import Config
from src.ui.window import GameWindow
from src.persistence import SaveManager, SaveError, LoadError


def main():
    """Главная функция"""
    print("=" * 60)
    print("БАЗИС И НАДСТРОЙКА")
    print("Симулятор развития общества")
    print("Графический интерфейс")
    print("=" * 60)
    print()

    save_manager = SaveManager()
    sim = None

    # Проверяем автосохранение
    if save_manager.has_autosave():
        print("Найдено автосохранение. Загрузить? (y/n)")
        choice = input("> ").strip().lower()
        if choice == "y":
            try:
                config = Config()
                sim = Simulation(config)
                save_manager.load_autosave(sim)
                print(f"Загружено: год {sim.year}, население {len(sim.npcs)}")
            except LoadError as e:
                print(f"Ошибка загрузки: {e}")
                sim = None

    if sim is None:
        # Конфигурация
        config = Config(
            initial_population=20,
            initial_families=5,
            map_width=50,
            map_height=50,
        )

        print("Инициализация мира...")

        # Создаём симуляцию
        sim = Simulation(config)
        init_events = sim.initialize()

        print(f"Создано {len(sim.npcs)} жителей")

        # Показываем начальные события
        for event in init_events[:5]:
            print(f"  - {event}")

    print()
    print("Запуск графического интерфейса...")
    print()
    print("Управление:")
    print("  WASD/Стрелки - перемещение камеры")
    print("  Колесо мыши  - масштабирование")
    print("  ЛКМ на NPC   - информация")
    print("  Пробел       - пауза")
    print("  1-4          - скорость (x1, x2, x5, x10)")
    print("  G            - сетка")
    print("  F5           - быстрое сохранение")
    print("  F9           - быстрая загрузка")
    print("  ESC          - выход")
    print()

    # Создаём окно
    window = GameWindow(
        width=1280,
        height=720,
        title="Базис и Надстройка - Симулятор"
    )

    # Устанавливаем симуляцию и менеджер сохранений
    window.set_simulation(sim)
    window.set_save_manager(save_manager)

    # Запускаем игровой цикл
    try:
        window.run()
    except KeyboardInterrupt:
        window.stop()

    print()
    print("Симуляция завершена.")
    print(f"Прошло {sim.year} лет, {sim.generations} поколений.")


if __name__ == "__main__":
    main()
