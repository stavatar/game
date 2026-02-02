---
title: Система NPC - Персонажи и Искусственный Интеллект
description: Описание системы персонажей (NPC), модели характеров, BDI-архитектуры, системы памяти, генетики, личности, потребностей и механик принятия решений
keywords:
  - NPC
  - персонажи
  - BDI архитектура
  - память
  - генеративные агенты
  - личность
  - потребности
  - генетика
  - искусственный интеллект
  - автономные агенты
lang: ru
---

# Система NPC - Персонажи и Искусственный Интеллект

## Обзор

Система NPC (модули `npc/` и `npc/ai/`) — это сердце игровой симуляции. Каждый NPC — это уникальный, автономный персонаж с собственной личностью, памятью, потребностями и способностью принимать собственные решения. В отличие от жёстко запрограммированных персонажей, NPC в этой симуляции являются **эмергентными агентами**, поведение которых возникает из взаимодействия базовых систем.

**Ключевые компоненты:**

- **Character** — модель единого NPC с характеристиками, навыками, личностью
- **Genetics** — система наследования черт от родителей
- **Personality** — система черт характера, влияющих на решения
- **Needs** — система потребностей (голод, энергия, общение, цель жизни)
- **Memory System** — поток памяти, рефлексия и социальные сети (вдохновлено Generative Agents)
- **BDI Architecture** — Beliefs (убеждения) → Desires (желания) → Intentions (намерения) → Actions (действия)
- **RelationshipManager** — социальные отношения между NPC

**Философский контекст:**

NPC система базируется на нескольких научных и философских основаниях:

1. **BDI-архитектура (Bratman, 1987)** — классическая модель практического рассуждения: агент воспринимает мир, формирует убеждения, из них рождаются желания, из желаний — намерения (планы), которые исполняются через действия.

2. **Generative Agents (Stanford, 2023)** — революционное исследование, показавшее, что память, социальные сети и рефлексия позволяют виртуальным агентам создавать исторически достоверное социальное поведение. Наша система памяти вдохновлена этой работой.

3. **Agent-Based Modeling** — дисциплина, исследующая как простые локальные взаимодействия между агентами приводят к сложному эмергентному поведению на макроуровне.

---

## 1. Модель Персонажа (Character)

### 1.1. Структура персонажа

Каждый NPC представлен классом `Character` с полным набором атрибутов:

```python
@dataclass
class NPC:
    """Уникальная личность в игровом мире"""

    # Идентификация
    id: str                              # Уникальный ID (первые 8 символов UUID)
    name: str                            # Имя
    surname: str                         # Фамилия
    gender: Gender                       # Пол (MALE / FEMALE)
    age: int                             # Возраст в годах

    # Внешность (генерируется из генов)
    appearance: Dict[str, str]          # {"hair": "чёрные", "eyes": "карие", ...}

    # Характеристики и навыки
    stats: Stats                        # 7 основных характеристик (1-20)
    skills: Skills                      # 10 навыков (0-100)

    # Психология
    personality: Personality            # Черты характера (3+ черты из 28 возможных)
    needs: Needs                        # 8 типов потребностей (0-100)

    # Социальное
    relationships: RelationshipManager  # Отношения со всеми известными NPC
    occupation: Occupation              # Профессия
    wealth: int                         # Деньги

    # Местоположение
    current_location_id: Optional[str]  # Где находится сейчас
    home_location_id: Optional[str]     # Дома (базовое местоположение)
    work_location_id: Optional[str]     # Работает где-то

    # Состояние
    health: float                       # Здоровье (0-100)
    is_alive: bool                      # Жив ли
    is_sleeping: bool                   # Спит ли
    current_activity: str               # Чем занимается сейчас

    # Память и цели
    memories: List[Memory]              # Все воспоминания (50-200+)
    goals: List[Goal]                   # Долгосрочные цели (3-5 обычно)
    life_events: List[str]              # Ключевые события жизни

    # Развитие
    experience: int                     # Общий опыт
    days_lived: int                     # Дней прожил в мире
```

### 1.2. Характеристики (Stats)

Каждый NPC имеет 7 основных характеристик (от 1 до 20 баллов):

| Характеристика | Влияет на | Базовое значение |
|---|---|---|
| **Strength** (Сила) | Боевые навыки, физическая работа | 10 |
| **Agility** (Ловкость) | Скорость, воровство, охота | 10 |
| **Endurance** (Выносливость) | Здоровье, длительная работа | 10 |
| **Intelligence** (Интеллект) | Обучение, магия, ремёсла | 10 |
| **Charisma** (Харизма) | Торговля, лидерство, убеждение | 10 |
| **Perception** (Восприятие) | Скрытые предметы, опасности | 10 |
| **Luck** (Удача) | Критические события, случайность | 10 |

Характеристики наследуются от родителей через гены с возможностью мутации:

```python
# Генетический модификатор (-3 до +3)
strength_modifier = father_gene_strength + mother_gene_strength
npc.stats.strength = 10 + strength_modifier
```

### 1.3. Навыки (Skills)

Каждый NPC может развивать 10 навыков (от 0 до 100):

```python
@dataclass
class Skills:
    combat: int = 0          # Боевые навыки
    crafting: int = 0        # Ремесла
    trading: int = 0         # Торговля
    farming: int = 0         # Земледелие
    cooking: int = 0         # Готовка
    medicine: int = 0        # Лечение
    persuasion: int = 0      # Убеждение
    stealth: int = 0         # Скрытность
    music: int = 0           # Музыка
    knowledge: int = 0       # Знания
```

Навыки развиваются через практику:

```python
# Каждый раз когда NPC рубит дерево
npc.skills.improve("crafting", amount=1)  # +1 к мастерству
```

### 1.4. Профессии (Occupation)

NPC могут иметь одну из 15 профессий:

```python
class Occupation(Enum):
    NONE = "безработный"
    FARMER = "фермер"           # Земледелие, свой участок
    BLACKSMITH = "кузнец"       # Ремесла, торговля
    MERCHANT = "торговец"       # Торговля, путешествия
    GUARD = "стражник"          # Боевые навыки, охрана
    INNKEEPER = "трактирщик"    # Гостеприимство, торговля
    HEALER = "лекарь"           # Медицина
    HUNTER = "охотник"          # Охота
    CRAFTSMAN = "ремесленник"   # Ремесла
    SCHOLAR = "учёный"          # Знания
    PRIEST = "священник"        # Идеология, верования
    BARD = "бард"               # Музыка, развлечение
    BEGGAR = "нищий"            # Низший класс
    NOBLE = "дворянин"          # Высший класс
    SERVANT = "слуга"           # Работает на другого
```

