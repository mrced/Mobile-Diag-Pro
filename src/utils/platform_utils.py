"""
Utilitários específicos de plataforma.
"""
import os
import platform
from pathlib import Path

def get_platform() -> str:
    """Retorna a plataforma atual ('windows', 'linux', 'darwin')."""
    sys_plat = platform.system().lower()
    if sys_plat == 'darwin':
        return 'darwin'
    elif sys_plat == 'linux':
        return 'linux'
    else:
        return 'windows'

def get_platform_tools_dir() -> Path:
    """Retorna o diretório platform_tools para a plataforma atual."""
    base_dir = Path(__file__).parent.parent.parent
    plat = get_platform()
    return base_dir / "platform_tools" / plat

def get_adb_path() -> Path:
    """Retorna o caminho completo para o executável do adb."""
    tools_dir = get_platform_tools_dir()
    executable = "adb.exe" if get_platform() == 'windows' else "adb"
    return tools_dir / executable

def get_fastboot_path() -> Path:
    """Retorna o caminho completo para o executável do fastboot."""
    tools_dir = get_platform_tools_dir()
    executable = "fastboot.exe" if get_platform() == 'windows' else "fastboot"
    return tools_dir / executable

def get_config_dir() -> Path:
    """Retorna e cria o diretório de configurações."""
    config_dir = Path.home() / ".mobile-diag-pro"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_log_dir() -> Path:
    """Retorna e cria o diretório de logs."""
    log_dir = get_config_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def is_adb_available() -> bool:
    """Verifica se o binário do ADB está disponível e executável."""
    adb_path = get_adb_path()
    return adb_path.exists() and os.access(adb_path, os.X_OK)

def is_fastboot_available() -> bool:
    """Verifica se o binário do Fastboot está disponível e executável."""
    fastboot_path = get_fastboot_path()
    return fastboot_path.exists() and os.access(fastboot_path, os.X_OK)
