from PySide6.QtCore import QObject, Signal

class DashboardViewModel(QObject):
    """
    ViewModel para a página de Dashboard.
    Gerencia o estado e comunicação com a camada de serviço.
    """
    
    device_info_updated = Signal(object)  # DeviceInfo
    battery_updated = Signal(object)  # BatteryInfo
    cpu_updated = Signal(object)  # CPUInfo
    memory_updated = Signal(object)  # MemoryInfo
    thermal_updated = Signal(object)  # ThermalInfo
    device_disconnected = Signal()
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_device_info = None
        self.current_battery = None
        self.current_cpu = None
        self.current_memory = None
        self.current_thermal = None

    def refresh_all(self, serial: str):
        """
        Solicita a atualização de todos os dados do dispositivo.
        A ser conectado aos serviços ADB.
        """
        # TODO: Implementar chamadas assíncronas aos serviços ADB
        pass

    def clear(self):
        """Limpa o estado atual e emite sinal de desconexão."""
        self.current_device_info = None
        self.current_battery = None
        self.current_cpu = None
        self.current_memory = None
        self.current_thermal = None
        self.device_disconnected.emit()
