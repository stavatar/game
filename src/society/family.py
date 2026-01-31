"""
Система семей и родственных связей.

Семья - базовая ячейка общества:
- Определяет наследование
- Влияет на социальные связи
- Формирует идентичность
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto
import uuid


class KinshipType(Enum):
    """Типы родства"""
    PARENT = "родитель"
    CHILD = "ребёнок"
    SPOUSE = "супруг"
    SIBLING = "брат/сестра"
    GRANDPARENT = "дед/бабка"
    GRANDCHILD = "внук"
    UNCLE_AUNT = "дядя/тётя"
    NEPHEW_NIECE = "племянник"
    COUSIN = "двоюродный"


class MarriageType(Enum):
    """Типы брака"""
    MONOGAMY = "моногамия"
    POLYGYNY = "полигиния"      # Многожёнство
    POLYANDRY = "полиандрия"    # Многомужество
    GROUP = "групповой"


@dataclass
class KinshipRelation:
    """Родственная связь"""
    relative_id: str
    kinship_type: KinshipType
    is_blood: bool = True       # Кровное родство


@dataclass
class Marriage:
    """Брак"""
    id: str
    spouse1_id: str
    spouse2_id: str
    year_married: int
    year_ended: Optional[int] = None
    is_active: bool = True
    children: List[str] = field(default_factory=list)  # ID детей

    def add_child(self, child_id: str) -> None:
        self.children.append(child_id)


@dataclass
class Family:
    """
    Семья - группа родственников.

    В примитивном обществе семья - это:
    - Родители и дети
    - Братья и сёстры
    - Расширенная семья (деды, дядья)
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""              # Фамилия/название рода

    # Члены семьи
    members: Set[str] = field(default_factory=set)
    head_id: Optional[str] = None  # Глава семьи

    # Родословная
    ancestors: List[str] = field(default_factory=list)  # Известные предки

    # Статус
    founding_year: int = 0
    prestige: float = 0.0       # Престиж семьи (0-100)

    def add_member(self, npc_id: str) -> None:
        self.members.add(npc_id)

    def remove_member(self, npc_id: str) -> None:
        self.members.discard(npc_id)
        if self.head_id == npc_id:
            self.head_id = None

    def get_size(self) -> int:
        return len(self.members)

    def is_empty(self) -> bool:
        return len(self.members) == 0


