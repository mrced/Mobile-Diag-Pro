from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect

from src.core.theme_manager import ThemeManager

class ToastNotification(QFrame):
    """
    Notificação Toast animada.
    """
    def __init__(self, parent, message: str, toast_type: str = "info", duration: int = 3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        self._setup_ui(message, toast_type)
        self._duration = duration
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_toast)
        
        self.hide()

    def _setup_ui(self, message: str, toast_type: str):
        self.setProperty("class", "toast-notification")
        c = ThemeManager().colors
        
        colors = {
            "info": "#2196f3",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336"
        }
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        color = colors.get(toast_type, colors["info"])
        icon = icons.get(toast_type, icons["info"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.surface};
                border-left: 4px solid {color};
                border-radius: 4px;
            }}
            QLabel {{
                color: {c.text_primary};
                font-size: 14px;
            }}
            QPushButton {{
                border: none;
                background: transparent;
                color: {c.text_secondary};
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {c.text_primary};
            }}
        """)
        
        layout = QHBoxLayout(self)
        
        self.icon_label = QLabel(icon)
        self.msg_label = QLabel(message)
        self.msg_label.setWordWrap(True)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.hide_toast)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.msg_label, 1)
        layout.addWidget(self.close_btn)
        
        self.adjustSize()
        self.setFixedWidth(300)

    def show_toast_anim(self):
        parent = self.parent()
        if not parent:
            return
            
        self.show()
        self.raise_()
        
        parent_rect = parent.rect()
        start_rect = QRect(parent_rect.width(), 20, self.width(), self.height())
        end_rect = QRect(parent_rect.width() - self.width() - 20, 20, self.width(), self.height())
        
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()
        
        self._timer.start(self._duration)

    def hide_toast(self):
        parent = self.parent()
        if not parent:
            self.deleteLater()
            return
            
        start_rect = self.geometry()
        end_rect = QRect(parent.rect().width(), start_rect.y(), self.width(), self.height())
        
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()

    @classmethod
    def show_toast(cls, parent, message: str, toast_type: str = "info", duration: int = 3000):
        toast = cls(parent, message, toast_type, duration)
        toast.show_toast_anim()
        return toast
