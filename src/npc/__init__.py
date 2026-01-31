"""
Система NPC - уникальные личности в игровом мире.

Каждый NPC имеет:
- Генетику (наследование от родителей)
- Память (воспоминания и рефлексия)
- Личность (черты характера)
- Потребности (иерархия Маслоу)
- Отношения (с другими NPC)
- AI (BDI-архитектура)
"""
from .character import NPC, Gender, Stats, Skills, Memory, Goal
from .personality import Personality, Trait
from .needs import Needs, Need
from .relationships import RelationshipManager, Relationship
from .genetics import Genome, GeneticsSystem, GeneType
from .memory import MemoryStream, MemoryEntry, MemoryType, Reflection
from .ai import BDIAgent, Belief, Desire, Intention, Action

__all__ = [
    # Основной класс
    'NPC', 'Gender', 'Stats', 'Skills', 'Memory', 'Goal',
    # Личность
    'Personality', 'Trait',
    # Потребности
    'Needs', 'Need',
    # Отношения
    'RelationshipManager', 'Relationship',
    # Генетика
    'Genome', 'GeneticsSystem', 'GeneType',
    # Память
    'MemoryStream', 'MemoryEntry', 'MemoryType', 'Reflection',
    # AI
    'BDIAgent', 'Belief', 'Desire', 'Intention', 'Action',
]
