# Epics and User Stories

## Базис и Надстройка - Симулятор Развития Общества

**Версия:** 1.0
**Дата:** 2026-01-31
**Статус:** Актуален
**Автор:** Scrum Master Agent (BMAD Method)

---

## Обзор

Данный документ содержит эпики и пользовательские истории, организованные по функциональным областям проекта. Истории следуют формату Given/When/Then (Gherkin) для acceptance criteria.

---

## Epic #1.0: Ядро Симуляции (Core Simulation)

**Описание:** Базовая инфраструктура для запуска и управления симуляцией.

**Статус:** Done

### US-1.1: Конфигурация Симуляции

**ID:** US-1.1
**Приоритет:** P0
**Статус:** Done
**Story Points:** 3

**Описание:**
Как разработчик, я хочу иметь централизованную конфигурацию, чтобы легко настраивать параметры симуляции.

**Acceptance Criteria:**

```gherkin
Given система инициализирована
When я создаю SimulationConfig с параметрами
Then все параметры (world_size, population, rates) доступны глобально

Given конфигурация загружена
When я использую пресет REALISTIC/ACCELERATED/SANDBOX
Then параметры автоматически настраиваются под пресет

Given невалидные параметры (population < 0)
When я пытаюсь создать конфигурацию
Then выбрасывается ValidationError
```

**Tasks:**
- [x] Создать dataclass SimulationConfig
- [x] Реализовать валидацию параметров
- [x] Добавить три пресета
- [x] Написать unit tests

**Files:** `src/core/config.py`

---

### US-1.2: Система Событий

**ID:** US-1.2
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как разработчик, я хочу pub/sub систему событий, чтобы компоненты могли взаимодействовать слабосвязанно.

**Acceptance Criteria:**

```gherkin
Given EventBus инициализирован
When компонент подписывается на EventType.NPC_BORN
Then handler вызывается при публикации этого события

Given несколько подписчиков на событие
When событие публикуется
Then все подписчики получают уведомление

Given событие имеет EventImportance.HISTORIC
When оно логируется
Then оно сохраняется в истории мира
```

**Tasks:**
- [x] Создать Enum EventType (60+ типов)
- [x] Создать Enum EventImportance
- [x] Реализовать EventBus с subscribe/publish
- [x] Добавить логирование важных событий
- [x] Написать integration tests

**Files:** `src/core/events.py`

---

### US-1.3: Главный Цикл Симуляции

**ID:** US-1.3
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как пользователь, я хочу, чтобы симуляция обновлялась каждый час игрового времени, следуя марксистскому порядку (базис → надстройка).

**Acceptance Criteria:**

```gherkin
Given симуляция запущена
When вызывается update()
Then подсистемы обновляются в порядке: Time → Economy → Society → Culture → NPC

Given прошёл 1 час
When обновляется экономика
Then все производства продвигаются на 1 час

Given NPC голоден (hunger < 0.2)
When обновляются NPC
Then NPC приоритетно ищет еду
```

**Tasks:**
- [x] Создать класс Simulation
- [x] Реализовать update() с правильным порядком
- [x] Интегрировать все подсистемы
- [x] Добавить NPCState для отслеживания состояния
- [x] Написать integration tests

**Files:** `src/core/simulation.py`

---

## Epic #2.0: Мир и Окружение (World & Environment)

**Описание:** Физический мир, карта, климат и время.

**Статус:** Done

### US-2.1: Карта Мира

**ID:** US-2.1
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как система, я хочу иметь сетку мира, чтобы размещать локации и отслеживать позиции NPC.

**Acceptance Criteria:**

```gherkin
Given карта 40x40
When я запрашиваю ячейку (10, 15)
Then получаю MapCell с terrain, resources, npcs

Given NPC в позиции (5, 5)
When он перемещается в (5, 6)
Then его позиция обновляется и он виден в новой локации

Given локация типа FOREST
When NPC собирает ресурсы
Then доступны WOOD и FOOD (ягоды)
```

