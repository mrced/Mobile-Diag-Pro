from dataclasses import dataclass
from src.core.constants import BatteryHealth, BatteryStatus

@dataclass
class BatteryInfo:
    """Modelo de dados contendo informações da bateria."""
    level: int = 0
    voltage: int = 0  # mV
    temperature: float = 0.0  # Celsius
    health: BatteryHealth = BatteryHealth.UNKNOWN
    status: BatteryStatus = BatteryStatus.UNKNOWN
    technology: str = ''
    present: bool = True
    ac_powered: bool = False
    usb_powered: bool = False
    wireless_powered: bool = False
    max_charging_current: int = 0  # µA
    max_charging_voltage: int = 0  # µV
    charge_counter: int = 0  # µAh
    cycle_count: int = -1  # -1 = unavailable
    charge_full: int = -1  # µAh current capacity
    charge_full_design: int = -1  # µAh factory capacity
    health_percentage: float = -1.0  # calculated: full/design*100
