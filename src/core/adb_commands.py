from typing import Dict, List, Any
from src.core.adb_client import ADBClient
from src.utils.parsers import (
    parse_battery_dumpsys, parse_cpu_info, parse_meminfo, 
    parse_df_output, parse_thermal_zones, parse_sensor_service, 
    parse_display_info, parse_ps_output, parse_package_list, safe_int, safe_float
)
from src.core.logger import get_logger

logger = get_logger(__name__)

class ADBCommands:
    """Classe com comandos de alto nível para diagnóstico."""
    
    def __init__(self, client: ADBClient):
        """Inicializa os comandos com o cliente ADB."""
        self.client = client

    def get_device_info(self, serial: str) -> Dict[str, Any]:
        """Obtém informações do dispositivo."""
        props = self.client.get_all_props(serial)
        return {
            'manufacturer': props.get('ro.product.manufacturer', ''),
            'model': props.get('ro.product.model', ''),
            'brand': props.get('ro.product.brand', ''),
            'device': props.get('ro.product.device', ''),
            'serial': serial,
            'android_version': props.get('ro.build.version.release', ''),
            'sdk': safe_int(props.get('ro.build.version.sdk', '0')),
            'security_patch': props.get('ro.build.version.security_patch', ''),
            'build': props.get('ro.build.display.id', ''),
            'cpu_abi': props.get('ro.product.cpu.abi', ''),
            'platform': props.get('ro.board.platform', ''),
            'bootloader': props.get('ro.bootloader', ''),
            'baseband': props.get('ro.baseband', '')
        }

    def get_battery_info(self, serial: str) -> Dict[str, Any]:
        """Obtém informações da bateria."""
        output = self.client.dumpsys(serial, 'battery')
        return parse_battery_dumpsys(output)

    def get_cpu_info(self, serial: str) -> Dict[str, Any]:
        """Obtém informações de CPU."""
        output = self.client.shell(serial, "cat /proc/cpuinfo")
        cpu_data = parse_cpu_info(output)
        
        stat_output = self.client.shell(serial, "cat /proc/stat")
        total_usage = 0.0
        if stat_output:
            lines = stat_output.splitlines()
            if lines and lines[0].startswith('cpu '):
                parts = [safe_int(x) for x in lines[0].split()[1:]]
                if len(parts) >= 4:
                    idle = parts[3]
                    total = sum(parts)
                    total_usage = (total - idle) / total * 100.0 if total > 0 else 0.0
        
        cpu_data['total_usage'] = total_usage
        return cpu_data

    def get_memory_info(self, serial: str) -> Dict[str, Any]:
        """Obtém informações de memória."""
        output = self.client.shell(serial, "cat /proc/meminfo")
        return parse_meminfo(output)

    def get_storage_info(self, serial: str) -> Dict[str, Any]:
        """Obtém informações de armazenamento."""
        output = self.client.shell(serial, "df -h")
        partitions = parse_df_output(output)
        return {'partitions': partitions}

    def get_thermal_info(self, serial: str) -> Dict[str, Any]:
        """Obtém informações térmicas."""
        output = self.client.shell(serial, "cat /sys/class/thermal/thermal_zone*/type /sys/class/thermal/thermal_zone*/temp")
        return {'zones': parse_thermal_zones(output), 'status': 'NONE'}

    def get_sensor_list(self, serial: str) -> List[Dict[str, Any]]:
        """Obtém lista de sensores."""
        output = self.client.dumpsys(serial, 'sensorservice')
        return parse_sensor_service(output)

    def get_display_info(self, serial: str) -> Dict[str, Any]:
        """Obtém informações de display."""
        size_output = self.client.shell(serial, "wm size")
        density_output = self.client.shell(serial, "wm density")
        return parse_display_info(size_output, density_output)

    def get_network_info(self, serial: str) -> Dict[str, Any]:
        """Obtém informações de rede."""
        return {'wifi': {}, 'cellular': {}}

    def get_running_processes(self, serial: str) -> List[Dict[str, Any]]:
        """Obtém processos em execução."""
        output = self.client.shell(serial, "ps")
        return parse_ps_output(output)

    def get_installed_packages(self, serial: str, user_only: bool = False) -> List[str]:
        """Obtém pacotes instalados."""
        cmd = "pm list packages"
        if user_only:
            cmd += " -3"
        output = self.client.shell(serial, cmd)
        return parse_package_list(output)

    def read_sysfs(self, serial: str, path: str) -> str:
        """Lê um arquivo sysfs de forma segura."""
        output = self.client.shell(serial, f"cat {path}")
        return output.strip() if "No such file" not in output else ""

    def get_battery_health_details(self, serial: str) -> Dict[str, Any]:
        """Obtém detalhes de saúde da bateria."""
        charge_full = safe_int(self.read_sysfs(serial, "/sys/class/power_supply/battery/charge_full"))
        charge_full_design = safe_int(self.read_sysfs(serial, "/sys/class/power_supply/battery/charge_full_design"))
        cycle_count = safe_int(self.read_sysfs(serial, "/sys/class/power_supply/battery/cycle_count"), -1)
        
        health_pct = -1.0
        if charge_full > 0 and charge_full_design > 0:
            health_pct = (charge_full / charge_full_design) * 100.0
            
        return {
            'charge_full': charge_full,
            'charge_full_design': charge_full_design,
            'cycle_count': cycle_count,
            'health_percentage': health_pct
        }
