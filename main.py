"""
Mobile-Diag-Pro — Ponto de entrada da aplicação.

Inicializa o sistema de logging, cria a janela principal com todas as páginas
e inicia o loop de eventos Qt.
"""
import sys
import argparse
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from src.core.constants import APP_NAME, APP_VERSION
from src.core.theme_manager import ThemeManager
from src.core.logger import setup_logging, get_logger
from src.views.main_window import MainWindow
from src.views.pages.dashboard_page import DashboardPage

logger = get_logger(__name__)

# Diretório raiz do projeto (onde main.py reside)
ROOT_DIR = Path(__file__).resolve().parent


def create_placeholder_page(name: str) -> QWidget:
    """Cria uma página temporária com texto centralizado."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(40, 40, 40, 40)

    icon_label = QLabel("🚧")
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setStyleSheet("font-size: 48px; background: transparent;")

    title_label = QLabel(name)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet("font-size: 28px; font-weight: bold; background: transparent;")

    subtitle_label = QLabel("Em desenvolvimento — disponível em breve")
    subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle_label.setStyleSheet("font-size: 16px; background: transparent;")

    layout.addStretch()
    layout.addWidget(icon_label)
    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    layout.addStretch()

    return widget


def main() -> None:
    """Função principal da aplicação."""
    # Argumentos de linha de comando
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument("--debug", action="store_true", help="Habilitar modo debug")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="Tema da interface (dark ou light)")
    args = parser.parse_args()

    # Configurar logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(level=log_level)
    logger.info(f"Iniciando {APP_NAME} v{APP_VERSION}")

    # Configurações para displays de alta resolução
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    # Criar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("MobileDiagPro")

    # Inicializar gerenciador de temas
    theme_mgr = ThemeManager()
    theme_mgr.initialize(args.theme)

    # Criar janela principal
    window = MainWindow()

    # Criar páginas
    pages = [
        DashboardPage(),                              # 0 - Dashboard
        create_placeholder_page("Diagnóstico"),       # 1 - Diagnóstico
        create_placeholder_page("Flash / Recovery"),  # 2 - Flash
        create_placeholder_page("Monitoramento"),     # 3 - Monitoramento
        create_placeholder_page("ADB Shell"),         # 4 - ADB Shell
        create_placeholder_page("Backup"),            # 5 - Backup
        create_placeholder_page("Configurações"),     # 6 - Configurações
    ]

    # Adicionar páginas ao QStackedWidget
    for page in pages:
        window.stacked_widget.addWidget(page)

    # Exibir janela
    window.show()
    logger.info("Interface gráfica inicializada com sucesso")

    # Iniciar loop de eventos
    exit_code = app.exec()
    logger.info(f"Aplicação encerrada com código: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
