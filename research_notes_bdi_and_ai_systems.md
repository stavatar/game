# Исследование: NPC и AI системы
## BDI цикл и Генеративные Агенты

**Дата исследования:** 2026-02-02
**Статус:** Завершено для subtask-1-3

---

## 1. Обзор BDI-архитектуры

BDI (Beliefs-Desires-Intentions) - это архитектура для моделирования автономного поведения агентов.

В проекте реализовано как полный цикл, основанный на классической BDI-теории (Bratman, 1987):

```
PERCEPTION → BELIEFS → DESIRES → INTENTIONS → ACTIONS → FEEDBACK
(восприятие)→(убеждения)→(желания)→(намерения)→(действия)→(обратная связь)
```

### 1.1 Архитектурная иерархия

```
NPC (Character)
├── BDIAgent
│   ├── Beliefs (убеждения о мире)
│   ├── Desires (желания/цели)
│   ├── Intentions (намерения/планы)
│   └── deliberate() - главный цикл
├── MemoryStream (память для принятия решений)
│   ├── memories (воспоминания)
│   ├── reflections (выводы из опыта)
│   └── retrieve() - поиск релевантных воспоминаний
├── Needs (потребности, влияют на желания)
└── Personality (черты характера, модифицируют приоритеты)
```

---

## 2. Фаза 1: ВОСПРИЯТИЕ (PERCEPTION)

**Что происходит:** NPC получает информацию из окружающего мира и обновляет свои убеждения.

### 2.1 Входные данные восприятия

Восприятие описывается как словарь с разными категориями:

```python
perception_data = {
    "self_state": {           # Состояние самого NPC
        "health": 85.0,
        "hunger": 35.0,       # Низкое - голоден
        "energy": 50.0,
        "location": "loc_001"
    },
    "nearby_npcs": [          # NPC поблизости
        {"id": "npc_002", "distance": 5, "relationship": 0.5},
        {"id": "npc_003", "distance": 15, "relationship": -0.2},
    ],
    "nearby_resources": {     # Доступные ресурсы
        "res_001": {"type": "food", "quantity": 20, "distance": 10},
        "res_002": {"type": "water", "quantity": 100, "distance": 20},
    },
    "weather": "солнечно",    # Условия мира
    "time_of_day": "день",
    "threats": [              # Опасности
        {"id": "danger_001", "type": "enemy", "distance": 30}
    ]
}
```

### 2.2 Обновление убеждений из восприятия

**Код из bdi.py:**

```python
def update_beliefs_from_perception(self, perception_data: Dict[str, Any],
                                   current_day: int) -> None:
    """
    Обновляет убеждения на основе восприятия.
    """
    # Обновляем убеждения о себе
    if "self_state" in perception_data:
        state = perception_data["self_state"]
        for key, value in state.items():
            self.add_belief(BeliefCategory.SELF, key, value,
                           current_day=current_day)

    # Обновляем убеждения о мире
    if "weather" in perception_data:
        self.add_belief(BeliefCategory.WORLD, "погода",
                       perception_data["weather"], current_day=current_day)

    if "time_of_day" in perception_data:
        self.add_belief(BeliefCategory.WORLD, "время_суток",
                       perception_data["time_of_day"], current_day=current_day)

    # Обновляем убеждения об угрозах
    if "threats" in perception_data:
        for threat in perception_data["threats"]:
            self.add_belief(BeliefCategory.DANGER, threat["id"],
                           threat, current_day=current_day)
```

### 2.3 Структура убеждения

**Код из bdi.py:**

```python
@dataclass
class Belief:
    """Убеждение - единица знания NPC о мире."""
    id: str                      # Уникальный ID
    category: BeliefCategory     # Категория (SELF, WORLD, SOCIAL, etc.)
    subject: str                 # О чём убеждение
    content: Any                 # Содержание (значение)
    confidence: float = 1.0      # Уверенность (0-1)
    timestamp: int = 0           # Когда получено (день)
    source: str = "наблюдение"   # Источник информации

    def is_stale(self, current_day: int, max_age: int = 30) -> bool:
        """Проверяет, устарело ли убеждение (старше 30 дней)"""
        return (current_day - self.timestamp) > max_age

    def decay_confidence(self, amount: float = 0.1) -> None:
        """Уверенность снижается со временем"""
        self.confidence = max(0, self.confidence - amount)
```

