import socket
import struct
import subprocess
import threading
from PySide6.QtCore import QObject, Signal

from src.core.constants import DEFAULT_TIMEOUT
from src.core.exceptions import ADBConnectionError, ADBTimeoutError, ADBCommandError
from src.core.logger import get_logger

logger = get_logger(__name__)

class ADBClient(QObject):
    """Cliente para comunicação com o servidor ADB."""
    
    connection_established = Signal()
    connection_lost = Signal()
    command_output = Signal(str)

    def __init__(self, host: str = '127.0.0.1', port: int = 5037):
        """Inicializa o cliente ADB."""
        super().__init__()
        self.host = host
        self.port = port
        self.lock = threading.Lock()

    def _encode_message(self, data: str) -> bytes:
        """Codifica a mensagem para o formato do protocolo ADB."""
        length = f"{len(data):04x}".encode('utf-8')
        return length + data.encode('utf-8')

    def _send_command(self, command: str, timeout: float = DEFAULT_TIMEOUT) -> str:
        """Envia um comando para o servidor ADB."""
        with self.lock:
            try:
                with socket.create_connection((self.host, self.port), timeout=timeout) as sock:
                    sock.sendall(self._encode_message(command))
                    
                    status = sock.recv(4).decode('utf-8')
                    if status != 'OKAY':
                        error_len_str = sock.recv(4).decode('utf-8')
                        error_len = int(error_len_str, 16) if error_len_str else 0
                        error_msg = sock.recv(error_len).decode('utf-8') if error_len else "Unknown error"
                        raise ADBCommandError(f"ADB Error: {error_msg}")
                    
                    response_len_str = sock.recv(4).decode('utf-8')
                    if not response_len_str:
                        return ""
                    try:
                        response_len = int(response_len_str, 16)
                    except ValueError:
                        # Para comandos que não enviam tamanho
                        return response_len_str + sock.recv(4096).decode('utf-8', errors='replace')
                    
                    response = sock.recv(response_len).decode('utf-8', errors='replace')
                    return response
            except socket.timeout:
                raise ADBTimeoutError("ADB connection timed out")
            except ConnectionRefusedError:
                raise ADBConnectionError("Could not connect to ADB server")

    def start_server(self) -> bool:
        """Inicia o servidor ADB."""
        try:
            subprocess.run(['adb', 'start-server'], check=True, capture_output=True)
            self.connection_established.emit()
            return True
        except subprocess.SubprocessError:
            return False

    def kill_server(self) -> bool:
        """Para o servidor ADB."""
        try:
            subprocess.run(['adb', 'kill-server'], check=True, capture_output=True)
            self.connection_lost.emit()
            return True
        except subprocess.SubprocessError:
            return False

    def get_devices(self) -> list[tuple[str, str]]:
        """Retorna uma lista de dispositivos conectados."""
        try:
            response = self._send_command('host:devices')
            devices = []
            for line in response.splitlines():
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) == 2:
                        devices.append((parts[0], parts[1]))
            return devices
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []

    def shell(self, serial: str, command: str, timeout: float = DEFAULT_TIMEOUT) -> str:
        """Executa um comando shell no dispositivo."""
        try:
            # Em modo shell, temos que enviar o transporte e depois o shell.
            with self.lock:
                with socket.create_connection((self.host, self.port), timeout=timeout) as sock:
                    sock.sendall(self._encode_message(f"host:transport:{serial}"))
                    if sock.recv(4).decode('utf-8') != 'OKAY':
                        raise ADBCommandError("Failed to set transport")
                    
                    sock.sendall(self._encode_message(f"shell:{command}"))
                    if sock.recv(4).decode('utf-8') != 'OKAY':
                        raise ADBCommandError("Failed to execute shell command")
                    
                    output = b""
                    while True:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        output += chunk
                    
                    result = output.decode('utf-8', errors='replace')
                    self.command_output.emit(result)
                    return result
        except Exception as e:
            logger.error(f"Shell command error: {e}")
            raise ADBCommandError(f"Shell failed: {str(e)}")

    def get_prop(self, serial: str, prop: str) -> str:
        """Retorna uma propriedade do dispositivo."""
        return self.shell(serial, f"getprop {prop}").strip()

    def get_all_props(self, serial: str) -> dict[str, str]:
        """Retorna todas as propriedades do dispositivo."""
        output = self.shell(serial, "getprop")
        from src.utils.parsers import parse_getprop_output
        return parse_getprop_output(output)

    def dumpsys(self, serial: str, service: str, args: str = '') -> str:
        """Executa o comando dumpsys."""
        cmd = f"dumpsys {service} {args}".strip()
        return self.shell(serial, cmd)

    def pull_file(self, serial: str, remote_path: str, local_path: str) -> bool:
        """Puxa um arquivo do dispositivo."""
        try:
            subprocess.run(['adb', '-s', serial, 'pull', remote_path, local_path], check=True, capture_output=True)
            return True
        except subprocess.SubprocessError:
            return False

    def push_file(self, serial: str, local_path: str, remote_path: str) -> bool:
        """Envia um arquivo para o dispositivo."""
        try:
            subprocess.run(['adb', '-s', serial, 'push', local_path, remote_path], check=True, capture_output=True)
            return True
        except subprocess.SubprocessError:
            return False

    def reboot(self, serial: str, mode: str = '') -> bool:
        """Reinicia o dispositivo."""
        try:
            cmd = ['adb', '-s', serial, 'reboot']
            if mode:
                cmd.append(mode)
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.SubprocessError:
            return False

    def is_server_running(self) -> bool:
        """Verifica se o servidor ADB está rodando."""
        try:
            with socket.create_connection((self.host, self.port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False
