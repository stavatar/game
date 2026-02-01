"""
Система классов - emergent социальная структура.

По Марксу, класс определяется отношением к средствам производства:
- Владельцы средств производства (эксплуататоры)
- Не владеющие (эксплуатируемые)

Классы НЕ задаются жёстко, а ВОЗНИКАЮТ из экономических отношений.

Теория классовой борьбы основана на:
- Britannica: Class Struggle
- Lukacs: Class Consciousness (1920)
- Gramsci: Prison Notebooks - Hegemony Theory
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, TYPE_CHECKING
from enum import Enum, auto
import math
import random
from uuid import uuid4

if TYPE_CHECKING:
    from ..culture.beliefs import BeliefSystem
    from ..economy.property import OwnershipSystem


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

    @property
    def is_exploiter(self) -> bool:
        """Является ли класс эксплуататорским"""
        return self in [ClassType.LANDOWNER, ClassType.CHIEF]

    @property
    def is_exploited(self) -> bool:
        """Является ли класс эксплуатируемым"""
        return self in [ClassType.LANDLESS, ClassType.LABORER]


class ConflictType(Enum):
    """
    Типы классовых конфликтов.

    От мирных форм к революционным:
    - Забастовка: отказ от работы
    - Бунт: стихийное восстание
    - Восстание: организованное выступление
    - Революция: попытка смены общественного строя
    """
    STRIKE = ("забастовка", 0.2, "отказ от работы")
    LAND_DISPUTE = ("земельный спор", 0.3, "конфликт за землю")
    RIOT = ("бунт", 0.5, "стихийное восстание")
    UPRISING = ("восстание", 0.7, "организованное выступление")
    REBELLION = ("революция", 0.9, "попытка смены строя")

    def __init__(self, russian_name: str, violence_level: float, description: str):
        self.russian_name = russian_name
        self.violence_level = violence_level
        self.description = description


class ConflictStage(Enum):
    """
    Стадии развития классового конфликта.

    По диалектике: количественные изменения → качественный скачок
    """
    BREWING = ("назревание", 0.0, 0.3)      # Накопление противоречий
    LATENT = ("латентный", 0.3, 0.5)        # Скрытое противостояние
    ACTIVE = ("активный", 0.5, 0.7)          # Открытое противостояние
    ESCALATING = ("эскалация", 0.7, 0.9)     # Обострение конфликта
    CRISIS = ("кризис", 0.9, 1.0)            # Критическая точка
    RESOLVING = ("разрешение", 0.5, 0.3)     # Поиск решения
    RESOLVED = ("завершён", 0.0, 0.0)        # Конфликт окончен

    def __init__(self, russian_name: str, min_intensity: float, max_intensity: float):
        self.russian_name = russian_name
        self.min_intensity = min_intensity
        self.max_intensity = max_intensity


class ConflictOutcome(Enum):
    """
    Возможные исходы классового конфликта.

    Определяется соотношением сил и классовым сознанием.
    """
    SUPPRESSED = ("подавлен", -0.3, 0.0)           # Победа эксплуататоров
    STALEMATE = ("ничья", 0.0, 0.1)                # Патовая ситуация
    COMPROMISE = ("компромисс", 0.1, 0.2)          # Частичные уступки
    PARTIAL_VICTORY = ("частичная победа", 0.2, 0.3)  # Частичная победа угнетённых
    VICTORY = ("победа", 0.3, 0.5)                 # Полная победа угнетённых
    REVOLUTION = ("революция", 0.5, 1.0)           # Смена общественного строя

    def __init__(self, russian_name: str, consciousness_change: float,
                 property_redistribution: float):
        self.russian_name = russian_name
        self.consciousness_change = consciousness_change  # Влияние на сознание
        self.property_redistribution = property_redistribution  # % перераспределения


class ConsciousnessPhase(Enum):
    """
    Фазы развития классового сознания (по Грамши).

    От экономико-корпоративного к политическому.
    """
    NONE = ("отсутствует", 0.0, 0.1)           # Нет осознания
    ECONOMIC = ("экономическое", 0.1, 0.3)    # Осознание экономических интересов
    CORPORATIVE = ("корпоративное", 0.3, 0.5) # Осознание групповых интересов
    POLITICAL = ("политическое", 0.5, 0.7)    # Осознание классовых интересов
    HEGEMONIC = ("гегемоническое", 0.7, 1.0)  # Борьба за гегемонию

    def __init__(self, russian_name: str, min_level: float, max_level: float):
        self.russian_name = russian_name
        self.min_level = min_level
        self.max_level = max_level

    @classmethod
    def from_level(cls, level: float) -> 'ConsciousnessPhase':
        """Определяет фазу по уровню сознания"""
        for phase in cls:
            if phase.min_level <= level < phase.max_level:
                return phase
        return cls.HEGEMONIC if level >= 0.7 else cls.NONE


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
    """
    Классовый конфликт.

    Конфликт между классами возникает из объективных противоречий
    в отношениях собственности и распределения прибавочного продукта.

    Динамика конфликта:
    1. Назревание (накопление противоречий)
    2. Латентная фаза (скрытое недовольство)
    3. Активная фаза (открытое противостояние)
    4. Эскалация/Разрешение
    """
    id: str

    # Тип и стороны конфликта
    conflict_type: ConflictType
    oppressed_class: ClassType      # Угнетённый класс (инициатор)
    ruling_class: ClassType         # Правящий класс (защитник status quo)

    # Участники (NPC)
    participants: Dict[str, ClassType] = field(default_factory=dict)  # npc_id -> class
    leaders: List[str] = field(default_factory=list)  # ID лидеров восстания
    suppression_forces: List[str] = field(default_factory=list)  # ID подавителей

    # Состояние конфликта
    stage: ConflictStage = ConflictStage.BREWING
    intensity: float = 0.1          # 0-1, сила конфликта
    violence_level: float = 0.0     # 0-1, уровень насилия
    organization_level: float = 0.0 # 0-1, организованность

    # Причины и триггеры
    primary_cause: str = ""
    grievances: List[str] = field(default_factory=list)  # Список жалоб/претензий
    trigger_event: str = ""         # Событие-триггер

    # Требования и уступки
    demands: List[str] = field(default_factory=list)
    concessions_offered: List[str] = field(default_factory=list)
    concessions_rejected: List[str] = field(default_factory=list)

    # Временные характеристики
    year_started: int = 0
    days_active: int = 0
    year_resolved: Optional[int] = None

    # Экономические последствия
    production_loss: float = 0.0    # Потери производства (0-1)
    property_damaged: float = 0.0   # Повреждённое имущество

    # Идеологическая поддержка
    ideological_support: Dict[str, float] = field(default_factory=dict)  # belief_id -> support

    # Результат
    resolved: bool = False
    outcome: Optional[ConflictOutcome] = None
    consequences: List[str] = field(default_factory=list)

    # Для обратной совместимости
    @property
    def class1(self) -> ClassType:
        return self.oppressed_class

    @property
    def class2(self) -> ClassType:
        return self.ruling_class

    @property
    def cause(self) -> str:
        return self.primary_cause

    def add_participant(self, npc_id: str, npc_class: ClassType) -> None:
        """Добавляет участника конфликта"""
        self.participants[npc_id] = npc_class

    def add_leader(self, npc_id: str) -> None:
        """Добавляет лидера восстания"""
        if npc_id not in self.leaders:
            self.leaders.append(npc_id)
            # Лидеры повышают организованность
            self.organization_level = min(1.0, self.organization_level + 0.1)

    def add_grievance(self, grievance: str) -> None:
        """Добавляет жалобу/претензию"""
        if grievance not in self.grievances:
            self.grievances.append(grievance)
            # Жалобы накапливают напряжение
            self.intensity = min(1.0, self.intensity + 0.05)

    def add_demand(self, demand: str) -> None:
        """Добавляет требование"""
        if demand not in self.demands:
            self.demands.append(demand)

    def escalate(self, amount: float = 0.1) -> bool:
        """
        Эскалация конфликта.

        Возвращает True, если произошёл переход на новую стадию.
        """
        old_stage = self.stage
        self.intensity = min(1.0, self.intensity + amount)
        self.violence_level = min(1.0, self.violence_level + amount * 0.5)

        # Определяем новую стадию
        new_stage = self._determine_stage()
        if new_stage != old_stage:
            self.stage = new_stage
            return True
        return False

    def de_escalate(self, amount: float = 0.1) -> bool:
        """
        Деэскалация конфликта.

        Возвращает True, если произошёл переход на новую стадию.
        """
        old_stage = self.stage
        self.intensity = max(0.0, self.intensity - amount)
        self.violence_level = max(0.0, self.violence_level - amount * 0.3)

        # Переход к разрешению
        if self.intensity < 0.3 and self.stage not in [
            ConflictStage.RESOLVED, ConflictStage.RESOLVING
        ]:
            self.stage = ConflictStage.RESOLVING
            return True
        return False

    def _determine_stage(self) -> ConflictStage:
        """Определяет стадию конфликта по интенсивности"""
        if self.resolved:
            return ConflictStage.RESOLVED

        if self.intensity >= 0.9:
            return ConflictStage.CRISIS
        elif self.intensity >= 0.7:
            return ConflictStage.ESCALATING
        elif self.intensity >= 0.5:
            return ConflictStage.ACTIVE
        elif self.intensity >= 0.3:
            return ConflictStage.LATENT
        else:
            return ConflictStage.BREWING

    def update_conflict_type(self) -> bool:
        """
        Обновляет тип конфликта в зависимости от интенсивности.

        Возвращает True, если тип изменился.
        """
        old_type = self.conflict_type

        # Определяем новый тип по интенсивности и организованности
        if self.intensity >= 0.9 and self.organization_level >= 0.7:
            new_type = ConflictType.REBELLION
        elif self.intensity >= 0.7:
            new_type = ConflictType.UPRISING
        elif self.intensity >= 0.5:
            new_type = ConflictType.RIOT
        elif self.intensity >= 0.3:
            new_type = ConflictType.LAND_DISPUTE
        else:
            new_type = ConflictType.STRIKE

        if new_type != old_type:
            self.conflict_type = new_type
            return True
        return False

    def resolve(self, outcome: ConflictOutcome, year: int) -> None:
        """Разрешает конфликт с указанным исходом"""
        self.resolved = True
        self.outcome = outcome
        self.year_resolved = year
        self.stage = ConflictStage.RESOLVED
        self.consequences.append(f"Конфликт завершён: {outcome.russian_name}")

    def get_oppressed_strength(self) -> float:
        """Вычисляет силу угнетённой стороны"""
        base = len([p for p, c in self.participants.items()
                    if c == self.oppressed_class])
        # Модификаторы
        leader_bonus = len(self.leaders) * 0.2
        org_bonus = self.organization_level * 0.5
        return base * (1 + leader_bonus + org_bonus)

    def get_ruling_strength(self) -> float:
        """Вычисляет силу правящей стороны"""
        base = len([p for p, c in self.participants.items()
                    if c == self.ruling_class])
        suppression_bonus = len(self.suppression_forces) * 0.3
        return base * (1 + suppression_bonus)

    def get_summary(self) -> str:
        """Возвращает краткое описание конфликта"""
        return (
            f"{self.conflict_type.russian_name}: "
            f"{self.oppressed_class.russian_name} vs {self.ruling_class.russian_name} "
            f"({self.stage.russian_name}, интенсивность: {self.intensity:.0%})"
        )


@dataclass
class ConsciousnessSpreadEvent:
    """
    Событие распространения классового сознания.

    Сознание распространяется через:
    - Социальное взаимодействие
    - Общий опыт эксплуатации
    - Влияние "органических интеллектуалов" (по Грамши)
    """
    from_npc: str
    to_npc: str
    class_type: ClassType
    amount: float
    trigger: str
    timestamp: int = 0


class ClassConsciousnessSystem:
    """
    Система распространения классового сознания.

    Основана на теории Грамши о культурной гегемонии:
    - Ложное сознание подавляет классовую борьбу
    - Кризисы разрушают ложное сознание
    - Органические интеллектуалы распространяют истинное сознание
    """

    # Верования, подавляющие классовое сознание (ложное сознание)
    FALSE_CONSCIOUSNESS_BELIEFS = [
        'hierarchy_divine',      # Иерархия божественна
        'property_sacred',       # Собственность священна
        'natural_inequality',    # Неравенство естественно
    ]

    # Верования, поддерживающие классовое сознание
    TRUE_CONSCIOUSNESS_BELIEFS = [
        'equality',              # Равенство
        'collective_good',       # Коллективное благо
        'labor_value',           # Ценность труда
    ]

    def __init__(self):
        self.spread_history: List[ConsciousnessSpreadEvent] = []
        self.organic_intellectuals: Set[str] = set()  # NPC-просветители

    def spread_consciousness(
        self,
        from_npc_id: str,
        to_npc_id: str,
        class_system: 'ClassSystem',
        belief_system: Optional['BeliefSystem'] = None,
        relationship_strength: float = 0.5,
        trigger: str = "социальное взаимодействие"
    ) -> Optional[ConsciousnessSpreadEvent]:
        """
        Распространяет классовое сознание от одного NPC к другому.

        Факторы влияния:
        1. Они должны быть одного класса
        2. Сила отношений
        3. Уровень сознания источника
        4. Верования (ложное сознание vs истинное)
        5. Статус органического интеллектуала
        """
        # Получаем классы
        source_class = class_system.npc_class.get(from_npc_id)
        target_class = class_system.npc_class.get(to_npc_id)

        if not source_class or not target_class:
            return None

        # Только между членами одного класса
        if source_class != target_class:
            return None

        # Только для эксплуатируемых классов
        if not source_class.is_exploited:
            return None

        # Получаем уровень сознания источника
        source_consciousness = 0.0
        if source_class in class_system.classes:
            source_consciousness = class_system.classes[source_class].class_consciousness

        # Минимальный уровень для распространения
        if source_consciousness < 0.1:
            return None

        # Базовое влияние
        base_influence = source_consciousness * 0.1

        # Модификатор отношений
        relationship_modifier = 0.5 + relationship_strength * 0.5
        base_influence *= relationship_modifier

        # Модификатор органического интеллектуала
        if from_npc_id in self.organic_intellectuals:
            base_influence *= 2.0

        # Модификатор верований (ложное сознание)
        belief_modifier = self._calculate_belief_modifier(
            to_npc_id, belief_system
        )
        base_influence *= belief_modifier

        # Ограничиваем влияние
        final_amount = min(0.15, max(0.01, base_influence))

        event = ConsciousnessSpreadEvent(
            from_npc=from_npc_id,
            to_npc=to_npc_id,
            class_type=source_class,
            amount=final_amount,
            trigger=trigger
        )

        self.spread_history.append(event)
        return event

    def _calculate_belief_modifier(
        self,
        npc_id: str,
        belief_system: Optional['BeliefSystem']
    ) -> float:
        """
        Вычисляет модификатор от верований.

        Ложное сознание снижает восприимчивость к классовому сознанию.
        """
        if not belief_system:
            return 1.0

        modifier = 1.0

        # Получаем верования NPC (если система поддерживает)
        npc_beliefs = getattr(belief_system, 'npc_beliefs', {}).get(npc_id, set())

        # Ложное сознание подавляет
        for false_belief in self.FALSE_CONSCIOUSNESS_BELIEFS:
            if false_belief in npc_beliefs:
                modifier *= 0.5

        # Истинное сознание усиливает
        for true_belief in self.TRUE_CONSCIOUSNESS_BELIEFS:
            if true_belief in npc_beliefs:
                modifier *= 1.5

        return max(0.1, min(2.0, modifier))

    def register_organic_intellectual(self, npc_id: str) -> None:
        """
        Регистрирует NPC как органического интеллектуала.

        Органические интеллектуалы (по Грамши) - представители класса,
        которые осознают и выражают интересы своего класса.
        """
        self.organic_intellectuals.add(npc_id)

    def check_intellectual_emergence(
        self,
        npc_id: str,
        intelligence: int,
        class_consciousness: float,
        social_connections: int
    ) -> bool:
        """
        Проверяет, может ли NPC стать органическим интеллектуалом.

        Условия:
        - Высокий интеллект (>12)
        - Высокое классовое сознание (>0.5)
        - Много социальных связей (>5)
        """
        if (intelligence > 12 and
            class_consciousness > 0.5 and
            social_connections > 5):
            self.register_organic_intellectual(npc_id)
            return True
        return False

    def crisis_effect(
        self,
        class_system: 'ClassSystem',
        crisis_severity: float
    ) -> float:
        """
        Эффект кризиса на классовое сознание.

        Кризисы (голод, катаклизмы) разрушают ложное сознание
        и ускоряют развитие классового сознания.
        """
        consciousness_boost = crisis_severity * 0.2

        # Применяем ко всем эксплуатируемым классам
        for class_type, social_class in class_system.classes.items():
            if class_type.is_exploited:
                social_class.class_consciousness = min(
                    1.0,
                    social_class.class_consciousness + consciousness_boost
                )

        return consciousness_boost


class ConflictResolutionSystem:
    """
    Система разрешения классовых конфликтов.

    Определяет исход конфликта на основе:
    - Соотношения сил
    - Уровня организации
    - Классового сознания
    - Внешних факторов
    """

    def __init__(self):
        self.resolution_history: List[Tuple[str, ConflictOutcome, int]] = []

    def calculate_force_ratio(
        self,
        conflict: ClassConflict,
        class_system: 'ClassSystem',
        ownership_system: Optional['OwnershipSystem'] = None
    ) -> float:
        """
        Вычисляет соотношение сил сторон.

        >1.0 означает преимущество угнетённых
        <1.0 означает преимущество правящего класса
        """
        oppressed_strength = self._calculate_side_strength(
            conflict.oppressed_class,
            class_system,
            ownership_system,
            is_oppressed=True,
            conflict=conflict
        )

        ruling_strength = self._calculate_side_strength(
            conflict.ruling_class,
            class_system,
            ownership_system,
            is_oppressed=False,
            conflict=conflict
        )

        if ruling_strength == 0:
            return float('inf')

        return oppressed_strength / ruling_strength

    def _calculate_side_strength(
        self,
        class_type: ClassType,
        class_system: 'ClassSystem',
        ownership_system: Optional['OwnershipSystem'],
        is_oppressed: bool,
        conflict: ClassConflict
    ) -> float:
        """Вычисляет силу одной стороны конфликта"""
        if class_type not in class_system.classes:
            return 0.0

        social_class = class_system.classes[class_type]

        # Базовая сила = численность
        strength = social_class.get_size()

        if is_oppressed:
            # Модификаторы для угнетённых
            # Классовое сознание критически важно
            consciousness_modifier = 1 + social_class.class_consciousness * 2
            strength *= consciousness_modifier

            # Организованность
            org_modifier = 1 + conflict.organization_level
            strength *= org_modifier

            # Лидеры
            leader_modifier = 1 + len(conflict.leaders) * 0.2
            strength *= leader_modifier
        else:
            # Модификаторы для правящего класса
            # Богатство и ресурсы
            wealth_modifier = 1 + social_class.avg_wealth / 1000
            strength *= wealth_modifier

            # Политическая власть
            power_modifier = 1 + social_class.political_power
            strength *= power_modifier

            # Силы подавления
            suppression_modifier = 1 + len(conflict.suppression_forces) * 0.3
            strength *= suppression_modifier

        return max(0.1, strength)

    def attempt_resolution(
        self,
        conflict: ClassConflict,
        class_system: 'ClassSystem',
        ownership_system: Optional['OwnershipSystem'] = None,
        year: int = 0
    ) -> Optional[ConflictOutcome]:
        """
        Пытается разрешить конфликт.

        Возвращает исход, если конфликт может быть разрешён.
        """
        # Конфликт должен быть в стадии разрешения или кризиса
        if conflict.stage not in [
            ConflictStage.RESOLVING,
            ConflictStage.CRISIS,
            ConflictStage.ESCALATING
        ]:
            # Проверяем длительность - затяжные конфликты разрешаются
            if conflict.days_active < 30:
                return None

        force_ratio = self.calculate_force_ratio(
            conflict, class_system, ownership_system
        )

        # Добавляем элемент случайности
        random_factor = random.uniform(0.8, 1.2)
        adjusted_ratio = force_ratio * random_factor

        # Определяем исход
        if adjusted_ratio > 3.0:
            outcome = ConflictOutcome.REVOLUTION
        elif adjusted_ratio > 2.0:
            outcome = ConflictOutcome.VICTORY
        elif adjusted_ratio > 1.5:
            outcome = ConflictOutcome.PARTIAL_VICTORY
        elif adjusted_ratio > 0.8:
            outcome = ConflictOutcome.COMPROMISE
        elif adjusted_ratio > 0.5:
            outcome = ConflictOutcome.STALEMATE
        else:
            outcome = ConflictOutcome.SUPPRESSED

        self.resolution_history.append((conflict.id, outcome, year))
        return outcome

    def apply_outcome(
        self,
        conflict: ClassConflict,
        outcome: ConflictOutcome,
        class_system: 'ClassSystem',
        ownership_system: Optional['OwnershipSystem'] = None,
        year: int = 0
    ) -> List[str]:
        """
        Применяет последствия исхода конфликта.

        Возвращает список событий/последствий.
        """
        events = []

        # Разрешаем конфликт
        conflict.resolve(outcome, year)

        # Изменение классового сознания
        if conflict.oppressed_class in class_system.classes:
            class_system.classes[conflict.oppressed_class].class_consciousness = min(
                1.0,
                class_system.classes[conflict.oppressed_class].class_consciousness +
                outcome.consciousness_change
            )

        # Применяем специфические последствия
        if outcome == ConflictOutcome.REVOLUTION:
            events.extend(self._apply_revolution(
                conflict, class_system, ownership_system
            ))
        elif outcome == ConflictOutcome.VICTORY:
            events.extend(self._apply_victory(
                conflict, class_system, ownership_system
            ))
        elif outcome == ConflictOutcome.PARTIAL_VICTORY:
            events.extend(self._apply_partial_victory(
                conflict, class_system
            ))
        elif outcome == ConflictOutcome.COMPROMISE:
            events.extend(self._apply_compromise(conflict))
        elif outcome == ConflictOutcome.SUPPRESSED:
            events.extend(self._apply_suppression(
                conflict, class_system
            ))

        events.append(
            f"Конфликт '{conflict.conflict_type.russian_name}' завершён: "
            f"{outcome.russian_name}"
        )

        return events

    def _apply_revolution(
        self,
        conflict: ClassConflict,
        class_system: 'ClassSystem',
        ownership_system: Optional['OwnershipSystem']
    ) -> List[str]:
        """Применяет последствия революции"""
        events = ["Произошла революция!"]

        # Перераспределение собственности (50%)
        if ownership_system:
            redistributed = self._redistribute_property(
                ownership_system, 0.5
            )
            events.append(f"Перераспределено {redistributed} единиц собственности")

        # Резкий рост сознания
        for class_type in [conflict.oppressed_class]:
            if class_type in class_system.classes:
                class_system.classes[class_type].class_consciousness = 1.0

        # Политическая власть переходит к угнетённым
        if conflict.oppressed_class in class_system.classes:
            class_system.classes[conflict.oppressed_class].political_power = 1.0
        if conflict.ruling_class in class_system.classes:
            class_system.classes[conflict.ruling_class].political_power = 0.1

        events.append("Политическая власть перешла к угнетённым классам")
        return events

    def _apply_victory(
        self,
        conflict: ClassConflict,
        class_system: 'ClassSystem',
        ownership_system: Optional['OwnershipSystem']
    ) -> List[str]:
        """Применяет последствия победы"""
        events = ["Угнетённые одержали победу"]

        # Перераспределение собственности (30%)
        if ownership_system:
            redistributed = self._redistribute_property(
                ownership_system, 0.3
            )
            events.append(f"Перераспределено {redistributed} единиц собственности")

        return events

    def _apply_partial_victory(
        self,
        conflict: ClassConflict,
        class_system: 'ClassSystem'
    ) -> List[str]:
        """Применяет последствия частичной победы"""
        events = ["Достигнута частичная победа"]

        # Выполняем часть требований
        fulfilled = conflict.demands[:len(conflict.demands)//2]
        for demand in fulfilled:
            events.append(f"Выполнено требование: {demand}")

        return events

    def _apply_compromise(self, conflict: ClassConflict) -> List[str]:
        """Применяет последствия компромисса"""
        events = ["Достигнут компромисс"]

        # Выполняем минимальные уступки
        if conflict.demands:
            events.append(f"Частичное выполнение: {conflict.demands[0]}")

        return events

    def _apply_suppression(
        self,
        conflict: ClassConflict,
        class_system: 'ClassSystem'
    ) -> List[str]:
        """Применяет последствия подавления"""
        events = ["Восстание подавлено"]

        # Снижаем классовое сознание
        if conflict.oppressed_class in class_system.classes:
            class_system.classes[conflict.oppressed_class].class_consciousness *= 0.5
            events.append("Классовое сознание временно снижено")

        # Усиливаем власть правящего класса
        if conflict.ruling_class in class_system.classes:
            class_system.classes[conflict.ruling_class].political_power = min(
                1.0,
                class_system.classes[conflict.ruling_class].political_power + 0.2
            )

        return events

    def _redistribute_property(
        self,
        ownership_system: 'OwnershipSystem',
        fraction: float
    ) -> int:
        """
        Перераспределяет собственность.

        Возвращает количество перераспределённых единиц.
        """
        # Заглушка - реальная реализация зависит от OwnershipSystem
        return int(10 * fraction)


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
    - Классовое сознание
    """

    # Антагонистические пары классов
    ANTAGONIST_PAIRS = [
        (ClassType.LANDOWNER, ClassType.LANDLESS),
        (ClassType.LANDOWNER, ClassType.LABORER),
        (ClassType.CRAFTSMAN, ClassType.LABORER),
        (ClassType.CHIEF, ClassType.COMMUNAL_MEMBER),
    ]

    def __init__(self):
        # Классы
        self.classes: Dict[ClassType, SocialClass] = {}

        # NPC -> его класс
        self.npc_class: Dict[str, ClassType] = {}

        # Конфликты
        self.conflicts: List[ClassConflict] = []

        # Подсистемы
        self.consciousness_system = ClassConsciousnessSystem()
        self.resolution_system = ConflictResolutionSystem()

        # История
        self.class_emergence_history: List[Tuple[ClassType, int]] = []

        # Флаги развития
        self.classes_emerged: bool = False
        self.first_class_year: int = 0

        # Cooldown для конфликтов (предотвращает бесконечные восстания)
        self.conflict_cooldown: int = 0
        self.last_conflict_year: int = 0

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
        """
        Проверяет, не начался ли классовый конфликт.

        Условия для конфликта:
        1. Высокая напряжённость (>0.5)
        2. Наличие классового сознания (>0.3)
        3. Прошло время после предыдущего конфликта (cooldown)
        4. Есть антагонистические классы
        """
        # Проверяем cooldown
        if self.conflict_cooldown > 0:
            self.conflict_cooldown -= 1
            return None

        tension = self.check_class_tension()

        if tension < 0.4:
            return None

        # Проверяем каждую пару антагонистов
        for ruling_class, oppressed_class in self.ANTAGONIST_PAIRS:
            if ruling_class not in self.classes or oppressed_class not in self.classes:
                continue

            oppressed = self.classes[oppressed_class]

            # Проверяем уровень сознания
            if oppressed.class_consciousness < 0.2:
                continue

            # Вероятность конфликта
            conflict_probability = (
                tension * 0.5 +
                oppressed.class_consciousness * 0.3 +
                (0.2 if len(self.conflicts) == 0 else 0.0)  # Бонус за первый конфликт
            )

            # Случайная проверка
            if random.random() < conflict_probability:
                conflict = self._create_conflict(
                    oppressed_class, ruling_class, tension, year
                )
                self.conflicts.append(conflict)
                self.last_conflict_year = year
                return conflict

        return None

    def _create_conflict(
        self,
        oppressed_class: ClassType,
        ruling_class: ClassType,
        tension: float,
        year: int
    ) -> ClassConflict:
        """Создаёт новый классовый конфликт"""
        # Определяем тип конфликта по напряжённости
        if tension > 0.8:
            conflict_type = ConflictType.UPRISING
        elif tension > 0.6:
            conflict_type = ConflictType.RIOT
        elif tension > 0.4:
            conflict_type = ConflictType.LAND_DISPUTE
        else:
            conflict_type = ConflictType.STRIKE

        # Определяем причину
        causes = self._identify_grievances(oppressed_class, ruling_class)

        conflict = ClassConflict(
            id=f"conflict_{year}_{str(uuid4())[:8]}",
            conflict_type=conflict_type,
            oppressed_class=oppressed_class,
            ruling_class=ruling_class,
            intensity=tension,
            primary_cause=causes[0] if causes else "классовые противоречия",
            grievances=causes,
            year_started=year
        )

        # Добавляем участников
        if oppressed_class in self.classes:
            for npc_id in self.classes[oppressed_class].members:
                conflict.add_participant(npc_id, oppressed_class)

        if ruling_class in self.classes:
            for npc_id in self.classes[ruling_class].members:
                conflict.add_participant(npc_id, ruling_class)

        # Генерируем требования
        conflict.demands = self._generate_demands(oppressed_class, ruling_class)

        return conflict

    def _identify_grievances(
        self,
        oppressed_class: ClassType,
        ruling_class: ClassType
    ) -> List[str]:
        """Определяет жалобы угнетённого класса"""
        grievances = []

        if oppressed_class == ClassType.LANDLESS:
            grievances.append("неравенство в распределении земли")
            grievances.append("отсутствие средств к существованию")

        if oppressed_class == ClassType.LABORER:
            grievances.append("тяжёлые условия труда")
            grievances.append("низкая оплата труда")
            grievances.append("эксплуатация")

        if ruling_class == ClassType.LANDOWNER:
            grievances.append("накопление земли в руках немногих")

        # Добавляем общие жалобы по уровню неравенства
        if self.classes_emerged:
            grievances.append("растущее неравенство")

        return grievances

    def _generate_demands(
        self,
        oppressed_class: ClassType,
        ruling_class: ClassType
    ) -> List[str]:
        """Генерирует требования восставших"""
        demands = []

        if oppressed_class == ClassType.LANDLESS:
            demands.append("перераспределение земли")
            demands.append("доступ к общинным угодьям")

        if oppressed_class == ClassType.LABORER:
            demands.append("улучшение условий труда")
            demands.append("справедливая доля урожая")
            demands.append("право на отдых")

        demands.append("признание прав угнетённых")
        demands.append("ограничение власти богатых")

        return demands

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

    def update_conflicts(
        self,
        year: int,
        ownership_system: Optional['OwnershipSystem'] = None
    ) -> List[str]:
        """
        Обновляет все активные конфликты.

        Вызывается каждый день симуляции.
        """
        events = []

        for conflict in self.conflicts:
            if conflict.resolved:
                continue

            conflict.days_active += 1

            # Обновляем интенсивность на основе напряжённости
            tension = self.check_class_tension()

            if tension > conflict.intensity:
                # Эскалация
                if conflict.escalate(0.02):
                    events.append(
                        f"Конфликт '{conflict.conflict_type.russian_name}' "
                        f"перешёл в стадию: {conflict.stage.russian_name}"
                    )
                # Обновляем тип конфликта
                if conflict.update_conflict_type():
                    events.append(
                        f"Конфликт перерос в {conflict.conflict_type.russian_name}!"
                    )
            else:
                # Деэскалация
                conflict.de_escalate(0.01)

            # Проверяем разрешение
            if conflict.stage in [ConflictStage.CRISIS, ConflictStage.RESOLVING]:
                outcome = self.resolution_system.attempt_resolution(
                    conflict, self, ownership_system, year
                )
                if outcome:
                    resolution_events = self.resolution_system.apply_outcome(
                        conflict, outcome, self, ownership_system, year
                    )
                    events.extend(resolution_events)

                    # Устанавливаем cooldown после разрешения
                    self.conflict_cooldown = 30  # дней

            # Обновляем потери производства
            if conflict.stage in [ConflictStage.ACTIVE, ConflictStage.ESCALATING,
                                   ConflictStage.CRISIS]:
                conflict.production_loss = min(
                    0.5,
                    conflict.production_loss + 0.01
                )

        return events

    def spread_consciousness(
        self,
        npc_id: str,
        target_npc_id: str,
        belief_system: Optional['BeliefSystem'] = None,
        relationship_strength: float = 0.5
    ) -> bool:
        """
        Распространяет классовое сознание между NPC.

        Возвращает True, если распространение произошло.
        """
        event = self.consciousness_system.spread_consciousness(
            npc_id,
            target_npc_id,
            self,
            belief_system,
            relationship_strength
        )

        if event:
            # Применяем изменение сознания
            if event.class_type in self.classes:
                self.classes[event.class_type].class_consciousness = min(
                    1.0,
                    self.classes[event.class_type].class_consciousness + event.amount
                )
            return True

        return False

    def apply_crisis_effect(self, crisis_severity: float) -> float:
        """
        Применяет эффект кризиса на классовое сознание.

        Кризисы (голод, катаклизмы) разрушают ложное сознание.
        """
        return self.consciousness_system.crisis_effect(self, crisis_severity)

    def get_active_conflicts(self) -> List[ClassConflict]:
        """Возвращает активные конфликты"""
        return [c for c in self.conflicts if not c.resolved]

    def get_conflict_summary(self) -> str:
        """Возвращает сводку по конфликтам"""
        active = self.get_active_conflicts()
        if not active:
            return "Нет активных конфликтов"

        summaries = [c.get_summary() for c in active]
        return "; ".join(summaries)

    def get_consciousness_phase(self, class_type: ClassType) -> ConsciousnessPhase:
        """Возвращает фазу классового сознания"""
        if class_type not in self.classes:
            return ConsciousnessPhase.NONE

        level = self.classes[class_type].class_consciousness
        return ConsciousnessPhase.from_level(level)

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику классов"""
        active_conflicts = self.get_active_conflicts()

        # Сознание эксплуатируемых классов
        consciousness_info = {}
        for class_type in [ClassType.LANDLESS, ClassType.LABORER]:
            if class_type in self.classes:
                phase = self.get_consciousness_phase(class_type)
                consciousness_info[class_type.russian_name] = {
                    "level": round(self.classes[class_type].class_consciousness, 2),
                    "phase": phase.russian_name
                }

        return {
            "classes_emerged": self.classes_emerged,
            "first_class_year": self.first_class_year,
            "class_distribution": self.get_class_distribution(),
            "class_tension": round(self.check_class_tension(), 2),
            "active_conflicts": len(active_conflicts),
            "conflict_summary": self.get_conflict_summary(),
            "total_conflicts": len(self.conflicts),
            "resolved_conflicts": len(self.conflicts) - len(active_conflicts),
            "consciousness": consciousness_info,
            "organic_intellectuals": len(self.consciousness_system.organic_intellectuals),
            "dominant_class": (
                self.get_dominant_class().russian_name
                if self.get_dominant_class() else "нет"
            ),
        }
