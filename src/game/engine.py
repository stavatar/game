"""
Игровой движок - управляет игровым циклом и пользовательским интерфейсом.
"""
import os
import sys
from typing import Optional, List

from ..world.world import World
from ..world.location import Location
from ..npc.character import NPC
from ..ai.behavior import BehaviorSystem


class GameEngine:
    """
    Главный игровой движок.

    Отвечает за:
    - Игровой цикл
    - Пользовательский ввод/вывод
    - Координацию систем
    """

    def __init__(self, world: World = None):
        self.world = world or World.generate_village()
        self.behavior = BehaviorSystem(self.world)
        self.running = False
        self.selected_npc: Optional[NPC] = None
        self.auto_simulate = False
        self.events_buffer: List[str] = []

    def clear_screen(self):
        """Очищает экран"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Выводит заголовок"""
        print("=" * 60)
        print(f"  ЖИВОЙ МИР: {self.world.name}")
        print("=" * 60)
        print(self.world.time.get_full_datetime())
        print("-" * 60)

    def print_menu(self):
        """Выводит главное меню"""
        print("\n[Команды]")
        print("  1. Пропустить час      | 2. Пропустить день")
        print("  3. Список жителей      | 4. Список локаций")
        print("  5. Информация о NPC    | 6. Информация о локации")
        print("  7. Последние события   | 8. Авто-симуляция (вкл/выкл)")
        print("  9. Социальная сеть     | 0. Выход")
        print("-" * 60)

    def get_input(self, prompt: str = "> ") -> str:
        """Получает ввод пользователя"""
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return "0"

    def simulate_hour(self) -> List[str]:
        """Симулирует один час игрового времени"""
        events = []

        # Обновляем мир
        world_events = self.world.update(60)
        events.extend(world_events)

        # Симулируем поведение NPC
        behavior_events = self.behavior.simulate_all_npcs()
        events.extend(behavior_events)

        # Сохраняем события
        self.events_buffer.extend(events)
        if len(self.events_buffer) > 100:
            self.events_buffer = self.events_buffer[-100:]

        return events

    def simulate_day(self) -> List[str]:
        """Симулирует один день"""
        all_events = []
        for _ in range(24):
            events = self.simulate_hour()
            all_events.extend(events)
        return all_events

    def show_residents(self):
        """Показывает список жителей"""
        print("\n[Жители]")
        print("-" * 60)

        npcs = sorted(self.world.npcs.values(), key=lambda n: n.name)

        for i, npc in enumerate(npcs, 1):
            status = "" if npc.is_alive else " [мёртв]"
            location = ""
            if npc.current_location_id:
                loc = self.world.get_location(npc.current_location_id)
                if loc:
                    location = f" @ {loc.name}"

            print(f"  {i:2}. {npc.get_full_name()}, {npc.age} лет, "
                  f"{npc.occupation.value}{location}{status}")

        print(f"\nВсего: {len(npcs)} жителей")

    def show_locations(self):
        """Показывает список локаций"""
        print("\n[Локации]")
        print("-" * 60)

        # Сортируем по типу
        locations = sorted(
            self.world.locations.values(),
            key=lambda l: (l.location_type.value, l.name)
        )

        for loc in locations:
            npc_count = loc.get_npc_count()
            status = "открыто" if loc.is_open(self.world.time.hour) else "закрыто"
            print(f"  {loc.name} ({loc.location_type.value}) - "
                  f"{npc_count}/{loc.capacity} чел. [{status}]")

        print(f"\nВсего: {len(locations)} локаций")

    def show_npc_info(self):
        """Показывает подробную информацию о NPC"""
        name = self.get_input("Введите имя NPC: ")
        npc = self.world.find_npc_by_name(name)

        if not npc:
            print(f"NPC с именем '{name}' не найден.")
            return

        print("\n" + "=" * 60)
        print(f"  {npc.get_full_name()}")
        print("=" * 60)

        # Основная информация
        print(f"\nВозраст: {npc.age} лет")
        print(f"Пол: {npc.gender.value}")
        print(f"Профессия: {npc.occupation.value}")
        print(f"Богатство: {npc.wealth} монет")

        # Внешность
        print(f"\nВнешность: {npc.describe_appearance()}")

        # Характер
        print(f"\nХарактер: {npc.personality.describe()}")

        # Характеристики
        print("\nХарактеристики:")
        print(f"  Сила: {npc.stats.strength} | Ловкость: {npc.stats.agility} | "
              f"Выносливость: {npc.stats.endurance}")
        print(f"  Интеллект: {npc.stats.intelligence} | Харизма: {npc.stats.charisma} | "
              f"Восприятие: {npc.stats.perception}")

        # Навыки
        best_skills = npc.skills.get_best_skills(3)
        if best_skills:
            skills_str = ", ".join([f"{s[0]}:{s[1]}" for s in best_skills if s[1] > 0])
            if skills_str:
                print(f"\nЛучшие навыки: {skills_str}")

        # Состояние
        print(f"\nЗдоровье: {npc.health:.0f}%")
        print(f"Настроение: {npc.needs.get_mood()}")
        print(f"Состояние: {npc.needs.describe_state()}")
        print(f"Текущее занятие: {npc.current_activity}")

        # Местоположение
        if npc.current_location_id:
            loc = self.world.get_location(npc.current_location_id)
            if loc:
                print(f"Местоположение: {loc.name}")

        # Цели
        if npc.goals:
            print("\nЦели в жизни:")
            for goal in npc.goals[:3]:
                status = "выполнено" if goal.completed else f"{goal.progress*100:.0f}%"
                print(f"  - {goal.description} [{status}]")

        # Отношения
        friends = npc.relationships.get_friends()
        enemies = npc.relationships.get_enemies()

        if friends:
            friend_names = [self.world.get_npc(f).name for f in friends
                           if self.world.get_npc(f)][:5]
            print(f"\nДрузья: {', '.join(friend_names)}")

        if enemies:
            enemy_names = [self.world.get_npc(e).name for e in enemies
                          if self.world.get_npc(e)][:3]
            print(f"Враги: {', '.join(enemy_names)}")

    def show_location_info(self):
        """Показывает информацию о локации"""
        name = self.get_input("Введите название локации: ")

        # Ищем локацию по названию
        location = None
        name_lower = name.lower()
        for loc in self.world.locations.values():
            if name_lower in loc.name.lower():
                location = loc
                break

        if not location:
            print(f"Локация '{name}' не найдена.")
            return

        print("\n" + "=" * 60)
        print(f"  {location.name}")
        print("=" * 60)

        print(f"\nТип: {location.location_type.value}")
        if location.description:
            print(f"Описание: {location.description}")

        status = "открыто" if location.is_open(self.world.time.hour) else "закрыто"
        print(f"Статус: {status}")
        print(f"Часы работы: {location.open_hours[0]}:00 - {location.open_hours[1]}:00")

        if location.available_services:
            print(f"Услуги: {', '.join(location.available_services)}")

        # Кто здесь находится
        npcs_here = self.world.get_npcs_at_location(location.id)
        print(f"\nПрисутствуют ({len(npcs_here)}/{location.capacity}):")

        if npcs_here:
            for npc in npcs_here[:10]:
                activity = npc.current_activity
                print(f"  - {npc.name} ({npc.occupation.value}) - {activity}")
            if len(npcs_here) > 10:
                print(f"  ... и ещё {len(npcs_here) - 10}")
        else:
            print("  (пусто)")

    def show_events(self):
        """Показывает последние события"""
        print("\n[Последние события]")
        print("-" * 60)

        if not self.events_buffer:
            print("  Пока ничего не произошло.")
            return

        # Показываем последние 20 событий
        for event in self.events_buffer[-20:]:
            print(f"  {event}")

    def show_social_network(self):
        """Показывает социальную сеть - кто с кем дружит"""
        print("\n[Социальная сеть]")
        print("-" * 60)

        for npc in sorted(self.world.npcs.values(), key=lambda n: n.name):
            if not npc.is_alive:
                continue

            friends = npc.relationships.get_friends()
            romantic = npc.relationships.get_romantic_interests()

            if friends or romantic:
                print(f"\n{npc.name}:")

                if friends:
                    friend_info = []
                    for fid in friends[:5]:
                        friend = self.world.get_npc(fid)
                        if friend:
                            rel = npc.relationships.get(fid)
                            friend_info.append(f"{friend.name} ({rel.relationship_type.value})")
                    print(f"  Друзья: {', '.join(friend_info)}")

                if romantic:
                    romantic_info = []
                    for rid in romantic[:3]:
                        interest = self.world.get_npc(rid)
                        if interest:
                            romantic_info.append(interest.name)
                    print(f"  Романтические интересы: {', '.join(romantic_info)}")

    def run(self):
        """Главный игровой цикл"""
        self.running = True

        print("\nДобро пожаловать в ЖИВОЙ МИР!")
        print("Это симулятор деревни, где каждый NPC живёт своей жизнью.")
        print("Наблюдайте, как они работают, общаются, заводят друзей и врагов.\n")

        while self.running:
            self.clear_screen()
            self.print_header()

            # Показываем краткую сводку
            living = len(self.world.get_living_npcs())
            print(f"Население: {living} жителей")

            # Показываем последние 5 событий
            if self.events_buffer:
                print("\nПоследние события:")
                for event in self.events_buffer[-5:]:
                    print(f"  • {event}")

            self.print_menu()

            if self.auto_simulate:
                print("[Авто-симуляция включена - нажмите Enter для продолжения]")

            choice = self.get_input()

            if choice == "1":
                events = self.simulate_hour()
                print(f"\nПрошёл час. Событий: {len(events)}")
                self.get_input("Нажмите Enter...")

            elif choice == "2":
                print("\nСимулирую день...")
                events = self.simulate_day()
                print(f"Прошёл день. Событий: {len(events)}")
                self.get_input("Нажмите Enter...")

            elif choice == "3":
                self.show_residents()
                self.get_input("\nНажмите Enter...")

            elif choice == "4":
                self.show_locations()
                self.get_input("\nНажмите Enter...")

            elif choice == "5":
                self.show_npc_info()
                self.get_input("\nНажмите Enter...")

            elif choice == "6":
                self.show_location_info()
                self.get_input("\nНажмите Enter...")

            elif choice == "7":
                self.show_events()
                self.get_input("\nНажмите Enter...")

            elif choice == "8":
                self.auto_simulate = not self.auto_simulate
                status = "включена" if self.auto_simulate else "выключена"
                print(f"\nАвто-симуляция {status}")
                self.get_input("Нажмите Enter...")

            elif choice == "9":
                self.show_social_network()
                self.get_input("\nНажмите Enter...")

            elif choice == "0":
                print("\nДо свидания!")
                self.running = False

            elif choice == "" and self.auto_simulate:
                # При авто-симуляции пустой ввод = пропустить час
                self.simulate_hour()


def main():
    """Точка входа"""
    print("Генерирую мир...")
    world = World.generate_village("Лесная Поляна", population=15)

    print(f"Создана деревня '{world.name}' с {len(world.npcs)} жителями")

    engine = GameEngine(world)
    engine.run()


if __name__ == "__main__":
    main()
