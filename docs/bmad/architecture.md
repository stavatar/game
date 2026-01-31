# Architecture Document

## Базис и Надстройка - Симулятор Развития Общества

**Версия:** 1.0
**Дата:** 2026-01-31
**Статус:** Утверждена
**Автор:** Architect Agent (BMAD Method)

---

## 1. Обзор Системы (System Overview)

### 1.1 Архитектурное Видение

Система построена по принципу **многоуровневой агентной симуляции** с четырьмя основными слоями:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                                │
│                 (CLI Interface, Visualization)                       │
├─────────────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER                                 │
│              (Simulation Loop, Event System)                         │
├─────────────────────────────────────────────────────────────────────┤
│                      DOMAIN LAYER                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ ECONOMY  │→│ SOCIETY  │→│ CULTURE  │→│   NPC    │           │
│  │  (Base)  │  │(Structure)│  │(Superstr.)│  │ (Agents) │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
├─────────────────────────────────────────────────────────────────────┤
│                   INFRASTRUCTURE LAYER                               │
│              (World, Map, Time, Climate)                            │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Ключевые Архитектурные Решения

| ID | Решение | Обоснование |
|----|---------|-------------|
| ADR-001 | Марксистский порядок обновления: Базис → Общество → Надстройка → NPC | Экономика определяет всё остальное |
| ADR-002 | Event-Driven Architecture через EventBus | Слабая связанность, расширяемость |
| ADR-003 | BDI для AI NPC | Автономность и реалистичность поведения |
| ADR-004 | Emergent-системы (классы, культура не задаются жёстко) | Философская основа проекта |
| ADR-005 | Composition over Inheritance | Гибкость и тестируемость |

---

## 2. Технологический Стек (Technology Stack)

### 2.1 Core Technologies

| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| Язык | Python | 3.11+ | Основной язык разработки |
| Типизация | typing, dataclasses | stdlib | Статическая типизация |
| Enums | enum | stdlib | Типобезопасные перечисления |
| Random | random | stdlib | Генерация случайных событий |

### 2.2 Архитектурные Паттерны

| Паттерн | Применение | Файлы |
|---------|------------|-------|
| **Observer/Pub-Sub** | Система событий | `core/events.py` |
| **State Machine** | Состояния NPC, сезоны | `npc/character.py`, `world/climate.py` |
| **Strategy** | Способы производства, поведение | `economy/production.py`, `ai/behavior.py` |
| **Factory** | Создание NPC, локаций, ресурсов | `core/simulation.py` |
| **Dependency Injection** | Передача World, Config | Везде |
| **Repository** | Хранение сущностей | `world/world.py` |

### 2.3 Зависимости

```
src/
├── core/          # Нет внешних зависимостей
├── world/         # → core
├── economy/       # → core, world
├── society/       # → core, world, economy
├── culture/       # → core, world, economy, society
├── npc/           # → core, world, economy, society, culture
├── ai/            # → npc
├── game/          # → all
└── data/          # Нет зависимостей
```

---

## 3. Компонентная Архитектура (Component Architecture)

### 3.1 Core Module (`src/core/`)

#### 3.1.1 config.py
**Назначение:** Централизованная конфигурация всей системы.

```python
@dataclass
class SimulationConfig:
    # Параметры мира
    world_width: int = 40
    world_height: int = 40
    initial_population: int = 15

    # Параметры демографии
    base_fertility_rate: float = 0.3
    base_mortality_rate: float = 0.05
    max_age: int = 80

    # Экономические параметры
    tech_progress_speed: float = 1.0

    # Культурные параметры
    belief_influence: float = 0.5
```

**Пресеты:**
- `REALISTIC` — медленное, реалистичное развитие
- `ACCELERATED` — ускоренное для тестирования
- `SANDBOX` — максимальная гибкость

#### 3.1.2 events.py
**Назначение:** Event-Driven архитектура через Pub/Sub.