Профессия определяет начальные навыки, доход и социальный статус.

---

## 2. Генетика и Наследование

### 2.1. Система генов (Genetics System)

NPC наследуют черты от родителей через гены. Система поддерживает **менделевскую генетику** с доминантностью и мутациями:

```python
class GeneType(Enum):
    # Физические гены
    HEIGHT = "рост"              # Низкий, средний, высокий
    BUILD = "телосложение"       # Худощавый, обычный, крепкий, массивный
    HAIR_COLOR = "цвет волос"    # От светлых до чёрных
    EYE_COLOR = "цвет глаз"      # От голубых до чёрных
    SKIN_TONE = "тон кожи"

    # Генетические предрасположенности
    STRENGTH_POTENTIAL = "потенциал силы"
    AGILITY_POTENTIAL = "потенциал ловкости"
    INTELLIGENCE_POTENTIAL = "потенциал интеллекта"
    ENDURANCE_POTENTIAL = "потенциал выносливости"

    # Биологические черты
    LONGEVITY = "долголетие"           # Как долго живёт
    FERTILITY = "плодовитость"         # Сколько детей может иметь
    DISEASE_RESISTANCE = "здоровье"

    # Психологические предрасположенности
    TEMPERAMENT = "темперамент"
    INTROVERSION = "интроверсия"
    AGGRESSION = "агрессивность"
    CURIOSITY = "любопытство"
```

### 2.2. Наследование от родителей

Каждый ген имеет два аллеля (от каждого родителя) с доминантностью:

```python
@dataclass
class Gene:
    gene_type: GeneType
    allele1: float          # Аллель от матери (0-1)
    allele2: float          # Аллель от отца (0-1)
    dominance: float = 0.5  # 0=рецессивный, 0.5=кодоминант, 1=доминантный

    def get_expression(self) -> float:
        """Вычисляет выраженное значение"""
        if self.dominance > 0.5:
            return max(self.allele1, self.allele2)  # Доминантный аллель
        elif self.dominance < 0.5:
            return min(self.allele1, self.allele2)  # Рецессивный аллель
        else:
            return (self.allele1 + self.allele2) / 2  # Среднее
```

**Пример наследования:**

```
Отец: Высокий, чёрные волосы, сильный
  genes = {
    HEIGHT: (0.8, 0.8, dominance=0.7),  # Доминантен к высоте
    STRENGTH: (0.75, 0.75, dominance=0.6)
  }

Мать: Средняя, русые волосы, обычная сила
  genes = {
    HEIGHT: (0.5, 0.5, dominance=0.7),
    STRENGTH: (0.5, 0.5, dominance=0.6)
  }

Ребёнок наследует:
  HEIGHT: (0.8 or 0.5, 0.8 or 0.5) = возможно высокий
  STRENGTH: (0.75 or 0.5, 0.75 or 0.5) = выше среднего
```

### 2.3. Мутации

С вероятностью 5% при каждом рождении может произойти мутация:

```python
# Мутация - случайное изменение аллеля на ±0.2
if random.random() < mutation_rate:
    allele1 = max(0, min(1, allele1 + random.uniform(-0.2, 0.2)))
    mutations.append(f"Мутация в гене {gene_type.value}")
```

Мутации могут быть как полезными, так и вредными:
- **Полезная мутация:** ребёнок более выносливый, чем оба родителя
- **Вредная мутация:** слабое здоровье, короткая жизнь

---

## 3. Личность и Потребности

### 3.1. Система личности (Personality)

Личность NPC состоит из **3-5 черт характера** из 28 возможных:

```python
class Trait(Enum):
    # Социальные черты
    EXTROVERT = "экстраверт"           # Любит общество
    INTROVERT = "интроверт"            # Предпочитает одиночество
    FRIENDLY = "дружелюбный"           # Доброжелателен
    HOSTILE = "враждебный"             # Агрессивен
    CHARISMATIC = "харизматичный"      # Привлекает людей

    # Эмоциональные черты
    CHEERFUL = "весёлый"               # Оптимист
    MELANCHOLIC = "меланхоличный"      # Пессимист
    CALM = "спокойный"                 # Сдержан
    HOTHEAD = "вспыльчивый"            # Вспыхивает
    BRAVE = "храбрый"                  # Смел
    COWARD = "трусливый"               # Боязлив

    # Моральные черты
    HONEST = "честный"
    DECEITFUL = "лживый"
    GENEROUS = "щедрый"
    GREEDY = "жадный"
    COMPASSIONATE = "сострадательный"
    CRUEL = "жестокий"

    # И ещё 12 других...
```

**Противоположные черты:** NPC не может одновременно быть экстравертом И интровертом:

```python
OPPOSITE_TRAITS = {
    Trait.EXTROVERT: Trait.INTROVERT,
    Trait.BRAVE: Trait.COWARD,
    Trait.HONEST: Trait.DECEITFUL,
    # ...
}
```

### 3.2. Черты как модификаторы поведения

Личность влияет на:

```python
# Социальное взаимодействие
def get_social_modifier(self) -> float:
    modifier = 1.0
    if self.has_trait(Trait.EXTROVERT):
        modifier += 0.3      # Экстраверты лучше в социуме
    if self.has_trait(Trait.HOSTILE):
        modifier -= 0.3      # Враждебные - хуже
    return max(0.1, modifier)

# Рабочая эффективность
def get_work_modifier(self) -> float:
    modifier = 1.0
    if self.has_trait(Trait.HARDWORKING):
        modifier += 0.3      # Трудолюбивые работают эффективнее
    if self.has_trait(Trait.LAZY):
        modifier -= 0.3      # Ленивые - менее эффективны
    return max(0.1, modifier)

# Смелость в боевых ситуациях
def get_courage_modifier(self) -> float:
    modifier = 1.0
    if self.has_trait(Trait.BRAVE):
        modifier += 0.4      # Храбрые смелее
    if self.has_trait(Trait.COWARD):
        modifier -= 0.4      # Трусливые убегают
    return max(0.1, modifier)
```

### 3.3. Система потребностей (Needs)

Каждый NPC имеет 8 основных потребностей (от 0 до 100):

