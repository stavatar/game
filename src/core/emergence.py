"""
Система отслеживания эмержентных свойств симуляции.

Эмержентность (emergence) - это возникновение свойств системы,
которые не присущи её отдельным компонентам.

По Марксу, ключевые эмержентные явления:
- Частная собственность (из накопления излишков)
- Классы (из отношений собственности)
- Идеология (из классовых интересов)
- Классовая борьба (из противоречий)

Этот модуль отслеживает:
1. Когда возникают эмержентные свойства
2. При каких условиях они возникают
3. Как они развиваются со временем
4. Какие причинно-следственные связи прослеживаются

По спецификации INT-040: метрики обнаружения эмержентности.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple, TYPE_CHECKING
from enum import Enum, auto
from datetime import datetime
import math

if TYPE_CHECKING:
    from .simulation import Simulation


class EmergenceType(Enum):
    """
    Типы эмержентных явлений.

    Каждый тип представляет качественный переход
    в развитии общества.
    """
    PRIVATE_PROPERTY = ("частная собственность", "Переход от общинной к частной собственности")
    CLASS_FORMATION = ("классообразование", "Появление классов из отношений собственности")
    CLASS_CONSCIOUSNESS = ("классовое сознание", "Осознание классовых интересов")
    DOMINANT_IDEOLOGY = ("доминирующая идеология", "Формирование господствующей системы идей")
    CLASS_CONFLICT = ("классовый конфликт", "Открытое противостояние классов")
    TRADITION = ("традиция", "Закрепление практик в культуре")
    BELIEF = ("верование", "Формирование религиозных/идеологических представлений")
    SOCIAL_NORM = ("социальная норма", "Установление правил поведения")
    TECHNOLOGY = ("технология", "Открытие новых способов производства")
    SURPLUS = ("излишки", "Производство сверх необходимого для выживания")

    def __init__(self, russian_name: str, description: str):
        self.russian_name = russian_name
        self.description = description


class DevelopmentStage(Enum):
    """
    Стадии развития общества.

    По марксистской периодизации с дополнениями.
    """
    PRIMITIVE_COMMUNISM = ("первобытный коммунизм", 0, "Общая собственность, нет классов")
    PROTO_SURPLUS = ("прото-излишки", 1, "Появление нерегулярных излишков")
    SURPLUS_PRODUCTION = ("регулярные излишки", 2, "Стабильное производство излишков")
    PROPERTY_EMERGENCE = ("зарождение собственности", 3, "Первые формы частной собственности")
    CLASS_EMERGENCE = ("зарождение классов", 4, "Дифференциация на классы")
    CLASS_SOCIETY = ("классовое общество", 5, "Установившаяся классовая структура")
    CLASS_STRUGGLE = ("классовая борьба", 6, "Активное противостояние классов")
    CRISIS = ("кризис", 7, "Обострение противоречий до предела")

    def __init__(self, russian_name: str, level: int, description: str):
        self.russian_name = russian_name
        self.level = level
        self.description = description

    @classmethod
    def from_level(cls, level: int) -> 'DevelopmentStage':
        """Возвращает стадию по уровню развития"""
        for stage in cls:
            if stage.level == level:
                return stage
        return cls.PRIMITIVE_COMMUNISM if level < 0 else cls.CRISIS


@dataclass
class EmergenceEvent:
    """
    Событие эмерджентности - фиксирует момент возникновения
    нового системного свойства.

    Каждое событие содержит:
    - Что возникло (тип)
    - Когда возникло (год симуляции)
    - При каких условиях (контекст)
    - Что этому предшествовало (причины)
    - Что из этого следует (эффекты)
    """
    emergence_type: EmergenceType
    year: int
    description: str

    # Контекст возникновения
    conditions: Dict[str, Any] = field(default_factory=dict)
    triggering_factors: List[str] = field(default_factory=list)

    # Причинно-следственные связи
    caused_by: List[str] = field(default_factory=list)  # ID предыдущих событий
    leads_to: List[str] = field(default_factory=list)   # ID последующих событий

    # Количественные характеристики
    magnitude: float = 1.0         # Масштаб явления (0-1)
    stability: float = 0.5         # Устойчивость (0-1)
    reversibility: float = 0.5     # Обратимость (0-1, 0=необратимо)

    # Метаданные
    id: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"emergence_{self.emergence_type.name}_{self.year}"
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def get_summary(self) -> str:
        """Возвращает краткое описание события"""
        return (
            f"Год {self.year}: {self.emergence_type.russian_name} - "
            f"{self.description} (масштаб: {self.magnitude:.0%})"
        )


@dataclass
class EmergenceMetrics:
    """
    Метрики эмержентности - количественные показатели
    развития эмержентных свойств.

    Используются для:
    - Мониторинга прогресса симуляции
    - Сравнения разных запусков
    - Анализа чувствительности
    """
    # Базовые метрики
    development_stage: DevelopmentStage = DevelopmentStage.PRIMITIVE_COMMUNISM
    development_level: float = 0.0    # 0-1, непрерывный уровень

    # Метрики собственности
    property_inequality: float = 0.0   # Коэффициент Джини
    private_property_share: float = 0.0  # Доля частной собственности

    # Метрики классов
    class_differentiation: float = 0.0  # Степень классовой дифференциации
    class_tension: float = 0.0          # Классовая напряжённость
    consciousness_level: float = 0.0    # Средний уровень классового сознания

    # Метрики культуры
    ideology_coherence: float = 0.0     # Согласованность идеологии
    tradition_count: int = 0            # Количество традиций
    belief_diversity: float = 0.0       # Разнообразие верований

    # Метрики динамики
    emergence_velocity: float = 0.0     # Скорость возникновения новых явлений
    stability_index: float = 1.0        # Индекс стабильности (1 = стабильно)
    crisis_probability: float = 0.0     # Вероятность кризиса

    # Временные метки ключевых событий
    first_surplus_year: Optional[int] = None
    first_property_year: Optional[int] = None
    first_class_year: Optional[int] = None
    first_conflict_year: Optional[int] = None

    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку метрик"""
        return {
            "stage": self.development_stage.russian_name,
            "development_level": round(self.development_level, 2),
            "inequality": round(self.property_inequality, 2),
            "class_tension": round(self.class_tension, 2),
            "consciousness": round(self.consciousness_level, 2),
            "stability": round(self.stability_index, 2),
            "crisis_probability": round(self.crisis_probability, 2),
            "key_years": {
                "surplus": self.first_surplus_year,
                "property": self.first_property_year,
                "classes": self.first_class_year,
                "conflict": self.first_conflict_year,
            },
        }