```python
class EventType(Enum):
    # Lifecycle Events
    NPC_BORN = "npc_born"
    NPC_DIED = "npc_died"
    NPC_AGED = "npc_aged"

    # Economic Events
    RESOURCE_GATHERED = "resource_gathered"
    TECHNOLOGY_DISCOVERED = "technology_discovered"

    # Social Events
    MARRIAGE = "marriage"
    CLASS_EMERGED = "class_emerged"

    # Cultural Events
    BELIEF_FORMED = "belief_formed"
    TRADITION_ESTABLISHED = "tradition_established"

    # Climate Events
    SEASON_CHANGED = "season_changed"
    CATASTROPHE = "catastrophe"

class EventImportance(Enum):
    TRIVIAL = 1      # Рутинные события
    MINOR = 2        # Небольшие события
    NOTABLE = 3      # Заметные события
    IMPORTANT = 4    # Важные события
    MAJOR = 5        # Крупные события
    HISTORIC = 6     # Исторические события

class EventBus:
    def subscribe(self, event_type: EventType, handler: Callable) -> None
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None
    def publish(self, event: Event) -> None
```

#### 3.1.3 simulation.py
**Назначение:** Главный цикл симуляции, координация подсистем.

```python
class Simulation:
    def __init__(self, config: SimulationConfig):
        self.world = World(config)
        self.event_bus = EventBus()
        self.time_system = TimeSystem()

    def update(self) -> None:
        """Один тик симуляции (1 час)"""
        # 1. Обновляем время
        self.time_system.advance()

        # 2. БАЗИС обновляется первым
        self._update_economy()

        # 3. Социальная структура
        self._update_society()

        # 4. НАДСТРОЙКА следует за базисом
        self._update_culture()

        # 5. NPC действуют
        self._update_npcs()

        # 6. Климат и катаклизмы
        self._update_climate()
```

### 3.2 World Module (`src/world/`)

#### 3.2.1 world.py
**Назначение:** Главный контейнер мира.

```python
class World:
    npcs: Dict[UUID, Character]          # Все NPC по ID
    locations: Dict[Tuple[int,int], Location]  # Локации по координатам
    families: Dict[UUID, Family]         # Семьи

    def get_npc(self, npc_id: UUID) -> Character
    def get_npcs_at(self, x: int, y: int) -> List[Character]
    def move_npc(self, npc: Character, target: Location) -> None
    def add_npc(self, npc: Character) -> None
    def remove_npc(self, npc_id: UUID) -> None
```

#### 3.2.2 map.py
**Назначение:** Карта мира как сетка.

```python
class WorldMap:
    width: int
    height: int
    grid: List[List[MapCell]]

    def get_cell(self, x: int, y: int) -> MapCell
    def get_neighbors(self, x: int, y: int) -> List[MapCell]
    def find_path(self, start: Tuple, end: Tuple) -> List[Tuple]
```

#### 3.2.3 location.py
**Назначение:** Конкретная локация на карте.

```python
class LocationType(Enum):
    FIELD = "field"
    FOREST = "forest"
    LAKE = "lake"
    SETTLEMENT = "settlement"
    CAVE = "cave"
    MOUNTAIN = "mountain"

class Location:
    type: LocationType
    coordinates: Tuple[int, int]
    npcs: Set[UUID]              # NPC в локации
    resources: Inventory         # Ресурсы локации
    buildings: List[Building]    # Строения
```

#### 3.2.4 climate.py
**Назначение:** Климатическая система и катаклизмы.

```python
class Season(Enum):
    SPRING = "spring"   # Дни 1-90
    SUMMER = "summer"   # Дни 91-180
    AUTUMN = "autumn"   # Дни 181-270
    WINTER = "winter"   # Дни 271-360

class Catastrophe(Enum):
    DROUGHT = "drought"
    FLOOD = "flood"
    PLAGUE = "plague"
    FAMINE = "famine"
    FIRE = "fire"
    HARSH_WINTER = "harsh_winter"
    LOCUSTS = "locusts"

class ClimateSystem:
    def get_current_season(self) -> Season
    def get_temperature(self) -> float
    def get_precipitation(self) -> float
    def check_catastrophe(self) -> Optional[Catastrophe]
    def apply_catastrophe_effects(self, catastrophe: Catastrophe) -> None
```

#### 3.2.5 time_system.py
**Назначение:** Система времени.

```python
class TimeOfDay(Enum):
    NIGHT = "night"       # 22:00 - 05:59
    DAWN = "dawn"         # 06:00 - 07:59
    DAY = "day"           # 08:00 - 17:59
    DUSK = "dusk"         # 18:00 - 21:59

class TimeSystem:
    hour: int              # 0-23
    day: int               # 1-30
    month: int             # 1-12
    year: int              # 1+

    def advance(self, hours: int = 1) -> None
    def get_time_of_day(self) -> TimeOfDay
    def get_season(self) -> Season
    def get_total_hours(self) -> int
```