**Tasks:**
- [x] Создать WorldMap с сеткой
- [x] Реализовать MapCell с terrain
- [x] Добавить методы get_neighbors, find_path
- [x] Реализовать перемещение NPC
- [x] Написать tests

**Files:** `src/world/map.py`, `src/world/location.py`

---

### US-2.2: Система Времени

**ID:** US-2.2
**Приоритет:** P0
**Статус:** Done
**Story Points:** 3

**Описание:**
Как система, я хочу отслеживать время (часы, дни, месяцы, годы), чтобы управлять циклами симуляции.

**Acceptance Criteria:**

```gherkin
Given время 23:00 дня 1
When проходит 2 часа
Then становится 01:00 дня 2

Given месяц 12, день 30
When проходит 1 день
Then месяц становится 1, год увеличивается

Given время 12:00
When запрашивается TimeOfDay
Then возвращается DAY
```

**Tasks:**
- [x] Создать TimeSystem
- [x] Реализовать advance() с переносами
- [x] Добавить TimeOfDay enum
- [x] Связать с сезонами
- [x] Написать tests

**Files:** `src/world/time_system.py`

---

### US-2.3: Климатическая Система

**ID:** US-2.3
**Приоритет:** P1
**Статус:** Done
**Story Points:** 5

**Описание:**
Как мир, я хочу иметь сезоны и катаклизмы, чтобы влиять на ресурсы и выживание NPC.

**Acceptance Criteria:**

```gherkin
Given день 100 (лето)
When запрашивается сезон
Then возвращается SUMMER

Given лето
When генерируются ресурсы
Then food regeneration увеличена на 50%

Given засуха активна
When проверяется здоровье NPC
Then mortality rate увеличивается
```

**Tasks:**
- [x] Создать Season enum
- [x] Реализовать ClimateSystem
- [x] Добавить катаклизмы (7 типов)
- [x] Связать с ресурсами и здоровьем
- [x] Написать tests

**Files:** `src/world/climate.py`

---

## Epic #3.0: Экономический Базис (Economic Base)

**Описание:** Производство, ресурсы, технологии и собственность — основа марксистской модели.

**Статус:** Done

### US-3.1: Система Ресурсов

**ID:** US-3.1
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как экономика, я хочу отслеживать ресурсы (еда, дерево, камень), чтобы NPC могли производить и потреблять.

**Acceptance Criteria:**

```gherkin
Given инвентарь пуст
When добавляется 10 единиц FOOD
Then inventory.get(FOOD) возвращает 10

Given инвентарь с capacity 100
When добавляется 150 единиц
Then добавляется только 100, остальное теряется

Given FOOD в инвентаре = 5
When NPC ест 3
Then FOOD становится 2
```

**Tasks:**
- [x] Создать ResourceType enum (12+ типов)
- [x] Реализовать Inventory с capacity
- [x] Добавить методы add/remove/has
- [x] Реализовать регенерацию ресурсов
- [x] Написать tests

**Files:** `src/economy/resources.py`

---

### US-3.2: Система Производства

**ID:** US-3.2
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как NPC, я хочу производить товары из ресурсов, используя технологии.

**Acceptance Criteria:**

```gherkin
Given NPC знает HUNTING и имеет WEAPON
When выполняет HUNT
Then получает FOOD (5) и LEATHER (1)

Given NPC не знает AGRICULTURE
When пытается выполнить FARMING
Then действие недоступно

Given несколько NPC работают вместе
When production collective
Then output увеличивается
```

**Tasks:**
- [x] Создать ProductionMethod dataclass
- [x] Реализовать 20+ методов производства
- [x] Добавить проверку requirements
- [x] Реализовать коллективное производство
- [x] Написать tests

**Files:** `src/economy/production.py`

---

### US-3.3: Технологическое Древо

**ID:** US-3.3
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как цивилизация, я хочу открывать технологии, чтобы получать доступ к новым методам производства.

**Acceptance Criteria:**

