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
from src.core.device_manager import DeviceManager
from src.views.main_window import MainWindow
from src.views.pages.dashboard_page import DashboardPage
from src.views.pages.diagnostic_page import DiagnosticPage
from src.views.pages.monitoring_page import MonitoringPage
from src.viewmodels.flash_vm import FlashViewModel
from src.views.pages.flash_page import FlashPage
from src.views.pages.adb_shell_page import ADBShellPage
from src.views.pages.backup_page import BackupPage
from src.views.pages.settings_page import SettingsPage

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

    subtitle_label = QLabel("Em desenvolvimento — disponível na próxima fase")
    subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle_label.setStyleSheet("font-size: 16px; color: #86868b; background: transparent;")

    layout.addStretch()
    layout.addWidget(icon_label)
    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    layout.addStretch()

    return widget


def handle_exception(exc_type, exc_value, exc_traceback):
    """Captura exceções globais para evitar que o .exe feche silenciosamente."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    import traceback
    from datetime import datetime
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Erro não tratado na aplicação:\n{err_msg}")

    try:
        from src.utils.platform_utils import get_log_dir
        crash_file = get_log_dir() / "crash.log"
        with open(crash_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}] CRASH:\n{err_msg}\n")
    except Exception:
        pass

    try:
        from PySide6.QtWidgets import QMessageBox
        if QApplication.instance():
            QMessageBox.critical(
                None, 
                "Mobile-Diag-Pro — Erro Crítico", 
                f"Ocorreu uma falha inesperada na aplicação:\n\n{exc_value}\n\nDetalhes gravados em crash.log."
            )
    except Exception:
        pass

sys.excepthook = handle_exception


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

    # Criar gerenciador de dispositivos
    device_manager = DeviceManager()

    # Criar janela principal
    window = MainWindow()

    # Inicializar as páginas reais
    dashboard_page = DashboardPage()
    diagnostic_page = DiagnosticPage()
    flash_vm = FlashViewModel()
    flash_page = FlashPage(flash_vm)
    monitoring_page = MonitoringPage()
    adb_shell_page = ADBShellPage()
    backup_page = BackupPage()
    settings_page = SettingsPage()

    # Criar lista de páginas
    pages = [
        dashboard_page,                               # 0 - Dashboard
        diagnostic_page,                              # 1 - Diagnóstico
        flash_page,                                   # 2 - Flash / Recovery
        monitoring_page,                              # 3 - Monitoramento
        adb_shell_page,                               # 4 - ADB Shell & Logcat
        backup_page,                                  # 5 - Backup
        settings_page,                                # 6 - Configurações
    ]

    # Adicionar páginas ao QStackedWidget
    for page in pages:
        window.stacked_widget.addWidget(page)

    # Conectar sinais do DeviceManager
    def on_device_connected(device_info):
        # Atualizar title_bar.status_indicator
        status = f"🟢 {device_info.manufacturer} {device_info.model} ({device_info.mode.name})"
        window.title_bar.status_indicator.setText(status)

        # Passar device info / serial para todas as páginas ativas
        dashboard_page.update_device_info(device_info)
        diagnostic_page.set_device(device_info.serial)
        flash_page.set_device(device_info.serial)
        monitoring_page.set_device(device_info.serial)
        adb_shell_page.set_device(device_info.serial)
        backup_page.set_device(device_info.serial)

        logger.info(f"Dispositivo conectado e propagado: {device_info.serial}")

    def on_device_disconnected():
        window.title_bar.status_indicator.setText("🔴 Desconectado")
        dashboard_page.clear()
        diagnostic_page.set_device("")
        flash_page.set_device("")
        monitoring_page.set_device("")
        adb_shell_page.set_device("")
        backup_page.set_device("")
        logger.info("Nenhum dispositivo conectado.")

    device_manager.device_connected.connect(on_device_connected)
    device_manager.device_disconnected.connect(on_device_disconnected)

    # Iniciar monitoramento do device manager
    device_manager.start_monitoring()

    # Exibir janela
    window.show()
    logger.info("Interface gráfica inicializada com sucesso")

    # Iniciar loop de eventos
    exit_code = app.exec()

    # Limpeza
    device_manager.stop_monitoring()

    logger.info(f"Aplicação encerrada com código: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