### 3.3 Economy Module (`src/economy/`)

#### 3.3.1 resources.py
**Назначение:** Система ресурсов и инвентари.

```python
class ResourceType(Enum):
    # Базовые
    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    STONE = "stone"

    # Обработанные
    LEATHER = "leather"
    CLOTH = "cloth"
    METAL = "metal"

    # Редкие
    ORE = "ore"
    GOLD = "gold"

class Inventory:
    resources: Dict[ResourceType, float]
    capacity: float

    def add(self, resource: ResourceType, amount: float) -> bool
    def remove(self, resource: ResourceType, amount: float) -> bool
    def get(self, resource: ResourceType) -> float
    def has(self, resource: ResourceType, amount: float) -> bool
```

#### 3.3.2 production.py
**Назначение:** Методы производства.

```python
class ProductionMethod:
    name: str
    inputs: Dict[ResourceType, float]    # Требуемые ресурсы
    outputs: Dict[ResourceType, float]   # Производимые ресурсы
    required_tech: Optional[Technology]  # Нужная технология
    required_tools: List[ResourceType]   # Нужные инструменты
    skill_required: str                   # Требуемый навык
    base_duration: int                    # Базовое время (часы)

    def can_perform(self, npc: Character, location: Location) -> bool
    def perform(self, npc: Character, location: Location) -> ProductionResult

# Примеры методов:
GATHERING = ProductionMethod(
    name="gathering",
    inputs={},
    outputs={ResourceType.FOOD: 2.0},
    required_tech=Technology.BASIC_GATHERING,
    base_duration=2
)

HUNTING = ProductionMethod(
    name="hunting",
    inputs={},
    outputs={ResourceType.FOOD: 5.0, ResourceType.LEATHER: 1.0},
    required_tech=Technology.HUNTING,
    required_tools=[ResourceType.WEAPON],
    base_duration=4
)
```

#### 3.3.3 property.py
**Назначение:** Система собственности.

```python
class PropertyType(Enum):
    COMMUNAL = "communal"    # Общинная
    PERSONAL = "personal"    # Личная (личные вещи)
    PRIVATE = "private"      # Частная (средства производства)
    FAMILY = "family"        # Семейная

class PropertyCategory(Enum):
    LAND = "land"
    TOOLS = "tools"
    LIVESTOCK = "livestock"
    BUILDING = "building"
    RESOURCES = "resources"
    KNOWLEDGE = "knowledge"

class PropertyRight:
    owner_id: UUID
    property_type: PropertyType
    category: PropertyCategory
    can_use: bool
    can_transfer: bool
    can_inherit: bool

    def transfer_to(self, new_owner_id: UUID) -> None
    def inherit(self, heir_id: UUID) -> None
```

#### 3.3.4 technology.py
**Назначение:** Технологическое древо.

```python
class Era(Enum):
    PRIMITIVE = "primitive"
    STONE_AGE = "stone_age"
    BRONZE_AGE = "bronze_age"
    IRON_AGE = "iron_age"

class Technology:
    name: str
    era: Era
    prerequisites: List[Technology]
    unlocks: List[ProductionMethod]
    discovery_difficulty: float

class TechnologyTree:
    technologies: Dict[str, Technology]

    def can_discover(self, tech: Technology, known: Set[Technology]) -> bool
    def get_available(self, known: Set[Technology]) -> List[Technology]

# Пример древа:
# PRIMITIVE:
#   ├── STONE_WORKING
#   ├── FIRE_MAKING
#   ├── HUNTING
#   ├── GATHERING
#   └── FISHING
#
# STONE_AGE:
#   ├── BOW_AND_ARROW (← HUNTING + STONE_WORKING)
#   ├── POTTERY (← FIRE_MAKING)
#   ├── WEAVING (← GATHERING)
#   ├── BASIC_AGRICULTURE (← GATHERING + STONE_WORKING)
#   ├── ANIMAL_DOMESTICATION (← HUNTING)
#   └── SHELTER_BUILDING (← STONE_WORKING)
```

### 3.4 Society Module (`src/society/`)

#### 3.4.1 family.py
**Назначение:** Семейная система.

