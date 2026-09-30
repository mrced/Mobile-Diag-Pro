"""
Utilitários específicos de plataforma e resolução de recursos para PyInstaller e execução normal.
"""
import os
import sys
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


def get_app_root_dir() -> Path:
    """
    Retorna o diretório raiz da aplicação.
    Compatível com execução direta via Python e empacotamento PyInstaller (--onefile e --onedir).
    """
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def get_resource_path(relative_path: str) -> Path:
    """
    Resolve o caminho absoluto para arquivos de assets/recursos,
    buscando no _MEIPASS, na pasta do executável ou no diretório de desenvolvimento.
    """
    root = get_app_root_dir()
    candidate = root / relative_path
    if candidate.exists():
        return candidate

    if getattr(sys, 'frozen', False):
        # Tentar ao lado do executável
        candidate_exe = Path(sys.executable).parent / relative_path
        if candidate_exe.exists():
            return candidate_exe

        # Tentar dentro de _internal (PyInstaller onedir)
        candidate_internal = Path(sys.executable).parent / "_internal" / relative_path
        if candidate_internal.exists():
            return candidate_internal

    return candidate


def get_platform_tools_dir() -> Path:
    """Retorna o diretório platform_tools para a plataforma atual."""
    root = get_app_root_dir()
    plat = get_platform()
    return root / "platform_tools" / plat


def get_adb_path() -> Path:
    """Retorna o caminho para o executável do adb (bundled ou no PATH)."""
    tools_dir = get_platform_tools_dir()
    executable = "adb.exe" if get_platform() == 'windows' else "adb"
    bundled = tools_dir / executable
    if bundled.exists():
        return bundled
    # Fallback para o PATH do sistema
    return Path(executable)


def get_fastboot_path() -> Path:
    """Retorna o caminho para o executável do fastboot (bundled ou no PATH)."""
    tools_dir = get_platform_tools_dir()
    executable = "fastboot.exe" if get_platform() == 'windows' else "fastboot"
    bundled = tools_dir / executable
    if bundled.exists():
        return bundled
    # Fallback para o PATH do sistema
    return Path(executable)


def get_config_dir() -> Path:
    """Retorna e cria o diretório de configurações ~/.mobile-diag-pro."""
    config_dir = Path.home() / ".mobile-diag-pro"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_log_dir() -> Path:
    """Retorna e cria o diretório de logs."""
    log_dir = get_config_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def is_adb_available() -> bool:
    """Verifica se o binário do ADB está acessível."""
    adb_path = get_adb_path()
    return adb_path.exists() and os.access(adb_path, os.X_OK)


def is_fastboot_available() -> bool:
    """Verifica se o binário do Fastboot está acessível."""
    fastboot_path = get_fastboot_path()
    return fastboot_path.exists() and os.access(fastboot_path, os.X_OK)
