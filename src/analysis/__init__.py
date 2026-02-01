"""
Модуль анализа симуляции.

Предоставляет инструменты для:
- Анализа чувствительности параметров
- Батч-запуска симуляций
- Сравнения результатов

По спецификации INT-041.
"""
from .sensitivity import (
    SensitivityAnalyzer,
    ParameterSpec,
    ParameterType,
    OutcomeSpec,
    OutcomeCategory,
    SamplingStrategy,
    RunResult,
    SensitivityResult,
    AnalysisReport,
)

__all__ = [
    "SensitivityAnalyzer",
    "ParameterSpec",
    "ParameterType",
    "OutcomeSpec",
    "OutcomeCategory",
    "SamplingStrategy",
    "RunResult",
    "SensitivityResult",
    "AnalysisReport",
]
