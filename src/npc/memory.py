"""
Система памяти NPC - основа для принятия решений.

Вдохновлено исследованием Generative Agents (Stanford):
- Поток памяти (Memory Stream)
- Рефлексия (Reflection) - выводы из опыта
- Извлечение (Retrieval) - поиск релевантных воспоминаний

Память определяет:
- Как NPC воспринимает мир
- Какие решения принимает
- Как относится к другим
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto
from datetime import datetime
import random
import math


class MemoryType(Enum):
    """Типы воспоминаний"""
    OBSERVATION = "наблюдение"      # Что видел
    ACTION = "действие"              # Что делал
    CONVERSATION = "разговор"        # С кем говорил
    EMOTION = "эмоция"               # Что чувствовал
    REFLECTION = "размышление"       # Вывод из опыта
    PLAN = "план"                    # Намерение
    RELATIONSHIP = "отношение"       # Изменение отношений
    ECONOMIC = "экономическое"       # Связанное с экономикой
    TRAUMA = "травма"                # Травматическое событие
    JOY = "радость"                  # Радостное событие


class EmotionalValence(Enum):
    """Эмоциональная окраска"""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


@dataclass
class MemoryEntry:
    """
    Единица памяти.

    Каждое воспоминание имеет:
    - Содержание (что произошло)
    - Время (когда)
    - Важность (насколько значимо)
    - Эмоциональную окраску
    - Связи (с кем/чем связано)
    """
    id: str
    memory_type: MemoryType
    description: str                 # Описание события

    # Время
    year: int = 0
    month: int = 0
    day: int = 0
    hour: int = 0

    # Значимость и эмоции
    importance: float = 0.5          # 0-1, насколько важно
    emotional_valence: EmotionalValence = EmotionalValence.NEUTRAL
    emotional_intensity: float = 0.5  # 0-1, сила эмоции

    # Связи
    related_npc_ids: List[str] = field(default_factory=list)
    related_location_id: Optional[str] = None
    related_objects: List[str] = field(default_factory=list)

    # Метаданные
    access_count: int = 0            # Сколько раз вспоминали
    last_accessed: int = 0           # Когда последний раз

    # Для рефлексий - на чём основано
    based_on_memories: List[str] = field(default_factory=list)

    def get_recency_score(self, current_day: int) -> float:
        """
        Вычисляет оценку свежести воспоминания.
        Свежие воспоминания более доступны.
        """
        days_ago = current_day - (self.year * 360 + self.month * 30 + self.day)
        # Экспоненциальное затухание
        decay_rate = 0.995
        return math.pow(decay_rate, days_ago)

    def get_relevance_score(self, query_npcs: List[str] = None,
                           query_location: str = None,
                           query_type: MemoryType = None) -> float:
        """
        Вычисляет релевантность воспоминания к запросу.
        """
        score = 0.0

        if query_npcs:
            overlap = len(set(query_npcs) & set(self.related_npc_ids))
            score += overlap * 0.3

        if query_location and self.related_location_id == query_location:
            score += 0.2

        if query_type and self.memory_type == query_type:
            score += 0.2

        return score

    def get_retrieval_score(self, current_day: int,
                           query_npcs: List[str] = None,
                           query_location: str = None) -> float:
        """
        Общая оценка для извлечения воспоминания.
        Комбинирует: важность + свежесть + релевантность
        """
        recency = self.get_recency_score(current_day)
        relevance = self.get_relevance_score(query_npcs, query_location)

        # Важность имеет наибольший вес
        return (self.importance * 0.5 +
                recency * 0.3 +
                relevance * 0.2)


@dataclass
class Reflection:
    """
    Рефлексия - вывод из накопленного опыта.

    NPC периодически анализирует воспоминания и делает выводы:
    - "Иван всегда помогает мне - он хороший друг"
    - "Зимой еды мало - нужно запасать осенью"
    - "Землевладельцы забирают много - это несправедливо"
    """
    id: str
    conclusion: str                  # Сам вывод
    confidence: float = 0.5          # Уверенность в выводе (0-1)

    # На чём основан вывод
    supporting_memories: List[str] = field(default_factory=list)
    evidence_count: int = 0          # Сколько примеров подтверждают

    # Тип вывода
    about_npc: Optional[str] = None  # Если вывод о конкретном NPC
    about_world: bool = False        # Если вывод о мире
    about_self: bool = False         # Если вывод о себе

    # Когда сделан
    year: int = 0
    day: int = 0

    # Может ли измениться
    is_core_belief: bool = False     # Ключевые убеждения меняются сложнее


class MemoryStream:
    """
    Поток памяти NPC.

    Хранит все воспоминания и обеспечивает:
    - Добавление новых воспоминаний
    - Извлечение релевантных
    - Периодическую рефлексию
    - Забывание неважного
    """

    def __init__(self, owner_id: str, max_memories: int = 200):
        self.owner_id = owner_id
        self.max_memories = max_memories

        # Хранилище
        self.memories: Dict[str, MemoryEntry] = {}
        self.reflections: Dict[str, Reflection] = {}

        # Индексы для быстрого поиска
        self._by_npc: Dict[str, Set[str]] = {}      # npc_id -> memory_ids
        self._by_location: Dict[str, Set[str]] = {} # location_id -> memory_ids
        self._by_type: Dict[MemoryType, Set[str]] = {}

        # Счётчик для ID
        self._memory_counter = 0
        self._reflection_counter = 0

        # Порог для рефлексии
        self.reflection_threshold = 10  # Каждые N воспоминаний
        self._memories_since_reflection = 0

    def add_memory(self,
                   memory_type: MemoryType,
                   description: str,
                   year: int,
                   month: int = 0,
                   day: int = 0,
                   hour: int = 0,
                   importance: float = 0.5,
                   emotional_valence: EmotionalValence = EmotionalValence.NEUTRAL,
                   emotional_intensity: float = 0.5,
                   related_npcs: List[str] = None,
                   related_location: str = None,
                   related_objects: List[str] = None) -> MemoryEntry:
        """
        Добавляет новое воспоминание.
        """
        self._memory_counter += 1
        memory_id = f"mem_{self.owner_id}_{self._memory_counter}"

        memory = MemoryEntry(
            id=memory_id,
            memory_type=memory_type,
            description=description,
            year=year,
            month=month,
            day=day,
            hour=hour,
            importance=importance,
            emotional_valence=emotional_valence,
            emotional_intensity=emotional_intensity,
            related_npc_ids=related_npcs or [],
            related_location_id=related_location,
            related_objects=related_objects or [],
        )

        self.memories[memory_id] = memory

        # Обновляем индексы
        self._index_memory(memory)

        # Проверяем, нужна ли рефлексия
        self._memories_since_reflection += 1

        # Очищаем старые неважные воспоминания если переполнение
        if len(self.memories) > self.max_memories:
            self._forget_unimportant()

        return memory

    def _index_memory(self, memory: MemoryEntry) -> None:
        """Добавляет воспоминание в индексы"""
        # По NPC
        for npc_id in memory.related_npc_ids:
            if npc_id not in self._by_npc:
                self._by_npc[npc_id] = set()
            self._by_npc[npc_id].add(memory.id)

        # По локации
        if memory.related_location_id:
            loc = memory.related_location_id
            if loc not in self._by_location:
                self._by_location[loc] = set()
            self._by_location[loc].add(memory.id)

        # По типу
        if memory.memory_type not in self._by_type:
            self._by_type[memory.memory_type] = set()
        self._by_type[memory.memory_type].add(memory.id)

    def retrieve(self,
                 current_day: int,
                 count: int = 5,
                 about_npc: str = None,
                 about_location: str = None,
                 memory_type: MemoryType = None,
                 min_importance: float = 0.0) -> List[MemoryEntry]:
        """
        Извлекает наиболее релевантные воспоминания.

        Использует комбинацию:
        - Важность
        - Свежесть (recency)
        - Релевантность запросу
        """
        candidates = list(self.memories.values())

        # Фильтруем по минимальной важности
        candidates = [m for m in candidates if m.importance >= min_importance]

        # Фильтруем по типу если указан
        if memory_type:
            candidates = [m for m in candidates if m.memory_type == memory_type]

        # Вычисляем оценки
        query_npcs = [about_npc] if about_npc else None
        scored = [
            (m, m.get_retrieval_score(current_day, query_npcs, about_location))
            for m in candidates
        ]

        # Сортируем по оценке
        scored.sort(key=lambda x: x[1], reverse=True)

        # Увеличиваем счётчик доступа
        result = []
        for memory, score in scored[:count]:
            memory.access_count += 1
            memory.last_accessed = current_day
            result.append(memory)

        return result

    def retrieve_about_npc(self, npc_id: str, count: int = 5) -> List[MemoryEntry]:
        """Извлекает воспоминания о конкретном NPC"""
        if npc_id not in self._by_npc:
            return []

        memory_ids = self._by_npc[npc_id]
        memories = [self.memories[mid] for mid in memory_ids if mid in self.memories]

        # Сортируем по важности и свежести
        memories.sort(key=lambda m: m.importance, reverse=True)
        return memories[:count]

    def get_impression_of(self, npc_id: str) -> Tuple[float, str]:
        """
        Возвращает общее впечатление о NPC.

        Возвращает: (оценка от -1 до 1, текстовое описание)
        """
        memories = self.retrieve_about_npc(npc_id, count=20)

        if not memories:
            return 0.0, "незнакомец"

        # Средняя эмоциональная оценка с учётом важности
        total_score = 0.0
        total_weight = 0.0

        for m in memories:
            weight = m.importance * m.emotional_intensity
            score = m.emotional_valence.value / 2  # -1 до 1
            total_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0, "знакомый"

        impression = total_score / total_weight

        # Текстовое описание
        if impression < -0.6:
            desc = "враг"
        elif impression < -0.3:
            desc = "неприятный человек"
        elif impression < 0.3:
            desc = "знакомый"
        elif impression < 0.6:
            desc = "приятель"
        else:
            desc = "друг"

        return impression, desc

    def reflect(self, current_year: int, current_day: int) -> List[Reflection]:
        """
        Выполняет рефлексию - анализ накопленного опыта.

        Создаёт выводы типа:
        - "X часто помогает мне" → "X - друг"
        - "Зимой всегда голодно" → "Нужно запасать еду"
        - "Богатые забирают много" → "Это несправедливо"
        """
        new_reflections = []

        # 1. Рефлексия об NPC
        for npc_id, memory_ids in self._by_npc.items():
            if npc_id == self.owner_id:
                continue

            memories = [self.memories[mid] for mid in memory_ids if mid in self.memories]
            if len(memories) >= 3:  # Достаточно данных для вывода
                reflection = self._reflect_about_npc(npc_id, memories, current_year, current_day)
                if reflection:
                    new_reflections.append(reflection)

        # 2. Рефлексия о паттернах
        pattern_reflection = self._reflect_about_patterns(current_year, current_day)
        if pattern_reflection:
            new_reflections.append(pattern_reflection)

        # 3. Рефлексия о себе
        self_reflection = self._reflect_about_self(current_year, current_day)
        if self_reflection:
            new_reflections.append(self_reflection)

        # Сбрасываем счётчик
        self._memories_since_reflection = 0

        return new_reflections

    def _reflect_about_npc(self, npc_id: str, memories: List[MemoryEntry],
                          year: int, day: int) -> Optional[Reflection]:
        """Создаёт вывод о конкретном NPC"""
        # Считаем положительные и отрицательные взаимодействия
        positive = sum(1 for m in memories if m.emotional_valence.value > 0)
        negative = sum(1 for m in memories if m.emotional_valence.value < 0)
        total = len(memories)

        if total < 3:
            return None

        self._reflection_counter += 1
        ref_id = f"ref_{self.owner_id}_{self._reflection_counter}"

        # Формируем вывод
        if positive > negative * 2:
            conclusion = f"Этот человек хорошо ко мне относится, он друг"
            confidence = min(0.9, positive / total)
        elif negative > positive * 2:
            conclusion = f"Этот человек плохо ко мне относится, нужно быть осторожным"
            confidence = min(0.9, negative / total)
        else:
            return None  # Нет явного паттерна

        reflection = Reflection(
            id=ref_id,
            conclusion=conclusion,
            confidence=confidence,
            supporting_memories=[m.id for m in memories[:5]],
            evidence_count=total,
            about_npc=npc_id,
            year=year,
            day=day,
        )

        self.reflections[ref_id] = reflection
        return reflection

    def _reflect_about_patterns(self, year: int, day: int) -> Optional[Reflection]:
        """Ищет паттерны в событиях"""
        # Пример: анализ экономических воспоминаний
        economic_memories = [
            self.memories[mid]
            for mid in self._by_type.get(MemoryType.ECONOMIC, set())
            if mid in self.memories
        ]

        if len(economic_memories) < 5:
            return None

        # Считаем негативные экономические события
        negative = sum(1 for m in economic_memories if m.emotional_valence.value < 0)

        if negative > len(economic_memories) * 0.6:
            self._reflection_counter += 1
            ref_id = f"ref_{self.owner_id}_{self._reflection_counter}"

            reflection = Reflection(
                id=ref_id,
                conclusion="Жизнь тяжела, ресурсов не хватает",
                confidence=negative / len(economic_memories),
                supporting_memories=[m.id for m in economic_memories[:5]],
                evidence_count=negative,
                about_world=True,
                year=year,
                day=day,
            )

            self.reflections[ref_id] = reflection
            return reflection

        return None

    def _reflect_about_self(self, year: int, day: int) -> Optional[Reflection]:
        """Рефлексия о собственных действиях"""
        action_memories = [
            self.memories[mid]
            for mid in self._by_type.get(MemoryType.ACTION, set())
            if mid in self.memories
        ]

        if len(action_memories) < 5:
            return None

        # Анализ успешности действий
        positive = sum(1 for m in action_memories if m.emotional_valence.value > 0)

        if positive > len(action_memories) * 0.7:
            self._reflection_counter += 1
            ref_id = f"ref_{self.owner_id}_{self._reflection_counter}"

            reflection = Reflection(
                id=ref_id,
                conclusion="Мои действия приносят результат, я на верном пути",
                confidence=positive / len(action_memories),
                supporting_memories=[m.id for m in action_memories[:5]],
                evidence_count=positive,
                about_self=True,
                year=year,
                day=day,
            )

            self.reflections[ref_id] = reflection
            return reflection

        return None

    def _forget_unimportant(self) -> None:
        """Удаляет наименее важные воспоминания"""
        # Сортируем по важности и частоте доступа
        sorted_memories = sorted(
            self.memories.values(),
            key=lambda m: m.importance + (m.access_count * 0.1),
        )

        # Удаляем 20% наименее важных
        to_remove = len(sorted_memories) // 5
        for memory in sorted_memories[:to_remove]:
            # Не удаляем рефлексии и очень важные воспоминания
            if memory.memory_type == MemoryType.REFLECTION:
                continue
            if memory.importance >= 0.8:
                continue

            del self.memories[memory.id]

            # Убираем из индексов
            for npc_id in memory.related_npc_ids:
                if npc_id in self._by_npc:
                    self._by_npc[npc_id].discard(memory.id)

            if memory.related_location_id in self._by_location:
                self._by_location[memory.related_location_id].discard(memory.id)

            if memory.memory_type in self._by_type:
                self._by_type[memory.memory_type].discard(memory.id)

    def should_reflect(self) -> bool:
        """Проверяет, пора ли делать рефлексию"""
        return self._memories_since_reflection >= self.reflection_threshold

    def get_recent_memories(self, count: int = 10) -> List[MemoryEntry]:
        """Возвращает последние воспоминания"""
        sorted_memories = sorted(
            self.memories.values(),
            key=lambda m: (m.year, m.month, m.day, m.hour),
            reverse=True
        )
        return sorted_memories[:count]

    def get_traumatic_memories(self) -> List[MemoryEntry]:
        """Возвращает травматические воспоминания"""
        return [
            m for m in self.memories.values()
            if m.memory_type == MemoryType.TRAUMA or
               (m.emotional_valence == EmotionalValence.VERY_NEGATIVE and
                m.emotional_intensity > 0.7)
        ]

    def get_happy_memories(self) -> List[MemoryEntry]:
        """Возвращает радостные воспоминания"""
        return [
            m for m in self.memories.values()
            if m.memory_type == MemoryType.JOY or
               (m.emotional_valence == EmotionalValence.VERY_POSITIVE and
                m.emotional_intensity > 0.7)
        ]

    def get_statistics(self) -> Dict[str, any]:
        """Статистика памяти"""
        type_counts = {}
        for mem_type in MemoryType:
            type_counts[mem_type.value] = len(self._by_type.get(mem_type, set()))

        return {
            "total_memories": len(self.memories),
            "total_reflections": len(self.reflections),
            "known_npcs": len(self._by_npc),
            "known_locations": len(self._by_location),
            "by_type": type_counts,
            "traumatic": len(self.get_traumatic_memories()),
            "happy": len(self.get_happy_memories()),
        }