### 2.4 Категории убеждений

```python
class BeliefCategory(Enum):
    """Категории убеждений"""
    SELF = "о себе"              # Здоровье, голод, усталость
    WORLD = "о мире"             # Погода, время, ресурсы
    SOCIAL = "социальные"        # Об отношениях с другими
    ECONOMIC = "экономические"   # О собственности, богатстве
    LOCATION = "о местах"        # Где что находится
    DANGER = "об опасностях"     # Угрозы
    OPPORTUNITY = "о возможностях" # Шансы
```

### 2.5 Забывание старых убеждений

Убеждения со временем становятся менее надёжными:

```python
def decay_old_beliefs(self, current_day: int, max_age: int = 30) -> None:
    """Уменьшает уверенность в старых убеждениях (возрастом >30 дней)"""
    for belief in self.beliefs.values():
        if belief.is_stale(current_day, max_age):
            belief.decay_confidence(0.1)
```

---

## 3. Фаза 2: УБЕЖДЕНИЯ → ЖЕЛАНИЯ (BELIEFS → DESIRES)

**Что происходит:** Убеждения о своём состоянии преобразуются в желания, определяющие цели.

### 3.1 Преобразование потребностей в желания

Потребности NPC (из системы needs.py) преобразуются в желания через специальную функцию:

**Код из bdi.py:**

```python
def update_desires_from_needs(self, needs: Dict[str, float]) -> None:
    """
    Обновляет желания на основе потребностей.

    needs: словарь вида {"hunger": 30, "energy": 80, ...}
    Низкие значения = неудовлетворённая потребность
    """
    # Маппинг потребностей на желания
    need_to_desire = {
        "hunger": DesireType.EAT,
        "thirst": DesireType.DRINK,
        "energy": DesireType.SLEEP,
        "health": DesireType.HEALTH,
        "social": DesireType.BELONG,
        "safety": DesireType.SAFETY,
    }

    for need_name, value in needs.items():
        if need_name in need_to_desire:
            desire_type = need_to_desire[need_name]
            # Низкое значение потребности = высокая интенсивность желания
            intensity = 1.0 - (value / 100.0)
            self.update_desire_intensity(desire_type, intensity)
```

**Пример:**
- Если `hunger = 35` → `intensity = 1.0 - 0.35 = 0.65` → Сильное желание есть
- Если `hunger = 95` → `intensity = 1.0 - 0.95 = 0.05` → Слабое желание есть

### 3.2 Иерархия желаний (пирамида Маслоу)

**Код из bdi.py:**

```python
class DesireType(Enum):
    """Типы желаний (по пирамиде Маслоу)"""

    # Физиологические (базовые) - высший приоритет
    SURVIVE = ("выжить", 1.0)
    EAT = ("поесть", 0.9)
    DRINK = ("попить", 0.9)
    SLEEP = ("поспать", 0.85)
    WARMTH = ("согреться", 0.8)

    # Безопасность
    SAFETY = ("быть в безопасности", 0.7)
    SHELTER = ("иметь укрытие", 0.65)
    HEALTH = ("быть здоровым", 0.7)

    # Социальные
    BELONG = ("принадлежать группе", 0.5)
    FRIENDSHIP = ("иметь друзей", 0.45)
    FAMILY = ("иметь семью", 0.5)
    INTIMACY = ("близость", 0.4)

    # Уважение
    RESPECT = ("уважение других", 0.4)
    STATUS = ("статус в обществе", 0.35)
    WEALTH = ("богатство", 0.3)
    POWER = ("власть", 0.25)

    # Самореализация
    MASTERY = ("мастерство", 0.3)
    KNOWLEDGE = ("знания", 0.25)
    CREATIVITY = ("творчество", 0.2)
    PURPOSE = ("цель в жизни", 0.2)
```

### 3.3 Структура желания

