from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from src.core.theme_manager import ThemeManager

class StatusBadge(QFrame):
    """
    Widget em formato de pílula para exibir status coloridos.
    """
    def __init__(self, text: str = "", color: str = "#4caf50", icon: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "status-badge")
        self.setFixedHeight(24)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 4, 12, 4)
        self.layout.setSpacing(6)
        
        self.label = QLabel(f"{icon} {text}".strip(), self)
        self.label.setStyleSheet(f"color: #ffffff; font-weight: bold; font-size: 12px;")
        
        self.layout.addWidget(self.label)
        
        self.setStyleSheet(f"QFrame.status-badge {{ background-color: {color}; border-radius: 12px; }}")

    @classmethod
    def connected(cls, parent=None):
        return cls("Conectado", ThemeManager().colors.success, "🟢", parent)

    @classmethod
    def disconnected(cls, parent=None):
        return cls("Desconectado", ThemeManager().colors.muted, "⚫", parent)

    @classmethod
    def recovery(cls, parent=None):
        return cls("Recovery", ThemeManager().colors.warning, "🟡", parent)

    @classmethod
    def fastboot(cls, parent=None):
        return cls("Fastboot", "#ff9500", "🟠", parent)

    @classmethod
    def unauthorized(cls, parent=None):
        return cls("Não Autorizado", ThemeManager().colors.danger, "🔴", parent)

    @classmethod
    def unknown(cls, parent=None):
        return cls("Desconhecido", ThemeManager().colors.muted, "❓", parent)
