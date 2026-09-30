"""
ViewModel para ADB Shell Interativo e Visualizador de Logcat.
"""
from typing import Optional
import subprocess

from PySide6.QtCore import QObject, Signal, Slot, QThread

from src.core.adb_client import ADBClient
from src.core.command_executor import CommandExecutor
from src.core.logger import get_logger

logger = get_logger(__name__)


class LogcatThread(QThread):
    """Thread dedicada para leitura contínua de Logcat sem travar a GUI."""
    line_received = Signal(str, str) # linha, prioridade ('V', 'D', 'I', 'W', 'E', 'F')

    def __init__(self, serial: str, filter_str: str = "", min_priority: str = "V") -> None:
        super().__init__()
        self.serial = serial
        self.filter_str = filter_str.lower()
        self.min_priority = min_priority
        self._running = True
        self._process: Optional[subprocess.Popen] = None

    def run(self) -> None:
        cmd = ["adb"]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(["logcat", "-v", "time"])

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            priority_order = {"V": 0, "D": 1, "I": 2, "W": 3, "E": 4, "F": 5}
            min_level = priority_order.get(self.min_priority, 0)

            while self._running and self._process.stdout:
                line = self._process.stdout.readline()
                if not line:
                    break

                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # Identificar nível de prioridade (ex: '09-30 12:00:00.000 I/Tag...')
                level = "I"
                for p in [" V/", " D/", " I/", " W/", " E/", " F/"]:
                    if p in line:
                        level = p.strip()[0]
                        break

                if priority_order.get(level, 0) >= min_level:
                    if not self.filter_str or self.filter_str in line_stripped.lower():
                        self.line_received.emit(line_stripped, level)

        except Exception as e:
            logger.error(f"Erro no streaming de logcat: {e}")
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass


class ADBShellViewModel(QObject):
    """
    ViewModel para controle do terminal ADB e streaming de logs.
    """
    command_output = Signal(str)
    logcat_line = Signal(str, str)
    is_logging_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._adb = ADBClient()
        self._executor = CommandExecutor()
        self._logcat_thread: Optional[LogcatThread] = None
        self._serial: Optional[str] = None

    def set_device(self, serial: str) -> None:
        """Atualiza o serial do dispositivo atual."""
        self._serial = serial
        if self.is_logging():
            self.stop_logcat()

    def execute_command(self, command: str) -> None:
        """Executa um comando shell no dispositivo assincronamente."""
        if not command:
            return

        def _run():
            try:
                return self._adb.shell(self._serial or "", command)
            except Exception as e:
                return f"Erro ao executar comando: {e}\n"

        worker_signals = self._executor.submit(_run)
        worker_signals.result.connect(lambda res: self.command_output.emit(str(res)))
        worker_signals.error.connect(lambda err: self.command_output.emit(f"Erro: {err}\n"))

    def start_logcat(self, filter_str: str = "", min_priority: str = "V") -> None:
        """Inicia a captura contínua de Logcat."""
        self.stop_logcat()

        self._logcat_thread = LogcatThread(self._serial or "", filter_str, min_priority)
        self._logcat_thread.line_received.connect(self.logcat_line)
        self._logcat_thread.start()
        self.is_logging_changed.emit(True)

    def stop_logcat(self) -> None:
        """Interrompe a captura de Logcat."""
        if self._logcat_thread and self._logcat_thread.isRunning():
            self._logcat_thread.stop()
            self._logcat_thread.wait(1000)
            self._logcat_thread = None
            self.is_logging_changed.emit(False)

    def is_logging(self) -> bool:
        """Retorna se o Logcat está ativo."""
        return self._logcat_thread is not None and self._logcat_thread.isRunning()

    def clear_device_logcat(self) -> None:
        """Executa adb logcat -c para limpar o buffer do dispositivo."""
        def _clear():
            cmd = ["adb"]
            if self._serial:
                cmd.extend(["-s", self._serial])
            cmd.extend(["logcat", "-c"])
            subprocess.run(cmd, capture_output=True)

        self._executor.submit(_clear)
