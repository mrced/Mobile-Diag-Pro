from dataclasses import dataclass, field
from src.core.constants import ThermalStatus

@dataclass
class ThermalZone:
    """Zona térmica."""
    name: str = ''
    temperature: float = 0.0  # Celsius
    zone_type: str = ''

@dataclass
class ThermalInfo:
    """Informações térmicas do dispositivo."""
    status: ThermalStatus = ThermalStatus.NONE
    zones: list[ThermalZone] = field(default_factory=list)
    cpu_temp: float = 0.0
    gpu_temp: float = 0.0
    battery_temp: float = 0.0
    skin_temp: float = 0.0
