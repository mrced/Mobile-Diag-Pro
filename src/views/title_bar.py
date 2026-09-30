from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class TitleBar(QWidget):
    """
    Barra de título customizada para a janela principal.
    Permite arrastar a janela, fechar, minimizar e maximizar.
    """

    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setObjectName("TitleBar")
        self._drag_pos: QPoint | None = None
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura a interface da barra de título."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(10)

        # Ícone do App
        self.icon_label = QLabel("📱", self)
        self.icon_label.setFixedSize(24, 24)
        layout.addWidget(self.icon_label)

        # Nome do App
        self.title_label = QLabel("Mobile-Diag-Pro v1.0", self)
        self.title_label.setProperty("class", "page-title")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Status do Dispositivo
        self.status_indicator = QLabel("🔴 Desconectado", self)
        self.status_indicator.setObjectName("statusIndicator")
        layout.addWidget(self.status_indicator)

        layout.addStretch()

        # Botões de controle de janela
        self.btn_minimize = QPushButton("—", self)
        self.btn_maximize = QPushButton("🗖", self)
        self.btn_close = QPushButton("✕", self)

        self.btn_minimize.setObjectName("titleBarBtn")
        self.btn_maximize.setObjectName("titleBarBtn")
        self.btn_close.setObjectName("titleBarCloseBtn")

        for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
            btn.setFixedSize(40, 40)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)
        layout.addWidget(self.btn_close)

        # Conectar sinais
        self.btn_minimize.clicked.connect(self.minimize_clicked)
        self.btn_maximize.clicked.connect(self.maximize_clicked)
        self.btn_close.clicked.connect(self.close_clicked)

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
