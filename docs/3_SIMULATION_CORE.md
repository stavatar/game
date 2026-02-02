---
title: Ядро Симуляции - Основной Цикл и Система Событий
description: Описание основного цикла симуляции, архитектуры событий, паттерна EventBus, систем отслеживания эмерджентности и валидации консистентности
keywords:
  - симуляция
  - основной цикл
  - события
  - EventBus
  - паттерн Pub-Sub
  - эмерджентность
  - консистентность
  - марксистская архитектура
lang: ru
---

# Ядро Симуляции - Основной Цикл и Система Событий

## Обзор

Ядро симуляции (core) — это центральная система, которая объединяет все подсистемы в единый функциональный организм. Основной компонент — главный цикл обновления, который управляет временем и координирует все процессы в мире.

**Ключевые компоненты:**
- **Симуляция** — главный класс, управляющий циклом обновления
- **EventBus** — система событий для коммуникации между системами
- **EmergenceTracker** — отслеживание эмерджентных явлений
- **ConsistencyValidator** — проверка консистентности состояния
- **ContradictionDetector** — обнаружение диалектических противоречий

---

## 1. Основной Цикл Симуляции

### 1.1. Архитектура по Марксу

Симуляция реализует марксистскую архитектуру социального развития:

```
ОКРУЖАЮЩАЯ СРЕДА (Время, климат)
         ↓
  БАЗИС (Экономика)
   ├─ Производство ресурсов
   ├─ Собственность
   └─ Классовая система
         ↓
   NPC ДЕЙСТВИЯ (Агенты)
   ├─ BDI решения
   ├─ Трудовая деятельность
   └─ Взаимодействия
         ↓
 НАДСТРОЙКА (Культура)
   ├─ Верования
   ├─ Традиции
   └─ Социальные нормы
         ↓
    ДЕМОГРАФИЯ
   ├─ Потребности NPC
   ├─ Рождаемость
   └─ Смертность
```

**Принцип**: По Марксу, базис (экономика) обновляется раньше надстройки (культуры), поскольку материальные условия определяют сознание.

### 1.2. Порядок Обновления в Каждой Итерации

Главный цикл обновления выполняет следующие шаги за каждый час игрового времени:

#### **Шаг 1: ВРЕМЯ И КЛИМАТ** (окружающая среда)
- Увеличение часа, дня, месяца, года
- Обновление климата (сезоны, погода, катаклизмы)
- Применение климатических модификаторов к производству
- **Частота**: каждый час (время), каждый день (климат)

#### **Шаг 2: БАЗИС** (экономика)
- Обновление производства (учёт сезонности)
- Обновление собственности и классовых отношений
- Обработка классовых конфликтов
- **Частота**: каждый час (производство), каждый день (конфликты)

#### **Шаг 3: NPC ДЕЙСТВИЯ** (поведение агентов)
- Выполнение BDI цикла для каждого NPC
- Трудовая деятельность
- Торговля и взаимодействия
- **Частота**: каждый час

#### **Шаг 4: НАДСТРОЙКА** (культура)
- Проверка появления новых верований
- Применение эффектов традиций
- Обновление норм и идеологии
- **Частота**: каждый день

#### **Шаг 5: ДЕМОГРАФИЯ** (потребности и воспроизводство)
- Обновление потребностей NPC
- Проверка рождаемости
- Обработка смертности (голод, болезни, конфликты)
- **Частота**: каждый день

### 1.3. Пример Кода: Основной Цикл

```python
def update(self, hours: int = 1) -> List[str]:
    """
    Обновляет симуляцию на указанное количество часов.

    Порядок обновления по марксистской архитектуре:
    1. Время и климат (окружающая среда)
    2. БАЗИС (экономика): производство, собственность, классы
    3. NPC действия (агенты реагируют на среду и базис)
    4. НАДСТРОЙКА (культура): верования, традиции, нормы
    5. Демография (рождения/смерти, потребности)
    """
    all_events = []

    for _ in range(hours):
        # === 1. ВРЕМЯ И КЛИМАТ ===
        self.hour += 1
        is_new_day = False

        if self.hour >= 24:
            self.hour = 0
            self.day += 1
            is_new_day = True

            if self.day > self.config.days_per_month:
                self.day = 1
                self.month += 1

                if self.month > self.config.months_per_year:
                    self.month = 1
                    self.year += 1

        # Климат раз в день
        if is_new_day:
            climate_events = self._update_climate()
            all_events.extend(climate_events)

        # === 2. БАЗИС (экономика) ===
        self.production.update(1.0)
        if is_new_day:
            conflict_events = self._process_class_conflicts()
            all_events.extend(conflict_events)

        # === 3. NPC ДЕЙСТВИЯ ===
        npc_events = self._process_npc_actions()
        all_events.extend(npc_events)

        # === 4. НАДСТРОЙКА (культура) ===
        if is_new_day:
            superstructure_events = self._update_superstructure()
            all_events.extend(superstructure_events)

        # === 5. ДЕМОГРАФИЯ ===
        if is_new_day:
            demography_events = self._update_demography()
            all_events.extend(demography_events)

    return all_events
```

