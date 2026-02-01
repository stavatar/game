"""
Система диалектических противоречий в симуляции.

По Марксу, развитие общества происходит через разрешение
диалектических противоречий. Главное противоречие:

ПРОИЗВОДИТЕЛЬНЫЕ СИЛЫ vs ПРОИЗВОДСТВЕННЫЕ ОТНОШЕНИЯ

Когда производительные силы (технологии, труд, средства производства)
перерастают производственные отношения (формы собственности, классы),
возникает кризис, ведущий к социальной трансформации.

Этот модуль отслеживает:
1. Основные диалектические противоречия
2. Их интенсивность и развитие
3. Моменты качественного скачка (революционной ситуации)

По спецификации INT-019: обнаружение диалектических противоречий.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple, TYPE_CHECKING
from enum import Enum, auto
from datetime import datetime
import math

if TYPE_CHECKING:
    from .simulation import Simulation


class ContradictionType(Enum):
    """
    Типы диалектических противоречий.

    По Марксу, общество развивается через разрешение
    противоречий между противоположными тенденциями.
    """
    FORCES_VS_RELATIONS = (
        "производительные силы vs производственные отношения",
        "Главное противоречие: технологии перерастают формы собственности"
    )
    LABOR_VS_CAPITAL = (
        "труд vs капитал",
        "Противоречие между интересами работников и собственников"
    )
    SOCIAL_VS_PRIVATE = (
        "общественное vs частное",
        "Противоречие между общественным характером производства и частным присвоением"
    )
    IDEOLOGY_VS_REALITY = (
        "идеология vs реальность",
        "Противоречие между господствующими идеями и материальными условиями"
    )
    ACCUMULATION_VS_CONSUMPTION = (
        "накопление vs потребление",
        "Противоречие между накоплением богатства и потребностями общества"
    )
    TRADITION_VS_PROGRESS = (
        "традиция vs прогресс",
        "Противоречие между устоявшимися практиками и новыми возможностями"
    )

    def __init__(self, russian_name: str, description: str):
        self.russian_name = russian_name
        self.description = description


class ContradictionPhase(Enum):
    """
    Фазы развития противоречия.

    По диалектике: накопление количественных изменений
    ведёт к качественному скачку.
    """
    LATENT = ("латентное", 0.0, 0.2, "Противоречие существует, но не проявляется")
    EMERGING = ("зарождающееся", 0.2, 0.4, "Противоречие начинает проявляться")
    DEVELOPING = ("развивающееся", 0.4, 0.6, "Противоречие нарастает")
    ACUTE = ("обострённое", 0.6, 0.8, "Противоречие достигает высокой интенсивности")
    CRITICAL = ("критическое", 0.8, 1.0, "Противоречие требует разрешения")

    def __init__(self, russian_name: str, min_intensity: float,
                 max_intensity: float, description: str):
        self.russian_name = russian_name
        self.min_intensity = min_intensity
        self.max_intensity = max_intensity
        self.description = description

    @classmethod
    def from_intensity(cls, intensity: float) -> 'ContradictionPhase':
        """Определяет фазу по интенсивности противоречия"""
        for phase in cls:
            if phase.min_intensity <= intensity < phase.max_intensity:
                return phase
        return cls.CRITICAL if intensity >= 0.8 else cls.LATENT


class ResolutionType(Enum):
    """
    Типы разрешения противоречия.

    Диалектическое противоречие может быть разрешено:
    - Синтезом (качественно новая форма)
    - Победой одной стороны
    - Временным компромиссом
    - Внешним вмешательством
    """
    SYNTHESIS = ("синтез", "Качественно новая форма, снимающая противоречие")
    DOMINANT_VICTORY = ("победа господствующей стороны", "Укрепление существующего порядка")
    SUBORDINATE_VICTORY = ("победа подчинённой стороны", "Революционное преобразование")
    COMPROMISE = ("компромисс", "Временное ослабление без полного разрешения")
    TRANSFORMATION = ("трансформация", "Переход в новый тип противоречия")
    EXTERNAL = ("внешнее разрешение", "Разрешение через внешние факторы")

    def __init__(self, russian_name: str, description: str):
        self.russian_name = russian_name
        self.description = description


@dataclass
class Contradiction:
    """
    Диалектическое противоречие.

    Представляет конкретное противоречие в обществе,
    отслеживая его развитие и возможное разрешение.
    """
    contradiction_type: ContradictionType
    year_emerged: int

    # Стороны противоречия
    thesis: str = ""           # Первая сторона (тезис)
    antithesis: str = ""       # Вторая сторона (антитезис)

    # Состояние противоречия
    intensity: float = 0.0     # 0-1, сила противоречия
    stability: float = 0.5     # 0-1, насколько устойчиво (0 = нестабильно)
    visibility: float = 0.0    # 0-1, насколько осознано участниками

    # Факторы, влияющие на противоречие
    driving_factors: List[str] = field(default_factory=list)
    restraining_factors: List[str] = field(default_factory=list)

    # История развития
    intensity_history: List[Tuple[int, float]] = field(default_factory=list)

    # Разрешение
    resolved: bool = False
    resolution_type: Optional[ResolutionType] = None
    resolution_year: Optional[int] = None
    synthesis: str = ""        # Описание синтеза при разрешении

    # Метаданные
    id: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"contradiction_{self.contradiction_type.name}_{self.year_emerged}"
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def phase(self) -> ContradictionPhase:
        """Текущая фаза противоречия"""
        return ContradictionPhase.from_intensity(self.intensity)

    def update_intensity(self, new_intensity: float, year: int) -> bool:
        """
        Обновляет интенсивность противоречия.

        Возвращает True, если произошёл переход в новую фазу.
        """
        old_phase = self.phase
        self.intensity = max(0.0, min(1.0, new_intensity))
        self.intensity_history.append((year, self.intensity))
        return self.phase != old_phase

    def add_driving_factor(self, factor: str) -> None:
        """Добавляет фактор, усиливающий противоречие"""
        if factor not in self.driving_factors:
            self.driving_factors.append(factor)

    def add_restraining_factor(self, factor: str) -> None:
        """Добавляет фактор, сдерживающий противоречие"""
        if factor not in self.restraining_factors:
            self.restraining_factors.append(factor)

    def resolve(self, resolution_type: ResolutionType, year: int,
                synthesis: str = "") -> None:
        """Разрешает противоречие"""
        self.resolved = True
        self.resolution_type = resolution_type
        self.resolution_year = year
        self.synthesis = synthesis

    def get_summary(self) -> str:
        """Возвращает краткое описание противоречия"""
        status = "разрешено" if self.resolved else self.phase.russian_name
        return (
            f"{self.contradiction_type.russian_name}: "
            f"{status} (интенсивность: {self.intensity:.0%})"
        )


@dataclass
class ContradictionEvent:
    """
    Событие, связанное с противоречием.

    Фиксирует моменты изменения состояния противоречия.
    """
    contradiction_id: str
    contradiction_type: ContradictionType
    event_description: str
    year: int

    # Тип события
    is_phase_change: bool = False
    is_resolution: bool = False
    is_emergence: bool = False

    # Контекст
    old_phase: Optional[ContradictionPhase] = None
    new_phase: Optional[ContradictionPhase] = None
    intensity: float = 0.0

    # Метаданные
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def get_summary(self) -> str:
        """Возвращает краткое описание события"""
        return f"Год {self.year}: {self.event_description}"


@dataclass
class ContradictionMetrics:
    """
    Метрики противоречий в системе.

    Агрегированные показатели состояния диалектических
    противоречий в обществе.
    """
    # Основные метрики
    total_contradictions: int = 0
    active_contradictions: int = 0
    resolved_contradictions: int = 0

    # Интенсивность
    avg_intensity: float = 0.0
    max_intensity: float = 0.0
    critical_count: int = 0     # Количество критических противоречий

    # Главное противоречие
    primary_contradiction_type: Optional[ContradictionType] = None
    primary_intensity: float = 0.0

    # Индекс революционной ситуации
    # (когда верхи не могут, а низы не хотят жить по-старому)
    revolutionary_potential: float = 0.0

    # Стабильность системы (обратно пропорциональна интенсивности противоречий)
    system_stability: float = 1.0

    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку метрик"""
        return {
            "total": self.total_contradictions,
            "active": self.active_contradictions,
            "resolved": self.resolved_contradictions,
            "avg_intensity": round(self.avg_intensity, 2),
            "max_intensity": round(self.max_intensity, 2),
            "critical_count": self.critical_count,
            "primary_contradiction": (
                self.primary_contradiction_type.russian_name
                if self.primary_contradiction_type else "нет"
            ),
            "revolutionary_potential": round(self.revolutionary_potential, 2),
            "system_stability": round(self.system_stability, 2),
        }


