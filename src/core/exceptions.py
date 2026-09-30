"""
Exceções customizadas do Mobile-Diag-Pro.
"""

class MobileDiagError(Exception):
    """Exceção base para o Mobile-Diag-Pro."""
    pass

class ADBConnectionError(MobileDiagError):
    """Erro de conexão com o servidor ADB."""
    pass

class ADBTimeoutError(MobileDiagError):
    """Tempo limite excedido na comunicação ADB."""
    pass

class ADBCommandError(MobileDiagError):
    """Erro ao executar comando ADB."""
    def __init__(self, command: str, stderr: str, message: str = "Erro no comando ADB") -> None:
        self.command = command
        self.stderr = stderr
        super().__init__(f"{message}: {command} -> {stderr}")

class FastbootError(MobileDiagError):
    """Erro em operações Fastboot."""
    pass

class FlashError(MobileDiagError):
    """Erro durante o procedimento de flash."""
    pass

class DeviceNotFoundError(MobileDiagError):
    """Dispositivo não encontrado."""
    pass

class UnauthorizedDeviceError(MobileDiagError):
    """Dispositivo ADB não autorizado."""
    pass

class InvalidFirmwareError(MobileDiagError):
    """Firmware inválido ou corrompido."""
    pass

class BackupError(MobileDiagError):
    """Erro em operações de backup."""
    pass
