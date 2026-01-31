"""
Система социальных норм - правила поведения.

Нормы отражают экономические отношения:
- Нормы собственности защищают владельцев
- Нормы труда регулируют эксплуатацию
- Нормы семьи определяют наследование
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set
from enum import Enum, auto


class NormType(Enum):
    """Типы норм"""
    PROPERTY = "собственность"
    LABOR = "труд"
    FAMILY = "семья"
    VIOLENCE = "насилие"
    SHARING = "распределение"
    AUTHORITY = "власть"


@dataclass
class SocialNorm:
    """Социальная норма"""
    id: str
    name: str
    norm_type: NormType
    description: str

    # Кому выгодна
    benefits_class: str = ""

    # Санкции за нарушение
    punishment_severity: float = 0.5  # 0-1

    # Насколько соблюдается
    compliance_rate: float = 0.8

    year_established: int = 0


class NormSystem:
    """Система социальных норм"""

    def __init__(self):
        self.norms: Dict[str, SocialNorm] = {}

        # Базовые нормы примитивной общины
        self._init_primitive_norms()

    def _init_primitive_norms(self) -> None:
        """Инициализирует базовые нормы"""
        # Норма взаимопомощи
        self.norms["mutual_aid"] = SocialNorm(
            id="mutual_aid",
            name="взаимопомощь",
            norm_type=NormType.SHARING,
            description="Члены общины помогают друг другу",
            punishment_severity=0.3,
        )

        # Запрет на насилие внутри общины
        self.norms["no_internal_violence"] = SocialNorm(
            id="no_internal_violence",
            name="мир внутри общины",
            norm_type=NormType.VIOLENCE,
            description="Насилие против своих недопустимо",
            punishment_severity=0.8,
        )

    def add_property_norm(self, year: int) -> SocialNorm:
        """Добавляет норму защиты собственности"""
        norm = SocialNorm(
            id="property_protection",
            name="защита владения",
            norm_type=NormType.PROPERTY,
            description="Чужое имущество неприкосновенно",
            benefits_class="LANDOWNER",
            punishment_severity=0.7,
            year_established=year,
        )
        self.norms[norm.id] = norm
        return norm

    def check_norm_violation(self, action: str, actor_class: str) -> tuple:
        """
        Проверяет нарушение нормы.
        Возвращает (нарушена_ли, какая_норма, серьёзность)
        """
        violation_map = {
            "theft": "property_protection",
            "violence": "no_internal_violence",
            "refusing_help": "mutual_aid",
        }

        norm_id = violation_map.get(action)
        if norm_id and norm_id in self.norms:
            norm = self.norms[norm_id]
            return True, norm, norm.punishment_severity

        return False, None, 0

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику"""
        return {
            "total_norms": len(self.norms),
            "by_type": {
                n.norm_type.value: n.name
                for n in self.norms.values()
            }
        }
