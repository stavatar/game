"""
Основной класс NPC - уникальная личность в игровом мире.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import random
import uuid

from .personality import Personality, Trait
from .needs import Needs, Need
from .relationships import RelationshipManager


class Gender(Enum):
    MALE = "мужской"
    FEMALE = "женский"


class Occupation(Enum):
    """Профессии NPC"""
    NONE = "безработный"
    FARMER = "фермер"
    BLACKSMITH = "кузнец"
    MERCHANT = "торговец"
    GUARD = "стражник"
    INNKEEPER = "трактирщик"
    HEALER = "лекарь"
    HUNTER = "охотник"
    CRAFTSMAN = "ремесленник"
    SCHOLAR = "учёный"
    PRIEST = "священник"
    BARD = "бард"
    BEGGAR = "нищий"
    NOBLE = "дворянин"
    SERVANT = "слуга"


@dataclass
class Stats:
    """Характеристики NPC"""
    strength: int = 10       # Сила
    agility: int = 10        # Ловкость
    endurance: int = 10      # Выносливость
    intelligence: int = 10   # Интеллект
    charisma: int = 10       # Харизма
    perception: int = 10     # Восприятие
    luck: int = 10           # Удача

    def modify(self, stat: str, value: int) -> None:
        """Изменяет характеристику"""
        if hasattr(self, stat):
            current = getattr(self, stat)
            setattr(self, stat, max(1, min(20, current + value)))

    @classmethod
    def generate_random(cls) -> 'Stats':
        """Генерирует случайные характеристики"""
        return cls(
            strength=random.randint(5, 15),
            agility=random.randint(5, 15),
            endurance=random.randint(5, 15),
            intelligence=random.randint(5, 15),
            charisma=random.randint(5, 15),
            perception=random.randint(5, 15),
            luck=random.randint(5, 15),
        )


@dataclass
class Skills:
    """Навыки NPC (0-100)"""
    combat: int = 0
    crafting: int = 0
    trading: int = 0
    farming: int = 0
    cooking: int = 0
    medicine: int = 0
    persuasion: int = 0
    stealth: int = 0
    music: int = 0
    knowledge: int = 0

    def improve(self, skill: str, amount: int = 1) -> None:
        """Улучшает навык"""
        if hasattr(self, skill):
            current = getattr(self, skill)
            setattr(self, skill, min(100, current + amount))

    def get_best_skills(self, count: int = 3) -> List[tuple]:
        """Возвращает лучшие навыки"""
        skills = [
            (name, value) for name, value in self.__dict__.items()
            if isinstance(value, int)
        ]
        return sorted(skills, key=lambda x: x[1], reverse=True)[:count]


@dataclass
class Memory:
    """Память о событии"""
    event_type: str
    description: str
    importance: float  # 0-1
    emotional_impact: float  # -1 до 1
    day: int
    related_npc_ids: List[str] = field(default_factory=list)


@dataclass
class Goal:
    """Цель/мечта NPC"""
    description: str
    priority: float  # 0-1
    progress: float = 0.0  # 0-1
    completed: bool = False


@dataclass
class NPC:
    """
    Уникальная личность в игровом мире.

    Каждый NPC имеет:
    - Уникальное имя и внешность
    - Характеристики и навыки
    - Личность с чертами характера
    - Потребности
    - Отношения с другими NPC
    - Память и цели
    - Профессию и роль в обществе
    """

    # Идентификация
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Безымянный"
    surname: str = ""
    gender: Gender = Gender.MALE
    age: int = 25

    # Внешность
    appearance: Dict[str, str] = field(default_factory=dict)

    # Характеристики
    stats: Stats = field(default_factory=Stats)
    skills: Skills = field(default_factory=Skills)

    # Личность
    personality: Personality = field(default_factory=Personality)

    # Потребности
    needs: Needs = field(default_factory=Needs)

    # Социальное
    relationships: RelationshipManager = field(default=None)
    occupation: Occupation = Occupation.NONE
    wealth: int = 100  # Деньги

    # Местоположение
    current_location_id: Optional[str] = None
    home_location_id: Optional[str] = None
    work_location_id: Optional[str] = None

    # Состояние
    health: float = 100.0
    is_alive: bool = True
    is_sleeping: bool = False
    current_activity: str = "бездельничает"

    # Память и цели
    memories: List[Memory] = field(default_factory=list)
    goals: List[Goal] = field(default_factory=list)
    life_events: List[str] = field(default_factory=list)

    # Развитие
    experience: int = 0
    days_lived: int = 0

    def __post_init__(self):
        if self.relationships is None:
            self.relationships = RelationshipManager(owner_id=self.id)

        if not self.appearance:
            self._generate_appearance()

        if not self.goals:
            self._generate_initial_goals()

    def _generate_appearance(self) -> None:
        """Генерирует случайную внешность"""
        hair_colors = ["чёрные", "каштановые", "русые", "рыжие", "светлые", "седые"]
        eye_colors = ["карие", "зелёные", "голубые", "серые", "чёрные"]
        heights = ["низкий", "средний", "высокий"]
        builds = ["худощавый", "обычный", "крепкий", "полный"]

        self.appearance = {
            "hair": random.choice(hair_colors),
            "eyes": random.choice(eye_colors),
            "height": random.choice(heights),
            "build": random.choice(builds),
        }

    def _generate_initial_goals(self) -> None:
        """Генерирует начальные цели на основе личности"""
        possible_goals = [
            ("Накопить богатство", 0.7),
            ("Найти любовь", 0.6),
            ("Стать мастером своего дела", 0.8),
            ("Завести семью", 0.5),
            ("Путешествовать по миру", 0.4),
            ("Обрести уважение", 0.6),
            ("Помочь нуждающимся", 0.5),
            ("Достичь власти", 0.7),
            ("Найти верных друзей", 0.5),
            ("Познать мудрость", 0.6),
        ]

        # Выбираем 2-3 цели
        num_goals = random.randint(2, 3)
        selected = random.sample(possible_goals, num_goals)

        for desc, priority in selected:
            # Модифицируем приоритет на основе личности
            if self.personality.has_trait(Trait.AMBITIOUS):
                priority = min(1.0, priority + 0.2)
            if self.personality.has_trait(Trait.CONTENT):
                priority = max(0.1, priority - 0.2)

            self.goals.append(Goal(description=desc, priority=priority))

    def get_full_name(self) -> str:
        """Возвращает полное имя"""
        if self.surname:
            return f"{self.name} {self.surname}"
        return self.name

    def describe_appearance(self) -> str:
        """Возвращает описание внешности"""
        return (
            f"{self.appearance['height']} {self.appearance['build']} "
            f"{'мужчина' if self.gender == Gender.MALE else 'женщина'} "
            f"с {self.appearance['hair']}и волосами и {self.appearance['eyes']}и глазами"
        )

    def update(self, hours: float = 1.0) -> List[str]:
        """
        Обновляет состояние NPC.
        Возвращает список событий, произошедших с NPC.
        """
        events = []

        if not self.is_alive:
            return events

        # Обновляем потребности
        self.needs.decay_all(hours)

        # Проверяем критические потребности
        if self.needs.get(Need.HUNGER).is_critical():
            self.health -= 1 * hours
            events.append(f"{self.name} голодает и теряет здоровье")

        if self.needs.get(Need.ENERGY).is_critical() and not self.is_sleeping:
            events.append(f"{self.name} падает от усталости")
            self.is_sleeping = True

        # Проверяем здоровье
        if self.health <= 0:
            self.is_alive = False
            events.append(f"{self.name} умер")

        return events

    def add_memory(self,
                   event_type: str,
                   description: str,
                   importance: float = 0.5,
                   emotional_impact: float = 0.0,
                   day: int = 0,
                   related_npcs: List[str] = None) -> None:
        """Добавляет воспоминание"""
        memory = Memory(
            event_type=event_type,
            description=description,
            importance=importance,
            emotional_impact=emotional_impact,
            day=day,
            related_npc_ids=related_npcs or []
        )
        self.memories.append(memory)

        # Храним только важные воспоминания (максимум 50)
        if len(self.memories) > 50:
            self.memories.sort(key=lambda m: m.importance, reverse=True)
            self.memories = self.memories[:50]

    def interact_with(self, other: 'NPC', interaction_type: str = "разговор") -> Dict[str, Any]:
        """
        Взаимодействует с другим NPC.
        Возвращает результат взаимодействия.
        """
        result = {
            "success": True,
            "type": interaction_type,
            "events": [],
            "relationship_change": 0
        }

        # Получаем отношения
        rel = self.relationships.get_or_create(other.id)
        other_rel = other.relationships.get_or_create(self.id)

        # Вычисляем базовый результат на основе личностей
        compatibility = self._calculate_compatibility(other)

        # Модификаторы от текущего состояния
        mood_modifier = (self.needs.get_overall_happiness() - 50) / 100
        other_mood_modifier = (other.needs.get_overall_happiness() - 50) / 100

        # Итоговое изменение отношений
        change = compatibility + mood_modifier + other_mood_modifier
        change = change * random.uniform(0.8, 1.2)  # Случайность

        # Применяем изменения
        is_positive = change > 0
        rel.modify(friendship=change * 5, trust=change * 2)
        rel.record_interaction(is_positive, f"{interaction_type} с {other.name}")

        other_rel.modify(friendship=change * 5, trust=change * 2)
        other_rel.record_interaction(is_positive, f"{interaction_type} с {self.name}")

        # Удовлетворяем социальную потребность
        social_gain = 10 + abs(change) * 5
        self.needs.satisfy(Need.SOCIAL, social_gain)
        other.needs.satisfy(Need.SOCIAL, social_gain)

        result["relationship_change"] = change
        result["events"].append(
            f"{self.name} {'приятно' if is_positive else 'неприятно'} "
            f"пообщался с {other.name}"
        )

        return result

    def _calculate_compatibility(self, other: 'NPC') -> float:
        """Вычисляет совместимость с другим NPC"""
        compatibility = 0.0

        # Схожие черты дают бонус
        common_traits = set(self.personality.traits) & set(other.personality.traits)
        compatibility += len(common_traits) * 0.1

        # Противоположные черты могут как притягивать, так и отталкивать
        if self.personality.has_trait(Trait.EXTROVERT):
            if other.personality.has_trait(Trait.INTROVERT):
                compatibility -= 0.1
        if self.personality.has_trait(Trait.FRIENDLY):
            compatibility += 0.15
        if other.personality.has_trait(Trait.FRIENDLY):
            compatibility += 0.15
        if self.personality.has_trait(Trait.HOSTILE):
            compatibility -= 0.2

        # Харизма влияет
        charisma_bonus = (self.stats.charisma + other.stats.charisma - 20) / 40
        compatibility += charisma_bonus * 0.2

        return compatibility

    def gain_experience(self, amount: int) -> None:
        """Получает опыт и возможно улучшает характеристики"""
        self.experience += amount

        # Каждые 100 очков опыта - шанс улучшить характеристику
        while self.experience >= 100:
            self.experience -= 100
            # Улучшаем случайную характеристику
            stat_names = ['strength', 'agility', 'endurance', 'intelligence',
                          'charisma', 'perception', 'luck']
            stat_to_improve = random.choice(stat_names)
            self.stats.modify(stat_to_improve, 1)

    def get_status_summary(self) -> str:
        """Возвращает краткую сводку о состоянии NPC"""
        status_parts = [
            f"{self.get_full_name()}, {self.age} лет",
            f"Профессия: {self.occupation.value}",
            f"Здоровье: {self.health:.0f}%",
            f"Настроение: {self.needs.get_mood()}",
            f"Характер: {self.personality.describe()}",
            f"Занятие: {self.current_activity}",
        ]

        return "\n".join(status_parts)

    @classmethod
    def generate_random(cls,
                        name: str = None,
                        gender: Gender = None,
                        occupation: Occupation = None) -> 'NPC':
        """Генерирует случайного NPC"""
        from ..data.names import generate_name

        if gender is None:
            gender = random.choice([Gender.MALE, Gender.FEMALE])

        if name is None:
            name = generate_name(gender)

        age = random.randint(18, 65)

        if occupation is None:
            occupation = random.choice(list(Occupation))

        npc = cls(
            name=name,
            gender=gender,
            age=age,
            stats=Stats.generate_random(),
            personality=Personality.generate_random(),
            needs=Needs.generate_random(),
            occupation=occupation,
            wealth=random.randint(10, 500),
        )

        # Настраиваем навыки на основе профессии
        npc._apply_occupation_skills()

        return npc

    def _apply_occupation_skills(self) -> None:
        """Добавляет навыки на основе профессии"""
        occupation_skills = {
            Occupation.FARMER: [("farming", 40), ("endurance", 2)],
            Occupation.BLACKSMITH: [("crafting", 50), ("strength", 2)],
            Occupation.MERCHANT: [("trading", 50), ("persuasion", 30)],
            Occupation.GUARD: [("combat", 40), ("perception", 20)],
            Occupation.INNKEEPER: [("cooking", 40), ("trading", 20)],
            Occupation.HEALER: [("medicine", 50), ("knowledge", 30)],
            Occupation.HUNTER: [("combat", 30), ("stealth", 40)],
            Occupation.CRAFTSMAN: [("crafting", 40)],
            Occupation.SCHOLAR: [("knowledge", 60)],
            Occupation.BARD: [("music", 50), ("persuasion", 30)],
        }

        skills_to_add = occupation_skills.get(self.occupation, [])
        for skill_name, value in skills_to_add:
            if hasattr(self.skills, skill_name):
                self.skills.improve(skill_name, value)
            elif hasattr(self.stats, skill_name):
                self.stats.modify(skill_name, value)
