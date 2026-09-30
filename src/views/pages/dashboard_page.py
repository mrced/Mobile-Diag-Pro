from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal

from src.views.widgets.device_card import DeviceCard
from src.views.widgets.gauge_widget import GaugeWidget
from src.core.theme_manager import ThemeManager

# Assumindo a existência destes modelos
# from src.models.device import DeviceInfo
# from src.models.battery import BatteryInfo
# from src.models.cpu import CPUInfo
# from src.models.memory import MemoryInfo
# from src.models.thermal import ThermalInfo

class DashboardPage(QWidget):
    """
    Página de Dashboard contendo a visão geral do dispositivo.
    """
    
    action_reboot = Signal()
    action_screenshot = Signal()
    action_screen_record = Signal()
    action_open_shell = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tm = ThemeManager()
        self._setup_ui()
        self._tm.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setStyleSheet("background-color: transparent;")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("Dashboard")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Visão geral do dispositivo")
        subtitle.setProperty("class", "secondary")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Device Card
        self.device_card = DeviceCard()
        layout.addWidget(self.device_card)
        
        # Gauges Row
        gauges_layout = QHBoxLayout()
        
        self.gauge_battery = GaugeWidget(title="Bateria", suffix="%")
        self.gauge_battery.setThresholds(60, 20)  # Precisa ajustar para coloração invertida se necessário
        
        self.gauge_battery_health = GaugeWidget(title="Saúde Bateria", suffix="%")
        self.gauge_battery_health.setThresholds(80, 50)
        
        self.gauge_cpu_temp = GaugeWidget(title="Temperatura CPU", suffix="°C", max_value=100)
        self.gauge_cpu_temp.setThresholds(50, 70)
        
        self.gauge_ram = GaugeWidget(title="Uso RAM", suffix="%")
        self.gauge_ram.setThresholds(70, 90)
        
        self.gauges = [self.gauge_battery, self.gauge_battery_health, self.gauge_cpu_temp, self.gauge_ram]
        
        gauges_layout.addWidget(self.gauge_battery)
        gauges_layout.addWidget(self.gauge_battery_health)
        gauges_layout.addWidget(self.gauge_cpu_temp)
        gauges_layout.addWidget(self.gauge_ram)
        
        layout.addLayout(gauges_layout)
        
        # Ações Rápidas
        actions_label = QLabel("Ações Rápidas")
        actions_label.setProperty("class", "section-title")
        layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        
        self.btn_reboot = self._create_action_btn("🔄", "Reiniciar")
        self.btn_reboot.clicked.connect(self.action_reboot)
        
        self.btn_screenshot = self._create_action_btn("📸", "Screenshot")
        self.btn_screenshot.clicked.connect(self.action_screenshot)
        
        self.btn_screen_record = self._create_action_btn("🎥", "Gravar Tela")
        self.btn_screen_record.clicked.connect(self.action_screen_record)
        
        self.btn_shell = self._create_action_btn("💻", "Abrir Shell")
        self.btn_shell.clicked.connect(self.action_open_shell)
        
        actions_layout.addWidget(self.btn_reboot)
        actions_layout.addWidget(self.btn_screenshot)
        actions_layout.addWidget(self.btn_screen_record)
        actions_layout.addWidget(self.btn_shell)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _create_action_btn(self, icon: str, text: str) -> QPushButton:
        btn = QPushButton()
        btn.setProperty("class", "card")
        layout = QVBoxLayout(btn)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setProperty("class", "action-icon")
        
        lbl_text = QLabel(text)
        lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_text.setProperty("class", "action-text")
        
        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_text)
        
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(100)
        return btn

    def update_device_info(self, info):
        self.device_card.update_device(info)

    def update_battery(self, info):
        self.gauge_battery.value = getattr(info, 'level', 0.0)
        self.gauge_battery_health.value = getattr(info, 'health_percent', 0.0)

    def update_cpu(self, info):
        pass # Atualizar widgets específicos de CPU se houverem

    def update_memory(self, info):
        self.gauge_ram.value = getattr(info, 'percent', 0.0)

    def update_thermal(self, info):
        self.gauge_cpu_temp.value = getattr(info, 'cpu_temp', 0.0)

    def clear(self):
        self.device_card.clear()
        for gauge in self.gauges:
            gauge.value = 0

    def _on_theme_changed(self, theme: str) -> None:
        """Garante que os gauges e outros elementos sejam atualizados quando o tema mudar."""
        for gauge in self.gauges:
            gauge.update()