---

## 2. Система Событий

### 2.1. Обзор EventBus

**EventBus** — это система событий, реализующая паттерн **Observer/Pub-Sub**. Она служит центром коммуникации между подсистемами симуляции.

**Зачем нужна EventBus?**
- **Слабая связанность**: системы не зависят друг от друга напрямую
- **Реактивность**: события распространяются синхронно по подписчикам
- **История**: все события логируются для анализа
- **Фильтрация**: подписчики могут реагировать только на интересующие типы

### 2.2. Типы Событий

EventType содержит 24 типа событий, сгруппированные по категориям:

#### **Жизненный цикл NPC** (3 типа)
- `NPC_BORN` — рождение NPC
- `NPC_DIED` — смерть NPC
- `NPC_AGED` — старение (день рождения)

#### **Семья** (3 типа)
- `MARRIAGE` — свадьба
- `DIVORCE` — развод
- `CHILD_BORN` — рождение ребёнка

#### **Экономика** (5 типов)
- `RESOURCE_GATHERED` — собран ресурс
- `RESOURCE_DEPLETED` — ресурс истощен
- `RESOURCE_REGENERATED` — ресурс восстановлен
- `ITEM_CRAFTED` — создана вещь
- `TRADE_COMPLETED` — завершена торговля

#### **Собственность** (3 типа)
- `PROPERTY_CLAIMED` — собственность захвачена
- `PROPERTY_TRANSFERRED` — передача собственности
- `PROPERTY_LOST` — потеря собственности

#### **Технологии** (3 типа)
- `TECHNOLOGY_DISCOVERED` — открыта технология
- `KNOWLEDGE_TRANSFERRED` — передача знаний
- `TOOL_CREATED` — создан инструмент

#### **Социум** (8 типов)
- `CLASS_EMERGED` — возникла класс
- `RELATIONSHIP_CHANGED` — изменились отношения
- `CONFLICT_STARTED` — начался конфликт
- `CONFLICT_ESCALATED` — конфликт обострился
- `CONFLICT_RESOLVED` — конфликт разрешён
- `REBELLION` — восстание
- `CONSCIOUSNESS_SPREAD` — распространение классового сознания
- `INTELLECTUAL_EMERGED` — появился интеллектуал

#### **Культура** (4 типа)
- `BELIEF_FORMED` — сформировано верование
- `TRADITION_CREATED` — создана традиция
- `NORM_ESTABLISHED` — установлена норма
- `RITUAL_PERFORMED` — совершён ритуал

#### **Климат** (5 типов)
- `SEASON_CHANGED` — смена сезона
- `WEATHER_EVENT` — погодное событие
- `DROUGHT` — засуха
- `PLAGUE` — чума
- `FAMINE` — голод

#### **Мир** (4 типа)
- `DAY_PASSED` — прошёл день
- `MONTH_PASSED` — прошёл месяц
- `YEAR_PASSED` — прошёл год
- `GENERATION_PASSED` — прошло поколение

#### **Общие** (1 тип)
- `CUSTOM` — пользовательское событие

### 2.3. Уровни Важности

Каждое событие имеет уровень важности (EventImportance):

```python
class EventImportance(Enum):
    TRIVIAL = 1        # Рутинные действия
    MINOR = 2          # Мелкие события
    NOTABLE = 3        # Заметные события
    IMPORTANT = 4      # Важные события
    MAJOR = 5          # Крупные события
    HISTORIC = 6       # Исторические события
```

**Применение**: система может фильтровать события по важности — логировать только важные, обновлять UI только при крупных событиях и т.д.

### 2.4. Структура События

