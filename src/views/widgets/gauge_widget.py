from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from src.core.theme_manager import ThemeManager

class GaugeWidget(QWidget):
    """
    Widget de medidor circular (gauge) para exibição de valores percentuais ou absolutos.
    """
    def __init__(self, title: str = "", suffix: str = "%", max_value: float = 100.0, parent=None):
        super().__init__(parent)
        self.setProperty("class", "gauge-widget")
        self.setMinimumSize(150, 150)
        
        self._value = 0.0
        self._max_value = max_value
        self._title = title
        self._suffix = suffix
        
        self._warning_threshold = 60.0
        self._critical_threshold = 85.0
        
        self._tm = ThemeManager()
        self._tm.theme_changed.connect(lambda _: self.update())
        
        self._anim = QPropertyAnimation(self, b"anim_value", self)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim.setDuration(500)

    def get_anim_value(self) -> float:
        return self._value

    def set_anim_value(self, val: float) -> None:
        self._value = val
        self.update()

    anim_value = Property(float, get_anim_value, set_anim_value)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        val = max(0.0, min(val, self._max_value))
        if self._value != val:
            self._anim.stop()
            self._anim.setStartValue(self._value)
            self._anim.setEndValue(val)
            self._anim.start()

    def setThresholds(self, warning: float, critical: float) -> None:
        self._warning_threshold = warning
        self._critical_threshold = critical
        self.update()

    def _get_color(self) -> QColor:
        c = self._tm.colors
        if self._value >= self._critical_threshold:
            return QColor(c.danger)
        elif self._value >= self._warning_threshold:
            return QColor(c.warning)
        return QColor(c.accent)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        size = min(width, height) - 20
        rect = QRectF((width - size) / 2, (height - size) / 2 - 10, size, size)
        
        c = self._tm.colors
        
        # Draw background arc
        bg_pen = QPen(QColor(c.gauge_track), 12)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 225 * 16, -270 * 16)
        
        # Draw value arc
        span_angle = -int((self._value / self._max_value) * 270 * 16)
        val_pen = QPen(self._get_color(), 12)
        val_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(val_pen)
        painter.drawArc(rect, 225 * 16, span_angle)
        
        # Draw text value
        painter.setPen(QColor(c.text_primary))
        font = QFont()
        font.setPixelSize(24)
        font.setBold(True)
        painter.setFont(font)
        text_rect = QRectF(rect.x(), rect.y(), rect.width(), rect.height())
        val_text = f"{int(self._value)}{self._suffix}"
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, val_text)
        
        # Draw title
        font.setPixelSize(14)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor(c.text_secondary))
        title_rect = QRectF(0, rect.bottom() + 5, width, 30)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop, self._title)
