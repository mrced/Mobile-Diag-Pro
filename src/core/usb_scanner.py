"""
Scanner de baixo nível de hardware USB para Windows.
Detecta dispositivos Android conectados mesmo quando ADB/Fastboot não os reconhece
(ex.: drivers ausentes, modo MTP sem depuração, modo EDL, Fastboot sem WinUSB).
"""
import ctypes
from ctypes import wintypes
import re
import sys
from typing import Optional
from dataclasses import dataclass

from src.core.constants import DeviceMode, KNOWN_VENDORS, EDL_PIDS
from src.core.logger import get_logger

logger = get_logger(__name__)

# Constantes do Windows Config Manager e Registro
CM_GETIDLIST_FILTER_PRESENT = 0x00000100
CONFIGFLAG_FAILEDINSTALL = 0x00000040  # Código 28 (Driver não instalado)


@dataclass
class RawUSBDevice:
    """Informações brutas de um dispositivo USB detectado no Windows."""
    instance_id: str
    vid: str
    pid: str
    serial: str
    description: str
    mfg: str
    config_flags: int
    is_driver_missing: bool
    compatible_ids: list[str]
    mode: DeviceMode
    vendor_name: str
    model_name: str
    status_message: str


class USBScanner:
    """
    Varredor nativo de dispositivos USB conectados ao Windows via cfgmgr32 e winreg.
    """

    def __init__(self):
        self._is_windows = sys.platform == "win32"
        self._cfgmgr32 = None
        if self._is_windows:
            try:
                self._cfgmgr32 = ctypes.windll.cfgmgr32
            except Exception as e:
                logger.warning(f"Não foi possível carregar cfgmgr32.dll: {e}")

    def scan_connected_android_devices(self) -> list[RawUSBDevice]:
        """
        Retorna todos os dispositivos Android ou associados (ADB, Fastboot, MTP, EDL)
        fisicamente conectados via USB neste momento.
        """
        if not self._is_windows or not self._cfgmgr32:
            return []

        import winreg

        results: list[RawUSBDevice] = []
        try:
            # Obter tamanho do buffer de dispositivos presentes
            buf_len = wintypes.ULONG(0)
            res = self._cfgmgr32.CM_Get_Device_ID_List_SizeW(
                ctypes.byref(buf_len), "USB", CM_GETIDLIST_FILTER_PRESENT
            )
            if res != 0 or buf_len.value <= 1:
                return []

            buf = ctypes.create_unicode_buffer(buf_len.value)
            res = self._cfgmgr32.CM_Get_Device_ID_ListW(
                "USB", buf, buf_len.value, CM_GETIDLIST_FILTER_PRESENT
            )
            if res != 0:
                return []

            raw_str = ctypes.wstring_at(ctypes.addressof(buf), buf_len.value)
            device_ids = [d for d in raw_str.split("\x00") if d.startswith("USB\\")]

            for dev_id in device_ids:
                # Extrair VID, PID e Serial da string de instância (ex: USB\VID_31EF&PID_4EE0\db4045e2)
                m = re.search(r"VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})\\?([^\\]*)", dev_id)
                if not m:
                    continue

                vid = f"0x{m.group(1).lower()}"
                pid = f"0x{m.group(2).lower()}"
                serial = m.group(3)

                # Consultar detalhes no registro do Windows
                key_path = rf"SYSTEM\CurrentControlSet\Enum\{dev_id}"
                desc = ""
                mfg = ""
                config_flags = 0
                compat_ids = []

                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as k:
                        try:
                            desc, _ = winreg.QueryValueEx(k, "DeviceDesc")
                            # Remover prefixos de INF se presentes
                            if desc.startswith("@") and ";" in desc:
                                desc = desc.split(";")[-1]
                        except OSError:
                            pass

                        try:
                            mfg, _ = winreg.QueryValueEx(k, "Mfg")
                            if mfg.startswith("@") and ";" in mfg:
                                mfg = mfg.split(";")[-1]
                        except OSError:
                            pass

                        try:
                            config_flags, _ = winreg.QueryValueEx(k, "ConfigFlags")
                        except OSError:
                            pass

                        try:
                            raw_compat, _ = winreg.QueryValueEx(k, "CompatibleIDs")
                            if isinstance(raw_compat, list):
                                compat_ids = raw_compat
                            elif isinstance(raw_compat, str):
                                compat_ids = [raw_compat]
                        except OSError:
                            pass
                except OSError:
                    continue

                # Analisar se é um dispositivo relevante (Android, Fastboot, ADB, EDL, etc.)
                is_android = self._is_android_device(vid, pid, desc, compat_ids)
                if not is_android:
                    continue

                is_driver_missing = bool(config_flags & CONFIGFLAG_FAILEDINSTALL)
                vendor_name = KNOWN_VENDORS.get(vid, mfg or "Fabricante Android")
                model_name = self._find_cached_device_model(serial) or desc or "Dispositivo Android"

                # Determinar o modo
                mode, status_msg = self._determine_mode(vid, pid, compat_ids, is_driver_missing, desc)

                dev = RawUSBDevice(
                    instance_id=dev_id,
                    vid=vid,
                    pid=pid,
                    serial=serial,
                    description=desc,
                    mfg=mfg,
                    config_flags=config_flags,
                    is_driver_missing=is_driver_missing,
                    compatible_ids=compat_ids,
                    mode=mode,
                    vendor_name=vendor_name,
                    model_name=model_name,
                    status_message=status_msg,
                )
                results.append(dev)

        except Exception as e:
            logger.error(f"Erro ao verificar dispositivos USB nativos: {e}")

        return results

    def _is_android_device(self, vid: str, pid: str, desc: str, compat_ids: list[str]) -> bool:
        """Determina se o dispositivo USB pertence ao ecossistema Android."""
        # Verificar Vendor ID conhecido
        if vid in KNOWN_VENDORS:
            return True

        # Verificar PIDs conhecidos
        if pid in EDL_PIDS or pid in ("0x4ee0", "0x4ee7", "0x4ee8", "0x685d", "0x6860"):
            return True

        # Verificar IDs compatíveis com ADB (Prot_01) ou Fastboot (Prot_03)
        compat_str = " ".join(compat_ids).upper()
        if "CLASS_FF&SUBCLASS_42" in compat_str:
            return True

        # Descrição com palavras-chave
        desc_lower = desc.lower()
        keywords = ["android", "adb", "fastboot", "gadget", "download", "qualcomm", "mediatek", "mtp"]
        if any(kw in desc_lower for kw in keywords):
            return True

        return False

    def _determine_mode(self, vid: str, pid: str, compat_ids: list[str], is_driver_missing: bool, desc: str) -> tuple[DeviceMode, str]:
        """Classifica o modo de operação do dispositivo."""
        compat_str = " ".join(compat_ids).upper()

        # EDL Qualcomm
        if pid == "0x9008" or "9008" in desc:
            return DeviceMode.QUALCOMM_EDL, "Modo de Emergência Qualcomm (EDL 9008)"

        # Samsung Download / Odin
        if vid == "0x04e8" and pid in ("0x685d", "0x6860"):
            return DeviceMode.SAMSUNG_DOWNLOAD, "Modo Download Samsung (Odin)"

        # Fastboot (Protocolo 03 ou PID 4ee0 ou gadget)
        if "PROT_03" in compat_str or pid == "0x4ee0" or "fastboot" in desc.lower() or "gadget" in desc.lower():
            if is_driver_missing:
                return DeviceMode.DRIVER_MISSING, "Fastboot Detectado — Driver Ausente no Windows (Código 28)"
            return DeviceMode.FASTBOOT, "Modo Fastboot (Bootloader)"

        # ADB (Protocolo 01)
        if "PROT_01" in compat_str:
            if is_driver_missing:
                return DeviceMode.DRIVER_MISSING, "ADB Detectado — Driver Ausente no Windows (Código 28)"
            return DeviceMode.ADB_NORMAL, "Modo ADB Conectado"

        # Se o driver estiver ausente
        if is_driver_missing:
            return DeviceMode.DRIVER_MISSING, "Dispositivo Conectado — Driver USB Ausente (Código 28)"

        # Se for MTP / Sem Depuração
        if "MTP" in desc.upper() or "WPD" in compat_str or "CLASS_06" in compat_str:
            return DeviceMode.USB_NO_DEBUGGING, "Conectado via USB (MTP) — Depuração USB Não Ativada"

        return DeviceMode.UNKNOWN, "Dispositivo USB Conectado"

    def _find_cached_device_model(self, serial: str) -> str:
        """Busca no registro se esse serial já foi registrado anteriormente com nome amigável."""
        if not serial or serial.startswith("&") or len(serial) < 4:
            return ""

        import winreg
        key_path = r"SYSTEM\CurrentControlSet\Enum\USB"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as root:
                num_subkeys = winreg.QueryInfoKey(root)[0]
                for i in range(num_subkeys):
                    dev_id = winreg.EnumKey(root, i)
                    try:
                        with winreg.OpenKey(root, dev_id) as dev_k:
                            num_inst = winreg.QueryInfoKey(dev_k)[0]
                            for j in range(num_inst):
                                inst_id = winreg.EnumKey(dev_k, j)
                                if inst_id.lower() == serial.lower():
                                    with winreg.OpenKey(dev_k, inst_id) as inst_k:
                                        try:
                                            desc, _ = winreg.QueryValueEx(inst_k, "DeviceDesc")
                                            if desc and not desc.startswith("@") and "gadget" not in desc.lower():
                                                return desc
                                        except OSError:
                                            pass
                    except OSError:
                        pass
        except Exception:
            pass

        return ""