@dataclass
class FamilySystem:
    """
    Система управления семьями и родством.

    Отслеживает:
    - Все семьи
    - Родственные связи
    - Браки
    - Генеалогию
    """

    # Все семьи
    families: Dict[str, Family] = field(default_factory=dict)

    # NPC -> Family ID
    npc_family: Dict[str, str] = field(default_factory=dict)

    # Родственные связи (npc_id -> list of relations)
    kinship: Dict[str, List[KinshipRelation]] = field(default_factory=dict)

    # Браки
    marriages: Dict[str, Marriage] = field(default_factory=dict)

    # NPC -> их активный брак
    npc_marriage: Dict[str, str] = field(default_factory=dict)

    # Тип брака в обществе (может меняться с развитием)
    dominant_marriage_type: MarriageType = MarriageType.MONOGAMY

    def create_family(self, name: str, founder_id: str, year: int) -> Family:
        """Создаёт новую семью"""
        family = Family(
            name=name,
            members={founder_id},
            head_id=founder_id,
            founding_year=year,
        )
        self.families[family.id] = family
        self.npc_family[founder_id] = family.id
        return family

    def get_family(self, family_id: str) -> Optional[Family]:
        """Возвращает семью"""
        return self.families.get(family_id)

    def get_npc_family(self, npc_id: str) -> Optional[Family]:
        """Возвращает семью NPC"""
        family_id = self.npc_family.get(npc_id)
        if family_id:
            return self.families.get(family_id)
        return None

    def add_kinship(self, npc1_id: str, npc2_id: str,
                    kinship_type: KinshipType, is_blood: bool = True) -> None:
        """Добавляет родственную связь"""
        # Добавляем связь NPC1 -> NPC2
        if npc1_id not in self.kinship:
            self.kinship[npc1_id] = []

        self.kinship[npc1_id].append(KinshipRelation(
            relative_id=npc2_id,
            kinship_type=kinship_type,
            is_blood=is_blood,
        ))

        # Добавляем обратную связь
        if npc2_id not in self.kinship:
            self.kinship[npc2_id] = []

        reverse_type = self._get_reverse_kinship(kinship_type)
        self.kinship[npc2_id].append(KinshipRelation(
            relative_id=npc1_id,
            kinship_type=reverse_type,
            is_blood=is_blood,
        ))

    def _get_reverse_kinship(self, kinship_type: KinshipType) -> KinshipType:
        """Возвращает обратный тип родства"""
        reverse_map = {
            KinshipType.PARENT: KinshipType.CHILD,
            KinshipType.CHILD: KinshipType.PARENT,
            KinshipType.SPOUSE: KinshipType.SPOUSE,
            KinshipType.SIBLING: KinshipType.SIBLING,
            KinshipType.GRANDPARENT: KinshipType.GRANDCHILD,
            KinshipType.GRANDCHILD: KinshipType.GRANDPARENT,
            KinshipType.UNCLE_AUNT: KinshipType.NEPHEW_NIECE,
            KinshipType.NEPHEW_NIECE: KinshipType.UNCLE_AUNT,
            KinshipType.COUSIN: KinshipType.COUSIN,
        }
        return reverse_map.get(kinship_type, kinship_type)

    def get_relatives(self, npc_id: str,
                      kinship_type: KinshipType = None) -> List[str]:
        """Возвращает родственников NPC"""
        if npc_id not in self.kinship:
            return []

        relatives = []
        for rel in self.kinship[npc_id]:
            if kinship_type is None or rel.kinship_type == kinship_type:
                relatives.append(rel.relative_id)

        return relatives

    def get_parents(self, npc_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Возвращает родителей"""
        parents = self.get_relatives(npc_id, KinshipType.PARENT)
        if len(parents) >= 2:
            return parents[0], parents[1]
        elif len(parents) == 1:
            return parents[0], None
        return None, None

    def get_children(self, npc_id: str) -> List[str]:
        """Возвращает детей"""
        return self.get_relatives(npc_id, KinshipType.CHILD)

    def get_siblings(self, npc_id: str) -> List[str]:
        """Возвращает братьев/сестёр"""
        return self.get_relatives(npc_id, KinshipType.SIBLING)

    def get_spouse(self, npc_id: str) -> Optional[str]:
        """Возвращает супруга"""
        marriage_id = self.npc_marriage.get(npc_id)
        if not marriage_id:
            return None

        marriage = self.marriages.get(marriage_id)
        if not marriage or not marriage.is_active:
            return None

        if marriage.spouse1_id == npc_id:
            return marriage.spouse2_id
        return marriage.spouse1_id

    def marry(self, npc1_id: str, npc2_id: str, year: int) -> Optional[Marriage]:
        """Заключает брак"""
        # Проверяем, не в браке ли уже
        if self.dominant_marriage_type == MarriageType.MONOGAMY:
            if self.get_spouse(npc1_id) or self.get_spouse(npc2_id):
                return None

        # Создаём брак
        marriage = Marriage(
            id=str(uuid.uuid4())[:8],
            spouse1_id=npc1_id,
            spouse2_id=npc2_id,
            year_married=year,
        )

        self.marriages[marriage.id] = marriage
        self.npc_marriage[npc1_id] = marriage.id
        self.npc_marriage[npc2_id] = marriage.id

        # Добавляем родственную связь
        self.add_kinship(npc1_id, npc2_id, KinshipType.SPOUSE, is_blood=False)

        # Объединяем семьи или присоединяем к одной
        family1 = self.get_npc_family(npc1_id)
        family2 = self.get_npc_family(npc2_id)

        if family1 and not family2:
            family1.add_member(npc2_id)
            self.npc_family[npc2_id] = family1.id
        elif family2 and not family1:
            family2.add_member(npc1_id)
            self.npc_family[npc1_id] = family2.id
        elif not family1 and not family2:
            # Создаём новую семью
            self.create_family(f"Семья_{marriage.id}", npc1_id, year)
            family = self.get_npc_family(npc1_id)
            family.add_member(npc2_id)
            self.npc_family[npc2_id] = family.id

        return marriage

    def register_birth(self, child_id: str, mother_id: str,
                       father_id: str, year: int) -> None:
        """Регистрирует рождение ребёнка"""
        # Добавляем родственные связи
        self.add_kinship(child_id, mother_id, KinshipType.PARENT)
        self.add_kinship(child_id, father_id, KinshipType.PARENT)

        # Добавляем связи с братьями/сёстрами
        siblings = self.get_children(mother_id) + self.get_children(father_id)
        for sibling_id in set(siblings):
            if sibling_id != child_id:
                self.add_kinship(child_id, sibling_id, KinshipType.SIBLING)

        # Добавляем в брак
        for marriage in self.marriages.values():
            if marriage.is_active:
                if (marriage.spouse1_id in [mother_id, father_id] and
                        marriage.spouse2_id in [mother_id, father_id]):
                    marriage.add_child(child_id)
                    break

        # Присоединяем к семье родителей
        parent_family = self.get_npc_family(mother_id) or self.get_npc_family(father_id)
        if parent_family:
            parent_family.add_member(child_id)
            self.npc_family[child_id] = parent_family.id

    def register_death(self, npc_id: str) -> None:
        """Регистрирует смерть"""
        # Завершаем брак
        marriage_id = self.npc_marriage.get(npc_id)
        if marriage_id and marriage_id in self.marriages:
            self.marriages[marriage_id].is_active = False

        # Удаляем из семьи
        family = self.get_npc_family(npc_id)
        if family:
            family.remove_member(npc_id)

            # Если глава семьи умер, выбираем нового
            if family.head_id == npc_id and family.members:
                # Выбираем старшего
                family.head_id = next(iter(family.members))

    def are_related(self, npc1_id: str, npc2_id: str) -> bool:
        """Проверяет, являются ли NPC родственниками"""
        if npc1_id not in self.kinship:
            return False

        # Прямые родственники
        direct = self.get_relatives(npc1_id)
        if npc2_id in direct:
            return True

        # Родственники через одно поколение
        for rel_id in direct:
            if npc2_id in self.get_relatives(rel_id):
                return True

        return False

    def get_family_tree(self, npc_id: str, depth: int = 2) -> Dict[str, List[str]]:
        """Возвращает семейное древо"""
        tree = {
            "parents": self.get_relatives(npc_id, KinshipType.PARENT),
            "children": self.get_relatives(npc_id, KinshipType.CHILD),
            "siblings": self.get_relatives(npc_id, KinshipType.SIBLING),
            "spouse": [],
        }

        spouse = self.get_spouse(npc_id)
        if spouse:
            tree["spouse"] = [spouse]

        if depth > 1:
            # Добавляем внуков и дедов
            grandparents = []
            for parent in tree["parents"]:
                grandparents.extend(self.get_relatives(parent, KinshipType.PARENT))
            tree["grandparents"] = grandparents

            grandchildren = []
            for child in tree["children"]:
                grandchildren.extend(self.get_relatives(child, KinshipType.CHILD))
            tree["grandchildren"] = grandchildren

        return tree

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику"""
        active_marriages = sum(1 for m in self.marriages.values() if m.is_active)
        avg_family_size = (
            sum(f.get_size() for f in self.families.values()) / len(self.families)
            if self.families else 0
        )

        return {
            "families": len(self.families),
            "active_marriages": active_marriages,
            "avg_family_size": round(avg_family_size, 1),
            "marriage_type": self.dominant_marriage_type.value,
        }
