"""
Культурная система - НАДСТРОЙКА по Марксу.

Надстройка отражает и закрепляет экономический базис:
- Верования оправдывают существующий порядок
- Традиции закрепляют отношения
- Нормы регулируют поведение
"""
from .beliefs import Belief, BeliefSystem, BeliefType
from .traditions import Tradition, TraditionSystem
from .norms import SocialNorm, NormSystem

__all__ = [
    'Belief', 'BeliefSystem', 'BeliefType',
    'Tradition', 'TraditionSystem',
    'SocialNorm', 'NormSystem',
]
