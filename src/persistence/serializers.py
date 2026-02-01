"""
Сериализаторы для различных компонентов симуляции.

Каждый сериализатор преобразует:
- Объект -> Dict (для сохранения)
- Dict -> Объект (для загрузки)
"""
from dataclasses import asdict, fields
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..core.simulation import Simulation, NPCState
    from ..core.config import Config
    from ..world.map import WorldMap, Position
    from ..society.classes import ClassSystem, SocialClass, ClassConflict


class BaseSerializer:
    """Базовый класс для сериализаторов"""

    @staticmethod
    def enum_to_str(value: Enum) -> str:
        """Преобразует Enum в строку"""
        return value.name if value else None

    @staticmethod
    def str_to_enum(value: str, enum_class: type) -> Optional[Enum]:
        """Преобразует строку в Enum"""
        if not value:
            return None
        try:
            return enum_class[value]
        except KeyError:
            return None


class ConfigSerializer(BaseSerializer):
    """Сериализатор конфигурации"""

    @staticmethod
    def serialize(config: 'Config') -> Dict[str, Any]:
        """Сериализует конфигурацию"""
        return {
            "initial_population": config.initial_population,
            "initial_families": config.initial_families,
            "map_width": config.map_width,
            "map_height": config.map_height,
            "starting_age_min": config.starting_age_min,
            "starting_age_max": config.starting_age_max,
            "days_per_month": config.days_per_month,
            "hours_per_day": config.hours_per_day,
        }

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> 'Config':
        """Десериализует конфигурацию"""
        from ..core.config import Config
        return Config(
            initial_population=data.get("initial_population", 12),
            initial_families=data.get("initial_families", 3),
            map_width=data.get("map_width", 50),
            map_height=data.get("map_height", 50),
            starting_age_min=data.get("starting_age_min", 16),
            starting_age_max=data.get("starting_age_max", 35),
            days_per_month=data.get("days_per_month", 30),
            hours_per_day=data.get("hours_per_day", 24),
        )


class NPCSerializer(BaseSerializer):
    """Сериализатор NPC"""

    @staticmethod
    def serialize(npc: 'NPCState') -> Dict[str, Any]:
        """Сериализует NPC"""
        return {
            "id": npc.id,
            "name": npc.name,
            "age": npc.age,
            "is_female": npc.is_female,
            "is_alive": npc.is_alive,
            "position": {"x": npc.position.x, "y": npc.position.y},
            "health": npc.health,
            "hunger": npc.hunger,
            "energy": npc.energy,
            "happiness": npc.happiness,
            "skills": npc.skills,
            "traits": npc.traits,
            "intelligence": npc.intelligence,
            "family_id": npc.family_id,
            "spouse_id": npc.spouse_id,
            "inventory": NPCSerializer._serialize_inventory(npc.inventory),
        }

    @staticmethod
    def _serialize_inventory(inventory) -> Dict[str, Any]:
        """Сериализует инвентарь"""
        if not inventory:
            return {"owner_id": "", "resources": {}, "capacity": 100.0}

        resources = {}
        for resource_type, resource in inventory.resources.items():
            resources[resource_type.name] = {
                "quantity": resource.quantity,
                "quality": resource.quality,
                "creator_id": resource.creator_id,
                "creation_year": resource.creation_year,
            }

        return {
            "owner_id": inventory.owner_id,
            "resources": resources,
            "capacity": inventory.capacity,
        }

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> 'NPCState':
        """Десериализует NPC"""
        from ..core.simulation import NPCState
        from ..world.map import Position
        from ..economy.resources import Inventory, Resource, ResourceType

        # Позиция
        pos_data = data.get("position", {"x": 25, "y": 25})
        position = Position(x=pos_data["x"], y=pos_data["y"])

        # NPC
        npc = NPCState(
            id=data["id"],
            name=data["name"],
            age=data["age"],
            is_female=data["is_female"],
            is_alive=data.get("is_alive", True),
            position=position,
            health=data.get("health", 100.0),
            hunger=data.get("hunger", 0.0),
            energy=data.get("energy", 100.0),
            happiness=data.get("happiness", 50.0),
            skills=data.get("skills", {}),
            traits=data.get("traits", []),
            intelligence=data.get("intelligence", 10),
            family_id=data.get("family_id"),
            spouse_id=data.get("spouse_id"),
        )

        # Инвентарь
        inv_data = data.get("inventory", {})
        if inv_data:
            npc.inventory = Inventory(
                owner_id=inv_data.get("owner_id", npc.id),
                capacity=inv_data.get("capacity", 100.0)
            )
            for resource_name, res_data in inv_data.get("resources", {}).items():
                try:
                    resource_type = ResourceType[resource_name]
                    resource = Resource(
                        resource_type=resource_type,
                        quantity=res_data["quantity"],
                        quality=res_data.get("quality", 1.0),
                        creator_id=res_data.get("creator_id"),
                        creation_year=res_data.get("creation_year", 0),
                    )
                    npc.inventory.resources[resource_type] = resource
                except KeyError:
                    pass  # Неизвестный тип ресурса

        return npc