```python
class Need(Enum):
    HUNGER = "голод"           # Потребность в еде
    ENERGY = "энергия"         # Усталость
    SOCIAL = "общение"         # Потребность в социальном контакте
    FUN = "развлечение"        # Потребность в развлечениях
    COMFORT = "комфорт"        # Потребность в комфортном жилище
    HYGIENE = "гигиена"        # Потребность в чистоте
    SAFETY = "безопасность"    # Потребность в безопасности
    PURPOSE = "цель"           # Потребность в смысле жизни, мечте
```

Каждая потребность имеет:

```python
@dataclass
class NeedState:
    value: float = 100.0        # Уровень удовлетворения (0-100)
    decay_rate: float = 1.0     # Скорость уменьшения за час
    priority_weight: float = 1.0 # Приоритет (важность)

    def is_critical(self) -> bool:
        """Критическое состояние (< 20)"""
        return self.value < 20

    def get_urgency(self) -> float:
        """Срочность (0-1)"""
        return (100 - self.value) / 100 * self.priority_weight
```

**Приоритеты потребностей** (установлены по классической пирамиде Маслоу):

| Потребность | Приоритет | Decay Rate | Когда критична |
|---|---|---|---|
| HUNGER (голод) | 1.5 ⭐⭐⭐ | 3.0 | < 20 = голодаете |
| ENERGY (энергия) | 1.4 ⭐⭐⭐ | 2.5 | < 20 = засыпаете |
| SAFETY (безопасность) | 2.0 ⭐⭐⭐⭐ | 0.5 | < 20 = паника |
| PURPOSE (цель) | 1.2 ⭐⭐ | 0.3 | < 20 = отчаяние |
| SOCIAL (общение) | 1.0 ⭐ | 1.5 | < 20 = одиночество |

**Пример: Как NPC становится голодным**

```
Час 1:  HUNGER = 80 (сыт)
Час 2:  HUNGER -= 3.0 = 77
Час 3:  HUNGER -= 3.0 = 74
...
Час 20: HUNGER = 20 (критически голоден)
Час 21: HUNGER = 17 (срочно нужна еда)

→ BDI система генерирует желание EAT
→ NPC ищет еду или просит у соседей
→ Если находит: HUNGER += 50 (сыт)
```

**Влияние на настроение:**

```python
def get_overall_happiness(self) -> float:
    """Общее счастье на основе удовлетворённости потребностей"""
    total_weighted = sum(
        state.value * state.priority_weight
        for state in self.states.values()
    )
    total_weight = sum(state.priority_weight for state in self.states.values())
    return total_weighted / total_weight

# Результаты:
# 80-100: счастлив
# 60-80:  доволен
# 40-60:  нормально
# 20-40:  недоволен
# 0-20:   несчастен
```

---

## 4. BDI-архитектура (Beliefs-Desires-Intentions)

### 4.1. Обзор BDI цикла

BDI-архитектура — это классическая модель автономного агента, состоящая из 5 этапов:

```
┌─────────────────────────────────────────────────────────┐
│                   BDI ЦИКЛ NPC                          │
└─────────────────────────────────────────────────────────┘

1. ВОСПРИЯТИЕ (Perception)
   ↓ Обновляем убеждения о мире

2. ФОРМИРОВАНИЕ УБЕЖДЕНИЙ (Belief Update)
   ↓ На основе наблюдений и памяти

3. ГЕНЕРИРОВАНИЕ ЖЕЛАНИЙ (Desire Generation)
   ↓ Из потребностей и убеждений

4. ВЫБОР НАМЕРЕНИЙ (Intention Selection)
   ↓ Что-то делаем для удовлетворения желаний

5. ВЫПОЛНЕНИЕ ДЕЙСТВИЙ (Action Execution)
   ↓ Выполняем выбранный план

6. ОБНОВЛЕНИЕ СОСТОЯНИЯ (Feedback)
   ↓ Результат влияет на убеждения

   → Цикл повторяется каждый час симуляции
```

### 4.2. Убеждения (Beliefs)

Убеждение — это единица знания NPC о мире. Каждое убеждение имеет:

```python
@dataclass
class Belief:
    """Убеждение NPC о мире"""
    id: str                     # Уникальный ID
    category: BeliefCategory    # Категория
    subject: str                # О чём верование (тема)
    content: Any                # Содержание (значение)
    confidence: float = 1.0     # Уверенность (0-1)
    timestamp: int = 0          # Когда получено
    source: str = "наблюдение"  # Откуда знание

    def is_stale(self, current_day: int) -> bool:
        """Устарело ли убеждение?"""
        return (current_day - self.timestamp) > 30  # Старше 30 дней

    def decay_confidence(self) -> None:
        """Уверенность уменьшается со временем"""
        self.confidence = max(0, self.confidence - 0.1)
```

**Категории убеждений:**

```python
class BeliefCategory(Enum):
    SELF = "о себе"             # "Я голоден", "Я утомлён"
    WORLD = "о мире"            # "Погода холодная", "Ресурсы редки"
    SOCIAL = "социальные"       # "Иван мне нравится", "Боюсь Грудня"
    ECONOMIC = "экономические"  # "Хлеб дорогой", "Земля мне принадлежит"
    LOCATION = "о местах"       # "В сарае есть зерно", "Монастырь на севере"
    DANGER = "об опасностях"    # "Волки в лесу", "Чума в городе"
    OPPORTUNITY = "о возможностях" # "Можно торговать", "Нужна помощь"
```

**Пример убеждений реального NPC:**

```python
# Фермер Иван (день 15)
beliefs = {
    "weather_cold": Belief(
        id="w1",
        category=BeliefCategory.WORLD,
        subject="погода",
        content="холодная",
        confidence=1.0,      # Только что заметил
        timestamp=15
    ),
    "i_am_hungry": Belief(
        id="self1",
        category=BeliefCategory.SELF,
        subject="голод",
        content=0.3,         # Значение голода (0-1)
        confidence=1.0
    ),
    "ivan_friendly": Belief(
        id="soc1",
        category=BeliefCategory.SOCIAL,
        subject="соосед Иван",
        content="дружелюбный",
        confidence=0.8,      # Давно не виделись, уверенность ниже
        timestamp=2          # 13 дней назад
    ),
    "grain_in_barn": Belief(
        id="loc1",
        category=BeliefCategory.LOCATION,
        subject="зерно",
        content="в сарае",
        confidence=1.0,
        timestamp=14         # Вчера видели
    ),
}
```

### 4.3. Желания (Desires)

Желания возникают из потребностей и убеждений:

