---
title: Руководство Разработчика
description: Руководство для разработчиков по расширению систем и добавлению новых функций
keywords:
  - разработка
  - архитектура
  - расширение
  - паттерны
  - тестирование
lang: ru
---

# Руководство Разработчика

Это руководство поможет вам разобраться в архитектуре проекта и добавить новые функции.

## Структура Проекта

```
src/
├── core/
│   ├── config.py           # Конфигурация - настраиваемые параметры
│   ├── simulation.py       # Главный цикл симуляции
│   ├── events.py           # Система событий (pub/sub паттерн)
│   ├── emergence.py        # Инструменты для emergent поведения
│   ├── consistency.py      # Проверка консистентности
│   └── dialectics.py       # Марксистский анализ
│
├── world/
│   ├── map.py              # Карта мира (координаты, локации)
│   ├── terrain.py          # Типы местности
│   ├── climate.py          # Сезоны, погода, катаклизмы
│   └── location.py         # Локации и ресурсы
│
├── economy/
│   ├── resources.py        # Система ресурсов
│   ├── production.py       # Производство и труд
│   ├── technology.py       # Технологии и их открытие
│   └── property.py         # Собственность и классы
│
├── society/
│   ├── family.py           # Семьи и родство
│   ├── demography.py       # Демография и жизненные циклы
│   └── classes.py          # Классовая структура
│
├── culture/
│   ├── beliefs.py          # Верования и идеология
│   ├── traditions.py       # Традиции и обряды
│   └── norms.py            # Социальные нормы
│
├── npc/
│   ├── character.py        # Основной класс NPC
│   ├── genetics.py         # Генетика и наследование
│   ├── memory.py           # Память и опыт (Memory Stream)
│   ├── personality.py      # Личность и черты
│   ├── needs.py            # Потребности и мотивация
│   └── ai/
│       └── bdi.py          # BDI-архитектура (Beliefs-Desires-Intentions)
│
├── ai/
│   └── behavior.py         # Поведенческие модели
│
├── analysis/
│   └── sensitivity.py      # Анализ чувствительности параметров
│
└── data/
    └── names.py            # Банк имён

tests/
├── unit/                   # Модульные тесты
├── integration/            # Интеграционные тесты
└── fixtures/               # Тестовые данные и фикстуры
```

## Принципы Разработки

### 1. Emergent Поведение

Всё должно ВОЗНИКАТЬ, а не задаваться:

```python
# ❌ ПЛОХО - задаём поведение напрямую
npc.add_belief(Belief("богатство хорошо"))

# ✅ ХОРОШО - верование возникает из условий
if npc.has_property and npc.social_class == "wealthy":
    # Верование возникает само через BeliefSystem
    belief_system.generate_ideology_for_class("wealthy")
```

### 2. Системный Анализ (Базис → Надстройка)

- **Базис** (экономика): ресурсы, производство, собственность, технологии
- **Надстройка** (культура): верования, идеология, традиции, нормы

Надстройка должна ВОЗНИКАТЬ из базиса, а не наоборот:

```python
# Правильный порядок:
1. Формируется способ производства
2. Возникают классы
3. На основе этого формируется идеология
```

### 3. Type Hints и Документация

Всегда используйте type hints:

```python
from typing import Dict, List, Optional, Set, Tuple

def transfer_knowledge(teacher_id: str, student_id: str,
                       tech_id: str, hours: float) -> bool:
    """Передача знания от учителя к ученику."""
    pass
```

### 4. Dataclasses и Enums

Для структур данных используйте `dataclasses`:

```python
from dataclasses import dataclass, field
from enum import Enum

class TechEra(Enum):
    """Технологические эпохи"""
    PRIMITIVE = ("первобытная", 0)
    STONE_AGE = ("каменный век", 1)

    def __init__(self, name: str, level: int):
        self.name = name
        self.level = level

@dataclass
class Technology:
    id: str
    name: str
    category: TechCategory
    era: TechEra
    prerequisites: List[str] = field(default_factory=list)
    production_bonus: Dict[str, float] = field(default_factory=dict)
```