class MapSerializer(BaseSerializer):
    """Сериализатор карты мира"""

    @staticmethod
    def serialize(world_map: 'WorldMap') -> Dict[str, Any]:
        """Сериализует карту"""
        tiles_data = {}
        for (x, y), tile in world_map.tiles.items():
            key = f"{x},{y}"
            tiles_data[key] = {
                "terrain": tile.terrain.name,
                "elevation": tile.elevation,
                "moisture": tile.moisture,
            }

        return {
            "width": world_map.width,
            "height": world_map.height,
            "seed": world_map.seed,
            "tiles": tiles_data,
        }

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> 'WorldMap':
        """Десериализует карту"""
        from ..world.map import WorldMap
        from ..world.terrain import Tile, TerrainType

        # Создаём карту с тем же seed
        world_map = WorldMap(
            width=data["width"],
            height=data["height"],
            seed=data.get("seed", 0),
        )

        # Восстанавливаем модифицированные тайлы
        for key, tile_data in data.get("tiles", {}).items():
            try:
                x, y = map(int, key.split(","))
                terrain = TerrainType[tile_data["terrain"]]

                if (x, y) in world_map.tiles:
                    world_map.tiles[(x, y)].terrain = terrain
                    world_map.tiles[(x, y)].elevation = tile_data.get("elevation", 0.5)
                    world_map.tiles[(x, y)].moisture = tile_data.get("moisture", 0.5)
            except (ValueError, KeyError):
                pass

        return world_map