```python
@dataclass
class Desire:
    """Желание NPC"""
    desire_type: DesireType     # Тип желания (из пирамиды Маслоу)
    intensity: float = 0.5      # Интенсивность (0-1)
    target: Optional[str] = None # Конкретная цель (ID объекта/NPC)
    conditions_met: bool = False # Можно ли удовлетворить сейчас?
    blocked_by: List[str] = field(default_factory=list)  # Что мешает

    def get_priority(self) -> float:
        """Приоритет = базовый приоритет × интенсивность"""
        return self.desire_type.base_priority * self.intensity

    def is_urgent(self) -> bool:
        """Срочное ли желание?"""
        return self.intensity > 0.8 and self.desire_type.base_priority > 0.7
```

**Типы желаний** (пирамида Маслоу):

```python
class DesireType(Enum):
    # Физиологические (базовые)
    EAT = ("поесть", 0.9)                  # Приоритет 0.9
    SLEEP = ("поспать", 0.85)
    SURVIVE = ("выжить", 1.0)

    # Безопасность
    SAFETY = ("быть в безопасности", 0.7)
    HEALTH = ("быть здоровым", 0.7)

    # Социальные
    BELONG = ("принадлежать группе", 0.5)
    FRIENDSHIP = ("иметь друзей", 0.45)
    FAMILY = ("иметь семью", 0.5)

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

**Пример: Как возникает желание EAT**

```python
# Потребность HUNGER = 15 (критическая)
hunger_urgency = (100 - 15) / 100 * 1.5 = 1.275

# → Генерируется желание
desire = Desire(
    desire_type=DesireType.EAT,
    intensity=1.0,                      # Максимальное
    target=None,                        # Ещё не знаем где еда
    conditions_met=False,               # Нет еды под рукой
)

# Приоритет желания
priority = 0.9 * 1.0 = 0.9  # Очень высокий приоритет!

# NPC: "Я должен поесть немедленно!"
```

### 4.4. Намерения (Intentions)

Намерение — это выбранный план действий для удовлетворения желания:

```python
@dataclass
class Intention:
    """Намерение - выбранный план действий"""
    id: str
    source_desire: DesireType        # Какое желание удовлетворяет
    actions: List[Action]            # Последовательность действий
    current_action_index: int = 0    # Какое действие выполняем
    priority: float = 0.5

    def get_current_action(self) -> Optional[Action]:
        """Получить текущее действие"""
        if self.current_action_index < len(self.actions):
            return self.actions[self.current_action_index]
        return None

    def advance(self) -> bool:
        """Перейти к следующему действию. Возвращает True если план завершён."""
        self.current_action_index += 1
        return self.current_action_index >= len(self.actions)
```

**Пример: План для удовлетворения голода**

```python
# NPC голоден, знает что зерно в сарае
intention = Intention(
    id="int_eat_001",
    source_desire=DesireType.EAT,
    actions=[
        Action(
            action_type=ActionType.MOVE,
            location_id="barn_1",
            duration=0.5,
            priority=1.0
        ),
        Action(
            action_type=ActionType.GATHER,
            target_id="grain_pile",
            duration=1.0,
            priority=1.0,
            energy_cost=20
        ),
        Action(
            action_type=ActionType.EAT,
            target_id="grain",
            duration=0.5,
            priority=1.0,
            expected_reward={"hunger": 50}
        ),
    ],
    priority=0.9  # Очень приоритетный план
)

# Выполнение плана:
# Час 1: MOVE to barn → успешно
# Час 2: GATHER grain → +30 зерна в инвентаре
# Час 3: EAT → HUNGER = 65 (удовлетворён)
```

### 4.5. Действия (Actions)

```python
@dataclass
class Action:
    """Конкретное действие"""
    action_type: ActionType           # Тип действия
    target_id: Optional[str] = None   # На что направлено
    location_id: Optional[str] = None # Где выполнять
    duration: float = 1.0            # Часов на выполнение
    priority: float = 0.5            # Приоритет
    success_chance: float = 0.8      # Вероятность успеха
    energy_cost: float = 10.0        # Энергия
    expected_reward: Dict = field(default_factory=dict)

class ActionType(Enum):
    # Базовые
    IDLE = "бездействовать"
    MOVE = "перемещаться"
    REST = "отдыхать"
    SLEEP = "спать"

    # Добыча ресурсов
    GATHER = "собирать"
    HUNT = "охотиться"
    FARM = "обрабатывать землю"

    # Производство
    CRAFT = "мастерить"
    COOK = "готовить"

    # Социальное
    TALK = "разговаривать"
    TRADE = "торговать"
    HELP = "помогать"

    # Потребление
    EAT = "есть"
    DRINK = "пить"
```

### 4.6. Практический пример BDI цикла

```
========== ДЕНЬ 15, ЧАС 3 ==========
NPC: Фермер Иван (40 лет, трудолюбивый)

ШАГ 1: ВОСПРИЯТИЕ
├─ Наблюдает окружение
├─ Видит сарай, товарищей, еду
└─ Обновляет убеждения о мире

ШАГ 2: УБЕЖДЕНИЯ
├─ HUNGER = 25 (начинает голодать)
├─ ENERGY = 60 (устал от работы)
├─ в памяти: "зерно в сарае" (confidence=1.0)
└─ в памяти: "Петр добрый парень" (confidence=0.9)

ШАГ 3: ЖЕЛАНИЯ (по приоритету)
1. EAT (priority=0.9) ← САМОЕ СРОЧНОЕ!
2. SLEEP (priority=0.85)
3. SOCIAL (priority=0.45)
4. MASTERY (priority=0.3) ← может подождать

ШАГ 4: НАМЕРЕНИЯ
Выбирает план для EAT:
├─ Вариант 1: "Пойти в сарай и взять зерна"
├─ Вариант 2: "Попросить еду у Петра"
└─ Выбирает вариант 1 (ближе, быстрее)

ШАГ 5: ДЕЙСТВИЯ
├─ Текущее действие: MOVE к сараю (1 час)
├─ Следующее действие: GATHER зерно (1 час)
└─ Затем: COOK и EAT (1 час)

========== ДЕНЬ 15, ЧАС 4 ==========
✓ Добрался до сарая
✓ Собрал 30 единиц зерна
│ ENERGY -= 20
│ HUNGER -= 10 (работал, голодней стал)

========== ДЕНЬ 15, ЧАС 5 ==========
✓ Приготовил кашу
✓ Поел кашу
│ HUNGER = 60 ✓ (удовлетворён)
│ HAPPINESS = 70 (доволен)