class ContradictionDetector:
    """
    Детектор диалектических противоречий.

    Отслеживает и анализирует противоречия в обществе:
    1. Обнаруживает возникновение противоречий
    2. Измеряет их интенсивность
    3. Прогнозирует развитие
    4. Регистрирует разрешение

    Использование:
        detector = ContradictionDetector()
        events = detector.update(simulation)  # Обновляет состояние
        metrics = detector.get_metrics()       # Получает метрики
        report = detector.get_report()         # Получает текстовый отчёт
    """

    # Пороговые значения для обнаружения противоречий
    TECH_PROPERTY_THRESHOLD = 0.3    # Разрыв технологий и собственности
    EXPLOITATION_THRESHOLD = 0.4     # Порог эксплуатации для труд vs капитал
    CONSCIOUSNESS_THRESHOLD = 0.3    # Порог сознания для идеология vs реальность
    INEQUALITY_THRESHOLD = 0.4       # Порог неравенства для соц. vs частное

    def __init__(self):
        # Активные противоречия
        self.contradictions: Dict[str, Contradiction] = {}

        # История событий
        self.events: List[ContradictionEvent] = []

        # Метрики
        self.metrics = ContradictionMetrics()

        # Последние вычисленные показатели (для отслеживания динамики)
        self._last_update_year: int = 0
        self._previous_metrics: Optional[ContradictionMetrics] = None

    def update(self, simulation: 'Simulation') -> List[ContradictionEvent]:
        """
        Обновляет состояние противоречий на основе данных симуляции.

        Выполняет:
        1. Проверку возникновения новых противоречий
        2. Обновление интенсивности существующих
        3. Проверку разрешения противоречий
        4. Обновление агрегированных метрик

        Args:
            simulation: Объект симуляции для анализа

        Returns:
            Список новых событий
        """
        current_year = simulation.year
        new_events = []

        # Сохраняем предыдущие метрики
        if self._last_update_year < current_year:
            self._previous_metrics = ContradictionMetrics(
                avg_intensity=self.metrics.avg_intensity,
                revolutionary_potential=self.metrics.revolutionary_potential,
            )
            self._last_update_year = current_year

        # Проверяем возникновение и обновление каждого типа противоречия
        new_events.extend(self._check_forces_vs_relations(simulation))
        new_events.extend(self._check_labor_vs_capital(simulation))
        new_events.extend(self._check_social_vs_private(simulation))
        new_events.extend(self._check_ideology_vs_reality(simulation))
        new_events.extend(self._check_accumulation_vs_consumption(simulation))
        new_events.extend(self._check_tradition_vs_progress(simulation))

        # Проверяем разрешение противоречий
        new_events.extend(self._check_resolutions(simulation))

        # Обновляем агрегированные метрики
        self._update_metrics(simulation)

        return new_events

    def _check_forces_vs_relations(self, simulation: 'Simulation') -> List[ContradictionEvent]:
        """
        Проверяет противоречие: Производительные силы vs Производственные отношения.

        Главное противоречие по Марксу. Возникает когда:
        - Технологический уровень высок
        - Но формы собственности отстают (нет или примитивная частная собственность)
        - Или классовая структура не соответствует производительным силам

        Интенсивность зависит от разрыва между:
        - Уровнем технологий (количество и качество)
        - Развитостью производственных отношений (собственность, классы)
        """
        events = []
        year = simulation.year
        c_type = ContradictionType.FORCES_VS_RELATIONS
        c_id = f"contradiction_{c_type.name}"

        # Вычисляем уровень производительных сил
        # (технологии, навыки, средства производства)
        tech_stats = simulation.knowledge.get_statistics()
        tech_count = tech_stats.get("discovered", 0)
        tech_level = min(1.0, tech_count / 20)  # Нормализуем (20 технологий = 100%)

        # Добавляем уровень навыков населения
        skill_sum = 0
        skill_count = 0
        for npc in simulation.npcs.values():
            if npc.is_alive:
                skill_sum += npc.get_skill("gathering") + npc.get_skill("crafting")
                skill_count += 1
        avg_skill = skill_sum / (skill_count * 2) if skill_count > 0 else 0
        skill_level = avg_skill / 100  # Нормализуем (100 = максимум)

        productive_forces = (tech_level * 0.7 + skill_level * 0.3)

        # Вычисляем развитость производственных отношений
        # (собственность, классы, разделение труда)
        property_development = 0.0
        if simulation.ownership.private_property_emerged:
            property_development = 0.5
            # Дополнительно за развитость классов
            if simulation.classes.classes_emerged:
                property_development += 0.3
                # За разнообразие классов
                class_count = len([c for c in simulation.classes.classes.values()
                                   if c.get_size() > 0])
                property_development += min(0.2, class_count * 0.05)

        production_relations = property_development

        # Вычисляем разрыв (противоречие)
        # Противоречие возникает, когда силы опережают отношения
        gap = max(0.0, productive_forces - production_relations)

        # Порог для возникновения противоречия
        if gap > self.TECH_PROPERTY_THRESHOLD:
            if c_id not in self.contradictions:
                # Создаём новое противоречие
                contradiction = Contradiction(
                    contradiction_type=c_type,
                    year_emerged=year,
                    thesis="производительные силы (технологии, труд)",
                    antithesis="производственные отношения (собственность)",
                    intensity=gap,
                )
                contradiction.add_driving_factor("технологический прогресс")
                contradiction.add_restraining_factor("инерция социальных отношений")

                self.contradictions[c_id] = contradiction
                event = ContradictionEvent(
                    contradiction_id=c_id,
                    contradiction_type=c_type,
                    event_description=(
                        f"Возникло главное диалектическое противоречие: "
                        f"производительные силы ({productive_forces:.0%}) опережают "
                        f"производственные отношения ({production_relations:.0%})"
                    ),
                    year=year,
                    is_emergence=True,
                    intensity=gap,
                )
                self.events.append(event)
                events.append(event)
            else:
                # Обновляем существующее
                contradiction = self.contradictions[c_id]
                old_phase = contradiction.phase
                phase_changed = contradiction.update_intensity(gap, year)

                if phase_changed:
                    event = ContradictionEvent(
                        contradiction_id=c_id,
                        contradiction_type=c_type,
                        event_description=(
                            f"Противоречие производительных сил и отношений "
                            f"перешло в фазу: {contradiction.phase.russian_name}"
                        ),
                        year=year,
                        is_phase_change=True,
                        old_phase=old_phase,
                        new_phase=contradiction.phase,
                        intensity=gap,
                    )
                    self.events.append(event)
                    events.append(event)

                # Обновляем факторы
                if tech_count > 10:
                    contradiction.add_driving_factor("накопление технологий")
                if not simulation.classes.classes_emerged:
                    contradiction.add_driving_factor("отсутствие классовой структуры")

        return events

    def _check_labor_vs_capital(self, simulation: 'Simulation') -> List[ContradictionEvent]:
        """
        Проверяет противоречие: Труд vs Капитал.

        Возникает когда существуют классы эксплуататоров и эксплуатируемых.
        Интенсивность зависит от:
        - Нормы эксплуатации (разрыв в богатстве)
        - Классового сознания угнетённых
        - Соотношения численности классов
        """
        events = []
        year = simulation.year
        c_type = ContradictionType.LABOR_VS_CAPITAL
        c_id = f"contradiction_{c_type.name}"

        # Проверяем наличие классов
        if not simulation.classes.classes_emerged:
            return events

        # Вычисляем интенсивность
        # Норма эксплуатации
        economic_conditions = simulation._get_economic_conditions()
        exploitation_rate = economic_conditions.get("exploitation_rate", 0.0)

        # Классовое сознание угнетённых
        consciousness_sum = 0.0
        consciousness_count = 0
        for class_type, social_class in simulation.classes.classes.items():
            if class_type.is_exploited and social_class.get_size() > 0:
                consciousness_sum += social_class.class_consciousness
                consciousness_count += 1
        avg_consciousness = (consciousness_sum / consciousness_count
                             if consciousness_count > 0 else 0.0)

        # Классовое напряжение
        class_tension = simulation.classes.check_class_tension()

        # Интегральная интенсивность противоречия
        intensity = (
            exploitation_rate * 0.4 +
            avg_consciousness * 0.3 +
            class_tension * 0.3
        )

        if intensity > self.EXPLOITATION_THRESHOLD:
            if c_id not in self.contradictions:
                contradiction = Contradiction(
                    contradiction_type=c_type,
                    year_emerged=year,
                    thesis="труд (работники, эксплуатируемые)",
                    antithesis="капитал (собственники, эксплуататоры)",
                    intensity=intensity,
                )
                contradiction.add_driving_factor("эксплуатация труда")
                if avg_consciousness > 0.2:
                    contradiction.add_driving_factor("рост классового сознания")

                self.contradictions[c_id] = contradiction
                event = ContradictionEvent(
                    contradiction_id=c_id,
                    contradiction_type=c_type,
                    event_description=(
                        f"Возникло противоречие труда и капитала: "
                        f"эксплуатация {exploitation_rate:.0%}, "
                        f"сознание {avg_consciousness:.0%}"
                    ),
                    year=year,
                    is_emergence=True,
                    intensity=intensity,
                )
                self.events.append(event)
                events.append(event)
            else:
                contradiction = self.contradictions[c_id]
                old_phase = contradiction.phase
                phase_changed = contradiction.update_intensity(intensity, year)

                if phase_changed:
                    event = ContradictionEvent(
                        contradiction_id=c_id,
                        contradiction_type=c_type,
                        event_description=(
                            f"Противоречие труда и капитала "
                            f"перешло в фазу: {contradiction.phase.russian_name}"
                        ),
                        year=year,
                        is_phase_change=True,
                        old_phase=old_phase,
                        new_phase=contradiction.phase,
                        intensity=intensity,
                    )
                    self.events.append(event)
                    events.append(event)

        return events

    def _check_social_vs_private(self, simulation: 'Simulation') -> List[ContradictionEvent]:
        """
        Проверяет противоречие: Общественное vs Частное.

        Возникает когда производство становится общественным (зависит от многих),
        но присвоение остаётся частным (выгода идёт немногим).

        Интенсивность зависит от:
        - Неравенства в распределении
        - Доли частной собственности
        - Социальной зависимости производства
        """
        events = []
        year = simulation.year
        c_type = ContradictionType.SOCIAL_VS_PRIVATE
        c_id = f"contradiction_{c_type.name}"

        # Проверяем наличие частной собственности
        if not simulation.ownership.private_property_emerged:
            return events

        # Неравенство
        inequality = simulation.ownership.calculate_inequality()

        # Доля частной собственности
        from ..economy.property import PropertyType
        total_property = len(simulation.ownership.properties)
        private_property = sum(
            1 for p in simulation.ownership.properties.values()
            if p.owner_type == PropertyType.PRIVATE
        )
        private_share = private_property / total_property if total_property > 0 else 0.0

        # Социальная зависимость (много ли людей участвует в производстве)
        workers = sum(1 for n in simulation.npcs.values() if n.is_alive and n.can_work())
        total_alive = sum(1 for n in simulation.npcs.values() if n.is_alive)
        social_dependency = workers / total_alive if total_alive > 0 else 0.0

        # Интенсивность: частная собственность высока, неравенство высоко,
        # но все зависят от общественного производства
        intensity = (
            inequality * 0.4 +
            private_share * 0.3 +
            (social_dependency * inequality) * 0.3
        )

        if intensity > self.INEQUALITY_THRESHOLD:
            if c_id not in self.contradictions:
                contradiction = Contradiction(
                    contradiction_type=c_type,
                    year_emerged=year,
                    thesis="общественный характер производства",
                    antithesis="частное присвоение результатов",
                    intensity=intensity,
                )
                contradiction.add_driving_factor("рост неравенства")
                contradiction.add_driving_factor("зависимость от общего производства")

                self.contradictions[c_id] = contradiction
                event = ContradictionEvent(
                    contradiction_id=c_id,
                    contradiction_type=c_type,
                    event_description=(
                        f"Возникло противоречие общественного и частного: "
                        f"неравенство {inequality:.0%}, "
                        f"частная собственность {private_share:.0%}"
                    ),
                    year=year,
                    is_emergence=True,
                    intensity=intensity,
                )
                self.events.append(event)
                events.append(event)
            else:
                contradiction = self.contradictions[c_id]
                old_phase = contradiction.phase
                phase_changed = contradiction.update_intensity(intensity, year)

                if phase_changed:
                    event = ContradictionEvent(
                        contradiction_id=c_id,
                        contradiction_type=c_type,
                        event_description=(
                            f"Противоречие общественного и частного "
                            f"перешло в фазу: {contradiction.phase.russian_name}"
                        ),
                        year=year,
                        is_phase_change=True,
                        old_phase=old_phase,
                        new_phase=contradiction.phase,
                        intensity=intensity,
                    )
                    self.events.append(event)
                    events.append(event)

        return events

    def _check_ideology_vs_reality(self, simulation: 'Simulation') -> List[ContradictionEvent]:
        """
        Проверяет противоречие: Идеология vs Реальность.

        Возникает когда господствующая идеология не соответствует
        материальным условиям жизни большинства.

        Интенсивность зависит от:
        - Разрыва между идеологией и классовым положением
        - Уровня классового сознания (осознания этого разрыва)
        - Распространённости доминирующей идеологии среди угнетённых
        """
        events = []
        year = simulation.year
        c_type = ContradictionType.IDEOLOGY_VS_REALITY
        c_id = f"contradiction_{c_type.name}"

        # Проверяем наличие доминирующей идеологии
        if not simulation.beliefs.dominant_beliefs:
            return events

        # Проверяем наличие классов
        if not simulation.classes.classes_emerged:
            return events

        # Считаем долю угнетённых, принявших доминирующую идеологию
        exploited_with_dominant = 0
        total_exploited = 0

        for class_type, social_class in simulation.classes.classes.items():
            if class_type.is_exploited:
                for member_id in social_class.members:
                    total_exploited += 1
                    npc_beliefs = simulation.beliefs.npc_beliefs.get(member_id, set())
                    if any(b in npc_beliefs for b in simulation.beliefs.dominant_beliefs):
                        exploited_with_dominant += 1

        if total_exploited == 0:
            return events

        ideology_penetration = exploited_with_dominant / total_exploited

        # Классовое сознание угнетённых (осознание разрыва)
        avg_consciousness = 0.0
        consciousness_count = 0
        for class_type, social_class in simulation.classes.classes.items():
            if class_type.is_exploited and social_class.get_size() > 0:
                avg_consciousness += social_class.class_consciousness
                consciousness_count += 1
        if consciousness_count > 0:
            avg_consciousness /= consciousness_count

        # Интенсивность: высокое проникновение идеологии + рост сознания = противоречие
        # Парадокс: идеология навязана, но сознание растёт
        intensity = ideology_penetration * avg_consciousness * 2

        if intensity > self.CONSCIOUSNESS_THRESHOLD:
            if c_id not in self.contradictions:
                contradiction = Contradiction(
                    contradiction_type=c_type,
                    year_emerged=year,
                    thesis="господствующая идеология",
                    antithesis="материальные условия жизни угнетённых",
                    intensity=intensity,
                    visibility=avg_consciousness,  # Видимость = осознанность
                )
                contradiction.add_driving_factor("ложное сознание угнетённых")
                contradiction.add_driving_factor("рост классового сознания")

                self.contradictions[c_id] = contradiction
                event = ContradictionEvent(
                    contradiction_id=c_id,
                    contradiction_type=c_type,
                    event_description=(
                        f"Возникло противоречие идеологии и реальности: "
                        f"проникновение идеологии {ideology_penetration:.0%}, "
                        f"сознание {avg_consciousness:.0%}"
                    ),
                    year=year,
                    is_emergence=True,
                    intensity=intensity,
                )
                self.events.append(event)
                events.append(event)
            else:
                contradiction = self.contradictions[c_id]
                old_phase = contradiction.phase
                phase_changed = contradiction.update_intensity(intensity, year)
                contradiction.visibility = avg_consciousness

                if phase_changed:
                    event = ContradictionEvent(
                        contradiction_id=c_id,
                        contradiction_type=c_type,
                        event_description=(
                            f"Противоречие идеологии и реальности "
                            f"перешло в фазу: {contradiction.phase.russian_name}"
                        ),
                        year=year,
                        is_phase_change=True,
                        old_phase=old_phase,
                        new_phase=contradiction.phase,
                        intensity=intensity,
                    )
                    self.events.append(event)
                    events.append(event)

        return events

    def _check_accumulation_vs_consumption(self, simulation: 'Simulation') -> List[ContradictionEvent]:
        """
        Проверяет противоречие: Накопление vs Потребление.

        Возникает когда богатство накапливается у немногих,
        а большинство испытывает нужду.

        Интенсивность зависит от:
        - Концентрации богатства
        - Уровня удовлетворения базовых потребностей
        - Разницы в качестве жизни
        """
        events = []
        year = simulation.year
        c_type = ContradictionType.ACCUMULATION_VS_CONSUMPTION
        c_id = f"contradiction_{c_type.name}"

        # Вычисляем концентрацию богатства
        wealth_data = []
        hunger_levels = []

        for npc in simulation.npcs.values():
            if npc.is_alive:
                # Богатство = инвентарь + собственность
                wealth = npc.inventory.total_value()
                props = simulation.ownership.get_owner_properties(npc.id)
                wealth += len(props) * 10 if props else 0
                wealth_data.append(wealth)

                # Уровень голода (нужды)
                hunger_levels.append(npc.hunger)

        if not wealth_data or len(wealth_data) < 2:
            return events

        # Концентрация богатства (топ 20% vs остальные)
        sorted_wealth = sorted(wealth_data, reverse=True)
        top_20_count = max(1, len(sorted_wealth) // 5)
        top_20_wealth = sum(sorted_wealth[:top_20_count])
        total_wealth = sum(sorted_wealth)
        concentration = top_20_wealth / total_wealth if total_wealth > 0 else 0

        # Средний уровень голода
        avg_hunger = sum(hunger_levels) / len(hunger_levels)
        hunger_factor = avg_hunger / 100  # Нормализуем

        # Интенсивность: высокая концентрация + высокий голод
        intensity = concentration * 0.6 + hunger_factor * 0.4

        # Порог зависит от голода
        threshold = 0.3 if avg_hunger > 30 else 0.5

        if intensity > threshold:
            if c_id not in self.contradictions:
                contradiction = Contradiction(
                    contradiction_type=c_type,
                    year_emerged=year,
                    thesis="накопление богатства",
                    antithesis="потребности общества",
                    intensity=intensity,
                )
                if concentration > 0.5:
                    contradiction.add_driving_factor("концентрация богатства")
                if avg_hunger > 30:
                    contradiction.add_driving_factor("массовый голод")

                self.contradictions[c_id] = contradiction
                event = ContradictionEvent(
                    contradiction_id=c_id,
                    contradiction_type=c_type,
                    event_description=(
                        f"Возникло противоречие накопления и потребления: "
                        f"концентрация {concentration:.0%}, "
                        f"голод {avg_hunger:.0f}%"
                    ),
                    year=year,
                    is_emergence=True,
                    intensity=intensity,
                )
                self.events.append(event)
                events.append(event)
            else:
                contradiction = self.contradictions[c_id]
                old_phase = contradiction.phase
                phase_changed = contradiction.update_intensity(intensity, year)

                if phase_changed:
                    event = ContradictionEvent(
                        contradiction_id=c_id,
                        contradiction_type=c_type,
                        event_description=(
                            f"Противоречие накопления и потребления "
                            f"перешло в фазу: {contradiction.phase.russian_name}"
                        ),
                        year=year,
                        is_phase_change=True,
                        old_phase=old_phase,
                        new_phase=contradiction.phase,
                        intensity=intensity,
                    )
                    self.events.append(event)
                    events.append(event)

        return events

    def _check_tradition_vs_progress(self, simulation: 'Simulation') -> List[ContradictionEvent]:
        """
        Проверяет противоречие: Традиция vs Прогресс.

        Возникает когда новые технологии и практики вступают
        в противоречие с устоявшимися традициями и нормами.

        Интенсивность зависит от:
        - Скорости технологического прогресса
        - Силы традиционных норм
        - Разрыва между новыми возможностями и старыми практиками
        """
        events = []
        year = simulation.year
        c_type = ContradictionType.TRADITION_VS_PROGRESS
        c_id = f"contradiction_{c_type.name}"

        # Уровень технологического прогресса
        tech_stats = simulation.knowledge.get_statistics()
        tech_count = tech_stats.get("discovered", 0)

        # Количество традиций и норм
        tradition_count = len(simulation.traditions.traditions)
        norm_count = len(simulation.norms.norms)

        # Скорость прогресса (технологии / год)
        progress_rate = tech_count / year if year > 0 else 0

        # Сила традиций (нормализованная)
        tradition_strength = min(1.0, (tradition_count + norm_count) / 10)

        # Разрыв возникает когда прогресс быстрый, а традиции сильные
        if progress_rate > 0.5 and tradition_strength > 0.3:
            intensity = min(1.0, progress_rate * tradition_strength)

            if c_id not in self.contradictions:
                contradiction = Contradiction(
                    contradiction_type=c_type,
                    year_emerged=year,
                    thesis="прогресс (новые технологии и практики)",
                    antithesis="традиция (устоявшиеся нормы и обычаи)",
                    intensity=intensity,
                )
                contradiction.add_driving_factor("технологический прогресс")
                contradiction.add_restraining_factor("традиционные нормы")

                self.contradictions[c_id] = contradiction
                event = ContradictionEvent(
                    contradiction_id=c_id,
                    contradiction_type=c_type,
                    event_description=(
                        f"Возникло противоречие традиции и прогресса: "
                        f"прогресс {progress_rate:.2f}/год, "
                        f"традиции {tradition_strength:.0%}"
                    ),
                    year=year,
                    is_emergence=True,
                    intensity=intensity,
                )
                self.events.append(event)
                events.append(event)
            else:
                contradiction = self.contradictions[c_id]
                old_phase = contradiction.phase
                phase_changed = contradiction.update_intensity(intensity, year)

                if phase_changed:
                    event = ContradictionEvent(
                        contradiction_id=c_id,
                        contradiction_type=c_type,
                        event_description=(
                            f"Противоречие традиции и прогресса "
                            f"перешло в фазу: {contradiction.phase.russian_name}"
                        ),
                        year=year,
                        is_phase_change=True,
                        old_phase=old_phase,
                        new_phase=contradiction.phase,
                        intensity=intensity,
                    )
                    self.events.append(event)
                    events.append(event)

        return events

    def _check_resolutions(self, simulation: 'Simulation') -> List[ContradictionEvent]:
        """
        Проверяет разрешение противоречий.

        Противоречие может быть разрешено:
        - Революцией (победа угнетённых)
        - Реформой (компромисс)
        - Подавлением (победа господствующих)
        - Трансформацией (переход в новую форму)
        """
        events = []
        year = simulation.year

        for c_id, contradiction in list(self.contradictions.items()):
            if contradiction.resolved:
                continue

            # Проверяем условия разрешения

            # 1. Революция (классовый конфликт с победой угнетённых)
            if contradiction.contradiction_type == ContradictionType.LABOR_VS_CAPITAL:
                for conflict in simulation.classes.conflicts:
                    if conflict.resolved and conflict.outcome:
                        from ..society.classes import ConflictOutcome
                        if conflict.outcome in [ConflictOutcome.REVOLUTION,
                                                ConflictOutcome.VICTORY]:
                            contradiction.resolve(
                                ResolutionType.SUBORDINATE_VICTORY,
                                year,
                                synthesis="новые производственные отношения"
                            )
                            event = ContradictionEvent(
                                contradiction_id=c_id,
                                contradiction_type=contradiction.contradiction_type,
                                event_description=(
                                    f"Противоречие труда и капитала разрешено "
                                    f"через {contradiction.resolution_type.russian_name}"
                                ),
                                year=year,
                                is_resolution=True,
                                intensity=contradiction.intensity,
                            )
                            self.events.append(event)
                            events.append(event)
                            break

            # 2. Снижение интенсивности ниже порога = временное разрешение
            if contradiction.intensity < 0.1:
                contradiction.resolve(
                    ResolutionType.COMPROMISE,
                    year,
                    synthesis="временное ослабление противоречия"
                )
                event = ContradictionEvent(
                    contradiction_id=c_id,
                    contradiction_type=contradiction.contradiction_type,
                    event_description=(
                        f"Противоречие '{contradiction.contradiction_type.russian_name}' "
                        f"временно ослабло"
                    ),
                    year=year,
                    is_resolution=True,
                    intensity=contradiction.intensity,
                )
                self.events.append(event)
                events.append(event)

        return events

    def _update_metrics(self, simulation: 'Simulation') -> None:
        """Обновляет агрегированные метрики противоречий"""
        active = [c for c in self.contradictions.values() if not c.resolved]
        resolved = [c for c in self.contradictions.values() if c.resolved]

        self.metrics.total_contradictions = len(self.contradictions)
        self.metrics.active_contradictions = len(active)
        self.metrics.resolved_contradictions = len(resolved)

        if active:
            intensities = [c.intensity for c in active]
            self.metrics.avg_intensity = sum(intensities) / len(intensities)
            self.metrics.max_intensity = max(intensities)
            self.metrics.critical_count = sum(
                1 for c in active if c.phase == ContradictionPhase.CRITICAL
            )

            # Главное противоречие = с максимальной интенсивностью
            primary = max(active, key=lambda c: c.intensity)
            self.metrics.primary_contradiction_type = primary.contradiction_type
            self.metrics.primary_intensity = primary.intensity
        else:
            self.metrics.avg_intensity = 0.0
            self.metrics.max_intensity = 0.0
            self.metrics.critical_count = 0
            self.metrics.primary_contradiction_type = None
            self.metrics.primary_intensity = 0.0

        # Революционный потенциал
        # Зависит от: интенсивности противоречий, классового сознания, конфликтов
        revolutionary_factors = [self.metrics.max_intensity]

        if simulation.classes.classes_emerged:
            class_tension = simulation.classes.check_class_tension()
            revolutionary_factors.append(class_tension)

            # Классовое сознание
            for class_type, social_class in simulation.classes.classes.items():
                if class_type.is_exploited:
                    revolutionary_factors.append(social_class.class_consciousness)

        self.metrics.revolutionary_potential = (
            sum(revolutionary_factors) / len(revolutionary_factors)
            if revolutionary_factors else 0.0
        )

        # Стабильность системы (обратно пропорциональна противоречиям)
        self.metrics.system_stability = max(0.0, 1.0 - self.metrics.avg_intensity)

    def get_metrics(self) -> ContradictionMetrics:
        """Возвращает текущие метрики противоречий"""
        return self.metrics

    def get_contradictions(self,
                           active_only: bool = False) -> List[Contradiction]:
        """
        Возвращает список противоречий.

        Args:
            active_only: Если True, возвращает только неразрешённые
        """
        contradictions = list(self.contradictions.values())
        if active_only:
            contradictions = [c for c in contradictions if not c.resolved]
        return contradictions

    def get_events(self, limit: int = None) -> List[ContradictionEvent]:
        """Возвращает историю событий"""
        if limit:
            return self.events[-limit:]
        return self.events

    def get_primary_contradiction(self) -> Optional[Contradiction]:
        """Возвращает главное (наиболее интенсивное) противоречие"""
        active = [c for c in self.contradictions.values() if not c.resolved]
        if not active:
            return None
        return max(active, key=lambda c: c.intensity)

    def get_report(self) -> str:
        """Возвращает текстовый отчёт о противоречиях"""
        lines = [
            "=== ОТЧЁТ О ДИАЛЕКТИЧЕСКИХ ПРОТИВОРЕЧИЯХ ===",
            "",
            f"Всего противоречий: {self.metrics.total_contradictions}",
            f"Активных: {self.metrics.active_contradictions}",
            f"Разрешённых: {self.metrics.resolved_contradictions}",
            "",
            "--- Интенсивность ---",
            f"Средняя: {self.metrics.avg_intensity:.0%}",
            f"Максимальная: {self.metrics.max_intensity:.0%}",
            f"Критических: {self.metrics.critical_count}",
            "",
        ]

        if self.metrics.primary_contradiction_type:
            lines.extend([
                "--- Главное противоречие ---",
                f"Тип: {self.metrics.primary_contradiction_type.russian_name}",
                f"Интенсивность: {self.metrics.primary_intensity:.0%}",
                "",
            ])

        lines.extend([
            "--- Состояние системы ---",
            f"Революционный потенциал: {self.metrics.revolutionary_potential:.0%}",
            f"Стабильность системы: {self.metrics.system_stability:.0%}",
            "",
            "--- Активные противоречия ---",
        ])

        for contradiction in self.get_contradictions(active_only=True):
            lines.append(f"• {contradiction.get_summary()}")

        if not self.get_contradictions(active_only=True):
            lines.append("(нет активных противоречий)")

        lines.extend(["", "--- Последние события ---"])
        for event in self.get_events(limit=5):
            lines.append(f"• {event.get_summary()}")

        if not self.events:
            lines.append("(нет событий)")

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику для внешнего использования"""
        return {
            "metrics": self.metrics.get_summary(),
            "active_contradictions": [
                {
                    "type": c.contradiction_type.russian_name,
                    "phase": c.phase.russian_name,
                    "intensity": round(c.intensity, 2),
                    "thesis": c.thesis,
                    "antithesis": c.antithesis,
                }
                for c in self.get_contradictions(active_only=True)
            ],
            "total_events": len(self.events),
            "recent_events": [e.get_summary() for e in self.get_events(limit=5)],
        }
