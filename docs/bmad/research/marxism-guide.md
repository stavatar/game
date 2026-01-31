# Research: Marxism for Game Simulation

## Руководство по Марксистской Теории для Проекта "Базис и Надстройка"

**Версия:** 1.0
**Дата:** 2026-01-31
**Тип документа:** Исследование
**Статус:** Завершено

---

## 1. Введение

Данный документ содержит результаты исследования марксистской теории исторического материализма с практическими примерами и рекомендациями по их моделированию в проекте "Базис и Надстройка".

> "Не сознание людей определяет их бытие, а наоборот, их общественное бытие определяет их сознание."
> — Карл Маркс, "К критике политической экономии" (1859)

---

## 2. Исторический Материализм: Основы

### 2.1 Центральный Тезис

**Исторический материализм** — теория исторического анализа, ищущая конечную причину и движущую силу всех важных исторических событий в **экономическом развитии общества**, в изменениях **способов производства** и **обмена**, и в вытекающем из этого **делении общества на классы** и **борьбе этих классов**.

### 2.2 Базис и Надстройка

```
┌─────────────────────────────────────────────────────────────────┐
│                        НАДСТРОЙКА                                │
│                       (Superstructure)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ИДЕОЛОГИЯ          │  Философия, религия, искусство          │
│   ПОЛИТИКА           │  Государство, законы, армия              │
│   КУЛЬТУРА           │  Традиции, нормы, мораль                 │
│                                                                  │
│   ▲ Отражает и оправдывает базис                               │
│   │                                                              │
├───┼──────────────────────────────────────────────────────────────┤
│   │                        БАЗИС                                 │
│   │                  (Economic Base)                             │
├───┼──────────────────────────────────────────────────────────────┤
│   │                                                              │
│   │   ПРОИЗВОДСТВЕННЫЕ     │  Кто владеет средствами           │
│   │   ОТНОШЕНИЯ            │  производства? Кто работает?       │
│   │                        │  Как распределяется продукт?       │
│   │                        │                                     │
│   │   ПРОИЗВОДИТЕЛЬНЫЕ     │  Орудия труда, технологии,         │
│   │   СИЛЫ                 │  рабочая сила, знания              │
│   │                                                              │
└───┴──────────────────────────────────────────────────────────────┘
```

### 2.3 Ключевая Формула

```
Производительные силы
        ↓
        определяют
        ↓
Производственные отношения (= БАЗИС)
        ↓
        определяют
        ↓
Надстройка (идеология, политика, культура)
```

**Важное уточнение от Энгельса:**

> "Экономическое положение — это базис, но различные элементы надстройки... также оказывают своё влияние на ход исторической борьбы."

Т.е. связь **не механическая**, а **диалектическая** — надстройка тоже влияет на базис, но в конечном счёте определяющим является экономика.

---

## 3. Способы Производства (Modes of Production)

### 3.1 Пять Стадий Развития Общества

| Стадия | Базис | Классы | Надстройка |
|--------|-------|--------|------------|
| **1. Первобытный коммунизм** | Общинная собственность | Нет классов | Анимизм, тотемизм |
| **2. Рабовладение** | Рабы как собственность | Рабовладельцы / Рабы | Многобожие, культ героев |
| **3. Феодализм** | Земля у феодалов | Феодалы / Крестьяне | Монотеизм, "божественное право" |
| **4. Капитализм** | Частная собственность на средства производства | Буржуазия / Пролетариат | Либерализм, "свобода" |
| **5. Коммунизм** | Общественная собственность | Нет классов | ? (гуманизм) |

### 3.2 Детальное Описание Стадий

#### 3.2.1 Первобытный Коммунизм (Primitive Communism)

**Характеристики:**
- Собственность принадлежит **всей общине**
- Нет **прибавочного продукта** (всё потребляется)
- Нет **эксплуатации** (некого эксплуатировать)
- **Разделение труда** минимальное (по полу/возрасту)

**Для симуляции:**
```python
class PrimitiveCommunism:
    property_type = PropertyType.COMMUNAL
    surplus_production = 0
    class_structure = None

    def distribute_resources(self, resources, population):
        # Равное распределение
        per_person = resources / len(population)
        return {npc: per_person for npc in population}
```

