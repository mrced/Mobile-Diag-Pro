from dataclasses import dataclass

@dataclass
class MemoryInfo:
    """Informações sobre o uso de memória."""
    total: int = 0  # bytes
    free: int = 0
    available: int = 0
    buffers: int = 0
    cached: int = 0
    swap_total: int = 0
    swap_free: int = 0
    zram_used: int = 0
    usage_percentage: float = 0.0  # calculated