```gherkin
Given NPC знает STONE_WORKING и HUNTING
When проверяются доступные технологии
Then BOW_AND_ARROW доступна для открытия

Given NPC работает с камнем
When прогресс достигает 100%
Then технология открывается и публикуется событие

Given технология открыта одним NPC
When другой NPC учится у него
Then прогресс изучения ускоряется
```

**Tasks:**
- [x] Создать Technology dataclass
- [x] Реализовать 40+ технологий
- [x] Создать TechnologyTree с prerequisites
- [x] Реализовать discovery через работу
- [x] Добавить передачу знаний
- [x] Написать tests

**Files:** `src/economy/technology.py`

---

### US-3.4: Система Собственности

**ID:** US-3.4
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как общество, я хочу отслеживать собственность, чтобы классы могли ВОЗНИКАТЬ из экономических отношений.

**Acceptance Criteria:**

```gherkin
Given примитивная община
When вся собственность COMMUNAL
Then классов нет, все равны

Given NPC накопил землю
When property_type становится PRIVATE
Then NPC становится LANDOWNER

Given LANDOWNER умирает
When есть наследник
Then собственность переходит к наследнику
```

**Tasks:**
- [x] Создать PropertyType и PropertyCategory enums
- [x] Реализовать PropertyRight с правами
- [x] Добавить transfer и inheritance
- [x] Связать с классовой системой
- [x] Написать tests

**Files:** `src/economy/property.py`

---

## Epic #4.0: Социальная Структура (Social Structure)

**Описание:** Семьи, демография и классы.

**Статус:** Done ✅

### US-4.1: Семейная Система

**ID:** US-4.1
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как NPC, я хочу создавать семьи, чтобы иметь социальные связи и наследование.

**Acceptance Criteria:**

```gherkin
Given два взрослых NPC разного пола
When они вступают в брак
Then создаётся Family с обоими как members

Given семья с детьми
When рождается ребёнок
Then он добавляется в family.members

Given глава семьи умирает
When определяется новый глава
Then старший взрослый член становится главой
```

**Tasks:**
- [x] Создать Family dataclass
- [x] Реализовать Marriage
- [x] Добавить add/remove members
- [x] Реализовать inheritance logic
- [x] Написать tests

**Files:** `src/society/family.py`

---

### US-4.2: Демография

**ID:** US-4.2
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как симуляция, я хочу моделировать рождения и смерти, чтобы популяция развивалась реалистично.

**Acceptance Criteria:**

```gherkin
Given NPC возраста 75
When рассчитывается mortality_rate
Then rate значительно выше, чем для молодого

Given мать и отец
When рождается ребёнок
Then он наследует генетические черты обоих

Given NPC голодает (hunger < 0.1)
When проверяется смертность
Then mortality_rate увеличивается значительно
```

**Tasks:**
- [x] Создать LifeStage enum
- [x] Реализовать calculate_mortality_rate
- [x] Реализовать process_birth с генетикой
- [x] Добавить факторы смертности
- [x] Написать tests

**Files:** `src/society/demography.py`

---

### US-4.3: Классовая Система (Emergent)

**ID:** US-4.3
**Приоритет:** P0
**Статус:** Done ✅
**Story Points:** 8
**Evil Audit Score:** 8.75/10

**Описание:**
Как марксистская симуляция, я хочу, чтобы классы ВОЗНИКАЛИ из отношений собственности, а не задавались жёстко.

**Acceptance Criteria:**

```gherkin
Given все ресурсы общинные
When определяется класс NPC
Then все являются COMMUNAL_MEMBER

Given NPC владеет землёй (PRIVATE)
When определяется его класс
Then он становится LANDOWNER

Given NPC не владеет ничем
When определяется его класс
Then он становится LABORER
```

