"""
Система отношений между NPC - управляет социальными связями.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from .character import NPC


class RelationType(Enum):
    """Типы отношений"""
    STRANGER = "незнакомец"
    ACQUAINTANCE = "знакомый"
    FRIEND = "друг"
    CLOSE_FRIEND = "близкий друг"
    BEST_FRIEND = "лучший друг"
    ROMANTIC = "романтические"
    PARTNER = "партнёр"
    SPOUSE = "супруг"
    RIVAL = "соперник"
    ENEMY = "враг"
    FAMILY = "семья"
    COLLEAGUE = "коллега"
    MENTOR = "наставник"
    STUDENT = "ученик"


@dataclass
class Relationship:
    """Отношения между двумя NPC"""

    target_id: str  # ID другого NPC

    # Основные показатели (-100 до 100)
    friendship: float = 0.0  # Дружба
    romance: float = 0.0     # Романтика
    respect: float = 0.0     # Уважение
    trust: float = 0.0       # Доверие

    # История взаимодействий
    interactions_count: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0

    # Память о событиях
    memories: List[str] = field(default_factory=list)

    # Текущий тип отношений
    relationship_type: RelationType = RelationType.STRANGER

    def get_overall_opinion(self) -> float:
        """Возвращает общее мнение о персонаже (-100 до 100)"""
        return (
            self.friendship * 0.4 +
            self.respect * 0.3 +
            self.trust * 0.3
        )

    def modify(self,
               friendship: float = 0,
               romance: float = 0,
               respect: float = 0,
               trust: float = 0) -> None:
        """Изменяет показатели отношений"""
        self.friendship = max(-100, min(100, self.friendship + friendship))
        self.romance = max(-100, min(100, self.romance + romance))
        self.respect = max(-100, min(100, self.respect + respect))
        self.trust = max(-100, min(100, self.trust + trust))

        self._update_relationship_type()

    def record_interaction(self, positive: bool, memory: Optional[str] = None) -> None:
        """Записывает взаимодействие"""
        self.interactions_count += 1
        if positive:
            self.positive_interactions += 1
        else:
            self.negative_interactions += 1

        if memory:
            self.memories.append(memory)
            # Храним только последние 10 воспоминаний
            if len(self.memories) > 10:
                self.memories.pop(0)

    def _update_relationship_type(self) -> None:
        """Обновляет тип отношений на основе показателей"""
        opinion = self.get_overall_opinion()

        # Романтические отношения имеют приоритет
        if self.romance > 70 and self.friendship > 50:
            if self.trust > 80:
                self.relationship_type = RelationType.SPOUSE
            elif self.trust > 60:
                self.relationship_type = RelationType.PARTNER
            else:
                self.relationship_type = RelationType.ROMANTIC
            return

        # Враждебные отношения
        if opinion < -60:
            self.relationship_type = RelationType.ENEMY
            return
        elif opinion < -30:
            self.relationship_type = RelationType.RIVAL
            return

        # Дружеские отношения
        if self.friendship > 80 and self.trust > 70:
            self.relationship_type = RelationType.BEST_FRIEND
        elif self.friendship > 60:
            self.relationship_type = RelationType.CLOSE_FRIEND
        elif self.friendship > 30:
            self.relationship_type = RelationType.FRIEND
        elif self.interactions_count > 3:
            self.relationship_type = RelationType.ACQUAINTANCE
        else:
            self.relationship_type = RelationType.STRANGER

    def decay(self, days: float = 1.0) -> None:
        """Отношения слегка угасают без взаимодействия"""
        decay_rate = 0.1 * days

        # Отношения стремятся к нейтральному состоянию
        if self.friendship > 0:
            self.friendship = max(0, self.friendship - decay_rate)
        elif self.friendship < 0:
            self.friendship = min(0, self.friendship + decay_rate)

        if self.romance > 0:
            self.romance = max(0, self.romance - decay_rate * 1.5)

        # Доверие и уважение более стабильны
        if abs(self.trust) > 50:
            self.trust *= 0.99
        if abs(self.respect) > 50:
            self.respect *= 0.99

    def describe(self) -> str:
        """Возвращает описание отношений"""
        opinion = self.get_overall_opinion()

        if opinion > 50:
            feeling = "очень хорошо относится"
        elif opinion > 20:
            feeling = "хорошо относится"
        elif opinion > -20:
            feeling = "нейтрально относится"
        elif opinion > -50:
            feeling = "недолюбливает"
        else:
            feeling = "ненавидит"

        return f"{self.relationship_type.value} ({feeling})"


@dataclass
class RelationshipManager:
    """Менеджер всех отношений NPC"""

    owner_id: str
    relationships: Dict[str, Relationship] = field(default_factory=dict)

    def get_or_create(self, target_id: str) -> Relationship:
        """Получает или создаёт отношения с другим NPC"""
        if target_id not in self.relationships:
            self.relationships[target_id] = Relationship(target_id=target_id)
        return self.relationships[target_id]

    def get(self, target_id: str) -> Optional[Relationship]:
        """Получает отношения, если они существуют"""
        return self.relationships.get(target_id)

    def has_relationship(self, target_id: str) -> bool:
        """Проверяет, есть ли отношения с NPC"""
        return target_id in self.relationships

    def get_friends(self) -> List[str]:
        """Возвращает список ID друзей"""
        return [
            rel.target_id for rel in self.relationships.values()
            if rel.friendship > 30
        ]

    def get_enemies(self) -> List[str]:
        """Возвращает список ID врагов"""
        return [
            rel.target_id for rel in self.relationships.values()
            if rel.get_overall_opinion() < -30
        ]

    def get_romantic_interests(self) -> List[str]:
        """Возвращает список романтических интересов"""
        return [
            rel.target_id for rel in self.relationships.values()
            if rel.romance > 30
        ]

    def get_best_friend(self) -> Optional[str]:
        """Возвращает ID лучшего друга"""
        friends = [
            (rel.target_id, rel.friendship)
            for rel in self.relationships.values()
            if rel.friendship > 50
        ]
        if friends:
            return max(friends, key=lambda x: x[1])[0]
        return None

    def decay_all(self, days: float = 1.0) -> None:
        """Применяет угасание ко всем отношениям"""
        for rel in self.relationships.values():
            rel.decay(days)

    def get_social_circle_size(self) -> int:
        """Возвращает размер социального круга"""
        return len([
            r for r in self.relationships.values()
            if r.interactions_count > 3
        ])

    def describe_social_life(self) -> str:
        """Описывает социальную жизнь NPC"""
        friends = len(self.get_friends())
        enemies = len(self.get_enemies())
        romantic = len(self.get_romantic_interests())

        parts = []
        if friends > 0:
            parts.append(f"{friends} друзей")
        if enemies > 0:
            parts.append(f"{enemies} врагов")
        if romantic > 0:
            parts.append(f"{romantic} романтических интересов")

        if parts:
            return "Имеет " + ", ".join(parts)
        return "Одиночка"