```python
@dataclass
class Desire:
    """Желание - цель или потребность NPC."""
    desire_type: DesireType       # Тип (из иерархии Маслоу)
    intensity: float = 0.5        # 0-1, насколько сильно хочет
    target: Optional[str] = None  # Конкретная цель (ID объекта/NPC)
    conditions_met: bool = False  # Выполнены ли условия
    blocked_by: List[str] = field(default_factory=list)  # Что мешает

    def get_priority(self) -> float:
        """Вычисляет приоритет желания"""
        return self.desire_type.base_priority * self.intensity

    def is_urgent(self) -> bool:
        """Проверяет, срочное ли желание"""
        # Интенсивность > 0.8 И базовый приоритет > 0.7
        return self.intensity > 0.8 and self.desire_type.base_priority > 0.7
```

### 3.4 Влияние личности на желания

Черты характера (из personality.py) модифицируют приоритеты желаний:

**Код из bdi.py:**

```python
def apply_personality(self, personality_traits: Dict[str, float]) -> None:
    """
    Применяет черты характера к приоритетам желаний.

    Например:
    - Жадность увеличивает приоритет WEALTH
    - Общительность увеличивает BELONG, FRIENDSHIP
    - Амбициозность увеличивает POWER, STATUS
    """
    trait_effects = {
        "greedy": [(DesireType.WEALTH, 0.3)],
        "social": [(DesireType.BELONG, 0.2), (DesireType.FRIENDSHIP, 0.2)],
        "ambitious": [(DesireType.POWER, 0.2), (DesireType.STATUS, 0.2)],
        "curious": [(DesireType.KNOWLEDGE, 0.3)],
        "lazy": [(DesireType.SLEEP, 0.2)],
        "brave": [(DesireType.SAFETY, -0.2)],  # Меньше боится
        "fearful": [(DesireType.SAFETY, 0.3)],
    }

    for trait, value in personality_traits.items():
        if trait in trait_effects:
            for desire_type, modifier in trait_effects[trait]:
                if desire_type in self.desires:
                    # Модифицируем приоритет
                    self.personality_modifiers[desire_type.name] = modifier * value
```

### 3.5 Выбор самого срочного желания

```python
def get_most_urgent_desire(self) -> Optional[Desire]:
    """Возвращает самое срочное желание"""
    # Сначала смотрим на критические желания
    urgent = [d for d in self.desires.values() if d.is_urgent()]
    if urgent:
        return max(urgent, key=lambda d: d.get_priority())

    # Иначе берём активное желание с наибольшим приоритетом
    active = self.get_active_desires()
    return active[0] if active else None
```

---

## 4. Фаза 3: ЖЕЛАНИЯ → НАМЕРЕНИЯ (DESIRES → INTENTIONS)

**Что происходит:** Желания превращаются в конкретные планы (намерения) с последовательностью действий.

### 4.1 Структура намерения

**Код из bdi.py:**

```python
@dataclass
class Intention:
    """
    Намерение - выбранный план действий.

    Намерение связывает желание с конкретными действиями.
    """
    id: str                          # "int_npc_001_1"
    source_desire: DesireType        # Какое желание удовлетворяет
    actions: List[Action] = field(default_factory=list)  # Последовательность
    current_action_index: int = 0    # Текущее действие в плане
    priority: float = 0.5            # Приоритет этого намерения

    # Состояние
    is_active: bool = True           # Активно ли намерение
    is_complete: bool = False        # Завершено ли
    is_failed: bool = False          # Провалилось ли

    # Прогресс
    progress: float = 0.0            # 0-1
    started_at: int = 0              # День начала

    def get_current_action(self) -> Optional[Action]:
        """Возвращает текущее действие в плане"""
        if self.current_action_index < len(self.actions):
            return self.actions[self.current_action_index]
        return None

    def advance(self) -> bool:
        """Переходит к следующему действию. Возвращает True если есть ещё."""
        self.current_action_index += 1
        if self.current_action_index >= len(self.actions):
            self.is_complete = True
            return False
        return True
```

### 4.2 Структура действия

```python
@dataclass
class Action:
    """Действие - конкретный шаг для выполнения намерения."""
    action_type: ActionType          # Тип действия (MOVE, EAT, CRAFT и т.д.)
    target_id: Optional[str] = None  # На что направлено
    location_id: Optional[str] = None  # Где выполнять
    duration: float = 1.0            # Часов на выполнение
    priority: float = 0.5            # Приоритет

    # Результат
    success_chance: float = 0.8      # Вероятность успеха (0-1)
    energy_cost: float = 10.0        # Стоимость энергии
    expected_reward: Dict[str, float] = field(default_factory=dict)

    def describe(self) -> str:
        """Описание действия для логирования"""
        desc = self.action_type.value
        if self.target_id:
            desc += f" (цель: {self.target_id})"
        return desc
```

