"""
Фреймворк анализа чувствительности параметров симуляции.

Этот модуль позволяет:
1. Определять параметры и их диапазоны для варьирования
2. Запускать батчи симуляций с различными комбинациями параметров
3. Собирать метрики результатов по каждому запуску
4. Анализировать влияние параметров на результаты
5. Выявлять наиболее критичные параметры

По спецификации INT-041: фреймворк анализа чувствительности.

Применение в марксистском анализе:
- Как начальное неравенство влияет на классообразование?
- Как размер популяции влияет на скорость накопления?
- Какие параметры критичны для возникновения частной собственности?
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple, Callable, Union, TYPE_CHECKING
from enum import Enum, auto
from datetime import datetime
import random
import math
import copy
import statistics
from collections import defaultdict

if TYPE_CHECKING:
    from ..core.simulation import Simulation


class ParameterType(Enum):
    """
    Типы параметров для анализа чувствительности.

    Каждый тип определяет как параметр варьируется и интерпретируется.
    """
    CONTINUOUS = ("непрерывный", "Вещественное значение в диапазоне")
    INTEGER = ("целочисленный", "Целое значение в диапазоне")
    CATEGORICAL = ("категориальный", "Дискретный набор значений")
    BOOLEAN = ("логический", "True или False")

    def __init__(self, russian_name: str, description: str):
        self.russian_name = russian_name
        self.description = description


class SamplingStrategy(Enum):
    """
    Стратегии семплирования пространства параметров.

    Разные стратегии дают разный баланс между
    покрытием пространства и количеством запусков.
    """
    GRID = ("сетка", "Полный перебор всех комбинаций точек сетки")
    RANDOM = ("случайный", "Случайная выборка из пространства параметров")
    LATIN_HYPERCUBE = ("латинский гиперкуб", "Стратифицированная выборка для лучшего покрытия")
    SOBOL = ("последовательность Соболя", "Квази-случайная последовательность низкого расхождения")
    ONE_AT_A_TIME = ("по одному", "Варьирование одного параметра при фиксации остальных")

    def __init__(self, russian_name: str, description: str):
        self.russian_name = russian_name
        self.description = description


class OutcomeCategory(Enum):
    """
    Категории результатов симуляции для анализа.

    Группируем метрики по смыслу для удобства интерпретации.
    """
    ECONOMIC = ("экономические", "Показатели экономического развития")
    SOCIAL = ("социальные", "Показатели социальной структуры")
    CULTURAL = ("культурные", "Показатели культурного развития")
    DEMOGRAPHIC = ("демографические", "Показатели населения")
    EMERGENCE = ("эмерджентные", "Показатели возникновения новых свойств")
    DIALECTIC = ("диалектические", "Показатели противоречий")

    def __init__(self, russian_name: str, description: str):
        self.russian_name = russian_name
        self.description = description


@dataclass
class ParameterSpec:
    """
    Спецификация параметра для анализа чувствительности.

    Определяет:
    - Имя параметра и как его установить в симуляции
    - Тип параметра (непрерывный, дискретный, категориальный)
    - Диапазон или набор возможных значений
    - Базовое (по умолчанию) значение
    """
    name: str
    param_type: ParameterType
    description: str = ""

    # Путь для установки значения (например, "config.initial_population")
    path: str = ""

    # Для непрерывных и целочисленных параметров
    min_value: float = 0.0
    max_value: float = 1.0
    default_value: float = 0.5

    # Для категориальных параметров
    categories: List[Any] = field(default_factory=list)
    default_category: Any = None

    # Количество точек для сетки
    grid_points: int = 5

    # Категория влияния (для группировки)
    category: str = "general"

    # Единицы измерения (для отображения)
    units: str = ""

    def get_grid_values(self) -> List[Any]:
        """Возвращает значения для сеточного семплирования"""
        if self.param_type == ParameterType.BOOLEAN:
            return [False, True]
        elif self.param_type == ParameterType.CATEGORICAL:
            return self.categories
        elif self.param_type == ParameterType.INTEGER:
            step = max(1, int((self.max_value - self.min_value) / (self.grid_points - 1)))
            return list(range(int(self.min_value), int(self.max_value) + 1, step))
        else:  # CONTINUOUS
            step = (self.max_value - self.min_value) / (self.grid_points - 1)
            return [self.min_value + i * step for i in range(self.grid_points)]

    def sample_random(self) -> Any:
        """Возвращает случайное значение из допустимого диапазона"""
        if self.param_type == ParameterType.BOOLEAN:
            return random.choice([False, True])
        elif self.param_type == ParameterType.CATEGORICAL:
            return random.choice(self.categories)
        elif self.param_type == ParameterType.INTEGER:
            return random.randint(int(self.min_value), int(self.max_value))
        else:  # CONTINUOUS
            return random.uniform(self.min_value, self.max_value)

    def sample_from_unit(self, unit_value: float) -> Any:
        """
        Преобразует значение из [0,1] в значение параметра.
        Используется для Latin Hypercube и Sobol семплирования.
        """
        if self.param_type == ParameterType.BOOLEAN:
            return unit_value >= 0.5
        elif self.param_type == ParameterType.CATEGORICAL:
            idx = int(unit_value * len(self.categories))
            idx = min(idx, len(self.categories) - 1)
            return self.categories[idx]
        elif self.param_type == ParameterType.INTEGER:
            val = self.min_value + unit_value * (self.max_value - self.min_value)
            return int(round(val))
        else:  # CONTINUOUS
            return self.min_value + unit_value * (self.max_value - self.min_value)


@dataclass
class OutcomeSpec:
    """
    Спецификация метрики результата для отслеживания.

    Определяет что измерять и как извлекать значение из симуляции.
    """
    name: str
    description: str
    category: OutcomeCategory

    # Функция для извлечения значения из симуляции
    # Сигнатура: (simulation) -> float
    extractor: Optional[Callable[['Simulation'], float]] = None

    # Путь для извлечения (альтернатива функции)
    path: str = ""

    # Единицы измерения
    units: str = ""

    # Диапазон ожидаемых значений (для нормализации)
    expected_min: float = 0.0
    expected_max: float = 1.0

    # Направление оптимизации (maximize/minimize/target)
    optimization_direction: str = "none"
    target_value: Optional[float] = None


@dataclass
class RunResult:
    """
    Результат одного запуска симуляции.

    Содержит:
    - Значения параметров, использованных в запуске
    - Значения всех отслеживаемых метрик
    - Метаданные запуска (время, длительность, статус)
    """
    run_id: int
    parameters: Dict[str, Any]
    outcomes: Dict[str, float]

    # Метаданные
    simulation_years: int = 0
    wall_time_seconds: float = 0.0
    success: bool = True
    error_message: str = ""

    # Временные метки
    started_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()

    def get_param_vector(self, param_names: List[str]) -> List[float]:
        """Возвращает вектор значений параметров"""
        return [float(self.parameters.get(name, 0)) for name in param_names]

    def get_outcome_vector(self, outcome_names: List[str]) -> List[float]:
        """Возвращает вектор значений метрик"""
        return [self.outcomes.get(name, 0.0) for name in outcome_names]


@dataclass
class SensitivityResult:
    """
    Результат анализа чувствительности одного параметра.

    Показывает как параметр влияет на каждую метрику результата.
    """
    parameter_name: str

    # Влияние на каждую метрику
    # outcome_name -> correlation coefficient
    correlations: Dict[str, float] = field(default_factory=dict)

    # Статистическая значимость корреляций
    # outcome_name -> p-value (приближённая)
    significance: Dict[str, float] = field(default_factory=dict)

    # Среднее изменение метрики при изменении параметра на 1 стд. отклонение
    standardized_effects: Dict[str, float] = field(default_factory=dict)

    # Индекс важности (среднее |correlation| по всем метрикам)
    importance_index: float = 0.0

    def calculate_importance(self) -> None:
        """Вычисляет индекс важности параметра"""
        if self.correlations:
            self.importance_index = statistics.mean(
                abs(c) for c in self.correlations.values()
            )


@dataclass
class AnalysisReport:
    """
    Полный отчёт анализа чувствительности.

    Агрегирует результаты всех запусков и анализа.
    """
    # Конфигурация анализа
    total_runs: int
    simulation_years_per_run: int
    sampling_strategy: SamplingStrategy
    parameters_analyzed: List[str]
    outcomes_tracked: List[str]

    # Результаты запусков
    successful_runs: int = 0
    failed_runs: int = 0
    total_wall_time: float = 0.0

    # Статистика параметров
    parameter_statistics: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Статистика метрик
    outcome_statistics: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Результаты анализа чувствительности
    sensitivity_results: Dict[str, SensitivityResult] = field(default_factory=dict)

    # Ранжирование параметров по важности
    parameter_ranking: List[Tuple[str, float]] = field(default_factory=list)

    # Корреляционная матрица параметр-метрика
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Ключевые находки
    key_findings: List[str] = field(default_factory=list)

    # Временные метки
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class SensitivityAnalyzer:
    """
    Анализатор чувствительности параметров симуляции.

    Позволяет:
    1. Определить параметры для варьирования
    2. Определить метрики результатов для отслеживания
    3. Запустить батч симуляций с разными параметрами
    4. Проанализировать влияние параметров на результаты
    5. Сгенерировать отчёт с рекомендациями

    Использование:
        analyzer = SensitivityAnalyzer()
        analyzer.add_parameter(ParameterSpec(...))
        analyzer.add_outcome(OutcomeSpec(...))
        analyzer.run_analysis(n_runs=100, years_per_run=50)
        report = analyzer.get_report()
    """

    # Предопределённые параметры симуляции
    STANDARD_PARAMETERS: Dict[str, ParameterSpec] = {
        "initial_population": ParameterSpec(
            name="initial_population",
            param_type=ParameterType.INTEGER,
            description="Начальный размер популяции",
            path="config.initial_population",
            min_value=4,
            max_value=50,
            default_value=12,
            grid_points=5,
            category="demographic",
            units="человек"
        ),
        "map_size": ParameterSpec(
            name="map_size",
            param_type=ParameterType.INTEGER,
            description="Размер карты",
            path="config.map_size",
            min_value=20,
            max_value=100,
            default_value=50,
            grid_points=5,
            category="world",
            units="клеток"
        ),
        "initial_resources_multiplier": ParameterSpec(
            name="initial_resources_multiplier",
            param_type=ParameterType.CONTINUOUS,
            description="Множитель начальных ресурсов",
            path="config.initial_resources_multiplier",
            min_value=0.5,
            max_value=2.0,
            default_value=1.0,
            grid_points=5,
            category="economic"
        ),
        "gathering_efficiency": ParameterSpec(
            name="gathering_efficiency",
            param_type=ParameterType.CONTINUOUS,
            description="Базовая эффективность собирательства",
            path="production.base_efficiency.gathering",
            min_value=0.5,
            max_value=2.0,
            default_value=1.0,
            grid_points=5,
            category="economic"
        ),
        "property_claim_probability": ParameterSpec(
            name="property_claim_probability",
            param_type=ParameterType.CONTINUOUS,
            description="Вероятность заявки на собственность при излишках",
            path="ownership.claim_probability",
            min_value=0.0,
            max_value=0.5,
            default_value=0.1,
            grid_points=5,
            category="economic"
        ),
        "belief_spread_rate": ParameterSpec(
            name="belief_spread_rate",
            param_type=ParameterType.CONTINUOUS,
            description="Скорость распространения верований",
            path="beliefs.spread_rate",
            min_value=0.1,
            max_value=1.0,
            default_value=0.5,
            grid_points=5,
            category="cultural"
        ),
        "class_consciousness_growth": ParameterSpec(
            name="class_consciousness_growth",
            param_type=ParameterType.CONTINUOUS,
            description="Скорость роста классового сознания",
            path="classes.consciousness_growth_rate",
            min_value=0.01,
            max_value=0.2,
            default_value=0.05,
            grid_points=5,
            category="social"
        ),
        "technology_discovery_rate": ParameterSpec(
            name="technology_discovery_rate",
            param_type=ParameterType.CONTINUOUS,
            description="Базовая вероятность открытия технологии",
            path="knowledge.discovery_rate",
            min_value=0.001,
            max_value=0.05,
            default_value=0.01,
            grid_points=5,
            category="economic"
        ),
    }

    def __init__(self):
        # Конфигурация параметров для варьирования
        self.parameters: Dict[str, ParameterSpec] = {}

        # Конфигурация метрик для отслеживания
        self.outcomes: Dict[str, OutcomeSpec] = {}

        # Результаты запусков
        self.results: List[RunResult] = []

        # Текущий анализ
        self._analysis_report: Optional[AnalysisReport] = None

        # Фабрика симуляции (для создания новых экземпляров)
        self._simulation_factory: Optional[Callable[[], 'Simulation']] = None

        # Добавляем стандартные метрики результатов
        self._setup_standard_outcomes()

    def _setup_standard_outcomes(self) -> None:
        """Настраивает стандартные метрики результатов"""
        # Экономические метрики
        self.add_outcome(OutcomeSpec(
            name="property_inequality",
            description="Коэффициент Джини неравенства собственности",
            category=OutcomeCategory.ECONOMIC,
            path="ownership.calculate_inequality()",
            expected_min=0.0,
            expected_max=1.0
        ))

        self.add_outcome(OutcomeSpec(
            name="private_property_emerged",
            description="Возникла ли частная собственность (0/1)",
            category=OutcomeCategory.EMERGENCE,
            path="ownership.private_property_emerged",
            expected_min=0.0,
            expected_max=1.0
        ))

        self.add_outcome(OutcomeSpec(
            name="first_property_year",
            description="Год возникновения частной собственности",
            category=OutcomeCategory.EMERGENCE,
            path="ownership.first_private_property_year",
            expected_min=1.0,
            expected_max=100.0
        ))

        # Социальные метрики
        self.add_outcome(OutcomeSpec(
            name="classes_emerged",
            description="Возникли ли классы (0/1)",
            category=OutcomeCategory.EMERGENCE,
            path="classes.classes_emerged",
            expected_min=0.0,
            expected_max=1.0
        ))

        self.add_outcome(OutcomeSpec(
            name="class_tension",
            description="Уровень классового напряжения",
            category=OutcomeCategory.SOCIAL,
            path="classes.check_class_tension()",
            expected_min=0.0,
            expected_max=1.0
        ))

        self.add_outcome(OutcomeSpec(
            name="class_consciousness",
            description="Средний уровень классового сознания угнетённых",
            category=OutcomeCategory.SOCIAL,
            expected_min=0.0,
            expected_max=1.0
        ))

        # Культурные метрики
        self.add_outcome(OutcomeSpec(
            name="traditions_count",
            description="Количество возникших традиций",
            category=OutcomeCategory.CULTURAL,
            path="len(traditions.traditions)",
            expected_min=0.0,
            expected_max=20.0
        ))

        self.add_outcome(OutcomeSpec(
            name="beliefs_count",
            description="Количество возникших верований",
            category=OutcomeCategory.CULTURAL,
            path="len(beliefs.beliefs)",
            expected_min=0.0,
            expected_max=20.0
        ))

        # Демографические метрики
        self.add_outcome(OutcomeSpec(
            name="final_population",
            description="Конечный размер популяции",
            category=OutcomeCategory.DEMOGRAPHIC,
            expected_min=0.0,
            expected_max=100.0,
            units="человек"
        ))

        self.add_outcome(OutcomeSpec(
            name="population_growth_rate",
            description="Средний темп роста населения",
            category=OutcomeCategory.DEMOGRAPHIC,
            expected_min=-0.1,
            expected_max=0.1
        ))

        # Технологические метрики
        self.add_outcome(OutcomeSpec(
            name="technologies_discovered",
            description="Количество открытых технологий",
            category=OutcomeCategory.ECONOMIC,
            path="len(knowledge.discovered_technologies)",
            expected_min=0.0,
            expected_max=50.0
        ))

        # Диалектические метрики
        self.add_outcome(OutcomeSpec(
            name="contradictions_count",
            description="Количество активных противоречий",
            category=OutcomeCategory.DIALECTIC,
            expected_min=0.0,
            expected_max=6.0
        ))

        self.add_outcome(OutcomeSpec(
            name="revolutionary_potential",
            description="Революционный потенциал",
            category=OutcomeCategory.DIALECTIC,
            expected_min=0.0,
            expected_max=1.0
        ))

        # Эмерджентные метрики
        self.add_outcome(OutcomeSpec(
            name="development_level",
            description="Уровень развития общества",
            category=OutcomeCategory.EMERGENCE,
            expected_min=0.0,
            expected_max=1.0
        ))

        self.add_outcome(OutcomeSpec(
            name="conflicts_count",
            description="Количество классовых конфликтов",
            category=OutcomeCategory.SOCIAL,
            path="len(classes.conflicts)",
            expected_min=0.0,
            expected_max=10.0
        ))

    def add_parameter(self, spec: ParameterSpec) -> None:
        """Добавляет параметр для варьирования"""
        self.parameters[spec.name] = spec

    def add_standard_parameter(self, name: str) -> bool:
        """Добавляет один из стандартных параметров по имени"""
        if name in self.STANDARD_PARAMETERS:
            self.parameters[name] = copy.deepcopy(self.STANDARD_PARAMETERS[name])
            return True
        return False

    def add_all_standard_parameters(self) -> None:
        """Добавляет все стандартные параметры"""
        for name in self.STANDARD_PARAMETERS:
            self.add_standard_parameter(name)

    def add_outcome(self, spec: OutcomeSpec) -> None:
        """Добавляет метрику результата для отслеживания"""
        self.outcomes[spec.name] = spec

    def remove_parameter(self, name: str) -> bool:
        """Удаляет параметр из анализа"""
        if name in self.parameters:
            del self.parameters[name]
            return True
        return False

    def remove_outcome(self, name: str) -> bool:
        """Удаляет метрику из отслеживания"""
        if name in self.outcomes:
            del self.outcomes[name]
            return True
        return False

    def set_simulation_factory(self, factory: Callable[[], 'Simulation']) -> None:
        """
        Устанавливает фабрику для создания симуляций.

        Фабрика должна возвращать новый экземпляр Simulation
        при каждом вызове.
        """
        self._simulation_factory = factory

    def _create_simulation(self) -> 'Simulation':
        """Создаёт новый экземпляр симуляции"""
        if self._simulation_factory:
            return self._simulation_factory()

        # Ленивый импорт для избежания циклических зависимостей
        from ..core.simulation import Simulation
        return Simulation()

    def _apply_parameters(self, simulation: 'Simulation',
                          parameters: Dict[str, Any]) -> None:
        """
        Применяет набор параметров к симуляции.

        Параметры применяются через path или специальную логику.
        """
        for name, value in parameters.items():
            if name not in self.parameters:
                continue

            spec = self.parameters[name]

            # Применяем по известным путям
            if name == "initial_population":
                simulation.config.initial_population = int(value)
            elif name == "map_size":
                simulation.config.map_size = int(value)
            elif name == "initial_resources_multiplier":
                # Применяем при инициализации
                simulation._initial_resources_multiplier = float(value)
            elif name == "gathering_efficiency":
                simulation.production._base_efficiency_modifier = float(value)
            elif name == "property_claim_probability":
                simulation._property_claim_probability = float(value)
            elif name == "belief_spread_rate":
                simulation.beliefs._spread_rate = float(value)
            elif name == "class_consciousness_growth":
                simulation.classes._consciousness_growth_rate = float(value)
            elif name == "technology_discovery_rate":
                simulation.knowledge._discovery_rate_modifier = float(value)
            # Добавляем кастомную логику для других параметров

    def _extract_outcomes(self, simulation: 'Simulation') -> Dict[str, float]:
        """
        Извлекает все метрики результатов из симуляции.

        Использует extractors или paths из спецификаций.
        """
        outcomes = {}

        for name, spec in self.outcomes.items():
            try:
                if spec.extractor:
                    outcomes[name] = spec.extractor(simulation)
                elif spec.path:
                    # Пытаемся вычислить путь
                    outcomes[name] = self._evaluate_path(simulation, spec.path)
                else:
                    # Пробуем извлечь по имени
                    outcomes[name] = self._extract_by_name(simulation, name)
            except Exception:
                # При ошибке используем NaN
                outcomes[name] = float('nan')

        return outcomes

    def _evaluate_path(self, simulation: 'Simulation', path: str) -> float:
        """Вычисляет значение по пути в симуляции"""
        # Простой eval с ограниченным контекстом
        try:
            # Заменяем вызовы методов
            if "()" in path:
                parts = path.split(".")
                obj = simulation
                for i, part in enumerate(parts[:-1]):
                    obj = getattr(obj, part)

                final_part = parts[-1]
                if "()" in final_part:
                    method_name = final_part.replace("()", "")
                    return float(getattr(obj, method_name)())
                else:
                    return float(getattr(obj, final_part))

            # len() вызовы
            if path.startswith("len(") and path.endswith(")"):
                inner_path = path[4:-1]
                parts = inner_path.split(".")
                obj = simulation
                for part in parts:
                    obj = getattr(obj, part)
                return float(len(obj))

            # Простой доступ к атрибутам
            parts = path.split(".")
            obj = simulation
            for part in parts:
                obj = getattr(obj, part)

            # Преобразуем в float
            if isinstance(obj, bool):
                return 1.0 if obj else 0.0
            return float(obj)

        except (AttributeError, TypeError, ValueError):
            return float('nan')

    def _extract_by_name(self, simulation: 'Simulation', name: str) -> float:
        """Извлекает значение метрики по имени"""
        try:
            if name == "property_inequality":
                return simulation.ownership.calculate_inequality()

            elif name == "private_property_emerged":
                return 1.0 if simulation.ownership.private_property_emerged else 0.0

            elif name == "first_property_year":
                year = simulation.ownership.first_private_property_year
                return float(year) if year else float('nan')

            elif name == "classes_emerged":
                return 1.0 if simulation.classes.classes_emerged else 0.0

            elif name == "class_tension":
                return simulation.classes.check_class_tension()

            elif name == "class_consciousness":
                consciousness_values = []
                for class_type, social_class in simulation.classes.classes.items():
                    if class_type.is_exploited and social_class.get_size() > 0:
                        consciousness_values.append(social_class.class_consciousness)
                return statistics.mean(consciousness_values) if consciousness_values else 0.0

            elif name == "traditions_count":
                return float(len(simulation.traditions.traditions))

            elif name == "beliefs_count":
                return float(len(simulation.beliefs.beliefs))

            elif name == "final_population":
                return float(sum(1 for n in simulation.npcs.values() if n.is_alive))

            elif name == "population_growth_rate":
                initial = simulation.config.initial_population
                final = sum(1 for n in simulation.npcs.values() if n.is_alive)
                years = simulation.year
                if years > 0 and initial > 0:
                    return (final - initial) / (initial * years)
                return 0.0

            elif name == "technologies_discovered":
                return float(len(simulation.knowledge.discovered_technologies))

            elif name == "contradictions_count":
                if hasattr(simulation, 'contradiction_detector'):
                    return float(simulation.contradiction_detector.metrics.active_contradictions)
                return 0.0

            elif name == "revolutionary_potential":
                if hasattr(simulation, 'contradiction_detector'):
                    return simulation.contradiction_detector.metrics.revolutionary_potential
                return 0.0

            elif name == "development_level":
                if hasattr(simulation, 'emergence_tracker'):
                    return simulation.emergence_tracker.metrics.development_level
                return 0.0

            elif name == "conflicts_count":
                return float(len(simulation.classes.conflicts))

            return float('nan')

        except Exception:
            return float('nan')

    def _generate_parameter_samples(self,
                                     n_samples: int,
                                     strategy: SamplingStrategy
                                     ) -> List[Dict[str, Any]]:
        """
        Генерирует набор комбинаций параметров для запусков.

        Args:
            n_samples: Желаемое количество выборок
            strategy: Стратегия семплирования

        Returns:
            Список словарей параметров для каждого запуска
        """
        if not self.parameters:
            return [{}]

        param_names = list(self.parameters.keys())

        if strategy == SamplingStrategy.GRID:
            return self._generate_grid_samples()

        elif strategy == SamplingStrategy.RANDOM:
            return self._generate_random_samples(n_samples)

        elif strategy == SamplingStrategy.LATIN_HYPERCUBE:
            return self._generate_lhs_samples(n_samples)

        elif strategy == SamplingStrategy.ONE_AT_A_TIME:
            return self._generate_oat_samples()

        else:
            # По умолчанию - случайное семплирование
            return self._generate_random_samples(n_samples)

    def _generate_grid_samples(self) -> List[Dict[str, Any]]:
        """Генерирует полную сетку комбинаций"""
        param_names = list(self.parameters.keys())
        param_values = [self.parameters[name].get_grid_values() for name in param_names]

        # Декартово произведение
        samples = []
        self._cartesian_product(param_names, param_values, 0, {}, samples)

        return samples

    def _cartesian_product(self,
                           names: List[str],
                           values: List[List[Any]],
                           idx: int,
                           current: Dict[str, Any],
                           result: List[Dict[str, Any]]) -> None:
        """Рекурсивно строит декартово произведение"""
        if idx == len(names):
            result.append(current.copy())
            return

        for val in values[idx]:
            current[names[idx]] = val
            self._cartesian_product(names, values, idx + 1, current, result)

    def _generate_random_samples(self, n_samples: int) -> List[Dict[str, Any]]:
        """Генерирует случайные выборки"""
        samples = []
        for _ in range(n_samples):
            sample = {}
            for name, spec in self.parameters.items():
                sample[name] = spec.sample_random()
            samples.append(sample)
        return samples

    def _generate_lhs_samples(self, n_samples: int) -> List[Dict[str, Any]]:
        """
        Генерирует выборки методом Latin Hypercube Sampling.

        Обеспечивает лучшее покрытие пространства параметров
        при меньшем количестве выборок.
        """
        param_names = list(self.parameters.keys())
        n_params = len(param_names)

        # Генерируем латинский гиперкуб в единичном кубе
        # Для каждого параметра делим [0,1] на n_samples равных интервалов
        # и берём по одной точке из каждого интервала (случайно внутри)

        unit_samples = []
        for _ in range(n_samples):
            unit_samples.append([0.0] * n_params)

        for param_idx in range(n_params):
            # Перестановка для данного параметра
            perm = list(range(n_samples))
            random.shuffle(perm)

            for sample_idx in range(n_samples):
                # Случайная точка внутри своего интервала
                low = perm[sample_idx] / n_samples
                high = (perm[sample_idx] + 1) / n_samples
                unit_samples[sample_idx][param_idx] = random.uniform(low, high)

        # Преобразуем единичные координаты в реальные значения параметров
        samples = []
        for unit_sample in unit_samples:
            sample = {}
            for param_idx, name in enumerate(param_names):
                spec = self.parameters[name]
                sample[name] = spec.sample_from_unit(unit_sample[param_idx])
            samples.append(sample)

        return samples

    def _generate_oat_samples(self) -> List[Dict[str, Any]]:
        """
        Генерирует выборки методом One-At-A-Time.

        Варьирует один параметр при фиксации остальных
        на значениях по умолчанию.
        """
        samples = []

        # Базовая выборка с дефолтными значениями
        base_sample = {}
        for name, spec in self.parameters.items():
            if spec.param_type == ParameterType.CATEGORICAL:
                base_sample[name] = spec.default_category or spec.categories[0]
            else:
                base_sample[name] = spec.default_value

        samples.append(base_sample.copy())

        # Для каждого параметра - варьируем только его
        for vary_name, vary_spec in self.parameters.items():
            for value in vary_spec.get_grid_values():
                if vary_spec.param_type == ParameterType.CATEGORICAL:
                    if value == vary_spec.default_category:
                        continue
                else:
                    if value == vary_spec.default_value:
                        continue

                sample = base_sample.copy()
                sample[vary_name] = value
                samples.append(sample)

        return samples

    def run_single(self,
                   parameters: Dict[str, Any],
                   years: int,
                   run_id: int = 0) -> RunResult:
        """
        Выполняет один запуск симуляции с заданными параметрами.

        Args:
            parameters: Словарь параметров для этого запуска
            years: Количество лет симуляции
            run_id: Идентификатор запуска

        Returns:
            Результат запуска
        """
        import time
        start_time = time.time()

        result = RunResult(
            run_id=run_id,
            parameters=parameters.copy(),
            outcomes={},
            simulation_years=years
        )

        try:
            # Создаём симуляцию
            simulation = self._create_simulation()

            # Применяем параметры
            self._apply_parameters(simulation, parameters)

            # Инициализируем
            simulation.initialize()

            # Запускаем на заданное количество лет
            hours_per_year = 24 * 365
            for _ in range(years):
                simulation.update(hours_per_year)

            # Извлекаем результаты
            result.outcomes = self._extract_outcomes(simulation)
            result.success = True

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.wall_time_seconds = time.time() - start_time
        result.completed_at = datetime.now().isoformat()

        return result

    def run_analysis(self,
                     n_runs: int = 100,
                     years_per_run: int = 50,
                     strategy: SamplingStrategy = SamplingStrategy.LATIN_HYPERCUBE,
                     progress_callback: Optional[Callable[[int, int], None]] = None
                     ) -> AnalysisReport:
        """
        Выполняет полный анализ чувствительности.

        Args:
            n_runs: Количество запусков симуляции
            years_per_run: Количество лет в каждом запуске
            strategy: Стратегия семплирования параметров
            progress_callback: Функция для отслеживания прогресса (current, total)

        Returns:
            Полный отчёт анализа
        """
        # Очищаем предыдущие результаты
        self.results = []

        # Генерируем выборки параметров
        samples = self._generate_parameter_samples(n_runs, strategy)
        actual_n_runs = len(samples)

        # Запускаем симуляции
        for i, params in enumerate(samples):
            result = self.run_single(params, years_per_run, run_id=i)
            self.results.append(result)

            if progress_callback:
                progress_callback(i + 1, actual_n_runs)

        # Анализируем результаты
        self._analysis_report = self._analyze_results(
            actual_n_runs, years_per_run, strategy
        )

        return self._analysis_report

    def _analyze_results(self,
                         n_runs: int,
                         years_per_run: int,
                         strategy: SamplingStrategy) -> AnalysisReport:
        """Анализирует результаты запусков"""
        report = AnalysisReport(
            total_runs=n_runs,
            simulation_years_per_run=years_per_run,
            sampling_strategy=strategy,
            parameters_analyzed=list(self.parameters.keys()),
            outcomes_tracked=list(self.outcomes.keys())
        )

        # Считаем успешные/неуспешные запуски
        report.successful_runs = sum(1 for r in self.results if r.success)
        report.failed_runs = sum(1 for r in self.results if not r.success)
        report.total_wall_time = sum(r.wall_time_seconds for r in self.results)

        # Фильтруем только успешные для анализа
        successful_results = [r for r in self.results if r.success]

        if not successful_results:
            report.key_findings.append("Все запуски завершились с ошибками")
            return report

        # Статистика параметров
        for param_name in self.parameters:
            values = [r.parameters.get(param_name, 0) for r in successful_results]
            # Преобразуем в числа если возможно
            try:
                numeric_values = [float(v) if not isinstance(v, bool) else (1.0 if v else 0.0)
                                  for v in values]
                report.parameter_statistics[param_name] = {
                    "mean": statistics.mean(numeric_values),
                    "std": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0.0,
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                }
            except (TypeError, ValueError):
                pass

        # Статистика метрик
        for outcome_name in self.outcomes:
            values = [r.outcomes.get(outcome_name, float('nan'))
                      for r in successful_results]
            # Убираем NaN
            clean_values = [v for v in values if not math.isnan(v)]
            if clean_values:
                report.outcome_statistics[outcome_name] = {
                    "mean": statistics.mean(clean_values),
                    "std": statistics.stdev(clean_values) if len(clean_values) > 1 else 0.0,
                    "min": min(clean_values),
                    "max": max(clean_values),
                    "valid_count": len(clean_values),
                }

        # Вычисляем корреляции параметр-метрика
        report.correlation_matrix = self._compute_correlations(successful_results)

        # Анализ чувствительности для каждого параметра
        for param_name in self.parameters:
            sensitivity = self._analyze_parameter_sensitivity(
                param_name, successful_results
            )
            report.sensitivity_results[param_name] = sensitivity

        # Ранжируем параметры по важности
        report.parameter_ranking = sorted(
            [(name, sr.importance_index)
             for name, sr in report.sensitivity_results.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # Генерируем ключевые находки
        report.key_findings = self._generate_findings(report)

        return report

    def _compute_correlations(self,
                               results: List[RunResult]
                               ) -> Dict[str, Dict[str, float]]:
        """Вычисляет корреляционную матрицу параметр-метрика"""
        matrix = {}

        for param_name, param_spec in self.parameters.items():
            matrix[param_name] = {}

            # Получаем значения параметра
            param_values = []
            for r in results:
                val = r.parameters.get(param_name)
                if isinstance(val, bool):
                    val = 1.0 if val else 0.0
                elif param_spec.param_type == ParameterType.CATEGORICAL:
                    # Для категорий пропускаем корреляцию
                    continue
                try:
                    param_values.append(float(val))
                except (TypeError, ValueError):
                    param_values.append(0.0)

            if not param_values:
                continue

            for outcome_name in self.outcomes:
                outcome_values = [
                    r.outcomes.get(outcome_name, float('nan'))
                    for r in results
                ]

                # Корреляция Пирсона
                corr = self._pearson_correlation(param_values, outcome_values)
                matrix[param_name][outcome_name] = corr

        return matrix

    def _pearson_correlation(self,
                              x: List[float],
                              y: List[float]) -> float:
        """Вычисляет коэффициент корреляции Пирсона"""
        # Убираем пары с NaN
        pairs = [(xi, yi) for xi, yi in zip(x, y)
                 if not (math.isnan(xi) or math.isnan(yi))]

        if len(pairs) < 3:
            return 0.0

        x_clean = [p[0] for p in pairs]
        y_clean = [p[1] for p in pairs]

        n = len(pairs)
        mean_x = sum(x_clean) / n
        mean_y = sum(y_clean) / n

        # Ковариация и стандартные отклонения
        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in pairs) / n
        std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x_clean) / n)
        std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y_clean) / n)

        if std_x == 0 or std_y == 0:
            return 0.0

        return cov / (std_x * std_y)

    def _analyze_parameter_sensitivity(self,
                                        param_name: str,
                                        results: List[RunResult]
                                        ) -> SensitivityResult:
        """Анализирует чувствительность для одного параметра"""
        sensitivity = SensitivityResult(parameter_name=param_name)

        param_spec = self.parameters[param_name]

        # Получаем значения параметра
        param_values = []
        for r in results:
            val = r.parameters.get(param_name)
            if isinstance(val, bool):
                val = 1.0 if val else 0.0
            elif param_spec.param_type == ParameterType.CATEGORICAL:
                # Для категорий используем индекс
                try:
                    val = param_spec.categories.index(val)
                except ValueError:
                    val = 0
            try:
                param_values.append(float(val))
            except (TypeError, ValueError):
                param_values.append(0.0)

        if not param_values:
            return sensitivity

        # Для каждой метрики вычисляем корреляцию
        for outcome_name in self.outcomes:
            outcome_values = [
                r.outcomes.get(outcome_name, float('nan'))
                for r in results
            ]

            corr = self._pearson_correlation(param_values, outcome_values)
            sensitivity.correlations[outcome_name] = corr

            # Приближённая значимость (требует > 30 наблюдений)
            n = len([v for v in outcome_values if not math.isnan(v)])
            if n > 3 and abs(corr) > 0:
                t_stat = corr * math.sqrt((n - 2) / (1 - corr ** 2 + 1e-10))
                # Упрощённая p-value (не точная, но индикативная)
                sensitivity.significance[outcome_name] = min(1.0, 2.0 / (1 + abs(t_stat)))

        sensitivity.calculate_importance()
        return sensitivity

    def _generate_findings(self, report: AnalysisReport) -> List[str]:
        """Генерирует текстовые выводы из анализа"""
        findings = []

        # Самые важные параметры
        if report.parameter_ranking:
            top_params = report.parameter_ranking[:3]
            if top_params[0][1] > 0.3:
                findings.append(
                    f"Наиболее влиятельный параметр: {top_params[0][0]} "
                    f"(индекс важности: {top_params[0][1]:.2f})"
                )

        # Сильные корреляции
        for param_name, correlations in report.correlation_matrix.items():
            for outcome_name, corr in correlations.items():
                if abs(corr) > 0.7:
                    direction = "положительно" if corr > 0 else "отрицательно"
                    findings.append(
                        f"Сильная корреляция: {param_name} {direction} "
                        f"влияет на {outcome_name} (r={corr:.2f})"
                    )

        # Метрики с высокой вариабельностью
        for outcome_name, stats in report.outcome_statistics.items():
            if stats.get("mean", 0) > 0:
                cv = stats.get("std", 0) / stats.get("mean", 1)
                if cv > 0.5:
                    findings.append(
                        f"Высокая вариабельность: {outcome_name} "
                        f"(коэффициент вариации: {cv:.0%})"
                    )

        # Успешность запусков
        if report.failed_runs > 0:
            failure_rate = report.failed_runs / report.total_runs
            if failure_rate > 0.1:
                findings.append(
                    f"Внимание: {failure_rate:.0%} запусков завершились ошибкой"
                )

        return findings

    def get_report(self) -> Optional[AnalysisReport]:
        """Возвращает последний отчёт анализа"""
        return self._analysis_report

    def get_results(self) -> List[RunResult]:
        """Возвращает все результаты запусков"""
        return self.results

    def get_correlation_for_outcome(self,
                                     outcome_name: str
                                     ) -> Dict[str, float]:
        """
        Возвращает корреляции всех параметров с заданной метрикой.

        Полезно для ответа на вопрос: "Что влияет на X?"
        """
        if not self._analysis_report:
            return {}

        correlations = {}
        for param_name in self.parameters:
            if param_name in self._analysis_report.correlation_matrix:
                corr = self._analysis_report.correlation_matrix[param_name].get(
                    outcome_name, 0.0
                )
                correlations[param_name] = corr

        # Сортируем по абсолютному значению
        return dict(sorted(
            correlations.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        ))

    def get_parameter_effects(self,
                               param_name: str
                               ) -> Dict[str, float]:
        """
        Возвращает влияние параметра на все метрики.

        Полезно для ответа на вопрос: "На что влияет X?"
        """
        if not self._analysis_report:
            return {}

        if param_name in self._analysis_report.correlation_matrix:
            return self._analysis_report.correlation_matrix[param_name]

        return {}

    def get_text_report(self) -> str:
        """Возвращает текстовый отчёт анализа"""
        if not self._analysis_report:
            return "Анализ не выполнен. Запустите run_analysis() сначала."

        report = self._analysis_report
        lines = [
            "=" * 60,
            "ОТЧЁТ АНАЛИЗА ЧУВСТВИТЕЛЬНОСТИ ПАРАМЕТРОВ",
            "=" * 60,
            "",
            "--- Конфигурация ---",
            f"Всего запусков: {report.total_runs}",
            f"Успешных: {report.successful_runs}",
            f"Неуспешных: {report.failed_runs}",
            f"Лет на запуск: {report.simulation_years_per_run}",
            f"Стратегия семплирования: {report.sampling_strategy.russian_name}",
            f"Общее время: {report.total_wall_time:.1f} сек",
            "",
            f"Параметров: {len(report.parameters_analyzed)}",
            f"Метрик: {len(report.outcomes_tracked)}",
            "",
            "--- Ранжирование параметров по важности ---",
        ]

        for i, (name, importance) in enumerate(report.parameter_ranking[:10], 1):
            spec = self.parameters.get(name)
            desc = spec.description if spec else ""
            lines.append(f"{i}. {name}: {importance:.3f} - {desc}")

        lines.extend(["", "--- Ключевые находки ---"])
        for finding in report.key_findings:
            lines.append(f"• {finding}")

        if not report.key_findings:
            lines.append("(нет значимых находок)")

        lines.extend(["", "--- Статистика метрик ---"])
        for outcome_name, stats in report.outcome_statistics.items():
            spec = self.outcomes.get(outcome_name)
            desc = spec.description if spec else ""
            lines.append(
                f"• {outcome_name}: среднее={stats.get('mean', 0):.2f}, "
                f"std={stats.get('std', 0):.2f} - {desc}"
            )

        lines.extend(["", "--- Сильные корреляции (|r| > 0.5) ---"])
        found_strong = False
        for param_name, correlations in report.correlation_matrix.items():
            for outcome_name, corr in correlations.items():
                if abs(corr) > 0.5:
                    found_strong = True
                    sign = "+" if corr > 0 else ""
                    lines.append(f"• {param_name} → {outcome_name}: r={sign}{corr:.2f}")

        if not found_strong:
            lines.append("(нет корреляций |r| > 0.5)")

        lines.extend(["", "=" * 60])

        return "\n".join(lines)

    def export_results_csv(self, filepath: str) -> None:
        """Экспортирует результаты в CSV файл"""
        if not self.results:
            return

        import csv

        # Собираем все ключи
        param_keys = sorted(self.parameters.keys())
        outcome_keys = sorted(self.outcomes.keys())

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Заголовок
            header = ['run_id', 'success', 'years', 'wall_time'] + \
                     [f'param_{k}' for k in param_keys] + \
                     [f'outcome_{k}' for k in outcome_keys]
            writer.writerow(header)

            # Данные
            for result in self.results:
                row = [
                    result.run_id,
                    result.success,
                    result.simulation_years,
                    result.wall_time_seconds
                ]
                row.extend([result.parameters.get(k, '') for k in param_keys])
                row.extend([result.outcomes.get(k, '') for k in outcome_keys])
                writer.writerow(row)

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику для внешнего использования"""
        if not self._analysis_report:
            return {"status": "not_run"}

        return {
            "status": "completed",
            "total_runs": self._analysis_report.total_runs,
            "successful_runs": self._analysis_report.successful_runs,
            "failed_runs": self._analysis_report.failed_runs,
            "parameters_count": len(self.parameters),
            "outcomes_count": len(self.outcomes),
            "top_parameters": self._analysis_report.parameter_ranking[:5],
            "key_findings_count": len(self._analysis_report.key_findings),
        }