**Tasks:**
- [x] Создать ClassType enum
- [x] Реализовать determine_class (EMERGENT!)
- [x] Добавить class consciousness (Грамши)
- [x] Реализовать detect_class_conflict полностью
- [x] ConflictType, ConflictStage, ConsciousnessPhase enums
- [x] ClassConsciousnessSystem с organic intellectuals
- [x] ConflictResolutionSystem с исходами
- [x] Интеграция с Simulation
- [x] 52 unit tests (100% pass)

**Files:** `src/society/classes.py`

---

## Epic #5.0: Культурная Надстройка (Cultural Superstructure)

**Описание:** Верования, традиции и нормы, определяемые базисом.

**Статус:** Done

### US-5.1: Система Верований (Emergent)

**ID:** US-5.1
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как культура, я хочу, чтобы верования ВОЗНИКАЛИ из экономических условий, следуя марксистской модели.

**Acceptance Criteria:**

```gherkin
Given появилась частная собственность
When формируются верования
Then появляется PROPERTY_SACRED с BeliefOrigin.ECONOMIC

Given классовое неравенство
When верование выгодно владельцам
Then HIERARCHY_NATURAL укрепляется среди них

Given катаклизм (засуха)
When формируются верования
Then ANIMISM усиливается с BeliefOrigin.CRISIS
```

**Tasks:**
- [x] Создать BeliefType enum
- [x] Создать BeliefOrigin enum
- [x] Реализовать form_belief (EMERGENT!)
- [x] Связать с классами (benefiting_class)
- [x] Добавить belief conflicts
- [x] Написать tests

**Files:** `src/culture/beliefs.py`

---

### US-5.2: Традиции

**ID:** US-5.2
**Приоритет:** P1
**Статус:** Done
**Story Points:** 3

**Описание:**
Как культура, я хочу иметь традиции и ритуалы, связанные с верованиями и сезонами.

**Acceptance Criteria:**

```gherkin
Given верование ANCESTOR_WORSHIP сильно
When приходит осень
Then активируется традиция "Праздник урожая"

Given традиция требует FOOD: 50
When ресурсов достаточно
Then традиция проводится и social cohesion растёт
```

**Tasks:**
- [x] Создать Tradition dataclass
- [x] Связать с beliefs и seasons
- [x] Реализовать perform_tradition
- [x] Написать tests

**Files:** `src/culture/traditions.py`

---

### US-5.3: Социальные Нормы

**ID:** US-5.3
**Приоритет:** P1
**Статус:** Done
**Story Points:** 3

**Описание:**
Как общество, я хочу иметь нормы поведения со штрафами за нарушения.

**Acceptance Criteria:**

```gherkin
Given норма "не красть"
When NPC крадёт
Then его reputation уменьшается

Given нарушение нормы
When enforcement сильный
Then штраф применяется немедленно
```

**Tasks:**
- [x] Создать SocialNorm dataclass
- [x] Реализовать check_violation
- [x] Добавить apply_penalty
- [x] Написать tests

**Files:** `src/culture/norms.py`

---

## Epic #6.0: NPC - Уникальные Личности (NPC Characters)

**Описание:** Персонажи как автономные агенты с генетикой, памятью и личностью.

**Статус:** Done

### US-6.1: Базовые Характеристики NPC

**ID:** US-6.1
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как NPC, я хочу иметь уникальные характеристики (stats, skills), чтобы отличаться от других.

**Acceptance Criteria:**

```gherkin
Given новый NPC создаётся
When характеристики генерируются
Then stats (strength, dexterity, etc.) в диапазоне 1-20

Given NPC занимается охотой
When он часто охотится
Then skill hunting постепенно растёт

Given два NPC
When сравниваются их характеристики
Then они различаются (уникальность)
```

**Tasks:**
- [x] Создать Stats dataclass
- [x] Создать Skills dataclass
- [x] Реализовать Character class
- [x] Добавить skill growth
- [x] Написать tests

**Files:** `src/npc/character.py`

---

### US-6.2: Система Личности

**ID:** US-6.2
**Приоритет:** P0
**Статус:** Done
**Story Points:** 3

**Описание:**
Как NPC, я хочу иметь черты характера, чтобы они влияли на мои решения.