```python
@dataclass
class Event:
    """Событие в симуляции"""

    # Тип и важность
    event_type: EventType
    importance: EventImportance = EventImportance.MINOR

    # Время события (игровое время)
    year: int = 0
    month: int = 0
    day: int = 0
    hour: int = 0

    # Место события (координаты в мире)
    location_id: Optional[str] = None
    x: float = 0.0
    y: float = 0.0

    # Участники
    actor_id: Optional[str] = None           # Кто совершил
    target_id: Optional[str] = None          # На кого направлено
    witness_ids: List[str] = field(...)      # Свидетели

    # Дополнительные данные
    data: Dict[str, Any] = field(...)

    # Описание события
    description: str = ""
    description_template: str = ""

    # Метаданные
    id: str = field(...)                     # Уникальный ID события
    timestamp: float = field(...)            # Реальное время события

    # Причинно-следственные связи
    caused_by: Optional[str] = None          # ID события-причины
    causes: List[str] = field(...)           # ID вызванных событий
```

### 2.5. Паттерн EventBus

#### **Подписка на события**

```python
# Подписка на конкретный тип события
event_bus.subscribe(EventType.MARRIAGE, handle_marriage)

# Подписка на все события
event_bus.subscribe_all(log_all_events)

# Отписка
event_bus.unsubscribe(EventType.MARRIAGE, handle_marriage)
```

#### **Публикация события**

```python
# Создаём событие
event = Event(
    event_type=EventType.MARRIAGE,
    importance=EventImportance.NOTABLE,
    year=year, month=month, day=day,
    actor_id=npc1.id,
    target_id=npc2.id,
    description=f"{npc1.name} женился на {npc2.name}"
)

# Публикуем событие
event_bus.publish(event)
```

#### **Обработка события**

```python
def handle_marriage(event: Event):
    """Обработчик события свадьбы"""
    npc1_id = event.actor_id
    npc2_id = event.target_id

    # Логируем
    print(f"Свадьба: {event.description}")

    # Обновляем состояние
    npc1.married_to = npc2_id
    npc2.married_to = npc1_id
```

### 2.6. Примеры Использования

#### **Пример 1: Отслеживание классовых конфликтов**

```python
class ClassConflictManager:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.active_conflicts = []

        # Подписываемся на события конфликтов
        event_bus.subscribe(EventType.CONFLICT_STARTED, self._on_conflict_started)
        event_bus.subscribe(EventType.CONFLICT_ESCALATED, self._on_conflict_escalated)
        event_bus.subscribe(EventType.CONFLICT_RESOLVED, self._on_conflict_resolved)

    def _on_conflict_started(self, event: Event):
        """Обработка начала конфликта"""
        conflict_info = {
            'id': event.id,
            'class1': event.data.get('class1'),
            'class2': event.data.get('class2'),
            'year': event.year,
            'intensity': 1
        }
        self.active_conflicts.append(conflict_info)
        print(f"Начался конфликт между {conflict_info['class1']} и {conflict_info['class2']}")

    def _on_conflict_escalated(self, event: Event):
        """Обработка обострения конфликта"""
        for conflict in self.active_conflicts:
            if conflict['id'] == event.id:
                conflict['intensity'] += 1
                print(f"Конфликт обострился! Интенсивность: {conflict['intensity']}")
```

#### **Пример 2: История событий**

```python
# Получение истории событий
event_history = event_bus._event_history

# Фильтрация по типу
marriage_events = [e for e in event_history if e.event_type == EventType.MARRIAGE]

# Фильтрация по важности
historic_events = [e for e in event_history if e.importance.value >= 5]

# Событие за определённый год
year_5_events = [e for e in event_history if e.year == 5]
```

---

## 3. Отслеживание Эмерджентности

### 3.1. EmergenceTracker

**EmergenceTracker** отслеживает эмерджентные явления в симуляции — явления, которые возникли органически из взаимодействия простых правил, а не были запрограммированы явно.

**Примеры эмерджентных явлений:**
- Возникновение частной собственности
- Формирование социальных классов
- Развитие идеологии и верований
- Появление лидеров и интеллектуалов
- Началcо восстаний

### 3.2. EmergenceMetrics