```python
class Family:
    id: UUID
    name: str
    members: Set[UUID]          # ID членов семьи
    head: UUID                  # Глава семьи
    property: List[PropertyRight]

    def add_member(self, npc_id: UUID) -> None
    def remove_member(self, npc_id: UUID) -> None
    def set_head(self, npc_id: UUID) -> None
    def get_inheritance(self) -> Dict[UUID, List[PropertyRight]]

class Marriage:
    spouse1_id: UUID
    spouse2_id: UUID
    year_married: int
    children: List[UUID]

    def create_family(self) -> Family
    def divorce(self) -> None
```

#### 3.4.2 demography.py
**Назначение:** Демографические процессы.

```python
class LifeStage(Enum):
    INFANT = "infant"       # 0-2
    CHILD = "child"         # 3-12
    TEENAGER = "teenager"   # 13-17
    YOUNG_ADULT = "young"   # 18-30
    ADULT = "adult"         # 31-50
    MATURE = "mature"       # 51-65
    ELDER = "elder"         # 66+

class DemographySystem:
    def get_life_stage(self, age: int) -> LifeStage
    def calculate_mortality_rate(self, npc: Character) -> float
    def calculate_fertility(self, npc: Character) -> float
    def process_birth(self, mother: Character, father: Character) -> Character
    def process_death(self, npc: Character) -> DeathEvent
```

#### 3.4.3 classes.py
**Назначение:** Классовая система (EMERGENT).

```python
class ClassType(Enum):
    """Класс определяется отношением к средствам производства"""
    COMMUNAL_MEMBER = "communal"      # Член общины (до появления частной собственности)
    LANDOWNER = "landowner"           # Землевладелец
    LANDLESS = "landless"             # Безземельный
    CRAFTSMAN = "craftsman"           # Ремесленник (владеет инструментами)
    LABORER = "laborer"               # Работник (не владеет ничем)

class ClassSystem:
    def determine_class(self, npc: Character) -> ClassType:
        """
        EMERGENT: Класс определяется владением, не задаётся!
        """
        owned_land = self.get_owned_land(npc)
        owned_tools = self.get_owned_tools(npc)

        if self.is_communal_society():
            return ClassType.COMMUNAL_MEMBER
        elif owned_land > 0:
            return ClassType.LANDOWNER
        elif owned_tools > 0:
            return ClassType.CRAFTSMAN
        elif owned_land == 0 and owned_tools == 0:
            return ClassType.LABORER
        else:
            return ClassType.LANDLESS

    def calculate_class_consciousness(self, npc: Character) -> float
    def detect_class_conflict(self) -> Optional[ClassConflict]
```

### 3.5 Culture Module (`src/culture/`)

#### 3.5.1 beliefs.py
**Назначение:** Верования и идеология (EMERGENT).

```python
class BeliefType(Enum):
    # Примитивные
    ANIMISM = "animism"              # Духи в природе
    TOTEMISM = "totemism"            # Священные животные
    ANCESTOR_WORSHIP = "ancestors"   # Культ предков

    # Связанные с собственностью
    PROPERTY_SACRED = "property_sacred"      # Собственность священна
    COLLECTIVE_GOOD = "collective_good"      # Общинные ценности

    # Социальные
    HIERARCHY_NATURAL = "hierarchy_natural"  # Иерархия естественна
    EQUALITY_IDEAL = "equality_ideal"        # Равенство — идеал

class BeliefOrigin(Enum):
    """Откуда возникло верование"""
    NATURAL = "natural"          # Из наблюдения природы
    ECONOMIC = "economic"        # Из экономических условий
    SOCIAL = "social"            # Из социальных отношений
    CRISIS = "crisis"            # Из кризиса/катаклизма

class Belief:
    type: BeliefType
    origin: BeliefOrigin
    strength: float                     # 0.0 - 1.0
    benefiting_class: Optional[ClassType]  # Какому классу выгодно
    contradicts: List[BeliefType]       # С чем конфликтует

class BeliefSystem:
    def form_belief(self, conditions: Dict) -> Optional[Belief]:
        """
        EMERGENT: Верования возникают из условий!

        Примеры:
        - Появление частной собственности → PROPERTY_SACRED
        - Катаклизм → ANIMISM усиливается
        - Классовое неравенство → HIERARCHY_NATURAL (для верхов)
                                 → EQUALITY_IDEAL (для низов)
        """
        pass
```

#### 3.5.2 traditions.py
**Назначение:** Традиции и ритуалы.

