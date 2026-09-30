"""
Página com Terminal ADB Shell Interativo e Visualizador de Logcat em Tempo Real.
"""
from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget, QLineEdit, QComboBox, 
    QPlainTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QTextCursor

from src.viewmodels.adb_shell_vm import ADBShellViewModel
from src.views.widgets.terminal_widget import TerminalWidget
from src.core.theme_manager import ThemeManager


class ADBShellPage(QWidget):
    """
    Página com abas para ADB Shell e Logcat.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.view_model = ADBShellViewModel(self)
        self._tm = ThemeManager()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        header = QVBoxLayout()
        header.setSpacing(2)
        title = QLabel("Terminal & Logcat")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Console ADB Shell Interativo e Visualizador de Logs em Tempo Real")
        subtitle.setProperty("class", "secondary")
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()

        # ─── Aba 1: ADB Shell ───
        self.shell_tab = QWidget()
        shell_layout = QVBoxLayout(self.shell_tab)
        shell_layout.setContentsMargins(10, 14, 10, 10)
        self.terminal = TerminalWidget(self.shell_tab)
        shell_layout.addWidget(self.terminal)
        self.tabs.addTab(self.shell_tab, "💻 ADB Shell")

        # ─── Aba 2: Logcat Viewer ───
        self.logcat_tab = QWidget()
        logcat_layout = QVBoxLayout(self.logcat_tab)
        logcat_layout.setContentsMargins(10, 14, 10, 10)
        logcat_layout.setSpacing(8)

        # Barra de Controles do Logcat
        controls = QHBoxLayout()
        controls.setSpacing(8)

        controls.addWidget(QLabel("Prioridade:"))
        self.combo_priority = QComboBox()
        self.combo_priority.addItems([
            "Verbose (V)",
            "Debug (D)",
            "Info (I)",
            "Warning (W)",
            "Error (E)",
            "Fatal (F)"
        ])
        self.combo_priority.setCurrentIndex(0)
        controls.addWidget(self.combo_priority)

        self.input_filter = QLineEdit()
        self.input_filter.setPlaceholderText("Filtrar por texto, tag ou processo...")
        controls.addWidget(self.input_filter, 1)

        self.btn_toggle_log = QPushButton("▶ Iniciar Logcat")
        self.btn_toggle_log.setProperty("class", "primary")
        self.btn_toggle_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_log.clicked.connect(self._toggle_logcat)
        controls.addWidget(self.btn_toggle_log)

        self.btn_clear_log = QPushButton("Limpar")
        self.btn_clear_log.clicked.connect(self._clear_logcat)
        controls.addWidget(self.btn_clear_log)

        self.btn_export_log = QPushButton("Exportar (.txt)")
        self.btn_export_log.clicked.connect(self._export_logcat)
        controls.addWidget(self.btn_export_log)

        logcat_layout.addLayout(controls)

        # Visualizador de Logcat
        self.logcat_display = QPlainTextEdit()
        self.logcat_display.setReadOnly(True)
        self.logcat_display.setFont(QFont("Consolas", 11))
        self.logcat_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #161618;
                color: #f5f5f7;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        logcat_layout.addWidget(self.logcat_display, 1)

        self.tabs.addTab(self.logcat_tab, "📋 Logcat Viewer")

        main_layout.addWidget(self.tabs, 1)

    def _connect_signals(self) -> None:
        self.terminal.command_submitted.connect(self.view_model.execute_command)
        self.view_model.command_output.connect(self.terminal.append_output)

        self.view_model.logcat_line.connect(self._append_logcat_line)
        self.view_model.is_logging_changed.connect(self._on_logging_state_changed)

    def set_device(self, serial: str) -> None:
        """Define o dispositivo ativo para o shell e logcat."""
        self.view_model.set_device(serial)
        if serial:
            self.terminal.append_output(f"\n[INFO] Conectado ao dispositivo: {serial}\n")
        else:
            self.terminal.append_output("\n[INFO] Nenhum dispositivo conectado.\n")

    def _toggle_logcat(self) -> None:
        if self.view_model.is_logging():
            self.view_model.stop_logcat()
        else:
            priority_code = self.combo_priority.currentText()[-2] # e.g. 'V', 'I', 'E'
            filter_text = self.input_filter.text().strip()
            self.view_model.start_logcat(filter_text, priority_code)

    def _on_logging_state_changed(self, is_running: bool) -> None:
        if is_running:
            self.btn_toggle_log.setText("⏹ Pausar Logcat")
            self.btn_toggle_log.setStyleSheet("background-color: #ff453a; color: white; border-radius: 8px; font-weight: bold;")
        else:
            self.btn_toggle_log.setText("▶ Iniciar Logcat")
            self.btn_toggle_log.setStyleSheet("")
            self.btn_toggle_log.setProperty("class", "primary")

    def _append_logcat_line(self, line: str, priority: str) -> None:
        """Adiciona linha colorida conforme prioridade."""
        self.logcat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.logcat_display.insertPlainText(line + "\n")
        self.logcat_display.moveCursor(QTextCursor.MoveOperation.End)

    def _clear_logcat(self) -> None:
        self.logcat_display.clear()

    def _export_logcat(self) -> None:
        content = self.logcat_display.toPlainText()
        if not content:
            QMessageBox.information(self, "Exportar", "Nenhum log gravado para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Logcat", "logcat_output.txt", "Arquivos de Texto (*.txt);;Todos os Arquivos (*.*)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Exportar", f"Log exportado com sucesso em:\n{file_path}")
