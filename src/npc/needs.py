"""
Система потребностей NPC - управляет базовыми нуждами персонажей.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable
import random


class Need(Enum):
    """Типы потребностей NPC"""
    HUNGER = "голод"
    ENERGY = "энергия"
    SOCIAL = "общение"
    FUN = "развлечение"
    COMFORT = "комфорт"
    HYGIENE = "гигиена"
    SAFETY = "безопасность"
    PURPOSE = "цель"  # Потребность в смысле жизни


@dataclass
class NeedState:
    """Состояние отдельной потребности"""
    value: float = 100.0  # 0-100, где 100 = полностью удовлетворена
    decay_rate: float = 1.0  # Скорость уменьшения за игровой час
    priority_weight: float = 1.0  # Важность этой потребности

    def decay(self, hours: float = 1.0) -> None:
        """Уменьшает значение потребности со временем"""
        self.value = max(0, self.value - self.decay_rate * hours)

    def satisfy(self, amount: float) -> None:
        """Удовлетворяет потребность на заданное значение"""
        self.value = min(100, self.value + amount)

    def is_critical(self) -> bool:
        """Проверяет, находится ли потребность в критическом состоянии"""
        return self.value < 20

    def is_low(self) -> bool:
        """Проверяет, находится ли потребность на низком уровне"""
        return self.value < 40

    def get_urgency(self) -> float:
        """Возвращает срочность удовлетворения (0-1)"""
        return (100 - self.value) / 100 * self.priority_weight


@dataclass
class Needs:
    """Менеджер всех потребностей NPC"""

    states: Dict[Need, NeedState] = field(default_factory=dict)

    def __post_init__(self):
        if not self.states:
            self._initialize_defaults()

    def _initialize_defaults(self):
        """Инициализирует потребности значениями по умолчанию"""
        defaults = {
            Need.HUNGER: NeedState(value=80, decay_rate=3.0, priority_weight=1.5),
            Need.ENERGY: NeedState(value=100, decay_rate=2.5, priority_weight=1.4),
            Need.SOCIAL: NeedState(value=70, decay_rate=1.5, priority_weight=1.0),
            Need.FUN: NeedState(value=60, decay_rate=2.0, priority_weight=0.8),
            Need.COMFORT: NeedState(value=70, decay_rate=1.0, priority_weight=0.7),
            Need.HYGIENE: NeedState(value=90, decay_rate=1.5, priority_weight=0.9),
            Need.SAFETY: NeedState(value=100, decay_rate=0.5, priority_weight=2.0),
            Need.PURPOSE: NeedState(value=50, decay_rate=0.3, priority_weight=1.2),
        }
        self.states = defaults

    def get(self, need: Need) -> NeedState:
        """Возвращает состояние потребности"""
        return self.states.get(need, NeedState())

    def decay_all(self, hours: float = 1.0) -> None:
        """Уменьшает все потребности со временем"""
        for state in self.states.values():
            state.decay(hours)

    def satisfy(self, need: Need, amount: float) -> None:
        """Удовлетворяет конкретную потребность"""
        if need in self.states:
            self.states[need].satisfy(amount)

    def get_most_urgent(self) -> Optional[Need]:
        """Возвращает самую срочную потребность"""
        if not self.states:
            return None

        return max(
            self.states.keys(),
            key=lambda n: self.states[n].get_urgency()
        )

    def get_critical_needs(self) -> list:
        """Возвращает список критических потребностей"""
        return [
            need for need, state in self.states.items()
            if state.is_critical()
        ]

    def get_low_needs(self) -> list:
        """Возвращает список низких потребностей"""
        return [
            need for need, state in self.states.items()
            if state.is_low()
        ]

    def get_overall_happiness(self) -> float:
        """Возвращает общий уровень счастья (0-100)"""
        if not self.states:
            return 50.0

        total_weighted = sum(
            state.value * state.priority_weight
            for state in self.states.values()
        )
        total_weight = sum(
            state.priority_weight
            for state in self.states.values()
        )

        return total_weighted / total_weight if total_weight > 0 else 50.0

    def get_mood(self) -> str:
        """Возвращает текстовое описание настроения"""
        happiness = self.get_overall_happiness()

        if happiness >= 80:
            return "счастлив"
        elif happiness >= 60:
            return "доволен"
        elif happiness >= 40:
            return "нормально"
        elif happiness >= 20:
            return "недоволен"
        else:
            return "несчастен"

    def describe_state(self) -> str:
        """Возвращает описание текущего состояния"""
        critical = self.get_critical_needs()
        if critical:
            needs_text = ", ".join(n.value for n in critical)
            return f"срочно нуждается в: {needs_text}"

        low = self.get_low_needs()
        if low:
            needs_text = ", ".join(n.value for n in low)
            return f"хочет: {needs_text}"

        return self.get_mood()

    @classmethod
    def generate_random(cls) -> 'Needs':
        """Создаёт потребности со случайными начальными значениями"""
        needs = cls()
        for need, state in needs.states.items():
            # Случайное начальное значение с учётом типа потребности
            base = random.randint(40, 90)
            state.value = base
            # Небольшая вариация в скорости decay
            state.decay_rate *= random.uniform(0.8, 1.2)
        return needs
