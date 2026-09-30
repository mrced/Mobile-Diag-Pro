"""
Card Guia de Prontidão e Ações para Diagnóstico.
Informa ao usuário o estado atual do dispositivo USB e orienta exatamente o que fazer
para habilitar as análises (ex: aceitar depuração USB, sair do fastboot, etc.).
"""
from typing import Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QWidget, QGridLayout
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from src.core.constants import DeviceMode
from src.core.theme_manager import ThemeManager
from src.models.device import DeviceInfo


class ActionGuideCard(QFrame):
    """
    Cartão visual interativo que orienta o usuário sobre os passos necessários
    para que as análises de diagnóstico possam ocorrer de acordo com o estado do aparelho.
    """
    
    # Sinais emitidos para ações rápidas
    action_reboot_system = Signal()
    action_go_to_diagnostic = Signal()
    action_go_to_flash = Signal()
    action_refresh_device = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("actionGuideCard")
        self._tm = ThemeManager()
        self._current_mode = DeviceMode.UNKNOWN
        self._current_device: Optional[DeviceInfo] = None

        self._setup_ui()
        self._apply_theme()
        self.set_disconnected()

        self._tm.theme_changed.connect(lambda _: self._apply_theme())

    def _setup_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 16, 18, 16)
        self.main_layout.setSpacing(10)

        # Cabeçalho: Ícone de status + Título do Estado + Badge
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(10)

        self.icon_label = QLabel("🔌")
        self.icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        self.header_layout.addWidget(self.icon_label)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.title_label = QLabel("Prontidão para Diagnóstico")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 700; background: transparent;")
        self.subtitle_label = QLabel("Verificando pré-requisitos...")
        self.subtitle_label.setStyleSheet("font-size: 13px; background: transparent;")
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.subtitle_label)

        self.header_layout.addLayout(title_col, 1)

        self.status_badge = QLabel("Aguardando")
        self.status_badge.setStyleSheet("""
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
        """)
        self.header_layout.addWidget(self.status_badge, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self.main_layout.addLayout(self.header_layout)

        # Linha divisória
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.HLine)
        self.divider.setFixedHeight(1)
        self.main_layout.addWidget(self.divider)

        # Área de passos / instruções (Checklist & Orientações)
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 4, 0, 4)
        self.steps_layout.setSpacing(6)
        self.main_layout.addWidget(self.steps_container)

        # Barra de Botões de Ação Rápida
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)

        self.btn_primary = QPushButton("🔬 Iniciar Diagnóstico")
        self.btn_primary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_primary.setFixedHeight(34)
        self.btn_primary.setStyleSheet("""
            QPushButton {
                background-color: #0a84ff;
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #0071e3;
            }
        """)
        self.btn_primary.clicked.connect(self._on_primary_clicked)

        self.btn_secondary = QPushButton("🔄 Reiniciar no Sistema")
        self.btn_secondary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_secondary.setFixedHeight(34)
        self.btn_secondary.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f5f5f7;
                font-size: 13px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.14);
            }
        """)
        self.btn_secondary.clicked.connect(self._on_secondary_clicked)

        self.actions_layout.addWidget(self.btn_primary)
        self.actions_layout.addWidget(self.btn_secondary)
        self.actions_layout.addStretch()

        self.main_layout.addLayout(self.actions_layout)

    def _apply_theme(self) -> None:
        c = self._tm.colors
        self.setStyleSheet(f"""
            #actionGuideCard {{
                background-color: {c.surface};
                border: 1px solid {c.separator};
                border-radius: 10px;
            }}
        """)
        self.title_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c.text_primary}; background: transparent;")
        self.subtitle_label.setStyleSheet(f"font-size: 13px; color: {c.text_secondary}; background: transparent;")
        self.divider.setStyleSheet(f"background-color: {c.separator};")

    def _clear_steps(self) -> None:
        while self.steps_layout.count():
            item = self.steps_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _add_step(self, icon: str, text: str, highlight: bool = False) -> None:
        c = self._tm.colors
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(4, 2, 4, 2)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 14px; background: transparent;")
        
        lbl_text = QLabel(text)
        lbl_text.setTextFormat(Qt.TextFormat.RichText)
        color = c.text_primary if highlight else c.text_secondary
        weight = "600" if highlight else "400"
        lbl_text.setStyleSheet(f"font-size: 13px; font-weight: {weight}; color: {color}; background: transparent;")
        lbl_text.setWordWrap(True)

        row.addWidget(lbl_icon)
        row.addWidget(lbl_text, 1)

        container = QWidget()
        container.setLayout(row)
        self.steps_layout.addWidget(container)

    def set_disconnected(self) -> None:
        """Configura o cartão para o estado desconectado."""
        self._current_mode = DeviceMode.UNKNOWN
        self._current_device = None
        c = self._tm.colors

        self.icon_label.setText("🔌")
        self.title_label.setText("Nenhum Aparelho Conectado para Análise")
        self.subtitle_label.setText("Conecte um dispositivo Android via USB para iniciar os diagnósticos")
        
        self.status_badge.setText("● Desconectado")
        self.status_badge.setStyleSheet(f"background-color: rgba(142, 142, 147, 0.18); color: {c.muted}; border-radius: 8px; padding: 4px 8px; font-weight: 600;")

        self._clear_steps()
        self._add_step("1️⃣", "Conecte o smartphone ao computador usando um <b>cabo USB de boa qualidade</b> (com suporte a dados).")
        self._add_step("2️⃣", "No celular, abra <b>Configurações ➔ Sobre o telefone</b> e toque <b>7 vezes</b> seguidas em <i>'Número da Versão'</i> para ativar o modo desenvolvedor.")
        self._add_step("3️⃣", "Acesse <b>Configurações ➔ Sistema ➔ Opções do Desenvolvedor</b> e ATIVE a opção <b>'Depuração USB'</b>.")
        self._add_step("4️⃣", "Ao conectar, altere a notificação USB de <i>'Apenas Carregar'</i> para <b>'Transferência de Arquivos (MTP)'</b> caso solicitado.")

        self.btn_primary.setVisible(False)
        self.btn_secondary.setText("🔄 Atualizar / Verificar Novamente")
        self.btn_secondary.setVisible(True)

    def update_status(self, device_info: DeviceInfo) -> None:
        """Atualiza as instruções e botões com base no estado do dispositivo detectado."""
        self._current_device = device_info
        mode = getattr(device_info, 'mode', DeviceMode.UNKNOWN)
        self._current_mode = mode
        c = self._tm.colors

        self._clear_steps()

        if mode == DeviceMode.ADB_UNAUTHORIZED:
            self.icon_label.setText("⚠️")
            self.title_label.setText("Ação Obrigatória: Autorizar Depuração USB na Tela do Celular")
            self.subtitle_label.setText("O aparelho foi detectado, mas o Android requer sua permissão de segurança para liberar a análise")

            self.status_badge.setText("● Não Autorizado (RSA)")
            self.status_badge.setStyleSheet("background-color: rgba(255, 69, 58, 0.2); color: #ff453a; border-radius: 8px; padding: 4px 8px; font-weight: 700;")

            self._add_step("📱", "<b>Desbloqueie a tela</b> do seu celular agora.", highlight=True)
            self._add_step("🔑", "Uma mensagem pop-up intitulada <b>'Permitir a depuração USB?'</b> estará visível.", highlight=True)
            self._add_step("☑️", "Marque a caixa de seleção <b>'Sempre permitir a partir deste computador'</b>.", highlight=True)
            self._add_step("🔘", "Toque no botão <b>'Permitir'</b> ou <b>'OK'</b> para liberar o acesso.", highlight=True)
            self._add_step("💡", "<i>Dica: Se a mensagem não aparecer, desconecte e reconecte o cabo USB ou desative e reative a 'Depuração USB'.</i>")

            self.btn_primary.setText("🔄 Verificar Autorização")
            self.btn_primary.setVisible(True)
            self.btn_secondary.setVisible(False)

        elif mode in (DeviceMode.FASTBOOT, DeviceMode.FASTBOOTD):
            self.icon_label.setText("⚡")
            self.title_label.setText("Aparelho Detectado em Modo Fastboot (Bootloader)")
            self.subtitle_label.setText("O dispositivo está em modo de pré-inicialização de baixo nível")

            self.status_badge.setText("● Modo Fastboot")
            self.status_badge.setStyleSheet("background-color: rgba(255, 149, 0, 0.2); color: #ff9500; border-radius: 8px; padding: 4px 8px; font-weight: 700;")

            self._add_step("ℹ️", "Neste modo, o sistema Android não está carregado. Análises de sensores, bateria avançada e processos <b>não estão acessíveis</b>.")
            self._add_step("⚡", "<b>Funções disponíveis agora:</b> Gravação de partições/ROMs, desbloqueio de bootloader e testes de baixo nível.")
            self._add_step("💡", "<b>Para realizar o Diagnóstico Completo:</b> Reinicie o aparelho normalmente no sistema Android.")

            self.btn_primary.setText("⚡ Abrir Aba Flash / Recovery")
            self.btn_primary.setVisible(True)
            self.btn_secondary.setText("🔄 Reiniciar no Sistema (Fastboot Continue)")
            self.btn_secondary.setVisible(True)

        elif mode in (DeviceMode.RECOVERY, DeviceMode.SIDELOAD):
            self.icon_label.setText("📥")
            self.title_label.setText("Aparelho Detectado em Modo Recovery / Sideload")
            self.subtitle_label.setText("O dispositivo está no ambiente de recuperação")

            self.status_badge.setText("● Modo Recovery")
            self.status_badge.setStyleSheet("background-color: rgba(255, 159, 10, 0.2); color: #ff9f0a; border-radius: 8px; padding: 4px 8px; font-weight: 700;")

            self._add_step("ℹ️", "O modo Recovery permite aplicar atualizações OTA ou instalar pacotes de firmware via Sideload.")
            self._add_step("💡", "Para liberar os testes de diagnóstico de hardware, memória, CPU e tela, o aparelho precisa ser reiniciado no sistema.")

            self.btn_primary.setText("📥 Abrir Aba ADB Sideload")
            self.btn_primary.setVisible(True)
            self.btn_secondary.setText("🔄 Reiniciar no Sistema Android")
            self.btn_secondary.setVisible(True)

        elif mode == DeviceMode.ADB_NORMAL:
            self.icon_label.setText("✅")
            model = getattr(device_info, 'model', 'Dispositivo')
            manufacturer = getattr(device_info, 'manufacturer', '')
            self.title_label.setText(f"Aparelho Pronto para Análise — {manufacturer} {model}".strip())
            self.subtitle_label.setText("Todos os requisitos para diagnóstico avançado e telemetria estão atendidos")

            self.status_badge.setText("● Pronto para Diagnóstico")
            self.status_badge.setStyleSheet(f"background-color: rgba(48, 209, 88, 0.2); color: {c.success}; border-radius: 8px; padding: 4px 8px; font-weight: 700;")

            unlocked = getattr(device_info, 'bootloader_unlocked', False)
            bootloader_str = "Desbloqueado (Permite modificações de ROM/Root)" if unlocked else "Bloqueado (Original de Fábrica)"
            android_ver = getattr(device_info, 'android_version', '')
            sdk = getattr(device_info, 'sdk_version', 0)

            self._add_step("🟢", f"Comunicação ADB autorizada e operacional (Android {android_ver}, API {sdk}).", highlight=True)
            self._add_step("🔓", f"<b>Estado do Bootloader:</b> {bootloader_str}.")
            self._add_step("🔬", "Todas as <b>50+ rotinas de teste</b> (Bateria, CPU, RAM, Sensores, Rede, Armazenamento) estão liberadas para execução.")

            self.btn_primary.setText("🔬 Iniciar Diagnóstico Completo")
            self.btn_primary.setVisible(True)
            self.btn_secondary.setText("🔄 Reiniciar Aparelho")
            self.btn_secondary.setVisible(True)

        else:
            self.set_disconnected()

    def _on_primary_clicked(self) -> None:
        if self._current_mode == DeviceMode.ADB_NORMAL:
            self.action_go_to_diagnostic.emit()
        elif self._current_mode == DeviceMode.ADB_UNAUTHORIZED:
            self.action_refresh_device.emit()
        elif self._current_mode in (DeviceMode.FASTBOOT, DeviceMode.FASTBOOTD, DeviceMode.RECOVERY, DeviceMode.SIDELOAD):
            self.action_go_to_flash.emit()

    def _on_secondary_clicked(self) -> None:
        if self._current_mode in (DeviceMode.FASTBOOT, DeviceMode.FASTBOOTD, DeviceMode.RECOVERY, DeviceMode.SIDELOAD, DeviceMode.ADB_NORMAL):
            self.action_reboot_system.emit()
        else:
            self.action_refresh_device.emit()