## Как Добавить Новое NPC Поведение

### Шаг 1: Поймите Архитектуру BDI

BDI (Beliefs-Desires-Intentions) - основа поведения NPC:

```
Beliefs (Убеждения)
└─ Что NPC знает/думает о мире
   ├─ Экономические убеждения ("богатство хорошо")
   ├─ Социальные убеждения ("иерархия естественна")
   └─ Личные убеждения ("Иван мой друг")

Desires (Желания)
└─ Цели и потребности
   ├─ Базовые (голод, сон, тепло)
   ├─ Социальные (семья, статус, уважение)
   └─ Идеологические (вера, традиции)

Intentions (Намерения)
└─ Выбранные планы действий
   ├─ Немедленные (идти собирать)
   ├─ Среднесрочные (жениться)
   └─ Долгосрочные (накопить богатство)
```

### Шаг 2: Добавьте Новое Желание

В `src/npc/needs.py`:

```python
class NeedType(Enum):
    """Типы потребностей"""
    # Существующие...
    HUNGER = "голод"
    SLEEP = "сон"

    # Новая потребность
    KNOWLEDGE = "знание"

@dataclass
class Need:
    need_type: NeedType
    current: float  # 0-100, где 100 - срочно
    priority: int   # 1-10

    def is_urgent(self) -> bool:
        return self.current > 75
```

### Шаг 3: Добавьте Логику Удовлетворения

В `src/npc/character.py`:

```python
def satisfy_need(self, need_type: NeedType, action: str) -> float:
    """
    Удовлетворить потребность действием.

    Returns: Количество удовлетворённости (0-100)
    """
    need = self.needs.get(need_type)
    if not need:
        return 0

    satisfaction = 0

    if need_type == NeedType.KNOWLEDGE and action == "learn":
        satisfaction = 10 + (self.intelligence / 10)
        # Учитесь лучше, если умнее

    need.current = max(0, need.current - satisfaction)
    return satisfaction
```

### Шаг 4: Интегрируйте в BDI

В `src/npc/ai/bdi.py`:

```python
def form_intention(self) -> Optional[Intention]:
    """Сформировать намерение на основе убеждений и желаний"""

    # 1. Найти самое срочное желание
    urgent_need = self.find_urgent_need()

    # 2. Выбрать действие на основе убеждений
    if urgent_need == NeedType.KNOWLEDGE:
        # Убеждение: "знание ценно"
        if self.belief_system.has_belief("knowledge_valuable"):
            # Найти учителя
            teacher = self.find_teacher()
            if teacher:
                return Intention(
                    action="learn",
                    target=teacher,
                    priority=urgent_need.priority
                )

    # 3. Вернуть намерение
    return intention
```

### Пример: Добавить Поведение "Копить Богатство"

```python
# 1. В config.py добавьте настройку
@dataclass
class Config:
    wealth_accumulation_rate: float = 0.01

# 2. В needs.py добавьте потребность
class NeedType(Enum):
    WEALTH = "богатство"

# 3. В character.py добавьте логику
def accumulate_wealth(self, amount: float) -> None:
    """Накопить богатство"""
    if self.beliefs.has_belief("private_property_sacred"):
        self.wealth += amount * 1.5  # Более мотивирован
    else:
        self.wealth += amount

# 4. В bdi.py интегрируйте в принятие решений
def form_intention(self) -> Optional[Intention]:
    if self.need_wealth.is_urgent():
        if self.beliefs.has_belief("wealth_accumulation_good"):
            return Intention(action="work_for_wealth")
```

## Как Добавить Новую Технологию

### Шаг 1: Поймите Систему Технологий

Посмотрите `src/economy/technology.py`:

```python
@dataclass
class Technology:
    id: str                                # Уникальный идентификатор
    name: str                              # Русское название
    category: TechCategory                 # Категория (орудия, земледелие и т.д.)
    era: TechEra                          # Эпоха, когда может открыться
    prerequisites: List[str]               # Требуемые предыдущие технологии
    base_discovery_chance: float           # Шанс открытия в день
    production_bonus: Dict[str, float]     # Бонусы к производству
    unlocks: List[str]                     # Какие технологии открывает
```

