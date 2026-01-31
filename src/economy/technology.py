"""
Система технологий - развитие производительных сил.

Технологии:
- Открываются через работу и эксперименты
- Передаются через обучение
- Накапливаются в знаниях общества
- Определяют уровень развития производства
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto
import random


class TechCategory(Enum):
    """Категории технологий"""
    TOOLS = "орудия труда"
    AGRICULTURE = "земледелие"
    CRAFTS = "ремёсла"
    CONSTRUCTION = "строительство"
    SOCIAL = "социальные"
    WARFARE = "военное дело"


class TechEra(Enum):
    """Технологические эпохи"""
    PRIMITIVE = ("первобытная", 0)
    STONE_AGE = ("каменный век", 1)
    COPPER_AGE = ("медный век", 2)
    BRONZE_AGE = ("бронзовый век", 3)
    IRON_AGE = ("железный век", 4)
    EARLY_MEDIEVAL = ("раннее средневековье", 5)

    def __init__(self, russian_name: str, level: int):
        self.russian_name = russian_name
        self.level = level


@dataclass
class Technology:
    """
    Технология - единица знания.

    Каждая технология:
    - Имеет требования (другие технологии, ресурсы)
    - Даёт бонусы к производству
    - Может открывать новые возможности
    """
    id: str
    name: str
    description: str
    category: TechCategory
    era: TechEra

    # Требования для открытия
    prerequisites: List[str] = field(default_factory=list)  # ID других технологий
    required_resources: Dict[str, float] = field(default_factory=dict)
    min_intelligence: int = 5         # Минимальный интеллект для открытия

    # Сложность открытия
    discovery_difficulty: float = 1.0  # Множитель сложности
    base_discovery_chance: float = 0.001  # Базовый шанс открытия в день

    # Эффекты
    production_bonus: Dict[str, float] = field(default_factory=dict)
    unlocks: List[str] = field(default_factory=list)  # Что открывает
    enables_resources: List[str] = field(default_factory=list)  # Какие ресурсы становятся доступны

    # История
    discovered_by: Optional[str] = None
    discovery_year: int = 0
    discovery_location: Optional[Tuple[int, int]] = None

    def is_available(self, known_techs: Set[str]) -> bool:
        """Проверяет, доступна ли технология для изучения"""
        return all(prereq in known_techs for prereq in self.prerequisites)


# === Определение всех технологий ===
TECHNOLOGIES: Dict[str, Technology] = {}


def _register_tech(tech: Technology) -> None:
    """Регистрирует технологию"""
    TECHNOLOGIES[tech.id] = tech


# Первобытные технологии
_register_tech(Technology(
    id="stone_knapping",
    name="обработка камня",
    description="Умение создавать каменные орудия путём откалывания",
    category=TechCategory.TOOLS,
    era=TechEra.PRIMITIVE,
    base_discovery_chance=0.01,  # Легко открыть
    production_bonus={"gathering": 0.2, "hunting": 0.3},
    enables_resources=["stone_tool"],
))

_register_tech(Technology(
    id="fire_making",
    name="добыча огня",
    description="Умение добывать и поддерживать огонь",
    category=TechCategory.TOOLS,
    era=TechEra.PRIMITIVE,
    base_discovery_chance=0.005,
    production_bonus={"cooking": 1.0, "warmth": 0.5},
    unlocks=["pottery", "metalworking_basic"],
))

_register_tech(Technology(
    id="basic_hunting",
    name="охота",
    description="Организованная охота на дичь",
    category=TechCategory.TOOLS,
    era=TechEra.PRIMITIVE,
    prerequisites=["stone_knapping"],
    base_discovery_chance=0.008,
    production_bonus={"hunting": 0.5},
    enables_resources=["meat", "leather", "bone"],
))

_register_tech(Technology(
    id="fishing",
    name="рыболовство",
    description="Ловля рыбы с помощью простых приспособлений",
    category=TechCategory.TOOLS,
    era=TechEra.PRIMITIVE,
    base_discovery_chance=0.008,
    production_bonus={"fishing": 0.5},
    enables_resources=["fish"],
))

_register_tech(Technology(
    id="gathering",
    name="собирательство",
    description="Систематический сбор съедобных растений",
    category=TechCategory.AGRICULTURE,
    era=TechEra.PRIMITIVE,
    base_discovery_chance=0.01,
    production_bonus={"gathering": 0.3},
    enables_resources=["berries", "mushrooms", "fiber"],
))

# Каменный век
_register_tech(Technology(
    id="bow_arrow",
    name="лук и стрелы",
    description="Дистанционное оружие для охоты",
    category=TechCategory.WARFARE,
    era=TechEra.STONE_AGE,
    prerequisites=["stone_knapping", "basic_hunting"],
    base_discovery_chance=0.003,
    production_bonus={"hunting": 0.8},
    enables_resources=["bow"],
))

_register_tech(Technology(
    id="pottery",
    name="гончарное дело",
    description="Создание глиняной посуды",
    category=TechCategory.CRAFTS,
    era=TechEra.STONE_AGE,
    prerequisites=["fire_making"],
    base_discovery_chance=0.002,
    production_bonus={"storage": 0.5},
    enables_resources=["pottery"],
))

_register_tech(Technology(
    id="weaving",
    name="ткачество",
    description="Плетение тканей из волокон",
    category=TechCategory.CRAFTS,
    era=TechEra.STONE_AGE,
    prerequisites=["gathering"],
    base_discovery_chance=0.002,
    production_bonus={"clothing": 0.5},
    enables_resources=["cloth"],
))

_register_tech(Technology(
    id="agriculture_basic",
    name="примитивное земледелие",
    description="Выращивание растений",
    category=TechCategory.AGRICULTURE,
    era=TechEra.STONE_AGE,
    prerequisites=["gathering", "stone_knapping"],
    base_discovery_chance=0.001,
    discovery_difficulty=2.0,
    production_bonus={"farming": 1.0},
    enables_resources=["grain", "vegetables"],
    unlocks=["plow", "irrigation"],
))

_register_tech(Technology(
    id="animal_domestication",
    name="приручение животных",
    description="Содержание животных для еды и работы",
    category=TechCategory.AGRICULTURE,
    era=TechEra.STONE_AGE,
    prerequisites=["basic_hunting"],
    base_discovery_chance=0.0008,
    discovery_difficulty=2.5,
    production_bonus={"herding": 1.0},
    enables_resources=["milk", "leather"],
))

_register_tech(Technology(
    id="construction_basic",
    name="строительство жилищ",
    description="Постройка простых укрытий",
    category=TechCategory.CONSTRUCTION,
    era=TechEra.STONE_AGE,
    prerequisites=["stone_knapping"],
    base_discovery_chance=0.003,
    production_bonus={"shelter": 0.5},
))

# Медный/Бронзовый век
_register_tech(Technology(
    id="metalworking_basic",
    name="обработка металла",
    description="Плавка и ковка меди",
    category=TechCategory.CRAFTS,
    era=TechEra.COPPER_AGE,
    prerequisites=["fire_making", "pottery"],
    required_resources={"ore": 5.0},
    base_discovery_chance=0.0005,
    discovery_difficulty=3.0,
    min_intelligence=8,
    production_bonus={"smithing": 1.0},
    unlocks=["bronze_working"],
))

_register_tech(Technology(
    id="bronze_working",
    name="бронзовое литьё",
    description="Создание бронзовых орудий и оружия",
    category=TechCategory.CRAFTS,
    era=TechEra.BRONZE_AGE,
    prerequisites=["metalworking_basic"],
    required_resources={"ore": 10.0},
    base_discovery_chance=0.0003,
    discovery_difficulty=4.0,
    min_intelligence=9,
    production_bonus={"smithing": 0.5, "warfare": 0.5},
    enables_resources=["bronze", "bronze_tool", "sword"],
))

_register_tech(Technology(
    id="plow",
    name="плуг",
    description="Орудие для обработки земли",
    category=TechCategory.AGRICULTURE,
    era=TechEra.BRONZE_AGE,
    prerequisites=["agriculture_basic", "animal_domestication"],
    base_discovery_chance=0.001,
    discovery_difficulty=2.0,
    production_bonus={"farming": 0.8},
))

_register_tech(Technology(
    id="writing",
    name="письменность",
    description="Система записи информации",
    category=TechCategory.SOCIAL,
    era=TechEra.BRONZE_AGE,
    prerequisites=["pottery"],
    base_discovery_chance=0.0002,
    discovery_difficulty=5.0,
    min_intelligence=10,
    production_bonus={"knowledge_transfer": 2.0},
))

# Железный век
_register_tech(Technology(
    id="iron_working",
    name="обработка железа",
    description="Плавка и ковка железа",
    category=TechCategory.CRAFTS,
    era=TechEra.IRON_AGE,
    prerequisites=["bronze_working"],
    required_resources={"ore": 20.0},
    base_discovery_chance=0.0001,
    discovery_difficulty=5.0,
    min_intelligence=10,
    production_bonus={"smithing": 1.0, "warfare": 1.0},
    enables_resources=["iron", "iron_tool", "sword"],
))

# Социальные технологии
_register_tech(Technology(
    id="tribal_organization",
    name="племенная организация",
    description="Формальная структура общины",
    category=TechCategory.SOCIAL,
    era=TechEra.PRIMITIVE,
    base_discovery_chance=0.005,
    production_bonus={"coordination": 0.3},
))

_register_tech(Technology(
    id="division_of_labor",
    name="разделение труда",
    description="Специализация членов общины",
    category=TechCategory.SOCIAL,
    era=TechEra.STONE_AGE,
    prerequisites=["tribal_organization"],
    base_discovery_chance=0.002,
    production_bonus={"all": 0.2},
))

_register_tech(Technology(
    id="trade",
    name="торговля",
    description="Обмен товарами между людьми",
    category=TechCategory.SOCIAL,
    era=TechEra.STONE_AGE,
    prerequisites=["division_of_labor"],
    base_discovery_chance=0.001,
    production_bonus={"trade": 1.0},
))

_register_tech(Technology(
    id="private_property",
    name="частная собственность",
    description="Признание личного владения",
    category=TechCategory.SOCIAL,
    era=TechEra.BRONZE_AGE,
    prerequisites=["agriculture_basic", "trade"],
    base_discovery_chance=0.0005,
    discovery_difficulty=3.0,
))


@dataclass
class KnowledgeSystem:
    """
    Система знаний общества.

    Отслеживает:
    - Известные технологии
    - Кто что знает
    - Процесс открытий
    - Передачу знаний
    """

    # Глобально известные технологии
    discovered_technologies: Set[str] = field(default_factory=set)

    # Кто какие технологии знает (npc_id -> set of tech_ids)
    individual_knowledge: Dict[str, Set[str]] = field(default_factory=dict)

    # Прогресс открытий (tech_id -> progress 0-1)
    discovery_progress: Dict[str, float] = field(default_factory=dict)

    # История открытий
    discovery_history: List[Tuple[str, str, int]] = field(default_factory=list)

    def add_knowledge(self, npc_id: str, tech_id: str) -> None:
        """Добавляет знание NPC"""
        if npc_id not in self.individual_knowledge:
            self.individual_knowledge[npc_id] = set()
        self.individual_knowledge[npc_id].add(tech_id)

        # Добавляем в глобальные знания
        self.discovered_technologies.add(tech_id)

    def npc_knows(self, npc_id: str, tech_id: str) -> bool:
        """Проверяет, знает ли NPC технологию"""
        if npc_id not in self.individual_knowledge:
            return False
        return tech_id in self.individual_knowledge[npc_id]

    def get_npc_knowledge(self, npc_id: str) -> Set[str]:
        """Возвращает знания NPC"""
        return self.individual_knowledge.get(npc_id, set())

    def try_discovery(self, npc_id: str, activity: str,
                      intelligence: int, year: int) -> Optional[Technology]:
        """
        Попытка открыть технологию через деятельность.

        Возвращает открытую технологию или None.
        """
        npc_knowledge = self.get_npc_knowledge(npc_id)

        # Находим технологии, которые можно открыть
        available = []
        for tech_id, tech in TECHNOLOGIES.items():
            if tech_id in npc_knowledge:
                continue
            if not tech.is_available(npc_knowledge):
                continue
            if intelligence < tech.min_intelligence:
                continue

            # Проверяем, связана ли деятельность с технологией
            activity_relevance = self._get_activity_relevance(activity, tech)
            if activity_relevance > 0:
                available.append((tech, activity_relevance))

        if not available:
            return None

        # Пытаемся открыть
        for tech, relevance in available:
            # Прогресс зависит от интеллекта и релевантности
            progress_gain = (tech.base_discovery_chance *
                             relevance *
                             (intelligence / 10) /
                             tech.discovery_difficulty)

            # Накапливаем прогресс
            current = self.discovery_progress.get(tech.id, 0)
            new_progress = current + progress_gain

            if random.random() < new_progress:
                # Открытие!
                self.add_knowledge(npc_id, tech.id)
                tech.discovered_by = npc_id
                tech.discovery_year = year
                self.discovery_history.append((tech.id, npc_id, year))
                self.discovery_progress[tech.id] = 0
                return tech
            else:
                self.discovery_progress[tech.id] = min(0.5, new_progress)

        return None

    def transfer_knowledge(self, teacher_id: str, student_id: str,
                           tech_id: str, hours: float,
                           teacher_skill: float = 1.0,
                           student_intelligence: int = 10) -> bool:
        """
        Передача знания от учителя к ученику.

        Возвращает True, если знание передано.
        """
        if not self.npc_knows(teacher_id, tech_id):
            return False

        if self.npc_knows(student_id, tech_id):
            return True  # Уже знает

        tech = TECHNOLOGIES.get(tech_id)
        if not tech:
            return False

        # Шанс обучения
        learn_chance = (hours * 0.1 *
                        teacher_skill *
                        (student_intelligence / 10) /
                        tech.discovery_difficulty)

        if random.random() < learn_chance:
            self.add_knowledge(student_id, tech_id)
            return True

        return False

    def _get_activity_relevance(self, activity: str, tech: Technology) -> float:
        """Определяет релевантность деятельности для технологии"""
        relevance_map = {
            "gathering": ["gathering", "agriculture_basic", "weaving"],
            "hunting": ["basic_hunting", "bow_arrow", "stone_knapping"],
            "fishing": ["fishing"],
            "crafting": ["pottery", "weaving", "metalworking_basic", "bronze_working", "iron_working"],
            "farming": ["agriculture_basic", "plow", "irrigation"],
            "building": ["construction_basic"],
            "socializing": ["tribal_organization", "division_of_labor", "trade", "writing"],
        }

        related_techs = relevance_map.get(activity, [])
        if tech.id in related_techs:
            return 1.0
        if tech.category.name.lower() in activity:
            return 0.5
        return 0.1

    def get_current_era(self) -> TechEra:
        """Определяет текущую технологическую эпоху"""
        if not self.discovered_technologies:
            return TechEra.PRIMITIVE

        max_era = TechEra.PRIMITIVE
        for tech_id in self.discovered_technologies:
            tech = TECHNOLOGIES.get(tech_id)
            if tech and tech.era.level > max_era.level:
                max_era = tech.era

        return max_era

    def get_available_technologies(self) -> List[Technology]:
        """Возвращает технологии, доступные для открытия"""
        available = []
        for tech_id, tech in TECHNOLOGIES.items():
            if tech_id in self.discovered_technologies:
                continue
            if tech.is_available(self.discovered_technologies):
                available.append(tech)
        return available

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику знаний"""
        era = self.get_current_era()
        by_category = {}
        for tech_id in self.discovered_technologies:
            tech = TECHNOLOGIES.get(tech_id)
            if tech:
                cat = tech.category.name
                by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "era": era.russian_name,
            "total_discovered": len(self.discovered_technologies),
            "by_category": by_category,
            "knowledge_holders": len(self.individual_knowledge),
        }