#### 3.2.2 Рабовладельческий Строй (Slave Society)

**Характеристики:**
- Рабовладельцы владеют **рабами как вещами**
- Рабы лишены **всех прав**
- Появляется **прибавочный продукт**
- Государство защищает интересы рабовладельцев

**Исторические примеры:**
- Древняя Греция: полисы с демократией для граждан, рабство для остальных
- Древний Рим: латифундии, gladiators, масштабное рабство

**Для симуляции:**
```python
class SlaveSociety:
    property_type = PropertyType.PRIVATE  # включая рабов
    exploitation_rate = 1.0  # 100% продукта раба

    def can_own_slaves(self, npc):
        return npc.class_type == ClassType.CITIZEN

    def slave_produces(self, slave, hours):
        product = slave.work(hours)
        # Весь продукт идёт владельцу
        slave.owner.inventory.add(product)
        # Рабу — только для выживания
        slave.inventory.add(SUBSISTENCE_MINIMUM)
```

#### 3.2.3 Феодализм (Feudalism)

**Характеристики:**
- Феодалы владеют **землёй**
- Крестьяне **прикреплены к земле** (крепостные)
- **Личная зависимость** крестьянина от феодала
- Эксплуатация через **ренту** (барщина, оброк, десятина)

**Ключевое отличие от рабства:**

> "Феодал эксплуатировал крестьян, часто доводя их до нищеты. Но он не мог эксплуатировать ради накопления прибыли. Цель производства — потребление, не накопление."
> — Chris Harman

**Исторические примеры:**
- Европа X-XV вв.: манориальная система
- Россия до 1861: крепостное право
- Япония: самураи и крестьяне

**Для симуляции:**
```python
class Feudalism:
    property_type = PropertyType.PRIVATE  # земля
    serf_attachment = True  # крестьянин привязан к земле

    def calculate_rent(self, serf, lord):
        """Три формы ренты"""
        production = serf.produce()

        # Барщина: работа на земле феодала
        corvee = production * 0.3

        # Оброк: часть урожая
        quitrent = production * 0.3

        # Десятина: церкви
        tithe = production * 0.1

        lord.receive(corvee + quitrent)
        church.receive(tithe)
        serf.keep(production - corvee - quitrent - tithe)  # 30%
```

#### 3.2.4 Капитализм (Capitalism)

**Характеристики:**
- Частная собственность на **средства производства**
- Рабочие **формально свободны**, но вынуждены продавать рабочую силу
- Эксплуатация через **наёмный труд**
- Цель — **накопление капитала** (не потребление)

**Ключевые понятия:**

1. **Товар** — продукт, произведённый для продажи
2. **Рабочая сила как товар** — рабочий продаёт свой труд
3. **Прибавочная стоимость** — разница между созданной стоимостью и зарплатой

**Для симуляции:**
```python
class Capitalism:
    property_type = PropertyType.PRIVATE
    wage_labor = True
    goal = "accumulation"  # не consumption

    def exploit_worker(self, worker, capitalist, hours):
        """
        Рабочий работает 8 часов.
        За 4 часа он производит стоимость своей зарплаты.
        Оставшиеся 4 часа — прибавочная стоимость.
        """
        value_created = worker.produce(hours)
        wage = value_created * 0.5  # например
        surplus_value = value_created - wage

        worker.receive(wage)
        capitalist.receive(surplus_value)  # profit!

        return surplus_value
```

---

## 4. Прибавочная Стоимость (Surplus Value)

### 4.1 Определение

**Прибавочная стоимость** — новая стоимость, созданная рабочими сверх стоимости их рабочей силы, которая присваивается капиталистом.

### 4.2 Формулы

```
Стоимость товара = C + V + S

Где:
C = постоянный капитал (машины, сырьё)
V = переменный капитал (зарплата)
S = прибавочная стоимость (surplus value)

Норма прибавочной стоимости = S / V
Норма прибыли = S / (C + V)
```

### 4.3 Пример Расчёта

```
Фабрика:
- Машины и сырьё (C): $80
- Зарплата рабочих (V): $50
- Продали товар за: $150

Прибавочная стоимость (S) = 150 - 80 - 50 = $20

Норма эксплуатации = S/V = 20/50 = 40%
(Капиталист забирает 40% от того, что создали рабочие)

Норма прибыли = S/(C+V) = 20/130 = 15.4%
```

