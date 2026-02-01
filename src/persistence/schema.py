"""
Схема данных для сохранений.

Определяет:
- Версию формата
- Структуру метаданных
- Секции сохранения
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import json

# Версия формата сохранения
SAVE_VERSION = "1.0.0"

# Минимальная поддерживаемая версия
MIN_COMPATIBLE_VERSION = "1.0.0"


@dataclass
class SaveMetadata:
    """
    Метаданные сохранения.

    Содержит информацию о сохранении:
    - Версия формата
    - Время создания
    - Краткая статистика
    - Контрольная сумма
    """
    version: str = SAVE_VERSION
    created_at: str = ""
    save_name: str = ""
    description: str = ""

    # Статистика для предпросмотра
    year: int = 0
    population: int = 0
    era: str = ""

    # Целостность
    checksum: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь"""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "save_name": self.save_name,
            "description": self.description,
            "year": self.year,
            "population": self.population,
            "era": self.era,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SaveMetadata':
        """Создаёт из словаря"""
        return cls(
            version=data.get("version", SAVE_VERSION),
            created_at=data.get("created_at", ""),
            save_name=data.get("save_name", ""),
            description=data.get("description", ""),
            year=data.get("year", 0),
            population=data.get("population", 0),
            era=data.get("era", ""),
            checksum=data.get("checksum", ""),
        )


@dataclass
class SaveSection:
    """Секция сохранения"""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SaveData:
    """
    Полные данные сохранения.

    Структура:
    - metadata: информация о сохранении
    - config: конфигурация симуляции
    - time: игровое время
    - map: карта мира
    - npcs: все NPC
    - economy: экономика (собственность, технологии)
    - society: общество (семьи, классы)
    - culture: культура (верования, традиции)
    """
    metadata: SaveMetadata = field(default_factory=SaveMetadata)

    # Секции
    config: Dict[str, Any] = field(default_factory=dict)
    time: Dict[str, Any] = field(default_factory=dict)
    map_data: Dict[str, Any] = field(default_factory=dict)
    npcs: Dict[str, Any] = field(default_factory=dict)
    economy: Dict[str, Any] = field(default_factory=dict)
    society: Dict[str, Any] = field(default_factory=dict)
    culture: Dict[str, Any] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь для JSON"""
        return {
            "metadata": self.metadata.to_dict(),
            "config": self.config,
            "time": self.time,
            "map": self.map_data,
            "npcs": self.npcs,
            "economy": self.economy,
            "society": self.society,
            "culture": self.culture,
            "events": self.events,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SaveData':
        """Создаёт из словаря"""
        return cls(
            metadata=SaveMetadata.from_dict(data.get("metadata", {})),
            config=data.get("config", {}),
            time=data.get("time", {}),
            map_data=data.get("map", {}),
            npcs=data.get("npcs", {}),
            economy=data.get("economy", {}),
            society=data.get("society", {}),
            culture=data.get("culture", {}),
            events=data.get("events", []),
        )

    def calculate_checksum(self) -> str:
        """Вычисляет контрольную сумму данных"""
        # Исключаем metadata из подсчёта (там хранится checksum)
        data_for_hash = {
            "config": self.config,
            "time": self.time,
            "map": self.map_data,
            "npcs": self.npcs,
            "economy": self.economy,
            "society": self.society,
            "culture": self.culture,
        }
        json_str = json.dumps(data_for_hash, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()[:16]

    def verify_checksum(self) -> bool:
        """Проверяет контрольную сумму"""
        if not self.metadata.checksum:
            return True  # Нет checksum - пропускаем проверку
        return self.calculate_checksum() == self.metadata.checksum


def is_version_compatible(version: str) -> bool:
    """Проверяет совместимость версии"""
    try:
        v_parts = [int(x) for x in version.split(".")]
        min_parts = [int(x) for x in MIN_COMPATIBLE_VERSION.split(".")]

        for v, m in zip(v_parts, min_parts):
            if v < m:
                return False
            if v > m:
                return True

        return True
    except (ValueError, AttributeError):
        return False
