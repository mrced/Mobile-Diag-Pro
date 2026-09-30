import hashlib
import os
from typing import Dict, Tuple, List

def calculate_sha256(file_path: str) -> str:
    """
    Calcula o hash SHA-256 de um arquivo de forma eficiente.
    
    Args:
        file_path: Caminho absoluto para o arquivo.
        
    Returns:
        String hexadecimal com o hash SHA-256.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return ""

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verifica se o hash SHA-256 do arquivo corresponde ao esperado.
    
    Args:
        file_path: Caminho absoluto para o arquivo.
        expected_hash: Hash SHA-256 esperado.
        
    Returns:
        True se corresponder, False caso contrário.
    """
    if not expected_hash:
        return False
    actual_hash = calculate_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower()

def inspect_firmware_file(file_path: str) -> Dict[str, str]:
    """
    Inspeciona um arquivo de firmware e detecta sua possível partição alvo
    baseado no nome e formato.
    
    Args:
        file_path: Caminho para o arquivo.
        
    Returns:
        Dicionário com informações do arquivo: extensão, tamanho_bytes, particao_alvo.
    """
    info = {
        "extension": "",
        "size_bytes": 0,
        "target_partition": "unknown"
    }
    
    if not os.path.exists(file_path):
        return info
        
    info["size_bytes"] = os.path.getsize(file_path)
    filename = os.path.basename(file_path).lower()
    
    # Extrair extensão
    _, ext = os.path.splitext(filename)
    info["extension"] = ext.lstrip(".")
    
    # Lista comum de partições pelo nome do arquivo
    common_partitions = [
        "boot", "recovery", "system", "vendor", "product",
        "super", "vbmeta", "dtbo", "userdata", "cache"
    ]
    
    for part in common_partitions:
        if filename.startswith(part):
            info["target_partition"] = part
            break
            
    return info

def validate_flash_prerequisites(device_info: Dict[str, str], target_partition: str) -> Tuple[bool, List[str]]:
    """
    Valida os pré-requisitos antes de iniciar um flash.
    
    Args:
        device_info: Informações do dispositivo contendo nível de bateria, estado do bootloader, etc.
        target_partition: Nome da partição alvo para o flash.
        
    Returns:
        Tupla (é_valido, lista_de_erros).
    """
    errors = []
    
    # Verifica bateria
    battery_level_str = device_info.get("battery_level", "0")
    try:
        battery_level = int(battery_level_str.replace("%", ""))
        if battery_level < 30:
            errors.append(f"Nível de bateria muito baixo ({battery_level}%). Mínimo de 30% exigido.")
    except ValueError:
        pass  # Se não for possível ler a bateria, talvez permita ou avise, optamos por ignorar a falha estrita
        
    # Verifica bootloader
    unlocked = device_info.get("unlocked", "").lower()
    # Em alguns aparelhos, "yes" ou "true". Se for estritamente trancado e não for OTA sideload:
    if unlocked in ("no", "false", "0") and target_partition != "sideload":
        errors.append("O bootloader está bloqueado. Desbloqueie antes de flashear partições críticas.")
        
    # Verifica modo fastboot (se esperado)
    mode = device_info.get("mode", "").lower()
    if target_partition != "sideload" and mode not in ("fastboot", "fastbootd"):
        errors.append("O dispositivo não está em modo fastboot.")
        
    is_valid = len(errors) == 0
    return is_valid, errors
