from dataclasses import dataclass, field

@dataclass
class PartitionMap:
    """Mapeamento de partição para flash."""
    name: str = ''
    image_path: str = ''
    is_logical: bool = False
    slot: str = ''  # 'a', 'b', or ''
    size: int = 0
    is_sparse: bool = False

@dataclass
class FlashJob:
    """Configuração de trabalho de flash."""
    device_serial: str = ''
    partitions: list[PartitionMap] = field(default_factory=list)
    wipe_data: bool = False
    disable_avb: bool = False
    reboot_after: bool = True
    slot: str = ''  # target slot
    is_ab_device: bool = False
    is_dynamic: bool = False