### Шаг 2: Добавьте Новую Технологию

В `src/economy/technology.py`:

```python
# 1. Добавьте в TechCategory если нужна новая категория
class TechCategory(Enum):
    MEDICINE = "медицина"  # Новая!

# 2. Зарегистрируйте технологию
_register_tech(Technology(
    id="herbalism",
    name="использование трав",
    description="Лечение болезней травами",
    category=TechCategory.MEDICINE,
    era=TechEra.PRIMITIVE,
    prerequisites=["gathering"],  # Нужно собирательство
    base_discovery_chance=0.005,   # Редкое открытие
    discovery_difficulty=1.5,      # Средняя сложность
    production_bonus={
        "healing": 0.5,
        "health_restoration": 1.0,
    },
    enables_resources=["herbal_remedy"],
))
```

### Шаг 3: Добавьте Эффекты Технологии

В `src/economy/production.py`:

```python
def apply_technology_bonus(self, tech_id: str, activity: str) -> float:
    """Применить бонус технологии к деятельности"""
    tech = TECHNOLOGIES.get(tech_id)
    if not tech:
        return 1.0

    bonus = tech.production_bonus.get(activity, 0)
    return 1.0 + bonus

# Использование:
production = base_production * apply_technology_bonus(
    "herbalism", "healing"
)
```

### Шаг 4: Интегрируйте в Открытие Технологий

В `src/economy/technology.py` уже есть система:

```python
class KnowledgeSystem:
    def try_discovery(self, npc_id: str, activity: str,
                      intelligence: int, year: int) -> Optional[Technology]:
        """
        Попытка открыть технологию через деятельность.

        Система автоматически:
        - Проверяет требования
        - Накапливает прогресс
        - Открывает при достаточном уровне
        """
```

Просто добавьте деятельность в `_get_activity_relevance`:

```python
def _get_activity_relevance(self, activity: str, tech: Technology) -> float:
    relevance_map = {
        # ...
        "healing": ["herbalism"],  # Добавьте это
    }
```

## Как Добавить Новое Верование/Традицию

### Шаг 1: Изучите Систему Верований

В `src/culture/beliefs.py`:

```python
class BeliefType(Enum):
    """Типы верований"""
    ANIMISM = "анимизм"
    ANCESTOR_WORSHIP = "культ предков"
    # и так далее...

@dataclass
class Belief:
    id: str
    name: str
    belief_type: BeliefType
    origin: BeliefOrigin  # Откуда взялось
    holders: Set[str]     # Кто верит (NPC IDs)
```

### Шаг 2: Добавьте Новое Верование

В `src/culture/beliefs.py`:

```python
# 1. Добавьте тип если нужен новый
class BeliefType(Enum):
    SCIENCE = "научность"  # Новый тип!

# 2. Добавьте верование
INITIAL_BELIEFS = {
    "rationalism": Belief(
        id="rationalism",
        name="рациональность",
        description="Логика и разум важнее традиции",
        belief_type=BeliefType.SCIENCE,
        origin=BeliefOrigin.ECONOMIC,  # Возникает из экономики
        required_tech=["writing"],     # Нужна письменность
        min_social_class="educated",   # Для образованных
        behavior_effects={
            "accept_new_technology": 0.8,
            "respect_traditions": -0.5,
        },
    ),
}
```

### Шаг 3: Добавьте Условия Возникновения

В `src/culture/beliefs.py`:

```python
class BeliefSystem:
    def generate_beliefs_from_economy(self, economy_state: Dict) -> List[Belief]:
        """
        Верования ВОЗНИКАЮТ из экономического базиса.
        """
        beliefs = []

        # Если есть частная собственность, возникает верование в её священность
        if economy_state["has_private_property"]:
            beliefs.append(INITIAL_BELIEFS["property_sacred"])

        # Если есть классовая система, возникает идеология её оправдания
        if economy_state["class_gap"] > 0.7:
            beliefs.append(INITIAL_BELIEFS["hierarchy_divine"])

        # Если высокий уровень образования, возникает рационализм
        if economy_state["average_intelligence"] > 8:
            beliefs.append(INITIAL_BELIEFS["rationalism"])

        return beliefs
```

