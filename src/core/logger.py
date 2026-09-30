"""
Módulo de logs da aplicação.
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

def setup_logging(level: str = 'DEBUG') -> None:
    """Configura o sistema de logs."""
    log_dir: Path = Path.home() / ".mobile-diag-pro" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file: Path = log_dir / "mobile_diag.log"
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    
    # File Handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Root Logger
    root_logger = logging.getLogger()
    
    numeric_level = getattr(logging, level.upper(), logging.DEBUG)
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """Obtém um logger nomeado.
    
    Args:
        name: Nome do logger (geralmente __name__).
        
    Returns:
        Logger configurado.
    """
    return logging.getLogger(name)
