"""
ViewModel para a tela de monitoramento em tempo real.
"""
from typing import Optional, Dict

from PySide6.QtCore import QObject, Signal, QTimer, Slot

from src.core.command_executor import CommandExecutor
from src.core.adb_client import ADBClient
from src.core.adb_commands import ADBCommands
from src.core.logger import get_logger

logger = get_logger(__name__)

class MonitoringViewModel(QObject):
    """
    ViewModel para monitoramento contínuo de telemetria.
    """
    
    cpu_telemetry = Signal(float, dict) # total_cpu_pct, {core0: pct, core1: pct...}
    memory_telemetry = Signal(float, float, float) # used_mb, free_mb, cached_mb
    thermal_telemetry = Signal(dict) # {cpu: temp, battery: temp, gpu: temp, skin: temp}
    battery_telemetry = Signal(float, int, int) # level, voltage_mv, current_ma
    is_monitoring_changed = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Inicializa o ViewModel de Monitoramento."""
        super().__init__(parent)
        self._serial: Optional[str] = None
        self._is_monitoring: bool = False
        self._interval_ms: int = 1000
        
        self._timer = QTimer(self)
        self._timer.setInterval(self._interval_ms)
        self._timer.timeout.connect(self._fetch_telemetry)
        
        # Executor e Comandos
        self._executor = CommandExecutor()
        self._adb_client = ADBClient()
        self._adb_commands = ADBCommands(self._adb_client)
        
    @property
    def is_monitoring(self) -> bool:
        """Retorna se o monitoramento está ativo."""
        return self._is_monitoring
        
    def start_monitoring(self, serial: str) -> None:
        """Inicia o monitoramento para um dispositivo específico."""
        if not serial:
            logger.warning("Não é possível iniciar monitoramento: serial não fornecido")
            return
            
        self._serial = serial
        self._is_monitoring = True
        self._timer.start()
        self.is_monitoring_changed.emit(self._is_monitoring)
        logger.info(f"Monitoramento iniciado no dispositivo {serial} com intervalo {self._interval_ms}ms")
        
    def stop_monitoring(self) -> None:
        """Para o monitoramento contínuo."""
        self._is_monitoring = False
        self._timer.stop()
        self.is_monitoring_changed.emit(self._is_monitoring)
        logger.info("Monitoramento parado")
        
    def set_interval(self, ms: int) -> None:
        """Define o intervalo de atualização do monitoramento."""
        self._interval_ms = max(500, min(2000, ms))
        self._timer.setInterval(self._interval_ms)
        logger.debug(f"Intervalo de monitoramento alterado para {self._interval_ms}ms")

    @Slot()
    def _fetch_telemetry(self) -> None:
        """Busca os dados de telemetria assincronamente usando CommandExecutor."""
        if not self._serial:
            return
            
        # Busca em background para não travar a GUI
        worker_signals = self._executor.submit(self._fetch_all_data, self._serial)
        worker_signals.result.connect(self._process_telemetry)
        worker_signals.error.connect(lambda e: logger.error(f"Erro no monitoramento: {e}"))

    def _fetch_all_data(self, serial: str) -> dict:
        """Função bloqueante executada em background para coletar os dados."""
        cpu = self._adb_commands.get_cpu_info(serial)
        mem = self._adb_commands.get_memory_info(serial)
        temp = self._adb_commands.get_thermal_info(serial)
        bat = self._adb_commands.get_battery_info(serial)
        
        return {
            'cpu': cpu,
            'mem': mem,
            'temp': temp,
            'bat': bat
        }

    @Slot(object)
    def _process_telemetry(self, data: dict) -> None:
        """Processa os dados retornados do worker e emite sinais."""
        if not self._is_monitoring:
            return
            
        # CPU
        cpu_data = data.get('cpu', {})
        total_cpu = cpu_data.get('total_usage', 0.0)
        cores = cpu_data.get('cores', {})
        if not isinstance(cores, dict):
            cores = {}
        if not cores:
            # Fake cores if missing from adb parser
            cores = {'Core 0': total_cpu}
        self.cpu_telemetry.emit(total_cpu, cores)
        
        # Memory
        mem_data = data.get('mem', {})
        total_kb = mem_data.get('MemTotal', 1)
        free_kb = mem_data.get('MemFree', 0)
        cached_kb = mem_data.get('Cached', 0)
        
        used_mb = max(0, (total_kb - free_kb - cached_kb) / 1024.0)
        free_mb = free_kb / 1024.0
        cached_mb = cached_kb / 1024.0
        self.memory_telemetry.emit(used_mb, free_mb, cached_mb)
        
        # Thermal
        temp_data = data.get('temp', {})
        zones = temp_data.get('zones', {})
        cpu_temp = 40.0
        battery_temp = 35.0
        gpu_temp = 40.0
        skin_temp = 30.0
        
        for name, value in zones.items():
            name_lower = name.lower()
            val = float(value) / 1000.0 if float(value) > 1000 else float(value)
            
            if 'cpu' in name_lower or 'tsens' in name_lower:
                cpu_temp = max(cpu_temp, val)
            elif 'batt' in name_lower or 'bms' in name_lower:
                battery_temp = max(battery_temp, val)
            elif 'gpu' in name_lower:
                gpu_temp = max(gpu_temp, val)
            elif 'skin' in name_lower or 'quiet' in name_lower:
                skin_temp = max(skin_temp, val)
                
        thermal_dict = {
            'CPU': cpu_temp,
            'Bateria': battery_temp,
            'GPU': gpu_temp,
            'Chassi': skin_temp
        }
        self.thermal_telemetry.emit(thermal_dict)
        
        # Battery
        bat_data = data.get('bat', {})
        level = float(bat_data.get('level', 0.0))
        voltage = int(bat_data.get('voltage', 0))
        current = int(bat_data.get('current now', 0))
        self.battery_telemetry.emit(level, voltage, current)
