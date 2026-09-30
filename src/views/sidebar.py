"""
Barra lateral de navegação colapsável com rodapé do desenvolvedor.
"""
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy

GITHUB_REPO_URL = "https://github.com/mrced/Mobile-Diag-Pro"


class Sidebar(QWidget):
    """
    Barra lateral de navegação colapsável estilo macOS.
    Inclui botões das seções principais e rodapé com identificação do desenvolvedor.
    """

    page_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "sidebar")

        self._is_expanded = True
        self._expanded_width = 220
        self._collapsed_width = 64

        self.setFixedWidth(self._expanded_width)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._nav_buttons: list[QPushButton] = []
        self._pages_info = [
            ("📊  Dashboard", "📊", 0),
            ("🔬  Diagnóstico", "🔬", 1),
            ("⚡  Flash/Recovery", "⚡", 2),
            ("📈  Monitoramento", "📈", 3),
            ("💻  ADB Shell", "💻", 4),
            ("💾  Backup", "💾", 5),
            ("⚙️  Configurações", "⚙️", 6),
        ]
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura a interface da barra lateral."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        # Botão Toggle
        self.toggle_btn = QPushButton("☰", self)
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.setProperty("class", "sidebar-button")
        self.toggle_btn.setToolTip("Expandir / Recolher menu")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.toggle_btn)

        # Separador sutil
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("sidebarSeparator")
        line.setFixedHeight(1)
        layout.addWidget(line)
        layout.addSpacing(6)

        # Botões de Navegação
        for full_text, icon_only, index in self._pages_info:
            btn = QPushButton(full_text, self)
            btn.setFixedHeight(42)
            btn.setProperty("class", "sidebar-button")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self._on_button_clicked(idx))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Rodapé do Desenvolvedor
        footer_line = QFrame()
        footer_line.setFrameShape(QFrame.Shape.HLine)
        footer_line.setObjectName("sidebarSeparator")
        footer_line.setFixedHeight(1)
        layout.addWidget(footer_line)
        layout.addSpacing(4)

        self.dev_btn = QPushButton("⌥ Onyalan S. Almeida", self)
        self.dev_btn.setFixedHeight(36)
        self.dev_btn.setProperty("class", "sidebar-button")
        self.dev_btn.setToolTip(f"Desenvolvido por Onyalan S. Almeida — Ver código no GitHub\n{GITHUB_REPO_URL}")
        self.dev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dev_btn.clicked.connect(self._open_developer_github)
        layout.addWidget(self.dev_btn)

        # Botão ativo inicial
        if self._nav_buttons:
            self._set_active_button(0)

        # Configurar animação de expansão/recolhimento
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(220)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def _open_developer_github(self) -> None:
        """Abre a página do projeto no GitHub."""
        QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL))

    def _on_button_clicked(self, index: int) -> None:
        """Manipula o clique em um botão de navegação."""
        self._set_active_button(index)
        self.page_changed.emit(index)

    def _set_active_button(self, index: int) -> None:
        """Define visualmente o botão ativo."""
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.setProperty("class", "sidebar-button-active")
            else:
                btn.setProperty("class", "sidebar-button")

            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def toggle_sidebar(self) -> None:
        """Alterna a largura da barra lateral entre colapsada e expandida."""
        self.animation.stop()

        if self._is_expanded:
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(self._collapsed_width)
            self._is_expanded = False
            # Trocar para ícones simples
            for i, (_, icon_only, _) in enumerate(self._pages_info):
                self._nav_buttons[i].setText(icon_only)
            self.dev_btn.setText("⌥")
        else:
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(self._expanded_width)
            self._is_expanded = True
            # Restaurar texto completo
            for i, (full_text, _, _) in enumerate(self._pages_info):
                self._nav_buttons[i].setText(full_text)
            self.dev_btn.setText("⌥ Onyalan S. Almeida")

        self.animation.start()