class ClassSerializer(BaseSerializer):
    """Сериализатор системы классов"""

    @staticmethod
    def serialize(class_system: 'ClassSystem') -> Dict[str, Any]:
        """Сериализует систему классов"""
        from ..society.classes import ClassType

        # Классы
        classes_data = {}
        for class_type, social_class in class_system.classes.items():
            classes_data[class_type.name] = {
                "members": list(social_class.members),
                "avg_wealth": social_class.avg_wealth,
                "avg_property": social_class.avg_property,
                "political_power": social_class.political_power,
                "class_consciousness": social_class.class_consciousness,
            }

        # NPC -> класс
        npc_classes = {
            npc_id: class_type.name
            for npc_id, class_type in class_system.npc_class.items()
        }

        # Конфликты
        conflicts_data = []
        for conflict in class_system.conflicts:
            conflicts_data.append({
                "id": conflict.id,
                "conflict_type": conflict.conflict_type.name,
                "oppressed_class": conflict.oppressed_class.name,
                "ruling_class": conflict.ruling_class.name,
                "stage": conflict.stage.name,
                "intensity": conflict.intensity,
                "violence_level": conflict.violence_level,
                "organization_level": conflict.organization_level,
                "primary_cause": conflict.primary_cause,
                "grievances": conflict.grievances,
                "demands": conflict.demands,
                "year_started": conflict.year_started,
                "days_active": conflict.days_active,
                "resolved": conflict.resolved,
                "outcome": conflict.outcome.name if conflict.outcome else None,
                "participants": {
                    npc_id: ct.name
                    for npc_id, ct in conflict.participants.items()
                },
                "leaders": conflict.leaders,
            })

        # Органические интеллектуалы
        intellectuals = list(class_system.consciousness_system.organic_intellectuals)

        return {
            "classes": classes_data,
            "npc_classes": npc_classes,
            "conflicts": conflicts_data,
            "classes_emerged": class_system.classes_emerged,
            "first_class_year": class_system.first_class_year,
            "conflict_cooldown": class_system.conflict_cooldown,
            "organic_intellectuals": intellectuals,
        }

    @staticmethod
    def deserialize(data: Dict[str, Any], class_system: 'ClassSystem') -> None:
        """Десериализует систему классов (in-place)"""
        from ..society.classes import (
            ClassType, SocialClass, ClassConflict,
            ConflictType, ConflictStage, ConflictOutcome
        )

        # Очищаем
        class_system.classes.clear()
        class_system.npc_class.clear()
        class_system.conflicts.clear()

        # Классы
        for class_name, class_data in data.get("classes", {}).items():
            try:
                class_type = ClassType[class_name]
                social_class = SocialClass(
                    class_type=class_type,
                    members=set(class_data.get("members", [])),
                    avg_wealth=class_data.get("avg_wealth", 0.0),
                    avg_property=class_data.get("avg_property", 0.0),
                    political_power=class_data.get("political_power", 0.0),
                    class_consciousness=class_data.get("class_consciousness", 0.0),
                )
                class_system.classes[class_type] = social_class
            except KeyError:
                pass

        # NPC -> класс
        for npc_id, class_name in data.get("npc_classes", {}).items():
            try:
                class_system.npc_class[npc_id] = ClassType[class_name]
            except KeyError:
                pass

        # Конфликты
        for conflict_data in data.get("conflicts", []):
            try:
                conflict = ClassConflict(
                    id=conflict_data["id"],
                    conflict_type=ConflictType[conflict_data["conflict_type"]],
                    oppressed_class=ClassType[conflict_data["oppressed_class"]],
                    ruling_class=ClassType[conflict_data["ruling_class"]],
                    stage=ConflictStage[conflict_data["stage"]],
                    intensity=conflict_data.get("intensity", 0.1),
                    violence_level=conflict_data.get("violence_level", 0.0),
                    organization_level=conflict_data.get("organization_level", 0.0),
                    primary_cause=conflict_data.get("primary_cause", ""),
                    grievances=conflict_data.get("grievances", []),
                    demands=conflict_data.get("demands", []),
                    year_started=conflict_data.get("year_started", 0),
                    days_active=conflict_data.get("days_active", 0),
                    resolved=conflict_data.get("resolved", False),
                    leaders=conflict_data.get("leaders", []),
                )

                # Outcome
                outcome_name = conflict_data.get("outcome")
                if outcome_name:
                    conflict.outcome = ConflictOutcome[outcome_name]

                # Participants
                for npc_id, ct_name in conflict_data.get("participants", {}).items():
                    conflict.participants[npc_id] = ClassType[ct_name]

                class_system.conflicts.append(conflict)
            except KeyError:
                pass

        # Флаги
        class_system.classes_emerged = data.get("classes_emerged", False)
        class_system.first_class_year = data.get("first_class_year", 0)
        class_system.conflict_cooldown = data.get("conflict_cooldown", 0)

        # Интеллектуалы
        intellectuals = data.get("organic_intellectuals", [])
        class_system.consciousness_system.organic_intellectuals = set(intellectuals)


