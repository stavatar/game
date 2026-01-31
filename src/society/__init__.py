"""
Социальная система - структура общества.

Включает:
- Семьи и родство
- Демографию
- Классовую структуру
- Конфликты
"""
from .family import Family, FamilySystem, KinshipType
from .demography import DemographySystem, LifeEvent
from .classes import SocialClass, ClassSystem

__all__ = [
    'Family', 'FamilySystem', 'KinshipType',
    'DemographySystem', 'LifeEvent',
    'SocialClass', 'ClassSystem',
]
