"""
Система проверки согласованности состояния симуляции.

Обеспечивает:
- Обнаружение рассинхронизации между подсистемами
- Валидация ссылочной целостности
- Логирование несоответствий для отладки

По спецификации INT-022: валидация определяет и сообщает о дрейфе состояния.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, TYPE_CHECKING
from enum import Enum, auto
import logging

from ..economy.property import PropertyType

if TYPE_CHECKING:
    from .simulation import Simulation


class ConsistencyLevel(Enum):
    """Уровень серьёзности проблемы согласованности"""
    INFO = auto()       # Информационное сообщение
    WARNING = auto()    # Предупреждение (возможная проблема)
    ERROR = auto()      # Ошибка (нарушение инвариантов)
    CRITICAL = auto()   # Критическая ошибка (симуляция может сломаться)


@dataclass
class ConsistencyIssue:
    """
    Проблема согласованности состояния.

    Описывает конкретное нарушение инварианта:
    - Какая система затронута
    - В чём проблема
    - Детали для отладки
    """
    level: ConsistencyLevel
    system: str                     # Какая система (npcs, property, classes...)
    description: str                # Описание проблемы
    details: Dict[str, Any] = field(default_factory=dict)
    suggestion: str = ""            # Предложение по исправлению

    def __str__(self) -> str:
        level_name = self.level.name
        return f"[{level_name}] {self.system}: {self.description}"

    def to_log_message(self) -> str:
        """Форматирует сообщение для лога"""
        parts = [f"[CONSISTENCY:{self.level.name}] {self.system}: {self.description}"]

        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"  Details: {details_str}")

        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")

        return "\n".join(parts)


@dataclass
class ConsistencyReport:
    """
    Отчёт о проверке согласованности.

    Собирает все найденные проблемы и предоставляет
    агрегированную информацию о состоянии симуляции.
    """
    issues: List[ConsistencyIssue] = field(default_factory=list)
    checks_performed: int = 0
    year: int = 0
    simulation_tick: int = 0

    def add_issue(self, issue: ConsistencyIssue) -> None:
        """Добавляет проблему в отчёт"""
        self.issues.append(issue)

    def add(self, level: ConsistencyLevel, system: str, description: str,
            details: Dict[str, Any] = None, suggestion: str = "") -> None:
        """Shortcut для добавления проблемы"""
        self.add_issue(ConsistencyIssue(
            level=level,
            system=system,
            description=description,
            details=details or {},
            suggestion=suggestion
        ))

    @property
    def is_valid(self) -> bool:
        """Возвращает True если нет ошибок (WARNINGS допустимы)"""
        return not any(
            issue.level in [ConsistencyLevel.ERROR, ConsistencyLevel.CRITICAL]
            for issue in self.issues
        )

    @property
    def has_critical(self) -> bool:
        """Есть ли критические ошибки"""
        return any(issue.level == ConsistencyLevel.CRITICAL for issue in self.issues)

    @property
    def error_count(self) -> int:
        """Количество ошибок (ERROR + CRITICAL)"""
        return sum(
            1 for issue in self.issues
            if issue.level in [ConsistencyLevel.ERROR, ConsistencyLevel.CRITICAL]
        )

    @property
    def warning_count(self) -> int:
        """Количество предупреждений"""
        return sum(1 for issue in self.issues if issue.level == ConsistencyLevel.WARNING)

    def get_issues_by_level(self, level: ConsistencyLevel) -> List[ConsistencyIssue]:
        """Возвращает проблемы определённого уровня"""
        return [issue for issue in self.issues if issue.level == level]

    def get_issues_by_system(self, system: str) -> List[ConsistencyIssue]:
        """Возвращает проблемы определённой системы"""
        return [issue for issue in self.issues if issue.system == system]

    def summary(self) -> str:
        """Возвращает краткую сводку"""
        if not self.issues:
            return f"Consistency OK: {self.checks_performed} checks passed"

        return (
            f"Consistency: {len(self.issues)} issues "
            f"({self.error_count} errors, {self.warning_count} warnings) "
            f"in {self.checks_performed} checks"
        )

    def to_log(self, logger: logging.Logger = None) -> None:
        """Логирует все проблемы"""
        if logger is None:
            logger = logging.getLogger("consistency")

        for issue in self.issues:
            msg = issue.to_log_message()
            if issue.level == ConsistencyLevel.CRITICAL:
                logger.critical(msg)
            elif issue.level == ConsistencyLevel.ERROR:
                logger.error(msg)
            elif issue.level == ConsistencyLevel.WARNING:
                logger.warning(msg)
            else:
                logger.info(msg)


def validate_state_consistency(simulation: 'Simulation') -> ConsistencyReport:
    """
    Проверяет согласованность состояния симуляции.

    Выполняет все проверки:
    1. NPC count consistency
    2. Property owner validity
    3. Class assignment after emergence
    4. Belief system consistency
    5. Family system consistency
    6. Event bus consistency

    Args:
        simulation: Объект симуляции для проверки

    Returns:
        ConsistencyReport с найденными проблемами
    """
    report = ConsistencyReport(
        year=simulation.year,
        simulation_tick=simulation.total_days * 24 + simulation.hour
    )

    # Выполняем все проверки
    _check_npc_consistency(simulation, report)
    _check_property_consistency(simulation, report)
    _check_class_consistency(simulation, report)
    _check_belief_consistency(simulation, report)
    _check_family_consistency(simulation, report)
    _check_demography_consistency(simulation, report)

    return report


def _check_npc_consistency(simulation: 'Simulation', report: ConsistencyReport) -> None:
    """
    Проверяет согласованность данных NPC.

    Проверки:
    - Живые NPC имеют корректное здоровье
    - Мёртвые NPC помечены is_alive=False
    - NPC существуют в ожидаемых местах
    """
    report.checks_performed += 1

    living_npcs = [n for n in simulation.npcs.values() if n.is_alive]
    dead_npcs = [n for n in simulation.npcs.values() if not n.is_alive]

    # Проверка: у живых NPC здоровье > 0
    for npc in living_npcs:
        if npc.health <= 0:
            report.add(
                ConsistencyLevel.ERROR,
                "npcs",
                f"NPC {npc.name} ({npc.id}) жив, но здоровье <= 0",
                {"npc_id": npc.id, "health": npc.health},
                "Вызовите handle_npc_death() для обработки смерти"
            )

    # Проверка: живые NPC имеют валидный возраст
    for npc in living_npcs:
        if npc.age < 0 or npc.age > 150:
            report.add(
                ConsistencyLevel.WARNING,
                "npcs",
                f"NPC {npc.name} ({npc.id}) имеет нереалистичный возраст",
                {"npc_id": npc.id, "age": npc.age}
            )

    # Проверка: живые NPC имеют валидные координаты
    for npc in living_npcs:
        if npc.position:
            x, y = npc.position.x, npc.position.y
            if x < 0 or y < 0 or x >= simulation.map.width or y >= simulation.map.height:
                report.add(
                    ConsistencyLevel.WARNING,
                    "npcs",
                    f"NPC {npc.name} ({npc.id}) находится за пределами карты",
                    {"npc_id": npc.id, "x": x, "y": y,
                     "map_size": (simulation.map.width, simulation.map.height)}
                )


def _check_property_consistency(simulation: 'Simulation', report: ConsistencyReport) -> None:
    """
    Проверяет согласованность системы собственности.

    Проверки:
    - Все владельцы существуют
    - Нет собственности у мёртвых NPC
    - Частная собственность помечена правильно
    """
    report.checks_performed += 1

    living_npc_ids = {n.id for n in simulation.npcs.values() if n.is_alive}
    dead_npc_ids = {n.id for n in simulation.npcs.values() if not n.is_alive}

    # Проверяем каждую единицу собственности
    orphaned_properties = []
    dead_owner_properties = []

    for prop_id, prop in simulation.ownership.properties.items():
        owner_id = prop.owner_id

        if not owner_id:
            # Собственность без владельца - допустимо для общинной
            if prop.owner_type == PropertyType.PRIVATE:
                report.add(
                    ConsistencyLevel.WARNING,
                    "property",
                    f"Частная собственность {prop_id} без владельца",
                    {"property_id": prop_id, "category": prop.category.value}
                )
            continue

        # Владелец не существует
        if owner_id not in simulation.npcs:
            orphaned_properties.append(prop_id)
            report.add(
                ConsistencyLevel.ERROR,
                "property",
                f"Владелец собственности {prop_id} не существует",
                {"property_id": prop_id, "owner_id": owner_id},
                "Удалите собственность или назначьте нового владельца"
            )

        # Владелец мёртв
        elif owner_id in dead_npc_ids:
            dead_owner_properties.append(prop_id)
            report.add(
                ConsistencyLevel.ERROR,
                "property",
                f"Собственность {prop_id} принадлежит мёртвому NPC",
                {"property_id": prop_id, "owner_id": owner_id},
                "Обработайте наследование через process_inheritance()"
            )

    # Сводка по собственности
    if orphaned_properties:
        report.add(
            ConsistencyLevel.INFO,
            "property",
            f"Найдено {len(orphaned_properties)} объектов с несуществующими владельцами",
            {"property_ids": orphaned_properties[:5]}  # Первые 5
        )


def _check_class_consistency(simulation: 'Simulation', report: ConsistencyReport) -> None:
    """
    Проверяет согласованность классовой системы.

    Проверки:
    - После emergence все живые NPC имеют класс
    - Члены классов существуют
    - npc_class соответствует членству в SocialClass
    """
    report.checks_performed += 1

    living_npc_ids = {n.id for n in simulation.npcs.values() if n.is_alive}

    # Если классы ещё не возникли, проверять нечего
    if not simulation.classes.classes_emerged:
        return

    # Проверка: все живые NPC имеют класс
    classless_npcs = []
    for npc_id in living_npc_ids:
        if npc_id not in simulation.classes.npc_class:
            classless_npcs.append(npc_id)

    if classless_npcs:
        report.add(
            ConsistencyLevel.WARNING,
            "classes",
            f"{len(classless_npcs)} живых NPC не имеют класса после emergence",
            {"npc_ids": classless_npcs[:5]},
            "Вызовите _update_npc_classes() для присвоения классов"
        )

    # Проверка: члены классов существуют и живы
    for class_type, social_class in simulation.classes.classes.items():
        dead_members = []
        missing_members = []

        for member_id in social_class.members:
            if member_id not in simulation.npcs:
                missing_members.append(member_id)
            elif not simulation.npcs[member_id].is_alive:
                dead_members.append(member_id)

        if missing_members:
            report.add(
                ConsistencyLevel.ERROR,
                "classes",
                f"Класс {class_type.russian_name} содержит несуществующих членов",
                {"class": class_type.name, "missing_ids": missing_members[:5]},
                "Удалите несуществующих членов из SocialClass.members"
            )

        if dead_members:
            report.add(
                ConsistencyLevel.ERROR,
                "classes",
                f"Класс {class_type.russian_name} содержит мёртвых членов",
                {"class": class_type.name, "dead_ids": dead_members[:5]},
                "Обработайте смерть через handle_npc_death()"
            )

    # Проверка: npc_class соответствует членству
    for npc_id, class_type in simulation.classes.npc_class.items():
        if npc_id not in living_npc_ids:
            continue  # Уже проверили выше

        if class_type in simulation.classes.classes:
            social_class = simulation.classes.classes[class_type]
            if npc_id not in social_class.members:
                report.add(
                    ConsistencyLevel.WARNING,
                    "classes",
                    f"NPC {npc_id} имеет класс {class_type.name}, но не в members",
                    {"npc_id": npc_id, "class": class_type.name},
                    "Синхронизируйте npc_class и SocialClass.members"
                )


def _check_belief_consistency(simulation: 'Simulation', report: ConsistencyReport) -> None:
    """
    Проверяет согласованность системы верований.

    Проверки:
    - Последователи верований существуют
    - npc_beliefs соответствует belief.adherents
    - Мёртвые NPC не являются последователями
    """
    report.checks_performed += 1

    living_npc_ids = {n.id for n in simulation.npcs.values() if n.is_alive}

    # Проверяем каждое верование
    for belief_id, belief in simulation.beliefs.beliefs.items():
        dead_adherents = []
        missing_adherents = []

        for adherent_id in belief.adherents:
            if adherent_id not in simulation.npcs:
                missing_adherents.append(adherent_id)
            elif not simulation.npcs[adherent_id].is_alive:
                dead_adherents.append(adherent_id)

        if missing_adherents:
            report.add(
                ConsistencyLevel.ERROR,
                "beliefs",
                f"Верование '{belief.name}' имеет несуществующих последователей",
                {"belief_id": belief_id, "missing_ids": missing_adherents[:5]},
                "Удалите несуществующих из belief.adherents"
            )

        if dead_adherents:
            report.add(
                ConsistencyLevel.ERROR,
                "beliefs",
                f"Верование '{belief.name}' имеет мёртвых последователей",
                {"belief_id": belief_id, "dead_ids": dead_adherents[:5]},
                "Обработайте смерть через handle_npc_death()"
            )

    # Проверяем npc_beliefs для живых NPC
    for npc_id, beliefs in simulation.beliefs.npc_beliefs.items():
        if npc_id not in simulation.npcs:
            report.add(
                ConsistencyLevel.WARNING,
                "beliefs",
                f"npc_beliefs содержит несуществующего NPC",
                {"npc_id": npc_id}
            )
            continue

        if not simulation.npcs[npc_id].is_alive:
            report.add(
                ConsistencyLevel.WARNING,
                "beliefs",
                f"npc_beliefs содержит мёртвого NPC",
                {"npc_id": npc_id}
            )


def _check_family_consistency(simulation: 'Simulation', report: ConsistencyReport) -> None:
    """
    Проверяет согласованность семейной системы.

    Проверки:
    - Супруги существуют и взаимно связаны
    - Члены семей существуют
    """
    report.checks_performed += 1

    living_npc_ids = {n.id for n in simulation.npcs.values() if n.is_alive}

    # Проверяем супружеские связи
    for npc_id, npc in simulation.npcs.items():
        if not npc.is_alive:
            continue

        spouse_id = npc.spouse_id
        if spouse_id:
            # Супруг существует?
            if spouse_id not in simulation.npcs:
                report.add(
                    ConsistencyLevel.ERROR,
                    "family",
                    f"Супруг NPC {npc.name} не существует",
                    {"npc_id": npc_id, "spouse_id": spouse_id},
                    "Очистите spouse_id"
                )
                continue

            spouse = simulation.npcs[spouse_id]

            # Супруг жив?
            if not spouse.is_alive:
                report.add(
                    ConsistencyLevel.WARNING,
                    "family",
                    f"Супруг NPC {npc.name} мёртв, но связь не очищена",
                    {"npc_id": npc_id, "spouse_id": spouse_id},
                    "Очистите spouse_id при смерти супруга"
                )
                continue

            # Взаимная связь?
            if spouse.spouse_id != npc_id:
                report.add(
                    ConsistencyLevel.ERROR,
                    "family",
                    f"Супружеская связь не взаимна: {npc.name} -> {spouse.name}",
                    {"npc_id": npc_id, "spouse_id": spouse_id,
                     "spouse_spouse_id": spouse.spouse_id},
                    "Синхронизируйте spouse_id у обоих NPC"
                )

    # Проверяем семьи
    for family_id, family in simulation.families.families.items():
        missing_members = []

        for member_id in family.members:
            if member_id not in simulation.npcs:
                missing_members.append(member_id)

        if missing_members:
            report.add(
                ConsistencyLevel.WARNING,
                "family",
                f"Семья {family_id} содержит несуществующих членов",
                {"family_id": family_id, "missing_ids": missing_members[:5]}
            )


def _check_demography_consistency(simulation: 'Simulation', report: ConsistencyReport) -> None:
    """
    Проверяет согласованность демографических данных.

    Проверки:
    - Количество живых NPC соответствует ожидаемому
    - Статистика демографии корректна
    """
    report.checks_performed += 1

    living_count = len([n for n in simulation.npcs.values() if n.is_alive])

    # Проверяем, что демография отслеживает правильное население
    # (если есть history, последняя запись должна быть близка к текущему)
    if simulation.demography.population_history:
        last_year, last_pop = simulation.demography.population_history[-1]

        # Допускаем небольшое расхождение из-за смертей/рождений
        # между записью и текущим моментом
        if abs(last_pop - living_count) > living_count * 0.5 and last_pop > 0:
            report.add(
                ConsistencyLevel.INFO,
                "demography",
                f"Население изменилось значительно с последней записи",
                {"recorded": last_pop, "actual": living_count,
                 "record_year": last_year, "current_year": simulation.year}
            )


def run_consistency_check(simulation: 'Simulation',
                          log_results: bool = True) -> ConsistencyReport:
    """
    Удобная функция для запуска проверки согласованности.

    Args:
        simulation: Симуляция для проверки
        log_results: Логировать ли результаты

    Returns:
        ConsistencyReport
    """
    report = validate_state_consistency(simulation)

    if log_results and report.issues:
        logger = logging.getLogger("simulation.consistency")
        report.to_log(logger)

    return report