════════════════════════════════════

РЕЗУЛЬТАТ:
✓ Голод удовлетворён через BDI рассуждение
✓ Личность (трудолюбивый) ускорила работу
✓ Память (знание о сарае) помогла быстро решить
✓ Потребности естественно влияют на поведение
```

---

## 5. Система Памяти (Memory System)

### 5.1. Вдохновение из "Generative Agents"

Система памяти вдохновлена революционным исследованием Stanford "Generative Agents: Interactive Simulacra of Human Behavior" (2023). Исследование показало, что виртуальные персонажи с хорошей памятью создают исторически достоверное поведение и социальные динамики, близкие к реальным.

**Ключевые идеи:**
1. **Поток памяти** — все события хранятся в хронологическом порядке
2. **Иерархия значимости** — важные события помнят лучше
3. **Рефлексия** — периодически анализируют свои воспоминания и делают выводы
4. **Забывание** — неважные события забываются
5. **Социальная интеграция** — памяти других NPC влияют на выводы

### 5.2. Типы памяти (MemoryEntry)

```python
class MemoryType(Enum):
    """Типы воспоминаний"""
    OBSERVATION = "наблюдение"      # "Видел Ивана в городе"
    ACTION = "действие"              # "Я рубил дрова"
    CONVERSATION = "разговор"        # "Петр сказал что..."
    EMOTION = "эмоция"               # "Чувствовал радость"
    REFLECTION = "размышление"       # "Вывод: он хороший человек"
    PLAN = "план"                    # "Хочу стать кузнецом"
    RELATIONSHIP = "отношение"       # "Ссорились с Иваном"
    ECONOMIC = "экономическое"       # "Хлеб дорогой"
    TRAUMA = "травма"                # "Был ранен волком"
    JOY = "радость"                  # "Родился сын!"

class EmotionalValence(Enum):
    """Эмоциональная окраска"""
    VERY_NEGATIVE = -2  # Ужас, боль
    NEGATIVE = -1       # Грусть, разочарование
    NEUTRAL = 0         # Нейтрально
    POSITIVE = 1        # Радость, удовлетворение
    VERY_POSITIVE = 2   # Счастье, экстаз
```

### 5.3. Структура памяти

```python
@dataclass
class MemoryEntry:
    """Единица памяти"""
    id: str
    memory_type: MemoryType
    description: str                 # Описание события

    # Время события
    year: int
    month: int
    day: int
    hour: int

    # Значимость и эмоции
    importance: float                # 0-1, насколько важно
    emotional_valence: EmotionalValence  # Позитивное/негативное?
    emotional_intensity: float       # 0-1, сила эмоции

    # Связи (что связано с этой памятью?)
    related_npc_ids: List[str]      # С какими NPC связано
    related_location_id: Optional[str]  # Где произошло
    related_objects: List[str]      # Какие предметы

    # Метаданные
    access_count: int = 0            # Сколько раз вспоминали
    last_accessed: int = 0           # Когда последний раз

    # Для рефлексий
    based_on_memories: List[str] = field(default_factory=list)

    def get_recency_score(self, current_day: int) -> float:
        """Свежесть воспоминания (свежие помнятся лучше)"""
        days_ago = current_day - (self.year * 360 + self.month * 30 + self.day)
        decay_rate = 0.995
        return pow(decay_rate, days_ago)  # Экспоненциальное затухание

    def get_relevance_score(self, query_npcs: List[str] = None,
                           query_location: str = None) -> float:
        """Релевантность к поиску"""
        score = 0.0
        if query_npcs:
            overlap = len(set(query_npcs) & set(self.related_npc_ids))
            score += overlap * 0.3
        if query_location and self.related_location_id == query_location:
            score += 0.2
        return score

    def get_retrieval_score(self, current_day: int,
                           query_npcs: List[str] = None) -> float:
        """Общая оценка для извлечения из памяти"""
        # Комбинирует: важность (50%) + свежесть (30%) + релевантность (20%)
        return (self.importance * 0.5 +
                self.get_recency_score(current_day) * 0.3 +
                self.get_relevance_score(query_npcs) * 0.2)
```

### 5.4. Поток памяти (MemoryStream)

```python
class MemoryStream:
    """Поток памяти одного NPC"""

    def __init__(self, owner_id: str, max_memories: int = 200):
        self.owner_id = owner_id
        self.max_memories = max_memories  # Максимум воспоминаний

        # Хранилище
        self.memories: Dict[str, MemoryEntry] = {}
        self.reflections: Dict[str, Reflection] = {}

        # Индексы для быстрого поиска
        self._by_npc: Dict[str, Set[str]] = {}      # npc_id → memory_ids
        self._by_location: Dict[str, Set[str]] = {} # location_id → memory_ids
        self._by_type: Dict[MemoryType, Set[str]] = {}

        # Порог рефлексии
        self.reflection_threshold = 10  # Рефлексия каждые 10 воспоминаний

    def add_memory(self, memory_type: MemoryType,
                   description: str, ...):
        """Добавить воспоминание"""
        memory = MemoryEntry(
            id=f"mem_{self._memory_counter}",
            memory_type=memory_type,
            description=description,
            ...
        )
        self.memories[memory.id] = memory

        # Индексирование
        self._by_npc[related_npc].add(memory.id)
        # Может быть нужна рефлексия
        self._check_reflection_needed()

        # Забывание: если памяти больше чем max
        if len(self.memories) > self.max_memories:
            self._forget_least_important()

    def retrieve_memories(self,
                         query_npcs: List[str] = None,
                         query_location: str = None,
                         limit: int = 5) -> List[MemoryEntry]:
        """Извлечь релевантные воспоминания"""
        scores = {}
        for mem_id, memory in self.memories.items():
            score = memory.get_retrieval_score(
                self.current_day,
                query_npcs
            )
            scores[mem_id] = score

        # Вернуть топ-N
        top_memories = sorted(scores.items(),
                            key=lambda x: x[1],
                            reverse=True)[:limit]

        return [self.memories[mem_id] for mem_id, _ in top_memories]