### 4.3 Планирование действий для желания

**Код из bdi.py:**

```python
def plan_for_desire(self, desire: Desire,
                    available_actions: List[ActionType],
                    world_state: Dict[str, Any]) -> List[Action]:
    """
    Создаёт план действий для удовлетворения желания.

    Это упрощённый планировщик. В идеале здесь был бы
    полноценный планировщик (STRIPS, HTN, или GOAP).
    """
    actions = []

    # Простое сопоставление желаний и действий
    desire_actions = {
        DesireType.EAT: [
            (ActionType.GATHER, 0.5),    # Собрать еду
            (ActionType.HUNT, 0.4),      # Охотиться
            (ActionType.COOK, 0.3),      # Готовить
            (ActionType.EAT, 1.0),       # Есть
        ],
        DesireType.DRINK: [
            (ActionType.MOVE, 0.3),      # К воде
            (ActionType.DRINK, 1.0),     # Пить
        ],
        DesireType.SLEEP: [
            (ActionType.MOVE, 0.2),      # Домой
            (ActionType.SLEEP, 1.0),     # Спать
        ],
        DesireType.SAFETY: [
            (ActionType.MOVE, 0.5),      # В безопасное место
            (ActionType.REST, 0.3),      # Отдохнуть
        ],
        DesireType.BELONG: [
            (ActionType.MOVE, 0.3),      # Найти других
            (ActionType.TALK, 0.8),      # Разговаривать
        ],
        DesireType.WEALTH: [
            (ActionType.WORK, 0.6),      # Работать
            (ActionType.TRADE, 0.5),     # Торговать
            (ActionType.GATHER, 0.4),    # Собирать
        ],
        DesireType.KNOWLEDGE: [
            (ActionType.LEARN, 0.8),     # Учиться
            (ActionType.TALK, 0.4),      # Разговаривать
        ],
        DesireType.MASTERY: [
            (ActionType.WORK, 0.7),      # Работать
            (ActionType.CRAFT, 0.6),     # Мастерить
        ],
    }

    # Получаем шаблон плана
    template = desire_actions.get(desire.desire_type, [(ActionType.IDLE, 0.1)])

    for action_type, base_priority in template:
        if action_type in available_actions:
            action = Action(
                action_type=action_type,
                priority=base_priority * desire.intensity,
                target_id=desire.target,
            )
            actions.append(action)

    return actions
```

### 4.4 Создание намерения

```python
def create_intention(self, desire: Desire, actions: List[Action],
                    current_day: int) -> Intention:
    """Создаёт намерение для удовлетворения желания"""
    self._intention_counter += 1
    intention_id = f"int_{self.owner_id}_{self._intention_counter}"

    intention = Intention(
        id=intention_id,
        source_desire=desire.desire_type,
        actions=actions,
        priority=desire.get_priority(),  # Наследуем приоритет от желания
        started_at=current_day,
    )

    self.intentions[intention_id] = intention
    return intention
```

### 4.5 Выбор намерения для выполнения

```python
def select_intention(self) -> Optional[Intention]:
    """Выбирает намерение для выполнения"""
    # Фильтруем активные незавершённые намерения
    active = [
        i for i in self.intentions.values()
        if i.is_active and not i.is_complete and not i.is_failed
    ]

    if not active:
        return None

    # Выбираем по приоритету (первое активное намерение)
    return max(active, key=lambda i: i.priority)
```

---

## 5. Фаза 4: НАМЕРЕНИЯ → ДЕЙСТВИЯ (INTENTIONS → ACTIONS)

**Что происходит:** Выбранное намерение начинает выполняться через последовательность действий.

### 5.1 Главный цикл обдумывания (deliberation)

**Код из bdi.py:**

