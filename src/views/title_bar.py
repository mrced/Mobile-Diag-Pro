"""
Barra de título customizada com controles de janela, alternador de tema e link do desenvolvedor.
"""
from PySide6.QtCore import Qt, Signal, QPoint, QUrl
from PySide6.QtGui import QMouseEvent, QDesktopServices
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QToolTip

from src.core.theme_manager import ThemeManager

GITHUB_REPO_URL = "https://github.com/mrced/Mobile-Diag-Pro"


class TitleBar(QWidget):
    """
    Barra de título customizada para a janela principal (estilo macOS).
    Inclui botões de janela, alternador Dark/Light e link para o GitHub do desenvolvedor.
    """

    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(42)
        self.setObjectName("TitleBar")
        self._drag_pos: QPoint | None = None
        self._tm = ThemeManager()

        self._setup_ui()
        self._tm.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        """Configura a interface da barra de título."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(8)

        # Ícone do App
        self.icon_label = QLabel("📱", self)
        self.icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(self.icon_label)

        # Nome do App
        self.title_label = QLabel("Mobile-Diag-Pro", self)
        self.title_label.setObjectName("appTitle")
        self.title_label.setStyleSheet("font-weight: 700; font-size: 13px; background: transparent;")
        layout.addWidget(self.title_label)

        # Badge de Versão
        self.version_badge = QLabel("v1.0.0", self)
        self.version_badge.setStyleSheet("font-size: 11px; color: #86868b; background: transparent; padding-top: 2px;")
        layout.addWidget(self.version_badge)

        layout.addStretch()

        # Status do Dispositivo
        self.status_indicator = QLabel("● Desconectado", self)
        self.status_indicator.setObjectName("statusIndicator")
        self.status_indicator.setStyleSheet("font-size: 12px; font-weight: 600; color: #86868b; background: transparent;")
        layout.addWidget(self.status_indicator)

        layout.addStretch()

        # Botão GitHub do Desenvolvedor
        self.btn_github = QPushButton("⭐ GitHub", self)
        self.btn_github.setObjectName("titleBarActionBtn")
        self.btn_github.setToolTip(f"Desenvolvido por Onyalan S. Almeida — Abrir repositório no GitHub\n{GITHUB_REPO_URL}")
        self.btn_github.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_github.clicked.connect(self._open_github)
        layout.addWidget(self.btn_github)

        # Botão Alternar Tema (Dark / Light)
        theme_icon = "☀️" if self._tm.is_dark else "🌙"
        self.btn_theme = QPushButton(theme_icon, self)
        self.btn_theme.setObjectName("titleBarActionBtn")
        self.btn_theme.setFixedSize(32, 30)
        self.btn_theme.setToolTip("Alternar modo Claro / Escuro")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self._toggle_theme)
        layout.addWidget(self.btn_theme)

        # Separador sutil
        sep = QLabel("│", self)
        sep.setStyleSheet("color: #48484a; font-size: 12px; background: transparent;")
        layout.addWidget(sep)

        # Botões de controle de janela
        self.btn_minimize = QPushButton("—", self)
        self.btn_maximize = QPushButton("🗖", self)
        self.btn_close = QPushButton("✕", self)

        self.btn_minimize.setObjectName("titleBarBtn")
        self.btn_maximize.setObjectName("titleBarBtn")
        self.btn_close.setObjectName("titleBarCloseBtn")

        for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
            btn.setFixedSize(36, 30)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)
        layout.addWidget(self.btn_close)

        # Conectar sinais
        self.btn_minimize.clicked.connect(self.minimize_clicked)
        self.btn_maximize.clicked.connect(self.maximize_clicked)
        self.btn_close.clicked.connect(self.close_clicked)

    def _open_github(self) -> None:
        """Abre o repositório do desenvolvedor no navegador padrão."""
        QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL))

    def _toggle_theme(self) -> None:
        """Alterna o tema entre Dark e Light."""
        self._tm.toggle_theme()

    def _on_theme_changed(self, theme: str) -> None:
        """Atualiza o ícone do botão de tema conforme o modo ativo."""
        self.btn_theme.setText("☀️" if theme == "dark" else "🌙")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Inicia a operação de arrastar a janela."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Move a janela principal ao arrastar a barra de título."""
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            window = self.window()
            if not window.isMaximized():
                delta = event.globalPosition().toPoint() - self._drag_pos
                window.move(window.pos() + delta)
                self._drag_pos = event.globalPosition().toPoint()
                event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finaliza a operação de arrastar a janela."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Alterna o estado de maximizar/restaurar ao clicar duas vezes."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_clicked.emit()
            event.accept()