```

### 5.5. Рефлексия (Reflection)

Периодически NPC размышляет над своими воспоминаниями и делает выводы:

```python
@dataclass
class Reflection:
    """Вывод из воспоминаний"""
    id: str
    conclusion: str                  # Сам вывод: "Иван - хороший человек"
    confidence: float = 0.5          # Уверенность (0-1)

    # На чём основан вывод
    supporting_memories: List[str]   # Какие память подтверждают
    evidence_count: int = 0          # Сколько примеров

    # Контекст
    about_npc: Optional[str] = None  # Если вывод о конкретном NPC
    about_world: bool = False        # Если вывод о мире
    about_self: bool = False         # Если вывод о себе

    # Когда сделан
    year: int = 0
    day: int = 0

    # Стабильность
    is_core_belief: bool = False     # Ключевые убеждения меняются сложнее

def create_reflection(self, query_npcs: List[str] = None) -> Reflection:
    """Создать рефлексию из воспоминаний"""

    # Получить последние воспоминания
    recent_memories = self.retrieve_memories(
        query_npcs=query_npcs,
        limit=10
    )

    # Анализ: если часто вместе с Иваном что-то позитивное
    if len([m for m in recent_memories
           if "Иван" in m.description and
              m.emotional_valence in [1, 2]]) >= 3:

        reflection = Reflection(
            id=f"refl_{self._reflection_counter}",
            conclusion="Иван - хороший человек, можно ему доверять",
            confidence=0.8,
            supporting_memories=[m.id for m in recent_memories],
            evidence_count=3,
            about_npc="иван_id",
            about_world=False,
            is_core_belief=True  # Это важное убеждение
        )

        self.reflections[reflection.id] = reflection
        return reflection

# Пример: Результаты рефлексии NPC
reflections = {
    "refl_001": {
        "conclusion": "Иван добрый и помогает мне",
        "confidence": 0.9,
        "evidence_count": 5,
        "is_core_belief": True
    },
    "refl_002": {
        "conclusion": "Зимой еды мало, нужно запасать осенью",
        "confidence": 0.7,
        "evidence_count": 2,
        "is_core_belief": True
    },
    "refl_003": {
        "conclusion": "Землевладельцы берут слишком много урожая",
        "confidence": 0.6,
        "evidence_count": 3,
        "about_world": True
    },
}
```

### 5.6. Забывание

NPC забывает неважные события:

```python
def _forget_least_important(self):
    """Забыть наименее важное воспоминание"""
    if len(self.memories) <= self.max_memories:
        return

    # Найти наименее важное
    least_important = min(
        self.memories.values(),
        key=lambda m: (
            m.importance * 0.5 +        # Важность
            m.get_recency_score() * 0.3 +  # Свежесть
            m.access_count * 0.2        # Часто ли вспоминают
        )
    )

    # Удалить из памяти
    del self.memories[least_important.id]
    print(f"NPC забыл: {least_important.description}")

# Пример забывания:
# День 1: Видел птицу (importance=0.1) → быстро забудет
# День 1: Родился ребёнок (importance=0.95) → помнит всегда
# День 50: "Видел Ивана в сарае" (старое, неважное) → забыл
```

---

## 6. Отношения между NPC

### 6.1. Система отношений

```python
@dataclass
class Relationship:
    """Отношения между двумя NPC"""
    target_id: str

    # Основные показатели (-100 до 100)
    friendship: float = 0.0     # Дружба
    romance: float = 0.0        # Романтика
    respect: float = 0.0        # Уважение
    trust: float = 0.0          # Доверие

    # История
    interactions_count: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0

    # Воспоминания об этом NPC
    memories: List[str] = field(default_factory=list)

    # Тип отношений
    relationship_type: RelationType = RelationType.STRANGER

    def get_overall_opinion(self) -> float:
        """Общее мнение о персонаже"""
        return (
            self.friendship * 0.4 +
            self.respect * 0.3 +
            self.trust * 0.3
        )

class RelationType(Enum):
    """Типы отношений"""
    STRANGER = "незнакомец"
    ACQUAINTANCE = "знакомый"
    FRIEND = "друг"
    CLOSE_FRIEND = "близкий друг"
    BEST_FRIEND = "лучший друг"
    ROMANTIC = "романтические"
    PARTNER = "партнёр"
    SPOUSE = "супруг"
    RIVAL = "соперник"
    ENEMY = "враг"
    FAMILY = "семья"
    COLLEAGUE = "коллега"
    MENTOR = "наставник"
    STUDENT = "ученик"
```

**Пример эволюции отношений:**

```
День 1: Петр встретил Ивана
├─ relationship_type = STRANGER
├─ friendship = 0
└─ interactions_count = 1

День 5: Иван помог Петру (помощь)
├─ Positive interaction
├─ friendship += 20
├─ trust += 10
└─ relationship_type = ACQUAINTANCE

День 20: Вместе работали много раз
├─ 5 positive interactions
├─ friendship = 60
├─ respect = 50
├─ trust = 40
└─ relationship_type = FRIEND

День 100: Очень много времени вместе
├─ 40+ positive interactions
├─ friendship = 85
├─ trust = 80
├─ respect = 75
└─ relationship_type = BEST_FRIEND
```

---

## 7. Жизненный Цикл NPC

### 7.1. Этапы жизни

```python
class LifeStage(Enum):
    INFANT = "младенец"         # 0-2 года
    CHILD = "ребёнок"           # 3-12 лет
    ADOLESCENT = "подросток"    # 13-17 лет
    ADULT = "взрослый"          # 18-50 лет
    ELDER = "старец"            # 50+ лет
```

### 7.2. Рождение NPC

```python
# Родители создают ребёнка
def create_child(mother: NPC, father: NPC) -> NPC:
    """Родить нового NPC"""

    # Имя (комбинация родительских фамилий)
    surname = mother.surname if random.random() < 0.5 else father.surname
    name = random.choice(BABY_NAMES)

    # Геном от родителей
    genome = genetics_system.create_genome(
        npc_id=new_id,
        mother_id=mother.id,
        father_id=father.id
    )

    # Характеристики из генов
    stats = Stats(
        strength=10 + genome.get_stat_modifiers()["strength"],
        intelligence=10 + genome.get_stat_modifiers()["intelligence"],
        # ...
    )

    # Личность (иногда наследует от родителей)
    personality = Personality()
    if random.random() < 0.3:  # 30% шанс
        personality.traits = mother.personality.traits  # Наследует от матери

    # Создаём нового NPC
    child = NPC(
        id=new_id,
        name=name,
        surname=surname,
        age=0,
        gender=Gender.MALE if random.random() < 0.5 else Gender.FEMALE,
        stats=stats,
        personality=personality,
        # ...
    )

    return child
