from dataclasses import dataclass, field

@dataclass
class PartitionInfo:
    """Informações de uma partição de armazenamento."""
    name: str = ''
    filesystem: str = ''
    size: str = ''
    used: str = ''
    free: str = ''
    use_percent: str = ''
    mount_point: str = ''

@dataclass
class StorageInfo:
    """Informações do armazenamento do dispositivo."""
    partitions: list[PartitionInfo] = field(default_factory=list)
    total_internal: str = ''
    free_internal: str = ''
    total_sdcard: str = ''
    free_sdcard: str = ''
