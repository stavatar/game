# Data Models Specification

## Базис и Надстройка - Симулятор Развития Общества

**Версия:** 1.0
**Дата:** 2026-01-31
**Автор:** Architect Agent (BMAD Method)

---

## 1. Overview

Данный документ описывает все модели данных проекта, их структуру, связи и ограничения.

---

## 2. Core Models

### 2.1 SimulationConfig

**Файл:** `src/core/config.py`

```python
@dataclass
class SimulationConfig:
    """Центральная конфигурация симуляции"""

    # World Parameters
    world_width: int = 40           # Ширина карты
    world_height: int = 40          # Высота карты
    initial_population: int = 15    # Начальная популяция
    initial_families: int = 4       # Начальные семьи

    # Demography Parameters
    base_fertility_rate: float = 0.3    # Базовая рождаемость
    base_mortality_rate: float = 0.05   # Базовая смертность
    max_age: int = 80                   # Максимальный возраст
    fertile_age_min: int = 16           # Минимальный детородный возраст
    fertile_age_max: int = 45           # Максимальный детородный возраст

    # Economic Parameters
    tech_progress_speed: float = 1.0    # Скорость тех. прогресса
    resource_regeneration: float = 0.1  # Регенерация ресурсов

    # Cultural Parameters
    belief_influence: float = 0.5       # Влияние верований
    tradition_strength: float = 0.3     # Сила традиций

    # Time Parameters
    hours_per_day: int = 24
    days_per_month: int = 30
    months_per_year: int = 12
```

**Constraints:**
- `world_width` > 0, `world_height` > 0
- `initial_population` >= 2 (для размножения)
- Все rates в диапазоне [0.0, 1.0]
- `max_age` > `fertile_age_max`

**Presets:**

| Preset | Description | Key Differences |
|--------|-------------|-----------------|
| REALISTIC | Медленное развитие | tech_progress=0.5, mortality=0.08 |
| ACCELERATED | Быстрое тестирование | tech_progress=2.0, mortality=0.03 |
| SANDBOX | Максимум свободы | Все rates высокие |

---

### 2.2 Event

**Файл:** `src/core/events.py`

```python
@dataclass
class Event:
    """Событие в симуляции"""

    id: UUID                        # Уникальный ID
    type: EventType                 # Тип события
    timestamp: int                  # Время (total_hours)
    importance: EventImportance     # Важность
    data: Dict[str, Any]           # Payload
    source_id: Optional[UUID]       # Источник (NPC/Location)
    target_ids: List[UUID]          # Затронутые сущности
```

**EventType Enum (60+ values):**

```python
class EventType(Enum):
    # Lifecycle
    NPC_BORN = "npc_born"
    NPC_DIED = "npc_died"
    NPC_AGED = "npc_aged"
    NPC_MARRIED = "npc_married"
    NPC_DIVORCED = "npc_divorced"

    # Economic
    RESOURCE_GATHERED = "resource_gathered"
    RESOURCE_CONSUMED = "resource_consumed"
    PRODUCTION_COMPLETED = "production_completed"
    TRADE_COMPLETED = "trade_completed"
    TECHNOLOGY_DISCOVERED = "technology_discovered"
    PROPERTY_TRANSFERRED = "property_transferred"

    # Social
    RELATIONSHIP_CHANGED = "relationship_changed"
    CLASS_EMERGED = "class_emerged"
    CLASS_CONFLICT = "class_conflict"
    FAMILY_CREATED = "family_created"

    # Cultural
    BELIEF_FORMED = "belief_formed"
    BELIEF_SPREAD = "belief_spread"
    TRADITION_ESTABLISHED = "tradition_established"
    NORM_VIOLATED = "norm_violated"

    # World
    SEASON_CHANGED = "season_changed"
    CATASTROPHE_STARTED = "catastrophe_started"
    CATASTROPHE_ENDED = "catastrophe_ended"
    LOCATION_DISCOVERED = "location_discovered"

    # Actions
    ACTION_STARTED = "action_started"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"
```

**EventImportance Enum:**

```python
class EventImportance(Enum):
    TRIVIAL = 1      # Рутина (NPC поел)
    MINOR = 2        # Мелочь (новый друг)
    NOTABLE = 3      # Заметно (новый навык)
    IMPORTANT = 4    # Важно (брак, рождение)
    MAJOR = 5        # Крупно (новый класс, война)
    HISTORIC = 6     # Историческое (новая эпоха)
```

---

## 3. World Models

### 3.1 Location

**Файл:** `src/world/location.py`

