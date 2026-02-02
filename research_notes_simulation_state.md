# Research Notes: Current Simulation State Analysis

## Task: subtask-1-1 - Analyze Current Simulation State

**Date**: 2026-02-02
**Files Analyzed**:
- `./src/core/simulation.py` - Main simulation loop
- `./src/core/events.py` - Event system
- `./src/core/config.py` - Simulation configuration

---

## Part 1: Simulation Update Cycle Order

### Actual Implementation Order (from Simulation.update() method)

The simulation follows a Marxist materialist architecture where the **basis (economic foundation) determines the superstructure (culture and ideology)**. However, the actual implementation order differs slightly from the conceptual spec.

**ACTUAL UPDATE CYCLE (5 phases per hour, with daily and yearly sub-cycles):**

```
┌─────────────────────────────────────────────────────────────────┐
│ EACH HOUR / SIMULATION TICK                                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. TIME & CLIMATE (Environmental Foundation)                    │
│    - Increment hour counter (1/24 day)                          │
│    - Update day/month/year when appropriate                     │
│    - ONCE PER DAY: Update climate and weather                   │
│                                                                  │
│ 2. BASIS/ECONOMICS (Marxist Base)                              │
│    - Update production (influenced by season from climate)      │
│    - Track resources and production output                      │
│    - ONCE PER DAY: Process class conflicts and relations        │
│                                                                  │
│ 3. NPC ACTIONS (Agency within Economic Structure)              │
│    - Each NPC decides action based on:                         │
│      * Economic situation (needs, resources)                   │
│      * Environmental conditions (terrain, climate)             │
│      * Beliefs and personality                                 │
│    - Actions: gather, craft, claim land, trade property        │
│                                                                  │
│ 4. SUPERSTRUCTURE/CULTURE (Marxist Superstructure)             │
│    - ONCE PER DAY: Update beliefs, traditions, norms           │
│    - Beliefs emerge from economic base                         │
│    - Culture reflects class positions                          │
│                                                                  │
│ 5. DEMOGRAPHY (Population and Life Cycles)                     │
│    - ONCE PER DAY: Handle births and deaths                    │
│    - NPC aging and need satisfaction                           │
│    - Life expectancy checks                                    │
│                                                                  │
│ ONCE PER YEAR:                                                  │
│    - Process yearly updates (not detailed yet)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Insight: Phase Organization

- **Hourly**: TIME increment + NPC ACTIONS run every hour
- **Daily**: CLIMATE, ECONOMICS, CULTURE, DEMOGRAPHY run daily
- **Yearly**: Specific year-end processing

### Comparison with Spec vs Reality

| Aspect | Conceptual Order (Spec) | Actual Code Order | Notes |
|--------|------------------------|-------------------|-------|
| TIME | First (logical) | 1st (integrated with climate) | ✓ Correct |
| ECONOMY | 2nd | 2nd | ✓ Correct |
| SOCIETY | 3rd | 5th (part of demography) | Mixed: class calculations are in economy step |
| CULTURE | 4th | 4th | ✓ Correct |
| NPC | 5th | 3rd | Different: NPCs act between economics and culture |
| CLIMATE | 6th | 1st | Different: Climate is foundational environment |

### Current Implementation Discrepancy

The spec mentions: `TIME→ECONOMY→SOCIETY→CULTURE→NPC→CLIMATE`

But the code implements: `TIME+CLIMATE→ECONOMY→NPC→CULTURE→DEMOGRAPHY`

**Reasoning in Code Comments:**
> "По Марксу: базис определяет надстройку, поэтому экономика обновляется ДО культуры. NPC действуют в рамках экономической структуры, а культурные изменения следуют за их действиями."
>
> Translation: "According to Marx: the basis determines the superstructure, therefore economics is updated BEFORE culture. NPCs act within the economic structure, and cultural changes follow their actions."

---

## Part 2: Event System Architecture

### EventType Enum (24 distinct event types)

The event system uses a publish-subscribe pattern with the following event categories:

#### 1. **Life Cycle Events** (3 types)
- `NPC_BORN` - NPC is created
- `NPC_DIED` - NPC dies
- `NPC_AGED` - NPC ages (birthday milestone)

#### 2. **Family Events** (3 types)
- `MARRIAGE` - Two NPCs marry
- `DIVORCE` - Spouses separate
- `CHILD_BORN` - Child is born to parents

#### 3. **Economic Events** (5 types)
- `RESOURCE_GATHERED` - Resource collected from environment
- `RESOURCE_DEPLETED` - Resource exhausted
- `RESOURCE_REGENERATED` - Resource restored
- `ITEM_CRAFTED` - Item created through production
- `TRADE_COMPLETED` - Trade transaction between NPCs

#### 4. **Property Events** (3 types)
- `PROPERTY_CLAIMED` - NPC claims new property
- `PROPERTY_TRANSFERRED` - Property ownership changes
- `PROPERTY_LOST` - Property is removed/destroyed

#### 5. **Technology Events** (3 types)
- `TECHNOLOGY_DISCOVERED` - New technology invented
- `KNOWLEDGE_TRANSFERRED` - Technology taught to NPC
- `TOOL_CREATED` - Tool made from technology

#### 6. **Social Events** (8 types)
- `CLASS_EMERGED` - New social class forms
- `RELATIONSHIP_CHANGED` - Relationship between NPCs shifts
- `CONFLICT_STARTED` - Class conflict begins
- `CONFLICT_ESCALATED` - Conflict intensifies
- `CONFLICT_RESOLVED` - Conflict ends
- `REBELLION` - Uprising/revolution occurs
- `CONSCIOUSNESS_SPREAD` - Class consciousness transmitted
- `INTELLECTUAL_EMERGED` - Organic intellectual appears

#### 7. **Cultural Events** (4 types)
- `BELIEF_FORMED` - New belief emerges
- `TRADITION_CREATED` - New tradition established
- `NORM_ESTABLISHED` - Social norm created
- `RITUAL_PERFORMED` - Ritual conducted

#### 8. **Climate Events** (5 types)
- `SEASON_CHANGED` - Season transitions
- `WEATHER_EVENT` - Weather changes
- `DROUGHT` - Drought conditions
- `PLAGUE` - Disease outbreak
- `FAMINE` - Food shortage

#### 9. **Time Events** (4 types)
- `DAY_PASSED` - One day completed
- `MONTH_PASSED` - One month completed
- `YEAR_PASSED` - One year completed
- `GENERATION_PASSED` - Generational change

### Event Importance Levels

Events have 6 importance levels affecting storage and visibility:

```python
EventImportance.TRIVIAL   = 1  # Routine actions
EventImportance.MINOR     = 2  # Minor events
EventImportance.NOTABLE   = 3  # Noteworthy events
EventImportance.IMPORTANT = 4  # Important events
EventImportance.MAJOR     = 5  # Significant events
EventImportance.HISTORIC  = 6  # Historical turning points
```

### Event Data Structure

Each event contains:
```
- event_type: EventType (what happened)
- importance: EventImportance (how significant)
- year, month, day, hour: Timing information
- location_id, x, y: Location coordinates
- actor_id: Who performed the action
- target_id: Who/what was affected
- witness_ids: Who observed the event
- data: Dictionary of event-specific data
- description: Human-readable text
- description_template: Template with placeholders
- id: Unique identifier
- timestamp: Unix timestamp
- caused_by: ID of causal event
- causes: IDs of consequent events
```

### EventBus Implementation

The system uses a **Publisher-Subscriber pattern**:

```python
class EventBus:
    # Subscribe to specific event types
    subscribe(event_type: EventType, callback: Callable)

    # Subscribe to all events
    subscribe_all(callback: Callable)

    # Unsubscribe
    unsubscribe(event_type: EventType, callback: Callable)

    # Publish event to all subscribers
    publish(event: Event)

    # Query historical events with filters
    get_history(event_type, min_importance, actor_id, limit)

    # Get only historic events
    get_historic_events(limit)

    # Clear non-historic events
    clear_history()
