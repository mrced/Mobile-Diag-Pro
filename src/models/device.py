from dataclasses import dataclass
from src.core.constants import DeviceMode

@dataclass
class DeviceInfo:
    """Modelo de dados contendo informações do dispositivo."""
    serial: str = ''
    manufacturer: str = ''
    model: str = ''
    brand: str = ''
    device_name: str = ''
    android_version: str = ''
    sdk_version: int = 0
    security_patch: str = ''
    build_id: str = ''
    cpu_abi: str = ''
    platform: str = ''
    bootloader: str = ''
    baseband: str = ''
    mode: DeviceMode = DeviceMode.UNKNOWN
    is_rooted: bool = False
    bootloader_unlocked: bool = False
    verified_boot_state: str = ''
    encryption_state: str = ''
    usb_state: str = ''
    driver_missing: bool = False
    status_message: str = ''
    hardware_id: str = ''
    usb_desc: str = ''