```python
@dataclass
class Location:
    """Локация на карте"""

    id: UUID
    type: LocationType
    name: str
    coordinates: Tuple[int, int]    # (x, y)
    npcs: Set[UUID]                 # ID NPC в локации
    resources: Inventory            # Ресурсы локации
    buildings: List[Building]       # Строения
    capacity: int                   # Макс. население
    danger_level: float             # 0.0 - 1.0
```

**LocationType Enum:**

```python
class LocationType(Enum):
    FIELD = "field"           # Поле (земледелие)
    FOREST = "forest"         # Лес (дерево, охота)
    LAKE = "lake"             # Озеро (рыба, вода)
    RIVER = "river"           # Река (вода, рыба)
    MOUNTAIN = "mountain"     # Горы (камень, руда)
    SETTLEMENT = "settlement" # Поселение
    CAVE = "cave"             # Пещера (укрытие)
    PLAIN = "plain"           # Равнина
```

**Production by LocationType:**

| LocationType | Available Resources | Production Methods |
|--------------|---------------------|-------------------|
| FIELD | FOOD | FARMING |
| FOREST | WOOD, FOOD(berries), GAME | GATHERING, HUNTING, LOGGING |
| LAKE | WATER, FISH | FISHING |
| MOUNTAIN | STONE, ORE | MINING |
| SETTLEMENT | - | CRAFTING, TRADING |

---

### 3.2 MapCell

**Файл:** `src/world/map.py`

```python
@dataclass
class MapCell:
    """Ячейка карты"""

    coordinates: Tuple[int, int]
    terrain: TerrainType
    vegetation: float           # 0.0 - 1.0
    moisture: float             # 0.0 - 1.0
    elevation: float            # 0.0 - 1.0
    location: Optional[Location]
    discovered: bool = False
```

**TerrainType Enum:**

```python
class TerrainType(Enum):
    GRASSLAND = "grassland"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    WATER = "water"
    DESERT = "desert"
    SWAMP = "swamp"
    TUNDRA = "tundra"
```

---

### 3.3 TimeState

**Файл:** `src/world/time_system.py`

```python
@dataclass
class TimeState:
    """Состояние времени"""

    hour: int           # 0-23
    day: int            # 1-30
    month: int          # 1-12
    year: int           # 1+
    total_hours: int    # Всего часов от начала

    @property
    def time_of_day(self) -> TimeOfDay:
        if 22 <= self.hour or self.hour < 6:
            return TimeOfDay.NIGHT
        elif 6 <= self.hour < 8:
            return TimeOfDay.DAWN
        elif 8 <= self.hour < 18:
            return TimeOfDay.DAY
        else:
            return TimeOfDay.DUSK

    @property
    def season(self) -> Season:
        day_of_year = (self.month - 1) * 30 + self.day
        if day_of_year <= 90:
            return Season.SPRING
        elif day_of_year <= 180:
            return Season.SUMMER
        elif day_of_year <= 270:
            return Season.AUTUMN
        else:
            return Season.WINTER
```

---

### 3.4 ClimateState

**Файл:** `src/world/climate.py`

```python
@dataclass
class ClimateState:
    """Климатическое состояние"""

    season: Season
    temperature: float          # -20 to 40 (Celsius)
    precipitation: float        # 0.0 - 1.0
    active_catastrophe: Optional[Catastrophe]
    catastrophe_duration: int   # Дней до конца

@dataclass
class Catastrophe:
    """Катаклизм"""

    type: CatastropheType
    severity: float             # 0.0 - 1.0
    affected_area: List[Tuple[int, int]]  # Координаты
    started: int                # Год начала
    duration: int               # Длительность в днях

    def affects_location(self, loc: Location) -> bool:
        return loc.coordinates in self.affected_area
```

**CatastropheType Enum:**

```python
class CatastropheType(Enum):
    DROUGHT = "drought"         # -50% food production
    FLOOD = "flood"             # Destroys buildings
    PLAGUE = "plague"           # +100% mortality
    FAMINE = "famine"           # No food regeneration
    FIRE = "fire"               # Destroys forests
    HARSH_WINTER = "harsh_winter"  # +50% food consumption
    LOCUSTS = "locusts"         # -90% crops
```

---

## 4. Economy Models

### 4.1 Resource

**Файл:** `src/economy/resources.py`