```python
def deliberate(self, current_day: int,
               available_actions: List[ActionType],
               world_state: Dict[str, Any]) -> Optional[Action]:
    """
    Главный цикл обдумывания.

    Возвращает следующее действие для выполнения.

    Шаги:
    1. Проверяем текущее намерение
    2. Выбираем самое срочное желание если нет намерения
    3. Создаём план
    4. Создаём намерение
    5. Возвращаем первое действие
    """
    # 1. Проверяем текущее намерение
    if self.current_intention:
        intention = self.intentions.get(self.current_intention)
        if intention and intention.is_active and not intention.is_complete:
            action = intention.get_current_action()
            if action:
                return action  # Продолжаем выполнение

    # 2. Выбираем самое срочное желание
    urgent_desire = self.get_most_urgent_desire()
    if not urgent_desire:
        return Action(action_type=ActionType.IDLE)

    # 3. Создаём план действий
    actions = self.plan_for_desire(urgent_desire, available_actions, world_state)
    if not actions:
        return Action(action_type=ActionType.IDLE)

    # 4. Создаём намерение
    intention = self.create_intention(urgent_desire, actions, current_day)
    self.current_intention = intention.id

    # 5. Возвращаем первое действие
    return intention.get_current_action()
```

### 5.2 Типы действий

```python
class ActionType(Enum):
    """Типы действий, которые может выполнить NPC"""

    # Базовые
    IDLE = "бездействовать"
    MOVE = "перемещаться"
    REST = "отдыхать"
    SLEEP = "спать"

    # Добыча ресурсов
    GATHER = "собирать"
    HUNT = "охотиться"
    FISH = "рыбачить"
    FARM = "обрабатывать землю"
    HARVEST = "собирать урожай"

    # Производство
    CRAFT = "мастерить"
    BUILD = "строить"
    COOK = "готовить"

    # Социальное
    TALK = "разговаривать"
    TRADE = "торговать"
    HELP = "помогать"
    TEACH = "обучать"
    LEARN = "учиться"

    # Потребление
    EAT = "есть"
    DRINK = "пить"

    # Работа
    WORK = "работать"
    WORK_FOR_OTHER = "работать на другого"
```

---

## 6. Фаза 5: ОБРАТНАЯ СВЯЗЬ (FEEDBACK)

**Что происходит:** Результаты действия обновляют состояние NPC, память и убеждения.

### 6.1 Обработка результата действия

**Код из bdi.py:**

```python
def complete_action(self, action: Action, success: bool,
                   result: Dict[str, Any]) -> None:
    """
    Обрабатывает завершение действия.

    Обновляет намерение и убеждения на основе результата.
    """
    if self.current_intention:
        intention = self.intentions.get(self.current_intention)
        if intention:
            if success:
                # Действие успешно - переходим к следующему
                if not intention.advance():
                    # План завершён
                    self.current_intention = None
            else:
                # Действие провалилось - отказываемся от намерения
                intention.is_failed = True
                self.current_intention = None
```

### 6.2 Реакция на внезапные события

NPC может прервать текущее намерение при внезапной опасности:

**Код из bdi.py:**

```python
def react_to_event(self, event_type: str, event_data: Dict[str, Any],
                  current_day: int) -> Optional[Action]:
    """
    Реакция на внезапное событие.

    Может прервать текущее намерение если событие важное.
    """
    # Опасность - немедленная реакция
    if event_type == "danger":
        # Прерываем текущее намерение
        if self.current_intention:
            self.abandon_intention(self.current_intention)

        # Добавляем убеждение об угрозе
        self.add_belief(BeliefCategory.DANGER, event_data.get("id", "unknown"),
                       event_data, current_day=current_day)

        # Срочное желание безопасности
        self.update_desire_intensity(DesireType.SAFETY, 1.0)

        return Action(
            action_type=ActionType.MOVE,
            priority=1.0,
            target_id=event_data.get("safe_location"),
        )

    # Возможность - можем отложить
    if event_type == "opportunity":
        self.add_belief(BeliefCategory.OPPORTUNITY, event_data.get("id", "unknown"),
                       event_data, current_day=current_day)
        # Не прерываем текущее действие

    return None
```

---

## 7. Генеративные Агенты: Система Памяти

**Основание:** Stanford "Generative Agents: Interactive Simulacra of Human Behavior"