```python
class Tradition:
    name: str
    related_beliefs: List[BeliefType]
    season: Optional[Season]           # Когда проводится
    required_resources: Dict[ResourceType, float]
    social_effect: Dict[str, float]    # Влияние на общество

class TraditionSystem:
    def check_tradition_emergence(self, society_state: Dict) -> Optional[Tradition]
    def perform_tradition(self, tradition: Tradition) -> TraditionResult
```

#### 3.5.3 norms.py
**Назначение:** Социальные нормы.

```python
class SocialNorm:
    name: str
    description: str
    violation_penalty: float           # Штраф за нарушение
    enforcement_strength: float        # Как строго соблюдается
    related_beliefs: List[BeliefType]

class NormSystem:
    def check_norm_violation(self, action: Action, npc: Character) -> bool
    def apply_penalty(self, npc: Character, norm: SocialNorm) -> None
```

### 3.6 NPC Module (`src/npc/`)

#### 3.6.1 character.py
**Назначение:** Основной класс NPC.

```python
@dataclass
class Stats:
    strength: int       # 1-20, физическая сила
    dexterity: int      # 1-20, ловкость
    intelligence: int   # 1-20, интеллект
    charisma: int       # 1-20, харизма
    luck: int           # 1-20, удача

@dataclass
class Skills:
    combat: float       # 0.0 - 100.0
    crafting: float
    trading: float
    farming: float
    medicine: float
    leadership: float

class Character:
    id: UUID
    name: str
    gender: Gender
    age: int
    stats: Stats
    skills: Skills
    personality: Personality
    needs: NeedSystem
    memory: MemorySystem
    relationships: RelationshipSystem
    inventory: Inventory
    location: Location

    # Генетика
    father_id: Optional[UUID]
    mother_id: Optional[UUID]
    genetic_traits: GeneticTraits

    # BDI
    bdi: BDISystem

    def update(self, world: World) -> None
    def perform_action(self, action: Action) -> ActionResult
```

#### 3.6.2 personality.py
**Назначение:** Система личности.

```python
class Trait(Enum):
    # Социальные
    EXTROVERT = "extrovert"
    INTROVERT = "introvert"
    FRIENDLY = "friendly"
    HOSTILE = "hostile"

    # Рабочие
    HARDWORKING = "hardworking"
    LAZY = "lazy"
    CAREFUL = "careful"
    RECKLESS = "reckless"

    # Экономические
    GREEDY = "greedy"
    GENEROUS = "generous"
    FRUGAL = "frugal"
    WASTEFUL = "wasteful"

    # Эмоциональные
    BRAVE = "brave"
    COWARDLY = "cowardly"
    CALM = "calm"
    EMOTIONAL = "emotional"

class Personality:
    traits: Dict[Trait, float]  # trait -> strength (0.0 - 1.0)

    def get_trait_strength(self, trait: Trait) -> float
    def affects_decision(self, action: Action) -> float  # Модификатор решения
```

#### 3.6.3 needs.py
**Назначение:** Система потребностей.

```python
class NeedType(Enum):
    HUNGER = "hunger"
    THIRST = "thirst"
    SLEEP = "sleep"
    SOCIAL = "social"
    ENTERTAINMENT = "entertainment"
    SAFETY = "safety"
    COMFORT = "comfort"

class Need:
    type: NeedType
    current: float      # 0.0 (критично) - 1.0 (удовлетворено)
    decay_rate: float   # Скорость убывания
    priority: int       # Приоритет при выборе действий

class NeedSystem:
    needs: Dict[NeedType, Need]

    def update(self, hours: int) -> None
    def get_most_urgent(self) -> Need
    def satisfy(self, need_type: NeedType, amount: float) -> None
```

#### 3.6.4 relationships.py
**Назначение:** Отношения между NPC.

```python
class RelationType(Enum):
    FRIEND = "friend"
    ENEMY = "enemy"
    ROMANTIC = "romantic"
    FAMILY = "family"
    COLLEAGUE = "colleague"
    RIVAL = "rival"

class Relationship:
    target_id: UUID
    type: RelationType
    strength: float         # -1.0 (враг) до 1.0 (близкий друг)
    trust: float            # 0.0 - 1.0
    history: List[Interaction]

class RelationshipSystem:
    relationships: Dict[UUID, Relationship]

    def get_relationship(self, other_id: UUID) -> Relationship
    def update_relationship(self, other_id: UUID, interaction: Interaction) -> None
    def get_friends(self) -> List[UUID]
    def get_enemies(self) -> List[UUID]
```

#### 3.6.5 genetics.py
**Назначение:** Генетическая система.

