"""
ViewModel de Diagnóstico Avançado.
Executa rotinas reais no dispositivo conectado via DiagnosticEngine e atualiza a interface de forma assíncrona.
"""
from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from PySide6.QtCore import QObject, Signal, Slot, QThread

from src.core.constants import TestStatus
from src.core.diagnostic_engine import DiagnosticEngine, DiagnosticReport, TestResult
from src.core.report_generator import ReportGenerator
from src.core.logger import get_logger

logger = get_logger(__name__)


class DiagnosticWorkerThread(QThread):
    progress = Signal(int, str)
    result_ready = Signal(object)
    finished_report = Signal(object)
    error = Signal(str)

    def __init__(self, serial: str, test_ids: List[str]):
        super().__init__()
        self.serial = serial
        self.test_ids = test_ids
        self._is_cancelled = False
        self._engine = DiagnosticEngine()

    def run(self):
        results = []
        start_time = datetime.now()

        for i, tid in enumerate(self.test_ids):
            if self._is_cancelled:
                break

            self.progress.emit(i, tid)

            try:
                res = self._engine.run_test(self.serial, tid)
            except Exception as e:
                logger.error(f"Erro ao executar teste {tid}: {e}")
                res = TestResult(
                    test_id=tid,
                    name=tid,
                    category="unknown",
                    status=TestStatus.FAILED,
                    message=f"Falha ao executar teste: {str(e)}",
                    details={"Erro": str(e)},
                )

            results.append(res)
            self.result_ready.emit(res)

        if not self._is_cancelled:
            passed = sum(1 for r in results if r.status == TestStatus.PASSED)
            warning = sum(1 for r in results if r.status == TestStatus.WARNING)
            failed = sum(1 for r in results if r.status == TestStatus.FAILED)
            skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
            total = len(results) or 1
            score = max(0, int(((passed * 100) + (warning * 50)) / total))

            report = DiagnosticReport(
                device_serial=self.serial,
                start_time=start_time,
                end_time=datetime.now(),
                overall_score=score,
                passed_count=passed,
                warning_count=warning,
                failed_count=failed,
                skipped_count=skipped,
                results=results,
            )
            self.finished_report.emit(report)

    def cancel(self):
        self._is_cancelled = True


class DiagnosticViewModel(QObject):
    """
    ViewModel para a página de Diagnóstico.
    Gerencia o estado dos testes, execução real via DiagnosticEngine e estatísticas.
    """

    # Sinais
    diagnostic_started = Signal(int)  # total tests
    test_progress = Signal(int, str)  # current test index, test name
    test_completed = Signal(object)  # TestResult
    diagnostic_finished = Signal(object)  # DiagnosticReport
    category_filter_changed = Signal(str)
    error_occurred = Signal(str)
    stats_updated = Signal(int, int, int, int)  # passed, warning, failed, total

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self.available_tests: List[str] = []
        self.selected_test_ids: List[str] = []
        self.current_serial: str = ""
        self.is_running: bool = False

        self._diagnostic_thread: Optional[DiagnosticWorkerThread] = None
        self._last_report: Optional[DiagnosticReport] = None

        # Estatísticas atuais
        self.stat_passed = 0
        self.stat_warning = 0
        self.stat_failed = 0
        self.stat_total = 0

    def start_diagnostic(self, serial: str, test_ids: Optional[List[str]] = None):
        """
        Inicia a execução assíncrona dos diagnósticos reais no dispositivo.
        """
        if self.is_running:
            self.error_occurred.emit("Diagnóstico já está em execução.")
            return

        self.current_serial = serial
        tests_to_run = test_ids if test_ids is not None else self.selected_test_ids

        if not tests_to_run:
            self.error_occurred.emit("Nenhum teste selecionado para execução.")
            return

        self.is_running = True
        self.stat_total = len(tests_to_run)
        self.stat_passed = 0
        self.stat_warning = 0
        self.stat_failed = 0

        self.stats_updated.emit(0, 0, 0, self.stat_total)
        self.diagnostic_started.emit(self.stat_total)

        # Thread de execução real
        self._diagnostic_thread = DiagnosticWorkerThread(serial, tests_to_run)
        self._diagnostic_thread.progress.connect(self._on_test_progress)
        self._diagnostic_thread.result_ready.connect(self._on_test_completed)
        self._diagnostic_thread.finished_report.connect(self._on_diagnostic_finished)
        self._diagnostic_thread.error.connect(self._on_error)
        self._diagnostic_thread.start()

    def stop_diagnostic(self):
        """
        Cancela a execução atual.
        """
        if self.is_running and self._diagnostic_thread:
            self._diagnostic_thread.cancel()
            self.is_running = False
            self.error_occurred.emit("Diagnóstico cancelado pelo usuário.")

    def export_report(self, format_type: str = "html", output_dir: Optional[str] = None) -> str:
        """
        Exporta o relatório do diagnóstico gerado em formato HTML ou JSON.
        """
        if not self._last_report:
            self.error_occurred.emit("Nenhum relatório disponível para exportação. Execute um diagnóstico primeiro.")
            return ""

        if not output_dir:
            output_dir = os.path.expanduser("~/Documents")

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filename = os.path.join(
            output_dir,
            f"relatorio_diagnostico_{self.current_serial}_{int(datetime.now().timestamp())}.{format_type}",
        )

        try:
            generator = ReportGenerator()
            if format_type.lower() == "json":
                out_path = generator.generate_json(self._last_report, Path(filename))
            else:
                out_path = generator.generate_html(self._last_report, Path(filename))
            return str(out_path)
        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")
            self.error_occurred.emit(f"Falha ao exportar relatório: {str(e)}")
            return ""

    @Slot(int, str)
    def _on_test_progress(self, index: int, test_name: str):
        self.test_progress.emit(index, test_name)

    @Slot(object)
    def _on_test_completed(self, result: TestResult):
        status_val = getattr(result.status, "value", str(result.status))
        if status_val == "passed":
            self.stat_passed += 1
        elif status_val == "failed":
            self.stat_failed += 1
        elif status_val == "warning":
            self.stat_warning += 1

        self.stats_updated.emit(self.stat_passed, self.stat_warning, self.stat_failed, self.stat_total)
        self.test_completed.emit(result)

    @Slot(object)
    def _on_diagnostic_finished(self, report: DiagnosticReport):
        self.is_running = False
        self._last_report = report
        self.diagnostic_finished.emit(report)

    @Slot(str)
    def _on_error(self, message: str):
        self.is_running = False
        self.error_occurred.emit(message)
