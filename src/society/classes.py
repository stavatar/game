"""
Система классов - emergent социальная структура.

По Марксу, класс определяется отношением к средствам производства:
- Владельцы средств производства (эксплуататоры)
- Не владеющие (эксплуатируемые)

Классы НЕ задаются жёстко, а ВОЗНИКАЮТ из экономических отношений.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto
import math


class ClassType(Enum):
    """
    Типы классов (возникают по мере развития).

    В примитивной общине классов нет.
    Они появляются с возникновением частной собственности.
    """
    NONE = ("нет класса", 0)                    # Примитивная община
    COMMUNAL_MEMBER = ("общинник", 1)           # Член общины
    LANDOWNER = ("землевладелец", 2)            # Владеет землёй
    LANDLESS = ("безземельный", 2)              # Не владеет землёй
    CRAFTSMAN = ("ремесленник", 2)              # Владеет мастерской
    LABORER = ("работник", 2)                   # Работает на других
    ELDER = ("старейшина", 1)                   # Общинная элита
    CHIEF = ("вождь", 2)                        # Военный лидер

    def __init__(self, russian_name: str, development_level: int):
        self.russian_name = russian_name
        self.development_level = development_level


@dataclass
class SocialClass:
    """
    Социальный класс.

    Класс - это группа людей с одинаковым отношением к средствам производства.
    """
    class_type: ClassType
    members: Set[str] = field(default_factory=set)

    # Характеристики класса
    avg_wealth: float = 0.0
    avg_property: float = 0.0
    political_power: float = 0.0        # Влияние на решения

    # Классовое сознание (развивается со временем)
    class_consciousness: float = 0.0     # 0-1, осознание общих интересов

    # Отношения с другими классами
    relations: Dict[str, float] = field(default_factory=dict)  # class_type -> -1 до 1

    def add_member(self, npc_id: str) -> None:
        self.members.add(npc_id)

    def remove_member(self, npc_id: str) -> None:
        self.members.discard(npc_id)

    def get_size(self) -> int:
        return len(self.members)


@dataclass
class ClassConflict:
    """Классовый конфликт"""
    id: str
    class1: ClassType
    class2: ClassType
    intensity: float            # 0-1
    cause: str
    year_started: int
    resolved: bool = False
    year_resolved: Optional[int] = None
    outcome: str = ""


class ClassSystem:
    """
    Система классов.

    Определяет классовую принадлежность на основе:
    - Владения средствами производства
    - Богатства
    - Социального положения

    Отслеживает:
    - Возникновение классов
    - Классовое неравенство
    - Классовые конфликты
    """

    def __init__(self):
        # Классы
        self.classes: Dict[ClassType, SocialClass] = {}

        # NPC -> его класс
        self.npc_class: Dict[str, ClassType] = {}

        # Конфликты
        self.conflicts: List[ClassConflict] = []

        # История
        self.class_emergence_history: List[Tuple[ClassType, int]] = []

        # Флаги развития
        self.classes_emerged: bool = False
        self.first_class_year: int = 0

    def determine_class(self,
                        npc_id: str,
                        owns_land: bool,
                        owns_tools: bool,
                        owns_livestock: bool,
                        wealth: float,
                        works_for_others: bool,
                        is_elder: bool = False,
                        is_chief: bool = False,
                        private_property_exists: bool = False) -> ClassType:
        """
        Определяет класс NPC на основе экономического положения.

        Класс - emergent свойство, не задаётся напрямую!
        """
        # Если частной собственности ещё нет - все общинники
        if not private_property_exists:
            if is_chief:
                return ClassType.CHIEF
            if is_elder:
                return ClassType.ELDER
            return ClassType.COMMUNAL_MEMBER

        # Определяем по владению средствами производства
        owns_means_of_production = owns_land or owns_tools or owns_livestock

        if owns_means_of_production:
            if owns_land:
                return ClassType.LANDOWNER
            else:
                return ClassType.CRAFTSMAN
        else:
            if works_for_others:
                return ClassType.LABORER
            else:
                return ClassType.LANDLESS

    def update_npc_class(self, npc_id: str, new_class: ClassType, year: int) -> bool:
        """
        Обновляет класс NPC.

        Возвращает True, если класс изменился.
        """
        old_class = self.npc_class.get(npc_id)

        if old_class == new_class:
            return False

        # Удаляем из старого класса
        if old_class and old_class in self.classes:
            self.classes[old_class].remove_member(npc_id)

        # Добавляем в новый класс
        if new_class not in self.classes:
            self.classes[new_class] = SocialClass(class_type=new_class)

            # Фиксируем возникновение нового класса
            if new_class not in [ClassType.NONE, ClassType.COMMUNAL_MEMBER]:
                self.class_emergence_history.append((new_class, year))

                if not self.classes_emerged:
                    self.classes_emerged = True
                    self.first_class_year = year

        self.classes[new_class].add_member(npc_id)
        self.npc_class[npc_id] = new_class

        return True

    def calculate_inequality(self, wealth_data: Dict[str, float]) -> float:
        """
        Вычисляет классовое неравенство.

        Использует коэффициент Джини.
        """
        if not wealth_data:
            return 0.0

        values = sorted(wealth_data.values())
        n = len(values)
        if n <= 1:
            return 0.0

        # Коэффициент Джини
        cumulative = sum((2 * i - n - 1) * v for i, v in enumerate(values, 1))
        return cumulative / (n * sum(values)) if sum(values) > 0 else 0.0

    def check_class_tension(self) -> float:
        """
        Вычисляет напряжённость между классами.

        Зависит от:
        - Неравенства
        - Размера угнетённых классов
        - Классового сознания
        """
        if not self.classes_emerged:
            return 0.0

        tension = 0.0

        # Находим эксплуататоров и эксплуатируемых
        exploiters = [ClassType.LANDOWNER, ClassType.CHIEF]
        exploited = [ClassType.LANDLESS, ClassType.LABORER]

        exploiter_count = sum(
            self.classes[c].get_size()
            for c in exploiters if c in self.classes
        )
        exploited_count = sum(
            self.classes[c].get_size()
            for c in exploited if c in self.classes
        )

        if exploiter_count == 0 or exploited_count == 0:
            return 0.0

        # Диспропорция
        ratio = exploited_count / exploiter_count
        tension += min(1.0, ratio / 10)  # Чем больше эксплуатируемых - тем больше напряжение

        # Классовое сознание увеличивает напряжение
        for class_type in exploited:
            if class_type in self.classes:
                tension += self.classes[class_type].class_consciousness * 0.3

        return min(1.0, tension)

    def check_for_conflict(self, year: int) -> Optional[ClassConflict]:
        """Проверяет, не начался ли классовый конфликт"""
        tension = self.check_class_tension()

        if tension < 0.5:
            return None

        # Вероятность конфликта зависит от напряжения
        if tension > 0.8 or (tension > 0.5 and len(self.conflicts) == 0):
            # Определяем стороны конфликта
            if ClassType.LANDOWNER in self.classes and ClassType.LANDLESS in self.classes:
                conflict = ClassConflict(
                    id=f"conflict_{year}",
                    class1=ClassType.LANDLESS,
                    class2=ClassType.LANDOWNER,
                    intensity=tension,
                    cause="неравенство в распределении земли",
                    year_started=year,
                )
                self.conflicts.append(conflict)
                return conflict

        return None

    def increase_class_consciousness(self, class_type: ClassType,
                                      amount: float = 0.01) -> None:
        """Увеличивает классовое сознание"""
        if class_type in self.classes:
            self.classes[class_type].class_consciousness = min(
                1.0,
                self.classes[class_type].class_consciousness + amount
            )

    def get_class_distribution(self) -> Dict[str, int]:
        """Возвращает распределение по классам"""
        return {
            c.class_type.russian_name: c.get_size()
            for c in self.classes.values()
            if c.get_size() > 0
        }

    def get_dominant_class(self) -> Optional[ClassType]:
        """Возвращает доминирующий класс (по политической власти)"""
        if not self.classes:
            return None

        return max(
            self.classes.keys(),
            key=lambda c: self.classes[c].political_power
        )

    def update_class_relations(self, year: int) -> None:
        """Обновляет отношения между классами"""
        # Антагонистические классы
        antagonists = [
            (ClassType.LANDOWNER, ClassType.LANDLESS),
            (ClassType.LANDOWNER, ClassType.LABORER),
        ]

        for c1, c2 in antagonists:
            if c1 in self.classes and c2 in self.classes:
                # Отношения ухудшаются с ростом неравенства
                self.classes[c1].relations[c2.name] = -0.5
                self.classes[c2].relations[c1.name] = -0.5

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику классов"""
        return {
            "classes_emerged": self.classes_emerged,
            "first_class_year": self.first_class_year,
            "class_distribution": self.get_class_distribution(),
            "class_tension": round(self.check_class_tension(), 2),
            "active_conflicts": len([c for c in self.conflicts if not c.resolved]),
            "dominant_class": (
                self.get_dominant_class().russian_name
                if self.get_dominant_class() else "нет"
            ),
        }
