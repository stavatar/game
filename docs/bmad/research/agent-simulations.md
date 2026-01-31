# Research: Agent-Based Simulations & Game AI

## Руководство по созданию реалистичных агентных симуляций

**Версия:** 1.0
**Дата:** 2026-01-31
**Тип документа:** Исследование
**Статус:** Завершено

---

## 1. Введение

Данный документ содержит результаты исследования лучших практик создания агентных симуляций с реалистичным поведением NPC. Материал предназначен для использования при разработке проекта "Базис и Надстройка".

---

## 2. Ключевые Концепции

### 2.1 Agent-Based Modeling (ABM)

**Определение:** Agent-Based Model (ABM) — это вычислительная модель, симулирующая действия и взаимодействия автономных агентов для понимания поведения системы.

> "The whole is greater than the sum of its parts" — эмерджентность возникает из взаимодействия простых компонентов.

**Ключевые характеристики:**
- Агенты действуют **автономно**
- Агенты **взаимодействуют** друг с другом
- Из взаимодействий возникает **эмерджентное** поведение
- Система демонстрирует **нелинейную** динамику

### 2.2 Complex Adaptive Systems (CAS)

Сложные адаптивные системы характеризуются:
- **Агентами**, способными адаптироваться
- **Нелинейными** взаимодействиями
- **Эмерджентными** свойствами
- **Самоорганизацией**

**Применение к проекту:**
```
Примитивная община → Появление излишков → Частная собственность
                                              ↓
                                         Классы (EMERGENT!)
                                              ↓
                                         Идеология (EMERGENT!)
```

---

## 3. Референсные Игры и Их Техники

### 3.1 Dwarf Fortress

**Источник:** [Game AI Pro 2 - Simulation Principles from Dwarf Fortress](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter41_Simulation_Principles_from_Dwarf_Fortress.pdf)

#### Принципы дизайна (от Tarn Adams):

| Принцип | Описание | Применение к проекту |
|---------|----------|---------------------|
| **Автономия дварфов** | "Дварфы также должны осуществлять автономию вне официальных обязанностей" | NPC действуют по BDI, а не по скриптам |
| **Актёры своих историй** | "Это большая часть того, откуда берётся эмерджентный нарратив" | Memory System + Relationships |
| **Глубокая симуляция** | Сотни факторов влияют на поведение | Потребности, личность, верования, класс |

#### Ключевые системы DF:

```
┌─────────────────────────────────────────────────────────┐
│                  DWARF FORTRESS                          │
├─────────────────────────────────────────────────────────┤
│  Needs System       │ Hunger, thirst, sleep, social    │
│  Personality Traits │ 50+ traits influence behavior    │
│  Relationships      │ Friends, enemies, lovers         │
│  Memory            │ Dwarves remember events          │
│  Skills            │ Learn through practice           │
│  Goals             │ Personal ambitions               │
└─────────────────────────────────────────────────────────┘
```

#### Уроки для проекта:

1. **Не скриптуй — симулируй.** Вместо "NPC #5 идёт в точку А" → "NPC голоден и ищет еду"
2. **Уникальность через комбинацию.** Каждый NPC — комбинация traits, не хардкод
3. **История возникает.** Не пиши сюжет — дай системам породить его

### 3.2 The Sims (Utility AI)

