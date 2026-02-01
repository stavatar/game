---
title: Живой Мир
description: Симулятор деревни с уникальными NPC
keywords:
  - игра
  - симулятор
  - NPC
  - деревня
  - AI
  - Python
lang: ru
---

# Живой Мир

Симулятор деревни с уникальными NPC, где каждый житель - настоящая личность со своим характером, потребностями и целями.

## Особенности

### Уникальные NPC
Каждый житель имеет:
- **Личность** - набор черт характера (экстраверт/интроверт, дружелюбный/враждебный, трудолюбивый/ленивый и др.)
- **Характеристики** - сила, ловкость, интеллект, харизма и другие
- **Навыки** - торговля, ремесло, бой, медицина и др.
- **Потребности** - голод, сон, общение, развлечения
- **Цели и мечты** - накопить богатство, найти любовь, стать мастером
- **Отношения** - друзья, враги, романтические интересы

### Живой мир
- Симуляция времени (день/ночь, сезоны, погода)
- NPC самостоятельно принимают решения на основе своих потребностей и личности
- Социальные взаимодействия развивают отношения между NPC
- Профессии влияют на распорядок дня и навыки

### AI поведения
- Потребности определяют приоритеты действий
- Личность влияет на выбор между вариантами
- NPC запоминают события и других персонажей
- Отношения развиваются через взаимодействия

## Запуск

```bash
python ./main.py
```

## Управление

В игре доступны команды:
1. Пропустить час симуляции
2. Пропустить день
3. Посмотреть список жителей
4. Посмотреть локации
5. Информация о конкретном NPC
6. Информация о локации
7. Последние события
8. Авто-симуляция
9. Социальная сеть (кто с кем дружит)
0. Выход

## Структура проекта

```
./src/
├── npc/
│   ├── character.py     # Класс NPC
│   ├── personality.py   # Черты характера
│   ├── needs.py         # Система потребностей
│   └── relationships.py # Отношения между NPC
├── world/
│   ├── location.py      # Локации
│   ├── world.py         # Игровой мир
│   └── time_system.py   # Система времени
├── ai/
│   └── behavior.py      # AI принятия решений
├── game/
│   └── engine.py        # Игровой движок
└── data/
    └── names.py         # Генератор имён
```

## Пример вывода

```
=== Лесная Поляна ===
08:00, утро
День 1, месяц 1, год 1, весна
Погода: ясно

Население: 15 жителей

Последние события:
  • Иван заработал 12 монет
  • Мария приятно пообщалась с Анной
  • Пётр пришёл в Таверну
```

## JSON-схемы

### Config (Конфигурация симуляции)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Config",
  "description": "Конфигурация симуляции",
  "type": "object",
  "properties": {
    "world_name": { "type": "string", "default": "Первобытная община" },
    "map_width": { "type": "integer", "default": 50, "minimum": 10 },
    "map_height": { "type": "integer", "default": 50, "minimum": 10 },
    "simulation_speed": { "type": "integer", "enum": [0, 1, 2, 3, 4], "default": 2 },
    "hours_per_day": { "type": "integer", "default": 24 },
    "days_per_month": { "type": "integer", "default": 30 },
    "months_per_year": { "type": "integer", "default": 12 },
    "days_per_season": { "type": "integer", "default": 90 },
    "initial_population": { "type": "integer", "default": 12, "minimum": 1 },
    "initial_families": { "type": "integer", "default": 3, "minimum": 1 },
    "starting_age_min": { "type": "integer", "default": 16 },
    "starting_age_max": { "type": "integer", "default": 45 },
    "max_age": { "type": "integer", "default": 70 },
    "fertility_age_min": { "type": "integer", "default": 16 },
    "fertility_age_max_female": { "type": "integer", "default": 45 },
    "fertility_age_max_male": { "type": "integer", "default": 60 },
    "child_mortality_base": { "type": "number", "default": 0.15, "minimum": 0, "maximum": 1 },
    "resource_regeneration_rate": { "type": "number", "default": 0.1 },
    "resource_depletion_rate": { "type": "number", "default": 0.05 },
    "enable_seasons": { "type": "boolean", "default": true },
    "enable_weather_events": { "type": "boolean", "default": true },
    "enable_climate_change": { "type": "boolean", "default": true },
    "drought_probability": { "type": "number", "default": 0.05 },
    "plague_probability": { "type": "number", "default": 0.02 },
    "primitive_tool_efficiency": { "type": "number", "default": 1.0 },
    "technology_discovery_rate": { "type": "number", "default": 0.01 },
    "knowledge_transfer_rate": { "type": "number", "default": 0.1 },
    "enable_property": { "type": "boolean", "default": true },
    "enable_classes": { "type": "boolean", "default": true },
    "enable_conflicts": { "type": "boolean", "default": true },
    "rebellion_threshold": { "type": "number", "default": 0.7 },
    "enable_beliefs": { "type": "boolean", "default": true },
    "enable_traditions": { "type": "boolean", "default": true },
    "belief_influence_on_behavior": { "type": "number", "default": 0.3 },
    "event_detail_level": { "type": "integer", "enum": [1, 2, 3], "default": 3 },
    "show_map": { "type": "boolean", "default": true },
    "show_social_structure": { "type": "boolean", "default": true },
    "show_relationships": { "type": "boolean", "default": true }
  }
}
```

### SaveFile (Файл сохранения)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SaveFile",
  "description": "Формат файла сохранения симуляции",
  "type": "object",
  "required": ["version", "timestamp", "config", "world", "npcs", "time"],
  "properties": {
    "version": { "type": "string", "description": "Версия формата сохранения" },
    "timestamp": { "type": "string", "format": "date-time", "description": "Дата/время сохранения" },
    "config": { "$ref": "#/definitions/Config", "description": "Конфигурация симуляции" },
    "world": {
      "type": "object",
      "description": "Состояние мира",
      "properties": {
        "name": { "type": "string" },
        "locations": { "type": "array", "items": { "$ref": "#/definitions/Location" } },
        "resources": { "type": "object" }
      }
    },
    "npcs": {
      "type": "array",
      "description": "Список всех NPC",
      "items": { "$ref": "#/definitions/NPC" }
    },
    "time": {
      "type": "object",
      "description": "Состояние игрового времени",
      "properties": {
        "day": { "type": "integer", "minimum": 1 },
        "month": { "type": "integer", "minimum": 1 },
        "year": { "type": "integer", "minimum": 1 },
        "hour": { "type": "integer", "minimum": 0, "maximum": 23 },
        "season": { "type": "string", "enum": ["весна", "лето", "осень", "зима"] }
      }
    },
    "events": {
      "type": "array",
      "description": "История событий",
      "items": { "type": "object" }
    }
  },
  "definitions": {
    "Config": { "type": "object", "description": "См. схему Config выше" },
    "Location": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "type": { "type": "string" },
        "x": { "type": "integer" },
        "y": { "type": "integer" }
      }
    },
    "NPC": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "age": { "type": "integer" },
        "gender": { "type": "string", "enum": ["male", "female"] },
        "personality": { "type": "object" },
        "needs": { "type": "object" },
        "skills": { "type": "object" },
        "relationships": { "type": "array" },
        "location_id": { "type": "string" }
      }
    }
  }
}
```

## Развитие

Идеи для развития:
- Графический интерфейс (pygame)
- Система квестов и событий
- Экономика и торговля
- Браки и рождение детей
- Случайные события (праздники, бедствия)
- Сохранение/загрузка мира
