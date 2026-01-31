"""
Система личности NPC - определяет уникальный характер каждого персонажа.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List
import random


class Trait(Enum):
    """Черты характера NPC"""
    # Социальные черты
    EXTROVERT = "экстраверт"
    INTROVERT = "интроверт"
    FRIENDLY = "дружелюбный"
    HOSTILE = "враждебный"
    CHARISMATIC = "харизматичный"
    AWKWARD = "неловкий"

    # Эмоциональные черты
    CHEERFUL = "весёлый"
    MELANCHOLIC = "меланхоличный"
    CALM = "спокойный"
    HOTHEAD = "вспыльчивый"
    BRAVE = "храбрый"
    COWARD = "трусливый"

    # Моральные черты
    HONEST = "честный"
    DECEITFUL = "лживый"
    GENEROUS = "щедрый"
    GREEDY = "жадный"
    COMPASSIONATE = "сострадательный"
    CRUEL = "жестокий"

    # Интеллектуальные черты
    CURIOUS = "любопытный"
    APATHETIC = "апатичный"
    CREATIVE = "творческий"
    PRACTICAL = "практичный"
    WISE = "мудрый"
    NAIVE = "наивный"

    # Рабочие черты
    HARDWORKING = "трудолюбивый"
    LAZY = "ленивый"
    AMBITIOUS = "амбициозный"
    CONTENT = "довольный"
    PERFECTIONIST = "перфекционист"
    CARELESS = "небрежный"


# Противоположные черты - NPC не может иметь обе одновременно
OPPOSITE_TRAITS = {
    Trait.EXTROVERT: Trait.INTROVERT,
    Trait.FRIENDLY: Trait.HOSTILE,
    Trait.CHEERFUL: Trait.MELANCHOLIC,
    Trait.CALM: Trait.HOTHEAD,
    Trait.BRAVE: Trait.COWARD,
    Trait.HONEST: Trait.DECEITFUL,
    Trait.GENEROUS: Trait.GREEDY,
    Trait.COMPASSIONATE: Trait.CRUEL,
    Trait.CURIOUS: Trait.APATHETIC,
    Trait.CREATIVE: Trait.PRACTICAL,
    Trait.WISE: Trait.NAIVE,
    Trait.HARDWORKING: Trait.LAZY,
    Trait.AMBITIOUS: Trait.CONTENT,
    Trait.PERFECTIONIST: Trait.CARELESS,
}

# Добавляем обратные связи
OPPOSITE_TRAITS.update({v: k for k, v in OPPOSITE_TRAITS.items()})


@dataclass
class Personality:
    """Личность NPC - набор черт характера и базовых атрибутов"""

    traits: List[Trait] = field(default_factory=list)

    # Базовые атрибуты личности (0-100)
    openness: int = 50          # Открытость новому опыту
    conscientiousness: int = 50  # Добросовестность
    agreeableness: int = 50      # Доброжелательность
    neuroticism: int = 50        # Невротизм (эмоциональная нестабильность)

    def __post_init__(self):
        if not self.traits:
            self.traits = self._generate_random_traits()

    def _generate_random_traits(self, count: int = 3) -> List[Trait]:
        """Генерирует случайный набор непротиворечивых черт"""
        available_traits = list(Trait)
        selected_traits = []

        while len(selected_traits) < count and available_traits:
            trait = random.choice(available_traits)
            selected_traits.append(trait)
            available_traits.remove(trait)

            # Удаляем противоположную черту из доступных
            if trait in OPPOSITE_TRAITS:
                opposite = OPPOSITE_TRAITS[trait]
                if opposite in available_traits:
                    available_traits.remove(opposite)

        return selected_traits

    def has_trait(self, trait: Trait) -> bool:
        """Проверяет наличие черты"""
        return trait in self.traits

    def add_trait(self, trait: Trait) -> bool:
        """Добавляет черту, если она не противоречит существующим"""
        if trait in self.traits:
            return False

        # Проверяем на противоречие
        if trait in OPPOSITE_TRAITS:
            if OPPOSITE_TRAITS[trait] in self.traits:
                return False

        self.traits.append(trait)
        return True

    def get_social_modifier(self) -> float:
        """Возвращает модификатор социальных взаимодействий"""
        modifier = 1.0

        if self.has_trait(Trait.EXTROVERT):
            modifier += 0.3
        if self.has_trait(Trait.INTROVERT):
            modifier -= 0.2
        if self.has_trait(Trait.FRIENDLY):
            modifier += 0.2
        if self.has_trait(Trait.CHARISMATIC):
            modifier += 0.3
        if self.has_trait(Trait.AWKWARD):
            modifier -= 0.2
        if self.has_trait(Trait.HOSTILE):
            modifier -= 0.3

        return max(0.1, modifier)

    def get_work_modifier(self) -> float:
        """Возвращает модификатор рабочей эффективности"""
        modifier = 1.0

        if self.has_trait(Trait.HARDWORKING):
            modifier += 0.3
        if self.has_trait(Trait.LAZY):
            modifier -= 0.3
        if self.has_trait(Trait.PERFECTIONIST):
            modifier += 0.2
        if self.has_trait(Trait.CARELESS):
            modifier -= 0.2
        if self.has_trait(Trait.AMBITIOUS):
            modifier += 0.1

        return max(0.1, modifier)

    def get_courage_modifier(self) -> float:
        """Возвращает модификатор смелости"""
        modifier = 1.0

        if self.has_trait(Trait.BRAVE):
            modifier += 0.4
        if self.has_trait(Trait.COWARD):
            modifier -= 0.4
        if self.has_trait(Trait.HOTHEAD):
            modifier += 0.1
        if self.has_trait(Trait.CALM):
            modifier += 0.1

        return max(0.1, modifier)

    def describe(self) -> str:
        """Возвращает текстовое описание личности"""
        if not self.traits:
            return "обычный человек"

        trait_names = [t.value for t in self.traits]
        return ", ".join(trait_names)

    @classmethod
    def generate_random(cls) -> 'Personality':
        """Создаёт случайную личность"""
        return cls(
            traits=[],  # Будут сгенерированы в __post_init__
            openness=random.randint(20, 80),
            conscientiousness=random.randint(20, 80),
            agreeableness=random.randint(20, 80),
            neuroticism=random.randint(20, 80),
        )