### 4.4 Для Симуляции

```python
def calculate_surplus_value(production, workers, means_of_production):
    """
    Рассчитать прибавочную стоимость от производства

    production: dict{ResourceType: amount}
    workers: List[NPC]
    means_of_production: dict{ResourceType: amount}
    """
    # Стоимость произведённого
    total_value = sum(
        resource.base_value * amount
        for resource, amount in production.items()
    )

    # Постоянный капитал (износ средств производства)
    constant_capital = sum(
        resource.base_value * amount * DEPRECIATION_RATE
        for resource, amount in means_of_production.items()
    )

    # Переменный капитал (стоимость воспроизводства рабочей силы)
    # = сколько нужно рабочему для жизни
    variable_capital = sum(
        worker.subsistence_cost for worker in workers
    )

    # Прибавочная стоимость
    surplus_value = total_value - constant_capital - variable_capital

    # Норма эксплуатации
    exploitation_rate = surplus_value / variable_capital if variable_capital > 0 else 0

    return SurplusValueResult(
        total_value=total_value,
        constant_capital=constant_capital,
        variable_capital=variable_capital,
        surplus_value=surplus_value,
        exploitation_rate=exploitation_rate
    )
```

---

## 5. Первоначальное Накопление (Primitive Accumulation)

### 5.1 Определение

**Первоначальное накопление** — исторический процесс **отделения производителя от средств производства**, который создаёт условия для капитализма.

> "Так называемое первоначальное накопление есть не что иное, как исторический процесс отделения производителя от средств производства."
> — Маркс, "Капитал"

### 5.2 Механизмы

| Механизм | Описание | Пример |
|----------|----------|--------|
| **Enclosure** | Огораживание общинных земель | Англия, XV-XVIII вв. |
| **Колонизация** | Грабёж колоний | Испания в Америке |
| **Работорговля** | Эксплуатация рабского труда | Атлантическая торговля |
| **Государственный долг** | Перераспределение через налоги | Национальные банки |
| **Протекционизм** | Защита "своей" буржуазии | Меркантилизм |

### 5.3 Исторический Пример: Англия

**XV-XVI века:**

1. Крестьяне успешно **сопротивлялись** феодалам
2. К XV веку крепостничество **отменено**
3. Крестьяне имели **традиционные права** на землю

**XVI-XVIII века:**

1. Лорды **огораживают** общинные земли
2. Крестьяне **теряют** землю
3. Бывшие крестьяне становятся **наёмными работниками**
4. → Создаётся **рынок рабочей силы**

### 5.4 Для Симуляции

```python
class PrimitiveAccumulation:
    """Моделирование первоначального накопления"""

    def enclosure(self, common_land, lord):
        """Огораживание общинной земли"""
        # 1. Лорд объявляет землю своей
        self.transfer_ownership(
            land=common_land,
            from_owner=COMMUNAL,
            to_owner=lord
        )

        # 2. Крестьяне теряют права
        for peasant in common_land.users:
            peasant.lose_land_rights(common_land)

            # 3. Крестьянин становится безземельным
            if not peasant.has_other_land():
                peasant.class_type = ClassType.LANDLESS

                # 4. Вынужден продавать рабочую силу
                peasant.available_for_hire = True

    def check_conditions_for_capitalism(self, society):
        """Проверить, готово ли общество к капитализму"""
        # Нужно достаточно безземельных
        landless = [npc for npc in society.npcs
                    if npc.class_type == ClassType.LANDLESS]
        landless_ratio = len(landless) / len(society.npcs)

        # Нужны накопления у будущей буржуазии
        wealthy = [npc for npc in society.npcs
                   if npc.wealth > WEALTH_THRESHOLD]
        accumulation = sum(npc.wealth for npc in wealthy)

        # Нужен рынок
        market_developed = society.has_trade_network

        return (landless_ratio > 0.3 and
                accumulation > ACCUMULATION_THRESHOLD and
                market_developed)
```

---

## 6. Классовое Сознание и Ложное Сознание

### 6.1 Классовое Сознание (Class Consciousness)