class EmergenceTracker:
    """
    Трекер эмержентных свойств симуляции.

    Отслеживает:
    1. События эмерджентности (что возникло и когда)
    2. Метрики развития (количественные показатели)
    3. Причинно-следственные цепочки (что к чему привело)
    4. Стадии развития (качественные переходы)

    Использование:
        tracker = EmergenceTracker()
        tracker.update(simulation)  # Обновляет метрики
        metrics = tracker.get_metrics()  # Получает текущие метрики
        events = tracker.get_events()  # Получает историю событий
    """

    # Пороговые значения для определения стадий
    SURPLUS_THRESHOLD = 0.1         # Доля населения с излишками
    PROPERTY_THRESHOLD = 0.05       # Доля частной собственности
    CLASS_THRESHOLD = 0.2           # Неравенство для классообразования
    CONFLICT_THRESHOLD = 0.5        # Напряжённость для конфликта
    CRISIS_THRESHOLD = 0.8          # Напряжённость для кризиса

    def __init__(self):
        # История событий
        self.events: List[EmergenceEvent] = []
        self.events_by_type: Dict[EmergenceType, List[EmergenceEvent]] = {
            et: [] for et in EmergenceType
        }

        # Текущие метрики
        self.metrics = EmergenceMetrics()

        # Предыдущие значения для вычисления динамики
        self._previous_metrics: Optional[EmergenceMetrics] = None
        self._metrics_history: List[Tuple[int, EmergenceMetrics]] = []

        # Счётчики для отслеживания скорости
        self._events_this_year: int = 0
        self._last_update_year: int = 0

        # Флаги для предотвращения дублирования событий
        self._tracked_emergences: Set[str] = set()

    def update(self, simulation: 'Simulation') -> List[EmergenceEvent]:
        """
        Обновляет метрики и проверяет новые события эмерджентности.

        Вызывается ежегодно из симуляции для отслеживания
        развития эмержентных свойств.

        Args:
            simulation: Объект симуляции для анализа

        Returns:
            Список новых событий эмерджентности
        """
        current_year = simulation.year
        new_events = []

        # Сохраняем предыдущие метрики
        if self._last_update_year < current_year:
            self._previous_metrics = EmergenceMetrics(
                development_stage=self.metrics.development_stage,
                development_level=self.metrics.development_level,
                property_inequality=self.metrics.property_inequality,
                class_tension=self.metrics.class_tension,
                consciousness_level=self.metrics.consciousness_level,
            )
            self._events_this_year = 0
            self._last_update_year = current_year

        # Обновляем базовые метрики
        self._update_property_metrics(simulation)
        self._update_class_metrics(simulation)
        self._update_culture_metrics(simulation)
        self._update_dynamics(simulation)

        # Определяем стадию развития
        self._determine_development_stage()

        # Проверяем новые события эмерджентности
        new_events.extend(self._check_emergence_events(simulation))

        # Сохраняем историю метрик (раз в 10 лет)
        if current_year % 10 == 0:
            self._metrics_history.append((current_year, EmergenceMetrics(
                development_stage=self.metrics.development_stage,
                development_level=self.metrics.development_level,
                property_inequality=self.metrics.property_inequality,
                class_tension=self.metrics.class_tension,
            )))

        return new_events

    def _update_property_metrics(self, simulation: 'Simulation') -> None:
        """Обновляет метрики собственности"""
        # Базовые ценности ресурсов (условные единицы)
        resource_values = {
            "FOOD": 1,
            "NATURAL": 0.5,
            "MATERIAL": 2,
            "TOOL": 5,
            "LUXURY": 10,
            "KNOWLEDGE": 3,
        }

        # Неравенство собственности (Джини)
        wealth_data = {}
        for npc_id, npc in simulation.npcs.items():
            if npc.is_alive:
                # Считаем богатство как сумму ресурсов в инвентаре
                total_wealth = 0.0
                for resource in npc.inventory.resources.values():
                    category = resource.resource_type.category.name
                    value = resource_values.get(category, 1)
                    total_wealth += resource.quantity * value

                # Добавляем стоимость собственности (10 за каждую единицу)
                npc_properties = simulation.ownership.get_owner_properties(npc_id)
                property_value = len(npc_properties) * 10 if npc_properties else 0
                wealth_data[npc_id] = total_wealth + property_value

        if wealth_data and len(wealth_data) > 1:
            self.metrics.property_inequality = self._calculate_gini(
                list(wealth_data.values())
            )
        else:
            self.metrics.property_inequality = 0.0

        # Доля частной собственности
        from ..economy.property import PropertyType
        total_property = len(simulation.ownership.properties)
        private_property = sum(
            1 for p in simulation.ownership.properties.values()
            if p.owner_type == PropertyType.PRIVATE
        )
        if total_property > 0:
            self.metrics.private_property_share = private_property / total_property
        else:
            self.metrics.private_property_share = 0.0

        # Фиксируем год первой частной собственности
        if (simulation.ownership.private_property_emerged and
            self.metrics.first_property_year is None):
            self.metrics.first_property_year = simulation.ownership.first_private_property_year

    def _update_class_metrics(self, simulation: 'Simulation') -> None:
        """Обновляет метрики классов"""
        classes = simulation.classes

        # Классовая дифференциация
        if classes.classes_emerged:
            # Считаем количество разных классов с членами
            active_classes = [
                c for c in classes.classes.values()
                if c.get_size() > 0
            ]
            if active_classes:
                # Максимальное неравенство размеров классов
                sizes = [c.get_size() for c in active_classes]
                max_size = max(sizes)
                min_size = min(sizes)
                if max_size > 0:
                    self.metrics.class_differentiation = (max_size - min_size) / max_size

        # Классовая напряжённость
        self.metrics.class_tension = classes.check_class_tension()

        # Средний уровень классового сознания
        consciousness_values = []
        for class_type, social_class in classes.classes.items():
            if class_type.is_exploited and social_class.get_size() > 0:
                consciousness_values.append(social_class.class_consciousness)

        if consciousness_values:
            self.metrics.consciousness_level = sum(consciousness_values) / len(consciousness_values)
        else:
            self.metrics.consciousness_level = 0.0

        # Фиксируем год появления классов
        if classes.classes_emerged and self.metrics.first_class_year is None:
            self.metrics.first_class_year = classes.first_class_year

        # Фиксируем год первого конфликта
        if classes.conflicts and self.metrics.first_conflict_year is None:
            first_conflict = classes.conflicts[0]
            self.metrics.first_conflict_year = first_conflict.year_started

    def _update_culture_metrics(self, simulation: 'Simulation') -> None:
        """Обновляет метрики культуры"""
        beliefs = simulation.beliefs
        traditions = simulation.traditions

        # Количество традиций
        self.metrics.tradition_count = len(traditions.traditions)

        # Разнообразие верований (энтропия)
        if beliefs.beliefs:
            total_adherents = sum(
                b.get_adherent_count() for b in beliefs.beliefs.values()
            )
            if total_adherents > 0:
                entropy = 0.0
                for belief in beliefs.beliefs.values():
                    p = belief.get_adherent_count() / total_adherents
                    if p > 0:
                        entropy -= p * math.log(p)
                # Нормализуем
                max_entropy = math.log(len(beliefs.beliefs)) if len(beliefs.beliefs) > 1 else 1
                self.metrics.belief_diversity = entropy / max_entropy if max_entropy > 0 else 0.0

        # Согласованность идеологии (доля населения с доминирующими верованиями)
        if beliefs.dominant_beliefs:
            living_npcs = [n for n in simulation.npcs.values() if n.is_alive]
            if living_npcs:
                adherents_count = 0
                for npc in living_npcs:
                    npc_beliefs = beliefs.npc_beliefs.get(npc.id, set())
                    if any(b in npc_beliefs for b in beliefs.dominant_beliefs):
                        adherents_count += 1
                self.metrics.ideology_coherence = adherents_count / len(living_npcs)

    def _update_dynamics(self, simulation: 'Simulation') -> None:
        """Обновляет динамические метрики"""
        # Скорость возникновения новых явлений
        if self._previous_metrics:
            # Изменение уровня развития
            delta_level = self.metrics.development_level - self._previous_metrics.development_level
            self.metrics.emergence_velocity = max(0.0, delta_level)

        # Индекс стабильности (обратно пропорционален напряжённости)
        self.metrics.stability_index = 1.0 - self.metrics.class_tension * 0.5

        # Вероятность кризиса
        # Зависит от: напряжённости, сознания, неравенства
        crisis_factors = [
            self.metrics.class_tension,
            self.metrics.consciousness_level * 0.5,
            self.metrics.property_inequality * 0.3,
        ]
        self.metrics.crisis_probability = min(1.0, sum(crisis_factors) / 2)

    def _determine_development_stage(self) -> None:
        """Определяет текущую стадию развития"""
        # Непрерывный уровень развития (0-1)
        level = 0.0

        # Факторы развития с весами
        if self.metrics.private_property_share > 0:
            level += 0.2 * min(1.0, self.metrics.private_property_share / 0.3)

        if self.metrics.property_inequality > 0:
            level += 0.2 * min(1.0, self.metrics.property_inequality / 0.5)

        if self.metrics.class_differentiation > 0:
            level += 0.2 * self.metrics.class_differentiation

        if self.metrics.consciousness_level > 0:
            level += 0.2 * self.metrics.consciousness_level

        if self.metrics.class_tension > 0:
            level += 0.2 * self.metrics.class_tension

        self.metrics.development_level = min(1.0, level)

        # Определяем дискретную стадию
        if self.metrics.class_tension >= self.CRISIS_THRESHOLD:
            stage = DevelopmentStage.CRISIS
        elif self.metrics.class_tension >= self.CONFLICT_THRESHOLD:
            stage = DevelopmentStage.CLASS_STRUGGLE
        elif self.metrics.class_differentiation > 0.3:
            stage = DevelopmentStage.CLASS_SOCIETY
        elif self.metrics.class_differentiation > 0:
            stage = DevelopmentStage.CLASS_EMERGENCE
        elif self.metrics.private_property_share > 0:
            stage = DevelopmentStage.PROPERTY_EMERGENCE
        elif self.metrics.property_inequality > 0.1:
            stage = DevelopmentStage.SURPLUS_PRODUCTION
        elif self.metrics.property_inequality > 0:
            stage = DevelopmentStage.PROTO_SURPLUS
        else:
            stage = DevelopmentStage.PRIMITIVE_COMMUNISM

        self.metrics.development_stage = stage

    def _check_emergence_events(self, simulation: 'Simulation') -> List[EmergenceEvent]:
        """Проверяет и регистрирует новые события эмерджентности"""
        events = []
        year = simulation.year

        # === ЧАСТНАЯ СОБСТВЕННОСТЬ ===
        if (simulation.ownership.private_property_emerged and
            "private_property" not in self._tracked_emergences):
            event = EmergenceEvent(
                emergence_type=EmergenceType.PRIVATE_PROPERTY,
                year=simulation.ownership.first_private_property_year or year,
                description="Появилась частная собственность на землю",
                conditions={
                    "inequality": self.metrics.property_inequality,
                    "population": len([n for n in simulation.npcs.values() if n.is_alive]),
                },
                triggering_factors=[
                    "накопление излишков",
                    "индивидуальное производство",
                ],
                magnitude=self.metrics.private_property_share,
                stability=0.6,
                reversibility=0.3,
            )
            self._register_event(event)
            events.append(event)
            self._tracked_emergences.add("private_property")

        # === КЛАССООБРАЗОВАНИЕ ===
        if (simulation.classes.classes_emerged and
            "class_formation" not in self._tracked_emergences):
            event = EmergenceEvent(
                emergence_type=EmergenceType.CLASS_FORMATION,
                year=simulation.classes.first_class_year or year,
                description="Общество разделилось на классы",
                conditions={
                    "inequality": self.metrics.property_inequality,
                    "private_property_share": self.metrics.private_property_share,
                },
                triggering_factors=[
                    "неравенство собственности",
                    "разделение труда",
                ],
                caused_by=["emergence_PRIVATE_PROPERTY_*"],
                magnitude=self.metrics.class_differentiation,
                stability=0.7,
                reversibility=0.2,
            )
            self._register_event(event)
            events.append(event)
            self._tracked_emergences.add("class_formation")

        # === КЛАССОВОЕ СОЗНАНИЕ ===
        if (self.metrics.consciousness_level > 0.3 and
            "class_consciousness" not in self._tracked_emergences):
            event = EmergenceEvent(
                emergence_type=EmergenceType.CLASS_CONSCIOUSNESS,
                year=year,
                description="Угнетённые классы осознали свои интересы",
                conditions={
                    "consciousness_level": self.metrics.consciousness_level,
                    "class_tension": self.metrics.class_tension,
                },
                triggering_factors=[
                    "опыт эксплуатации",
                    "социальное взаимодействие",
                ],
                caused_by=["emergence_CLASS_FORMATION_*"],
                magnitude=self.metrics.consciousness_level,
                stability=0.5,
                reversibility=0.4,
            )
            self._register_event(event)
            events.append(event)
            self._tracked_emergences.add("class_consciousness")

        # === КЛАССОВЫЙ КОНФЛИКТ ===
        if (simulation.classes.conflicts and
            "class_conflict" not in self._tracked_emergences):
            first_conflict = simulation.classes.conflicts[0]
            event = EmergenceEvent(
                emergence_type=EmergenceType.CLASS_CONFLICT,
                year=first_conflict.year_started,
                description=f"Начался классовый конфликт: {first_conflict.conflict_type.russian_name}",
                conditions={
                    "tension": self.metrics.class_tension,
                    "consciousness": self.metrics.consciousness_level,
                },
                triggering_factors=[
                    "классовое напряжение",
                    "классовое сознание",
                ],
                caused_by=["emergence_CLASS_CONSCIOUSNESS_*"],
                magnitude=first_conflict.intensity,
                stability=0.3,
                reversibility=0.5,
            )
            self._register_event(event)
            events.append(event)
            self._tracked_emergences.add("class_conflict")

        # === ДОМИНИРУЮЩАЯ ИДЕОЛОГИЯ ===
        if (simulation.beliefs.dominant_beliefs and
            len(simulation.beliefs.dominant_beliefs) > 0 and
            "dominant_ideology" not in self._tracked_emergences):
            dominant_names = [
                simulation.beliefs.beliefs[b].name
                for b in simulation.beliefs.dominant_beliefs
                if b in simulation.beliefs.beliefs
            ]
            if dominant_names:
                event = EmergenceEvent(
                    emergence_type=EmergenceType.DOMINANT_IDEOLOGY,
                    year=year,
                    description=f"Сформировалась доминирующая идеология: {', '.join(dominant_names)}",
                    conditions={
                        "ideology_coherence": self.metrics.ideology_coherence,
                        "class_emerged": simulation.classes.classes_emerged,
                    },
                    triggering_factors=[
                        "интересы господствующего класса",
                        "распространение верований",
                    ],
                    caused_by=["emergence_CLASS_FORMATION_*"],
                    magnitude=self.metrics.ideology_coherence,
                    stability=0.6,
                    reversibility=0.4,
                )
                self._register_event(event)
                events.append(event)
                self._tracked_emergences.add("dominant_ideology")

        # === НОВЫЕ ВЕРОВАНИЯ ===
        for belief_id, belief in simulation.beliefs.beliefs.items():
            event_key = f"belief_{belief_id}"
            if event_key not in self._tracked_emergences:
                event = EmergenceEvent(
                    emergence_type=EmergenceType.BELIEF,
                    year=belief.year_emerged,
                    description=f"Возникло верование: {belief.name}",
                    conditions={
                        "origin": belief.origin.value,
                        "adherents": belief.get_adherent_count(),
                    },
                    triggering_factors=[str(k) + "=" + str(v) for k, v in belief.origin_conditions.items()],
                    magnitude=min(1.0, belief.get_adherent_count() / max(1, len(simulation.npcs))),
                    stability=belief.strength,
                    reversibility=0.6,
                )
                self._register_event(event)
                events.append(event)
                self._tracked_emergences.add(event_key)

        # === НОВЫЕ ТРАДИЦИИ ===
        for tradition_id, tradition in simulation.traditions.traditions.items():
            event_key = f"tradition_{tradition_id}"
            if event_key not in self._tracked_emergences:
                event = EmergenceEvent(
                    emergence_type=EmergenceType.TRADITION,
                    year=tradition.year_emerged,
                    description=f"Возникла традиция: {tradition.name}",
                    conditions={
                        "type": tradition.tradition_type.value,
                        "origin_event": tradition.origin_event,
                    },
                    triggering_factors=[tradition.origin_event] if tradition.origin_event else [],
                    magnitude=tradition.social_cohesion_bonus,
                    stability=0.8,
                    reversibility=0.2,
                )
                self._register_event(event)
                events.append(event)
                self._tracked_emergences.add(event_key)

        # === НОВЫЕ ТЕХНОЛОГИИ ===
        for tech_id in simulation.knowledge.discovered_technologies:
            event_key = f"tech_{tech_id}"
            if event_key not in self._tracked_emergences:
                from ..economy.technology import TECHNOLOGIES
                tech = TECHNOLOGIES.get(tech_id)
                if tech:
                    # Ищем год открытия в истории (tech_id, npc_id, year)
                    discovery_year = 1
                    for hist_tech_id, _, hist_year in simulation.knowledge.discovery_history:
                        if hist_tech_id == tech_id:
                            discovery_year = hist_year
                            break

                    event = EmergenceEvent(
                        emergence_type=EmergenceType.TECHNOLOGY,
                        year=discovery_year,
                        description=f"Открыта технология: {tech.name}",
                        conditions={
                            "era": tech.era.value,
                            "difficulty": tech.discovery_difficulty,
                        },
                        magnitude=0.5,
                        stability=0.9,
                        reversibility=0.1,
                    )
                    self._register_event(event)
                    events.append(event)
                self._tracked_emergences.add(event_key)

        return events

    def _register_event(self, event: EmergenceEvent) -> None:
        """Регистрирует событие в истории"""
        self.events.append(event)
        self.events_by_type[event.emergence_type].append(event)
        self._events_this_year += 1

    def _calculate_gini(self, values: List[float]) -> float:
        """Вычисляет коэффициент Джини для списка значений"""
        if not values or len(values) <= 1:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)
        total = sum(sorted_values)

        if total == 0:
            return 0.0

        cumulative = sum((2 * i - n - 1) * v for i, v in enumerate(sorted_values, 1))
        return cumulative / (n * total)

    def get_metrics(self) -> EmergenceMetrics:
        """Возвращает текущие метрики эмерджентности"""
        return self.metrics

    def get_events(self, emergence_type: EmergenceType = None) -> List[EmergenceEvent]:
        """
        Возвращает события эмерджентности.

        Args:
            emergence_type: Фильтр по типу (None = все события)
        """
        if emergence_type:
            return self.events_by_type.get(emergence_type, [])
        return self.events

    def get_timeline(self) -> List[Tuple[int, str]]:
        """Возвращает хронологию событий эмерджентности"""
        timeline = []
        for event in sorted(self.events, key=lambda e: e.year):
            timeline.append((event.year, event.get_summary()))
        return timeline

    def get_causal_chains(self) -> List[List[EmergenceEvent]]:
        """
        Возвращает причинно-следственные цепочки событий.

        Каждая цепочка - последовательность связанных событий.
        """
        chains = []

        # Ищем корневые события (без причин)
        roots = [e for e in self.events if not e.caused_by]

        for root in roots:
            chain = [root]
            self._build_chain(root, chain)
            if len(chain) > 1:
                chains.append(chain)

        return chains

    def _build_chain(self, event: EmergenceEvent, chain: List[EmergenceEvent]) -> None:
        """Рекурсивно строит цепочку событий"""
        for other in self.events:
            for cause_pattern in other.caused_by:
                if cause_pattern.startswith(event.emergence_type.name) or \
                   event.id in cause_pattern:
                    if other not in chain:
                        chain.append(other)
                        self._build_chain(other, chain)

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику по эмерджентным явлениям"""
        events_by_type_count = {
            et.russian_name: len(events)
            for et, events in self.events_by_type.items()
            if events
        }

        return {
            "total_events": len(self.events),
            "events_by_type": events_by_type_count,
            "development_stage": self.metrics.development_stage.russian_name,
            "development_level": round(self.metrics.development_level, 2),
            "metrics_summary": self.metrics.get_summary(),
            "timeline": self.get_timeline()[-10:],  # Последние 10 событий
        }

    def get_development_report(self) -> str:
        """Возвращает текстовый отчёт о развитии общества"""
        lines = [
            "=== ОТЧЁТ О РАЗВИТИИ ОБЩЕСТВА ===",
            "",
            f"Текущая стадия: {self.metrics.development_stage.russian_name}",
            f"Уровень развития: {self.metrics.development_level:.0%}",
            "",
            "--- Экономика ---",
            f"Неравенство (Джини): {self.metrics.property_inequality:.2f}",
            f"Доля частной собственности: {self.metrics.private_property_share:.0%}",
            "",
            "--- Классы ---",
            f"Классовая дифференциация: {self.metrics.class_differentiation:.0%}",
            f"Классовое напряжение: {self.metrics.class_tension:.0%}",
            f"Классовое сознание: {self.metrics.consciousness_level:.0%}",
            "",
            "--- Культура ---",
            f"Количество традиций: {self.metrics.tradition_count}",
            f"Разнообразие верований: {self.metrics.belief_diversity:.0%}",
            f"Согласованность идеологии: {self.metrics.ideology_coherence:.0%}",
            "",
            "--- Динамика ---",
            f"Скорость развития: {self.metrics.emergence_velocity:.2f}",
            f"Индекс стабильности: {self.metrics.stability_index:.0%}",
            f"Вероятность кризиса: {self.metrics.crisis_probability:.0%}",
            "",
            "--- Ключевые даты ---",
        ]

        if self.metrics.first_property_year:
            lines.append(f"Частная собственность: год {self.metrics.first_property_year}")
        if self.metrics.first_class_year:
            lines.append(f"Появление классов: год {self.metrics.first_class_year}")
        if self.metrics.first_conflict_year:
            lines.append(f"Первый конфликт: год {self.metrics.first_conflict_year}")

        lines.append("")
        lines.append(f"Всего событий эмерджентности: {len(self.events)}")

        return "\n".join(lines)
