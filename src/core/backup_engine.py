"""
Motor de Backup e Restauração via ADB.
"""
import os
import subprocess
from datetime import datetime
from PySide6.QtCore import QObject, Signal

class BackupEngine(QObject):
    """
    Classe responsável pela execução de operações de backup e restauração.
    """
    backup_progress = Signal(str)
    operation_completed = Signal(bool, str)

    def __init__(self, parent: QObject | None = None) -> None:
        """Inicializa o motor de backup."""
        super().__init__(parent)

    def backup_full(self, serial: str, output_path: str) -> tuple[bool, str]:
        """
        Executa o backup completo do sistema e dados de aplicativos.
        
        Args:
            serial: O número de série do dispositivo.
            output_path: O caminho onde o arquivo de backup será salvo.
            
        Returns:
            Uma tupla contendo o status de sucesso (bool) e uma mensagem (str).
        """
        try:
            cmd = ["adb", "-s", serial, "backup", "-apk", "-shared", "-all", "-f", output_path]
            self.backup_progress.emit(f"Iniciando backup completo: {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return True, "Backup completo finalizado com sucesso."
            return False, f"Falha no backup: {result.stderr}"
        except Exception as e:
            return False, f"Erro ao executar backup: {e}"

    def backup_apks_only(self, serial: str, output_path: str) -> tuple[bool, str]:
        """
        Executa o backup apenas dos APKs instalados pelo usuário.
        
        Args:
            serial: O número de série do dispositivo.
            output_path: O diretório onde os APKs serão salvos.
            
        Returns:
            Uma tupla contendo o status de sucesso e uma mensagem.
        """
        try:
            self.backup_progress.emit("Buscando pacotes no dispositivo...")
            cmd = ["adb", "-s", serial, "shell", "pm", "list", "packages", "-3"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return False, f"Falha ao listar pacotes: {result.stderr}"
                
            packages = [line.strip().replace("package:", "") for line in result.stdout.splitlines() if line.strip()]
            
            if not packages:
                return True, "Nenhum pacote de terceiro encontrado."
                
            os.makedirs(output_path, exist_ok=True)
            
            success_count = 0
            for pkg in packages:
                self.backup_progress.emit(f"Obtendo caminho do pacote {pkg}...")
                path_cmd = ["adb", "-s", serial, "shell", "pm", "path", pkg]
                path_res = subprocess.run(path_cmd, capture_output=True, text=True, check=False)
                if path_res.returncode == 0 and path_res.stdout:
                    apk_path = path_res.stdout.strip().replace("package:", "")
                    self.backup_progress.emit(f"Baixando APK: {pkg}...")
                    pull_cmd = ["adb", "-s", serial, "pull", apk_path, os.path.join(output_path, f"{pkg}.apk")]
                    pull_res = subprocess.run(pull_cmd, capture_output=True, text=True, check=False)
                    if pull_res.returncode == 0:
                        success_count += 1
                        
            return True, f"Backup de APKs concluído. {success_count}/{len(packages)} pacotes salvos."
        except Exception as e:
            return False, f"Erro ao realizar backup de APKs: {e}"

    def pull_media(self, serial: str, remote_folder: str, local_folder: str) -> tuple[bool, str]:
        """
        Copia mídias de uma pasta remota para uma pasta local.
        
        Args:
            serial: O número de série do dispositivo.
            remote_folder: A pasta de origem no dispositivo.
            local_folder: O diretório de destino no computador.
            
        Returns:
            Uma tupla contendo o status de sucesso e uma mensagem.
        """
        try:
            os.makedirs(local_folder, exist_ok=True)
            self.backup_progress.emit(f"Copiando mídias de {remote_folder} para {local_folder}...")
            cmd = ["adb", "-s", serial, "pull", remote_folder, local_folder]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return True, f"Mídias copiadas de {remote_folder} com sucesso."
            return False, f"Falha ao copiar mídias: {result.stderr}"
        except Exception as e:
            return False, f"Erro ao copiar mídias: {e}"

    def restore_backup(self, serial: str, backup_file_path: str) -> tuple[bool, str]:
        """
        Restaura um backup .ab para o dispositivo.
        
        Args:
            serial: O número de série do dispositivo.
            backup_file_path: O caminho para o arquivo de backup.
            
        Returns:
            Uma tupla contendo o status de sucesso e uma mensagem.
        """
        try:
            self.backup_progress.emit(f"Iniciando restauração a partir de: {backup_file_path}")
            cmd = ["adb", "-s", serial, "restore", backup_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return True, "Restauração finalizada com sucesso."
            return False, f"Falha na restauração: {result.stderr}"
        except Exception as e:
            return False, f"Erro ao executar restauração: {e}"

    def list_existing_backups(self, backup_dir: str) -> list[dict]:
        """
        Lista os arquivos de backup (.ab) existentes.
        
        Args:
            backup_dir: O diretório onde os backups são armazenados.
            
        Returns:
            Uma lista de dicionários contendo informações dos backups.
        """
        backups = []
        try:
            if not os.path.exists(backup_dir):
                return backups
                
            for item in os.listdir(backup_dir):
                full_path = os.path.join(backup_dir, item)
                if os.path.isfile(full_path) and item.endswith(".ab"):
                    size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    mod_time = os.path.getmtime(full_path)
                    mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                    
                    backups.append({
                        "filename": item,
                        "size_mb": round(size_mb, 2),
                        "modified_date": mod_date,
                        "full_path": full_path
                    })
            
            backups.sort(key=lambda x: x["modified_date"], reverse=True)
        except Exception as e:
            print(f"Erro ao listar backups: {e}")
            
        return backups
