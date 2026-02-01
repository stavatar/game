#!/usr/bin/env python3
"""
БАЗИС И НАДСТРОЙКА - Симулятор развития общества по Марксу

Экономика (базис) определяет культуру (надстройку).
Наблюдайте, как из примитивной общины возникают:
- Частная собственность
- Классы
- Идеология

Каждый NPC уникален и принимает решения самостоятельно.

Запуск:
    python main.py
"""
import sys
import time

from src.core.simulation import Simulation
from src.core.config import Config, SimulationSpeed
from src.persistence import SaveManager, SaveError, LoadError


def clear_screen():
    """Очищает экран"""
    print("\033[H\033[J", end="")


def show_main_menu() -> str:
    """Показывает главное меню и возвращает выбор"""
    print("=" * 60)
    print("БАЗИС И НАДСТРОЙКА")
    print("Симулятор развития общества")
    print("=" * 60)
    print()
    print("  1 - Новая игра")
    print("  2 - Загрузить сохранение")
    print("  3 - Выход")
    print()
    return input("> ").strip()


def show_load_menu(save_manager: SaveManager) -> str:
    """Показывает меню загрузки, возвращает путь к файлу или пустую строку"""
    saves = save_manager.list_saves()

    if not saves:
        print("\nНет доступных сохранений.")
        input("Enter...")
        return ""

    print("\n=== СОХРАНЕНИЯ ===")
    for i, save in enumerate(saves, 1):
        size_kb = save.size_bytes / 1024
        print(f"  {i}. {save.save_name}")
        print(f"     Год: {save.year}, Население: {save.population}, Эпоха: {save.era}")
        print(f"     Создано: {save.created_at[:19]}, Размер: {size_kb:.1f} KB")
        print()

    print("  0 - Назад")
    print()

    try:
        choice = input("> ").strip()
        if choice == "0" or not choice:
            return ""
        idx = int(choice) - 1
        if 0 <= idx < len(saves):
            return saves[idx].filepath
    except ValueError:
        pass

    print("Неверный выбор.")
    return ""


def main():
    """Главная функция"""
    save_manager = SaveManager()

    # Главное меню
    while True:
        choice = show_main_menu()

        if choice == "3" or choice.lower() == "q":
            print("До свидания!")
            return

        elif choice == "2":
            # Загрузка
            filepath = show_load_menu(save_manager)
            if filepath:
                try:
                    print(f"\nЗагрузка {filepath}...")
                    config = Config()  # Базовый конфиг, будет перезаписан
                    sim = Simulation(config)
                    save_manager.load(filepath, sim)
                    print(f"Загружено: год {sim.year}, население {len(sim.npcs)}")
                    input("Enter...")
                    break
                except LoadError as e:
                    print(f"\nОшибка загрузки: {e}")
                    input("Enter...")
            continue

        elif choice == "1":
            # Новая игра
            print()
            print("Инициализация мира...")

            config = Config(
                initial_population=12,
                initial_families=3,
                map_width=40,
                map_height=40,
            )

            sim = Simulation(config)
            init_events = sim.initialize()

            print(f"Создано {len(sim.npcs)} жителей")
            print()

            for event in init_events[:10]:
                print(f"  • {event}")

            print()
            input("Нажмите Enter для начала симуляции...")
            break
        else:
            continue

    # Главный цикл
    running = True
    auto_mode = False
    speed_delay = 0.5

    while running:
        clear_screen()

        # Показываем статус
        print(sim.get_status())
        print()

        # Показываем карту
        print("КАРТА:")
        print(sim.get_map_view())
        print()

        # Последние события
        print("Последние события:")
        for event in sim.event_log[-5:]:
            print(f"  • {event}")
        print()

        # Меню
        if auto_mode:
            print("[Авто-режим] Пробел - пауза")
        else:
            print("Команды:")
            print("  1 - Час          2 - День       3 - Месяц")
            print("  4 - Год          5 - Жители     6 - Статистика")
            print("  s - Сохранить    l - Загрузить  f - Быстрое сохр.")
            print("  a - Авто-режим   q - Выход")

        if auto_mode:
            # Авто-режим
            events = sim.update(24)  # День
            time.sleep(speed_delay)

            # Проверяем нажатие клавиши (упрощённо)
            # В реальности нужен неблокирующий ввод
            continue

        # Ввод команды
        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd == "q":
            running = False

        elif cmd == "1":
            events = sim.update(1)
            for e in events:
                print(f"  {e}")
            input("Enter...")

        elif cmd == "2":
            events = sim.update(24)
            for e in events[-10:]:
                print(f"  {e}")
            input("Enter...")

        elif cmd == "3":
            events = sim.update(24 * 30)
            for e in events[-15:]:
                print(f"  {e}")
            input("Enter...")

        elif cmd == "4":
            events = sim.update(24 * 360)
            for e in events[-20:]:
                print(f"  {e}")
            input("Enter...")

        elif cmd == "5":
            print(sim.get_npc_list())
            input("Enter...")

        elif cmd == "6":
            # Подробная статистика
            print("\n=== СТАТИСТИКА ===")
            print(f"\nЭкономика (БАЗИС):")
            print(f"  Эпоха: {sim.knowledge.get_current_era().russian_name}")
            print(f"  Технологий открыто: {len(sim.knowledge.discovered_technologies)}")
            print(f"  Частная собственность: {'да' if sim.ownership.private_property_emerged else 'нет'}")
            print(f"  Неравенство (Джини): {sim.ownership.calculate_inequality():.2f}")

            print(f"\nОбщество:")
            print(f"  Семей: {len(sim.families.families)}")
            print(f"  Классы: {sim.classes.get_class_distribution()}")
            print(f"  Напряжённость: {sim.classes.check_class_tension():.2f}")

            print(f"\nКультура (НАДСТРОЙКА):")
            print(f"  Верований: {len(sim.beliefs.beliefs)}")
            for b in sim.beliefs.beliefs.values():
                print(f"    - {b.name}: {b.get_adherent_count()} чел.")

            print(f"\nДемография:")
            stats = sim.demography.get_statistics()
            print(f"  Рождений в этом году: {stats['births_this_year']}")
            print(f"  Смертей в этом году: {stats['deaths_this_year']}")
            print(f"  Ожидаемая продолжительность жизни: {stats['life_expectancy']}")

            input("\nEnter...")

        elif cmd == "a":
            auto_mode = True
            print("Авто-режим включён. Нажмите Ctrl+C для выхода.")

        elif cmd == "s":
            # Сохранение
            print("\nВведите имя сохранения (или Enter для авто):")
            name = input("> ").strip()
            try:
                filepath = save_manager.save(sim, name if name else None)
                print(f"Сохранено: {filepath}")
            except SaveError as e:
                print(f"Ошибка сохранения: {e}")
            input("Enter...")

        elif cmd == "l":
            # Загрузка
            filepath = show_load_menu(save_manager)
            if filepath:
                try:
                    save_manager.load(filepath, sim)
                    print(f"Загружено: год {sim.year}, население {len(sim.npcs)}")
                except LoadError as e:
                    print(f"Ошибка загрузки: {e}")
                input("Enter...")

        elif cmd == "f":
            # Быстрое сохранение
            try:
                filepath = save_manager.quick_save(sim)
                print(f"Быстрое сохранение: {filepath}")
            except SaveError as e:
                print(f"Ошибка: {e}")
            input("Enter...")

    print("\nСимуляция завершена.")
    print(f"Прошло {sim.year} лет, {sim.generations} поколений.")


if __name__ == "__main__":
    main()
