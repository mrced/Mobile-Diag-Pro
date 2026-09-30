"""Gerenciador de temas — controla a alternância entre temas claro e escuro."""
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from src.core.logger import get_logger

logger = get_logger(__name__)


class ThemeColors:
    """Armazena as cores do tema ativo para uso em widgets com QPainter."""
    
    def __init__(self, is_dark: bool = True):
        if is_dark:
            # macOS Dark
            self.background = "#1c1c1e"
            self.sidebar = "#252527"
            self.surface = "#2c2c2e"
            self.elevated = "#3a3a3c"
            self.separator = "#48484a"
            self.muted = "#636366"
            self.accent = "#0a84ff"
            self.text_primary = "#f5f5f7"
            self.text_secondary = "#98989d"
            self.success = "#30d158"
            self.warning = "#ff9f0a"
            self.danger = "#ff453a"
            self.chart_bg = "#1c1c1e"
            self.gauge_track = "#3a3a3c"
        else:
            # macOS Light
            self.background = "#f5f5f7"
            self.sidebar = "#e8e8ed"
            self.surface = "#ffffff"
            self.elevated = "#e5e5ea"
            self.separator = "#d1d1d6"
            self.muted = "#aeaeb2"
            self.accent = "#007aff"
            self.text_primary = "#1d1d1f"
            self.text_secondary = "#86868b"
            self.success = "#34c759"
            self.warning = "#ff9500"
            self.danger = "#ff3b30"
            self.chart_bg = "#ffffff"
            self.gauge_track = "#e5e5ea"


class ThemeManager(QObject):
    """Gerenciador de temas singleton."""
    
    theme_changed = Signal(str)  # 'dark' or 'light'
    
    _instance: Optional['ThemeManager'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        self._current_theme = 'dark'
        self._colors = ThemeColors(is_dark=True)
        self._root_dir = Path(__file__).resolve().parent.parent.parent  # project root
    
    @property
    def current_theme(self) -> str:
        return self._current_theme
    
    @property
    def colors(self) -> ThemeColors:
        return self._colors
    
    @property
    def is_dark(self) -> bool:
        return self._current_theme == 'dark'
    
    def set_theme(self, theme: str) -> None:
        """Define o tema ('dark' ou 'light')."""
        if theme not in ('dark', 'light'):
            logger.warning(f"Tema inválido: {theme}")
            return
        if theme == self._current_theme:
            return
        
        self._current_theme = theme
        self._colors = ThemeColors(is_dark=(theme == 'dark'))
        self._apply_stylesheet()
        self.theme_changed.emit(theme)
        logger.info(f"Tema alterado para: {theme}")
    
    def toggle_theme(self) -> None:
        """Alterna entre dark e light."""
        new_theme = 'light' if self._current_theme == 'dark' else 'dark'
        self.set_theme(new_theme)
    
    def _apply_stylesheet(self) -> None:
        """Aplica o QSS do tema atual."""
        app = QApplication.instance()
        if not app:
            return
        from src.utils.platform_utils import get_resource_path
        qss_path = get_resource_path(f"assets/themes/{self._current_theme}.qss")
        if qss_path.exists():
            with open(qss_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
            logger.info(f"Stylesheet aplicado: {qss_path}")
        else:
            logger.warning(f"Stylesheet não encontrado: {qss_path}")
    
    def initialize(self, theme: str = 'dark') -> None:
        """Inicializa o tema na primeira execução."""
        self._current_theme = theme
        self._colors = ThemeColors(is_dark=(theme == 'dark'))
        self._apply_stylesheet()
        logger.info(f"Tema inicializado: {theme}")
