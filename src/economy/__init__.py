"""
Экономическая система - БАЗИС по Марксу.

Производительные силы + производственные отношения = экономический базис.
Базис определяет надстройку (культуру, политику, идеологию).
"""
from .resources import Resource, ResourceType, Inventory
from .production import Production, ProductionMethod, LaborType
from .technology import Technology, KnowledgeSystem, TechCategory, TechEra, TECHNOLOGIES
from .property import PropertyRight, PropertyType, PropertyCategory, OwnershipSystem

__all__ = [
    'Resource', 'ResourceType', 'Inventory',
    'Production', 'ProductionMethod', 'LaborType',
    'Technology', 'KnowledgeSystem', 'TechCategory', 'TechEra', 'TECHNOLOGIES',
    'PropertyRight', 'PropertyType', 'PropertyCategory', 'OwnershipSystem',
]
