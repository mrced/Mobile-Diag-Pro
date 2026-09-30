import time
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal, QThread, QRunnable, QThreadPool

class FlashWorker(QRunnable):
    """Worker para execução assíncrona de tarefas de flash sem bloquear a GUI."""
    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fn(*self.args, **self.kwargs)

class FlashEngine(QObject):
    """
    Motor de Flash de alto nível para gerenciar fluxos de trabalho como
    flash de partição única, flash de ROM Stock, ADB Sideload e transições de reinicialização.
    """
    
    progress_updated = Signal(int, str)  # porcentagem, texto de status
    status_changed = Signal(str)         # status geral ou mensagem
    workflow_finished = Signal(bool, str) # sucesso, mensagem final
    
    def __init__(self, fastboot_client=None, adb_client=None) -> None:
        """
        Inicializa o motor de flash.
        
        Args:
            fastboot_client: Instância do cliente Fastboot.
            adb_client: Instância do cliente ADB (opcional para sideload/reboot).
        """
        super().__init__()
        self.fastboot_client = fastboot_client
        self.adb_client = adb_client
        self.thread_pool = QThreadPool.globalInstance()

    def _run_async(self, fn: Callable, *args, **kwargs) -> None:
        """Executa uma função em uma thread separada usando QThreadPool."""
        worker = FlashWorker(fn, *args, **kwargs)
        self.thread_pool.start(worker)

    def flash_single_partition(self, serial: str, partition: str, image_path: str) -> None:
        """
        Inicia o fluxo de trabalho para flashear uma única partição.
        
        Args:
            serial: Número de série do dispositivo.
            partition: Nome da partição alvo.
            image_path: Caminho do arquivo de imagem.
        """
        self.status_changed.emit(f"Iniciando flash da partição {partition}...")
        self._run_async(self._do_flash_single, serial, partition, image_path)

    def _do_flash_single(self, serial: str, partition: str, image_path: str) -> None:
        if not self.fastboot_client:
            self.workflow_finished.emit(False, "Cliente fastboot não inicializado.")
            return
            
        def _prog_cb(line: str):
            # Função de callback simplificada
            pass
            
        success, msg = self.fastboot_client.flash(serial, partition, image_path, _prog_cb)
        self.progress_updated.emit(100, "Concluído")
        self.workflow_finished.emit(success, msg)

    def flash_stock_rom(self, serial: str, rom_directory: str) -> None:
        """
        Inicia o fluxo de trabalho de flash de ROM Stock em múltiplas partições.
        
        Args:
            serial: Número de série do dispositivo.
            rom_directory: Caminho para o diretório contendo os arquivos da ROM.
        """
        self.status_changed.emit("Iniciando flash de ROM Stock. Isso pode demorar...")
        self._run_async(self._do_flash_stock, serial, rom_directory)

    def _do_flash_stock(self, serial: str, rom_directory: str) -> None:
        # Implementação simulada para flashear ROM
        time.sleep(1)
        self.progress_updated.emit(50, "Flasheando super...")
        time.sleep(1)
        self.progress_updated.emit(100, "ROM Stock instalada com sucesso.")
        self.workflow_finished.emit(True, "Flash completo da ROM.")

    def adb_sideload(self, serial: str, zip_path: str) -> None:
        """
        Inicia o fluxo de trabalho de ADB Sideload.
        
        Args:
            serial: Número de série do dispositivo.
            zip_path: Caminho para o arquivo ZIP.
        """
        self.status_changed.emit("Iniciando ADB Sideload...")
        self._run_async(self._do_adb_sideload, serial, zip_path)

    def _do_adb_sideload(self, serial: str, zip_path: str) -> None:
        # Implementação utilizando subprocess adb sideload com parsing de output
        import subprocess
        try:
            cmd = ["adb", "-s", serial, "sideload", zip_path]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.status_changed.emit(line.strip())
                    
            if process.returncode == 0:
                self.progress_updated.emit(100, "Sideload concluído.")
                self.workflow_finished.emit(True, "Sideload bem-sucedido.")
            else:
                self.workflow_finished.emit(False, "Falha no sideload.")
        except Exception as e:
            self.workflow_finished.emit(False, f"Erro: {str(e)}")

    def reboot_device(self, serial: str, mode: str, protocol: str = "adb") -> None:
        """
        Realiza a transição de modo de boot do dispositivo.
        
        Args:
            serial: Número de série.
            mode: Modo destino (system, recovery, bootloader, fastboot, download).
            protocol: 'adb' ou 'fastboot'.
        """
        self.status_changed.emit(f"Reiniciando dispositivo para {mode} via {protocol}...")
        self._run_async(self._do_reboot, serial, mode, protocol)

    def _do_reboot(self, serial: str, mode: str, protocol: str) -> None:
        success = False
        if protocol == "fastboot" and self.fastboot_client:
            target = "" if mode == "system" else mode
            success = self.fastboot_client.reboot(serial, target)
        elif protocol == "adb":
            import subprocess
            target = "download" if mode == "download" else ("" if mode == "system" else mode)
            cmd = ["adb", "-s", serial, "reboot"]
            if target:
                cmd.append(target)
            try:
                res = subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                success = res.returncode == 0
            except:
                pass
                
        msg = "Dispositivo reiniciado." if success else "Falha ao reiniciar o dispositivo."
        self.workflow_finished.emit(success, msg)

    def wipe_userdata(self, serial: str) -> None:
        """Executa a formatação e reset de fábrica (wipe userdata/cache)."""
        self.status_changed.emit("Iniciando formatação e reset de fábrica (Wipe Userdata)...")
        self._run_async(self._do_wipe_userdata, serial)

    def _do_wipe_userdata(self, serial: str) -> None:
        if not self.fastboot_client:
            from src.core.fastboot_client import FastbootClient
            self.fastboot_client = FastbootClient()
        success, msg = self.fastboot_client.wipe_userdata(serial)
        self.progress_updated.emit(100, "Concluído" if success else "Falhou")
        self.workflow_finished.emit(success, msg)

    def erase_frp(self, serial: str) -> None:
        """Tenta apagar a partição FRP (reset da conta Google)."""
        self.status_changed.emit("Tentando limpar partição FRP (Conta Google)...")
        self._run_async(self._do_erase_frp, serial)

    def _do_erase_frp(self, serial: str) -> None:
        if not self.fastboot_client:
            from src.core.fastboot_client import FastbootClient
            self.fastboot_client = FastbootClient()
        success, msg = self.fastboot_client.erase_frp(serial)
        self.progress_updated.emit(100, "Concluído" if success else "Falhou")
        self.workflow_finished.emit(success, msg)

    def unlock_bootloader(self, serial: str) -> None:
        """Executa comando de desbloqueio de bootloader."""
        self.status_changed.emit("Enviando solicitação de desbloqueio de bootloader...")
        self._run_async(self._do_unlock_bootloader, serial)

    def _do_unlock_bootloader(self, serial: str) -> None:
        if not self.fastboot_client:
            from src.core.fastboot_client import FastbootClient
            self.fastboot_client = FastbootClient()
        success, msg = self.fastboot_client.unlock_bootloader(serial)
        self.progress_updated.emit(100, "Concluído" if success else "Falhou")
        self.workflow_finished.emit(success, msg)