**Определение:** Осознание своего положения в системе производственных отношений и общих интересов своего класса.

**Уровни:**

| Уровень | Описание | Пример |
|---------|----------|--------|
| **Класс-в-себе** | Объективное положение | Рабочие на фабрике |
| **Класс-для-себя** | Осознание общих интересов | Рабочие создают профсоюз |

### 6.2 Ложное Сознание (False Consciousness)

**Определение:** Ситуация, когда эксплуатируемый класс принимает идеологию, выгодную эксплуататорам.

**Примеры:**

| Ложное сознание | Чему служит |
|-----------------|-------------|
| "Богатство — божье благословение" | Оправдание неравенства |
| "Каждый может разбогатеть усердием" | Скрытие структурных барьеров |
| "Частная собственность священна" | Защита интересов собственников |
| "Иерархия естественна" | Оправдание власти элит |

### 6.3 Религия как "Опиум Народа"

> "Религия — это вздох угнетённой твари, сердце бессердечного мира... Это опиум народа."
> — Маркс

**Функции религии по Марксу:**

1. **Утешение** — обещание лучшей жизни после смерти
2. **Пассивность** — "терпи на земле, получишь на небе"
3. **Легитимация** — "власть от Бога"
4. **Отвлечение** — от реальных причин страданий

### 6.4 Для Симуляции

```python
class ConsciousnessSystem:
    """Система классового сознания"""

    def calculate_class_consciousness(self, npc):
        """Рассчитать уровень классового сознания NPC"""
        consciousness = 0.0

        # Факторы, повышающие сознание:

        # 1. Опыт эксплуатации
        exploitation_experienced = npc.memory.count_exploitations()
        consciousness += exploitation_experienced * 0.1

        # 2. Общение с представителями своего класса
        same_class_friends = npc.relationships.get_same_class()
        consciousness += len(same_class_friends) * 0.05

        # 3. Кризисы и катаклизмы (разрушают иллюзии)
        crises_experienced = npc.memory.count_crises()
        consciousness += crises_experienced * 0.15

        # Факторы, понижающие сознание (ложное сознание):

        # 1. Религиозность
        if BeliefType.HIERARCHY_NATURAL in npc.beliefs:
            consciousness -= 0.2
        if BeliefType.WEALTH_BLESSING in npc.beliefs:
            consciousness -= 0.15

        # 2. Индивидуальный успех (кооптация)
        if npc.experienced_upward_mobility:
            consciousness -= 0.3

        # 3. Пропаганда правящего класса
        ruling_class_propaganda = npc.exposure_to_dominant_ideology
        consciousness -= ruling_class_propaganda * 0.1

        return max(0.0, min(1.0, consciousness))

    def form_belief_from_conditions(self, npc, economic_conditions):
        """EMERGENT: Верования формируются из условий"""

        # Появление частной собственности → "собственность священна"
        if economic_conditions.private_property_emerged:
            if npc.class_type == ClassType.LANDOWNER:
                # Выгодно владельцам
                probability = 0.8
            else:
                # Внушается через надстройку
                probability = 0.3 + npc.exposure_to_ideology * 0.4

            if random.random() < probability:
                npc.beliefs.add(BeliefType.PROPERTY_SACRED)

        # Классовое неравенство → разные верования по классам
        if economic_conditions.class_inequality > 0.5:
            if npc.is_exploiter:
                # Эксплуататорам выгодно верить в естественность иерархии
                npc.beliefs.add(BeliefType.HIERARCHY_NATURAL)
            elif npc.class_consciousness > 0.5:
                # Сознательные эксплуатируемые — за равенство
                npc.beliefs.add(BeliefType.EQUALITY_IDEAL)
            else:
                # Несознательные — принимают идеологию господ
                npc.beliefs.add(BeliefType.HIERARCHY_NATURAL)
```

---

## 7. Диалектический Материализм

### 7.1 Три Закона Диалектики (Энгельс)

| Закон | Описание | Пример |
|-------|----------|--------|
| **Единство и борьба противоположностей** | Развитие через противоречия | Буржуазия vs Пролетариат |
| **Переход количества в качество** | Накопление → скачок | Реформы → Революция |
| **Отрицание отрицания** | Развитие по спирали | Феодализм → Капитализм → Коммунизм |