```python
class Gene:
    name: str
    dominant: bool
    effect: Dict[str, float]  # Влияние на характеристики

class GeneticTraits:
    genes: Dict[str, Tuple[Gene, Gene]]  # Пары генов (от отца и матери)

    def express(self) -> Dict[str, float]:
        """Экспрессия генов в характеристики"""
        pass

class GeneticSystem:
    def inherit(self, father: Character, mother: Character) -> GeneticTraits:
        """Наследование генов с мутациями"""
        pass

    def mutate(self, genes: GeneticTraits) -> GeneticTraits:
        """Случайные мутации"""
        pass
```

#### 3.6.6 memory.py
**Назначение:** Система памяти (Generative Agents).

```python
class Memory:
    id: UUID
    timestamp: int              # Когда произошло
    description: str            # Что произошло
    importance: float           # 0.0 - 1.0
    emotional_valence: float    # -1.0 (плохо) до 1.0 (хорошо)
    participants: List[UUID]    # Кто участвовал
    location: Tuple[int, int]   # Где произошло
    related_memories: List[UUID]

class Reflection:
    """Вывод из опыта"""
    id: UUID
    description: str            # "Иван часто помогает — он друг"
    supporting_memories: List[UUID]
    confidence: float           # Уверенность в выводе

class MemorySystem:
    memories: List[Memory]      # Поток памяти
    reflections: List[Reflection]

    def add_memory(self, memory: Memory) -> None
    def retrieve_relevant(self, context: str) -> List[Memory]
    def reflect(self) -> List[Reflection]
    def forget_unimportant(self) -> None
```

#### 3.6.7 ai/bdi.py
**Назначение:** BDI-архитектура.

```python
class Belief:
    """Убеждение о мире"""
    subject: str
    predicate: str
    confidence: float
    timestamp: int

class Desire:
    """Желание/Цель"""
    description: str
    priority: float
    deadline: Optional[int]
    satisfied_by: List[Action]

class Intention:
    """Выбранный план"""
    goal: Desire
    plan: List[Action]
    current_step: int
    status: IntentionStatus

class BDISystem:
    beliefs: List[Belief]
    desires: List[Desire]
    intentions: List[Intention]

    def perceive(self, world: World) -> None:
        """Обновление убеждений из мира"""
        pass

    def deliberate(self) -> Desire:
        """Выбор цели из желаний"""
        pass

    def plan(self, desire: Desire) -> Intention:
        """Создание плана достижения цели"""
        pass

    def execute(self) -> Action:
        """Выполнение следующего шага плана"""
        pass
```

### 3.7 AI Module (`src/ai/`)

#### 3.7.1 behavior.py
**Назначение:** Система принятия решений.

```python
class Action(Enum):
    GATHER = "gather"
    HUNT = "hunt"
    EAT = "eat"
    SLEEP = "sleep"
    SOCIALIZE = "socialize"
    WORK = "work"
    REST = "rest"
    TRADE = "trade"
    BUILD = "build"
    CRAFT = "craft"

class BehaviorSystem:
    def decide_action(self, npc: Character, world: World) -> Action:
        """
        Алгоритм принятия решений:
        1. Проверить критические потребности (голод < 0.2 → есть)
        2. Учесть время суток (ночь → спать)
        3. Получить желания из BDI
        4. Применить модификаторы личности
        5. Добавить случайность для реалистичности
        6. Выбрать действие с наивысшим приоритетом
        """
        pass

    def evaluate_action(self, action: Action, npc: Character) -> float:
        """Оценка полезности действия"""
        pass
```

### 3.8 Game Module (`src/game/`)

#### 3.8.1 engine.py
**Назначение:** Игровой движок и CLI.

```python
class GameEngine:
    simulation: Simulation
    running: bool

    def run(self) -> None:
        """Главный цикл игры"""
        pass

    def process_command(self, command: str) -> None:
        """Обработка команд пользователя"""
        pass

    def display_status(self) -> None:
        """Отображение статуса мира"""
        pass

    def display_npc(self, npc_id: UUID) -> None:
        """Информация о конкретном NPC"""
        pass
```

---

## 4. Потоки Данных (Data Flows)

### 4.1 Главный Цикл Обновления