### Шаг 4: Добавьте Влияние на Поведение

В `src/npc/ai/bdi.py`:

```python
def evaluate_action(self, action: str) -> float:
    """Оценить действие на основе убеждений"""
    score = 0

    for belief_id, belief in self.beliefs.items():
        if "rationalism" in belief_id:
            # Рационалист более охотно принимает новые технологии
            if action == "adopt_new_technology":
                score += 0.8
            # Но менее охотно соблюдает традиции
            if action == "follow_tradition":
                score -= 0.5

    return score
```

## Тестирование

### Структура Тестов

```
tests/
├── unit/
│   ├── test_technology.py
│   ├── test_beliefs.py
│   ├── test_npc_ai.py
│   └── test_economy.py
└── integration/
    ├── test_simulation_cycle.py
    └── test_emergence.py
```

### Написание Модульного Теста

```python
import pytest
from src.economy.technology import Technology, TechCategory, TechEra, KnowledgeSystem

def test_technology_discovery():
    """Тест открытия технологии"""
    # Arrange
    knowledge = KnowledgeSystem()
    npc_id = "npc_1"
    knowledge.individual_knowledge[npc_id] = {"stone_knapping"}

    # Act
    discovered = knowledge.try_discovery(
        npc_id=npc_id,
        activity="hunting",
        intelligence=8,
        year=0
    )

    # Assert
    assert discovered is not None
    assert discovered.id == "basic_hunting"
    assert knowledge.npc_knows(npc_id, "basic_hunting")

def test_technology_requires_prerequisites():
    """Технология открывается только если выполнены требования"""
    knowledge = KnowledgeSystem()
    npc_id = "npc_2"

    # БЕЗ камнеобработки не может охотиться
    knowledge.individual_knowledge[npc_id] = set()

    discovered = knowledge.try_discovery(
        npc_id=npc_id,
        activity="hunting",
        intelligence=10,
        year=0
    )

    # Не должно открыться
    assert discovered is None or discovered.id != "basic_hunting"
```

### Написание Интеграционного Теста

```python
def test_simulation_cycle():
    """Полный цикл симуляции"""
    from src.core.simulation import Simulation
    from src.core.config import Config

    # Arrange
    config = Config(
        initial_population=5,
        enable_property=True,
        enable_beliefs=True,
    )
    sim = Simulation(config)

    # Act
    for _ in range(100):  # 100 дней
        sim.step()

    # Assert
    assert len(sim.world.npcs) > 0
    assert len(sim.knowledge_system.discovered_technologies) > 0
    # Некоторые верования должны возникнуть
    assert len(sim.belief_system.beliefs) > 0
```

### Запуск Тестов

```bash
# Все тесты
pytest tests/

# Конкретный модуль
pytest tests/unit/test_technology.py

# С verbose выводом
pytest tests/ -v

# С покрытием кода
pytest tests/ --cov=src
```

## Соглашения о Коде

### Именование

```python
# NPC идентификаторы - строки
npc_id = "npc_123"

# Классы - CapCase
class BeliefSystem:
    pass

# Функции и методы - snake_case
def calculate_production_bonus():
    pass

# Константы - UPPER_SNAKE_CASE
MAX_AGE = 70
INITIAL_POPULATION = 12

# Приватные методы - _leading_underscore
def _calculate_internal_value():
    pass
```

### Документирование

Все модули, классы и функции должны иметь docstring:

```python
"""
Модуль: описание того, что здесь происходит.

Этот модуль отвечает за X, Y и Z.
Используется в процессе A.
"""

class MyClass:
    """
    Краткое описание класса.

    Более подробное описание того, как он работает,
    какие уникальные особенности и ограничения.
    """

def my_function(param1: str, param2: int) -> bool:
    """
    Краткое описание функции.

    Более подробное описание с примерами использования.

    Args:
        param1: Описание первого параметра
        param2: Описание второго параметра

    Returns:
        Описание того, что возвращается

    Raises:
        ValueError: Когда может возникнуть эта ошибка
    """
    pass
```