### 7.2 Диалектика в Истории

```
ТЕЗИС:        Феодализм (землевладельцы господствуют)
     ↓
АНТИТЕЗИС:    Буржуазия (накапливает капитал, требует власти)
     ↓
СИНТЕЗИС:     Капитализм (буржуазия господствует)

       Но это порождает новое противоречие!

ТЕЗИС:        Капитализм (буржуазия господствует)
     ↓
АНТИТЕЗИС:    Пролетариат (создаёт стоимость, требует справедливости)
     ↓
СИНТЕЗИС:     ?
```

### 7.3 Для Симуляции

```python
class DialecticalProcess:
    """Моделирование диалектических переходов"""

    def check_quantity_to_quality(self, society):
        """Закон перехода количества в качество"""

        # Пример: накопление недовольства → восстание
        discontent = society.measure_discontent()

        if discontent < 0.3:
            return None  # Стабильность
        elif discontent < 0.6:
            return "unrest"  # Волнения
        elif discontent < 0.8:
            return "protests"  # Протесты
        else:
            return "revolution"  # Качественный скачок!

    def check_contradiction(self, society):
        """Закон единства и борьбы противоположностей"""

        # Противоречие между производительными силами
        # и производственными отношениями
        productive_forces = society.technology_level
        relations_of_production = society.property_system

        # Если силы переросли отношения — кризис
        if productive_forces > relations_of_production.capacity:
            return Contradiction(
                thesis=relations_of_production,
                antithesis=productive_forces,
                tension=productive_forces - relations_of_production.capacity
            )

        return None

    def resolve_contradiction(self, contradiction):
        """Разрешение противоречия"""
        if contradiction.tension > REVOLUTION_THRESHOLD:
            # Революционный переход
            return self.revolutionary_transition(contradiction)
        else:
            # Реформистская адаптация
            return self.reform(contradiction)
```

---

## 8. Практические Рекомендации для Симуляции

### 8.1 Порядок Обновления (Критически Важно!)

```python
def update_simulation(world):
    """
    ОБЯЗАТЕЛЬНО: Базис обновляется ПЕРЕД надстройкой!
    Это фундаментальный принцип исторического материализма.
    """

    # 1. ПРОИЗВОДИТЕЛЬНЫЕ СИЛЫ
    world.technology.update()      # Открытия, инновации
    world.resources.update()       # Добыча, истощение

    # 2. ПРОИЗВОДСТВЕННЫЕ ОТНОШЕНИЯ
    world.production.update()      # Кто производит, для кого
    world.property.update()        # Кто владеет чем
    world.distribution.update()    # Как распределяется продукт

    # 3. КЛАССОВАЯ СТРУКТУРА (EMERGENT!)
    world.classes.update()         # Классы из отношений собственности

    # 4. НАДСТРОЙКА (СЛЕДУЕТ ЗА БАЗИСОМ)
    world.beliefs.update()         # Верования из экономических условий
    world.politics.update()        # Власть класса-собственника
    world.culture.update()         # Традиции, нормы

    # 5. NPC ДЕЙСТВУЮТ в этом контексте
    for npc in world.npcs:
        npc.update()
```

### 8.2 Чеклист Марксистской Модели

- [ ] Классы **возникают** из собственности, не задаются
- [ ] Верования **формируются** из экономических условий
- [ ] Базис обновляется **перед** надстройкой
- [ ] **Прибавочный продукт** отслеживается
- [ ] **Норма эксплуатации** рассчитывается
- [ ] **Классовое сознание** зависит от опыта
- [ ] **Ложное сознание** возможно (идеология)
- [ ] Катаклизмы **разрушают** ложное сознание
- [ ] Революции **возможны** при достаточном напряжении

### 8.3 Таблица Соответствий

| Марксистский Концепт | Реализация в Коде |
|----------------------|-------------------|
| Производительные силы | `Technology`, `Skills` |
| Производственные отношения | `PropertySystem`, `ClassSystem` |
| Прибавочная стоимость | `calculate_surplus_value()` |
| Классовая борьба | `ClassConflict`, `Revolution` |
| Идеология | `BeliefSystem` |
| Ложное сознание | `consciousness < 0.5 && dominant_belief` |
| Базис → Надстройка | Update order in `simulation.py` |