**Acceptance Criteria:**

```gherkin
Given NPC с trait GREEDY высоким
When выбирается действие
Then экономические действия приоритетнее

Given NPC с trait BRAVE
When опасная ситуация
Then он склонен действовать, а не бежать

Given NPC с INTROVERT
When social need низкий
Then он реже инициирует общение
```

**Tasks:**
- [x] Создать Trait enum
- [x] Реализовать Personality class
- [x] Добавить affects_decision()
- [x] Интегрировать с behavior system
- [x] Написать tests

**Files:** `src/npc/personality.py`

---

### US-6.3: Система Потребностей

**ID:** US-6.3
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как NPC, я хочу иметь потребности (голод, сон, социализация), чтобы они определяли мои приоритеты.

**Acceptance Criteria:**

```gherkin
Given NPC не ел 8 часов
When обновляются потребности
Then hunger уменьшается (0.0 = критично)

Given hunger < 0.2
When выбирается действие
Then EAT имеет наивысший приоритет

Given все потребности удовлетворены
When выбирается действие
Then NPC может работать или отдыхать
```

**Tasks:**
- [x] Создать NeedType enum
- [x] Реализовать Need class с decay
- [x] Создать NeedSystem
- [x] Добавить get_most_urgent()
- [x] Написать tests

**Files:** `src/npc/needs.py`

---

### US-6.4: Отношения между NPC

**ID:** US-6.4
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как NPC, я хочу помнить отношения с другими NPC, чтобы взаимодействовать по-разному.

**Acceptance Criteria:**

```gherkin
Given NPC_A помог NPC_B
When обновляются отношения
Then relationship strength увеличивается

Given relationship.strength > 0.7
When определяется тип
Then RelationType = FRIEND

Given NPC_A и NPC_B враги
When NPC_A выбирает партнёра для работы
Then он избегает NPC_B
```

**Tasks:**
- [x] Создать RelationType enum
- [x] Реализовать Relationship class
- [x] Создать RelationshipSystem
- [x] Добавить update на основе interactions
- [x] Написать tests

**Files:** `src/npc/relationships.py`

---

### US-6.5: Генетическая Система

**ID:** US-6.5
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как ребёнок, я хочу наследовать черты от родителей, чтобы создать генетическое разнообразие.

**Acceptance Criteria:**

```gherkin
Given мать с high strength, отец с low strength
When рождается ребёнок
Then его strength где-то между (с вариацией)

Given редкая мутация
When она происходит
Then ребёнок получает уникальную черту

Given популяция развивается
When проходят поколения
Then генетическое разнообразие сохраняется
```

**Tasks:**
- [x] Создать Gene dataclass
- [x] Реализовать GeneticTraits
- [x] Создать inherit() с комбинированием
- [x] Добавить мутации
- [x] Написать tests

**Files:** `src/npc/genetics.py`

---

### US-6.6: Система Памяти (Generative Agents)

**ID:** US-6.6
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как NPC, я хочу помнить события и делать выводы, чтобы моё поведение было реалистичным.

**Acceptance Criteria:**

```gherkin
Given важное событие (свадьба)
When оно происходит
Then добавляется Memory с high importance

Given NPC часто помогал мне
When вызывается reflect()
Then создаётся Reflection "X — друг"

Given запрос о человеке
When retrieve_relevant(person_name)
Then возвращаются связанные воспоминания
```

**Tasks:**
- [x] Создать Memory dataclass
- [x] Создать Reflection dataclass
- [x] Реализовать MemorySystem
- [x] Добавить retrieve_relevant()
- [x] Реализовать reflect()
- [x] Добавить forget_unimportant()
- [x] Написать tests

**Files:** `src/npc/memory.py`

---

### US-6.7: BDI-Архитектура

**ID:** US-6.7
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как NPC, я хочу иметь BDI-систему (Beliefs, Desires, Intentions), чтобы принимать автономные решения.

**Acceptance Criteria:**

