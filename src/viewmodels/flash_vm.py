"""
ViewModel para a página de Flash / Recovery / Desbloqueio.
Gerencia a lógica de gravação de imagens, sideload, comandos de desbloqueio e controle de modo do dispositivo.
"""
import os
from typing import List, Optional
from PySide6.QtCore import QObject, Signal, Slot

from src.core.flash_engine import FlashEngine
from src.core.fastboot_client import FastbootClient
from src.core.adb_client import ADBClient
from src.core.logger import get_logger

logger = get_logger(__name__)


class FlashViewModel(QObject):
    """
    ViewModel para a página de Flash / Recovery.
    Gerencia a lógica de gravação de imagens, sideload e controle de modo do dispositivo.
    """
    # Sinais
    device_mode_detected = Signal(str)
    flash_started = Signal(str)
    flash_progress = Signal(int, str)
    flash_log = Signal(str)
    flash_completed = Signal(bool, str)
    partition_list_updated = Signal(list)
    prerequisites_checked = Signal(bool, list)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Inicializa o ViewModel de Flash com o motor real."""
        super().__init__(parent)
        self._fastboot = FastbootClient()
        self._adb = ADBClient()
        self._engine = FlashEngine(fastboot_client=self._fastboot, adb_client=self._adb)

        # Conectar sinais do engine
        self._engine.progress_updated.connect(self._on_engine_progress)
        self._engine.status_changed.connect(self._on_engine_status)
        self._engine.workflow_finished.connect(self._on_engine_finished)

    def _on_engine_progress(self, percent: int, msg: str):
        self.flash_progress.emit(percent, msg)

    def _on_engine_status(self, msg: str):
        self.flash_log.emit(msg)

    def _on_engine_finished(self, success: bool, msg: str):
        self.flash_completed.emit(success, msg)
        self.flash_log.emit(f"[{'SUCESSO' if success else 'FALHA'}] {msg}")

    @Slot(str)
    def load_firmware(self, file_path: str) -> None:
        """Inspeciona um arquivo de firmware ou diretório."""
        self.flash_log.emit(f"Analisando firmware: {file_path}")
        if not os.path.exists(file_path):
            self.flash_log.emit("Erro: Arquivo ou diretório não encontrado.")
            return

        # Análise básica de extensão
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".img":
            self.flash_log.emit("Imagem individual identificada.")
            self.partition_list_updated.emit(["boot", "recovery", "super", "system", "vendor", "vbmeta", "cust"])
        elif ext == ".zip":
            self.flash_log.emit("Pacote ZIP identificado (OTA ou Sideload).")
            self.partition_list_updated.emit(["sideload_package"])
        elif os.path.isdir(file_path):
            files = [f for f in os.listdir(file_path) if f.endswith(".img")]
            self.flash_log.emit(f"Diretório de ROM analisado: {len(files)} imagens encontradas.")
            self.partition_list_updated.emit(files)

        self.prerequisites_checked.emit(True, [])

    @Slot(str, str, str)
    def start_flash(self, serial: str, partition: str, image_path: str) -> None:
        """Inicia a gravação de uma imagem em uma partição de forma assíncrona."""
        if not os.path.exists(image_path):
            self.flash_completed.emit(False, "Arquivo de imagem não encontrado.")
            return

        self.flash_started.emit(partition)
        self.flash_log.emit(f"Iniciando gravação na partição '{partition}' usando '{image_path}'...")
        self._engine.flash_single_partition(serial, partition, image_path)

    @Slot(str, str)
    def start_sideload(self, serial: str, zip_path: str) -> None:
        """Inicia o processo de ADB sideload de forma assíncrona."""
        if not os.path.exists(zip_path):
            self.flash_completed.emit(False, "Arquivo ZIP não encontrado.")
            return

        self.flash_log.emit(f"Iniciando ADB Sideload com arquivo '{zip_path}'...")
        self._engine.adb_sideload(serial, zip_path)

    @Slot(str, str)
    def reboot_device(self, serial: str, mode: str) -> None:
        """Reinicia o dispositivo para o modo especificado (normal, bootloader, recovery, fastbootd, download, continue)."""
        self.flash_log.emit(f"Reiniciando dispositivo {serial} para o modo: {mode}...")
        if mode == "continue":
            success = self._fastboot.continue_boot(serial)
            self.flash_log.emit("Comando 'fastboot continue' executado." if success else "Falha ao continuar boot.")
            self.flash_completed.emit(success, "Boot continuado" if success else "Falha no boot")
        else:
            protocol = "fastboot" if mode in ("bootloader", "fastbootd") else "adb"
            self._engine.reboot_device(serial, mode, protocol=protocol)

    @Slot(str)
    def unlock_bootloader(self, serial: str) -> None:
        """Aciona o comando de desbloqueio do bootloader."""
        self.flash_log.emit("Aviso: Tentando desbloquear o bootloader. ISSO APAGARÁ TODOS OS DADOS.")
        self._engine.unlock_bootloader(serial)

    @Slot(str)
    def wipe_userdata(self, serial: str) -> None:
        """Formata o dispositivo / Remove senhas e padrão de tela (Reset de Fábrica)."""
        self.flash_log.emit("Iniciando Wipe Userdata (Reset de Fábrica / Remoção de Bloqueio de Tela)...")
        self._engine.wipe_userdata(serial)

    @Slot(str)
    def erase_frp(self, serial: str) -> None:
        """Tenta apagar a partição FRP (Reset de Conta Google)."""
        self.flash_log.emit("Solicitando remoção de partição FRP...")
        self._engine.erase_frp(serial)
