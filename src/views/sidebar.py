from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy


class Sidebar(QWidget):
    """
    Barra lateral de navegação colapsável.
    """

    page_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "sidebar")
        
        self._is_expanded = True
        self._expanded_width = 220
        self._collapsed_width = 60
        
        self.setFixedWidth(self._expanded_width)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        self._nav_buttons: list[QPushButton] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura a interface da barra lateral."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Botão Toggle
        self.toggle_btn = QPushButton("☰", self)
        self.toggle_btn.setFixedHeight(50)
        self.toggle_btn.setProperty("class", "sidebar-button")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.toggle_btn)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("sidebarSeparator")
        layout.addWidget(line)

        # Páginas
        pages = [
            ("📊 Dashboard", 0),
            ("🔬 Diagnóstico", 1),
            ("⚡ Flash/Recovery", 2),
            ("📈 Monitoramento", 3),
            ("💻 ADB Shell", 4),
            ("💾 Backup", 5),
            ("⚙️ Configurações", 6)
        ]

        for text, index in pages:
            btn = QPushButton(text, self)
            btn.setFixedHeight(45)
            btn.setProperty("class", "sidebar-button")
            btn.clicked.connect(lambda checked, idx=index: self._on_button_clicked(idx))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Botão ativo inicial
        if self._nav_buttons:
            self._set_active_button(0)

        # Configurar animação
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart)

    def _on_button_clicked(self, index: int) -> None:
        """Manipula o clique em um botão de navegação."""
        self._set_active_button(index)
        self.page_changed.emit(index)

    def _set_active_button(self, index: int) -> None:
        """
        Define visualmente o botão ativo.
        
        Args:
            index (int): Índice do botão ativado.
        """
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.setProperty("class", "sidebar-button-active")
            else:
                btn.setProperty("class", "sidebar-button")
            
            # Necessário para forçar a atualização do estilo (QSS)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def toggle_sidebar(self) -> None:
        """Alterna o tamanho da barra lateral (colapsada/expandida)."""
        self.animation.stop()
        
        if self._is_expanded:
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(self._collapsed_width)
            self._is_expanded = False
            # Ajustar textos dos botões (opcional, ou gerenciar pelo CSS)
        else:
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(self._expanded_width)
            self._is_expanded = True
            
        self.animation.start()