```python
@dataclass
class EmergenceMetrics:
    """Метрики эмерджентности"""

    # Классовая структура
    num_classes: int = 0                    # Количество классов
    class_gini: float = 0.0                 # Коэффициент Джини для классов
    class_consciousness: float = 0.0        # Среднее классовое сознание

    # Собственность
    property_inequality: float = 0.0        # Неравенство собственности (Gini)
    land_owners: int = 0                    # Количество собственников земли
    landless: int = 0                       # Количество безземельных

    # Идеология
    num_beliefs: int = 0                    # Количество верований
    belief_diversity: float = 0.0           # Разнообразие верований
    hegemony_leader: Optional[str] = None   # Гегемонистская идеология

    # Социальные движения
    num_active_conflicts: int = 0           # Активные конфликты
    rebellions: int = 0                     # Количество восстаний

    # Временные метрики
    timestamp: float = 0.0
    year: int = 0
```

### 3.3. Пример: Отслеживание Возникновения Классов

```python
# В конце каждого года
metrics = EmergenceMetrics(year=self.year)

# Отслеживаем появление классов
metrics.num_classes = len(self.classes.class_structure)

# Отслеживаем неравенство
property_values = [npc.get_property_value() for npc in self.npcs.values()]
metrics.property_inequality = calculate_gini(property_values)

# Отслеживаем идеологию
metrics.num_beliefs = len(self.beliefs.beliefs)
metrics.belief_diversity = self._calculate_belief_diversity()

# Сохраняем метрику
self.emergence_tracker.record_metrics(metrics)

# Проверяем достижение вех (рубежей)
milestones = self.emergence_tracker.check_milestones(self.year)
for milestone in milestones:
    print(f"ВЕХA: {milestone}")
    event = Event(
        event_type=EventType.YEAR_PASSED,
        importance=EventImportance.MAJOR,
        description=f"Вехa: {milestone}"
    )
    self.event_bus.publish(event)
```

---

## 4. Валидация Консистентности

### 4.1. Проверки Консистентности

**ConsistencyValidator** проверяет корректность состояния симуляции. Помогает обнаружить баги, где одна система нарушила инварианты другой.

### 4.2. Уровни Консистентности

```python
class ConsistencyLevel(Enum):
    """Уровни проверки консистентности"""

    BASIC = 1           # Базовые проверки (быстро)
    DETAILED = 2        # Детальные проверки (медленнее)
    FULL = 3            # Полная проверка (очень медленно)
```

### 4.3. Примеры Проверок

```python
def validate_state_consistency(simulation: Simulation) -> Dict[str, Any]:
    """
    Проверяет консистентность состояния симуляции.

    Проверяет:
    - Все NPC в классовой системе существуют
    - Все ссылки на собственность валидны
    - Инвентари соответствуют производству
    - Семьи состоят из живых NPC
    """
    errors = []
    warnings = []

    # === Проверка NPC ===
    for npc_id, npc in simulation.npcs.items():
        # Проверяем возраст
        if npc.age < 0:
            errors.append(f"NPC {npc.name} имеет отрицательный возраст: {npc.age}")

        # Проверяем здоровье
        if npc.health < 0 or npc.health > 100:
            errors.append(f"NPC {npc.name} имеет невалидное здоровье: {npc.health}")

        # Проверяем позицию на карте
        if not simulation.map.is_valid_position(npc.position.x, npc.position.y):
            errors.append(f"NPC {npc.name} находится вне карты")

    # === Проверка семей ===
    for family in simulation.families.families.values():
        for member_id in family.members:
            if member_id not in simulation.npcs:
                errors.append(f"Семья ссылается на несуществующего NPC {member_id}")

    # === Проверка собственности ===
    for owner_id, properties in simulation.ownership.owner_to_properties.items():
        if owner_id not in simulation.npcs:
            errors.append(f"Собственность принадлежит несуществующему NPC {owner_id}")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'timestamp': datetime.now().isoformat()
    }
```

### 4.4. Периодическая Валидация

```python
# В методе update() каждые N ходов
if self.total_days % 365 == 0:  # Раз в год
    consistency_report = validate_state_consistency(self)
    if not consistency_report['valid']:
        print("ОШИБКА КОНСИСТЕНТНОСТИ!")
        for error in consistency_report['errors']:
            print(f"  - {error}")
```

---

## 5. Обнаружение Противоречий

### 5.1. ContradictionDetector

По диалектическому материализму, **противоречия** — двигатель развития. **ContradictionDetector** обнаруживает противоречия в системе:

**Примеры противоречий:**
- **Основное противоречие капитализма**: между возросшей производительностью и ограниченной платёжеспособностью рабочих
- **Классовое противоречие**: между интересами капиталистов (максимизация прибыли) и рабочих (максимизация дохода)
- **Противоречие между городом и деревней**: разные уровни развития
- **Противоречие между верой и реальностью**: идеология против фактического положения класса

