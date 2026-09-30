from typing import List, Optional, Dict, Any
import json
import os
from PySide6.QtCore import QObject, Signal, Slot, QThread

# Mocks para imports não disponíveis
class TestResult:
    def __init__(self, test_id: str, status, message: str = "", details: dict = None):
        self.test_id = test_id
        self.status = status
        self.message = message
        self.details = details or {}

class DiagnosticReport:
    def __init__(self, serial: str, results: List[TestResult]):
        self.serial = serial
        self.results = results
        self.passed = sum(1 for r in results if r.status.value == "passed")
        self.failed = sum(1 for r in results if r.status.value == "failed")
        self.warning = sum(1 for r in results if r.status.value == "warning")
        self.total = len(results)

class DummyDiagnosticThread(QThread):
    progress = Signal(int, str)
    result_ready = Signal(object)
    finished_report = Signal(object)
    error = Signal(str)

    def __init__(self, serial: str, test_ids: List[str]):
        super().__init__()
        self.serial = serial
        self.test_ids = test_ids
        self._is_cancelled = False

    def run(self):
        from src.views.widgets.test_item_widget import TestStatus
        import time
        import random
        
        results = []
        for i, tid in enumerate(self.test_ids):
            if self._is_cancelled:
                break
                
            self.progress.emit(i, tid)
            # Simulando execução
            time.sleep(1)
            
            # Simulando resultado aleatório
            status_choice = random.choices(
                [TestStatus.PASSED, TestStatus.FAILED, TestStatus.WARNING], 
                weights=[0.8, 0.1, 0.1]
            )[0]
            
            res = TestResult(tid, status_choice, f"Simulated message for {tid}", {"raw_value": random.randint(10, 100)})
            results.append(res)
            self.result_ready.emit(res)
            
        if not self._is_cancelled:
            report = DiagnosticReport(self.serial, results)
            self.finished_report.emit(report)

    def cancel(self):
        self._is_cancelled = True


class DiagnosticViewModel(QObject):
    """
    ViewModel para a página de Diagnóstico.
    Gerencia o estado dos testes, execução e estatísticas.
    """
    # Sinais
    diagnostic_started = Signal(int) # total tests
    test_progress = Signal(int, str) # current test index, test name
    test_completed = Signal(object) # TestResult
    diagnostic_finished = Signal(object) # DiagnosticReport
    category_filter_changed = Signal(str)
    error_occurred = Signal(str)
    stats_updated = Signal(int, int, int, int) # passed, warning, failed, total

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self.available_tests = []
        self.selected_test_ids = []
        self.current_serial = ""
        self.is_running = False
        
        self._diagnostic_thread = None
        
        # Estatísticas atuais
        self.stat_passed = 0
        self.stat_warning = 0
        self.stat_failed = 0
        self.stat_total = 0

    def start_diagnostic(self, serial: str, test_ids: Optional[List[str]] = None):
        """
        Inicia a execução assíncrona dos diagnósticos.
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
        
        # Utilizando Thread simulada (integrar com CommandExecutor real posteriormente)
        self._diagnostic_thread = DummyDiagnosticThread(serial, tests_to_run)
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
        Exporta o relatório do diagnóstico.
        """
        if not output_dir:
            output_dir = os.path.expanduser("~/Documents")
            
        filename = os.path.join(output_dir, f"diagnostic_report_{self.current_serial}.{format_type}")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if format_type == "html":
                    f.write("<html><body><h1>Relatório de Diagnóstico</h1></body></html>")
                else:
                    f.write("Relatório de Diagnóstico")
            return filename
        except Exception as e:
            self.error_occurred.emit(f"Falha ao exportar relatório: {str(e)}")
            return ""

    @Slot(int, str)
    def _on_test_progress(self, index: int, test_name: str):
        self.test_progress.emit(index, test_name)

    @Slot(object)
    def _on_test_completed(self, result: TestResult):
        from src.views.widgets.test_item_widget import TestStatus
        
        if result.status == TestStatus.PASSED:
            self.stat_passed += 1
        elif result.status == TestStatus.FAILED:
            self.stat_failed += 1
        elif result.status == TestStatus.WARNING:
            self.stat_warning += 1
            
        self.stats_updated.emit(self.stat_passed, self.stat_warning, self.stat_failed, self.stat_total)
        self.test_completed.emit(result)

    @Slot(object)
    def _on_diagnostic_finished(self, report: DiagnosticReport):
        self.is_running = False
        self.diagnostic_finished.emit(report)

    @Slot(str)
    def _on_error(self, message: str):
        self.error_occurred.emit(message)
