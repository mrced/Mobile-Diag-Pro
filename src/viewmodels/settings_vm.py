"""
Settings ViewModel.
"""
import subprocess
from typing import Dict, Any, Optional

from PySide6.QtCore import QObject, Signal

from src.core.config_manager import ConfigManager
from src.core.theme_manager import ThemeManager

class SettingsViewModel(QObject):
    """
    ViewModel para gerenciar configurações.
    """
    settings_saved = Signal()
    theme_changed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.theme_manager = ThemeManager()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Obtém uma configuração pelo nome."""
        return self.config_manager.get(key, default)

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Salva um dicionário de configurações."""
        for k, v in settings.items():
            self.config_manager.set(k, v)
        self.config_manager.save()
        self.settings_saved.emit()

    def reset_to_defaults(self) -> None:
        """Restaura as configurações de fábrica."""
        self.config_manager.reset_to_defaults()
        self.settings_saved.emit()

    def detect_platform_tools(self) -> str:
        """
        Detecta o caminho do adb (bundled vs system) e testa a conexão.
        Retorna uma mensagem de status.
        """
        try:
            import sys
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(["adb", "version"], capture_output=True, text=True, check=True, creationflags=flags)
            return f"ADB Detectado (Sistema): {result.stdout.splitlines()[0]}"
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "ADB não detectado no sistema."