### 5.2. ContradictionMetrics

```python
@dataclass
class ContradictionMetrics:
    """Метрики противоречий в системе"""

    # Основное противоречие
    production_consumption_gap: float = 0.0     # Разрыв между производством и потреблением
    class_interests_alignment: float = 0.0      # Выравнивание интересов классов

    # Идеологические противоречия
    consciousness_belief_gap: float = 0.0       # Разрыв между сознанием и верой

    # Социальные противоречия
    conflict_intensity: float = 0.0             # Интенсивность конфликтов

    timestamp: float = 0.0
    year: int = 0
```

### 5.3. Примеры Обнаружения

```python
def detect_contradictions(simulation: Simulation) -> ContradictionMetrics:
    """Обнаруживает основные противоречия в системе"""

    metrics = ContradictionMetrics(year=simulation.year)

    # === Противоречие производства и потребления ===
    total_produced = simulation.production.total_output
    total_consumed = sum(npc.get_total_consumption() for npc in simulation.npcs.values())
    metrics.production_consumption_gap = (total_produced - total_consumed) / max(1, total_produced)

    # === Противоречие интересов классов ===
    capitalists = [n for n in simulation.npcs.values() if n.social_class == SocialClass.CAPITALIST]
    workers = [n for n in simulation.npcs.values() if n.social_class == SocialClass.WORKER]

    if capitalists and workers:
        capitalist_interests = sum(c.get_profit_rate() for c in capitalists) / len(capitalists)
        worker_interests = sum(w.get_wage_satisfaction() for w in workers) / len(workers)
        metrics.class_interests_alignment = 1.0 / (1.0 + abs(capitalist_interests - worker_interests))

    # === Противоречие верования и реальности ===
    dominant_belief = simulation.beliefs.get_dominant_belief()
    if dominant_belief:
        # Если верование говорит, что система справедлива, но рабочие голодают
        working_class_satisfaction = _calculate_satisfaction(workers)
        if dominant_belief.describes_as_fair and working_class_satisfaction < 0.3:
            metrics.consciousness_belief_gap = 0.7

    return metrics
```

---

## 6. Текущее Состояние (As-Is)

### 6.1. Что Работает

✅ **Основной цикл симуляции**
- Порядок обновления следует марксистской архитектуре
- Время продвигается корректно (часы, дни, месяцы, годы)
- Все подсистемы вызываются в правильном порядке

✅ **EventBus система**
- События публикуются и обрабатываются корректно
- История событий сохраняется
- Подписчики получают события в реальном времени

✅ **Основные типы событий**
- 24 типа событий охватывают основные аспекты симуляции
- События содержат необходимые данные (время, место, участники)

✅ **Базовая валидация консистентности**
- Проверяются критические инварианты
- Ошибки логируются в консоль

### 6.2. Проблемы и Ограничения

❌ **Неактивная EventBus система** (INT-020)
- Большинство подсистем не публикуют события
- События не используются для коммуникации между системами
- Система сильно связана (tight coupling)

❌ **Отсутствие отслеживания эмерджентности** (INT-040)
- EmergenceTracker создан, но не используется
- Вехи (milestones) развития не отслеживаются
- Нет механизма для обнаружения качественных скачков

❌ **Неполная валидация консистентности**
- Проверки выполняются редко (раз в год или вручную)
- Нет автоматического исправления ошибок
- Сложно отладить проблемы с консистентностью

❌ **Отсутствие обнаружения противоречий** (INT-019)
- ContradictionDetector создан, но не интегрирован
- Система не использует противоречия как двигатель развития
- Нет механизма для эскалации конфликтов на основе противоречий

---

## 7. Планируемое Состояние (To-Be)

Улучшения описаны в документе [FUTURE_STATE.md](./10_FUTURE_STATE.md) под EPIC-INTEGRATION и EPIC-AI.

### 7.1. INT-020: Активация EventBus Системы

**Описание**: Все подсистемы должны публиковать события при важных изменениях состояния.

**Что изменится:**
- Production система будет публиковать `RESOURCE_GATHERED`, `ITEM_CRAFTED`, `PRODUCTION_DECLINED`
- PropertySystem будет публиковать `PROPERTY_CLAIMED`, `PROPERTY_TRANSFERRED`, `PROPERTY_LOST`
- ClassSystem будет публиковать `CLASS_EMERGED`, `CLASS_CONSCIOUSNESS_CHANGED`
- BeliefSystem будет публиковать `BELIEF_FORMED`, `BELIEF_SPREAD`
- ConflictSystem будет публиковать `CONFLICT_STARTED`, `CONFLICT_ESCALATED`, `REBELLION`

