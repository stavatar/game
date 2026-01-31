"""
Система генетики - наследование черт от родителей.

Моделирует:
- Наследование физических характеристик
- Наследование предрасположенностей
- Мутации и вариации
- Генетическое разнообразие популяции
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto
import random
import math


class GeneType(Enum):
    """Типы генов"""
    # Физические
    HEIGHT = "рост"
    BUILD = "телосложение"
    HAIR_COLOR = "цвет волос"
    EYE_COLOR = "цвет глаз"
    SKIN_TONE = "тон кожи"

    # Характеристики (предрасположенности)
    STRENGTH_POTENTIAL = "потенциал силы"
    AGILITY_POTENTIAL = "потенциал ловкости"
    INTELLIGENCE_POTENTIAL = "потенциал интеллекта"
    ENDURANCE_POTENTIAL = "потенциал выносливости"

    # Особенности
    LONGEVITY = "долголетие"
    FERTILITY = "плодовитость"
    DISEASE_RESISTANCE = "сопротивляемость болезням"

    # Психологические предрасположенности
    TEMPERAMENT = "темперамент"
    INTROVERSION = "интроверсия"
    AGGRESSION = "агрессивность"
    CURIOSITY = "любопытство"


@dataclass
class Gene:
    """
    Ген - единица наследования.

    Каждый ген имеет два аллеля (от каждого родителя).
    Выражение зависит от доминантности.
    """
    gene_type: GeneType
    allele1: float  # Значение от первого родителя (0-1)
    allele2: float  # Значение от второго родителя (0-1)
    dominance: float = 0.5  # 0 = полностью рецессивный, 1 = полностью доминантный

    def get_expression(self) -> float:
        """
        Вычисляет выражение гена.
        Учитывает доминантность и взаимодействие аллелей.
        """
        # Смешанное наследование с учётом доминантности
        if self.dominance > 0.5:
            # Доминантный аллель - берём максимум
            return max(self.allele1, self.allele2)
        elif self.dominance < 0.5:
            # Рецессивный - берём минимум
            return min(self.allele1, self.allele2)
        else:
            # Кодоминантность - среднее
            return (self.allele1 + self.allele2) / 2

    def get_random_allele(self) -> float:
        """Возвращает случайный аллель для передачи потомству"""
        return random.choice([self.allele1, self.allele2])


@dataclass
class Genome:
    """
    Геном - полный набор генов NPC.

    Определяет:
    - Физические характеристики
    - Предрасположенности к навыкам
    - Склонности характера
    """
    genes: Dict[GeneType, Gene] = field(default_factory=dict)

    # Родословная
    mother_id: Optional[str] = None
    father_id: Optional[str] = None
    generation: int = 0

    # Мутации
    mutations: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Если геном пустой - инициализируем случайно
        if not self.genes:
            self._initialize_random()

    def _initialize_random(self) -> None:
        """Создаёт случайный геном (первое поколение)"""
        for gene_type in GeneType:
            # Случайные аллели
            allele1 = random.random()
            allele2 = random.random()

            # Доминантность зависит от типа гена
            if gene_type in [GeneType.HAIR_COLOR, GeneType.EYE_COLOR]:
                dominance = 0.7  # Тёмные цвета доминантны
            elif gene_type in [GeneType.AGGRESSION, GeneType.TEMPERAMENT]:
                dominance = 0.5  # Кодоминантность
            else:
                dominance = random.uniform(0.4, 0.6)

            self.genes[gene_type] = Gene(
                gene_type=gene_type,
                allele1=allele1,
                allele2=allele2,
                dominance=dominance
            )

    def get_trait(self, gene_type: GeneType) -> float:
        """Получает выраженное значение черты"""
        if gene_type in self.genes:
            return self.genes[gene_type].get_expression()
        return 0.5  # Среднее значение по умолчанию

    def get_physical_traits(self) -> Dict[str, str]:
        """Преобразует гены в описательные физические черты"""
        traits = {}

        # Рост
        height_val = self.get_trait(GeneType.HEIGHT)
        if height_val < 0.3:
            traits["height"] = "низкий"
        elif height_val < 0.7:
            traits["height"] = "средний"
        else:
            traits["height"] = "высокий"

        # Телосложение
        build_val = self.get_trait(GeneType.BUILD)
        if build_val < 0.25:
            traits["build"] = "худощавый"
        elif build_val < 0.5:
            traits["build"] = "обычный"
        elif build_val < 0.75:
            traits["build"] = "крепкий"
        else:
            traits["build"] = "массивный"

        # Цвет волос (тёмные доминантны)
        hair_val = self.get_trait(GeneType.HAIR_COLOR)
        if hair_val < 0.2:
            traits["hair"] = "светлые"
        elif hair_val < 0.4:
            traits["hair"] = "русые"
        elif hair_val < 0.6:
            traits["hair"] = "каштановые"
        elif hair_val < 0.8:
            traits["hair"] = "тёмные"
        else:
            traits["hair"] = "чёрные"

        # Цвет глаз
        eye_val = self.get_trait(GeneType.EYE_COLOR)
        if eye_val < 0.2:
            traits["eyes"] = "голубые"
        elif eye_val < 0.4:
            traits["eyes"] = "серые"
        elif eye_val < 0.6:
            traits["eyes"] = "зелёные"
        elif eye_val < 0.8:
            traits["eyes"] = "карие"
        else:
            traits["eyes"] = "чёрные"

        return traits

    def get_stat_modifiers(self) -> Dict[str, int]:
        """Получает модификаторы характеристик от генов"""
        modifiers = {}

        # Преобразуем потенциалы в модификаторы (-3 до +3)
        str_pot = self.get_trait(GeneType.STRENGTH_POTENTIAL)
        modifiers["strength"] = int((str_pot - 0.5) * 6)

        agi_pot = self.get_trait(GeneType.AGILITY_POTENTIAL)
        modifiers["agility"] = int((agi_pot - 0.5) * 6)

        int_pot = self.get_trait(GeneType.INTELLIGENCE_POTENTIAL)
        modifiers["intelligence"] = int((int_pot - 0.5) * 6)

        end_pot = self.get_trait(GeneType.ENDURANCE_POTENTIAL)
        modifiers["endurance"] = int((end_pot - 0.5) * 6)

        return modifiers

    def get_lifespan_modifier(self) -> float:
        """Возвращает модификатор продолжительности жизни"""
        longevity = self.get_trait(GeneType.LONGEVITY)
        disease_res = self.get_trait(GeneType.DISEASE_RESISTANCE)

        # Базовый модификатор 0.8 - 1.2
        modifier = 0.8 + (longevity * 0.2) + (disease_res * 0.2)
        return modifier

    def get_fertility_modifier(self) -> float:
        """Возвращает модификатор плодовитости"""
        fertility = self.get_trait(GeneType.FERTILITY)
        # Модификатор 0.5 - 1.5
        return 0.5 + fertility

    def get_temperament_traits(self) -> Dict[str, float]:
        """Возвращает черты темперамента"""
        return {
            "introversion": self.get_trait(GeneType.INTROVERSION),
            "aggression": self.get_trait(GeneType.AGGRESSION),
            "curiosity": self.get_trait(GeneType.CURIOSITY),
            "temperament": self.get_trait(GeneType.TEMPERAMENT),
        }


class GeneticsSystem:
    """
    Система генетики для популяции.

    Управляет:
    - Созданием геномов
    - Наследованием
    - Мутациями
    - Генетическим разнообразием
    """

    def __init__(self, mutation_rate: float = 0.05):
        self.mutation_rate = mutation_rate
        self.genomes: Dict[str, Genome] = {}  # npc_id -> Genome

    def create_genome(self, npc_id: str,
                      mother_id: Optional[str] = None,
                      father_id: Optional[str] = None) -> Genome:
        """
        Создаёт геном для NPC.

        Если указаны родители - наследует от них.
        Иначе - случайный геном.
        """
        if mother_id and father_id:
            genome = self._inherit_genome(mother_id, father_id)
        else:
            genome = Genome()

        genome.mother_id = mother_id
        genome.father_id = father_id

        if mother_id and mother_id in self.genomes:
            genome.generation = self.genomes[mother_id].generation + 1

        self.genomes[npc_id] = genome
        return genome

    def _inherit_genome(self, mother_id: str, father_id: str) -> Genome:
        """Создаёт геном потомка от двух родителей"""
        mother_genome = self.genomes.get(mother_id)
        father_genome = self.genomes.get(father_id)

        if not mother_genome or not father_genome:
            # Если геном родителя неизвестен - создаём случайный
            return Genome()

        child_genes = {}
        mutations = []

        for gene_type in GeneType:
            mother_gene = mother_genome.genes.get(gene_type)
            father_gene = father_genome.genes.get(gene_type)

            if not mother_gene or not father_gene:
                # Создаём случайный ген
                child_genes[gene_type] = Gene(
                    gene_type=gene_type,
                    allele1=random.random(),
                    allele2=random.random()
                )
                continue

            # Получаем аллели от родителей
            allele1 = mother_gene.get_random_allele()
            allele2 = father_gene.get_random_allele()

            # Мутации
            if random.random() < self.mutation_rate:
                # Мутация - случайное изменение аллеля
                if random.random() < 0.5:
                    allele1 = max(0, min(1, allele1 + random.uniform(-0.2, 0.2)))
                else:
                    allele2 = max(0, min(1, allele2 + random.uniform(-0.2, 0.2)))
                mutations.append(f"Мутация в гене {gene_type.value}")

            # Наследуем доминантность (обычно стабильна)
            dominance = (mother_gene.dominance + father_gene.dominance) / 2

            child_genes[gene_type] = Gene(
                gene_type=gene_type,
                allele1=allele1,
                allele2=allele2,
                dominance=dominance
            )

        genome = Genome(genes=child_genes, mutations=mutations)
        return genome

    def get_genome(self, npc_id: str) -> Optional[Genome]:
        """Получает геном NPC"""
        return self.genomes.get(npc_id)

    def calculate_genetic_distance(self, npc1_id: str, npc2_id: str) -> float:
        """
        Вычисляет генетическую дистанцию между NPC.

        Используется для:
        - Определения родства
        - Предотвращения инбридинга
        - Вычисления совместимости
        """
        genome1 = self.genomes.get(npc1_id)
        genome2 = self.genomes.get(npc2_id)

        if not genome1 or not genome2:
            return 1.0  # Максимальная дистанция если нет данных

        total_distance = 0
        gene_count = 0

        for gene_type in GeneType:
            gene1 = genome1.genes.get(gene_type)
            gene2 = genome2.genes.get(gene_type)

            if gene1 and gene2:
                # Дистанция как разница в выражении
                expr1 = gene1.get_expression()
                expr2 = gene2.get_expression()
                total_distance += abs(expr1 - expr2)
                gene_count += 1

        if gene_count == 0:
            return 1.0

        return total_distance / gene_count

    def are_related(self, npc1_id: str, npc2_id: str, max_generations: int = 3) -> bool:
        """Проверяет, являются ли NPC родственниками"""
        # Проверяем общих предков
        ancestors1 = self._get_ancestors(npc1_id, max_generations)
        ancestors2 = self._get_ancestors(npc2_id, max_generations)

        # Есть ли пересечение
        return bool(ancestors1 & ancestors2)

    def _get_ancestors(self, npc_id: str, max_generations: int) -> set:
        """Получает множество предков NPC"""
        ancestors = set()
        to_check = [(npc_id, 0)]

        while to_check:
            current_id, generation = to_check.pop()

            if generation >= max_generations:
                continue

            genome = self.genomes.get(current_id)
            if not genome:
                continue

            if genome.mother_id:
                ancestors.add(genome.mother_id)
                to_check.append((genome.mother_id, generation + 1))

            if genome.father_id:
                ancestors.add(genome.father_id)
                to_check.append((genome.father_id, generation + 1))

        return ancestors

    def get_population_diversity(self) -> float:
        """
        Вычисляет генетическое разнообразие популяции.

        Высокое разнообразие = здоровая популяция
        Низкое = риск вырождения
        """
        if len(self.genomes) < 2:
            return 1.0

        total_diversity = 0
        comparisons = 0

        npc_ids = list(self.genomes.keys())
        for i, id1 in enumerate(npc_ids):
            for id2 in npc_ids[i+1:]:
                total_diversity += self.calculate_genetic_distance(id1, id2)
                comparisons += 1

        if comparisons == 0:
            return 1.0

        return total_diversity / comparisons

    def get_statistics(self) -> Dict[str, any]:
        """Возвращает статистику генетической системы"""
        if not self.genomes:
            return {
                "population_size": 0,
                "diversity": 0,
                "avg_generation": 0,
                "total_mutations": 0,
            }

        generations = [g.generation for g in self.genomes.values()]
        mutations = sum(len(g.mutations) for g in self.genomes.values())

        return {
            "population_size": len(self.genomes),
            "diversity": round(self.get_population_diversity(), 2),
            "avg_generation": round(sum(generations) / len(generations), 1),
            "max_generation": max(generations),
            "total_mutations": mutations,
        }