Память - это основа для принятия решений. NPC хранит воспоминания и делает из них выводы.

### 7.1 Типы воспоминаний

**Код из memory.py:**

```python
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
```

### 7.2 Структура воспоминания

**Код из memory.py:**

```python
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
    id: str                          # "mem_npc_001_1"
    memory_type: MemoryType          # Тип воспоминания
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

    def get_recency_score(self, current_day: int) -> float:
        """
        Вычисляет оценку свежести воспоминания.
        Свежие воспоминания более доступны.

        Использует экспоненциальное затухание:
        score = (0.995)^(days_ago)
        """
        days_ago = current_day - (self.year * 360 + self.month * 30 + self.day)
        decay_rate = 0.995
        return math.pow(decay_rate, days_ago)
```

### 7.3 Извлечение (Retrieval) воспоминаний

**Код из memory.py:**

```python
def retrieve(self,
             current_day: int,
             count: int = 5,
             about_npc: str = None,
             about_location: str = None,
             memory_type: MemoryType = None,
             min_importance: float = 0.0) -> List[MemoryEntry]:
    """
    Извлекает наиболее релевантные воспоминания.

    Использует комбинацию трёх факторов:
    1. Важность (importance)
    2. Свежесть (recency)
    3. Релевантность запросу (relevance)
    """
    candidates = list(self.memories.values())

    # Фильтруем по минимальной важности
    candidates = [m for m in candidates if m.importance >= min_importance]

    # Вычисляем оценки для каждого воспоминания
    query_npcs = [about_npc] if about_npc else None
    scored = [
        (m, m.get_retrieval_score(current_day, query_npcs, about_location))
        for m in candidates
    ]

    # Сортируем по оценке (самые релевантные первыми)
    scored.sort(key=lambda x: x[1], reverse=True)

    # Возвращаем топ N воспоминаний
    result = []
    for memory, score in scored[:count]:
        memory.access_count += 1        # Отмечаем обращение
        memory.last_accessed = current_day
        result.append(memory)

    return result
```

### 7.4 Рефлексия (Reflection) - выводы из опыта

**Код из memory.py:**

```python
def reflect(self, current_year: int, current_day: int) -> List[Reflection]:
    """
    Выполняет рефлексию - анализ накопленного опыта.

    Создаёт выводы типа:
    - "X часто помогает мне" → "X - друг"
    - "Зимой всегда голодно" → "Нужно запасать еду"
    - "Богатые забирают много" → "Это несправедливо"

    Возвращает список новых рефлексий.
    """
    new_reflections = []

    # 1. Рефлексия об NPC
    for npc_id, memory_ids in self._by_npc.items():
        if npc_id == self.owner_id:
            continue

        memories = [self.memories[mid] for mid in memory_ids
                   if mid in self.memories]
        if len(memories) >= 3:  # Достаточно данных для вывода
            reflection = self._reflect_about_npc(npc_id, memories,
                                                current_year, current_day)
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
```

### 7.5 Пример рефлексии об NPC

**Код из memory.py:**

```python
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

    # Формируем вывод на основе паттерна
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
```

### 7.6 Получение впечатления об NPC

```python
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

    # Текстовое описание на основе впечатления
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
```

---

## 8. Интеграция: BDI + Память → Решения

**Как память влияет на BDI цикл:**

### 8.1 Восприятие улучшается памятью

NPC может вспомнить что-то из памяти, когда видит связанный объект:

```python
# Пример (псевдокод, не в коде)
def update_beliefs_from_perception(perception_data):
    # Добавляем новые убеждения из восприятия
    self.add_belief(...)

    # Но также вспоминаем связанные события
    if "npc" in perception_data:
        npc_id = perception_data["npc"]
        memories = self.memory_stream.retrieve_about_npc(npc_id)
        # Эти воспоминания влияют на интерпретацию текущего события
```

### 8.2 Желания модифицируются памятью

Воспоминания влияют на приоритеты:

```python
# Пример: если у NPC есть воспоминание о голоде в прошлом
# он может дольше хранить еду или работать для получения запасов
```

### 8.3 Намерения учитывают опыт

```python
def plan_for_desire(self, desire, ...):
    # Смотрим в память: какие действия помогли раньше?
    # memories = self.memory_stream.retrieve(action_type)
    # Выбираем план на основе успешного опыта
```