```

### Event History Management

- **Max History**: 10,000 events stored
- **Auto-pruning**: When limit exceeded, older trivial events are discarded but historic events (MAJOR, HISTORIC) are preserved
- **Query filtering**: By type, importance, actor, with configurable limit
- **Causal chains**: Events track what caused them and what they caused

### Helper Functions for Event Creation

The module includes factory functions for common event types:

```python
create_birth_event(npc_id, mother_id, father_id, year, location_id)
create_death_event(npc_id, cause, age, year, location_id)
create_technology_event(discoverer_id, tech_name, year, location_id)
create_class_emergence_event(class_name, members, year)
create_conflict_started_event(conflict_id, type, oppressed, ruling, cause, year)
create_conflict_escalated_event(conflict_id, new_stage, new_type, intensity, year)
create_conflict_resolved_event(conflict_id, outcome, consequences, year)
create_consciousness_spread_event(from_npc_id, to_npc_id, class, amount, year)
create_intellectual_emerged_event(npc_id, class_name, year)
create_rebellion_event(leader_ids, oppressed_class, participant_count, year)
```

---

## Part 3: Configuration System

### Configuration Files

The `Config` class (in config.py) provides comprehensive settings:

#### World Settings
- `world_name`: Name of the simulated world
- `map_width`, `map_height`: Map dimensions in cells

#### Time Settings
- `simulation_speed`: PAUSED, SLOW, NORMAL, FAST, VERY_FAST
- `hours_per_day`: Default 24
- `days_per_month`: Default 30
- `months_per_year`: Default 12
- `days_per_season`: Default 90

#### Population Settings
- `initial_population`: Starting NPC count (default 12)
- `initial_families`: Starting family groups (default 3)
- `starting_age_min/max`: Age range of initial NPCs (16-45)

#### Demographic Settings
- `max_age`: Life expectancy (default 70)
- `fertility_age_min/max`: Reproductive age ranges
- `child_mortality_base`: Base child death rate (default 0.15 = 15%)

#### Climate Settings
- `enable_seasons`: Enable seasonal cycles
- `enable_weather_events`: Enable catastrophes
- `enable_climate_change`: Enable long-term climate shifts
- `drought_probability`: Annual drought chance
- `plague_probability`: Annual plague chance

#### Economic Settings
- `primitive_tool_efficiency`: Tool effectiveness multiplier
- `technology_discovery_rate`: Chance of tech discovery per work-day
- `knowledge_transfer_rate`: Learning/teaching speed

#### Social Settings
- `enable_property`: Allow property ownership
- `enable_classes`: Allow class emergence
- `enable_conflicts`: Allow class conflicts
- `rebellion_threshold`: Dissatisfaction level for uprising

#### Cultural Settings
- `enable_beliefs`: Allow belief systems
- `enable_traditions`: Allow tradition formation
- `belief_influence_on_behavior`: How much beliefs affect NPC behavior (0-1 scale)

#### Presets

Three preset configurations provided:
- **PRESET_REALISTIC**: Slow tech, high mortality, short lifespan
- **PRESET_ACCELERATED**: Fast tech discovery, moderate mortality
- **PRESET_SANDBOX**: Very fast simulation, no climate events, low mortality

---

## Part 4: Key Architectural Insights

### 1. Marxist Base-Superstructure Implementation

The simulation explicitly implements the Marxist materialist concept:

```
BASIS (Foundation)          SUPERSTRUCTURE (Ideological)
├── Production              ├── Beliefs
├── Property ownership      ├── Traditions
├── Class structure         ├── Norms
└── Resources              └── Ideology/Consciousness

