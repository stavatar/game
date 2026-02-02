"""
Демографическая система - рождение, смерть, старение.

Демография зависит от:
- Экономических условий (достаток → больше детей)
- Климата и здоровья
- Социальных норм
- Уровня развития
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum, auto
import random
import math


class LifeStage(Enum):
    """Этапы жизни"""
    INFANT = ("младенец", 0, 2)
    CHILD = ("ребёнок", 2, 12)
    ADOLESCENT = ("подросток", 12, 16)
    YOUNG_ADULT = ("молодой", 16, 30)
    ADULT = ("взрослый", 30, 50)
    ELDER = ("старик", 50, 100)

    def __init__(self, russian_name: str, min_age: int, max_age: int):
        self.russian_name = russian_name
        self.min_age = min_age
        self.max_age = max_age

    @classmethod
    def from_age(cls, age: int) -> 'LifeStage':
        for stage in cls:
            if stage.min_age <= age < stage.max_age:
                return stage
        return cls.ELDER


class DeathCause(Enum):
    """Причины смерти"""
    OLD_AGE = "старость"
    DISEASE = "болезнь"
    STARVATION = "голод"
    ACCIDENT = "несчастный случай"
    VIOLENCE = "насилие"
    CHILDBIRTH = "роды"
    INFANT_MORTALITY = "младенческая смертность"
    COLD = "переохлаждение"
    PREDATOR = "хищник"


@dataclass
class LifeEvent:
    """Событие в жизни NPC"""
    event_type: str
    year: int
    age: int
    description: str
    related_npc_ids: List[str] = field(default_factory=list)


@dataclass
class DemographicFactors:
    """Факторы, влияющие на демографию"""
    food_availability: float = 1.0      # Доступность еды (0-2)
    health_conditions: float = 1.0      # Здоровье населения (0-1)
    safety: float = 1.0                 # Безопасность (0-1)
    technology_level: float = 0.0       # Уровень развития (влияет на медицину)
    social_stability: float = 1.0       # Социальная стабильность


class DemographySystem:
    """
    Система демографии.

    Управляет:
    - Рождаемостью
    - Смертностью
    - Старением
    - Жизненными событиями
    """

    def __init__(self):
        # Базовые параметры
        self.base_fertility_rate: float = 0.15     # Вероятность зачатия в год
        self.base_infant_mortality: float = 0.2    # Детская смертность
        self.base_life_expectancy: float = 45      # Ожидаемая продолжительность жизни

        # Текущие факторы
        self.factors = DemographicFactors()

        # Статистика
        self.births_this_year: int = 0
        self.deaths_this_year: int = 0
        self.population_history: List[Tuple[int, int]] = []  # (год, население)

    def update_factors(self,
                       food: float = None,
                       health: float = None,
                       safety: float = None,
                       tech: float = None,
                       stability: float = None) -> None:
        """Обновляет демографические факторы"""
        if food is not None:
            self.factors.food_availability = max(0, min(2, food))
        if health is not None:
            self.factors.health_conditions = max(0, min(1, health))
        if safety is not None:
            self.factors.safety = max(0, min(1, safety))
        if tech is not None:
            self.factors.technology_level = max(0, tech)
        if stability is not None:
            self.factors.social_stability = max(0, min(1, stability))

    def calculate_fertility(self, age: int, is_female: bool,
                            has_partner: bool,
                            personal_health: float = 1.0) -> float:
        """
        Вычисляет вероятность зачатия.

        Зависит от:
        - Возраста
        - Наличия партнёра
        - Здоровья
        - Экономических условий
        """
        if not is_female or not has_partner:
            return 0.0

        # Возрастные границы фертильности
        if age < 16 or age > 45:
            return 0.0

        # Базовая вероятность с учётом возраста
        # Пик в 20-30 лет
        if age < 20:
            age_factor = 0.5
        elif age < 30:
            age_factor = 1.0
        elif age < 40:
            age_factor = 0.7
        else:
            age_factor = 0.3

        fertility = self.base_fertility_rate * age_factor

        # Влияние еды (голод снижает фертильность)
        food_factor = min(1.0, self.factors.food_availability)
        if food_factor < 0.5:
            fertility *= food_factor * 0.5
        else:
            fertility *= (0.25 + food_factor * 0.75)

        # Здоровье
        fertility *= personal_health * self.factors.health_conditions

        # Социальная стабильность
        fertility *= (0.5 + self.factors.social_stability * 0.5)

        return fertility

    def check_conception(self, mother_age: int, father_age: int,
                         mother_health: float = 1.0) -> bool:
        """Проверяет, произошло ли зачатие"""
        fertility = self.calculate_fertility(
            mother_age, True, True, mother_health
        )
        return random.random() < fertility

    def calculate_mortality(self, age: int, life_stage: LifeStage,
                            health: float = 1.0,
                            is_starving: bool = False) -> Tuple[float, DeathCause]:
        """
        Вычисляет вероятность смерти.

        Возвращает (вероятность, наиболее вероятная причина)
        """
        # Базовая смертность по возрасту (кривая Гомперца)
        base_mortality = 0.001 * math.exp(0.08 * age)

        # Детская смертность
        if life_stage == LifeStage.INFANT:
            base_mortality = self.base_infant_mortality
            # Снижается с развитием
            base_mortality *= (1 - self.factors.technology_level * 0.1)
            primary_cause = DeathCause.INFANT_MORTALITY

        elif life_stage == LifeStage.CHILD:
            base_mortality = 0.02
            primary_cause = DeathCause.DISEASE

        elif life_stage == LifeStage.ELDER:
            base_mortality = max(0.05, base_mortality)
            primary_cause = DeathCause.OLD_AGE

        else:
            primary_cause = DeathCause.DISEASE

        # Модификаторы

        # Голод
        if is_starving:
            base_mortality += 0.1
            primary_cause = DeathCause.STARVATION

        # Здоровье
        if health < 0.5:
            base_mortality *= (2 - health)
            if primary_cause != DeathCause.STARVATION:
                primary_cause = DeathCause.DISEASE

        # Безопасность
        if self.factors.safety < 0.5:
            accident_risk = 0.02 * (1 - self.factors.safety)
            base_mortality += accident_risk
            if random.random() < 0.3:
                primary_cause = DeathCause.ACCIDENT

        # Здоровье населения (эпидемии и т.д.)
        if self.factors.health_conditions < 0.7:
            base_mortality *= (1.5 - self.factors.health_conditions * 0.5)

        # Технологии снижают смертность
        tech_reduction = min(0.5, self.factors.technology_level * 0.05)
        base_mortality *= (1 - tech_reduction)

        return min(1.0, base_mortality), primary_cause

    def check_death(self, age: int, health: float = 1.0,
                    is_starving: bool = False) -> Tuple[bool, Optional[DeathCause]]:
        """
        Проверяет, умирает ли NPC.

        Возвращает (умер, причина)
        """
        life_stage = LifeStage.from_age(age)
        mortality, cause = self.calculate_mortality(
            age, life_stage, health, is_starving
        )

        if random.random() < mortality:
            return True, cause
        return False, None

    def check_childbirth_death(self, mother_age: int,
                               mother_health: float = 1.0) -> bool:
        """Проверяет смерть при родах"""
        # Базовый риск ~5% в примитивных условиях
        base_risk = 0.05

        # Возраст
        if mother_age < 18 or mother_age > 40:
            base_risk *= 1.5

        # Здоровье
        base_risk *= (2 - mother_health)

        # Технологии снижают риск
        base_risk *= (1 - min(0.8, self.factors.technology_level * 0.1))

        return random.random() < base_risk

    def calculate_life_expectancy(self) -> float:
        """Вычисляет текущую ожидаемую продолжительность жизни"""
        base = self.base_life_expectancy

        # Еда
        if self.factors.food_availability < 0.8:
            base *= (0.5 + self.factors.food_availability * 0.5)

        # Здоровье
        base *= (0.7 + self.factors.health_conditions * 0.3)

        # Безопасность
        base *= (0.8 + self.factors.safety * 0.2)

        # Технологии
        base += self.factors.technology_level * 5

        return base

    def get_reproduction_advice(self, population: int,
                                food_per_person: float) -> str:
        """Даёт рекомендации по воспроизводству"""
        if food_per_person < 0.5:
            return "Голод угрожает выживанию. Рождаемость снижена."
        elif food_per_person < 1.0:
            return "Еды хватает впритык. Умеренная рождаемость."
        elif food_per_person > 1.5:
            return "Достаток еды. Благоприятные условия для роста."
        else:
            return "Стабильные условия."

    def record_death(self, year: int, cause: str = "") -> None:
        """
        Записывает смерть в статистику.

        Args:
            year: Год смерти
            cause: Причина смерти (опционально)
        """
        self.deaths_this_year += 1

    def record_birth(self, year: int) -> None:
        """
        Записывает рождение в статистику.

        Args:
            year: Год рождения
        """
        self.births_this_year += 1

    def record_year_end(self, year: int, population: int) -> None:
        """Записывает статистику на конец года"""
        self.population_history.append((year, population))
        self.births_this_year = 0
        self.deaths_this_year = 0

    def get_population_growth_rate(self) -> float:
        """Вычисляет темп роста населения"""
        if len(self.population_history) < 2:
            return 0.0

        current = self.population_history[-1][1]
        previous = self.population_history[-2][1]

        if previous == 0:
            return 0.0

        return (current - previous) / previous

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает демографическую статистику"""
        return {
            "births_this_year": self.births_this_year,
            "deaths_this_year": self.deaths_this_year,
            "life_expectancy": round(self.calculate_life_expectancy(), 1),
            "growth_rate": round(self.get_population_growth_rate() * 100, 1),
            "factors": {
                "food": self.factors.food_availability,
                "health": self.factors.health_conditions,
                "safety": self.factors.safety,
            }
        }