```
┌──────────────────────────────────────────────────────────────┐
│                    MAIN UPDATE LOOP                           │
│                     (каждый час)                             │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. TIME SYSTEM                                               │
│    └─ advance() → hour++, check day/month/year/season        │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. ECONOMY (БАЗИС)                                           │
│    ├─ resources.update() → regenerate, decay                 │
│    ├─ production.update() → process active productions       │
│    ├─ technology.update() → check discoveries                │
│    └─ property.update() → handle transfers, inheritance      │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. SOCIETY                                                   │
│    ├─ family.update() → marriages, births, deaths           │
│    ├─ demography.update() → aging, mortality                │
│    └─ classes.update() → recalculate classes (EMERGENT)     │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. CULTURE (НАДСТРОЙКА)                                      │
│    ├─ beliefs.update() → form/strengthen beliefs            │
│    ├─ traditions.update() → check/perform traditions        │
│    └─ norms.update() → enforce norms                        │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. NPC ACTIONS                                               │
│    for each NPC:                                             │
│    ├─ needs.update() → decay needs                          │
│    ├─ bdi.perceive() → update beliefs                       │
│    ├─ behavior.decide() → choose action                     │
│    ├─ action.execute() → perform action                     │
│    └─ memory.add() → remember event                         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. CLIMATE                                                   │
│    ├─ check_season_change() → emit SEASON_CHANGED           │
│    └─ check_catastrophe() → maybe emit CATASTROPHE          │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Формирование Верований (Emergent)

```
Economic Conditions                    Belief Formation
─────────────────                     ─────────────────

Surplus Production ────────────────────► PROPERTY_SACRED
        │                                    │
        ▼                                    ▼
Private Property ─────────────────────► "Property is
        │                                 god-given"
        ▼                                    │
Class Division ────────────────────────► HIERARCHY_NATURAL
        │                                    │
        ▼                                    ▼
Exploitation ──────────────────────────► "Natural order"
                                         (benefits owners)
```

### 4.3 BDI Цикл

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PERCEIVE   │────►│  BELIEFS    │────►│ DELIBERATE  │
│  (World)    │     │  (Update)   │     │  (Goals)    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   EXECUTE   │◄────│ INTENTIONS  │◄────│    PLAN     │
│  (Action)   │     │  (Select)   │     │  (Create)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 5. Модель Данных (Data Models)

### 5.1 Entity-Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   WORLD      │       │   LOCATION   │       │   RESOURCE   │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id           │       │ id           │       │ type         │
│ name         │──1:N──│ coordinates  │──1:N──│ amount       │
│ year         │       │ type         │       │ quality      │
│ population   │       │ capacity     │       └──────────────┘
└──────────────┘       └──────────────┘
                              │
                              │ N:M
                              ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   FAMILY     │       │  CHARACTER   │       │  TECHNOLOGY  │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id           │       │ id           │       │ name         │
│ name         │──1:N──│ name         │──N:M──│ era          │
│ head_id      │       │ age          │       │ prerequisites│
│ property     │       │ gender       │       │ effects      │
└──────────────┘       │ stats        │       └──────────────┘
                       │ skills       │
                       │ personality  │
                       │ location_id  │
                       │ family_id    │
                       └──────────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
       ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
       │   MEMORY     │ │ RELATIONSHIP │ │   BELIEF     │
       ├──────────────┤ ├──────────────┤ ├──────────────┤
       │ id           │ │ npc1_id      │ │ type         │
       │ description  │ │ npc2_id      │ │ origin       │
       │ importance   │ │ type         │ │ strength     │
       │ timestamp    │ │ strength     │ │ class_benefit│
       └──────────────┘ └──────────────┘ └──────────────┘
```

### 5.2 Состояния (States)

#### NPC Lifecycle State

```
       BORN
         │
         ▼
    ┌─────────┐
    │ INFANT  │ (0-2)
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  CHILD  │ (3-12)
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │TEENAGER │ (13-17)
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ YOUNG   │ (18-30)
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ ADULT   │ (31-50)
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ MATURE  │ (51-65)
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ ELDER   │ (66+)
    └────┬────┘
         │
         ▼
       DEAD
```

#### Economic Formation State (Marxist)

```
    ┌────────────────────┐
    │ PRIMITIVE COMMUNISM│
    │ (No private prop)  │
    └─────────┬──────────┘
              │ Surplus production
              ▼
    ┌────────────────────┐
    │ TRANSITION         │
    │ (Personal property)│
    └─────────┬──────────┘
              │ Accumulation
              ▼
    ┌────────────────────┐
    │ PRIVATE PROPERTY   │
    │ (Class formation)  │
    └─────────┬──────────┘
              │ Class conflict
              ▼
    ┌────────────────────┐
    │ DEVELOPED CLASSES  │
    │ (Exploitation)     │
    └────────────────────┘
```