Flow: Economics → Determines → Culture
```

The code comments confirm this philosophy is intentional, not accidental.

### 2. Time Granularity Hierarchy

```
1 Hour     → NPC actions, basic time advancement
1 Day      → Climate, economics, culture, demography cycles
1 Month    → Implicit (tracked but not specifically processed)
1 Year     → Special yearly updates
```

### 3. Event-Driven System

Not all changes are directly calculated - many are event-triggered:
- Death of an NPC triggers cascading updates (inheritance, class recalculation, etc.)
- Property changes affect class membership
- Class changes affect consciousness and ideology

### 4. Current State vs. Planned State

The code indicates areas for future development:
- `enable_classes`, `enable_conflicts` flags suggest these systems are optional/incomplete
- Event system capacity limited to 10K events (mentions INT-040, INT-019, INT-022 in comments - these are from Task 002)
- Comments reference "Generative Agents" and "SNLT" (Socially Necessary Labour Time) improvements

---

## Part 5: Connections to Task 002 Issues

Several Task 002 EPIC improvements are referenced:

1. **INT-022**: Consistency validation checks
2. **INT-040**: Emergence tracking (commented in superstructure update)
3. **INT-019**: Dialectical contradictions (mentioned in contradictions tracking)

These features are partially implemented but need expansion.

---

## Summary for Documentation

When creating the `SIMULATION_CORE.md` document, it should:

1. **Show the actual update cycle**, not the spec cycle
2. **Explain why it differs**: TIME+CLIMATE are foundational environment, NPC acts between economics and culture per Marxist logic
3. **Document the EventBus pattern** in detail with all 24 event types
4. **Include code example** showing the update() method structure
5. **List all event importance levels** and their meanings
6. **Show configuration presets** and how they modify simulation behavior
7. **Highlight the Marxist philosophy** embedded in the code
8. **Note current limitations** that Task 002 will address

---

## Files for Future Reference

- **Source**: `./src/core/simulation.py` (lines 902-994 for main update loop)
- **Events**: `./src/core/events.py` (complete event system)
- **Config**: `./src/core/config.py` (all configurable parameters)

---

**Status**: ✓ Research Complete - Ready for Documentation Phase

