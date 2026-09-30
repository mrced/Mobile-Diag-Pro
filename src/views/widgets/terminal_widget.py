"""
Widget de Terminal Interativo estilo macOS para ADB Shell.
"""
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QPlainTextEdit, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor

from src.core.theme_manager import ThemeManager


class TerminalWidget(QWidget):
    """
    Console embutido com histórico de comandos e execução interativa.
    """
    command_submitted = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._tm = ThemeManager()
        self._history: List[str] = []
        self._history_index: int = -1

        self._setup_ui()
        self._tm.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Barra de Ações Rápidas do Terminal
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        # Atalhos rápidos comuns de técnicos
        shortcuts = [
            ("ps", "ps"),
            ("top (1x)", "top -n 1 -m 10"),
            ("df -h", "df -h"),
            ("bateria", "dumpsys battery"),
            ("propriedades", "getprop"),
            ("uptime", "uptime")
        ]

        for label, cmd in shortcuts:
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.setStyleSheet("font-size: 11px; padding: 2px 8px; border-radius: 4px;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, c=cmd: self._run_quick_command(c))
            top_bar.addWidget(btn)

        top_bar.addStretch()

        self.btn_copy = QPushButton("Copiar")
        self.btn_copy.setFixedHeight(26)
        self.btn_copy.setStyleSheet("font-size: 11px; padding: 2px 8px; border-radius: 4px;")
        self.btn_copy.clicked.connect(self.copy_all)
        top_bar.addWidget(self.btn_copy)

        self.btn_clear = QPushButton("Limpar")
        self.btn_clear.setFixedHeight(26)
        self.btn_clear.setStyleSheet("font-size: 11px; padding: 2px 8px; border-radius: 4px;")
        self.btn_clear.clicked.connect(self.clear_terminal)
        top_bar.addWidget(self.btn_clear)

        layout.addLayout(top_bar)

        # Área de Output
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 12))
        self.output_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #121214;
                color: #30d158;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.output_text, 1)

        # Barra de Entrada (Prompt)
        prompt_bar = QHBoxLayout()
        prompt_bar.setSpacing(6)

        self.prompt_label = QLabel("android@device:~$ ")
        self.prompt_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.prompt_label.setStyleSheet("color: #0a84ff; background: transparent;")
        prompt_bar.addWidget(self.prompt_label)

        self.cmd_input = QLineEdit()
        self.cmd_input.setFont(QFont("Consolas", 12))
        self.cmd_input.setPlaceholderText("Digite um comando shell e pressione Enter...")
        self.cmd_input.returnPressed.connect(self._on_enter_pressed)
        prompt_bar.addWidget(self.cmd_input, 1)

        layout.addLayout(prompt_bar)

    def _run_quick_command(self, command: str) -> None:
        """Executa um atalho rápido diretamente."""
        self.cmd_input.setText(command)
        self._on_enter_pressed()

    def _on_enter_pressed(self) -> None:
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return

        self._history.append(cmd)
        self._history_index = len(self._history)

        self.append_output(f"\nandroid@device:~$ {cmd}\n")
        self.command_submitted.emit(cmd)
        self.cmd_input.clear()

    def keyPressEvent(self, event) -> None:
        """Navega pelo histórico com setas Cima / Baixo quando o foco está no input."""
        if self.cmd_input.hasFocus():
            if event.key() == Qt.Key.Key_Up:
                if self._history and self._history_index > 0:
                    self._history_index -= 1
                    self.cmd_input.setText(self._history[self._history_index])
                return
            elif event.key() == Qt.Key.Key_Down:
                if self._history and self._history_index < len(self._history) - 1:
                    self._history_index += 1
                    self.cmd_input.setText(self._history[self._history_index])
                elif self._history_index >= len(self._history) - 1:
                    self._history_index = len(self._history)
                    self.cmd_input.clear()
                return

        super().keyPressEvent(event)

    def append_output(self, text: str) -> None:
        """Adiciona texto ao console e rola até o final."""
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)
        self.output_text.insertPlainText(text)
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)

    def clear_terminal(self) -> None:
        """Limpa todo o conteúdo do terminal."""
        self.output_text.clear()

    def copy_all(self) -> None:
        """Copia todo o texto do terminal para a área de transferência."""
        self.output_text.selectAll()
        self.output_text.copy()
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)

    def _on_theme_changed(self, theme: str) -> None:
        """Atualiza cores caso o tema mude."""
        c = self._tm.colors
        if theme == "dark":
            self.output_text.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #121214;
                    color: #30d158;
                    border: 1px solid #3a3a3c;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
        else:
            self.output_text.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #f0f0f4;
                    color: #1a7f37;
                    border: 1px solid #d1d1d6;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
