"""
Página de Monitoramento em Tempo Real.
"""
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, Slot

from src.viewmodels.monitoring_vm import MonitoringViewModel
from src.views.widgets.telemetry_chart import TelemetryChart
from src.core.theme_manager import ThemeManager

class MonitoringPage(QWidget):
    """
    Página de Monitoramento Contínuo com gráficos em tempo real.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.view_model = MonitoringViewModel(self)
        self.current_serial: Optional[str] = None
        self._tm = ThemeManager()
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)
        
        # --- Header ---
        self.header_layout = QHBoxLayout()
        
        self.title_layout = QVBoxLayout()
        self.title_label = QLabel("Monitoramento em Tempo Real")
        font_title = self.title_label.font()
        font_title.setPointSize(24)
        font_title.setBold(True)
        self.title_label.setFont(font_title)
        
        self.subtitle_label = QLabel("Telemetria Contínua de CPU, Memória, Temperatura e Energia")
        self.subtitle_label.setStyleSheet("color: gray;")
        
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addWidget(self.subtitle_label)
        self.header_layout.addLayout(self.title_layout)
        
        self.header_layout.addStretch()
        
        # Controles
        self.controls_layout = QHBoxLayout()
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["Rápido (0.5s)", "Normal (1.0s)", "Lento (2.0s)"])
        self.interval_combo.setCurrentIndex(1)
        
        self.btn_toggle = QPushButton("Iniciar Monitoramento")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #198754; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:checked {
                background-color: #dc3545;
            }
        """)
        
        self.btn_clear = QPushButton("Limpar Gráficos")
        self.btn_clear.setStyleSheet("padding: 8px 16px; border-radius: 6px;")
        
        self.controls_layout.addWidget(QLabel("Intervalo:"))
        self.controls_layout.addWidget(self.interval_combo)
        self.controls_layout.addWidget(self.btn_clear)
        self.controls_layout.addWidget(self.btn_toggle)
        
        self.header_layout.addLayout(self.controls_layout)
        self.main_layout.addLayout(self.header_layout)
        
        # --- Charts Grid ---
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(16)
        
        # 1. CPU Chart
        self.cpu_chart = TelemetryChart(title="Utilização de CPU (%)", y_range=(0, 100), y_label="%", buffer_size=120)
        self.lbl_cpu_val = QLabel("CPU: 0%")
        self.lbl_cpu_val.setStyleSheet("font-size: 16px; font-weight: bold;")
        cpu_layout = QVBoxLayout()
        cpu_layout.addWidget(self.lbl_cpu_val)
        cpu_layout.addWidget(self.cpu_chart)
        self.grid_layout.addLayout(cpu_layout, 0, 0)
        
        # 2. Memory Chart
        self.mem_chart = TelemetryChart(title="Uso de Memória (MB)", y_range=(0, 8000), y_label="MB", buffer_size=120)
        self.lbl_mem_val = QLabel("RAM: 0 / 0 MB")
        self.lbl_mem_val.setStyleSheet("font-size: 16px; font-weight: bold;")
        mem_layout = QVBoxLayout()
        mem_layout.addWidget(self.lbl_mem_val)
        mem_layout.addWidget(self.mem_chart)
        self.grid_layout.addLayout(mem_layout, 0, 1)
        
        # 3. Thermal Chart
        self.temp_chart = TelemetryChart(title="Zonas Térmicas (°C)", y_range=(20, 90), y_label="°C", buffer_size=120)
        self.lbl_temp_val = QLabel("Temp CPU: --°C")
        self.lbl_temp_val.setStyleSheet("font-size: 16px; font-weight: bold;")
        temp_layout = QVBoxLayout()
        temp_layout.addWidget(self.lbl_temp_val)
        temp_layout.addWidget(self.temp_chart)
        self.grid_layout.addLayout(temp_layout, 1, 0)
        
        # 4. Battery Chart
        self.bat_chart = TelemetryChart(title="Corrente da Bateria (mA)", y_range=(-3000, 3000), y_label="mA", buffer_size=120)
        self.lbl_bat_val = QLabel("Bateria: 0% | 0mV")
        self.lbl_bat_val.setStyleSheet("font-size: 16px; font-weight: bold;")
        bat_layout = QVBoxLayout()
        bat_layout.addWidget(self.lbl_bat_val)
        bat_layout.addWidget(self.bat_chart)
        self.grid_layout.addLayout(bat_layout, 1, 1)
        
        self.main_layout.addLayout(self.grid_layout, 1)

    def _connect_signals(self) -> None:
        self.btn_toggle.clicked.connect(self._on_toggle_clicked)
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        self.interval_combo.currentIndexChanged.connect(self._on_interval_changed)
        
        self.view_model.cpu_telemetry.connect(self._on_cpu_data)
        self.view_model.memory_telemetry.connect(self._on_memory_data)
        self.view_model.thermal_telemetry.connect(self._on_thermal_data)
        self.view_model.battery_telemetry.connect(self._on_battery_data)
        self.view_model.is_monitoring_changed.connect(self._on_monitoring_state_changed)
        
    def set_device(self, serial: str) -> None:
        """Define o dispositivo atual e para o monitoramento anterior se existir."""
        self.current_serial = serial
        if self.view_model.is_monitoring:
            self.view_model.stop_monitoring()
            self.btn_toggle.setChecked(False)

    @Slot()
    def _on_toggle_clicked(self) -> None:
        if self.btn_toggle.isChecked():
            if self.current_serial:
                self.view_model.start_monitoring(self.current_serial)
            else:
                self.btn_toggle.setChecked(False)
        else:
            self.view_model.stop_monitoring()

    @Slot(bool)
    def _on_monitoring_state_changed(self, active: bool) -> None:
        self.btn_toggle.setChecked(active)
        self.btn_toggle.setText("Pausar Monitoramento" if active else "Iniciar Monitoramento")

    @Slot()
    def _on_clear_clicked(self) -> None:
        self.cpu_chart.clear()
        self.mem_chart.clear()
        self.temp_chart.clear()
        self.bat_chart.clear()

    @Slot(int)
    def _on_interval_changed(self, index: int) -> None:
        intervals = [500, 1000, 2000]
        if 0 <= index < len(intervals):
            self.view_model.set_interval(intervals[index])

    @Slot(float, dict)
    def _on_cpu_data(self, total: float, cores: dict) -> None:
        self.lbl_cpu_val.setText(f"CPU: {total:.1f}%")
        self.cpu_chart.add_multi_values(cores)

    @Slot(float, float, float)
    def _on_memory_data(self, used: float, free: float, cached: float) -> None:
        total = used + free + cached
        if total > 0:
            self.lbl_mem_val.setText(f"RAM: {used/1024:.1f} / {total/1024:.1f} GB")
            # Ajusta limite Y dinamicamente caso seja maior que o padrão (8000 MB)
            max_y = max(8000.0, total)
            self.mem_chart.plot_widget.setYRange(0, max_y)
        self.mem_chart.add_multi_values({'Usado': used, 'Livre': free, 'Cache': cached})

    @Slot(dict)
    def _on_thermal_data(self, zones: dict) -> None:
        cpu_temp = zones.get('CPU', 0.0)
        self.lbl_temp_val.setText(f"Temp CPU: {cpu_temp:.1f}°C")
        self.temp_chart.add_multi_values(zones)

    @Slot(float, int, int)
    def _on_battery_data(self, level: float, voltage: int, current: int) -> None:
        self.lbl_bat_val.setText(f"Bateria: {level:.0f}% | {voltage}mV")
        self.bat_chart.add_multi_values({'Corrente': current})