```python
class ResourceType(Enum):
    """Типы ресурсов"""

    # Basic
    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    STONE = "stone"

    # Processed
    LEATHER = "leather"
    CLOTH = "cloth"
    POTTERY = "pottery"
    TOOLS = "tools"

    # Metal
    ORE = "ore"
    COPPER = "copper"
    BRONZE = "bronze"
    IRON = "iron"

    # Rare
    GOLD = "gold"
    GEMS = "gems"

@dataclass
class ResourceInfo:
    """Метаданные ресурса"""

    type: ResourceType
    base_value: float           # Базовая ценность
    decay_rate: float           # Скорость порчи (0 = не портится)
    weight: float               # Вес единицы
    stackable: bool = True
```

**Resource Values:**

| Resource | Base Value | Decay Rate | Weight |
|----------|------------|------------|--------|
| FOOD | 1.0 | 0.1/day | 0.5 |
| WATER | 0.5 | 0.0 | 1.0 |
| WOOD | 2.0 | 0.01/day | 2.0 |
| STONE | 3.0 | 0.0 | 5.0 |
| ORE | 5.0 | 0.0 | 3.0 |
| IRON | 15.0 | 0.0 | 2.0 |
| GOLD | 50.0 | 0.0 | 0.5 |

---

### 4.2 Inventory

**Файл:** `src/economy/resources.py`

```python
@dataclass
class Inventory:
    """Инвентарь NPC или локации"""

    owner_id: UUID
    resources: Dict[ResourceType, float]
    capacity: float             # Макс. вес
    current_weight: float       # Текущий вес

    def add(self, resource: ResourceType, amount: float) -> float:
        """Добавить ресурс, вернуть реально добавленное"""
        ...

    def remove(self, resource: ResourceType, amount: float) -> bool:
        """Убрать ресурс, вернуть успех"""
        ...

    def has(self, resource: ResourceType, amount: float) -> bool:
        """Проверить наличие"""
        ...

    def get(self, resource: ResourceType) -> float:
        """Получить количество"""
        ...

    def transfer_to(self, target: 'Inventory', resource: ResourceType, amount: float) -> bool:
        """Передать другому инвентарю"""
        ...
```

---

### 4.3 ProductionMethod

**Файл:** `src/economy/production.py`

```python
@dataclass
class ProductionMethod:
    """Метод производства"""

    id: str
    name: str
    inputs: Dict[ResourceType, float]       # Входные ресурсы
    outputs: Dict[ResourceType, float]      # Выходные ресурсы
    required_tech: Optional[str]            # Требуемая технология
    required_tools: List[ResourceType]      # Требуемые инструменты
    required_location: Optional[LocationType]  # Где можно производить
    skill_type: str                         # Какой навык используется
    skill_min: float                        # Минимальный уровень навыка
    base_duration: int                      # Время в часах
    base_success_rate: float                # Базовый шанс успеха

    def can_perform(self, npc: 'Character', location: Location) -> bool:
        """Проверить возможность выполнения"""
        ...

    def calculate_output(self, npc: 'Character') -> Dict[ResourceType, float]:
        """Рассчитать выход с учётом навыков"""
        ...
```

**Production Methods:**

| Method | Inputs | Outputs | Tech Required | Duration |
|--------|--------|---------|---------------|----------|
| GATHERING | - | FOOD: 2 | - | 2h |
| HUNTING | - | FOOD: 5, LEATHER: 1 | HUNTING | 4h |
| FISHING | - | FOOD: 3 | FISHING | 3h |
| LOGGING | - | WOOD: 3 | STONE_WORKING | 4h |
| FARMING | SEEDS: 1 | FOOD: 10 | AGRICULTURE | 8h |
| MINING | - | STONE: 2, ORE: 1 | STONE_WORKING | 6h |
| SMELTING | ORE: 3, WOOD: 2 | METAL: 1 | METALLURGY | 4h |
| CRAFTING | varies | varies | varies | varies |

---

### 4.4 Technology

**Файл:** `src/economy/technology.py`

```python
@dataclass
class Technology:
    """Технология"""

    id: str
    name: str
    description: str
    era: Era
    prerequisites: List[str]        # ID prerequisite технологий
    unlocks_methods: List[str]      # ID разблокируемых методов
    discovery_difficulty: float     # 0.0 - 1.0
    discovery_progress: float       # Текущий прогресс (0.0 - 1.0)

    def can_discover(self, known_techs: Set[str]) -> bool:
        """Проверить доступность для открытия"""
        return all(prereq in known_techs for prereq in self.prerequisites)
```

**Technology Tree (partial):**

