import re

def safe_int(value: str, default: int = 0) -> int:
    """Converte para inteiro com segurança."""
    try:
        if not value: return default
        return int(re.sub(r'[^\d-]', '', str(value)))
    except (ValueError, TypeError):
        return default

def safe_float(value: str, default: float = 0.0) -> float:
    """Converte para float com segurança."""
    try:
        if not value: return default
        return float(re.sub(r'[^\d.-]', '', str(value)))
    except (ValueError, TypeError):
        return default

def parse_battery_dumpsys(output: str) -> dict:
    """Faz o parse da saída do comando 'dumpsys battery'."""
    data = {}
    if not output: return data
    for line in output.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            data[key.strip().lower().replace(' ', '_')] = val.strip()
    return data

def parse_getprop_output(output: str) -> dict[str, str]:
    """Faz o parse da saída do comando 'getprop'."""
    data = {}
    if not output: return data
    for line in output.splitlines():
        match = re.match(r'\[(.*?)\]:\s*\[(.*?)\]', line)
        if match:
            data[match.group(1)] = match.group(2)
    return data

def parse_cpu_info(output: str) -> dict:
    """Faz o parse do arquivo /proc/cpuinfo."""
    data = {'cores': []}
    if not output: return data
    current_core = {}
    for line in output.splitlines():
        if not line.strip():
            if current_core:
                data['cores'].append(current_core)
                current_core = {}
            continue
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_')
            val = val.strip()
            if key == 'processor':
                current_core['index'] = safe_int(val)
            elif key == 'model_name':
                current_core['model'] = val
            elif key == 'cpu_mhz':
                current_core['mhz'] = safe_float(val)
            else:
                current_core[key] = val
    if current_core:
        data['cores'].append(current_core)
    return data

def parse_meminfo(output: str) -> dict:
    """Faz o parse do arquivo /proc/meminfo."""
    data = {}
    if not output: return data
    for line in output.splitlines():
        if ':' in line:
            parts = line.split(':', 1)
            key = parts[0].strip().lower().replace(' ', '_')
            val = parts[1].strip()
            val_bytes = safe_int(val) * 1024 if 'kB' in val else safe_int(val)
            data[key] = val_bytes
    return data

def parse_df_output(output: str) -> list[dict]:
    """Faz o parse da saída do comando 'df -h'."""
    partitions = []
    if not output: return partitions
    lines = output.splitlines()
    if not lines: return partitions
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 6:
            partitions.append({
                'name': parts[0],
                'size': parts[1],
                'used': parts[2],
                'free': parts[3],
                'use_percent': parts[4],
                'mount_point': parts[5]
            })
    return partitions

def parse_ps_output(output: str) -> list[dict]:
    """Faz o parse da saída do comando 'ps'."""
    processes = []
    if not output: return processes
    lines = output.splitlines()
    if not lines: return processes
    for line in lines[1:]:
        parts = line.split(None, 8)
        if len(parts) >= 9:
            processes.append({
                'user': parts[0],
                'pid': safe_int(parts[1]),
                'ppid': safe_int(parts[2]),
                'vsz': safe_int(parts[3]),
                'rss': safe_int(parts[4]),
                'name': parts[8]
            })
    return processes

def parse_thermal_zones(output: str) -> list[dict]:
    """Faz o parse da zona térmica."""
    zones = []
    if not output: return zones
    for line in output.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            zones.append({
                'name': key.strip(),
                'temperature': safe_float(val)
            })
    return zones

def parse_sensor_service(output: str) -> list[dict]:
    """Faz o parse do serviço de sensor."""
    sensors = []
    if not output: return sensors
    for line in output.splitlines():
        if 'Sensor' in line or 'name' in line.lower():
            sensors.append({'raw': line.strip()})
    return sensors

def parse_devices_output(output: str) -> list[tuple[str, str]]:
    """Faz o parse da saída de 'adb devices'."""
    devices = []
    if not output: return devices
    for line in output.splitlines()[1:]:
        if line.strip():
            parts = line.split()
            if len(parts) == 2:
                devices.append((parts[0], parts[1]))
    return devices

def parse_display_info(size_output: str, density_output: str) -> dict:
    """Faz o parse das informações de display."""
    data = {}
    if size_output and 'Physical size:' in size_output:
        data['resolution'] = size_output.split(':')[1].strip()
    if density_output and 'Physical density:' in density_output:
        data['density'] = safe_int(density_output.split(':')[1])
    return data

def parse_package_list(output: str) -> list[str]:
    """Faz o parse da lista de pacotes."""
    packages = []
    if not output: return packages
    for line in output.splitlines():
        if line.startswith('package:'):
            packages.append(line.replace('package:', '').strip())
    return packages
