import sys
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QMainWindow, QStatusBar
)

from src.views.title_bar import TitleBar
from src.views.sidebar import Sidebar


class MainWindow(QMainWindow):
    """
    Janela principal da aplicação.
    Gerencia o layout com barra de título customizada, barra lateral e área de conteúdo.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1200, 800)

        # Configurações iniciais
        self._setup_ui()
        self._connect_signals()
        
        # Geometria da janela para restauração
        self._normal_geometry = self.geometry()
        self._resizing = False

    def _setup_ui(self) -> None:
        """Configura a interface de usuário principal."""
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Barra de Título
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)

        # Layout do Corpo
        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        # Barra Lateral
        self.sidebar = Sidebar(self)
        self.body_layout.addWidget(self.sidebar)

        # Área de Conteúdo
        self.stacked_widget = QStackedWidget(self)
        self.body_layout.addWidget(self.stacked_widget, 1)

        self.main_layout.addLayout(self.body_layout)

        # Barra de Status
        self.status_bar = QStatusBar(self)
        self.status_bar.showMessage("Pronto")
        self.setStatusBar(self.status_bar)

    def _connect_signals(self) -> None:
        """Conecta os sinais e slots."""
        self.title_bar.close_clicked.connect(self.close)
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self.toggle_maximize)
        self.sidebar.page_changed.connect(self.switch_page)

    def toggle_maximize(self) -> None:
        """Alterna entre maximizar e restaurar a janela."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def add_page(self, name: str, icon: str, widget: QWidget) -> None:
        """
        Adiciona uma nova página ao StackedWidget.
        
        Args:
            name (str): Nome da página.
            icon (str): Ícone da página (emoji/texto).
            widget (QWidget): O widget da página a ser adicionado.
        """
        self.stacked_widget.addWidget(widget)
        # TODO: Adicionar o botão na barra lateral, ou a barra lateral já pode ter métodos para isso.
        
    def switch_page(self, index: int) -> None:
        """
        Altera a página atual visível.
        
        Args:
            index (int): O índice da página.
        """
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)

    def toggle_sidebar(self) -> None:
        """Alterna a visibilidade da barra lateral (expandida/colapsada)."""
        # Delegado para o Sidebar, assumindo que ele lida com sua própria animação
        pass

    def nativeEvent(self, event_type: bytes, message) -> tuple[bool, int]:
        """
        Manipula eventos nativos para permitir redimensionamento nas bordas
        em janelas sem borda no Windows.
        """
        if sys.platform != "win32":
            return super().nativeEvent(event_type, message)
            
        try:
            import ctypes
            from ctypes.wintypes import MSG
            
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084: # WM_NCHITTEST
                x = msg.pt.x - self.x()
                y = msg.pt.y - self.y()
                
                # Constantes do HitTest do Windows
                HTLEFT = 10
                HTRIGHT = 11
                HTTOP = 12
                HTTOPLEFT = 13
                HTTOPRIGHT = 14
                HTBOTTOM = 15
                HTBOTTOMLEFT = 16
                HTBOTTOMRIGHT = 17
                HTCLIENT = 1
                
                border_width = 8
                
                if self.isMaximized():
                    return False, 0
                    
                on_left = x < border_width
                on_right = x > self.width() - border_width
                on_top = y < border_width
                on_bottom = y > self.height() - border_width
                
                if on_top and on_left:
                    return True, HTTOPLEFT
                elif on_top and on_right:
                    return True, HTTOPRIGHT
                elif on_bottom and on_left:
                    return True, HTBOTTOMLEFT
                elif on_bottom and on_right:
                    return True, HTBOTTOMRIGHT
                elif on_left:
                    return True, HTLEFT
                elif on_right:
                    return True, HTRIGHT
                elif on_top:
                    return True, HTTOP
                elif on_bottom:
                    return True, HTBOTTOM
        except Exception:
            pass
                    
        return super().nativeEvent(event_type, message)