```
PRIMITIVE ERA:
├── STONE_WORKING (0.3)
├── FIRE_MAKING (0.3)
├── BASIC_HUNTING (0.2)
├── BASIC_GATHERING (0.1)
└── BASIC_FISHING (0.2)

STONE_AGE:
├── BOW_AND_ARROW (0.5) ← [HUNTING, STONE_WORKING]
├── POTTERY (0.4) ← [FIRE_MAKING]
├── WEAVING (0.4) ← [GATHERING]
├── BASIC_AGRICULTURE (0.6) ← [GATHERING, STONE_WORKING]
├── ANIMAL_DOMESTICATION (0.5) ← [HUNTING]
└── SHELTER_BUILDING (0.4) ← [STONE_WORKING]

BRONZE_AGE:
├── METALLURGY (0.7) ← [FIRE_MAKING, POTTERY]
├── BRONZE_WORKING (0.7) ← [METALLURGY]
├── PLOW (0.6) ← [AGRICULTURE, ANIMAL_DOMESTICATION]
├── WHEEL (0.7) ← [POTTERY, ANIMAL_DOMESTICATION]
└── WRITING (0.8) ← [POTTERY]

IRON_AGE:
└── IRON_WORKING (0.9) ← [BRONZE_WORKING]
```

---

### 4.5 PropertyRight

**Файл:** `src/economy/property.py`

```python
@dataclass
class PropertyRight:
    """Право собственности"""

    id: UUID
    owner_id: UUID                  # ID владельца (NPC или Family)
    owner_type: str                 # "npc" или "family"
    property_type: PropertyType     # COMMUNAL, PERSONAL, PRIVATE, FAMILY
    category: PropertyCategory      # LAND, TOOLS, etc.
    target_id: Optional[UUID]       # ID объекта (Location, Item)
    target_description: str         # Описание объекта
    can_use: bool                   # Право использования
    can_transfer: bool              # Право передачи
    can_inherit: bool               # Право наследования
    acquired_date: int              # Когда приобретено (year)

    def transfer_to(self, new_owner_id: UUID, new_owner_type: str) -> None:
        """Передать собственность"""
        ...

    def inherit(self, heir_id: UUID) -> None:
        """Наследовать"""
        ...
```

**PropertyType Enum:**

```python
class PropertyType(Enum):
    COMMUNAL = "communal"       # Общинная (всем)
    PERSONAL = "personal"       # Личная (одежда, еда)
    PRIVATE = "private"         # Частная (средства производства)
    FAMILY = "family"           # Семейная (дом, земля)
```

**PropertyCategory Enum:**

```python
class PropertyCategory(Enum):
    LAND = "land"               # Земля
    TOOLS = "tools"             # Инструменты
    LIVESTOCK = "livestock"     # Скот
    BUILDING = "building"       # Строения
    RESOURCES = "resources"     # Ресурсы
    KNOWLEDGE = "knowledge"     # Знания/технологии
```

---

## 5. Society Models

### 5.1 Family

**Файл:** `src/society/family.py`

```python
@dataclass
class Family:
    """Семья"""

    id: UUID
    name: str                       # Фамилия
    members: Set[UUID]              # ID членов
    head_id: UUID                   # Глава семьи
    property_rights: List[PropertyRight]
    residence: Optional[UUID]       # ID поселения
    founded_year: int               # Год основания
    lineage: List[UUID]             # Предки (для истории)

    def add_member(self, npc_id: UUID) -> None:
        """Добавить члена"""
        ...

    def remove_member(self, npc_id: UUID) -> None:
        """Убрать члена"""
        ...

    def elect_new_head(self, members: Dict[UUID, 'Character']) -> None:
        """Выбрать нового главу"""
        ...

    def calculate_wealth(self) -> float:
        """Посчитать богатство семьи"""
        ...
```

---

### 5.2 Marriage

**Файл:** `src/society/family.py`

```python
@dataclass
class Marriage:
    """Брак"""

    id: UUID
    spouse1_id: UUID
    spouse2_id: UUID
    year_married: int
    family_id: UUID                 # Созданная семья
    children: List[UUID]            # Дети от брака
    is_active: bool = True          # Не разведены

    def add_child(self, child_id: UUID) -> None:
        """Добавить ребёнка"""
        ...

    def divorce(self) -> None:
        """Развод"""
        ...
```

---

### 5.3 SocialClass

**Файл:** `src/society/classes.py`

