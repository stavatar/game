"""
Система верований - идеологическая надстройка.

По Марксу, идеология:
- Отражает интересы господствующего класса
- Оправдывает существующий порядок
- Воспринимается как "естественная" истина

Верования ВОЗНИКАЮТ из экономических условий, а не задаются извне.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto
import random


class BeliefType(Enum):
    """Типы верований"""
    ANIMISM = "анимизм"              # Духи природы
    ANCESTOR_WORSHIP = "культ предков"
    TOTEMISM = "тотемизм"            # Священное животное/растение
    SHAMANISM = "шаманизм"           # Посредники с духами
    POLYTHEISM = "многобожие"        # Много богов
    PROPERTY_SACRED = "священность собственности"
    HIERARCHY_DIVINE = "божественность иерархии"
    LABOR_VIRTUE = "добродетель труда"
    EQUALITY = "равенство"
    FATE = "судьба"


class BeliefOrigin(Enum):
    """Происхождение верования"""
    NATURAL = "природное"            # Из наблюдения природы
    ECONOMIC = "экономическое"       # Из экономических отношений
    SOCIAL = "социальное"            # Из социальных отношений
    CRISIS = "кризисное"             # Из кризиса/катаклизма


@dataclass
class Belief:
    """
    Верование - элемент идеологии.

    Каждое верование:
    - Имеет причину возникновения (в базисе)
    - Влияет на поведение
    - Может противоречить другим
    """
    id: str
    name: str
    belief_type: BeliefType
    description: str

    # Происхождение
    origin: BeliefOrigin
    origin_conditions: Dict[str, any] = field(default_factory=dict)
    year_emerged: int = 0

    # Распространённость
    adherents: Set[str] = field(default_factory=set)  # NPC, разделяющие верование
    strength: float = 0.5               # Сила убеждения (0-1)

    # Влияние на поведение
    behavior_modifiers: Dict[str, float] = field(default_factory=dict)
    # Например: {"sharing": 0.2, "violence": -0.3}

    # Связь с классами
    benefits_class: Optional[str] = None  # Какому классу выгодно
    opposes_class: Optional[str] = None   # Какому классу вредит

    # Совместимость с другими верованиями
    compatible_with: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)

    def get_adherent_count(self) -> int:
        return len(self.adherents)


class BeliefSystem:
    """
    Система верований общества.

    Верования:
    1. Возникают из экономических условий
    2. Распространяются через социализацию
    3. Отражают классовые интересы
    4. Влияют на поведение
    """

    def __init__(self):
        # Все верования
        self.beliefs: Dict[str, Belief] = {}

        # NPC -> их верования
        self.npc_beliefs: Dict[str, Set[str]] = {}

        # Доминирующая идеология
        self.dominant_beliefs: List[str] = []

        # История
        self.belief_history: List[tuple] = []

    def check_belief_emergence(self,
                               economic_conditions: Dict[str, any],
                               social_conditions: Dict[str, any],
                               year: int) -> Optional[Belief]:
        """
        Проверяет условия для возникновения нового верования.

        Верования EMERGENT - возникают из условий!
        """
        new_belief = None

        # === Анимизм - базовое верование ===
        if "animism" not in self.beliefs:
            # Появляется при взаимодействии с природой
            if economic_conditions.get("gathering_activity", 0) > 0:
                new_belief = Belief(
                    id="animism",
                    name="духи природы",
                    belief_type=BeliefType.ANIMISM,
                    description="Всё в природе имеет душу - деревья, реки, камни",
                    origin=BeliefOrigin.NATURAL,
                    year_emerged=year,
                    behavior_modifiers={"respect_nature": 0.3},
                )

        # === Культ предков ===
        elif "ancestor_worship" not in self.beliefs:
            # Появляется когда умирают первые члены общины
            if social_conditions.get("deaths_occurred", 0) > 3:
                new_belief = Belief(
                    id="ancestor_worship",
                    name="почитание предков",
                    belief_type=BeliefType.ANCESTOR_WORSHIP,
                    description="Духи предков защищают и направляют живых",
                    origin=BeliefOrigin.SOCIAL,
                    year_emerged=year,
                    behavior_modifiers={"respect_elders": 0.4, "tradition": 0.3},
                    compatible_with=["animism"],
                )

        # === Священность собственности ===
        elif "property_sacred" not in self.beliefs:
            # Появляется с возникновением частной собственности
            if economic_conditions.get("private_property_exists", False):
                inequality = economic_conditions.get("inequality", 0)
                if inequality > 0.3:
                    new_belief = Belief(
                        id="property_sacred",
                        name="священность владения",
                        belief_type=BeliefType.PROPERTY_SACRED,
                        description="Собственность дана духами и неприкосновенна",
                        origin=BeliefOrigin.ECONOMIC,
                        origin_conditions={"inequality": inequality},
                        year_emerged=year,
                        behavior_modifiers={"theft": -0.5, "sharing": -0.2},
                        benefits_class="LANDOWNER",
                        opposes_class="LANDLESS",
                    )

        # === Божественность иерархии ===
        elif "hierarchy_divine" not in self.beliefs:
            # Появляется с расслоением общества
            if social_conditions.get("classes_emerged", False):
                new_belief = Belief(
                    id="hierarchy_divine",
                    name="божественный порядок",
                    belief_type=BeliefType.HIERARCHY_DIVINE,
                    description="Социальный порядок установлен высшими силами",
                    origin=BeliefOrigin.ECONOMIC,
                    year_emerged=year,
                    behavior_modifiers={"obedience": 0.4, "rebellion": -0.5},
                    benefits_class="LANDOWNER",
                    compatible_with=["property_sacred"],
                )

        # === Добродетель труда ===
        elif "labor_virtue" not in self.beliefs:
            # Появляется когда появляются те, кто не трудится
            if economic_conditions.get("non_workers_exist", False):
                new_belief = Belief(
                    id="labor_virtue",
                    name="добродетель труда",
                    belief_type=BeliefType.LABOR_VIRTUE,
                    description="Труд облагораживает, праздность - грех",
                    origin=BeliefOrigin.ECONOMIC,
                    year_emerged=year,
                    behavior_modifiers={"work_ethic": 0.3},
                    # Эта идеология может служить как угнетателям, так и угнетённым
                )

        if new_belief:
            self.beliefs[new_belief.id] = new_belief
            self.belief_history.append((new_belief.id, year, new_belief.origin.value))
            return new_belief

        return None

    def spread_belief(self, belief_id: str, from_npc: str, to_npc: str,
                      influence: float = 0.1) -> bool:
        """
        Распространяет верование от одного NPC к другому.

        Вероятность принятия зависит от:
        - Влияния источника
        - Совместимости с существующими верованиями
        - Классовых интересов
        """
        if belief_id not in self.beliefs:
            return False

        belief = self.beliefs[belief_id]

        # Получаем верования NPC
        npc_beliefs = self.npc_beliefs.get(to_npc, set())

        # Проверяем конфликты
        for conflict_id in belief.conflicts_with:
            if conflict_id in npc_beliefs:
                influence *= 0.3  # Сложнее принять противоречащее

        # Проверяем совместимость
        for compat_id in belief.compatible_with:
            if compat_id in npc_beliefs:
                influence *= 1.5  # Легче принять совместимое

        # Случайность
        if random.random() < influence:
            self.add_belief_to_npc(to_npc, belief_id)
            return True

        return False

    def add_belief_to_npc(self, npc_id: str, belief_id: str) -> None:
        """Добавляет верование NPC"""
        if npc_id not in self.npc_beliefs:
            self.npc_beliefs[npc_id] = set()

        self.npc_beliefs[npc_id].add(belief_id)

        if belief_id in self.beliefs:
            self.beliefs[belief_id].adherents.add(npc_id)

    def get_npc_beliefs(self, npc_id: str) -> List[Belief]:
        """Возвращает верования NPC"""
        belief_ids = self.npc_beliefs.get(npc_id, set())
        return [self.beliefs[bid] for bid in belief_ids if bid in self.beliefs]

    def get_behavior_modifier(self, npc_id: str, behavior: str) -> float:
        """
        Возвращает модификатор поведения от верований.

        Например: get_behavior_modifier(npc, "sharing") -> 0.3
        означает +30% к вероятности поделиться
        """
        total = 0.0
        beliefs = self.get_npc_beliefs(npc_id)

        for belief in beliefs:
            modifier = belief.behavior_modifiers.get(behavior, 0)
            total += modifier * belief.strength

        return total

    def update_dominant_ideology(self, class_power: Dict[str, float]) -> None:
        """
        Обновляет доминирующую идеологию.

        По Марксу: идеи господствующего класса = господствующие идеи.
        """
        # Находим верования, выгодные доминирующему классу
        dominant_class = max(class_power.keys(), key=lambda c: class_power[c])

        dominant = []
        for belief in self.beliefs.values():
            if belief.benefits_class == dominant_class:
                dominant.append(belief.id)
            # Также добавляем общепринятые верования
            if belief.get_adherent_count() > len(self.npc_beliefs) * 0.5:
                if belief.id not in dominant:
                    dominant.append(belief.id)

        self.dominant_beliefs = dominant

    def check_ideological_conflict(self) -> Optional[tuple]:
        """Проверяет наличие идеологического конфликта"""
        # Ищем противоречащие верования с большим числом сторонников
        for b1_id, b1 in self.beliefs.items():
            for b2_id in b1.conflicts_with:
                if b2_id in self.beliefs:
                    b2 = self.beliefs[b2_id]
                    if b1.get_adherent_count() > 5 and b2.get_adherent_count() > 5:
                        return (b1_id, b2_id)
        return None

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику верований"""
        return {
            "total_beliefs": len(self.beliefs),
            "dominant_ideology": self.dominant_beliefs,
            "belief_distribution": {
                b.name: b.get_adherent_count()
                for b in self.beliefs.values()
            },
            "ideological_conflict": self.check_ideological_conflict(),
        }
