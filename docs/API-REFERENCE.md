---
title: "API Reference: Базис и Надстройка"
description: "Справочник по ключевым классам и функциям симуляции"
version: "1.0.0"
language: "ru"
keywords: ["api", "reference", "classes", "functions", "simulation", "npc", "events"]
last_updated: "2026-02-01"
---

# API Reference

Справочник по ключевым классам и функциям симуляции первобытной общины.

## Содержание

- [Core Module](#core-module)
  - [EventType](#eventtype)
  - [Event](#event)
  - [EventBus](#eventbus)
  - [Config](#config)
  - [Simulation](#simulation)
- [NPC Module](#npc-module)
  - [NPC](#npc)
  - [Stats](#stats)
  - [Skills](#skills)
  - [Personality](#personality)
  - [Trait](#trait)
  - [Needs](#needs)
  - [Relationship](#relationship)
  - [RelationshipManager](#relationshipmanager)
- [Примеры использования](#примеры-использования)

---

## Core Module

### EventType

**Модуль:** `src/core/events.py`

Enum, определяющий все типы событий в симуляции.

```python
from src.core.events import EventType
```

#### Категории событий

| Категория | События | Описание |
|-----------|---------|----------|
| Жизненный цикл | `NPC_BORN`, `NPC_DIED`, `NPC_AGED` | Рождение, смерть, старение |
| Семья | `MARRIAGE`, `DIVORCE`, `CHILD_BORN` | Семейные события |
| Экономика | `RESOURCE_GATHERED`, `RESOURCE_DEPLETED`, `ITEM_CRAFTED`, `TRADE_COMPLETED` | Ресурсы и торговля |
| Собственность | `PROPERTY_CLAIMED`, `PROPERTY_TRANSFERRED`, `PROPERTY_LOST` | Владение имуществом |
| Технологии | `TECHNOLOGY_DISCOVERED`, `KNOWLEDGE_TRANSFERRED`, `TOOL_CREATED` | Развитие технологий |
| Социум | `CLASS_EMERGED`, `RELATIONSHIP_CHANGED`, `CONFLICT_STARTED`, `REBELLION` | Социальные изменения |
| Культура | `BELIEF_FORMED`, `TRADITION_CREATED`, `NORM_ESTABLISHED`, `RITUAL_PERFORMED` | Культурные события |
| Климат | `SEASON_CHANGED`, `WEATHER_EVENT`, `DROUGHT`, `PLAGUE`, `FAMINE` | Погода и катастрофы |
| Мир | `DAY_PASSED`, `MONTH_PASSED`, `YEAR_PASSED`, `GENERATION_PASSED` | Течение времени |

#### EventImportance

```python
class EventImportance(Enum):
    TRIVIAL = 1      # Рутинные действия
    MINOR = 2        # Мелкие события
    NOTABLE = 3      # Заметные события
    IMPORTANT = 4    # Важные события
    MAJOR = 5        # Крупные события
    HISTORIC = 6     # Исторические события
```

---

### Event

**Модуль:** `src/core/events.py`

Dataclass, представляющий событие в симуляции.

```python
from src.core.events import Event, EventType, EventImportance
```

#### Атрибуты

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `event_type` | `EventType` | Тип события |
| `importance` | `EventImportance` | Важность события |
| `year`, `month`, `day`, `hour` | `int` | Время события |
| `location_id` | `Optional[str]` | ID локации |
| `x`, `y` | `float` | Координаты |
| `actor_id` | `Optional[str]` | ID NPC, совершившего действие |
| `target_id` | `Optional[str]` | ID целевого NPC |
| `witness_ids` | `List[str]` | Список ID свидетелей |
| `data` | `Dict[str, Any]` | Дополнительные данные |
| `description` | `str` | Описание события |
| `id` | `str` | Уникальный идентификатор (8 символов) |
| `caused_by` | `Optional[str]` | ID события-причины |
| `causes` | `List[str]` | ID вызванных событий |

#### Методы

```python
def format_time(self) -> str:
    """Форматирует время события в читаемую строку"""

def format_description(self, npc_names: Dict[str, str] = None) -> str:
    """Форматирует описание с подстановкой имён NPC"""

def is_historic(self) -> bool:
    """Проверяет, является ли событие историческим (MAJOR или выше)"""
```

#### Пример

```python
event = Event(
    event_type=EventType.TECHNOLOGY_DISCOVERED,
    importance=EventImportance.MAJOR,
    year=15,
    actor_id="npc_1",
    data={"technology": "agriculture"},
    description_template="{actor} открыл {technology}!"
)
```

---

### EventBus

**Модуль:** `src/core/events.py`

Шина событий для паттерна Observer/Pub-Sub.

```python
from src.core.events import EventBus, event_bus  # event_bus - глобальный экземпляр
```

#### Методы

```python
def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
    """Подписывается на определённый тип событий"""

def subscribe_all(self, callback: Callable[[Event], None]) -> None:
    """Подписывается на все события"""

def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
    """Отписывается от типа событий"""

def publish(self, event: Event) -> None:
    """Публикует событие всем подписчикам"""

def get_history(
    self,
    event_type: EventType = None,
    min_importance: EventImportance = None,
    actor_id: str = None,
    limit: int = 100
) -> List[Event]:
    """Получает историю событий с фильтрацией"""

def get_historic_events(self, limit: int = 50) -> List[Event]:
    """Получает только исторические события"""

def clear_history(self) -> None:
    """Очищает историю (кроме исторических событий)"""
```

#### Пример использования

```python
from src.core.events import event_bus, EventType

def on_birth(event):
    print(f"Родился NPC: {event.actor_id}")

event_bus.subscribe(EventType.NPC_BORN, on_birth)
```

---

### Config

**Модуль:** `src/core/config.py`

Dataclass с настройками симуляции.

```python
from src.core.config import Config, SimulationSpeed, EventDetailLevel
```

#### Ключевые параметры

| Категория | Параметр | Тип | По умолчанию | Описание |
|-----------|----------|-----|--------------|----------|
| Мир | `world_name` | `str` | "Первобытная община" | Название мира |
| Мир | `map_width`, `map_height` | `int` | 50 | Размеры карты |
| Время | `simulation_speed` | `SimulationSpeed` | `NORMAL` | Скорость симуляции |
| Демография | `initial_population` | `int` | 12 | Начальная популяция |
| Демография | `max_age` | `int` | 70 | Максимальный возраст |
| Демография | `child_mortality_base` | `float` | 0.15 | Детская смертность |
| Экономика | `technology_discovery_rate` | `float` | 0.01 | Шанс открытия |
| Климат | `drought_probability` | `float` | 0.05 | Вероятность засухи |
| Социум | `rebellion_threshold` | `float` | 0.7 | Порог бунта |

#### SimulationSpeed

```python
class SimulationSpeed(Enum):
    PAUSED = 0
    SLOW = 1       # 1 день = 10 сек
    NORMAL = 2     # 1 день = 5 сек
    FAST = 3       # 1 день = 1 сек
    VERY_FAST = 4  # 1 день = 0.1 сек
```

#### Методы

```python
def days_per_year(self) -> int:
    """Возвращает количество дней в году"""

def get_season(self, day_of_year: int) -> str:
    """Возвращает название сезона по дню года"""

def to_dict(self) -> Dict[str, Any]:
    """Сериализация в словарь"""

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'Config':
    """Десериализация из словаря"""
```

#### Пресеты

```python
from src.core.config import PRESET_REALISTIC, PRESET_ACCELERATED, PRESET_SANDBOX

# PRESET_REALISTIC - реалистичные настройки (медленное развитие, высокая смертность)
# PRESET_ACCELERATED - ускоренное развитие
# PRESET_SANDBOX - песочница без катастроф
```

---

### Simulation

**Модуль:** `src/core/simulation.py`

Главный класс симуляции, объединяющий все системы.

```python
from src.core.simulation import Simulation
from src.core.config import Config
```

#### Конструктор

```python
sim = Simulation(config: Config = None)
```

#### Атрибуты состояния

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `year`, `month`, `day`, `hour` | `int` | Текущее время |
| `npcs` | `Dict[str, NPCState]` | Все NPC |
| `map` | `WorldMap` | Карта мира |
| `climate` | `ClimateSystem` | Система климата |
| `knowledge` | `KnowledgeSystem` | Технологии |
| `ownership` | `OwnershipSystem` | Собственность |
| `families` | `FamilySystem` | Семьи |
| `classes` | `ClassSystem` | Классы |
| `beliefs` | `BeliefSystem` | Верования |
| `event_bus` | `EventBus` | Шина событий |

#### Методы

```python
def initialize(self) -> List[str]:
    """Инициализирует мир с начальной популяцией. Возвращает список событий."""

def update(self, hours: int = 1) -> List[str]:
    """Обновляет симуляцию на указанное количество часов. Возвращает события."""

def get_status(self) -> str:
    """Возвращает текстовый статус симуляции"""

def get_npc_list(self) -> str:
    """Возвращает форматированный список NPC"""

def get_map_view(self) -> str:
    """Возвращает ASCII-представление карты"""
```

#### Пример использования

```python
from src.core.simulation import Simulation
from src.core.config import Config

config = Config(initial_population=20)
sim = Simulation(config)

# Инициализация
events = sim.initialize()
for e in events:
    print(e)

# Основной цикл
for _ in range(100):
    events = sim.update(hours=24)  # Прошёл день
    for e in events:
        print(e)

    print(sim.get_status())
```

---

## NPC Module

### NPC

**Модуль:** `src/npc/character.py`

Dataclass, представляющий уникальную личность.

```python
from src.npc.character import NPC, Gender, Occupation
```

#### Основные атрибуты

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `id` | `str` | Уникальный ID (8 символов) |
| `name`, `surname` | `str` | Имя и фамилия |
| `gender` | `Gender` | Пол (`MALE`, `FEMALE`) |
| `age` | `int` | Возраст |
| `stats` | `Stats` | Характеристики |
| `skills` | `Skills` | Навыки |
| `personality` | `Personality` | Личность |
| `needs` | `Needs` | Потребности |
| `relationships` | `RelationshipManager` | Отношения |
| `occupation` | `Occupation` | Профессия |
| `health` | `float` | Здоровье (0-100) |
| `is_alive` | `bool` | Жив ли NPC |
| `memories` | `List[Memory]` | Воспоминания |
| `goals` | `List[Goal]` | Цели |

#### Occupation (профессии)

```python
class Occupation(Enum):
    NONE = "безработный"
    FARMER = "фермер"
    BLACKSMITH = "кузнец"
    MERCHANT = "торговец"
    GUARD = "стражник"
    HEALER = "лекарь"
    HUNTER = "охотник"
    SCHOLAR = "учёный"
    # ... и другие
```

#### Методы

```python
def get_full_name(self) -> str:
    """Возвращает полное имя"""

def describe_appearance(self) -> str:
    """Возвращает описание внешности"""

def update(self, hours: float = 1.0) -> List[str]:
    """Обновляет состояние NPC, возвращает события"""

def add_memory(
    self,
    event_type: str,
    description: str,
    importance: float = 0.5,
    emotional_impact: float = 0.0,
    day: int = 0,
    related_npcs: List[str] = None
) -> None:
    """Добавляет воспоминание"""

def interact_with(self, other: 'NPC', interaction_type: str = "разговор") -> Dict[str, Any]:
    """Взаимодействует с другим NPC"""

def gain_experience(self, amount: int) -> None:
    """Получает опыт и может улучшить характеристики"""

def get_status_summary(self) -> str:
    """Возвращает краткую сводку о состоянии"""

@classmethod
def generate_random(
    cls,
    name: str = None,
    gender: Gender = None,
    occupation: Occupation = None
) -> 'NPC':
    """Генерирует случайного NPC"""
```

---

### Stats

**Модуль:** `src/npc/character.py`

Dataclass характеристик NPC.

```python
@dataclass
class Stats:
    strength: int = 10       # Сила
    agility: int = 10        # Ловкость
    endurance: int = 10      # Выносливость
    intelligence: int = 10   # Интеллект
    charisma: int = 10       # Харизма
    perception: int = 10     # Восприятие
    luck: int = 10           # Удача
```

#### Методы

```python
def modify(self, stat: str, value: int) -> None:
    """Изменяет характеристику (в пределах 1-20)"""

@classmethod
def generate_random(cls) -> 'Stats':
    """Генерирует случайные характеристики (5-15)"""
```

---

### Skills

**Модуль:** `src/npc/character.py`

Dataclass навыков NPC (0-100).

```python
@dataclass
class Skills:
    combat: int = 0       # Бой
    crafting: int = 0     # Ремесло
    trading: int = 0      # Торговля
    farming: int = 0      # Земледелие
    cooking: int = 0      # Готовка
    medicine: int = 0     # Медицина
    persuasion: int = 0   # Убеждение
    stealth: int = 0      # Скрытность
    music: int = 0        # Музыка
    knowledge: int = 0    # Знания
```

#### Методы

```python
def improve(self, skill: str, amount: int = 1) -> None:
    """Улучшает навык (максимум 100)"""

def get_best_skills(self, count: int = 3) -> List[tuple]:
    """Возвращает лучшие навыки в формате [(name, value), ...]"""
```

---

### Personality

**Модуль:** `src/npc/personality.py`

Система личности NPC.

```python
from src.npc.personality import Personality, Trait
```

#### Атрибуты

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `traits` | `List[Trait]` | Черты характера |
| `openness` | `int` | Открытость (0-100) |
| `conscientiousness` | `int` | Добросовестность (0-100) |
| `agreeableness` | `int` | Доброжелательность (0-100) |
| `neuroticism` | `int` | Невротизм (0-100) |

#### Методы

```python
def has_trait(self, trait: Trait) -> bool:
    """Проверяет наличие черты"""

def add_trait(self, trait: Trait) -> bool:
    """Добавляет черту (если не противоречит). Возвращает успех."""

def get_social_modifier(self) -> float:
    """Модификатор социальных взаимодействий"""

def get_work_modifier(self) -> float:
    """Модификатор рабочей эффективности"""

def get_courage_modifier(self) -> float:
    """Модификатор смелости"""

def describe(self) -> str:
    """Текстовое описание личности"""

@classmethod
def generate_random(cls) -> 'Personality':
    """Создаёт случайную личность"""
```

---

### Trait

**Модуль:** `src/npc/personality.py`

Enum черт характера.

```python
class Trait(Enum):
    # Социальные
    EXTROVERT = "экстраверт"
    INTROVERT = "интроверт"
    FRIENDLY = "дружелюбный"
    HOSTILE = "враждебный"
    CHARISMATIC = "харизматичный"

    # Эмоциональные
    CHEERFUL = "весёлый"
    MELANCHOLIC = "меланхоличный"
    BRAVE = "храбрый"
    COWARD = "трусливый"

    # Моральные
    HONEST = "честный"
    DECEITFUL = "лживый"
    GENEROUS = "щедрый"
    GREEDY = "жадный"

    # Рабочие
    HARDWORKING = "трудолюбивый"
    LAZY = "ленивый"
    AMBITIOUS = "амбициозный"
    PERFECTIONIST = "перфекционист"
    # ... и другие
```

> **Примечание:** Противоположные черты взаимоисключающие (например, `EXTROVERT` и `INTROVERT`).

---

### Needs

**Модуль:** `src/npc/needs.py`

Система потребностей NPC.

```python
from src.npc.needs import Needs, Need, NeedState
```

#### Need (типы потребностей)

```python
class Need(Enum):
    HUNGER = "голод"
    ENERGY = "энергия"
    SOCIAL = "общение"
    FUN = "развлечение"
    COMFORT = "комфорт"
    HYGIENE = "гигиена"
    SAFETY = "безопасность"
    PURPOSE = "цель"
```

#### NeedState

```python
@dataclass
class NeedState:
    value: float = 100.0        # 0-100, где 100 = удовлетворена
    decay_rate: float = 1.0     # Скорость уменьшения в час
    priority_weight: float = 1.0 # Важность
```

**Методы NeedState:**
- `decay(hours: float)` — уменьшает значение
- `satisfy(amount: float)` — удовлетворяет потребность
- `is_critical()` — `value < 20`
- `is_low()` — `value < 40`
- `get_urgency()` — срочность (0-1)

#### Методы Needs

```python
def get(self, need: Need) -> NeedState:
    """Возвращает состояние потребности"""

def decay_all(self, hours: float = 1.0) -> None:
    """Уменьшает все потребности со временем"""

def satisfy(self, need: Need, amount: float) -> None:
    """Удовлетворяет конкретную потребность"""

def get_most_urgent(self) -> Optional[Need]:
    """Возвращает самую срочную потребность"""

def get_critical_needs(self) -> List[Need]:
    """Список критических потребностей"""

def get_overall_happiness(self) -> float:
    """Общий уровень счастья (0-100)"""

def get_mood(self) -> str:
    """Текстовое описание настроения"""

@classmethod
def generate_random(cls) -> 'Needs':
    """Создаёт потребности со случайными значениями"""
```

---

### Relationship

**Модуль:** `src/npc/relationships.py`

Отношения между двумя NPC.

```python
from src.npc.relationships import Relationship, RelationType
```

#### RelationType

```python
class RelationType(Enum):
    STRANGER = "незнакомец"
    ACQUAINTANCE = "знакомый"
    FRIEND = "друг"
    CLOSE_FRIEND = "близкий друг"
    BEST_FRIEND = "лучший друг"
    ROMANTIC = "романтические"
    SPOUSE = "супруг"
    RIVAL = "соперник"
    ENEMY = "враг"
    FAMILY = "семья"
    MENTOR = "наставник"
```

#### Атрибуты Relationship

| Атрибут | Тип | Диапазон | Описание |
|---------|-----|----------|----------|
| `target_id` | `str` | — | ID другого NPC |
| `friendship` | `float` | -100..100 | Дружба |
| `romance` | `float` | -100..100 | Романтика |
| `respect` | `float` | -100..100 | Уважение |
| `trust` | `float` | -100..100 | Доверие |
| `interactions_count` | `int` | — | Количество взаимодействий |
| `relationship_type` | `RelationType` | — | Тип отношений |

#### Методы

```python
def get_overall_opinion(self) -> float:
    """Общее мнение (-100..100)"""

def modify(
    self,
    friendship: float = 0,
    romance: float = 0,
    respect: float = 0,
    trust: float = 0
) -> None:
    """Изменяет показатели"""

def record_interaction(self, positive: bool, memory: Optional[str] = None) -> None:
    """Записывает взаимодействие"""

def decay(self, days: float = 1.0) -> None:
    """Отношения угасают без взаимодействия"""

def describe(self) -> str:
    """Описание отношений"""
```

---

### RelationshipManager

**Модуль:** `src/npc/relationships.py`

Менеджер всех отношений NPC.

```python
from src.npc.relationships import RelationshipManager
```

#### Методы

```python
def get_or_create(self, target_id: str) -> Relationship:
    """Получает или создаёт отношения с NPC"""

def get(self, target_id: str) -> Optional[Relationship]:
    """Получает отношения, если существуют"""

def get_friends(self) -> List[str]:
    """Список ID друзей (friendship > 30)"""

def get_enemies(self) -> List[str]:
    """Список ID врагов (opinion < -30)"""

def get_romantic_interests(self) -> List[str]:
    """Список романтических интересов"""

def get_best_friend(self) -> Optional[str]:
    """ID лучшего друга"""

def decay_all(self, days: float = 1.0) -> None:
    """Угасание всех отношений"""

def describe_social_life(self) -> str:
    """Описание социальной жизни"""
```

---

## Примеры использования

### Создание и запуск симуляции

```python
from src.core.simulation import Simulation
from src.core.config import Config, PRESET_ACCELERATED

# Создаём конфигурацию
config = PRESET_ACCELERATED
config.initial_population = 30

# Создаём и инициализируем симуляцию
sim = Simulation(config)
events = sim.initialize()

# Запускаем на 100 лет
for year in range(100):
    for day in range(config.days_per_year()):
        events = sim.update(hours=24)

        # Выводим важные события
        for e in events:
            if "открыл" in e or "умер" in e:
                print(f"[Год {sim.year}] {e}")

    print(sim.get_status())
```

### Подписка на события

```python
from src.core.events import event_bus, EventType, EventImportance

def log_historic_event(event):
    if event.importance.value >= EventImportance.MAJOR.value:
        print(f"ИСТОРИЧЕСКОЕ СОБЫТИЕ: {event.format_description()}")

event_bus.subscribe_all(log_historic_event)
```

### Работа с NPC

```python
from src.npc.character import NPC, Gender, Occupation

# Создание случайного NPC
npc = NPC.generate_random(name="Иван", gender=Gender.MALE)

# Вывод информации
print(npc.get_full_name())
print(npc.describe_appearance())
print(npc.personality.describe())
print(npc.needs.get_mood())

# Взаимодействие двух NPC
other = NPC.generate_random()
result = npc.interact_with(other, "разговор")
print(f"Изменение отношений: {result['relationship_change']}")
```

### Отслеживание отношений

```python
from src.npc.relationships import RelationshipManager, RelationType

# Получение друзей NPC
friends = npc.relationships.get_friends()
print(f"Друзья: {friends}")

# Изменение отношений
rel = npc.relationships.get_or_create(other.id)
rel.modify(friendship=20, trust=10)
print(rel.describe())
```

---

## Вспомогательные функции

### Фабрики событий

**Модуль:** `src/core/events.py`

```python
def create_birth_event(npc_id: str, mother_id: str, father_id: str,
                       year: int, location_id: str = None) -> Event:
    """Создаёт событие рождения"""

def create_death_event(npc_id: str, cause: str, age: int,
                       year: int, location_id: str = None) -> Event:
    """Создаёт событие смерти"""

def create_technology_event(discoverer_id: str, tech_name: str,
                            year: int, location_id: str = None) -> Event:
    """Создаёт событие открытия технологии"""

def create_class_emergence_event(class_name: str, members: List[str],
                                 year: int) -> Event:
    """Создаёт событие возникновения класса"""
```

---

## Архитектура

Симуляция следует принципу марксистской диалектики:

1. **БАЗИС (экономика)** обновляется первым
   - Ресурсы, технологии, собственность

2. **НАДСТРОЙКА (культура)** следует за базисом
   - Верования, традиции, нормы

3. **NPC** действуют в рамках базиса и надстройки
   - Принимают решения на основе потребностей и культуры