```python
@dataclass
class SocialClass:
    """Социальный класс (EMERGENT)"""

    type: ClassType
    members: Set[UUID]              # NPC в классе
    economic_power: float           # 0.0 - 1.0
    political_influence: float      # 0.0 - 1.0
    class_consciousness: float      # 0.0 - 1.0

    @staticmethod
    def determine_class(npc: 'Character', property_system: 'PropertySystem') -> ClassType:
        """
        EMERGENT: Класс определяется владением!
        """
        owned = property_system.get_owned_by(npc.id)
        land = [p for p in owned if p.category == PropertyCategory.LAND]
        tools = [p for p in owned if p.category == PropertyCategory.TOOLS]

        if not owned or all(p.property_type == PropertyType.COMMUNAL for p in owned):
            return ClassType.COMMUNAL_MEMBER
        elif land and any(p.property_type == PropertyType.PRIVATE for p in land):
            return ClassType.LANDOWNER
        elif tools and not land:
            return ClassType.CRAFTSMAN
        elif not land and not tools:
            return ClassType.LABORER
        else:
            return ClassType.LANDLESS
```

**ClassType Enum:**

```python
class ClassType(Enum):
    COMMUNAL_MEMBER = "communal"    # Член общины
    LANDOWNER = "landowner"         # Землевладелец
    LANDLESS = "landless"           # Безземельный
    CRAFTSMAN = "craftsman"         # Ремесленник
    LABORER = "laborer"             # Работник
```

---

## 6. Culture Models

### 6.1 Belief

**Файл:** `src/culture/beliefs.py`

```python
@dataclass
class Belief:
    """Верование (EMERGENT)"""

    id: UUID
    type: BeliefType
    origin: BeliefOrigin            # Откуда возникло
    strength: float                 # 0.0 - 1.0
    adherents: Set[UUID]            # NPC, разделяющие верование
    benefiting_class: Optional[ClassType]  # Кому выгодно
    contradicts: List[BeliefType]   # С чем конфликтует
    emerged_year: int               # Когда возникло
    economic_conditions: Dict[str, Any]  # При каких условиях

    def spreads_to(self, npc: 'Character') -> float:
        """Вероятность принятия NPC"""
        ...

    def conflicts_with(self, other: 'Belief') -> bool:
        """Конфликтует ли с другим верованием"""
        return other.type in self.contradicts
```

**BeliefType Enum:**

```python
class BeliefType(Enum):
    # Природные
    ANIMISM = "animism"                 # Духи в природе
    TOTEMISM = "totemism"               # Священные животные
    NATURALISM = "naturalism"           # Природа священна

    # Социальные
    ANCESTOR_WORSHIP = "ancestors"      # Культ предков
    HERO_WORSHIP = "heroes"             # Культ героев
    DIVINE_RULERS = "divine_rulers"     # Божественные правители

    # Экономические (EMERGENT!)
    PROPERTY_SACRED = "property_sacred" # Собственность священна
    COLLECTIVE_GOOD = "collective_good" # Общее благо
    WORK_VIRTUE = "work_virtue"         # Труд — добродетель
    WEALTH_BLESSING = "wealth_blessing" # Богатство — благословение

    # Социальный порядок
    HIERARCHY_NATURAL = "hierarchy"     # Иерархия естественна
    EQUALITY_IDEAL = "equality"         # Равенство — идеал
    TRADITION_SACRED = "tradition"      # Традиция священна
```

**BeliefOrigin Enum:**

```python
class BeliefOrigin(Enum):
    NATURAL = "natural"         # Из наблюдения природы
    ECONOMIC = "economic"       # Из экономических условий
    SOCIAL = "social"           # Из социальных отношений
    CRISIS = "crisis"           # Из кризиса/катаклизма
    TRADITION = "tradition"     # Из традиции
    LEADER = "leader"           # От лидера/авторитета
```

---

### 6.2 Tradition

**Файл:** `src/culture/traditions.py`

```python
@dataclass
class Tradition:
    """Традиция"""

    id: UUID
    name: str
    description: str
    related_beliefs: List[BeliefType]
    season: Optional[Season]        # Когда проводится
    frequency: str                  # "yearly", "monthly", "weekly"
    required_resources: Dict[ResourceType, float]
    participants_min: int           # Минимум участников
    social_effects: Dict[str, float]  # Влияние на общество
    emerged_year: int

    def can_perform(self, society: 'Society') -> bool:
        """Можно ли провести"""
        ...

    def perform(self, participants: List['Character']) -> Dict[str, Any]:
        """Провести традицию"""
        ...
```

---

### 6.3 SocialNorm

**Файл:** `src/culture/norms.py`

