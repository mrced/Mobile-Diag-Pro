import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QFileDialog, QCheckBox, QProgressBar, QTextEdit,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QSplitter, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Slot

class FlashPage(QWidget):
    """
    Página de Flash, Firmware & Desbloqueio.
    Fornece interface para instalação de partições (recovery, boot, super), stock ROM, 
    ADB sideload, controles de bootloader e ferramentas de manutenção técnica estilo TFT/MiFlash/Odin.
    """
    
    def __init__(self, view_model=None, parent: QWidget | None = None) -> None:
        """
        Inicializa a página de Flash.
        
        Args:
            view_model: Instância opcional do FlashViewModel.
            parent: Widget pai opcional.
        """
        super().__init__(parent)
        if view_model is None:
            from src.viewmodels.flash_vm import FlashViewModel
            self.view_model = FlashViewModel(self)
        else:
            self.view_model = view_model
            
        self.current_serial: str = ""
        self._setup_ui()
        self._connect_signals()

    def set_device(self, serial: str) -> None:
        """Atualiza o dispositivo ativo na página de flash."""
        self.current_serial = serial
        if serial:
            self._append_log(f"[INFO] Dispositivo selecionado: {serial}")
        else:
            self._append_log("[INFO] Nenhum dispositivo conectado.")
        
    def _setup_ui(self) -> None:
        """Configura a interface gráfica da página."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Cabeçalho
        header_layout = QVBoxLayout()
        title = QLabel("Flash, Firmware & Manutenção Técnica")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        subtitle = QLabel("Instalação de Stock ROM, Recovery, ADB Sideload e Desbloqueio Técnico (Estilo MiFlash / Odin / TFT)")
        subtitle.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)
        
        # Área Principal (Tabs + Console)
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_partition_flash_tab(), "⚡ Flash de Partição")
        self.tabs.addTab(self._create_stock_rom_tab(), "📦 Stock ROM")
        self.tabs.addTab(self._create_sideload_tab(), "📥 ADB Sideload")
        self.tabs.addTab(self._create_boot_control_tab(), "🔓 Desbloqueio & Manutenção (TFT / FRP / Wipe)")
        splitter.addWidget(self.tabs)
        
        # Console e Progresso
        console_widget = self._create_console_section()
        splitter.addWidget(console_widget)
        
        # Proporções (Tabs 60%, Console 40%)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)
        
    def _create_partition_flash_tab(self) -> QWidget:
        """Cria a aba de Flash de Partição Individual."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Seleção de Arquivo
        file_group = QGroupBox("Arquivo de Imagem (.img)")
        file_layout = QHBoxLayout()
        self.img_path_input = QLineEdit()
        self.img_path_input.setPlaceholderText("Selecione ou arraste um arquivo .img...")
        btn_browse_img = QPushButton("Procurar...")
        btn_browse_img.clicked.connect(self._browse_image)
        file_layout.addWidget(self.img_path_input)
        file_layout.addWidget(btn_browse_img)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Seleção de Partição
        part_group = QGroupBox("Configurações de Gravação")
        part_layout = QVBoxLayout()
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Partição de Destino:"))
        self.cb_partition = QComboBox()
        self.cb_partition.setEditable(True)
        self.cb_partition.addItems([
            "boot", "recovery", "init_boot", "vbmeta", "vbmeta_system",
            "super", "system", "vendor", "cust", "userdata"
        ])
        h_layout.addWidget(self.cb_partition, 1)
        part_layout.addLayout(h_layout)
        
        # Opções Adicionais
        self.chk_disable_avb = QCheckBox("Desabilitar AVB / Verity (--disable-verity --disable-verification)")
        self.chk_reboot = QCheckBox("Reiniciar automaticamente após o término")
        self.chk_reboot.setChecked(True)
        part_layout.addWidget(self.chk_disable_avb)
        part_layout.addWidget(self.chk_reboot)
        
        part_group.setLayout(part_layout)
        layout.addWidget(part_group)
        
        # Botão Flashear
        btn_flash = QPushButton("Gravar Partição")
        btn_flash.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 10px;")
        btn_flash.clicked.connect(self._on_flash_clicked)
        layout.addWidget(btn_flash, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addStretch()
        return tab
        
    def _create_stock_rom_tab(self) -> QWidget:
        """Cria a aba de Flash de Stock ROM Multi-Partição."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Seleção da Pasta da ROM
        fw_group = QGroupBox("Pasta da Firmware / Imagens")
        fw_layout = QHBoxLayout()
        self.fw_path_input = QLineEdit()
        self.fw_path_input.setPlaceholderText("Selecione o diretório contendo as imagens da Stock ROM...")
        btn_browse_fw = QPushButton("Procurar Diretório...")
        btn_browse_fw.clicked.connect(self._browse_firmware)
        fw_layout.addWidget(self.fw_path_input)
        fw_layout.addWidget(btn_browse_fw)
        fw_group.setLayout(fw_layout)
        layout.addWidget(fw_group)
        
        # Tabela de Partições Identificadas
        self.partition_table = QTableWidget(0, 2)
        self.partition_table.setHorizontalHeaderLabels(["Partição / Arquivo", "Status de Verificação"])
        self.partition_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.partition_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.partition_table)
        
        btn_flash_all = QPushButton("Instalar Stock ROM Completa")
        btn_flash_all.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        btn_flash_all.clicked.connect(lambda: self.view_model.flash_log.emit("Iniciando flash sequencial da ROM..."))
        layout.addWidget(btn_flash_all, alignment=Qt.AlignmentFlag.AlignRight)
        
        return tab
        
    def _create_sideload_tab(self) -> QWidget:
        """Cria a aba de ADB Sideload."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        instructions = QLabel(
            "<b>Instruções:</b><br>"
            "1. Reinicie o dispositivo em modo <b>Recovery</b>.<br>"
            "2. Selecione a opção <i>'Apply update from ADB'</i> no dispositivo.<br>"
            "3. Conecte o cabo USB e selecione o arquivo .zip abaixo.<br>"
            "4. Clique em Iniciar Sideload."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        file_layout = QHBoxLayout()
        self.zip_path_input = QLineEdit()
        self.zip_path_input.setPlaceholderText("Arquivo OTA ou ROM (.zip)...")
        btn_browse_zip = QPushButton("Procurar...")
        btn_browse_zip.clicked.connect(self._browse_zip)
        file_layout.addWidget(self.zip_path_input)
        file_layout.addWidget(btn_browse_zip)
        layout.addLayout(file_layout)
        
        btn_sideload = QPushButton("Iniciar Sideload")
        btn_sideload.clicked.connect(self._on_sideload_clicked)
        layout.addWidget(btn_sideload, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addStretch()
        return tab
        
    def _create_boot_control_tab(self) -> QWidget:
        """Cria a aba de controle de boot, manutenção e desbloqueio (Estilo TFT / Odin / MiFlash)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # 1. Modos de Boot (Transições Rápidas)
        reboot_group = QGroupBox("🔄 Modos de Boot & Reinicialização")
        rl = QHBoxLayout()
        rl.setSpacing(8)
        
        btn_reboot_sys = QPushButton("📱 Sistema Normal")
        btn_reboot_sys.clicked.connect(lambda: self.view_model.reboot_device(self.current_serial or "auto", "normal"))
        
        btn_reboot_rec = QPushButton("🛠️ Recovery Mode")
        btn_reboot_rec.clicked.connect(lambda: self.view_model.reboot_device(self.current_serial or "auto", "recovery"))
        
        btn_reboot_bl = QPushButton("⚡ Fastboot (Bootloader)")
        btn_reboot_bl.clicked.connect(lambda: self.view_model.reboot_device(self.current_serial or "auto", "bootloader"))
        
        btn_reboot_fbd = QPushButton("📦 Fastbootd (Dynamic)")
        btn_reboot_fbd.clicked.connect(lambda: self.view_model.reboot_device(self.current_serial or "auto", "fastbootd"))
        
        btn_reboot_dl = QPushButton("⬇️ Odin / Download (Samsung)")
        btn_reboot_dl.clicked.connect(lambda: self.view_model.reboot_device(self.current_serial or "auto", "download"))
        
        btn_reboot_edl = QPushButton("🔌 Qualcomm EDL 9008")
        btn_reboot_edl.clicked.connect(lambda: self.view_model.reboot_device(self.current_serial or "auto", "edl"))
        
        for b in [btn_reboot_sys, btn_reboot_rec, btn_reboot_bl, btn_reboot_fbd, btn_reboot_dl, btn_reboot_edl]:
            rl.addWidget(b)
        reboot_group.setLayout(rl)
        layout.addWidget(reboot_group)
        
        # 2. Desbloqueio e Remoção de Bloqueios (Estilo TFT / MiFlash / Dr.Fone)
        unlock_group = QGroupBox("🔓 Ferramentas Técnicas de Desbloqueio & Manutenção (Estilo TFT / MiFlash / Odin)")
        ul = QVBoxLayout()
        ul.setSpacing(12)
        
        desc_label = QLabel(
            "<b>Operações Técnicas de Manutenção e Recuperação:</b><br>"
            "Execute reset de fábrica, desbloqueio de bootloader OEM e recuperação de travamentos em tela fastboot."
        )
        desc_label.setStyleSheet("color: #a0a0b0; font-size: 13px;")
        ul.addWidget(desc_label)
        
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        
        # Wipe Userdata (Reset de fábrica / Limpeza de PIN ou padrão esquecido)
        btn_wipe_data = QPushButton("🧹 Formatar / Reset de Fábrica (Wipe Userdata)")
        btn_wipe_data.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; padding: 10px;")
        btn_wipe_data.setToolTip("Apaga as partições userdata e cache em modo Fastboot (remove senhas/padrões esquecidos)")
        btn_wipe_data.clicked.connect(self._on_wipe_userdata_clicked)
        action_row.addWidget(btn_wipe_data)
        
        # Erase FRP
        btn_erase_frp = QPushButton("🛡️ Resetar Partição FRP (Conta Google)")
        btn_erase_frp.setStyleSheet("background-color: #f0ad4e; color: white; font-weight: bold; padding: 10px;")
        btn_erase_frp.setToolTip("Tenta resetar a partição de proteção de fábrica (FRP) via comando Fastboot")
        btn_erase_frp.clicked.connect(self._on_erase_frp_clicked)
        action_row.addWidget(btn_erase_frp)
        
        # Desbloquear Bootloader
        btn_unlock_bl = QPushButton("🔓 Desbloquear Bootloader (OEM Unlock)")
        btn_unlock_bl.setStyleSheet("background-color: #0275d8; color: white; font-weight: bold; padding: 10px;")
        btn_unlock_bl.setToolTip("Envia 'fastboot flashing unlock' ou 'fastboot oem unlock' para liberar o bootloader")
        btn_unlock_bl.clicked.connect(self._on_unlock_bootloader_clicked)
        action_row.addWidget(btn_unlock_bl)
        
        # Sair de Bootloop
        btn_fix_bootloop = QPushButton("🔄 Sair de Bootloop (Fastboot Continue)")
        btn_fix_bootloop.setStyleSheet("padding: 10px;")
        btn_fix_bootloop.clicked.connect(lambda: self.view_model.reboot_device(self.current_serial or "auto", "continue"))
        action_row.addWidget(btn_fix_bootloop)
        
        ul.addLayout(action_row)
        
        # Card Informativo de Protocolos Fabricantes
        info_frame = QFrame()
        info_frame.setStyleSheet("background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 12px;")
        info_layout = QVBoxLayout(info_frame)
        info_title = QLabel("💡 <b>Guia Rápido dos Modos de Desbloqueio e Flashing por Marca:</b>")
        info_title.setStyleSheet("font-size: 13px; color: #f5f5f7;")
        info_text = QLabel(
            "• <b>Xiaomi / POCO (Mi Flash / TFT):</b> Coloque em Fastboot (Volume - + Power). Para ROMs completas use o script flash_all.bat ou grave super/boot.<br>"
            "• <b>Samsung (Odin Mode):</b> Conecte o cabo USB segurando Volume + e Volume - com o aparelho desligado para entrar em Download Mode.<br>"
            "• <b>Motorola:</b> Para obter a chave de desbloqueio do portal oficial, use 'fastboot oem get_unlock_data'.<br>"
            "• <b>Qualcomm Emergency (EDL 9008):</b> Utilizado quando o aparelho não liga nem entra em Fastboot (requer cabo EDL ou test-point na placa)."
        )
        info_text.setStyleSheet("color: #a0a0b0; font-size: 12px; line-height: 1.4;")
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)
        ul.addWidget(info_frame)
        
        unlock_group.setLayout(ul)
        layout.addWidget(unlock_group)
        
        layout.addStretch()
        return tab
        
    def _create_console_section(self) -> QWidget:
        """Cria a seção inferior com logs e barras de progresso."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Progresso
        self.lbl_status = QLabel("Aguardando ação...")
        layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Console de Log
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Console de Operação:"))
        log_header.addStretch()
        btn_clear_log = QPushButton("Limpar Log")
        btn_clear_log.setFlat(True)
        btn_clear_log.clicked.connect(self._clear_log)
        log_header.addWidget(btn_clear_log)
        layout.addLayout(log_header)
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: monospace;")
        layout.addWidget(self.log_console)
        
        return widget
        
    def _connect_signals(self) -> None:
        """Conecta os sinais do ViewModel aos componentes da View."""
        self.view_model.flash_log.connect(self._append_log)
        self.view_model.flash_progress.connect(self._update_progress)
        self.view_model.flash_completed.connect(self._on_flash_completed)
        self.view_model.partition_list_updated.connect(self._update_partition_table)
        
    # --- Slots de Ações da Interface ---
    
    @Slot()
    def _browse_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem", "", "Imagens de Disco (*.img);;Todos os Arquivos (*)")
        if file_path:
            self.img_path_input.setText(file_path)
            
    @Slot()
    def _browse_firmware(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Firmware")
        if path:
            self.fw_path_input.setText(path)
            self.view_model.load_firmware(path)
            
    @Slot()
    def _browse_zip(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Atualização ZIP", "", "Arquivos ZIP (*.zip);;Todos os Arquivos (*)")
        if file_path:
            self.zip_path_input.setText(file_path)

    @Slot()
    def _on_flash_clicked(self) -> None:
        image_path = self.img_path_input.text()
        partition = self.cb_partition.currentText()
        if not image_path or not partition:
            self._append_log("Erro: Por favor, selecione uma imagem e uma partição de destino.")
            return
        
        self.view_model.start_flash(self.current_serial or "auto", partition, image_path)

    @Slot()
    def _on_sideload_clicked(self) -> None:
        zip_path = self.zip_path_input.text()
        if not zip_path:
            self._append_log("Erro: Selecione um arquivo ZIP para o sideload.")
            return
        self.view_model.start_sideload(self.current_serial or "auto", zip_path)

    @Slot()
    def _on_wipe_userdata_clicked(self) -> None:
        reply = QMessageBox.warning(
            self,
            "Confirmar Formatação Completa (Wipe)",
            "<b>ATENÇÃO:</b> Esta operação apagará todos os dados, fotos, configurações e senhas/padrões do usuário (Reset de Fábrica via Fastboot).<br><br>Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.view_model.wipe_userdata(self.current_serial or "auto")

    @Slot()
    def _on_erase_frp_clicked(self) -> None:
        reply = QMessageBox.question(
            self,
            "Resetar Partição FRP (Conta Google)",
            "O comando tentará apagar a partição 'frp' via Fastboot.<br><br><b>Nota:</b> Requer bootloader desbloqueado ou suporte no aparelho.<br><br>Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.view_model.erase_frp(self.current_serial or "auto")

    @Slot()
    def _on_unlock_bootloader_clicked(self) -> None:
        reply = QMessageBox.warning(
            self,
            "Desbloquear Bootloader",
            "<b>AVISO IMPORTANTE:</b> O desbloqueio do bootloader apagará todos os dados do dispositivo e poderá invalidar a garantia.<br><br>Uma confirmação na tela do aparelho poderá ser solicitada.<br><br>Deseja enviar o comando de desbloqueio?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.view_model.unlock_bootloader(self.current_serial or "auto")

    @Slot(str)
    def _append_log(self, msg: str) -> None:
        self.log_console.append(msg)
        self.log_console.verticalScrollBar().setValue(self.log_console.verticalScrollBar().maximum())

    @Slot(int, str)
    def _update_progress(self, percent: int, msg: str) -> None:
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(msg)

    @Slot(bool, str)
    def _on_flash_completed(self, success: bool, msg: str) -> None:
        self._append_log(f"\n[{'SUCESSO' if success else 'FALHA'}] {msg}\n")
        self.lbl_status.setText("Pronto." if success else "Operação falhou.")

    @Slot(list)
    def _update_partition_table(self, partitions: list) -> None:
        self.partition_table.setRowCount(0)
        for row, part in enumerate(partitions):
            self.partition_table.insertRow(row)
            self.partition_table.setItem(row, 0, QTableWidgetItem(part))
            status_item = QTableWidgetItem("Pronto")
            status_item.setForeground(Qt.GlobalColor.green)
            self.partition_table.setItem(row, 1, status_item)

    @Slot()
    def _clear_log(self) -> None:
        self.log_console.clear()
