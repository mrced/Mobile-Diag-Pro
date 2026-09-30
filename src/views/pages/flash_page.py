import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QFileDialog, QCheckBox, QProgressBar, QTextEdit,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QSplitter
)
from PySide6.QtCore import Qt, Slot

class FlashPage(QWidget):
    """
    Página de Flash & Firmware.
    Fornece interface para instalação de partições (recovery, boot), stock ROM, 
    ADB sideload e controles de bootloader.
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
            self._append_log(f"[INFO] Dispositivo selecionado para Flash: {serial}")
        
    def _setup_ui(self) -> None:
        """Configura a interface gráfica da página."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Cabeçalho
        header_layout = QVBoxLayout()
        title = QLabel("Flash & Firmware")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        subtitle = QLabel("Instalação de Stock ROM, Recovery Customizado e ADB Sideload")
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
        self.tabs.addTab(self._create_boot_control_tab(), "🔄 Controle de Boot")
        splitter.addWidget(self.tabs)
        
        # Console e Progresso
        console_widget = self._create_console_section()
        splitter.addWidget(console_widget)
        
        # Proporções (Tabs 60%, Console 40%)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)
        
    def set_device(self, serial: str) -> None:
        """Define o serial do dispositivo ativo."""
        # Podemos salvar o serial para usar em operações futuras
        self._current_serial = serial
        if serial:
            self._append_log(f"Dispositivo conectado: {serial}")
        else:
            self._append_log("Dispositivo desconectado.")
        
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
        
        # Configurações de Flash
        config_group = QGroupBox("Configurações")
        config_layout = QVBoxLayout()
        
        part_layout = QHBoxLayout()
        part_layout.addWidget(QLabel("Partição de Destino:"))
        self.cb_partition = QComboBox()
        self.cb_partition.addItems([
            "boot", "recovery", "init_boot", "vbmeta", 
            "dtbo", "vendor_boot", "super", "system"
        ])
        self.cb_partition.setEditable(True) # Permite partição customizada
        part_layout.addWidget(self.cb_partition)
        part_layout.addStretch()
        config_layout.addLayout(part_layout)
        
        self.chk_disable_avb = QCheckBox("Desabilitar AVB / dm-verity (vbmeta flags)")
        self.chk_auto_reboot = QCheckBox("Auto-reboot após finalizar")
        self.chk_auto_reboot.setChecked(True)
        config_layout.addWidget(self.chk_disable_avb)
        config_layout.addWidget(self.chk_auto_reboot)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Ação Principal
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_flash = QPushButton("Iniciar Gravação (Flash)")
        btn_flash.setStyleSheet("background-color: #2980b9; color: white; padding: 8px 16px; font-weight: bold; border-radius: 4px;")
        btn_flash.clicked.connect(self._on_flash_clicked)
        btn_layout.addWidget(btn_flash)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        return tab
        
    def _create_stock_rom_tab(self) -> QWidget:
        """Cria a aba de instalação de Stock ROM."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Seleção de Firmware
        fw_group = QGroupBox("Firmware")
        fw_layout = QHBoxLayout()
        self.fw_path_input = QLineEdit()
        self.fw_path_input.setPlaceholderText("Pasta de firmware ou arquivo .zip...")
        btn_browse_fw = QPushButton("Procurar...")
        btn_browse_fw.clicked.connect(self._browse_firmware)
        fw_layout.addWidget(self.fw_path_input)
        fw_layout.addWidget(btn_browse_fw)
        fw_group.setLayout(fw_layout)
        layout.addWidget(fw_group)
        
        # Tabela de Partições
        self.partition_table = QTableWidget(0, 2)
        self.partition_table.setHorizontalHeaderLabels(["Partição", "Status/Arquivo"])
        self.partition_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.partition_table)
        
        btn_flash_all = QPushButton("Flash ROM Completa")
        btn_flash_all.setEnabled(False) # Habilitar após carregar firmware
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
        """Cria a aba de controle de boot e modos."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grid_layout = QVBoxLayout()
        grid_layout.setSpacing(10)
        
        # Botões de Reboot
        reboot_group = QGroupBox("Opções de Reinicialização")
        rl = QVBoxLayout()
        
        btn_reboot_sys = QPushButton("Reiniciar no Sistema (Normal)")
        btn_reboot_sys.clicked.connect(lambda: self.view_model.reboot_device("auto", "normal"))
        
        btn_reboot_rec = QPushButton("Modo Recovery")
        btn_reboot_rec.clicked.connect(lambda: self.view_model.reboot_device("auto", "recovery"))
        
        btn_reboot_bl = QPushButton("Modo Fastboot (Bootloader)")
        btn_reboot_bl.clicked.connect(lambda: self.view_model.reboot_device("auto", "bootloader"))
        
        btn_reboot_fbd = QPushButton("Modo Fastbootd")
        btn_reboot_fbd.clicked.connect(lambda: self.view_model.reboot_device("auto", "fastbootd"))
        
        btn_reboot_dl = QPushButton("Download Mode (Samsung)")
        btn_reboot_dl.clicked.connect(lambda: self.view_model.reboot_device("auto", "download"))
        
        rl.addWidget(btn_reboot_sys)
        rl.addWidget(btn_reboot_rec)
        rl.addWidget(btn_reboot_bl)
        rl.addWidget(btn_reboot_fbd)
        rl.addWidget(btn_reboot_dl)
        reboot_group.setLayout(rl)
        grid_layout.addWidget(reboot_group)
        
        # Ferramentas Avançadas
        adv_group = QGroupBox("Avançado")
        al = QVBoxLayout()
        
        btn_fix_bootloop = QPushButton("Sair de Bootloop (Fastboot Continue)")
        btn_fix_bootloop.clicked.connect(lambda: self.view_model.reboot_device("auto", "continue"))
        
        btn_unlock_bl = QPushButton("Desbloquear Bootloader")
        btn_unlock_bl.setStyleSheet("color: #e74c3c; font-weight: bold;")
        btn_unlock_bl.clicked.connect(lambda: self.view_model.unlock_bootloader("auto"))
        
        al.addWidget(btn_fix_bootloop)
        al.addWidget(btn_unlock_bl)
        adv_group.setLayout(al)
        grid_layout.addWidget(adv_group)
        
        layout.addLayout(grid_layout)
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
        self.log_console.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas, monospace; padding: 5px;")
        layout.addWidget(self.log_console)
        
        return widget

    def _connect_signals(self) -> None:
        """Conecta os sinais do ViewModel aos slots da View."""
        self.view_model.flash_log.connect(self._append_log)
        self.view_model.flash_progress.connect(self._update_progress)
        self.view_model.flash_completed.connect(self._on_flash_completed)
        self.view_model.partition_list_updated.connect(self._update_partition_table)

    @Slot()
    def _browse_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem", "", "Imagens (*.img);;Todos os Arquivos (*)")
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
        
        # Aqui deve-se abrir um QDialog de confirmação (FlashConfirmDialog)
        # Por enquanto iniciamos diretamente:
        self.view_model.start_flash("auto", partition, image_path)

    @Slot()
    def _on_sideload_clicked(self) -> None:
        zip_path = self.zip_path_input.text()
        if not zip_path:
            self._append_log("Erro: Selecione um arquivo ZIP para o sideload.")
            return
        self.view_model.start_sideload("auto", zip_path)

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