```

### 7.3. Взросление

```python
def age_one_year(self):
    """NPC стареет на 1 год"""
    self.age += 1
    self.days_lived += 360

    # Развитие характеристик в детстве
    if self.age < 18:
        # Дети развиваются быстрее
        for stat_name in ["intelligence", "agility", "endurance"]:
            stat = getattr(self.stats, stat_name)
            setattr(self.stats, stat_name, min(20, stat + random.randint(0, 2)))

    # Модификатор смертности с возрастом
    if self.age > 60:
        self.death_risk += 0.02  # Повышается риск смерти

    # Жизненный этап
    self.life_stage = self.get_life_stage()
```

### 7.4. Смерть

```python
class DeathCause(Enum):
    STARVATION = "голод"
    DISEASE = "болезнь"
    VIOLENCE = "насилие"
    AGE = "старость"
    ACCIDENT = "несчастный случай"
    UNKNOWN = "неизвестно"

def kill_npc(self, cause: DeathCause = DeathCause.UNKNOWN):
    """Убить NPC"""
    self.is_alive = False
    self.death_cause = cause
    self.death_day = current_day

    # Запись в память другим NPC
    for npc_id, relationship in self.relationships.relationships.items():
        other_npc = world.get_npc(npc_id)
        if other_npc and other_npc.is_alive:
            # Добавить воспоминание о смерти
            other_npc.memory_stream.add_memory(
                memory_type=MemoryType.EMOTION,
                description=f"{self.full_name()} умер",
                importance=0.8,
                emotional_valence=EmotionalValence.NEGATIVE,
                emotional_intensity=0.7 if relationship.get_overall_opinion() > 0 else 0.3
            )

    print(f"{self.full_name()} умер от {cause.value} на {self.age}-м году жизни")
```

---

## 8. Текущее Состояние Системы

### 8.1. Что работает

✅ **Полностью реализовано:**

1. **Модель персонажа** — все базовые атрибуты, характеристики, навыки
2. **Генетика** — наследование от родителей, мутации, физические черты
3. **Личность** — 28 черт характера, противоположные пары, модификаторы
4. **Потребности** — 8 типов потребностей с приоритетами и распадом
5. **BDI-цикл** — полная реализация убеждений, желаний, намерений, действий
6. **Поток памяти** — добавление, индексирование, простой поиск
7. **Отношения** — типы отношений, показатели дружбы/романтики/уважения/доверия
8. **Жизненный цикл** — рождение, взросление, старение, смерть

### 8.2. Ограничения и Проблемы

⚠️ **Текущие ограничения:**

1. **Недостаточная рефлексия** — рефлексия работает, но недостаточно глубокая
   - Нет сложного анализа закономерностей
   - Нет противоречий между убеждениями
   - Нет изменения убеждений на основе опыта

2. **Персистентность намерений** (EPIC-AI-001)
   - Намерения не сохраняются между днями
   - NPC забывает что делал вчера и начинает с нуля
   - Нет долгосрочного планирования

3. **Средства-целевое рассуждение (GOAP)** (EPIC-AI-005)
   - Нет генерирования планов через средства и цели
   - Нет поиска альтернативных путей если первый не работает
   - Планы жёсткие, не адаптируются

4. **Социальная интеграция памяти** (EPIC-AI-012)
   - Нет влияния памяти других NPC на выводы
   - Нет слухов, сплетен, коллективных убеждений
   - Нет изменения убеждений через общение

5. **Ограниченное количество воспоминаний**
   - Максимум 200 воспоминаний, потом забывают
   - Нет сжатия информации (summarization)
   - Нет долгосрочных выводов из опыта

6. **Конфликты убеждений**
   - Нет механики для разрешения противоречивых убеждений
   - NPC может верить в противоположное одновременно
   - Нет переживания когнитивного диссонанса

---

## 9. Планируемые Улучшения (Task 002)

### 9.1. EPIC-AI (Tier 5): 36 проблем

**Фаза 1: Базовые улучшения (недели 1-4)**

- **AI-001: Персистентность намерений** — сохранять планы между днями
- **AI-002: Долгосрочное планирование** — планировать на неделю/месяц вперёд
- **AI-003: Адаптивное планирование** — менять планы если условия изменились
- **AI-004: Приоритизация действий** — выбирать срочные задачи

**Фаза 2: Продвинутое рассуждение (недели 5-8)**

- **AI-005: GOAP интеграция** — Goal-Oriented Action Planning
- **AI-006: Средства-целевое рассуждение** — искать пути достижения целей
- **AI-007: Альтернативные планы** — если A не работает, пробуем B и C
- **AI-008: Обучение из опыта** — планы становятся лучше со временем

**Фаза 3: Социальный интеллект (недели 9-12)**

- **AI-012: Социальная интеграция** — включать память других в выводы
- **AI-013: Слухи и сплетни** — информация распространяется через общение
- **AI-014: Коллективные убеждения** — общее мнение влияет на личное
- **AI-015: Лидерство и влияние** — харизматичные NPC убеждают других

**Фаза 4: Глубокая рефлексия (недели 13-16)**

- **AI-020: Анализ закономерностей** — "каждую зиму еды мало"
- **AI-021: Теоретизирование** — "землевладельцы эксплуатируют нас"
- **AI-022: Моральные выводы** — "это несправедливо"
- **AI-023: Изменение убеждений** — убеждения меняются при доказательствах

**Фаза 5: Персонализация (недели 17-20)**

- **AI-030: Личные цели** — каждый NPC имеет уникальные амбиции
- **AI-031: Карьерные пути** — развитие в определённом направлении
- **AI-032: Творчество** — NPC создают новое (музыка, искусство, идеи)
- **AI-033: Философия** — NPC размышляют о смысле жизни

### 9.2. Интеграция с другими системами

**EPIC-ECONOMY + AI:**
- Экономическое рассуждение: "работаю за мизерную зарплату"
- Классовое сознание: "земельные собственники как класс эксплуатируют"
- Революционные идеи: "нужна коллективная собственность"

**EPIC-SUPERSTRUCTURE + AI:**
- Идеологическое влияние: верования определяют поведение
- Противодействие: рабочие верят в равенство, хозяева — в иерархию
- Гегемония: господствующий класс контролирует идеи

**EPIC-SOCIAL + AI:**
- Семейные узы: семейные воспоминания очень важны
- Демографические процессы: хотят ли NPC иметь детей?
- Классовое воспроизводство: дети наследуют класс и убеждения

---

## 10. Примеры Использования

### 10.1. Создание NPC

```python
# Создание свежего персонажа
npc = NPC(
    name="Иван",
    surname="Петров",
    gender=Gender.MALE,
    age=25,
    occupation=Occupation.FARMER
)

