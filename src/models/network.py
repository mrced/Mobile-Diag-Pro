from dataclasses import dataclass, field

@dataclass
class WiFiInfo:
    """Informações de WiFi."""
    ssid: str = ''
    bssid: str = ''
    rssi: int = 0  # dBm
    link_speed: int = 0  # Mbps
    frequency: int = 0  # MHz
    mac_address: str = ''
    ip_address: str = ''
    connected: bool = False

@dataclass
class CellularInfo:
    """Informações da rede celular."""
    signal_strength: int = 0  # dBm
    network_type: str = ''
    operator: str = ''
    sim_state: str = ''
    data_connected: bool = False

@dataclass
class NetworkInfo:
    """Informações de rede (WiFi e Celular)."""
    wifi: WiFiInfo = field(default_factory=WiFiInfo)
    cellular: CellularInfo = field(default_factory=CellularInfo)
