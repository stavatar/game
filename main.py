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


def clear_screen():
    """Очищает экран"""
    print("\033[H\033[J", end="")


def main():
    """Главная функция"""
    print("=" * 60)
    print("БАЗИС И НАДСТРОЙКА")
    print("Симулятор развития общества")
    print("=" * 60)
    print()
    print("Инициализация мира...")

    # Создаём симуляцию
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

    # Показываем начальные события
    for event in init_events[:10]:
        print(f"  • {event}")

    print()
    input("Нажмите Enter для начала симуляции...")

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

    print("\nСимуляция завершена.")
    print(f"Прошло {sim.year} лет, {sim.generations} поколений.")


if __name__ == "__main__":
    main()
