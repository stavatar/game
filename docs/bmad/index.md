---
title: BMAD Documentation Index
description: Навигационный центр BMAD-документации проекта симуляции развития общества
keywords:
  - BMAD
  - документация
  - навигация
  - индекс
  - методология
lang: ru
---

# BMAD Documentation Index

## Базис и Надстройка - Симулятор Развития Общества

**Документация по методологии [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)**

---

## Quick Start

```bash
cd /home/user/game
python3 main.py
```

---

## Documentation Structure

```
docs/bmad/
├── index.md                    # Этот файл (навигация)
├── project-brief.md            # Краткое описание проекта
├── PRD.md                      # Product Requirements Document
├── architecture.md             # Архитектурный документ
├── epics-and-stories.md        # Эпики и пользовательские истории
├── tech-specs/
│   └── data-models.md          # Модели данных
├── research/                   # Исследования для разработки
│   ├── agent-simulations.md    # Агентные симуляции и Game AI
│   └── marxism-guide.md        # Марксизм: теория и примеры
└── stories/                    # Отдельные story файлы (для SM)
```

---

## Documents Overview

### Planning Documents

| Document | Description | Audience |
|----------|-------------|----------|
| [Project Brief](project-brief.md) | Краткое описание проекта, цели, scope | PM, Stakeholders |
| [PRD](PRD.md) | Полные требования: FR, NFR, constraints | PM, Dev, QA |

### Architecture Documents

| Document | Description | Audience |
|----------|-------------|----------|
| [Architecture](architecture.md) | Техническая архитектура, компоненты, потоки | Architect, Dev |
| [Data Models](tech-specs/data-models.md) | Структуры данных, enums, relationships | Dev |

### Development Documents

| Document | Description | Audience |
|----------|-------------|----------|
| [Epics & Stories](epics-and-stories.md) | Backlog с user stories в Gherkin формате | SM, Dev, QA |

### Research Documents

| Document | Description | Audience |
|----------|-------------|----------|
| [Agent Simulations](research/agent-simulations.md) | Исследование агентных симуляций, Game AI, BDI, Generative Agents | Dev, Architect |
| [Marxism Guide](research/marxism-guide.md) | Марксистская теория с примерами для моделирования | Dev, Architect, PM |

---

## Project Summary

### What is This?

Агентная симуляция развития общества, основанная на марксистской теории:
- **Базис** (экономика) определяет **надстройку** (культуру)
- Классы **возникают** из отношений собственности
- NPC — **автономные агенты** с памятью и BDI-архитектурой

### Key Features

- **Emergent Systems**: Классы и культура не задаются, а возникают
- **BDI Architecture**: Beliefs-Desires-Intentions для NPC
- **Generative Agents**: Memory Stream, Reflection, Planning
- **Marxist Model**: Производительные силы → Производственные отношения → Надстройка

### Tech Stack

- **Language**: Python 3.11+
- **Architecture**: Event-Driven, Multi-Agent Simulation
- **Patterns**: Observer, Strategy, Factory, BDI
- **Dependencies**: None (core)

---

## Development Status

### Completed (MVP)

- [x] Core simulation loop
- [x] Event system (60+ event types)
- [x] World & map (40x40 grid)
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

### Planned

- [ ] Full BDI integration in main loop
- [ ] Class conflicts
- [ ] Graphics (pygame)
- [ ] Save/Load
- [ ] Statistics & charts
- [ ] LLM integration (optional)

---

## Architecture Overview

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

### Marxist Update Order

**Critical Design Decision**: Базис обновляется ПЕРЕД надстройкой!

```
Economy (production, property, technology)
    ↓
Society (family, demography, classes)
    ↓
Culture (beliefs, traditions, norms)
    ↓
NPC Actions (BDI cycle)
```

---

## Key Concepts

### Emergent Systems

В отличие от традиционных игр, где классы и культура **задаются** программистом:

| Traditional | This Project |
|-------------|--------------|
| Classes are predefined | Classes EMERGE from property relations |
| Culture is decoration | Culture FORMS from economic conditions |
| NPC follow scripts | NPC are autonomous agents |
| History is scripted | History generates itself |

### BDI Architecture

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

### Memory System (Generative Agents)

- **Memory Stream**: Все события в жизни NPC
- **Reflection**: Выводы из опыта ("Иван часто помогает — он друг")
- **Retrieval**: Поиск релевантных воспоминаний
- **Planning**: Планирование на основе памяти

---

## BMAD Methodology

This documentation follows the [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) — Breakthrough Method for Agile AI-Driven Development.

### BMAD Principles Used

1. **PRD with FR/NFR**: Functional & Non-Functional Requirements
2. **Architecture-First**: Design before coding
3. **Epics & Stories**: Gherkin-style acceptance criteria
4. **Emergent Planning**: Documentation as source of truth

### BMAD Agents Simulated

| Agent | Document |
|-------|----------|
| Analyst | project-brief.md |
| PM | PRD.md |
| Architect | architecture.md |
| SM | epics-and-stories.md |
| Dev | (implementation) |

---

## Contributing

### Code Style

- Type hints required
- Docstrings for public methods
- Max line length: 100

### Documentation Style

- Markdown with tables
- Gherkin for acceptance criteria
- Diagrams in ASCII

---

## Resources

### External - BMAD

- [BMAD-METHOD GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [BMAD Documentation](https://docs.bmad-method.org/)

### External - Agent Simulations

- [Generative Agents (Stanford)](https://arxiv.org/abs/2304.03442) — Memory Stream, Reflection, Planning
- [BDI Agents: From Theory to Practice](https://cdn.aaai.org/ICMAS/1995/ICMAS95-042.pdf) — BDI Architecture
- [Simulation Principles from Dwarf Fortress](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter41_Simulation_Principles_from_Dwarf_Fortress.pdf) — Emergent Narrative
- [The Genius AI Behind The Sims](https://gmtk.substack.com/p/the-genius-ai-behind-the-sims) — Utility AI

### External - Marxism

- [Base and superstructure - Wikipedia](https://en.wikipedia.org/wiki/Base_and_superstructure)
- [Historical materialism - Wikipedia](https://en.wikipedia.org/wiki/Historical_materialism)
- [Chris Harman: Base and Superstructure](https://www.marxists.org/archive/harman/1986/xx/base-super.html)
- [Marx's Capital, Volume 1](https://www.marxists.org/archive/marx/works/1867-c1/)

### Internal

- [Main README](/home/user/game/README.md)
- [Detailed Architecture](/home/user/game/docs/README.md)

---

*Last updated: 2026-01-31*