```gherkin
Given NPC видит еду
When perceive() вызывается
Then создаётся Belief "food_available_at_X"

Given NPC голоден
When deliberate() вызывается
Then Desire "eat" имеет высокий приоритет

Given выбрана цель "eat"
When plan() вызывается
Then создаётся Intention с планом [go_to_food, pick_up, eat]
```

**Tasks:**
- [x] Создать Belief dataclass
- [x] Создать Desire dataclass
- [x] Создать Intention dataclass
- [x] Реализовать BDISystem
- [x] Добавить perceive/deliberate/plan/execute
- [x] Написать tests

**Files:** `src/npc/ai/bdi.py`

---

## Epic #7.0: Поведенческая Система (Behavior System)

**Описание:** Принятие решений NPC на основе всех факторов.

**Статус:** Done

### US-7.1: Система Принятия Решений

**ID:** US-7.1
**Приоритет:** P0
**Статус:** Done
**Story Points:** 8

**Описание:**
Как NPC, я хочу выбирать действия на основе потребностей, личности и окружения.

**Acceptance Criteria:**

```gherkin
Given hunger < 0.2
When decide_action() вызывается
Then возвращается EAT

Given ночь и NPC устал
When decide_action() вызывается
Then возвращается SLEEP

Given NPC с HARDWORKING trait
When нужно выбрать между WORK и REST
Then WORK имеет больший вес
```

**Tasks:**
- [x] Создать Action enum
- [x] Реализовать BehaviorSystem
- [x] Добавить decide_action() с учётом всех факторов
- [x] Реализовать evaluate_action()
- [x] Интегрировать с BDI
- [x] Написать tests

**Files:** `src/ai/behavior.py`

---

## Epic #8.0: Пользовательский Интерфейс (User Interface)

**Описание:** CLI для управления и наблюдения за симуляцией.

**Статус:** Done ✅

### US-8.1: CLI Интерфейс

**ID:** US-8.1
**Приоритет:** P0
**Статус:** Done
**Story Points:** 5

**Описание:**
Как пользователь, я хочу управлять симуляцией через командную строку.

**Acceptance Criteria:**

```gherkin
Given симуляция запущена
When ввожу команду "1"
Then симуляция продвигается на 1 час

Given ввожу команду "3"
When отображается список
Then вижу всех жителей с их статусом

Given ввожу команду "5" и ID
When NPC существует
Then отображается подробная информация о нём
```

**Tasks:**
- [x] Создать GameEngine
- [x] Реализовать process_command()
- [x] Добавить display методы
- [x] Реализовать авто-симуляцию
- [x] Написать tests

**Files:** `src/game/engine.py`

---

### US-8.2: Визуализация Карты

**ID:** US-8.2
**Приоритет:** P1
**Статус:** Done (текстовая)
**Story Points:** 3

**Описание:**
Как пользователь, я хочу видеть карту мира, чтобы понимать расположение локаций и NPC.

**Acceptance Criteria:**

```gherkin
Given карта 40x40
When запрашивается визуализация
Then отображается ASCII-карта с terrain

Given NPC в локации
When локация отображается
Then видно количество NPC в ней
```

**Tasks:**
- [x] Создать MapVisualization
- [x] Реализовать ASCII render
- [x] Добавить NPC markers
- [x] Написать tests

**Files:** `src/world/map.py`

---

### US-8.3: Графический Интерфейс

**ID:** US-8.3
**Приоритет:** P2
**Статус:** Done ✅
**Story Points:** 13
**Evil Audit Score:** 8.42/10

**Описание:**
Как пользователь, я хочу графический интерфейс (pygame), чтобы наблюдать за симуляцией визуально.

**Acceptance Criteria:**

```gherkin
Given pygame установлен
When запускается графический режим
Then отображается окно с картой

Given NPC перемещается
When обновляется экран
Then виден спрайт NPC в новой позиции

Given клик на NPC
When обрабатывается событие
Then показывается popup с информацией
```

