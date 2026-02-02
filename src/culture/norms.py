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

    def get_action_constraint(self, action: str, actor_class: str) -> float:
        """
        Возвращает ограничение нормы для действия.

        Нормы ограничивают поведение:
        - Высокое значение (близкое к 1.0) = действие сильно ограничено
        - Низкое значение (близкое к 0.0) = действие разрешено
        - Класс актора влияет: нормы могут не применяться к привилегированным классам

        Returns:
            float: Степень ограничения (0.0 - нет ограничений, 1.0 - полный запрет)
        """
        # Маппинг действий на нормы, которые их ограничивают
        action_to_norm = {
            "theft": "property_protection",
            "claim_land": "property_protection",  # Захват чужой земли
            "violence": "no_internal_violence",
            "refusing_help": "mutual_aid",
            "not_sharing": "mutual_aid",
        }

        norm_id = action_to_norm.get(action)
        if not norm_id or norm_id not in self.norms:
            return 0.0  # Нет ограничений

        norm = self.norms[norm_id]

        # Базовое ограничение = серьёзность наказания * соблюдаемость
        constraint = norm.punishment_severity * norm.compliance_rate

        # Если норма выгодна классу актора, ограничение слабее
        # (нормы защищают интересы привилегированных классов)
        if norm.benefits_class and actor_class == norm.benefits_class:
            constraint *= 0.5  # Привилегированные классы менее ограничены

        return min(1.0, constraint)

    def should_help(self, actor_class: str) -> float:
        """
        Возвращает вероятность помочь другому, основанную на нормах.

        Норма mutual_aid обязывает помогать членам общины.

        Returns:
            float: Модификатор склонности помогать (0.0 - 1.0)
        """
        if "mutual_aid" not in self.norms:
            return 0.5  # Нейтральное значение

        norm = self.norms["mutual_aid"]
        # Высокая соблюдаемость = больше склонность помогать
        return norm.compliance_rate

    def can_claim_property(self, actor_class: str) -> bool:
        """
        Проверяет, можно ли захватить собственность по нормам.

        До появления нормы защиты собственности захват земли не запрещён.
        После появления - захват нарушает норму (кроме привилегированных классов).

        Returns:
            bool: True если захват разрешён нормами
        """
        if "property_protection" not in self.norms:
            return True  # Нет нормы - нет запрета

        norm = self.norms["property_protection"]

        # Если норма выгодна классу актора - захват разрешён
        # (те кто создал норму, защищают своё право владеть)
        if norm.benefits_class == actor_class:
            return True

        # Иначе захват нарушает норму
        return False

    def get_violence_tolerance(self, actor_class: str, target_internal: bool = True) -> float:
        """
        Возвращает допустимость насилия по нормам.

        Args:
            actor_class: Класс актора
            target_internal: True если цель - член общины

        Returns:
            float: 0.0 = полный запрет, 1.0 = полная допустимость
        """
        if "no_internal_violence" not in self.norms:
            return 0.5  # Нейтральное значение

        norm = self.norms["no_internal_violence"]

        if target_internal:
            # Насилие внутри общины строго запрещено
            return 1.0 - norm.punishment_severity * norm.compliance_rate
        else:
            # Насилие против чужих более терпимо
            return 0.7

    def update_compliance_from_class_power(self, class_power: Dict[str, float]) -> None:
        """
        Обновляет соблюдаемость норм в зависимости от власти классов.

        По Марксу: нормы, выгодные господствующему классу,
        соблюдаются лучше из-за институциональной поддержки.

        Args:
            class_power: Словарь {class_name: power_level}
        """
        for norm in self.norms.values():
            if not norm.benefits_class:
                continue

            # Если класс-бенефициар имеет власть, норма соблюдается лучше
            beneficiary_power = class_power.get(norm.benefits_class, 0.0)
            if beneficiary_power > 0.3:
                # Усиливаем соблюдаемость (до 95%)
                norm.compliance_rate = min(0.95, norm.compliance_rate + beneficiary_power * 0.1)
            elif beneficiary_power < 0.1:
                # Ослабляем соблюдаемость без поддержки (до 40%)
                norm.compliance_rate = max(0.4, norm.compliance_rate - 0.05)

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику"""
        return {
            "total_norms": len(self.norms),
            "by_type": {
                n.norm_type.value: n.name
                for n in self.norms.values()
            },
            "compliance_rates": {
                n.id: n.compliance_rate
                for n in self.norms.values()
            }
        }
