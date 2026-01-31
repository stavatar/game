"""
AI-система для NPC.

Реализует BDI-архитектуру (Beliefs-Desires-Intentions):
- Убеждения - что NPC знает о мире
- Желания - цели и потребности
- Намерения - выбранные планы действий
"""
from .bdi import BDIAgent, Belief, Desire, Intention, Action

__all__ = ['BDIAgent', 'Belief', 'Desire', 'Intention', 'Action']