**Tasks:**
- [x] Установить pygame-ce
- [x] Создать Window class с fixed time step game loop
- [x] Реализовать NPCSprite с анимацией
- [x] Добавить Camera с zoom/scroll
- [x] Создать MapRenderer с тайлами
- [x] UI panels: StatusBar, InfoPanel, EventLog, StatisticsPanel
- [x] Event handling: клики, клавиатура, колесо мыши
- [x] Индикаторы классового сознания и конфликтов
- [x] Speed controls (1x, 2x, 5x, 10x)
- [x] Интеграция с main_gui.py

**Files:** `src/ui/` (7 файлов), `main_gui.py`

---

## Epic #9.0: Сохранение и Загрузка (Persistence)

**Описание:** Сохранение и загрузка состояния мира.

**Статус:** Done ✅

### US-9.1: Сохранение Мира

**ID:** US-9.1
**Приоритет:** P2
**Статус:** Done ✅
**Story Points:** 8
**Evil Audit Score:** 8.33/10

**Описание:**
Как пользователь, я хочу сохранять состояние мира, чтобы продолжить позже.

**Acceptance Criteria:**

```gherkin
Given симуляция идёт 100 лет
When пользователь сохраняет
Then создаётся файл save.json с полным состоянием

Given save файл существует
When загружается
Then мир восстанавливается точно

Given corrupted save file
When загружается
Then показывается ошибка, мир не повреждается
```

**Tasks:**
- [x] Создать SaveManager с save/load/autosave/quicksave
- [x] Реализовать serialize для всех entities (NPC, Map, Classes, Conflicts)
- [x] Добавить gzip compression
- [x] Версионирование (SAVE_VERSION = "1.0.0")
- [x] Checksum validation
- [x] Ротация автосохранений (MAX_AUTOSAVES = 3)
- [x] Интеграция в main.py (s/l/f команды)
- [x] Интеграция в main_gui.py (F5/F9 клавиши)
- [x] Список сохранений с метаданными

**Files:** `src/persistence/` (4 файла)

---

## Backlog Summary

### By Epic

| Epic | Total Stories | Done | In Progress | Planned |
|------|---------------|------|-------------|---------|
| #1.0 Core | 3 | 3 | 0 | 0 |
| #2.0 World | 3 | 3 | 0 | 0 |
| #3.0 Economy | 4 | 4 | 0 | 0 |
| #4.0 Society | 3 | 3 | 0 | 0 |
| #5.0 Culture | 3 | 3 | 0 | 0 |
| #6.0 NPC | 7 | 7 | 0 | 0 |
| #7.0 Behavior | 1 | 1 | 0 | 0 |
| #8.0 UI | 3 | 3 | 0 | 0 |
| #9.0 Persistence | 1 | 1 | 0 | 0 |
| **TOTAL** | **28** | **28** | **0** | **0** |

### By Priority

| Priority | Count | Done |
|----------|-------|------|
| P0 (Critical) | 20 | 20 |
| P1 (High) | 5 | 5 |
| P2 (Medium) | 3 | 3 |

### Story Points

- **Total:** ~145 SP
- **Completed:** ~145 SP
- **Velocity:** 100% complete ✅

---

## Sprint Summary (2026-02-01)

### Completed Stories with Evil Audit Scores:

| Story | Score | Status |
|-------|-------|--------|
| US-4.3 Классовые Конфликты | 8.75/10 | ✅ APPROVED |
| US-8.3 Графический Интерфейс | 8.42/10 | ✅ APPROVED |
| US-9.1 Сохранение Мира | 8.33/10 | ✅ APPROVED |

### Key Achievements:
- **Классовая борьба по Грамши**: organic intellectuals, consciousness phases
- **GUI с pygame-ce**: fixed time step, camera, sprites, panels
- **Persistence**: JSON+gzip, versioning, autosave rotation

---

*Документ создан по методологии [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)*
*Обновлено: 2026-02-01 — Sprint Complete*
