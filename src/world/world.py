"""
Игровой мир - объединяет все системы.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import random

from .location import Location, LocationType
from .time_system import TimeSystem, TimeOfDay
from ..npc.character import NPC, Occupation, Gender


@dataclass
class World:
    """
    Игровой мир - содержит все локации и NPC.

    Управляет:
    - Созданием и хранением локаций
    - Созданием и хранением NPC
    - Перемещением NPC между локациями
    - Глобальными событиями
    """

    name: str = "Безымянный мир"

    # Хранилища
    locations: Dict[str, Location] = field(default_factory=dict)
    npcs: Dict[str, NPC] = field(default_factory=dict)

    # Время
    time: TimeSystem = field(default_factory=TimeSystem)

    # История событий
    event_log: List[str] = field(default_factory=list)

    def add_location(self, location: Location) -> None:
        """Добавляет локацию в мир"""
        self.locations[location.id] = location

    def add_npc(self, npc: NPC, location_id: Optional[str] = None) -> None:
        """Добавляет NPC в мир"""
        self.npcs[npc.id] = npc

        if location_id and location_id in self.locations:
            self.move_npc(npc.id, location_id)

    def get_location(self, location_id: str) -> Optional[Location]:
        """Возвращает локацию по ID"""
        return self.locations.get(location_id)

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Возвращает NPC по ID"""
        return self.npcs.get(npc_id)

    def get_npcs_at_location(self, location_id: str) -> List[NPC]:
        """Возвращает всех NPC в локации"""
        location = self.get_location(location_id)
        if not location:
            return []

        return [
            self.npcs[npc_id]
            for npc_id in location.current_npcs
            if npc_id in self.npcs
        ]

    def move_npc(self, npc_id: str, target_location_id: str) -> bool:
        """Перемещает NPC в другую локацию"""
        npc = self.get_npc(npc_id)
        target = self.get_location(target_location_id)

        if not npc or not target:
            return False

        if target.is_full():
            return False

        # Удаляем из текущей локации
        if npc.current_location_id:
            current = self.get_location(npc.current_location_id)
            if current:
                current.remove_npc(npc_id)

        # Добавляем в новую
        target.add_npc(npc_id)
        npc.current_location_id = target_location_id

        return True

    def update(self, minutes: int = 60) -> List[str]:
        """
        Обновляет мир на указанное количество минут.
        Возвращает список событий.
        """
        all_events = []

        # Обновляем время
        time_events = self.time.advance(minutes)
        all_events.extend(time_events)

        hours = minutes / 60.0

        # Обновляем всех NPC
        for npc in self.npcs.values():
            npc_events = npc.update(hours)
            all_events.extend(npc_events)

            # Угасание отношений каждые 24 часа
            if self.time.hour == 0 and minutes >= 60:
                npc.relationships.decay_all(1.0)

        # Логируем важные события
        for event in all_events:
            self.event_log.append(f"[{self.time.get_formatted_time()}] {event}")

        # Ограничиваем лог
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-500:]

        return all_events

    def get_random_location(self,
                            location_type: LocationType = None,
                            exclude: Set[str] = None) -> Optional[Location]:
        """Возвращает случайную локацию"""
        candidates = list(self.locations.values())

        if location_type:
            candidates = [l for l in candidates if l.location_type == location_type]

        if exclude:
            candidates = [l for l in candidates if l.id not in exclude]

        if not candidates:
            return None

        return random.choice(candidates)

    def find_npc_by_name(self, name: str) -> Optional[NPC]:
        """Находит NPC по имени"""
        name_lower = name.lower()
        for npc in self.npcs.values():
            if name_lower in npc.name.lower() or name_lower in npc.get_full_name().lower():
                return npc
        return None

    def get_living_npcs(self) -> List[NPC]:
        """Возвращает всех живых NPC"""
        return [npc for npc in self.npcs.values() if npc.is_alive]

    def get_npcs_by_occupation(self, occupation: Occupation) -> List[NPC]:
        """Возвращает NPC с указанной профессией"""
        return [
            npc for npc in self.npcs.values()
            if npc.occupation == occupation and npc.is_alive
        ]

    def get_world_summary(self) -> str:
        """Возвращает сводку о мире"""
        living = len(self.get_living_npcs())
        dead = len(self.npcs) - living

        return (
            f"=== {self.name} ===\n"
            f"{self.time.get_full_datetime()}\n"
            f"\nНаселение: {living} живых, {dead} умерших\n"
            f"Локаций: {len(self.locations)}\n"
        )

    @classmethod
    def generate_village(cls, name: str = "Лесная Поляна", population: int = 20) -> 'World':
        """Генерирует деревню с населением"""
        world = cls(name=name)

        # Создаём локации
        town_square = Location(
            name="Центральная площадь",
            location_type=LocationType.TOWN_SQUARE,
            description="Сердце деревни, где собираются жители",
            capacity=50,
        )
        world.add_location(town_square)

        tavern = Location.create_tavern("Весёлый Кабан")
        world.add_location(tavern)

        market = Location.create_market("Торговые ряды")
        world.add_location(market)

        blacksmith = Location(
            name="Кузница Молота",
            location_type=LocationType.BLACKSMITH,
            description="Здесь куётся лучшее оружие в округе",
            capacity=5,
            available_services=["ковка", "ремонт"],
            open_hours=(7, 19),
        )
        world.add_location(blacksmith)

        church = Location(
            name="Храм Света",
            location_type=LocationType.CHURCH,
            description="Место молитвы и утешения",
            capacity=30,
            available_services=["молитва", "благословение", "исцеление"],
            open_hours=(6, 21),
        )
        world.add_location(church)

        farm = Location(
            name="Большая ферма",
            location_type=LocationType.FARM,
            description="Кормит всю деревню",
            capacity=15,
            available_services=["работа", "еда"],
        )
        world.add_location(farm)

        forest = Location(
            name="Тёмный лес",
            location_type=LocationType.FOREST,
            description="Загадочный лес на окраине",
            capacity=30,
            available_services=["охота", "собирательство"],
        )
        world.add_location(forest)

        # Связываем локации
        all_location_ids = list(world.locations.keys())
        for loc_id in all_location_ids:
            loc = world.locations[loc_id]
            # Площадь связана со всеми
            if loc.location_type != LocationType.TOWN_SQUARE:
                loc.connect_to(town_square.id)
                town_square.connect_to(loc_id)

        # Создаём жителей
        # Определяем профессии для баланса
        occupations = [
            Occupation.INNKEEPER,  # 1 трактирщик
            Occupation.BLACKSMITH,  # 1 кузнец
            Occupation.MERCHANT,  # 2 торговца
            Occupation.MERCHANT,
            Occupation.GUARD,  # 2 стражника
            Occupation.GUARD,
            Occupation.PRIEST,  # 1 священник
            Occupation.HEALER,  # 1 лекарь
            Occupation.FARMER,  # остальные - фермеры и ремесленники
            Occupation.FARMER,
            Occupation.FARMER,
            Occupation.HUNTER,
            Occupation.CRAFTSMAN,
            Occupation.BARD,
        ]

        # Добавляем недостающих фермеров
        while len(occupations) < population:
            occupations.append(random.choice([
                Occupation.FARMER, Occupation.CRAFTSMAN,
                Occupation.SERVANT, Occupation.NONE
            ]))

        # Создаём NPC
        for i, occupation in enumerate(occupations[:population]):
            gender = random.choice([Gender.MALE, Gender.FEMALE])
            npc = NPC.generate_random(gender=gender, occupation=occupation)

            # Назначаем начальную локацию
            if occupation == Occupation.INNKEEPER:
                start_loc = tavern.id
                npc.work_location_id = tavern.id
            elif occupation == Occupation.BLACKSMITH:
                start_loc = blacksmith.id
                npc.work_location_id = blacksmith.id
            elif occupation == Occupation.MERCHANT:
                start_loc = market.id
                npc.work_location_id = market.id
            elif occupation == Occupation.PRIEST:
                start_loc = church.id
                npc.work_location_id = church.id
            elif occupation == Occupation.FARMER:
                start_loc = farm.id
                npc.work_location_id = farm.id
            elif occupation == Occupation.HUNTER:
                start_loc = forest.id
                npc.work_location_id = forest.id
            else:
                start_loc = town_square.id

            world.add_npc(npc, start_loc)

            # Создаём дом для NPC
            home = Location.create_home(f"Дом {npc.name}", npc.id)
            home.connect_to(town_square.id)
            town_square.connect_to(home.id)
            world.add_location(home)
            npc.home_location_id = home.id

        # Создаём начальные отношения между NPC
        npc_list = list(world.npcs.values())
        for i, npc1 in enumerate(npc_list):
            # Каждый знаком с 3-5 случайными NPC
            num_acquaintances = random.randint(3, 5)
            others = [n for n in npc_list if n.id != npc1.id]
            acquaintances = random.sample(others, min(num_acquaintances, len(others)))

            for npc2 in acquaintances:
                rel = npc1.relationships.get_or_create(npc2.id)
                # Случайные начальные отношения
                rel.modify(
                    friendship=random.randint(-20, 40),
                    trust=random.randint(-10, 30),
                    respect=random.randint(-10, 30),
                )
                rel.interactions_count = random.randint(1, 10)

        return world
