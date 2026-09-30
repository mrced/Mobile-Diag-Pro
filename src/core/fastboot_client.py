import subprocess
import re
from typing import List, Tuple, Dict, Optional
from PySide6.QtCore import QObject, Signal

class FastbootClient(QObject):
    """
    Cliente para interação com o utilitário fastboot.
    Fornece métodos para listar dispositivos, obter variáveis, flashear partições,
    e gerenciar o estado do bootloader e slots.
    """
    output_received = Signal(str)
    flash_progress = Signal(int, str)

    def __init__(self, fastboot_path: str = "fastboot") -> None:
        """
        Inicializa o cliente fastboot.
        
        Args:
            fastboot_path: Caminho para o executável do fastboot.
        """
        super().__init__()
        self._fastboot_path = fastboot_path

    def _run_cmd(self, args: List[str]) -> Tuple[bool, str, str]:
        """
        Executa um comando fastboot de forma síncrona.
        
        Args:
            args: Lista de argumentos do comando.
            
        Returns:
            Tupla contendo (sucesso, stdout, stderr).
        """
        try:
            cmd = [self._fastboot_path] + args
            result = subprocess.run(
                cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout, result.stderr
        except FileNotFoundError:
            return False, "", "Executável fastboot não encontrado."
        except Exception as e:
            return False, "", str(e)

    def get_devices(self) -> List[Tuple[str, str]]:
        """
        Lista os dispositivos conectados em modo fastboot ou fastbootd.
        
        Returns:
            Lista de tuplas (serial, estado).
        """
        success, stdout, _ = self._run_cmd(["devices"])
        devices = []
        if success:
            for line in stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        devices.append((parts[0], parts[1]))
        return devices

    def get_var(self, serial: str, var: str) -> str:
        """
        Obtém o valor de uma variável específica do fastboot.
        
        Args:
            serial: Número de série do dispositivo.
            var: Nome da variável (ex: product, unlocked).
            
        Returns:
            Valor da variável ou string vazia em caso de falha.
        """
        success, stdout, stderr = self._run_cmd(["-s", serial, "getvar", var])
        
        # O fastboot geralmente retorna getvar no stderr no formato "var: valor"
        output = stderr + "\n" + stdout
        for line in output.split("\n"):
            if line.startswith(f"{var}:"):
                return line.split(":", 1)[1].strip()
        return ""

    def get_all_vars(self, serial: str) -> Dict[str, str]:
        """
        Obtém as variáveis comuns do dispositivo.
        
        Args:
            serial: Número de série do dispositivo.
            
        Returns:
            Dicionário com as variáveis (product, unlocked, current-slot, etc).
        """
        vars_to_fetch = [
            "product", "unlocked", "current-slot",
            "max-download-size", "is-userspace", "secure"
        ]
        result = {}
        for var in vars_to_fetch:
            result[var] = self.get_var(serial, var)
        return result

    def flash(self, serial: str, partition: str, image_path: str, progress_callback=None) -> Tuple[bool, str]:
        """
        Flashea uma partição específica com a imagem fornecida.
        
        Args:
            serial: Número de série do dispositivo.
            partition: Nome da partição (ex: boot, system).
            image_path: Caminho para o arquivo de imagem.
            progress_callback: Função opcional de callback para progresso.
            
        Returns:
            Tupla contendo (sucesso, mensagem).
        """
        # Implementação simplificada para emitir progresso
        try:
            cmd = [self._fastboot_path, "-s", serial, "flash", partition, image_path]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            output_log = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line = line.strip()
                    output_log.append(line)
                    self.output_received.emit(line)
                    
                    if progress_callback:
                        progress_callback(line)
                        
            returncode = process.wait()
            output_str = "\n".join(output_log)
            
            if returncode == 0 and "OKAY" in output_str:
                return True, "Flash concluído com sucesso."
            else:
                return False, f"Falha ao flashear:\n{output_str}"
        except Exception as e:
            return False, f"Erro ao executar flash: {str(e)}"

    def erase(self, serial: str, partition: str) -> Tuple[bool, str]:
        """
        Apaga o conteúdo de uma partição.
        
        Args:
            serial: Número de série do dispositivo.
            partition: Nome da partição.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        success, stdout, stderr = self._run_cmd(["-s", serial, "erase", partition])
        output = stderr + stdout
        if success and "OKAY" in output:
            return True, "Partição apagada com sucesso."
        return False, f"Falha ao apagar partição: {output}"

    def reboot(self, serial: str, target: str = "") -> bool:
        """
        Reinicia o dispositivo.
        
        Args:
            serial: Número de série do dispositivo.
            target: Destino (vazio para sistema, 'bootloader', 'recovery', 'fastboot').
            
        Returns:
            Booleano indicando sucesso.
        """
        args = ["-s", serial, "reboot"]
        if target:
            args.append(target)
        success, _, _ = self._run_cmd(args)
        return success

    def unlock_bootloader(self, serial: str) -> Tuple[bool, str]:
        """
        Desbloqueia o bootloader do dispositivo.
        
        Args:
            serial: Número de série do dispositivo.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        success, stdout, stderr = self._run_cmd(["-s", serial, "flashing", "unlock"])
        if not success or "FAILED" in stderr:
            # Fallback
            success, stdout, stderr = self._run_cmd(["-s", serial, "oem", "unlock"])
            
        output = stderr + stdout
        if success and "OKAY" in output:
            return True, "Comando de desbloqueio enviado."
        return False, f"Falha ao desbloquear: {output}"

    def lock_bootloader(self, serial: str) -> Tuple[bool, str]:
        """
        Bloqueia o bootloader do dispositivo.
        
        Args:
            serial: Número de série do dispositivo.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        success, stdout, stderr = self._run_cmd(["-s", serial, "flashing", "lock"])
        output = stderr + stdout
        if success and "OKAY" in output:
            return True, "Comando de bloqueio enviado."
        return False, f"Falha ao bloquear: {output}"

    def set_active_slot(self, serial: str, slot: str) -> bool:
        """
        Define o slot ativo (A ou B).
        
        Args:
            serial: Número de série do dispositivo.
            slot: Slot desejado ('a' ou 'b').
            
        Returns:
            Booleano indicando sucesso.
        """
        success, stdout, stderr = self._run_cmd(["-s", serial, f"--set-active={slot}"])
        return success and "OKAY" in (stderr + stdout)

    def continue_boot(self, serial: str) -> bool:
        """
        Continua o boot normal a partir do bootloader.
        
        Args:
            serial: Número de série do dispositivo.
            
        Returns:
            Booleano indicando sucesso.
        """
        success, _, _ = self._run_cmd(["-s", serial, "continue"])
        return success

    def is_fastbootd(self, serial: str) -> bool:
        """
        Verifica se o dispositivo está no fastbootd (userspace).
        
        Args:
            serial: Número de série do dispositivo.
            
        Returns:
            True se estiver em fastbootd, False caso contrário.
        """
        is_userspace = self.get_var(serial, "is-userspace")
        return is_userspace.lower() == "yes"
