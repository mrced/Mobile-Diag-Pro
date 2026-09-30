"""
Constantes globais do sistema.
"""
from enum import Enum

APP_NAME: str = 'Mobile-Diag-Pro'
APP_VERSION: str = '1.0.0'
ADB_SERVER_PORT: int = 5037
DEFAULT_TIMEOUT: int = 10
POLLING_INTERVAL: int = 1000
TELEMETRY_INTERVAL: int = 500

class DeviceMode(Enum):
    """Modo do dispositivo."""
    UNKNOWN = "unknown"
    ADB_NORMAL = "adb_normal"
    ADB_UNAUTHORIZED = "adb_unauthorized"
    RECOVERY = "recovery"
    SIDELOAD = "sideload"
    FASTBOOT = "fastboot"
    FASTBOOTD = "fastbootd"
    SAMSUNG_DOWNLOAD = "samsung_download"
    QUALCOMM_EDL = "qualcomm_edl"
    MEDIATEK_BROM = "mediatek_brom"
    DRIVER_MISSING = "driver_missing"
    USB_NO_DEBUGGING = "usb_no_debugging"

class TestStatus(Enum):
    """Status dos testes de diagnóstico."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"

class BatteryHealth(Enum):
    """Saúde da bateria."""
    UNKNOWN = 1
    GOOD = 2
    OVERHEAT = 3
    DEAD = 4
    OVER_VOLTAGE = 5
    FAILURE = 6
    COLD = 7

class BatteryStatus(Enum):
    """Status de carregamento da bateria."""
    UNKNOWN = 1
    CHARGING = 2
    DISCHARGING = 3
    NOT_CHARGING = 4
    FULL = 5

class ThermalStatus(Enum):
    """Status térmico."""
    NONE = 0
    LIGHT = 1
    MODERATE = 2
    SEVERE = 3
    CRITICAL = 4
    EMERGENCY = 5
    SHUTDOWN = 6

KNOWN_VENDORS: dict[str, str] = {
    "0x04e8": "Samsung",
    "0x18d1": "Google",
    "0x2717": "Xiaomi",
    "0x2a70": "OnePlus",
    "0x22b8": "Motorola",
    "0x0fce": "Sony",
    "0x1004": "LG",
    "0x12d1": "Huawei",
    "0x22d9": "OPPO",
    "0x05c6": "Qualcomm",
    "0x0e8d": "MediaTek",
    "0x31ef": "Xiaomi / JLQ",
    "0x1782": "Spreadtrum / Unisoc",
    "0x2e04": "HMD Global / Nokia",
    "0x19d2": "ZTE",
    "0x0bb4": "HTC",
    "0x0b05": "ASUS"
}

EDL_PIDS: dict[str, str] = {
    "0x9008": "Qualcomm HS-USB QDLoader 9008"
}

# Constantes de cor padrão do tema escuro (macOS Dark)
BG_PRIMARY: str = "#1c1c1e"
BG_SECONDARY: str = "#252527"
BG_SURFACE: str = "#2c2c2e"
ACCENT_PRIMARY: str = "#0a84ff"
COLOR_SUCCESS: str = "#30d158"
COLOR_WARNING: str = "#ff9f0a"
COLOR_DANGER: str = "#ff453a"
TEXT_PRIMARY: str = "#f5f5f7"
TEXT_SECONDARY: str = "#98989d"
