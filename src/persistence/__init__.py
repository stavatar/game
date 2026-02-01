"""
Система сохранения и загрузки мира.

Обеспечивает:
- Сохранение состояния симуляции в JSON/gzip
- Загрузку сохранений
- Версионирование формата
- Валидацию данных
- Автосохранение

Источники и best practices:
- https://janakiev.com/blog/python-json/
- https://docs.python-guide.org/scenarios/serialization/
- https://realpython.com/python-serialize-data/
"""
from .save_manager import SaveManager, SaveError, LoadError
from .schema import SaveMetadata, SaveData, SAVE_VERSION
from .serializers import (
    SimulationSerializer,
    NPCSerializer,
    MapSerializer,
    ClassSerializer,
)

__all__ = [
    'SaveManager',
    'SaveError',
    'LoadError',
    'SaveMetadata',
    'SaveData',
    'SAVE_VERSION',
    'SimulationSerializer',
    'NPCSerializer',
    'MapSerializer',
    'ClassSerializer',
]
