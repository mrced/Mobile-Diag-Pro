import platform
import ctypes
import ctypes.wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject, Signal


class USBEventFilter(QAbstractNativeEventFilter):
    """
    Filtro de eventos nativos do Windows para detectar conexão e desconexão de dispositivos USB.
    """
    
    # Constantes do Windows API
    WM_DEVICECHANGE = 0x0219
    DBT_DEVICEARRIVAL = 0x8000
    DBT_DEVICEREMOVECOMPLETE = 0x8004

    def __init__(self, callback_plugged, callback_unplugged):
        super().__init__()
        self.callback_plugged = callback_plugged
        self.callback_unplugged = callback_unplugged

    def nativeEventFilter(self, eventType, message):
        """
        Filtra os eventos nativos procurando por WM_DEVICECHANGE.
        Retorna (False, 0) para permitir que outros processos tratem o evento.
        """
        if eventType == b"windows_generic_MSG" or eventType == b"windows_dispatcher_MSG":
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == self.WM_DEVICECHANGE:
                if msg.wParam == self.DBT_DEVICEARRIVAL:
                    self.callback_plugged()
                elif msg.wParam == self.DBT_DEVICEREMOVECOMPLETE:
                    self.callback_unplugged()
        return False, 0


class USBDetector(QObject):
    """
    Detector de chegada e remoção de dispositivos USB.
    Instala um filtro de eventos nativos (principalmente no Windows)
    para avisar quando dispositivos são conectados ou desconectados.
    """
    device_plugged = Signal()
    device_unplugged = Signal()

    def __init__(self) -> None:
        """
        Inicializa o detector e tenta registrar o filtro de eventos nativos na aplicação.
        """
        super().__init__()
        self._filter = None
        self._setup_detector()

    def _setup_detector(self) -> None:
        """
        Configura o hook no sistema operacional, se suportado (Windows).
        Para outros SOs, os sinais não serão emitidos automaticamente por esse mecanismo nativo.
        """
        if platform.system() == "Windows":
            try:
                self._filter = USBEventFilter(
                    self.device_plugged.emit,
                    self.device_unplugged.emit
                )
                app = QCoreApplication.instance()
                if app is not None:
                    app.installNativeEventFilter(self._filter)
            except Exception as e:
                print(f"Aviso: Não foi possível configurar o detector nativo de USB: {e}")
        else:
            print("Aviso: O detector nativo de USB atualmente suporta apenas Windows.")
