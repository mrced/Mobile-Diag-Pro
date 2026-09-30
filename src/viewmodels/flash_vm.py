import os
from typing import List, Optional
from PySide6.QtCore import QObject, Signal, Slot, QTimer

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
        """Inicializa o ViewModel de Flash."""
        super().__init__(parent)
        # Injetar dependências de serviços ADB/Fastboot
    
    @Slot(str)
    def load_firmware(self, file_path: str) -> None:
        """
        Inspeciona um arquivo de firmware ou diretório.
        
        Args:
            file_path: Caminho para o arquivo .img, .zip ou pasta de firmware.
        """
        self.flash_log.emit(f"Analisando firmware: {file_path}")
        if not os.path.exists(file_path):
            self.flash_log.emit("Erro: Arquivo ou diretório não encontrado.")
            return
            
        # Simulação de análise
        self.flash_log.emit("Firmware analisado com sucesso.")
        self.partition_list_updated.emit(["boot", "recovery", "system", "vendor"])
        self.prerequisites_checked.emit(True, [])
        
    @Slot(str, str, str)
    def start_flash(self, serial: str, partition: str, image_path: str) -> None:
        """
        Inicia a gravação de uma imagem em uma partição de forma assíncrona.
        
        Args:
            serial: O serial do dispositivo alvo.
            partition: A partição destino (ex: boot, recovery).
            image_path: O caminho para o arquivo de imagem.
        """
        if not os.path.exists(image_path):
            self.flash_completed.emit(False, "Arquivo de imagem não encontrado.")
            return
            
        self.flash_started.emit(partition)
        self.flash_log.emit(f"Iniciando gravação na partição '{partition}' usando '{image_path}'...")
        
        # Simulação de progresso (em produção, usar QThread/Worker)
        self.flash_progress.emit(10, "Verificando dispositivo...")
        QTimer.singleShot(1000, lambda: self._simulate_flash_step(50, "Gravando dados...", partition))

    def _simulate_flash_step(self, progress: int, msg: str, partition: str) -> None:
        """Simula passos do processo de flash."""
        self.flash_progress.emit(progress, msg)
        self.flash_log.emit(msg)
        if progress < 100:
            QTimer.singleShot(1500, lambda: self._simulate_flash_step(100, "Gravação concluída.", partition))
        else:
            self.flash_completed.emit(True, f"Partição {partition} gravada com sucesso.")

    @Slot(str, str)
    def start_sideload(self, serial: str, zip_path: str) -> None:
        """
        Inicia o processo de ADB sideload de forma assíncrona.
        
        Args:
            serial: O serial do dispositivo alvo.
            zip_path: Caminho para o arquivo .zip da atualização.
        """
        self.flash_log.emit(f"Iniciando ADB Sideload com arquivo '{zip_path}'...")
        self.flash_progress.emit(0, "Preparando sideload...")
        
        if not os.path.exists(zip_path):
            self.flash_completed.emit(False, "Arquivo ZIP não encontrado.")
            return
            
        # Simulação
        QTimer.singleShot(2000, lambda: self.flash_completed.emit(True, "Sideload concluído."))

    @Slot(str, str)
    def reboot_device(self, serial: str, mode: str) -> None:
        """
        Reinicia o dispositivo para o modo especificado.
        
        Args:
            serial: O serial do dispositivo.
            mode: Modo de destino (normal, bootloader, recovery, fastbootd).
        """
        self.flash_log.emit(f"Reiniciando dispositivo {serial} para o modo: {mode}...")
        # Simulação
        QTimer.singleShot(1000, lambda: self.flash_log.emit(f"Comando de reinicialização ({mode}) enviado."))

    @Slot(str)
    def unlock_bootloader(self, serial: str) -> None:
        """
        Aciona o comando de desbloqueio do bootloader.
        
        Args:
            serial: O serial do dispositivo.
        """
        self.flash_log.emit("Aviso: Tentando desbloquear o bootloader. ISSO APAGARÁ TODOS OS DADOS.")
        # Simulação
        QTimer.singleShot(1500, lambda: self.flash_log.emit("Comando 'fastboot flashing unlock' enviado. Verifique a tela do dispositivo."))
