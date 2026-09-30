from dataclasses import dataclass, field

@dataclass
class CPUCore:
    """Informações sobre um núcleo de CPU."""
    index: int = 0
    current_freq: int = 0  # kHz
    min_freq: int = 0
    max_freq: int = 0
    online: bool = True

@dataclass
class CPUInfo:
    """Informações gerais sobre o processador."""
    model: str = ''
    architecture: str = ''
    core_count: int = 0
    features: list[str] = field(default_factory=list)
    cores: list[CPUCore] = field(default_factory=list)
    total_usage: float = 0.0  # percentage
    user_usage: float = 0.0
    system_usage: float = 0.0
    io_wait: float = 0.0