class SimulationSerializer(BaseSerializer):
    """Главный сериализатор симуляции"""

    @staticmethod
    def serialize(simulation: 'Simulation') -> Dict[str, Any]:
        """Сериализует всю симуляцию"""
        from .schema import SaveData, SaveMetadata

        # Метаданные
        era = "Неизвестно"
        if hasattr(simulation, 'knowledge'):
            current_era = simulation.knowledge.get_current_era()
            if current_era:
                era = current_era.russian_name

        metadata = SaveMetadata(
            year=simulation.year,
            population=len([n for n in simulation.npcs.values() if n.is_alive]),
            era=era,
        )

        # Время
        time_data = {
            "year": simulation.year,
            "month": simulation.month,
            "day": simulation.day,
            "hour": simulation.hour,
            "total_days": simulation.total_days,
            "generations": simulation.generations,
        }

        # NPC
        npcs_data = {}
        for npc_id, npc in simulation.npcs.items():
            npcs_data[npc_id] = NPCSerializer.serialize(npc)

        # Экономика
        economy_data = {
            "knowledge": SimulationSerializer._serialize_knowledge(simulation.knowledge),
            "ownership": SimulationSerializer._serialize_ownership(simulation.ownership),
        }

        # Общество
        society_data = {
            "families": SimulationSerializer._serialize_families(simulation.families),
            "classes": ClassSerializer.serialize(simulation.classes),
        }

        # Культура
        culture_data = {
            "beliefs": SimulationSerializer._serialize_beliefs(simulation.beliefs),
        }

        # Собираем данные
        save_data = SaveData(
            metadata=metadata,
            config=ConfigSerializer.serialize(simulation.config),
            time=time_data,
            map_data=MapSerializer.serialize(simulation.map),
            npcs=npcs_data,
            economy=economy_data,
            society=society_data,
            culture=culture_data,
            events=simulation.event_log[-100:],  # Последние 100 событий
        )

        # Вычисляем checksum
        save_data.metadata.checksum = save_data.calculate_checksum()

        return save_data.to_dict()

    @staticmethod
    def _serialize_knowledge(knowledge) -> Dict[str, Any]:
        """Сериализует систему знаний"""
        return {
            "discovered_technologies": list(knowledge.discovered_technologies),
            "npc_knowledge": {
                npc_id: list(techs)
                for npc_id, techs in knowledge.npc_knowledge.items()
            },
        }

    @staticmethod
    def _serialize_ownership(ownership) -> Dict[str, Any]:
        """Сериализует систему собственности"""
        properties = {}
        for prop_id, prop in ownership.properties.items():
            properties[prop_id] = {
                "category": prop.category.name,
                "owner_type": prop.owner_type.name,
                "owner_id": prop.owner_id,
                "location": list(prop.location) if prop.location else None,
                "area": prop.area,
                "value": prop.value,
                "acquisition_year": prop.acquisition_year,
                "acquisition_method": prop.acquisition_method,
            }

        return {
            "properties": properties,
            "private_property_emerged": ownership.private_property_emerged,
            "emergence_year": ownership.emergence_year,
        }

    @staticmethod
    def _serialize_families(families) -> Dict[str, Any]:
        """Сериализует систему семей"""
        families_data = {}
        for family_id, family in families.families.items():
            families_data[family_id] = {
                "name": family.name,
                "members": list(family.members),
                "founder_id": family.founder_id,
                "head_id": family.head_id,
                "year_formed": family.year_formed,
            }

        return {
            "families": families_data,
            "marriages": [
                {"partner1": m[0], "partner2": m[1], "year": m[2]}
                for m in families.marriages
            ],
        }

    @staticmethod
    def _serialize_beliefs(beliefs) -> Dict[str, Any]:
        """Сериализует систему верований"""
        beliefs_data = {}
        for belief_id, belief in beliefs.beliefs.items():
            beliefs_data[belief_id] = {
                "name": belief.name,
                "description": belief.description,
                "adherents": list(belief.adherents),
            }

        return {
            "beliefs": beliefs_data,
            "npc_beliefs": {
                npc_id: list(b)
                for npc_id, b in beliefs.npc_beliefs.items()
            },
        }

    @staticmethod
    def deserialize(data: Dict[str, Any], simulation: 'Simulation') -> None:
        """Десериализует данные в симуляцию (in-place)"""
        from .schema import SaveData

        save_data = SaveData.from_dict(data)

        # Время
        simulation.year = save_data.time.get("year", 1)
        simulation.month = save_data.time.get("month", 1)
        simulation.day = save_data.time.get("day", 1)
        simulation.hour = save_data.time.get("hour", 6)
        simulation.total_days = save_data.time.get("total_days", 0)
        simulation.generations = save_data.time.get("generations", 1)

        # NPC
        simulation.npcs.clear()
        for npc_id, npc_data in save_data.npcs.items():
            simulation.npcs[npc_id] = NPCSerializer.deserialize(npc_data)

        # Классы
        ClassSerializer.deserialize(
            save_data.society.get("classes", {}),
            simulation.classes
        )

        # Экономика - знания
        knowledge_data = save_data.economy.get("knowledge", {})
        simulation.knowledge.discovered_technologies = set(
            knowledge_data.get("discovered_technologies", [])
        )
        simulation.knowledge.npc_knowledge = {
            npc_id: set(techs)
            for npc_id, techs in knowledge_data.get("npc_knowledge", {}).items()
        }

        # Экономика - собственность
        SimulationSerializer._deserialize_ownership(
            save_data.economy.get("ownership", {}),
            simulation.ownership
        )

        # Общество - семьи
        SimulationSerializer._deserialize_families(
            save_data.society.get("families", {}),
            simulation.families
        )

        # Культура - верования
        SimulationSerializer._deserialize_beliefs(
            save_data.culture.get("beliefs", {}),
            simulation.beliefs
        )

        # События
        simulation.event_log = save_data.events

    @staticmethod
    def _deserialize_ownership(data: Dict[str, Any], ownership) -> None:
        """Десериализует систему собственности"""
        from ..economy.property import PropertyRight, PropertyCategory, PropertyType

        ownership.properties.clear()
        ownership.owner_index.clear()
        ownership.location_index.clear()

        for prop_id, prop_data in data.get("properties", {}).items():
            try:
                prop = PropertyRight(
                    property_id=prop_id,
                    category=PropertyCategory[prop_data["category"]],
                    owner_type=PropertyType[prop_data["owner_type"]],
                    owner_id=prop_data.get("owner_id"),
                    location=tuple(prop_data["location"]) if prop_data.get("location") else None,
                    area=prop_data.get("area", 1.0),
                    value=prop_data.get("value", 0.0),
                    acquisition_year=prop_data.get("acquisition_year", 0),
                    acquisition_method=prop_data.get("acquisition_method", ""),
                )
                ownership.properties[prop_id] = prop

                if prop.owner_id:
                    if prop.owner_id not in ownership.owner_index:
                        ownership.owner_index[prop.owner_id] = set()
                    ownership.owner_index[prop.owner_id].add(prop_id)

                if prop.location:
                    ownership.location_index[prop.location] = prop_id
            except KeyError:
                pass

        ownership.private_property_emerged = data.get("private_property_emerged", False)
        ownership.emergence_year = data.get("emergence_year", 0)

    @staticmethod
    def _deserialize_families(data: Dict[str, Any], families) -> None:
        """Десериализует систему семей"""
        from ..society.family import Family

        families.families.clear()
        families.marriages.clear()

        for family_id, fam_data in data.get("families", {}).items():
            try:
                family = Family(
                    id=family_id,
                    name=fam_data.get("name", ""),
                    founder_id=fam_data.get("founder_id"),
                    head_id=fam_data.get("head_id"),
                    year_formed=fam_data.get("year_formed", 1),
                )
                family.members = set(fam_data.get("members", []))
                families.families[family_id] = family
            except Exception:
                pass

        for marriage in data.get("marriages", []):
            families.marriages.append(
                (marriage["partner1"], marriage["partner2"], marriage["year"])
            )

    @staticmethod
    def _deserialize_beliefs(data: Dict[str, Any], beliefs) -> None:
        """Десериализует систему верований"""
        # Восстанавливаем только adherents и npc_beliefs
        for belief_id, belief_data in data.get("beliefs", {}).items():
            if belief_id in beliefs.beliefs:
                beliefs.beliefs[belief_id].adherents = set(
                    belief_data.get("adherents", [])
                )

        beliefs.npc_beliefs = {
            npc_id: set(b)
            for npc_id, b in data.get("npc_beliefs", {}).items()
        }