```python
@dataclass
class SocialNorm:
    """Социальная норма"""

    id: UUID
    name: str
    description: str
    related_beliefs: List[BeliefType]
    violation_penalty: float        # 0.0 - 1.0 (репутация)
    enforcement_strength: float     # 0.0 - 1.0
    applies_to: List[ClassType]     # К каким классам применяется
    exempts: List[ClassType]        # Кто исключён

    def check_violation(self, action: 'Action', npc: 'Character') -> bool:
        """Нарушает ли действие норму"""
        ...

    def apply_penalty(self, npc: 'Character') -> None:
        """Применить штраф"""
        ...
```

---

## 7. NPC Models

### 7.1 Character

**Файл:** `src/npc/character.py`

```python
@dataclass
class Character:
    """NPC персонаж"""

    # Identity
    id: UUID
    name: str
    gender: Gender
    birth_year: int

    # Physical
    age: int
    health: float                   # 0.0 - 1.0
    stats: Stats
    genetic_traits: GeneticTraits

    # Mental
    personality: Personality
    skills: Skills
    memory: MemorySystem
    bdi: BDISystem

    # Social
    relationships: RelationshipSystem
    family_id: Optional[UUID]
    class_type: ClassType           # Определяется EMERGENT

    # Economic
    inventory: Inventory
    occupation: Optional[str]
    known_technologies: Set[str]

    # Location
    location_id: UUID
    home_location_id: Optional[UUID]

    # State
    current_action: Optional[Action]
    needs: NeedSystem
    beliefs: Set[BeliefType]

    def update(self, world: 'World', hours: int) -> List[Event]:
        """Обновить состояние"""
        ...

    def perform_action(self, action: Action) -> ActionResult:
        """Выполнить действие"""
        ...

    def die(self, cause: str) -> DeathEvent:
        """Смерть"""
        ...
```

---

### 7.2 Stats

**Файл:** `src/npc/character.py`

```python
@dataclass
class Stats:
    """Базовые характеристики NPC"""

    strength: int       # 1-20: Физическая сила
    dexterity: int      # 1-20: Ловкость, координация
    constitution: int   # 1-20: Выносливость, здоровье
    intelligence: int   # 1-20: Интеллект, обучаемость
    wisdom: int         # 1-20: Мудрость, восприятие
    charisma: int       # 1-20: Харизма, лидерство
    luck: int           # 1-20: Удача

    def get_modifier(self, stat: str) -> int:
        """D&D-style modifier: (stat - 10) // 2"""
        value = getattr(self, stat)
        return (value - 10) // 2

    @classmethod
    def random(cls, min_val: int = 3, max_val: int = 18) -> 'Stats':
        """Сгенерировать случайные stats"""
        ...
```

---

### 7.3 Skills

**Файл:** `src/npc/character.py`

```python
@dataclass
class Skills:
    """Навыки NPC"""

    combat: float = 0.0         # Бой
    hunting: float = 0.0        # Охота
    gathering: float = 0.0      # Собирательство
    farming: float = 0.0        # Земледелие
    fishing: float = 0.0        # Рыболовство
    crafting: float = 0.0       # Ремесло
    building: float = 0.0       # Строительство
    mining: float = 0.0         # Добыча
    trading: float = 0.0        # Торговля
    medicine: float = 0.0       # Медицина
    leadership: float = 0.0     # Лидерство
    speaking: float = 0.0       # Ораторство

    # All skills: 0.0 (новичок) - 100.0 (мастер)

    def improve(self, skill: str, amount: float) -> None:
        """Улучшить навык"""
        current = getattr(self, skill)
        new_value = min(100.0, current + amount)
        setattr(self, skill, new_value)

    def get_level(self, skill: str) -> str:
        """Получить уровень мастерства"""
        value = getattr(self, skill)
        if value < 20:
            return "novice"
        elif value < 40:
            return "apprentice"
        elif value < 60:
            return "journeyman"
        elif value < 80:
            return "expert"
        else:
            return "master"
```

---

### 7.4 Personality

**Файл:** `src/npc/personality.py`

```python
@dataclass
class Personality:
    """Личность NPC"""

    traits: Dict[Trait, float]      # trait -> strength (-1.0 to 1.0)

    def get_trait(self, trait: Trait) -> float:
        """Получить силу черты"""
        return self.traits.get(trait, 0.0)

    def has_trait(self, trait: Trait, threshold: float = 0.3) -> bool:
        """Имеет ли черту (выше порога)"""
        return self.get_trait(trait) >= threshold

    def affects_action(self, action: Action) -> float:
        """Модификатор действия от личности"""
        modifier = 0.0
        for trait, relevance in ACTION_TRAIT_RELEVANCE.get(action, {}).items():
            modifier += self.get_trait(trait) * relevance
        return modifier

    @classmethod
    def inherit(cls, parent1: 'Personality', parent2: 'Personality') -> 'Personality':
        """Наследовать личность от родителей"""
        ...
```