# Генерируются случайно:
# - Внешность из генов
# - Характеристики (8-12 за счёт генов)
# - Личность (3-4 черты)
# - Потребности (начальные значения)
# - Отношения (пустые)
# - Память (пустая)
# - Цели (генерируются)

print(npc.full_name())  # "Иван Петров"
print(npc.personality.describe())  # "храбрый, честный, трудолюбивый"
print(npc.appearance)  # {'hair': 'чёрные', 'eyes': 'карие', 'height': 'средний', 'build': 'крепкий'}
```

### 10.2. BDI цикл в действии

```python
# Каждый час симуляции
def npc_update_hour(npc):
    """Обновить NPC на один час"""

    # 1. Уменьшаем потребности
    npc.needs.decay_all(hours=1.0)

    # 2. BDI цикл
    # ВОСПРИЯТИЕ: обновляем убеждения
    current_beliefs = npc.bdi.update_beliefs(
        observations=npc.observe_surroundings()
    )

    # ЖЕЛАНИЯ: генерируем из потребностей
    desires = npc.bdi.generate_desires(npc.needs, npc.goals)

    # НАМЕРЕНИЯ: выбираем лучший план
    intention = npc.bdi.select_intention(desires)

    # ДЕЙСТВИЕ: выполняем текущее действие
    if intention:
        action = intention.get_current_action()
        result = npc.execute_action(action)

        # Обновляем память
        if result.significant:
            npc.memory_stream.add_memory(
                memory_type=MemoryType.ACTION,
                description=f"Выполнил {action.describe()}",
                importance=0.6
            )

        # Переходим к следующему действию
        if result.complete:
            intention.advance()

    # 3. Проверяем рефлексию
    npc.memory_stream.check_and_create_reflections()
```

### 10.3. Взаимодействие между NPC

```python
# Два NPC встречаются
def npcs_interact(npc1, npc2):
    """Взаимодействие между двумя NPC"""

    # Они видят друг друга
    if not npc1.knows(npc2.id):
        # Первая встреча
        npc1.meet_npc(npc2)
        relationship = Relationship(target_id=npc2.id)
        npc1.relationships.relationships[npc2.id] = relationship

    # Получают информацию друг о друге из памяти
    npc1_opinion = npc1.relationships.get_opinion(npc2.id)

    # Общаются
    npc1_personality_modifier = npc1.personality.get_social_modifier()
    conversation_success = npc1_personality_modifier * (npc1_opinion / 100)

    if conversation_success > 0.5:
        # Успешный разговор
        npc1.memory_stream.add_memory(
            memory_type=MemoryType.CONVERSATION,
            description=f"Говорил с {npc2.full_name()}, было приятно",
            related_npc_ids=[npc2.id],
            emotional_valence=EmotionalValence.POSITIVE,
            importance=0.5
        )

        # Улучшаем отношения
        npc1.relationships.modify_relationship(
            npc2.id,
            friendship=5,
            trust=3
        )
    else:
        # Неудачный разговор
        npc1.memory_stream.add_memory(
            memory_type=MemoryType.CONVERSATION,
            description=f"Ссорились с {npc2.full_name()}",
            related_npc_ids=[npc2.id],
            emotional_valence=EmotionalValence.NEGATIVE,
            importance=0.4
        )

        # Портим отношения
        npc1.relationships.modify_relationship(
            npc2.id,
            friendship=-5,
            trust=-3
        )
```

---

## 11. Интеграция с другими Системами

### 11.1. Связь с Экономической Системой

```
ECONOMY → NPC поведение → ECONOMY

Экономика влияет на NPC:
├─ Профессия определяет работу
├─ Доход определяет богатство
├─ Доступные ресурсы определяют потребления
└─ Класс (владелец/рабочий) определяет отношения

NPC влияет на экономику:
├─ Рабочие производят
├─ Торговцы обмениваются
├─ Изобретатели создают технологии
└─ Люди размножаются → население → спрос
```

### 11.2. Связь с Культурной Системой

```
CULTURE → NPC убеждения → NPC поведение

Верования влияют на NPC:
├─ "Труд облагораживает" → работают усерднее
├─ "Собственность священна" → защищают имущество
├─ "Все равны" → мятежные настроения
└─ "Боги решают" → смирение, покорность

NPC мышление влияет на культуру:
├─ Взрослые передают верования детям
├─ Лидеры распространяют идеи
├─ Революционеры создают новые верования
└─ Коллективные убеждения → новые верования системы
```

---

## 12. Заключение

Система NPC в этой симуляции — это сложный симбиоз искусственного интеллекта, психологии и марксистской экономики:

1. **Каждый персонаж уникален** — своя генетика, личность, память, убеждения
2. **Поведение эмергентно** — не жёстко запрограммировано, а возникает из BDI рассуждения
3. **Память определяет поведение** — как люди в реальности, NPC действуют на основе опыта
4. **Социальная интеграция** — отношения, общение, слухи, коллективные убеждения
5. **Класс определяет сознание** — экономическое положение влияет на мышление и поведение

Система памяти вдохновлена исследованиями Stanford и показывает как хорошо спроектированная память может создать убедительное и достоверное социальное поведение виртуальных персонажей.

---

## Ссылки на Связанные Документы

- [1_INTRODUCTION.md](./1_INTRODUCTION.md) — Философия проекта
- [2_ARCHITECTURE_OVERVIEW.md](./2_ARCHITECTURE_OVERVIEW.md) — Архитектура системы
- [3_SIMULATION_CORE.md](./3_SIMULATION_CORE.md) — Основной цикл симуляции
- [4_ECONOMIC_SYSTEM.md](./4_ECONOMIC_SYSTEM.md) — Экономическая система
- [5_SOCIETY_SYSTEM.md](./5_SOCIETY_SYSTEM.md) — Общество и классы
- [6_CULTURE_SYSTEM.md](./6_CULTURE_SYSTEM.md) — Культура и верования
- [8_WORLD_ENVIRONMENT.md](./8_WORLD_ENVIRONMENT.md) — Мир и климат
- [DOCUMENTATION_ROADMAP.md](./DOCUMENTATION_ROADMAP.md) — Карта документации

---

**Документ создан:** 2026-02-02
**Язык:** Русский
**Статус:** Завершён
**Последнее обновление:** 2026-02-02 22:30 UTC

