"""
Gerenciador de configurações da aplicação.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import QObject, Signal


class ConfigManager(QObject):
    """
    Gerenciador singleton de configurações.
    """
    config_changed = Signal(str, object)
    
    _instance = None
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self) -> None:
        if getattr(self, '_initialized', False):
            return
        super().__init__()
        self._initialized = True
        self._config_dir: Path = Path.home() / ".mobile-diag-pro"
        self._config_file: Path = self._config_dir / "config.json"
        
        self._default_config: Dict[str, Any] = {
            "platform_tools_path": "",
            "theme": "dark",
            "language": "pt_BR",
            "polling_interval": 1000,
            "telemetry_interval": 500,
            "backup_dir": str(Path.home() / "MobileDiagBackups"),
            "log_level": "DEBUG",
            "auto_update": True,
            "recent_devices": []
        }
        
        self._config: Dict[str, Any] = self._default_config.copy()
        self.load()

    def load(self) -> None:
        """Carrega as configurações do arquivo JSON."""
        if not self._config_file.exists():
            self.save()
            return
            
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self._config.update(loaded)
        except Exception:
            # Em caso de erro, continua com os padrões
            pass

    def save(self) -> None:
        """Salva as configurações atuais no arquivo JSON."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor da configuração."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Define um valor na configuração e notifica ouvintes se alterar."""
        if key in self._config and self._config[key] == value:
            return
            
        self._config[key] = value
        self.save()
        self.config_changed.emit(key, value)
        
    @property
    def platform_tools_path(self) -> str:
        return self.get("platform_tools_path", "")
        
    @platform_tools_path.setter
    def platform_tools_path(self, value: str) -> None:
        self.set("platform_tools_path", value)
        
    @property
    def theme(self) -> str:
        return self.get("theme", "dark")
        
    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)
        
    @property
    def language(self) -> str:
        return self.get("language", "pt_BR")
        
    @language.setter
    def language(self, value: str) -> None:
        self.set("language", value)
        
    @property
    def polling_interval(self) -> int:
        return self.get("polling_interval", 1000)
        
    @polling_interval.setter
    def polling_interval(self, value: int) -> None:
        self.set("polling_interval", value)
        
    @property
    def telemetry_interval(self) -> int:
        return self.get("telemetry_interval", 500)
        
    @telemetry_interval.setter
    def telemetry_interval(self, value: int) -> None:
        self.set("telemetry_interval", value)
        
    @property
    def backup_dir(self) -> str:
        return self.get("backup_dir", str(Path.home() / "MobileDiagBackups"))
        
    @backup_dir.setter
    def backup_dir(self, value: str) -> None:
        self.set("backup_dir", value)
        
    @property
    def log_level(self) -> str:
        return self.get("log_level", "DEBUG")
        
    @log_level.setter
    def log_level(self, value: str) -> None:
        self.set("log_level", value)
        
    @property
    def auto_update(self) -> bool:
        return self.get("auto_update", True)
        
    @auto_update.setter
    def auto_update(self, value: bool) -> None:
        self.set("auto_update", value)
        
    @property
    def recent_devices(self) -> list:
        return self.get("recent_devices", [])
        
    @recent_devices.setter
    def recent_devices(self, value: list) -> None:
        self.set("recent_devices", value)