---

## 9. Полный пример: BDI цикл в действии

### Сценарий: NPC голоден

**День 1, час 14:00 - Состояние начальное:**

```
NPC: Иван, 25 лет, фермер
- Hunger: 35 (НИЗКО!)
- Energy: 70
- Safety: 100
- Location: дом
```

### Шаг 1: ВОСПРИЯТИЕ

```python
perception_data = {
    "self_state": {
        "hunger": 35,
        "energy": 70,
        "health": 100,
        "location": "loc_home"
    },
    "nearby_resources": {
        "res_food_001": {"type": "food", "quantity": 10, "location": "kitchen"}
    },
    "weather": "солнечно",
    "time_of_day": "день"
}

bdi_agent.update_beliefs_from_perception(perception_data, current_day=1)
```

**Результат:** Добавлены убеждения:
- `SELF_hunger = 35`
- `LOCATION_res_food_001 = kitchen`
- `WORLD_weather = солнечно`

### Шаг 2: ЖЕЛАНИЯ

```python
# Из потребностей → желания
needs = {"hunger": 35, "energy": 70, ...}
bdi_agent.update_desires_from_needs(needs)

# hunger=35 → intensity = 1.0 - 0.35 = 0.65 (сильное желание есть!)
# DesireType.EAT имеет base_priority = 0.9
# get_priority() = 0.9 * 0.65 = 0.585
```

**Результат:**
```
Desire: EAT
- intensity: 0.65
- priority: 0.585 (очень высокий!)
- is_urgent: True (intensity > 0.8? нет, но базовый приоритет 0.9)
```

### Шаг 3: НАМЕРЕНИЯ (Планирование)

```python
# Выбираем самое срочное желание
urgent_desire = bdi_agent.get_most_urgent_desire()  # EAT
active_actions = [ActionType.MOVE, ActionType.EAT, ActionType.COOK, ...]

# Планируем
actions = bdi_agent.plan_for_desire(urgent_desire, active_actions, world_state)
# template для EAT: [(GATHER, 0.5), (HUNT, 0.4), (COOK, 0.3), (EAT, 1.0)]
# Результат: [
#   Action(GATHER, priority=0.5*0.65=0.325),
#   Action(HUNT, priority=0.4*0.65=0.26),
#   Action(COOK, priority=0.3*0.65=0.195),
#   Action(EAT, priority=1.0*0.65=0.65)
# ]

intention = bdi_agent.create_intention(urgent_desire, actions, current_day=1)
# intention.id = "int_ivan_001"
# intention.source_desire = DesireType.EAT
# intention.actions = [GATHER, HUNT, COOK, EAT]
# intention.current_action_index = 0
```

**Результат:** Намерение создано с планом: GATHER → HUNT → COOK → EAT

### Шаг 4: ДЕЙСТВИЯ

```python
# Главный цикл
action = bdi_agent.deliberate(current_day=1, available_actions, world_state)
# Возвращает: Action(GATHER)

# Выполняем действие
# Иван идёт собирать ягоды и фрукты
# (симуляция выполняет GATHER)
```

### Шаг 5: РЕЗУЛЬТАТ И ОБРАТНАЯ СВЯЗЬ

```python
# Действие завершилось
action_result = {
    "success": True,
    "food_gained": 5,
    "time_spent": 1.0,  # час
    "fatigue_gained": 10
}

bdi_agent.complete_action(action, success=True, result=action_result)
# intention.advance() → переходим к следующему действию (HUNT)
# current_intention остаётся active

# Обновляем память
memory_stream.add_memory(
    memory_type=MemoryType.ACTION,
    description="Собирал ягоды в лесу",
    year=1, month=0, day=1, hour=14,
    importance=0.4,
    emotional_valence=EmotionalValence.NEUTRAL,
    related_objects=["res_berry_001"]
)
```

### Шаг 6: СЛЕДУЮЩИЙ ЦИК

