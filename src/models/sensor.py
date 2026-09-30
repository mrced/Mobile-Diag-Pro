from dataclasses import dataclass

@dataclass
class SensorInfo:
    """Informações de sensor."""
    name: str = ''
    sensor_type: str = ''
    vendor: str = ''
    version: int = 0
    power: float = 0.0  # mA
    resolution: float = 0.0
    max_range: float = 0.0
    available: bool = True
