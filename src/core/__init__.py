"""
Ядро симуляции - управляет всеми системами.
"""
from .config import Config
from .simulation import Simulation
from .events import Event, EventBus

__all__ = ['Config', 'Simulation', 'Event', 'EventBus']