### 8.4 Пример Emergent-Перехода к Частной Собственности

```python
def check_property_emergence(world):
    """
    EMERGENT: Частная собственность возникает, когда:
    1. Есть излишек (surplus)
    2. Некоторые накапливают больше других
    3. Накопление передаётся по наследству
    """

    # 1. Появился ли излишек?
    total_production = world.total_production()
    total_consumption = world.total_consumption()
    surplus = total_production - total_consumption

    if surplus <= 0:
        return  # Нет излишка — нет накопления

    # 2. Неравномерное накопление
    wealth_distribution = [npc.wealth for npc in world.npcs]
    gini = calculate_gini(wealth_distribution)

    if gini < 0.3:
        return  # Относительное равенство

    # 3. Передача по наследству
    inheritance_events = world.events.filter(type=EventType.INHERITANCE)

    if len(inheritance_events) > INHERITANCE_THRESHOLD:
        # ПЕРЕХОД: Общинная → Частная собственность
        world.property_system.transition_to(PropertyType.PRIVATE)

        # Формируются верования, оправдывающие это
        world.beliefs.form(
            type=BeliefType.PROPERTY_SACRED,
            origin=BeliefOrigin.ECONOMIC,
            benefiting_class=ClassType.LANDOWNER
        )

        world.events.publish(Event(
            type=EventType.PROPERTY_SYSTEM_CHANGE,
            importance=EventImportance.HISTORIC,
            data={"from": "COMMUNAL", "to": "PRIVATE"}
        ))
```

---

## 9. Исторические Примеры для Вдохновения

### 9.1 Переход от Феодализма к Капитализму в Англии

| Год | Событие | Эффект |
|-----|---------|--------|
| 1348 | Чёрная смерть | -50% населения, крестьяне в силе |
| 1381 | Восстание Уота Тайлера | Крепостничество слабеет |
| XV в. | Крепостничество отменено | Крестьяне свободны |
| XVI в. | Огораживания начинаются | Крестьяне теряют землю |
| 1642 | Английская революция | Буржуазия против короля |
| 1688 | Славная революция | Парламент (буржуазия) побеждает |
| XVIII в. | Промышленная революция | Капитализм полностью |

**Для симуляции:** Моделируй огораживания, накопление капитала, классовые конфликты.

### 9.2 Формирование Идеологии

**Феодализм:**
- "Три сословия: молящиеся, воюющие, работающие"
- "Король — помазанник Божий"
- "Каждый на своём месте"

**Капитализм:**
- "Свобода, равенство, братство" (но формальное)
- "Частная собственность священна"
- "Каждый сам кузнец своего счастья"

**Для симуляции:** Верования должны **соответствовать** господствующему способу производства.

---

## 10. Источники

### Первоисточники

- Marx, K. "Das Kapital" (1867) — [marxists.org](https://www.marxists.org/archive/marx/works/1867-c1/)
- Marx, K. "The German Ideology" (1846)
- Marx, K. "A Contribution to the Critique of Political Economy" (1859)
- Engels, F. "The Origin of the Family, Private Property and the State" (1884)

### Вторичные источники

- [Base and superstructure - Wikipedia](https://en.wikipedia.org/wiki/Base_and_superstructure)
- [Historical materialism - Wikipedia](https://en.wikipedia.org/wiki/Historical_materialism)
- [Surplus value - Wikipedia](https://en.wikipedia.org/wiki/Surplus_value)
- [False consciousness - Wikipedia](https://en.wikipedia.org/wiki/False_consciousness)
- [Chris Harman: From feudalism to capitalism](https://www.marxists.org/archive/harman/1989/xx/transition.html)
- [Chris Harman: Base and Superstructure](https://www.marxists.org/archive/harman/1986/xx/base-super.html)
- [The base-superstructure: A model for analysis - Liberation School](https://www.liberationschool.org/base-superstructure-introduction/)

### Для дальнейшего изучения

- Lukács, G. "History and Class Consciousness" (1923)
- Gramsci, A. "Prison Notebooks" (1929-1935)
- Althusser, L. "Ideology and Ideological State Apparatuses" (1970)

---

*Документ создан по методологии [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)*
