from dataclasses import dataclass, field
from src.core.constants import TestStatus

@dataclass
class TestResult:
    """Resultado de um teste individual."""
    test_id: str = ''
    test_name: str = ''
    category: str = ''
    status: TestStatus = TestStatus.PENDING
    message: str = ''
    details: dict = field(default_factory=dict)
    duration: float = 0.0  # seconds
    timestamp: str = ''

@dataclass
class DiagnosticReport:
    """Relatório completo do diagnóstico."""
    device_serial: str = ''
    device_model: str = ''
    timestamp: str = ''
    overall_score: int = 0  # 0-100
    results: list[TestResult] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    warnings: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