**Trait Enum:**

```python
class Trait(Enum):
    # Социальность
    EXTROVERSION = "extroversion"       # + социализация, - одиночество
    # Доброжелательность
    AGREEABLENESS = "agreeableness"     # + кооперация, - конфликты
    # Добросовестность
    CONSCIENTIOUSNESS = "conscientiousness"  # + труд, - безделье
    # Эмоциональность
    NEUROTICISM = "neuroticism"         # + тревога, - спокойствие
    # Открытость
    OPENNESS = "openness"               # + новое, - традиция

    # Специфичные
    GREED = "greed"                     # Жадность
    BRAVERY = "bravery"                 # Храбрость
    CURIOSITY = "curiosity"             # Любопытство
    AMBITION = "ambition"               # Амбициозность
```

---

### 7.5 Need

**Файл:** `src/npc/needs.py`

```python
@dataclass
class Need:
    """Потребность"""

    type: NeedType
    current: float              # 0.0 (критично) - 1.0 (удовлетворено)
    decay_rate: float           # Скорость убывания в час
    critical_threshold: float   # Когда становится критичной
    satisfaction_actions: List[Action]  # Какие действия удовлетворяют

    def update(self, hours: int) -> None:
        """Обновить (убавить)"""
        self.current = max(0.0, self.current - self.decay_rate * hours)

    def satisfy(self, amount: float) -> None:
        """Удовлетворить"""
        self.current = min(1.0, self.current + amount)

    def is_critical(self) -> bool:
        """Критическая?"""
        return self.current < self.critical_threshold

    def priority(self) -> float:
        """Приоритет (чем ниже current, тем выше приоритет)"""
        return 1.0 - self.current
```

**NeedType Config:**

| NeedType | Decay Rate | Critical | Satisfaction Actions |
|----------|------------|----------|---------------------|
| HUNGER | 0.04/h | 0.2 | EAT |
| THIRST | 0.06/h | 0.15 | DRINK |
| SLEEP | 0.02/h | 0.1 | SLEEP |
| SOCIAL | 0.01/h | 0.3 | SOCIALIZE |
| ENTERTAINMENT | 0.005/h | 0.2 | REST, SOCIALIZE |
| SAFETY | 0.0 | 0.3 | FLEE, FIGHT |

---

### 7.6 Memory

**Файл:** `src/npc/memory.py`

```python
@dataclass
class Memory:
    """Воспоминание"""

    id: UUID
    timestamp: int                  # total_hours когда произошло
    description: str                # Что произошло
    type: MemoryType                # Тип воспоминания
    importance: float               # 0.0 - 1.0
    emotional_valence: float        # -1.0 (плохо) - 1.0 (хорошо)
    participants: List[UUID]        # Кто участвовал
    location: Tuple[int, int]       # Где произошло
    related_memories: List[UUID]    # Связанные воспоминания
    access_count: int = 0           # Сколько раз вспоминалось
    last_accessed: Optional[int] = None  # Когда последний раз

    def decay(self, current_time: int) -> float:
        """Рассчитать угасание"""
        age = current_time - self.timestamp
        base_decay = 0.999 ** age  # Экспоненциальное угасание
        importance_factor = self.importance
        access_factor = 1 + 0.1 * self.access_count
        return base_decay * importance_factor * access_factor
```

**MemoryType Enum:**

```python
class MemoryType(Enum):
    OBSERVATION = "observation"     # Что видел
    INTERACTION = "interaction"     # С кем общался
    ACTION = "action"               # Что делал
    EMOTION = "emotion"             # Что чувствовал
    KNOWLEDGE = "knowledge"         # Что узнал
    REFLECTION = "reflection"       # О чём думал
```

---

### 7.7 Relationship

**Файл:** `src/npc/relationships.py`

```python
@dataclass
class Relationship:
    """Отношение к другому NPC"""

    target_id: UUID
    type: RelationType
    strength: float             # -1.0 (враг) - 1.0 (близкий)
    trust: float                # 0.0 - 1.0
    familiarity: float          # 0.0 - 1.0 (как хорошо знает)
    history: List[Interaction]  # История взаимодействий
    started: int                # Когда началось

    def update(self, interaction: 'Interaction') -> None:
        """Обновить на основе взаимодействия"""
        ...

    def get_disposition(self) -> str:
        """Получить отношение"""
        if self.strength > 0.7:
            return "very_positive"
        elif self.strength > 0.3:
            return "positive"
        elif self.strength > -0.3:
            return "neutral"
        elif self.strength > -0.7:
            return "negative"
        else:
            return "very_negative"
```