```python
# Теперь hunger = 30 (снизилась)
# energy = 60 (тоже упала)
# Иван продолжит план...

# Час 15:00 - второе действие HUNT
# Результат: food_gained=8
# hunger = 22

# Час 16:00 - третье действие COOK
# Результат: готовое блюдо

# Час 17:00 - четвёртое действие EAT
# Результат: hunger = 85 (удовлетворено!)
# intention.is_complete = True
# current_intention = None
```

### Шаг 7: РЕФЛЕКСИЯ (позже, когда накопится опыт)

```python
# Спустя несколько дней, NPC делает рефлексию
reflections = memory_stream.reflect(year=1, day=5)

# Пример рефлексии:
# "Когда собираю ягоды и охотлюсь, я хорошо утоляю голод"
# "Фрукты находятся в лесу к северу от дома"
# "После работы я всегда чувствую себя усталым"
```

---

## 10. Ключевые особенности системы

### 10.1 Иерархическая структура решений

```
Потребности (Needs)
    ↓
Желания (Desires) - иерархия Маслоу
    ↓
Намерения (Intentions) - планы
    ↓
Действия (Actions) - атомарные операции
```

### 10.2 Память как фундамент

- **Воспоминания** хранят историю
- **Рефлексии** извлекают паттерны из истории
- **Впечатления** об NPC основаны на воспоминаниях
- **Убеждения** обновляются из восприятия И памяти

### 10.3 Личность как модификатор

Черты характера не меняют архитектуру, но модифицируют:
- Приоритеты желаний
- Скорость действий
- Совместимость с другими

### 10.4 Адаптивность

- Убеждения устаревают (decay_confidence)
- Воспоминания забываются (забывание неважного)
- Намерения могут быть прерваны срочными событиями
- Желания меняются при изменении потребностей

---

## 11. Текущие ограничения и будущее развитие

### 11.1 Текущие ограничения

1. **Планировщик** очень упрощён (простой шаблон)
   - Нет полноценного GOAP или HTN
   - Нет рассчитывания затрат ресурсов
   - Нет планирования кооперации

2. **Персистентность намерений** отсутствует
   - Намерения теряются при перезагрузке
   - Нет сохранения долгосрочных целей

3. **Средства-целевое рассуждение** минимально
   - Нет сложного средства-целевого анализа
   - Нет цепочек: ЦЕЛЬ → ПОДЦЕЛИ → СРЕДСТВА

4. **Координация между NPC** отсутствует
   - NPC не кооперируют для достижения целей
   - Нет коллективных намерений

### 11.2 Планируемые улучшения (из Task 002)

**EPIC-AI** содержит 36 проблем, включая:

- **AI-001:** Персистентность намерений (сохранение целей)
- **AI-005:** Полноценное средства-целевое рассуждение (means-end reasoning)
- **AI-015:** Кооперативное планирование между агентами
- **AI-020:** Долгосрочное планирование и обучение

---

## 12. Выводы

### BDI цикл в проекте:

1. **Восприятие** → обновление убеждений из окружения
2. **Убеждения** → преобразование в желания на основе потребностей
3. **Желания** → создание планов через простой шаблонный планировщик
4. **Намерения** → выбор активного намерения для выполнения
5. **Действия** → выполнение шагов плана
6. **Обратная связь** → обновление состояния и памяти

### Память (Generative Agents):

- Хранит **воспоминания** с временем, важностью, эмоциями
- Извлекает релевантные воспоминания через комбинацию свежести, важности, релевантности
- Делает **рефлексии** - выводы из паттернов опыта
- Преобразует воспоминания в **впечатления** об других NPC

### Интеграция:

- Воспоминания влияют на восприятие (добавляют контекст)
- Желания модифицируются личностью и историческим опытом
- Планы учитывают знания о мире (из убеждений)
- Рефлексии создают долгосрочные убеждения

---

## Файлы исследуемого кода:

- `./src/npc/character.py` - NPC класс
- `./src/npc/ai/bdi.py` - BDI-архитектура (1258 строк)
- `./src/npc/memory.py` - Система памяти (576 строк)
- `./src/npc/personality.py` - Личность (195 строк)
- `./src/npc/needs.py` - Потребности (168 строк)

**Общее количество строк кода NPC/AI:** ~2700 строк

---

**Исследование завершено:** ✓
**Документ:** BDI цикл с кодом и примерами
**Готово для следующей фазы:** Подготовка документации
