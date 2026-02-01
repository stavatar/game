---
title: "AI Context: Базис и Надстройка"
description: "Сводный контекстный файл для быстрого понимания проекта ИИ-агентами"
purpose: "Quick context for AI agents"
version: "1.0.0"
language: "ru"
keywords: ["simulation", "marxism", "society", "python", "bdi", "npc", "emergent", "agent"]
entry_points:
  cli: "./main.py"
  gui: "./main_gui.py"
last_updated: "2026-02-01"
---

# AI Context: Базис и Надстройка

> Симулятор развития общества на основе марксистской теории с эмерджентными классами и автономными NPC-агентами.

---

## Quick Facts

| Параметр | Значение |
|----------|----------|
| **Тип** | Python simulation game |
| **Тема** | Марксистское развитие общества |
| **Язык** | Python 3.11+ |
| **Зависимости** | None (core), pygame-ce (GUI) |
| **Entry CLI** | `./main.py` |
| **Entry GUI** | `./main_gui.py` |
| **Архитектура** | Event-Driven, Multi-Agent Simulation |
| **Паттерны** | Observer, Strategy, Factory, BDI |

---

## Architecture Summary

### Принцип Базис-Надстройка

Ключевое архитектурное решение: **экономический базис обновляется ПЕРЕД культурной надстройкой**.

```
┌─────────────────────────────────────────────────────────┐
│                    SIMULATION LOOP                       │
│                 (updates every hour)                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   1. TIME      →   2. ECONOMY    →   3. SOCIETY        │
│   (advance)        (БАЗИС)           (structure)        │
│                                                         │
│   4. CULTURE   →   5. NPC        →   6. CLIMATE        │
│   (НАДСТРОЙКА)     (actions)         (events)          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Порядок обновления (критически важен!)

```
Economy (production, property, technology)
    ↓
Society (family, demography, classes)
    ↓
Culture (beliefs, traditions, norms)
    ↓
NPC Actions (BDI cycle)
```

### Эмерджентные системы

В отличие от традиционных игр:

| Традиционный подход | Этот проект |
|---------------------|-------------|
| Классы предопределены | Классы ВОЗНИКАЮТ из отношений собственности |
| Культура — декорация | Культура ФОРМИРУЕТСЯ из экономических условий |
| NPC следуют скриптам | NPC — автономные агенты с BDI |
| История прописана | История генерируется сама |

---

## Key Classes

### Core (Ядро)

| Класс | Путь | Описание |
|-------|------|----------|
| `Simulation` | `./src/core/simulation.py` | Главный цикл симуляции |
| `Config` | `./src/core/config.py` | Конфигурация всех параметров |
| `EventBus` | `./src/core/events.py` | Система событий (pub/sub) |
| `EventType` | `./src/core/events.py` | Enum с 60+ типами событий |

### World (Мир)

| Класс | Путь | Описание |
|-------|------|----------|
| `WorldMap` | `./src/world/map.py` | Карта мира (сетка 50x50) |
| `ClimateSystem` | `./src/world/climate.py` | Климат, сезоны, катаклизмы |
| `Location` | `./src/world/location.py` | Локации на карте |
| `TimeSystem` | `./src/world/time_system.py` | Система времени (часы, дни, годы) |

### Economy (Базис)

| Класс | Путь | Описание |
|-------|------|----------|
| `Production` | `./src/economy/production.py` | Система производства (20+ методов) |
| `OwnershipSystem` | `./src/economy/property.py` | Собственность → классы |
| `KnowledgeSystem` | `./src/economy/technology.py` | Технологическое древо (40+ технологий) |
| `ResourceType` | `./src/economy/resources.py` | Типы ресурсов |

### Society (Социум)

| Класс | Путь | Описание |
|-------|------|----------|
| `FamilySystem` | `./src/society/family.py` | Семьи и родство |
| `DemographySystem` | `./src/society/demography.py` | Рождение, смерть, возраст |
| `ClassSystem` | `./src/society/classes.py` | Классовая система (EMERGENT!) |

### Culture (Надстройка)

| Класс | Путь | Описание |
|-------|------|----------|
| `BeliefSystem` | `./src/culture/beliefs.py` | Верования и идеология (EMERGENT!) |
| `TraditionSystem` | `./src/culture/traditions.py` | Традиции |
| `NormSystem` | `./src/culture/norms.py` | Социальные нормы |

### NPC (Персонажи)

| Класс | Путь | Описание |
|-------|------|----------|
| `Character` | `./src/npc/character.py` | Основной класс NPC |
| `Personality` | `./src/npc/personality.py` | Черты характера |
| `Needs` | `./src/npc/needs.py` | Система потребностей |
| `Memory` | `./src/npc/memory.py` | Память (Generative Agents) |
| `BDIAgent` | `./src/npc/ai/bdi.py` | BDI-архитектура (Beliefs-Desires-Intentions) |
| `Genetics` | `./src/npc/genetics.py` | Наследование от родителей |

### AI (Поведение)

| Класс | Путь | Описание |
|-------|------|----------|
| `BehaviorAI` | `./src/ai/behavior.py` | Система принятия решений |

---

## Run Commands

### Запуск

```bash
# CLI режим (основной)
python ./main.py

# GUI режим (требует pygame-ce)
python ./main_gui.py
```

### Тестирование

```bash
# Запуск всех тестов
pytest ./tests/ -v

# Проверка импорта
python -c "import main; print('OK')"
```

### Зависимости

```bash
# Установка для GUI
pip install pygame-ce