---

### 7.8 BDI Components

**Файл:** `src/npc/ai/bdi.py`

```python
@dataclass
class Belief:
    """Убеждение о мире"""

    id: UUID
    subject: str                # О чём (NPC, Location, Resource)
    predicate: str              # Что (has_food, is_dangerous, is_friend)
    value: Any                  # Значение
    confidence: float           # 0.0 - 1.0
    source: str                 # Откуда (observation, inference, told)
    timestamp: int              # Когда сформировано

@dataclass
class Desire:
    """Желание/Цель"""

    id: UUID
    description: str            # Описание цели
    type: DesireType            # Тип (need, goal, dream)
    priority: float             # 0.0 - 1.0
    deadline: Optional[int]     # Срок (если есть)
    conditions: Dict[str, Any]  # Условия выполнения
    satisfied: bool = False

@dataclass
class Intention:
    """Намерение (выбранный план)"""

    id: UUID
    goal: Desire                # Какую цель достигает
    plan: List[Action]          # Последовательность действий
    current_step: int           # Текущий шаг
    status: IntentionStatus     # active, suspended, achieved, failed
    started: int                # Когда начато
    context: Dict[str, Any]     # Контекст выполнения
```

**DesireType Enum:**

```python
class DesireType(Enum):
    NEED = "need"               # Базовая потребность
    GOAL = "goal"               # Краткосрочная цель
    DREAM = "dream"             # Долгосрочная мечта
    DUTY = "duty"               # Обязанность
    IMPULSE = "impulse"         # Импульс
```

---

## 8. Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            WORLD                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   Config    │    │   EventBus  │    │ TimeSystem  │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                         │
│                            │                                            │
│  ┌─────────────────────────┴─────────────────────────┐                 │
│  │                      WORLD                         │                 │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │                 │
│  │  │  Map     │──│ Location │──│ Climate  │        │                 │
│  │  └──────────┘  └────┬─────┘  └──────────┘        │                 │
│  │                     │                             │                 │
│  │              ┌──────┴──────┐                      │                 │
│  │              │             │                      │                 │
│  │         ┌────┴────┐  ┌────┴────┐                 │                 │
│  │         │Resources│  │   NPC   │                 │                 │
│  │         └─────────┘  └────┬────┘                 │                 │
│  └───────────────────────────┼───────────────────────┘                 │
│                              │                                         │
│  ┌───────────────────────────┴───────────────────────┐                │
│  │                    CHARACTER                       │                │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐           │                │
│  │  │  Stats  │  │Personali│  │ Skills  │           │                │
│  │  └─────────┘  └─────────┘  └─────────┘           │                │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐           │                │
│  │  │ Needs   │  │ Memory  │  │Relation │           │                │
│  │  └─────────┘  └─────────┘  └─────────┘           │                │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐           │                │
│  │  │Genetics │  │Inventory│  │   BDI   │           │                │
│  │  └─────────┘  └─────────┘  └─────────┘           │                │
│  └───────────────────────────────────────────────────┘                │
│                                                                        │
│  ┌────────────────────┐  ┌────────────────────┐                       │
│  │      ECONOMY       │  │      SOCIETY       │                       │
│  │  ┌──────────────┐  │  │  ┌──────────────┐  │                       │
│  │  │  Production  │  │  │  │    Family    │  │                       │
│  │  ├──────────────┤  │  │  ├──────────────┤  │                       │
│  │  │  Technology  │  │  │  │  Demography  │  │                       │
│  │  ├──────────────┤  │  │  ├──────────────┤  │                       │
│  │  │   Property   │──┼──┼──│   Classes    │  │                       │
│  │  └──────────────┘  │  │  └──────────────┘  │                       │
│  └────────────────────┘  └────────────────────┘                       │
│              │                     │                                   │
│              └──────────┬──────────┘                                   │
│                         │                                              │
│  ┌──────────────────────┴──────────────────────┐                      │
│  │                   CULTURE                    │                      │
│  │  ┌──────────────┐  ┌──────────────┐         │                      │
│  │  │   Beliefs    │  │  Traditions  │         │                      │
│  │  ├──────────────┤  ├──────────────┤         │                      │
│  │  │    Norms     │  │              │         │                      │
│  │  └──────────────┘  └──────────────┘         │                      │
│  └─────────────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Документ создан по методологии [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)*