### Обработка Ошибок

```python
# ✅ ХОРОШО - специфичная обработка
try:
    tech = TECHNOLOGIES[tech_id]
except KeyError:
    logger.error(f"Технология {tech_id} не найдена")
    return None

# ❌ ПЛОХО - общая обработка
try:
    tech = TECHNOLOGIES[tech_id]
except:
    pass
```

### Использование Логирования

```python
import logging

logger = logging.getLogger(__name__)

def important_function():
    logger.info("Начало важной функции")
    try:
        result = do_something()
        logger.debug(f"Результат: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        raise
```

## Отладка и Анализ

### Консистентность Симуляции

Используйте `src/core/consistency.py`:

```python
from src.core.consistency import ConsistencyChecker

checker = ConsistencyChecker(sim)
issues = checker.check_all()

if issues:
    for issue in issues:
        logger.warning(f"Проблема консистентности: {issue}")
```

### Анализ Чувствительности

Изучите влияние параметров на результаты:

```python
from src.analysis.sensitivity import SensitivityAnalyzer

analyzer = SensitivityAnalyzer()
results = analyzer.analyze_parameter_sensitivity(
    param_name="technology_discovery_rate",
    values=[0.001, 0.005, 0.01, 0.05],
    metric="average_technology_adoption_time"
)
```

### Марксистский Анализ

Вывести результаты в марксистском ключе:

```python
from src.core.dialectics import DialecticsAnalyzer

analyzer = DialecticsAnalyzer(sim)
report = analyzer.generate_report()
print(report.economic_base_summary)
print(report.ideological_superstructure_analysis)
print(report.class_conflict_dynamics)
```

## Часто Задаваемые Вопросы

### Q: Как добавить новый тип ресурса?

В `src/economy/resources.py`:

```python
class ResourceType(Enum):
    GRAIN = "зерно"
    MEAT = "мясо"
    METAL = "металл"
    KNOWLEDGE = "знание"  # Новый!

# Добавить в начальные ресурсы
INITIAL_RESOURCES = {
    ResourceType.KNOWLEDGE: Resource(
        type=ResourceType.KNOWLEDGE,
        quantity=0,
        regeneration_rate=0.05,
    ),
}
```

### Q: Как добавить новый жизненный этап?

В `src/npc/personality.py`:

```python
class LifeStage(Enum):
    INFANT = "младенец"        # 0-2
    CHILD = "ребёнок"          # 3-12
    ADULT = "взрослый"         # 18-50
    ELDER = "старик"           # 50+
    ANCESTOR = "предок"        # Новый! (после смерти)

def handle_as_ancestor(npc: Character):
    """Обработать NPC как предка"""
    npc.life_stage = LifeStage.ANCESTOR
    # Может влиять на верования других
    belief_system.increase_ancestor_worship(npc)
```

### Q: Как создать новое событие в системе?

В `src/core/events.py` используется паттерн pub/sub:

```python
from src.core.events import EventBus

event_bus = EventBus()

# Подписаться на событие
@event_bus.subscribe("technology_discovered")
def on_technology_discovered(event_data):
    tech_id = event_data["technology_id"]
    logger.info(f"Открыта технология: {tech_id}")

# Генерировать событие
event_bus.emit("technology_discovered", {
    "technology_id": "herbalism",
    "discovered_by": "npc_1",
    "year": 50,
})
```

## Ресурсы

- **README.md** - Общее описание проекта
- **config.py** - Все настраиваемые параметры
- **events.py** - Система событий
- **Исследования в README.md** - Основные вдохновляющие системы (Dwarf Fortress, BDI, Generative Agents)

## Получение Помощи

1. Проверьте соответствующий модуль в `src/`
2. Посмотрите docstring класса или функции
3. Найдите похожий функционал и используйте как пример
4. Проверьте тесты - часто там видна правильная мотель использования