---

## 6. Интеграции (Integrations)

### 6.1 Текущие

| Интеграция | Описание | Статус |
|------------|----------|--------|
| CLI | Командная строка | Done |
| File I/O | Чтение/запись конфигов | Planned |
| JSON Export | Экспорт статистики | Planned |

### 6.2 Планируемые

| Интеграция | Описание | Приоритет |
|------------|----------|-----------|
| Pygame | Графический интерфейс | P2 |
| SQLite | Сохранение мира | P2 |
| LLM API | Диалоги NPC | P3 |
| Matplotlib | Графики статистики | P2 |

---

## 7. Развёртывание (Deployment)

### 7.1 Требования

```
Python 3.11+
No external dependencies for core
Optional: pygame for graphics (planned)
```

### 7.2 Структура Проекта

```
game/
├── main.py                 # Entry point
├── README.md               # User documentation
├── docs/
│   ├── README.md           # Architecture docs
│   └── bmad/               # BMAD documentation
│       ├── PRD.md
│       ├── architecture.md
│       ├── epics-and-stories.md
│       ├── tech-specs/
│       └── stories/
└── src/
    ├── __init__.py
    ├── core/
    ├── world/
    ├── economy/
    ├── society/
    ├── culture/
    ├── npc/
    ├── ai/
    ├── game/
    └── data/
```

### 7.3 Запуск

```bash
cd /home/user/game
python3 main.py
```

---

## 8. Безопасность (Security)

### 8.1 Принципы

- Нет сетевого взаимодействия (локальная симуляция)
- Нет пользовательского ввода кроме CLI команд
- Все данные хранятся в памяти (нет файловых операций в ядре)

### 8.2 Валидация

- Все параметры конфигурации проверяются на корректность
- UUID используются для идентификации сущностей
- Границы значений проверяются (stats 1-20, needs 0-1, etc.)

---

## 9. Исследовательские Материалы (Research References)

Архитектурные решения в этом проекте основаны на исследованиях лучших практик в области агентных симуляций и марксистской теории.

### 9.1 Связь с Исследованиями

| Компонент | Исследование | Применённые Паттерны |
|-----------|-------------|---------------------|
| NPC AI (src/npc/, src/ai/) | [Agent Simulations](research/agent-simulations.md) | BDI Architecture, Memory Stream, Reflection |
| Behavior System | [Agent Simulations](research/agent-simulations.md) | Utility AI (The Sims), Needs-based decisions |
| Class System (src/society/) | [Marxism Guide](research/marxism-guide.md) | Emergent Classes, Property Relations |
| Culture System (src/culture/) | [Marxism Guide](research/marxism-guide.md) | Base→Superstructure, Ideology Formation |
| Economy (src/economy/) | [Marxism Guide](research/marxism-guide.md) | Surplus Value, Modes of Production |
| Simulation Loop | [Agent Simulations](research/agent-simulations.md) | Emergent Narrative (Dwarf Fortress) |

### 9.2 Ключевые Архитектурные Влияния

**От Generative Agents (Stanford):**
- Memory Stream архитектура в `src/npc/memory.py`
- Reflection механизм для формирования выводов
- Planning на основе памяти и целей

**От BDI Architecture:**
- Beliefs-Desires-Intentions цикл в `src/ai/bdi.py`
- Perception → Deliberation → Planning → Execution

**От Utility AI (The Sims):**
- Needs-based decision making
- Utility scores для выбора действий

**От Marxist Theory:**
- Порядок обновления: Economy → Society → Culture
- Emergent classes из property relations
- Superstructure зависит от Base

### 9.3 Рекомендации для Разработчиков

Перед началом работы рекомендуется ознакомиться с:

1. **[Agent Simulations Guide](research/agent-simulations.md)** — для понимания AI архитектуры NPC
2. **[Marxism Guide](research/marxism-guide.md)** — для понимания модели общества

---

## 10. История Изменений (Change History)

| Версия | Дата | Автор | Описание |
|--------|------|-------|----------|
| 1.0 | 2026-01-31 | Architect Agent | Первоначальная версия |
| 1.1 | 2026-01-31 | Architect Agent | Добавлены ссылки на исследования |

---

*Документ создан по методологии [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)*