**Источник:** [The Genius AI Behind The Sims](https://gmtk.substack.com/p/the-genius-ai-behind-the-sims)

#### Utility-Based Decision Making

```python
# Концептуальный пример Utility AI
def choose_action(sim):
    actions = get_available_actions()
    utilities = {}

    for action in actions:
        utility = 0
        for need in sim.needs:
            # Как хорошо это действие удовлетворит потребность?
            satisfaction = action.satisfies(need)
            # Насколько срочна потребность?
            urgency = 1.0 - need.current  # Чем ниже, тем срочнее
            utility += satisfaction * urgency

        # Модификаторы личности
        utility *= sim.personality.preference(action)
        # Модификатор расстояния
        utility *= distance_penalty(sim, action.target)

        utilities[action] = utility

    return max(utilities, key=utilities.get)
```

#### Система Потребностей (вдохновлена Маслоу)

```
┌─────────────────────────────────────────┐
│           ИЕРАРХИЯ МАСЛОУ               │
├─────────────────────────────────────────┤
│  5. Самоактуализация  │  Dreams, Goals │ ← Низкий приоритет
│  4. Уважение          │  Status        │
│  3. Социальные        │  Friends, Love │
│  2. Безопасность      │  Shelter       │
│  1. Физиологические   │  Food, Sleep   │ ← Высокий приоритет
└─────────────────────────────────────────┘

Принцип: Удовлетворяй базовые потребности ПЕРЕД высшими
```

**Применение к проекту:**

```python
class NeedSystem:
    PRIORITY_ORDER = [
        NeedType.HUNGER,      # Критично: умрёт
        NeedType.THIRST,      # Критично: умрёт
        NeedType.SLEEP,       # Важно: дебафф
        NeedType.SAFETY,      # Важно: стресс
        NeedType.SOCIAL,      # Желательно
        NeedType.ENTERTAINMENT,  # Желательно
        NeedType.SELF_ACTUALIZATION  # Роскошь
    ]
```

### 3.3 RimWorld (AI Storyteller)

**Источник:** [Emergent Narrative - TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/Main/EmergentNarrative)

#### AI Storyteller Concept

RimWorld использует централизованного AI Storyteller, который:
- Периодически запускает **события**
- Подстраивает **сложность** под игрока
- Создаёт **драматическое напряжение**

**Типы Storytellers:**

| Storyteller | Стиль | Применение |
|-------------|-------|------------|
| Cassandra | Плавное нарастание | Реалистичная симуляция |
| Phoebe | Много передышек | Sandbox режим |
| Randy | Полный хаос | Экстремальные эксперименты |

**Применение к проекту:**

```python
class EventDirector:
    """Генератор событий для драматизма"""

    def check_events(self, world_state):
        # Если слишком спокойно — добавь конфликт
        if world_state.tension < 0.3:
            self.trigger_crisis()

        # Если слишком тяжело — дай передышку
        if world_state.tension > 0.8:
            self.trigger_relief()

    def trigger_crisis(self):
        options = [
            Catastrophe.DROUGHT,
            Catastrophe.PLAGUE,
            Event.CLASS_CONFLICT,
            Event.INVASION
        ]
        return self.weighted_choice(options)
```

### 3.4 Crusader Kings (Character-Driven Simulation)

**Источник:** [How complex AI can promote Emergent Narrative](https://www.joeduffy.games/how-complex-ai-can-promote-emergent-narrative)

#### Принципы Henrik Fahraeus (CK2):

1. **Complex Simulation** — Много взаимосвязанных систем
2. **Unpredictability/Chaos** — Случайность для сюрпризов
3. **Human Factor** — Игрок добавляет интерпретацию
4. **Seedling of Narrative** — Зёрна историй (traits, events)
5. **Conflict** — Противоречия между персонажами
6. **Dubious Morals** — Моральные дилеммы

**Применение к проекту:**

```
SEEDLING: NPC Иван жаден (trait: GREEDY)
     ↓
CONFLICT: Иван хочет землю Петра
     ↓
EMERGENCE: Иван накапливает ресурсы, строит альянсы
     ↓
CRISIS: Конфликт между Иваном и Петром
     ↓
RESOLUTION: Одна из сторон побеждает
     ↓
CONSEQUENCE: Изменение классовой структуры
```

---

## 4. Generative Agents (Stanford, 2023)

**Источник:** [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)

### 4.1 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                  GENERATIVE AGENT                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   PERCEPTION ──────────► MEMORY STREAM                      │
│        │                      │                             │
│        │                      ├── Observations              │
│        │                      ├── Reflections               │
│        │                      └── Plans                     │
│        │                                                    │
│        ▼                      │                             │
│   RETRIEVAL ◄────────────────┘                             │
│        │                                                    │
│        ├── Recency (когда?)                                │
│        ├── Importance (насколько важно?)                   │
│        └── Relevance (насколько релевантно?)               │
│        │                                                    │
│        ▼                                                    │
│   REFLECTION ─────────► Higher-level insights              │
│        │                                                    │
│        ▼                                                    │
│   PLANNING ──────────► Day schedule, reactions             │
│        │                                                    │
│        ▼                                                    │
│   ACTION ────────────► Behavior in world                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Memory Stream

**Три типа записей:**

| Тип | Описание | Пример |
|-----|----------|--------|
| **Observation** | Что NPC видит/делает | "Видел Ивана собирающего ягоды" |
| **Reflection** | Вывод из опыта | "Иван часто помогает — он друг" |
| **Plan** | Намерение на будущее | "Завтра пойду на охоту с Иваном" |

### 4.3 Retrieval Function

```python
def retrieve_memories(agent, query, k=10):
    """Выбрать k наиболее релевантных воспоминаний"""
    scores = {}

    for memory in agent.memory_stream:
        # Recency: недавние важнее
        recency = exponential_decay(memory.timestamp, current_time)

        # Importance: важные события помнятся лучше
        importance = memory.importance  # 0.0 - 1.0

        # Relevance: насколько связано с запросом
        relevance = semantic_similarity(memory.description, query)

        # Итоговый скор
        scores[memory] = recency * 0.3 + importance * 0.3 + relevance * 0.4

    return sorted(scores, key=scores.get, reverse=True)[:k]
```

### 4.4 Reflection

```python
def reflect(agent):
    """Создать высокоуровневые выводы из опыта"""
    recent = agent.get_recent_memories(100)

    # Найти паттерны
    patterns = find_patterns(recent)

    for pattern in patterns:
        # Создать reflection
        reflection = Reflection(
            description=f"Conclusion: {pattern.summary}",
            supporting_memories=pattern.memories,
            importance=calculate_importance(pattern)
        )
        agent.memory_stream.add(reflection)
```

**Пример Reflection:**

```
Memories:
- "Иван дал мне еду" (day 5)
- "Иван помог построить хижину" (day 8)
- "Иван защитил меня от волка" (day 12)

Reflection:
- "Иван — мой друг, которому можно доверять"
- Importance: HIGH
- Supporting: [memory_5, memory_8, memory_12]
```

### 4.5 Planning

```python
def plan_day(agent):
    """Создать план на день"""
    # Получить релевантные воспоминания
    context = agent.retrieve("what should I do today")

    # Учесть потребности
    urgent_needs = agent.needs.get_urgent()

    # Учесть обязательства
    commitments = agent.get_commitments()

    # Сгенерировать план
    plan = []
    for hour in range(6, 22):  # 6:00 - 22:00
        activity = choose_activity(
            hour=hour,
            needs=urgent_needs,
            commitments=commitments,
            context=context
        )
        plan.append((hour, activity))

    return plan
```

### 4.6 Ablation Study Results

Stanford провёл исследование, убирая компоненты:

| Компонент | Без него | Эффект |
|-----------|----------|--------|
| Memory | Agent без памяти | Не помнит предыдущие разговоры |
| Reflection | Agent без рефлексии | Не делает выводов, поверхностные отношения |
| Planning | Agent без планирования | Хаотичное поведение, нет целей |

**Вывод:** Все три компонента критически важны для реалистичного поведения.

---

## 5. BDI Architecture

**Источник:** [BDI Agents: From Theory to Practice](https://cdn.aaai.org/ICMAS/1995/ICMAS95-042.pdf)

### 5.1 Философская основа (Bratman)

Michael Bratman разработал теорию **практического рассуждения**:

> Intentions are **conduct-controlling** pro-attitudes, not merely potential influences on action.

**Ключевые свойства Intentions:**
1. **Temporal persistence** — намерения сохраняются во времени
2. **Constrain future planning** — новые планы согласуются с существующими
3. **Prompt means-end reasoning** — намерения ведут к планированию

### 5.2 Компоненты BDI

```
┌─────────────────────────────────────────────────────────┐
│                     BDI AGENT                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  BELIEFS (B)                                            │
│  ├── О мире: "В лесу есть еда"                         │
│  ├── О себе: "Я голоден"                               │
│  └── О других: "Иван — враг"                           │
│                                                          │
│  DESIRES (D)                                            │
│  ├── Потребности: "Хочу есть"                          │
│  ├── Цели: "Хочу накопить богатство"                   │
│  └── Мечты: "Хочу стать вождём"                        │
│                                                          │
│  INTENTIONS (I)                                         │
│  ├── Текущий план: [go_to_forest, gather, return]      │
│  ├── Текущий шаг: gather                               │
│  └── Обязательства: "Завтра помогу Петру"              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.3 BDI Reasoning Cycle

```python
def bdi_cycle(agent, world):
    """Один цикл BDI-рассуждения"""

    # 1. PERCEIVE — обновить beliefs из мира
    percepts = world.get_percepts(agent)
    agent.beliefs.update(percepts)

    # 2. DELIBERATE — выбрать desire для преследования
    if not agent.current_intention or agent.current_intention.achieved:
        desires = agent.generate_desires()
        chosen_desire = agent.deliberate(desires)

        # 3. PLAN — создать план достижения
        plan = agent.plan(chosen_desire)
        agent.current_intention = Intention(chosen_desire, plan)

    # 4. EXECUTE — выполнить следующий шаг плана
    if agent.current_intention:
        action = agent.current_intention.next_step()
        result = world.execute(agent, action)

        # 5. REPLAN if needed
        if result.failed:
            agent.current_intention = None  # Пересмотреть
```

### 5.4 Deliberation Process

```python
def deliberate(agent, desires):
    """Выбрать какой desire преследовать"""
    scored_desires = []

    for desire in desires:
        score = 0.0

        # Насколько срочно?
        score += desire.urgency * 0.4

        # Насколько достижимо?
        achievability = estimate_achievability(desire, agent.beliefs)
        score += achievability * 0.3

        # Совместимо с существующими intentions?
        compatibility = check_compatibility(desire, agent.intentions)
        score += compatibility * 0.2

        # Соответствует личности?
        personality_fit = agent.personality.evaluate(desire)
        score += personality_fit * 0.1

        scored_desires.append((desire, score))

    return max(scored_desires, key=lambda x: x[1])[0]
```

---

## 6. Memory Architecture for NPCs

**Источник:** [Beyond Short-term Memory: The 3 Types of Long-term Memory](https://machinelearningmastery.com/beyond-short-term-memory-the-3-types-of-long-term-memory-ai-agents-need/)

### 6.1 Three Types of Long-Term Memory

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  EPISODIC MEMORY                                            │
│  ├── Что: Конкретные события и опыт                        │
│  ├── Пример: "Иван помог мне в день 5"                     │
│  └── Структура: (timestamp, event, participants, emotion)   │
│                                                              │
│  SEMANTIC MEMORY                                            │
│  ├── Что: Факты и общие знания                             │
│  ├── Пример: "Иван — мой друг"                             │
│  └── Структура: (subject, predicate, object, confidence)    │
│                                                              │
│  PROCEDURAL MEMORY                                          │
│  ├── Что: Навыки и "как делать"                            │
│  ├── Пример: "Как охотиться"                               │
│  └── Структура: (skill_name, steps, proficiency)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Применение к проекту

```python
@dataclass
class EpisodicMemory:
    """Конкретное событие"""
    id: UUID
    timestamp: int
    description: str
    participants: List[UUID]
    location: Tuple[int, int]
    emotion: float  # -1 to 1
    importance: float

@dataclass
class SemanticMemory:
    """Факт или вывод"""
    subject: str  # "Ivan"
    predicate: str  # "is_friend"
    object: Optional[str]  # None для unary predicates
    confidence: float
    derived_from: List[UUID]  # Episodic memories

@dataclass
class ProceduralMemory:
    """Навык"""
    skill_name: str
    steps: List[str]
    proficiency: float  # 0-100
    last_used: int
```

### 6.3 Memory Integration

```python
class IntegratedMemorySystem:
    """Объединённая система памяти"""

    def __init__(self):
        self.episodic = []
        self.semantic = {}
        self.procedural = {}

    def add_experience(self, event: Event):
        """Добавить опыт и извлечь знания"""
        # 1. Сохранить в episodic
        memory = self.create_episodic(event)
        self.episodic.append(memory)

        # 2. Попробовать извлечь semantic
        self.extract_semantic(memory)

        # 3. Обновить procedural если это действие
        if event.is_action:
            self.update_procedural(event.action_type)

    def retrieve(self, context: str, memory_type: str = "all"):
        """Получить релевантные воспоминания"""
        if memory_type == "episodic":
            return self.retrieve_episodic(context)
        elif memory_type == "semantic":
            return self.retrieve_semantic(context)
        elif memory_type == "procedural":
            return self.retrieve_procedural(context)
        else:
            return self.retrieve_all(context)
```

---

## 7. Emergent Narrative Design

**Источник:** [The Power of Emergent Stories in Video Games](https://dawnosaur.substack.com/p/the-power-of-emergent-stories-in)

### 7.1 Принципы

| Принцип | Описание | Реализация |
|---------|----------|------------|
| **Story-sifting** | Выделение интересного из хаоса | Event importance system |
| **Apophenia** | Игрок находит паттерны | Абстракция, недосказанность |
| **Conflict** | Противоречия создают драму | Классовые противоречия, личные враги |
| **Stakes** | Должно быть что терять | Permadeath, необратимые решения |
| **Agency** | Агенты сами принимают решения | BDI, автономия |

### 7.2 Story-Sifting System

```python
class StorySifter:
    """Выделяет интересные события"""

    INTEREST_FACTORS = {
        'conflict': 0.3,
        'relationship_change': 0.2,
        'status_change': 0.2,
        'death': 0.15,
        'birth': 0.1,
        'discovery': 0.05
    }

    def calculate_interest(self, event: Event) -> float:
        score = 0.0

        # Базовый интерес по типу
        score += event.importance.value * 0.3

        # Бонус за конфликт
        if event.involves_conflict:
            score += 0.3

        # Бонус за изменение отношений
        if event.changes_relationship:
            score += 0.2

        # Бонус за смерть/рождение важного NPC
        if event.type in [EventType.NPC_DIED, EventType.NPC_BORN]:
            score += event.npc_importance * 0.2

        return min(1.0, score)

    def get_highlights(self, events: List[Event], n: int = 10) -> List[Event]:
        """Получить N самых интересных событий"""
        scored = [(e, self.calculate_interest(e)) for e in events]
        sorted_events = sorted(scored, key=lambda x: x[1], reverse=True)
        return [e for e, _ in sorted_events[:n]]
```

---

## 8. Utility AI Deep Dive

**Источник:** [Utility system - Wikipedia](https://en.wikipedia.org/wiki/Utility_system)

### 8.1 Формулы расчёта Utility

```python
def calculate_utility(action, agent, world):
    """Рассчитать полезность действия"""

    # 1. Базовая полезность от удовлетворения потребностей
    need_utility = 0.0
    for need in agent.needs:
        satisfaction = action.satisfies(need)
        urgency = need.get_urgency()  # 0-1, выше = срочнее
        need_utility += satisfaction * urgency

    # 2. Модификатор от личности
    personality_mod = agent.personality.preference(action)

    # 3. Модификатор от расстояния
    distance = world.distance(agent.location, action.target)
    distance_mod = 1.0 / (1.0 + distance * 0.1)

    # 4. Модификатор от времени суток
    time_mod = action.time_preference(world.time_of_day)

    # 5. Модификатор от отношений (если действие с другим NPC)
    if action.involves_other:
        relationship = agent.relationships.get(action.other_id)
        relation_mod = 0.5 + relationship.strength * 0.5
    else:
        relation_mod = 1.0

    # Итоговая формула
    utility = need_utility * personality_mod * distance_mod * time_mod * relation_mod

    # 6. Добавить небольшой рандом для разнообразия
    utility *= random.uniform(0.9, 1.1)

    return utility
```

### 8.2 Болтцмановское распределение (The Sims 3)

Richard Evans использовал Boltzmann distribution:

```python
import math

def boltzmann_selection(actions_with_utilities, temperature):
    """
    Выбор действия с вероятностью пропорциональной exp(utility/temperature)

    temperature низкая → выбирается лучшее действие
    temperature высокая → больше случайности
    """
    # Рассчитать экспоненты
    exp_utilities = []
    for action, utility in actions_with_utilities:
        exp_u = math.exp(utility / temperature)
        exp_utilities.append((action, exp_u))

    # Нормализовать в вероятности
    total = sum(exp_u for _, exp_u in exp_utilities)
    probabilities = [(a, exp_u / total) for a, exp_u in exp_utilities]

    # Выбрать случайно по вероятностям
    return weighted_random_choice(probabilities)

def get_temperature(agent):
    """
    Счастливый NPC → низкая температура → рациональный выбор
    Несчастный NPC → высокая температура → хаотичное поведение
    """
    happiness = agent.get_happiness()  # 0-1
    return 0.1 + (1.0 - happiness) * 0.9
```

---

## 9. Практические Рекомендации для Проекта

### 9.1 Архитектурные Решения

| Решение | Рекомендация | Обоснование |
|---------|--------------|-------------|
| Decision Making | Utility AI + BDI | Utility для тактики, BDI для стратегии |
| Memory | Generative Agents style | Episodic + Semantic + Reflection |
| Events | Observer/Pub-Sub | Слабая связанность систем |
| Narrative | Emergent + Story-sifting | Не пиши сюжет, но выделяй интересное |

### 9.2 Чеклист Реалистичности NPC

- [ ] NPC имеет **уникальные traits** (не хардкод)
- [ ] NPC **помнит** прошлые события
- [ ] NPC делает **выводы** из опыта (reflection)
- [ ] NPC имеет **личные цели** (не только реакции)
- [ ] NPC **различает** других NPC (отношения)
- [ ] NPC **адаптируется** к изменениям
- [ ] NPC **автономен** (действует без команд игрока)
- [ ] NPC **непредсказуем** (но объясним post-hoc)

### 9.3 Анти-паттерны (чего избегать)

| Анти-паттерн | Проблема | Решение |
|--------------|----------|---------|
| Хардкод поведения | "NPC #5 всегда идёт в точку А" | Utility AI |
| Глобальные скрипты | "В год 100 начинается война" | Emergent conflicts |
| Одинаковые NPC | "Все крестьяне одинаковы" | Traits + genetics |
| Мгновенное забывание | "NPC не помнит вчерашний день" | Memory system |
| Детерминизм | "Одинаковые условия → одинаковый результат" | Stochasticity |

---

## 10. Источники

### Академические

- [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442) — Stanford, 2023
- [BDI Agents: From Theory to Practice](https://cdn.aaai.org/ICMAS/1995/ICMAS95-042.pdf) — Rao & Georgeff, 1995
- [Agent-based model - Wikipedia](https://en.wikipedia.org/wiki/Agent-based_model)

### Игровые

- [Simulation Principles from Dwarf Fortress](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter41_Simulation_Principles_from_Dwarf_Fortress.pdf) — Game AI Pro 2
- [The Genius AI Behind The Sims](https://gmtk.substack.com/p/the-genius-ai-behind-the-sims) — GMTK
- [How complex AI can promote Emergent Narrative](https://www.joeduffy.games/how-complex-ai-can-promote-emergent-narrative)
- [Dwarf Fortress: The Nexus of Emergent Complexity](https://research.genezi.io/p/dwarf-fortress-the-nexus-of-emergent)

### Технические

- [BDI Agent Architectures: A Survey](https://www.ijcai.org/proceedings/2020/0684.pdf) — IJCAI 2020
- [Utility system - Wikipedia](https://en.wikipedia.org/wiki/Utility_system)
- [Multi-Agent Systems in Gaming](https://smythos.com/developers/agent-development/multi-agent-systems-in-gaming/)

---

*Документ создан по методологии [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)*
