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

    # Bloqueio de instância única (Single Instance Lock)
    from PySide6.QtNetwork import QLocalServer, QLocalSocket

    ipc_server_name = "MobileDiagPro_SingleInstance_IPC"
    ipc_socket = QLocalSocket()
    ipc_socket.connectToServer(ipc_server_name)
    if ipc_socket.waitForConnected(400):
        # Outra instância já está ativa! Notifica e sai imediatamente.
        ipc_socket.write(b"ACTIVATE")
        ipc_socket.waitForBytesWritten(1000)
        ipc_socket.disconnectFromServer()
        logger.info("Instância existente detectada. Encerrando processo duplicado.")
        sys.exit(0)

    # Iniciar servidor IPC local para escutar futuras instâncias
    ipc_server = QLocalServer()
    ipc_server.removeServer(ipc_server_name)
    ipc_server.listen(ipc_server_name)

    # Inicializar gerenciador de temas
    theme_mgr = ThemeManager()
    theme_mgr.initialize(args.theme)

    # Criar gerenciador de dispositivos
    device_manager = DeviceManager()

    # Criar janela principal
    window = MainWindow()

    def on_new_instance():
        client = ipc_server.nextPendingConnection()
        if client:
            client.waitForReadyRead(400)
            window.showNormal()
            window.raise_()
            window.activateWindow()
            client.disconnectFromServer()

    ipc_server.newConnection.connect(on_new_instance)

    # Inicializar as páginas reais como filhas do stacked_widget
    dashboard_page = DashboardPage(window.stacked_widget)
    diagnostic_page = DiagnosticPage(window.stacked_widget)
    flash_vm = FlashViewModel()
    flash_page = FlashPage(flash_vm, parent=window.stacked_widget)
    monitoring_page = MonitoringPage(window.stacked_widget)
    adb_shell_page = ADBShellPage(window.stacked_widget)
    backup_page = BackupPage(window.stacked_widget)
    settings_page = SettingsPage(window.stacked_widget)

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
        diagnostic_page.set_device_info(device_info)
        flash_page.set_device(device_info.serial)
        monitoring_page.set_device(device_info.serial)
        adb_shell_page.set_device(device_info.serial)
        backup_page.set_device(device_info.serial)

        logger.info(f"Dispositivo conectado e propagado: {device_info.serial}")

    def on_device_disconnected():
        window.title_bar.status_indicator.setText("🔴 Desconectado")
        dashboard_page.clear()
        diagnostic_page.clear()
        flash_page.set_device("")
        monitoring_page.set_device("")
        adb_shell_page.set_device("")
        backup_page.set_device("")
        logger.info("Nenhum dispositivo conectado.")

    device_manager.device_connected.connect(on_device_connected)
    device_manager.device_disconnected.connect(on_device_disconnected)

    # Conectar navegação rápida e ações do Dashboard
    dashboard_page.action_go_to_diagnostic.connect(lambda: window.sidebar._on_button_clicked(1))
    dashboard_page.action_go_to_flash.connect(lambda: window.sidebar._on_button_clicked(2))
    dashboard_page.action_open_shell.connect(lambda: window.sidebar._on_button_clicked(4))

    def on_dashboard_reboot():
        serial = device_manager.current_serial
        mode = device_manager.current_mode
        from src.core.constants import DeviceMode
        import subprocess
        if mode in (DeviceMode.FASTBOOT, DeviceMode.FASTBOOTD):
            subprocess.run(["fastboot", "continue"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        elif serial:
            device_manager.adb_client.reboot(serial)

    dashboard_page.action_reboot.connect(on_dashboard_reboot)

    def on_dashboard_optimize():
        serial = device_manager.current_serial
        if not serial:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(window, "Aviso", "Nenhum dispositivo conectado para otimização.")
            return
        from src.views.dialogs.optimizer_dialog import OptimizerDialog
        dlg = OptimizerDialog(serial, window)
        dlg.exec()

    dashboard_page.action_optimize.connect(on_dashboard_optimize)


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
    import multiprocessing
    multiprocessing.freeze_support()
    main()
