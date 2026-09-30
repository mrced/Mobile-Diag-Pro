"""
Gerenciador de dispositivos — detecta, rastreia e gerencia o estado dos dispositivos conectados.

Implementa uma máquina de estados para gerenciar transições entre modos de conexão
(ADB, Fastboot, Recovery, etc.) e emite sinais quando o estado muda.
"""
import subprocess
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from src.core.adb_client import ADBClient
from src.core.adb_commands import ADBCommands
from src.core.constants import DeviceMode, POLLING_INTERVAL
from src.core.logger import get_logger
from src.models.device import DeviceInfo

logger = get_logger(__name__)


class DeviceManager(QObject):
    """
    Gerenciador central de dispositivos.

    Responsável por:
    - Detectar dispositivos conectados via ADB e Fastboot
    - Rastrear o modo atual do dispositivo (normal, recovery, fastboot, etc.)
    - Emitir sinais quando dispositivos são conectados/desconectados
    - Fornecer informações detalhadas do dispositivo ativo
    """

    # Sinais emitidos quando o estado do dispositivo muda
    device_connected = Signal(object)       # DeviceInfo
    device_disconnected = Signal()
    device_mode_changed = Signal(object)    # DeviceMode
    device_list_updated = Signal(list)      # list[tuple[str, str]]
    error_occurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        # Clientes ADB
        self._adb_client = ADBClient()
        self._adb_commands = ADBCommands(self._adb_client)

        # Estado atual
        self._current_device: Optional[DeviceInfo] = None
        self._current_serial: Optional[str] = None
        self._current_mode: DeviceMode = DeviceMode.UNKNOWN
        self._connected: bool = False

        # Timer de polling para detecção de dispositivos
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(POLLING_INTERVAL)
        self._poll_timer.timeout.connect(self._poll_devices)

    @property
    def adb_client(self) -> ADBClient:
        """Retorna o cliente ADB."""
        return self._adb_client

    @property
    def adb_commands(self) -> ADBCommands:
        """Retorna o wrapper de comandos ADB."""
        return self._adb_commands

    @property
    def current_device(self) -> Optional[DeviceInfo]:
        """Retorna as informações do dispositivo atual."""
        return self._current_device

    @property
    def current_serial(self) -> Optional[str]:
        """Retorna o serial do dispositivo atual."""
        return self._current_serial

    @property
    def current_mode(self) -> DeviceMode:
        """Retorna o modo atual do dispositivo."""
        return self._current_mode

    @property
    def is_connected(self) -> bool:
        """Retorna se um dispositivo está conectado."""
        return self._connected

    def start_monitoring(self) -> None:
        """Inicia o monitoramento de dispositivos."""
        logger.info("Iniciando monitoramento de dispositivos")
        self._ensure_adb_server()
        self._poll_timer.start()
        # Polling imediato na primeira vez
        self._poll_devices()

    def stop_monitoring(self) -> None:
        """Para o monitoramento de dispositivos."""
        logger.info("Parando monitoramento de dispositivos")
        self._poll_timer.stop()

    def _ensure_adb_server(self) -> None:
        """Garante que o servidor ADB está rodando."""
        if not self._adb_client.is_server_running():
            logger.info("Servidor ADB não está rodando. Iniciando...")
            if self._adb_client.start_server():
                logger.info("Servidor ADB iniciado com sucesso")
            else:
                logger.error("Falha ao iniciar servidor ADB")
                self.error_occurred.emit("Falha ao iniciar servidor ADB")

    @Slot()
    def _poll_devices(self) -> None:
        """Verifica periodicamente os dispositivos conectados."""
        try:
            # Verificar dispositivos ADB
            adb_devices = self._adb_client.get_devices()

            # Verificar dispositivos Fastboot
            fastboot_devices = self._get_fastboot_devices()

            # Combinar listas
            all_devices = []
            for serial, state in adb_devices:
                mode = self._state_to_mode(state)
                all_devices.append((serial, mode))

            for serial in fastboot_devices:
                all_devices.append((serial, DeviceMode.FASTBOOT))

            # Emitir lista atualizada
            self.device_list_updated.emit(
                [(s, m.value) for s, m in all_devices]
            )

            # Gerenciar conexão
            if all_devices:
                serial, mode = all_devices[0]  # Usar primeiro dispositivo

                if not self._connected or self._current_serial != serial:
                    # Novo dispositivo conectado
                    self._current_serial = serial
                    self._current_mode = mode
                    self._connected = True
                    self._fetch_device_info(serial, mode)

                elif self._current_mode != mode:
                    # Modo mudou
                    self._current_mode = mode
                    self.device_mode_changed.emit(mode)
                    logger.info(f"Modo do dispositivo alterado: {mode.value}")

            elif self._connected:
                # Dispositivo desconectado
                self._connected = False
                self._current_device = None
                self._current_serial = None
                self._current_mode = DeviceMode.UNKNOWN
                self.device_disconnected.emit()
                logger.info("Dispositivo desconectado")

        except Exception as e:
            logger.error(f"Erro ao verificar dispositivos: {e}")

    def _state_to_mode(self, state: str) -> DeviceMode:
        """Converte o estado ADB para DeviceMode."""
        state_map = {
            "device": DeviceMode.ADB_NORMAL,
            "unauthorized": DeviceMode.ADB_UNAUTHORIZED,
            "recovery": DeviceMode.RECOVERY,
            "sideload": DeviceMode.SIDELOAD,
            "offline": DeviceMode.UNKNOWN,
        }
        return state_map.get(state, DeviceMode.UNKNOWN)

    def _get_fastboot_devices(self) -> list[str]:
        try:
            import sys
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                ["fastboot", "devices"],
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=creationflags,
            )
            devices = []
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    parts = line.split("\t")
                    if parts:
                        devices.append(parts[0].strip())
            return devices
        except (subprocess.SubprocessError, FileNotFoundError):
            return []

    def _fetch_device_info(self, serial: str, mode: DeviceMode) -> None:
        """Busca informações detalhadas do dispositivo."""
        try:
            if mode == DeviceMode.ADB_NORMAL:
                info_dict = self._adb_commands.get_device_info(serial)
                device_info = DeviceInfo(
                    serial=serial,
                    manufacturer=info_dict.get("manufacturer", ""),
                    model=info_dict.get("model", ""),
                    brand=info_dict.get("brand", ""),
                    device_name=info_dict.get("device", ""),
                    android_version=info_dict.get("android_version", ""),
                    sdk_version=int(info_dict.get("sdk", "0") or "0"),
                    security_patch=info_dict.get("security_patch", ""),
                    build_id=info_dict.get("build", ""),
                    cpu_abi=info_dict.get("cpu_abi", ""),
                    platform=info_dict.get("platform", ""),
                    bootloader=info_dict.get("bootloader", ""),
                    baseband=info_dict.get("baseband", ""),
                    mode=mode,
                    bootloader_unlocked=info_dict.get("bootloader_unlocked", False),
                    verified_boot_state=info_dict.get("verified_boot_state", ""),
                    encryption_state=info_dict.get("encryption_state", ""),
                )
                self._current_device = device_info
                self.device_connected.emit(device_info)
                logger.info(
                    f"Dispositivo conectado: {device_info.manufacturer} "
                    f"{device_info.model} ({serial})"
                )

            elif mode == DeviceMode.ADB_UNAUTHORIZED:
                device_info = DeviceInfo(
                    serial=serial,
                    model="Dispositivo não autorizado",
                    mode=mode,
                )
                self._current_device = device_info
                self.device_connected.emit(device_info)
                logger.warning(f"Dispositivo não autorizado: {serial}")

            elif mode == DeviceMode.FASTBOOT:
                device_info = DeviceInfo(
                    serial=serial,
                    model="Modo Fastboot",
                    mode=mode,
                )
                self._current_device = device_info
                self.device_connected.emit(device_info)
                logger.info(f"Dispositivo em Fastboot: {serial}")

            elif mode == DeviceMode.RECOVERY:
                device_info = DeviceInfo(
                    serial=serial,
                    model="Modo Recovery",
                    mode=mode,
                )
                self._current_device = device_info
                self.device_connected.emit(device_info)
                logger.info(f"Dispositivo em Recovery: {serial}")

            else:
                device_info = DeviceInfo(serial=serial, mode=mode)
                self._current_device = device_info
                self.device_connected.emit(device_info)

        except Exception as e:
            logger.error(f"Erro ao obter informações do dispositivo: {e}")
            self.error_occurred.emit(f"Erro ao ler dispositivo: {str(e)}")

    def select_device(self, serial: str) -> None:
        """Seleciona um dispositivo específico pelo serial."""
        logger.info(f"Selecionando dispositivo: {serial}")
        self._current_serial = serial

        # Determinar modo
        adb_devices = self._adb_client.get_devices()
        for dev_serial, state in adb_devices:
            if dev_serial == serial:
                mode = self._state_to_mode(state)
                self._current_mode = mode
                self._connected = True
                self._fetch_device_info(serial, mode)
                return

        # Verificar Fastboot
        fastboot_devices = self._get_fastboot_devices()
        if serial in fastboot_devices:
            self._current_mode = DeviceMode.FASTBOOT
            self._connected = True
            self._fetch_device_info(serial, DeviceMode.FASTBOOT)

    def refresh(self) -> None:
        """Força uma atualização imediata do estado dos dispositivos."""
        self._poll_devices()