# Установка для тестов
pip install pytest
```

---

## File Index

### Корневые файлы

| Путь | Описание |
|------|----------|
| `./main.py` | CLI точка входа |
| `./main_gui.py` | GUI точка входа |
| `./README.md` | Главная документация |

### Документация

| Путь | Описание |
|------|----------|
| `./docs/README.md` | Обзор архитектуры |
| `./docs/bmad/index.md` | Индекс BMAD-документации |
| `./docs/bmad/architecture.md` | Архитектурный документ |
| `./docs/bmad/PRD.md` | Требования к продукту |
| `./docs/bmad/epics-and-stories.md` | Эпики и истории |
| `./docs/bmad/research/agent-simulations.md` | Исследование агентных симуляций |
| `./docs/bmad/research/marxism-guide.md` | Марксистская теория |

### Исходный код

```
./src/
├── core/           # Ядро симуляции
│   ├── config.py       # Конфигурация
│   ├── simulation.py   # Главный цикл
│   └── events.py       # Система событий (60+ типов)
│
├── world/          # Мир
│   ├── map.py          # Карта (сетка 50x50)
│   ├── terrain.py      # Типы местности
│   ├── climate.py      # Климат и катаклизмы
│   └── location.py     # Локации
│
├── economy/        # БАЗИС
│   ├── resources.py    # Ресурсы
│   ├── production.py   # Производство (20+ методов)
│   ├── technology.py   # Технологии (40+ технологий)
│   └── property.py     # Собственность → классы
│
├── society/        # Социальная структура
│   ├── family.py       # Семьи и родство
│   ├── demography.py   # Демография
│   └── classes.py      # Классовая система (EMERGENT!)
│
├── culture/        # НАДСТРОЙКА
│   ├── beliefs.py      # Верования (EMERGENT!)
│   ├── traditions.py   # Традиции
│   └── norms.py        # Социальные нормы
│
├── npc/            # Персонажи
│   ├── character.py    # Основной класс NPC
│   ├── genetics.py     # Генетика (наследование)
│   ├── memory.py       # Память (Generative Agents)
│   ├── personality.py  # Личность
│   ├── needs.py        # Потребности
│   ├── relationships.py # Отношения
│   └── ai/
│       └── bdi.py      # BDI-архитектура
│
├── ai/             # Поведение
│   └── behavior.py     # Система принятия решений
│
├── game/           # Игровой движок
│   └── engine.py       # Движок
│
└── data/           # Данные
    └── names.py        # Генератор имён
```

---

## BDI Architecture

Архитектура Beliefs-Desires-Intentions для автономных NPC:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PERCEIVE   │────►│  BELIEFS    │────►│ DELIBERATE  │
│  (World)    │     │  (Update)   │     │  (Goals)    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   EXECUTE   │◄────│ INTENTIONS  │◄────│    PLAN     │
│  (Action)   │     │  (Select)   │     │  (Create)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Цикл BDI:**
1. **Perceive** — NPC воспринимает мир
2. **Beliefs** — Обновляет свои убеждения
3. **Deliberate** — Формирует желания на основе потребностей
4. **Plan** — Создаёт план действий
5. **Intentions** — Выбирает намерение
6. **Execute** — Выполняет действие

---

## Memory System (Generative Agents)

Система памяти на основе исследования Stanford:

| Компонент | Описание | Файл |
|-----------|----------|------|
| **Memory Stream** | Все события в жизни NPC | `./src/npc/memory.py` |
| **Reflection** | Выводы из опыта | `./src/npc/memory.py` |
| **Retrieval** | Поиск релевантных воспоминаний | `./src/npc/memory.py` |
| **Planning** | Планирование на основе памяти | `./src/npc/ai/bdi.py` |

---

## Configuration Parameters

Ключевые параметры из `./src/core/config.py`:

| Параметр | Значение | Описание |
|----------|----------|----------|
| `map_width` | 50 | Ширина карты |
| `map_height` | 50 | Высота карты |
| `initial_population` | 12 | Начальное население |
| `initial_families` | 3 | Начальное число семей |
| `hours_per_day` | 24 | Часов в дне |
| `days_per_month` | 30 | Дней в месяце |
| `months_per_year` | 12 | Месяцев в году |
| `days_per_season` | 90 | Дней в сезоне |

---

## Development Status

### Готово (MVP)

- [x] Core simulation loop
- [x] Event system (60+ event types)
- [x] World & map (50x50 grid)
- [x] Climate & seasons
- [x] Resources & production (20+ methods)
- [x] Technology tree (40+ techs)
- [x] Property system (emergent classes)
- [x] Family & demography
- [x] Class system (EMERGENT!)
- [x] Belief system (EMERGENT!)
- [x] Traditions & norms
- [x] NPC: Stats, Skills, Personality, Needs
- [x] NPC: Genetics (inheritance)
- [x] NPC: Memory (Generative Agents)
- [x] NPC: BDI architecture
- [x] Behavior system
- [x] CLI interface
- [x] GUI interface (pygame-ce)

### Планируется

- [ ] Full BDI integration in main loop
- [ ] Class conflicts
- [ ] Save/Load improvements
- [ ] Statistics & charts
- [ ] LLM integration (optional)

---

## Links

| Ресурс | URL |
|--------|-----|
| BMAD Documentation | `./docs/bmad/index.md` |
| Architecture | `./docs/bmad/architecture.md` |
| PRD | `./docs/bmad/PRD.md` |
| Agent Simulations Research | `./docs/bmad/research/agent-simulations.md` |
| Marxism Guide | `./docs/bmad/research/marxism-guide.md` |

---

*Этот файл оптимизирован для быстрого понимания проекта ИИ-агентами.*
