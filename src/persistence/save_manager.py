"""
Менеджер сохранений.

Отвечает за:
- Сохранение в файл (JSON + gzip)
- Загрузку из файла
- Автосохранение
- Список сохранений
- Валидацию
"""
import json
import gzip
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from .schema import SaveData, SaveMetadata, SAVE_VERSION, is_version_compatible
from .serializers import SimulationSerializer

if TYPE_CHECKING:
    from ..core.simulation import Simulation


class SaveError(Exception):
    """Ошибка сохранения"""
    pass


class LoadError(Exception):
    """Ошибка загрузки"""
    pass


@dataclass
class SaveInfo:
    """Информация о сохранении для списка"""
    filepath: str
    filename: str
    save_name: str
    year: int
    population: int
    era: str
    created_at: str
    version: str
    size_bytes: int


class SaveManager:
    """
    Менеджер сохранений.

    Поддерживает:
    - Сохранение в JSON с gzip сжатием
    - Автосохранение
    - Версионирование
    - Валидацию
    """

    # Директория для сохранений по умолчанию
    DEFAULT_SAVE_DIR = "saves"

    # Расширение файлов
    SAVE_EXTENSION = ".sav.gz"

    # Автосохранение
    AUTOSAVE_NAME = "autosave"
    MAX_AUTOSAVES = 3

    def __init__(self, save_dir: str = None):
        """
        Args:
            save_dir: Директория для сохранений
        """
        self.save_dir = Path(save_dir or self.DEFAULT_SAVE_DIR)
        self._ensure_save_dir()

    def _ensure_save_dir(self) -> None:
        """Создаёт директорию для сохранений если не существует"""
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _get_save_path(self, name: str) -> Path:
        """Возвращает путь к файлу сохранения"""
        # Очищаем имя от недопустимых символов
        safe_name = "".join(c for c in name if c.isalnum() or c in "._-")
        if not safe_name:
            safe_name = "save"
        return self.save_dir / f"{safe_name}{self.SAVE_EXTENSION}"

    def save(self,
             simulation: 'Simulation',
             name: str = None,
             description: str = "") -> str:
        """
        Сохраняет симуляцию в файл.

        Args:
            simulation: Симуляция для сохранения
            name: Имя сохранения (опционально)
            description: Описание (опционально)

        Returns:
            Путь к сохранённому файлу

        Raises:
            SaveError: При ошибке сохранения
        """
        try:
            # Генерируем имя если не указано
            if not name:
                name = f"save_{simulation.year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Сериализуем
            save_data = SimulationSerializer.serialize(simulation)

            # Добавляем метаданные
            save_data["metadata"]["save_name"] = name
            save_data["metadata"]["description"] = description

            # Путь к файлу
            filepath = self._get_save_path(name)

            # Сохраняем с gzip
            json_str = json.dumps(save_data, ensure_ascii=False, indent=None)
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(json_str)

            return str(filepath)

        except Exception as e:
            raise SaveError(f"Не удалось сохранить: {e}")

    def load(self, filepath: str, simulation: 'Simulation') -> None:
        """
        Загружает сохранение в симуляцию.

        Args:
            filepath: Путь к файлу сохранения
            simulation: Симуляция для загрузки данных

        Raises:
            LoadError: При ошибке загрузки
        """
        try:
            path = Path(filepath)

            if not path.exists():
                raise LoadError(f"Файл не найден: {filepath}")

            # Читаем файл
            if filepath.endswith('.gz'):
                with gzip.open(path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            # Проверяем версию
            version = data.get("metadata", {}).get("version", "0.0.0")
            if not is_version_compatible(version):
                raise LoadError(
                    f"Несовместимая версия сохранения: {version}. "
                    f"Требуется >= {SAVE_VERSION}"
                )

            # Проверяем checksum
            save_data = SaveData.from_dict(data)
            if not save_data.verify_checksum():
                # Предупреждаем, но не блокируем
                print("Предупреждение: контрольная сумма не совпадает")

            # Загружаем данные
            SimulationSerializer.deserialize(data, simulation)

        except json.JSONDecodeError as e:
            raise LoadError(f"Ошибка формата JSON: {e}")
        except Exception as e:
            if isinstance(e, LoadError):
                raise
            raise LoadError(f"Не удалось загрузить: {e}")

    def autosave(self, simulation: 'Simulation') -> str:
        """
        Выполняет автосохранение.

        Ротирует старые автосохранения.

        Returns:
            Путь к файлу автосохранения
        """
        # Ротируем старые автосохранения
        for i in range(self.MAX_AUTOSAVES - 1, 0, -1):
            old_path = self._get_save_path(f"{self.AUTOSAVE_NAME}_{i}")
            new_path = self._get_save_path(f"{self.AUTOSAVE_NAME}_{i+1}")

            if old_path.exists():
                if new_path.exists():
                    new_path.unlink()
                old_path.rename(new_path)

        # Переименовываем текущее автосохранение
        current_path = self._get_save_path(self.AUTOSAVE_NAME)
        if current_path.exists():
            backup_path = self._get_save_path(f"{self.AUTOSAVE_NAME}_1")
            if backup_path.exists():
                backup_path.unlink()
            current_path.rename(backup_path)

        # Создаём новое автосохранение
        return self.save(simulation, self.AUTOSAVE_NAME, "Автосохранение")

    def list_saves(self) -> List[SaveInfo]:
        """
        Возвращает список доступных сохранений.

        Returns:
            Список SaveInfo отсортированный по дате (новые первыми)
        """
        saves = []

        for filepath in self.save_dir.glob(f"*{self.SAVE_EXTENSION}"):
            try:
                info = self._get_save_info(filepath)
                if info:
                    saves.append(info)
            except Exception:
                pass  # Пропускаем повреждённые файлы

        # Сортируем по дате (новые первыми)
        saves.sort(key=lambda s: s.created_at, reverse=True)

        return saves

    def _get_save_info(self, filepath: Path) -> Optional[SaveInfo]:
        """Читает метаданные сохранения"""
        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                # Читаем только начало файла для метаданных
                content = f.read(10000)  # Первые ~10KB

            # Парсим как JSON (может быть неполным)
            # Ищем секцию metadata
            import re
            match = re.search(r'"metadata"\s*:\s*\{[^}]+\}', content)

            if match:
                metadata_str = '{' + match.group() + '}'
                try:
                    data = json.loads(metadata_str)
                    metadata = data.get("metadata", {})
                except json.JSONDecodeError:
                    # Попробуем прочитать весь файл
                    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                    metadata = data.get("metadata", {})
            else:
                # Читаем весь файл
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                metadata = data.get("metadata", {})

            return SaveInfo(
                filepath=str(filepath),
                filename=filepath.name,
                save_name=metadata.get("save_name", filepath.stem),
                year=metadata.get("year", 0),
                population=metadata.get("population", 0),
                era=metadata.get("era", ""),
                created_at=metadata.get("created_at", ""),
                version=metadata.get("version", ""),
                size_bytes=filepath.stat().st_size,
            )

        except Exception:
            return None

    def delete_save(self, filepath: str) -> bool:
        """
        Удаляет сохранение.

        Args:
            filepath: Путь к файлу

        Returns:
            True если удалено успешно
        """
        try:
            path = Path(filepath)
            if path.exists() and path.suffix == '.gz':
                path.unlink()
                return True
            return False
        except Exception:
            return False

    def get_save_details(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает полные метаданные сохранения.

        Args:
            filepath: Путь к файлу

        Returns:
            Словарь с метаданными или None
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return None

            with gzip.open(path, 'rt', encoding='utf-8') as f:
                data = json.load(f)

            return data.get("metadata", {})

        except Exception:
            return None

    def quick_save(self, simulation: 'Simulation') -> str:
        """Быстрое сохранение с автоматическим именем"""
        return self.save(simulation, "quicksave", "Быстрое сохранение")

    def quick_load(self, simulation: 'Simulation') -> bool:
        """Загрузка быстрого сохранения"""
        filepath = self._get_save_path("quicksave")
        if filepath.exists():
            self.load(str(filepath), simulation)
            return True
        return False

    def has_quicksave(self) -> bool:
        """Проверяет наличие быстрого сохранения"""
        return self._get_save_path("quicksave").exists()

    def has_autosave(self) -> bool:
        """Проверяет наличие автосохранения"""
        return self._get_save_path(self.AUTOSAVE_NAME).exists()

    def load_autosave(self, simulation: 'Simulation') -> bool:
        """Загружает последнее автосохранение"""
        filepath = self._get_save_path(self.AUTOSAVE_NAME)
        if filepath.exists():
            self.load(str(filepath), simulation)
            return True
        return False