**Преимущества:**
- Слабая связанность между системами
- Реактивная архитектура
- Легче отлаживать (лог всех событий)

### 7.2. INT-019: Диалектический Анализ

**Описание**: Система должна активно обнаруживать и использовать противоречия для развития.

**Что изменится:**
- ContradictionDetector будет запускаться каждый год
- Выявленные противоречия будут инициировать конфликты
- Высокие противоречия будут ускорять революции
- Идеология будет адаптироваться к противоречиям

**Примеры:**
```python
# Если production_consumption_gap > 0.3
# → вероятность восстания увеличивается
# → рабочие начинают требовать выше зарплаты

# Если consciousness_belief_gap > 0.5
# → идеология быстро меняется
# → новые верования формируются чаще
```

### 7.3. INT-040: Отслеживание Эмерджентности

**Описание**: Система должна отслеживать вехи развития и качественные скачки.

**Вехи, которые будут отслеживаться:**
1. **Первая приватизация** — появление частной собственности
2. **Первый класс рабочих** — разделение на капиталистов и пролетариат
3. **Первое восстание** — первый классовый конфликт
4. **Первая революция** — успешное восстание
5. **Первая идеология** — доминирующее верование в обществе
6. **Гегемония** — культурное господство одного класса

**Что изменится:**
- EmergenceTracker будет полностью функционален
- Достижение вех будет издавать события
- История общества будет записываться с вехами

### 7.4. Интеграция всех компонентов

**Общая картина будущего состояния:**

```
АКТИВНАЯ EventBus СИСТЕМА
  ↓
РЕАКТИВНАЯ КОММУНИКАЦИЯ между системами
  ↓
ОТСЛЕЖИВАНИЕ ПРОТИВОРЕЧИЙ
  ↓
АВТОМАТИЧЕСКОЕ ЭСКАЛИРОВАНИЕ КОНФЛИКТОВ
  ↓
ОТСЛЕЖИВАНИЕ ЭМЕРДЖЕНТНОСТИ
  ↓
ИСТОРИЯ ОБЩЕСТВА с вехами
  ↓
СЛАБО СВЯЗАННАЯ, ГИБКАЯ АРХИТЕКТУРА
```

---

## 8. Кросс-Ссылки и Связанные Документы

### Основные Системы

- **[ARCHITECTURE_OVERVIEW.md](./2_ARCHITECTURE_OVERVIEW.md)** — общая архитектура и компоненты
- **[ECONOMIC_SYSTEM.md](./4_ECONOMIC_SYSTEM.md)** — подробнее о базисе (шаг 2)
- **[SOCIETY_SYSTEM.md](./5_SOCIETY_SYSTEM.md)** — подробнее об обществе (шаги 3-5)
- **[CULTURE_SYSTEM.md](./6_CULTURE_SYSTEM.md)** — подробнее о надстройке (шаг 4)
- **[NPC_SYSTEM.md](./7_NPC_SYSTEM.md)** — подробнее о BDI цикле NPC (шаг 3)

### Планируемые Улучшения

- **[FUTURE_STATE.md](./10_FUTURE_STATE.md)** — полное описание улучшений (Task 002)
  - INT-020: Активация EventBus
  - INT-019: Диалектический анализ
  - INT-040: Отслеживание эмерджентности

### Справочная Информация

- **[GLOSSARY.md](./11_GLOSSARY.md)** — глоссарий терминов
- **[DEVELOPER_GUIDE.md](./12_DEVELOPER_GUIDE.md)** — как расширять систему

---

## 9. Заключение

Ядро симуляции реализует **марксистскую архитектуру**, в которой:
1. **Время и окружение** создают условия
2. **Экономика (базис)** определяет структуру
3. **NPC действуют** в рамках экономики
4. **Культура (надстройка)** отражает экономику
5. **Демография** обновляет состояние

**EventBus система** обеспечивает слабую связанность между компонентами, хотя в текущем состоянии она недостаточно активна.

**Планируемые улучшения** сделают систему более реактивной, будут отслеживать эмерджентные явления и использовать противоречия как двигатель развития.

---

**Последнее обновление**: 2026-02-02
**Статус документации**: ✅ Завершено
**Версия спецификации**: 1.0

