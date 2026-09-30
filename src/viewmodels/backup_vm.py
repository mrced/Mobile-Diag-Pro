"""
ViewModel para Backup e Restauração.
"""
import os
import threading
from typing import List
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from src.core.backup_engine import BackupEngine

class BackupViewModel(QObject):
    """
    ViewModel responsável pela lógica de backup e restauração.
    """
    backup_started = Signal(str)
    backup_progress = Signal(str)
    backup_completed = Signal(bool, str)
    
    restore_started = Signal(str)
    restore_completed = Signal(bool, str)
    
    backup_list_updated = Signal(list)

    def __init__(self, parent: QObject | None = None) -> None:
        """Inicializa o ViewModel de Backup."""
        super().__init__(parent)
        self.engine = BackupEngine(self)
        self.engine.backup_progress.connect(self.backup_progress)
        self._serial: str = ""

    def set_device(self, serial: str) -> None:
        """
        Define o dispositivo atual ativo.
        
        Args:
            serial: O número de série do dispositivo.
        """
        self._serial = serial

    def start_full_backup(self, dest_folder: str) -> None:
        """
        Inicia o backup completo de forma assíncrona.
        
        Args:
            dest_folder: A pasta de destino ou arquivo de backup.
        """
        if not self._serial:
            self.backup_completed.emit(False, "Nenhum dispositivo selecionado.")
            return
            
        self.backup_started.emit("Iniciando backup completo. Verifique a tela do dispositivo.")
        
        def _task() -> None:
            if os.path.isdir(dest_folder):
                file_name = f"backup_{self._serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ab"
                output_path = os.path.join(dest_folder, file_name)
            else:
                output_path = dest_folder
                
            success, msg = self.engine.backup_full(self._serial, output_path)
            self.backup_completed.emit(success, msg)
            
        threading.Thread(target=_task, daemon=True).start()

    def start_media_backup(self, dest_folder: str, folders: List[str]) -> None:
        """
        Inicia o backup de mídias de forma assíncrona.
        
        Args:
            dest_folder: A pasta de destino no computador.
            folders: Lista de pastas remotas para copiar.
        """
        if not self._serial:
            self.backup_completed.emit(False, "Nenhum dispositivo selecionado.")
            return
            
        self.backup_started.emit("Iniciando backup de mídias...")
        
        def _task() -> None:
            all_success = True
            messages = []
            
            for remote_folder in folders:
                folder_name = os.path.basename(remote_folder.rstrip('/'))
                local_subfolder = os.path.join(dest_folder, folder_name)
                success, msg = self.engine.pull_media(self._serial, remote_folder, local_subfolder)
                messages.append(msg)
                if not success:
                    all_success = False
            
            final_msg = "\n".join(messages)
            if all_success:
                self.backup_completed.emit(True, "Backup de mídias concluído com sucesso.")
            else:
                self.backup_completed.emit(False, f"Problemas durante o backup:\n{final_msg}")
                
        threading.Thread(target=_task, daemon=True).start()

    def start_restore(self, backup_file: str) -> None:
        """
        Inicia a restauração de um backup de forma assíncrona.
        
        Args:
            backup_file: O caminho para o arquivo .ab.
        """
        if not self._serial:
            self.restore_completed.emit(False, "Nenhum dispositivo selecionado.")
            return
            
        self.restore_started.emit("Iniciando restauração. Verifique a tela do dispositivo.")
        
        def _task() -> None:
            success, msg = self.engine.restore_backup(self._serial, backup_file)
            self.restore_completed.emit(success, msg)
            
        threading.Thread(target=_task, daemon=True).start()

    def refresh_backup_list(self, backup_dir: str) -> None:
        """
        Atualiza a lista de backups disponíveis.
        
        Args:
            backup_dir: O diretório onde os backups estão salvos.
        """
        def _task() -> None:
            backups = self.engine.list_existing_backups(backup_dir)
            self.backup_list_updated.emit(backups)
            
        threading.Thread(target=_task, daemon=True).start()
