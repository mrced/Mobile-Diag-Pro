"""
Página de Backup e Restauração com estilo macOS.
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTabWidget, QCheckBox, QPushButton, QLineEdit,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from src.viewmodels.backup_vm import BackupViewModel

class BackupPage(QWidget):
    """
    Página principal de Backup e Restauração (Estilo macOS).
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        """Inicializa a página de backup."""
        super().__init__(parent)
        self.vm = BackupViewModel(self)
        self._serial: str = ""
        self._default_backup_dir = os.path.join(os.path.expanduser("~"), "Documents", "Mobile-Diag-Pro", "Backups")
        os.makedirs(self._default_backup_dir, exist_ok=True)
        
        self._setup_ui()
        self._connect_signals()
        self.vm.refresh_backup_list(self._default_backup_dir)

    def _setup_ui(self) -> None:
        """Configura a interface gráfica da página."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Backup & Restauração")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2C3E50;")
        subtitle = QLabel("Cópia de Segurança Completa, Aplicativos e Mídias")
        subtitle.setStyleSheet("font-size: 14px; color: #7F8C8D; margin-bottom: 10px;")
        
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #D4D4D5; border-radius: 6px; background: white; }
            QTabBar::tab { background: #F5F5F7; border: 1px solid #D4D4D5; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
            QTabBar::tab:selected { background: white; border-bottom-color: white; font-weight: bold; }
        """)

        self._setup_create_backup_tab()
        self._setup_restore_tab()
        self._setup_history_tab()

        main_layout.addWidget(self.tabs)

        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: #34495E; font-size: 12px;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; background: #ECF0F1; border-radius: 3px; }
            QProgressBar::chunk { background: #3498DB; border-radius: 3px; }
        """)
        
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.progress_bar)

    def _setup_create_backup_tab(self) -> None:
        """Configura a aba de criação de backup."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        options_group = QGroupBox("O que você deseja fazer backup?")
        options_layout = QVBoxLayout(options_group)
        
        self.chk_full = QCheckBox("Sistema & Dados de Apps (Full)")
        self.chk_full.setChecked(True)
        self.chk_apks = QCheckBox("Arquivos APKs instalados")
        self.chk_photos = QCheckBox("Fotos & Mídias (/sdcard/DCIM)")
        self.chk_docs = QCheckBox("Documentos & Downloads")
        
        options_layout.addWidget(self.chk_full)
        options_layout.addWidget(self.chk_apks)
        options_layout.addWidget(self.chk_photos)
        options_layout.addWidget(self.chk_docs)
        
        layout.addWidget(options_group)

        dest_layout = QHBoxLayout()
        self.dest_input = QLineEdit(self._default_backup_dir)
        self.dest_input.setReadOnly(True)
        btn_browse_dest = QPushButton("Procurar...")
        btn_browse_dest.clicked.connect(self._browse_dest_folder)
        
        dest_widget = QWidget()
        dest_widget.setLayout(dest_layout)
        dest_layout.setContentsMargins(0, 0, 0, 0)
        dest_layout.addWidget(QLabel("Pasta de Destino:"))
        dest_layout.addWidget(self.dest_input)
        dest_layout.addWidget(btn_browse_dest)
        
        layout.addWidget(dest_widget)
        
        warning = QLabel("⚠️ Aviso: A confirmação de backup pode requerer desbloqueio na tela do celular.")
        warning.setStyleSheet("color: #D35400; font-weight: bold;")
        layout.addWidget(warning)

        self.btn_start_backup = QPushButton("Iniciar Backup")
        self.btn_start_backup.setStyleSheet("""
            QPushButton { background-color: #007AFF; color: white; border-radius: 6px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:disabled { background-color: #A0C4FF; }
        """)
        self.btn_start_backup.clicked.connect(self._start_backup)
        layout.addWidget(self.btn_start_backup, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        self.tabs.addTab(tab, "💾 Criar Backup")

    def _setup_restore_tab(self) -> None:
        """Configura a aba de restauração."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.file_input.setPlaceholderText("Selecione um arquivo de backup (.ab)...")
        btn_browse_file = QPushButton("Selecionar Arquivo")
        btn_browse_file.clicked.connect(self._browse_restore_file)
        
        file_widget = QWidget()
        file_widget.setLayout(file_layout)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.addWidget(QLabel("Arquivo de Backup:"))
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(btn_browse_file)
        
        layout.addWidget(file_widget)
        
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet("color: #7F8C8D;")
        layout.addWidget(self.file_info_label)

        warning = QLabel("⚠️ Aviso: A confirmação de restauração deve ser aceita na tela do aparelho.")
        warning.setStyleSheet("color: #D35400; font-weight: bold;")
        layout.addWidget(warning)

        self.btn_start_restore = QPushButton("Iniciar Restauração no Aparelho")
        self.btn_start_restore.setStyleSheet("""
            QPushButton { background-color: #2ECC71; color: white; border-radius: 6px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #27AE60; }
            QPushButton:disabled { background-color: #A9DFBF; }
        """)
        self.btn_start_restore.clicked.connect(self._start_restore)
        layout.addWidget(self.btn_start_restore, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        self.tabs.addTab(tab, "📥 Restaurar")

    def _setup_history_tab(self) -> None:
        """Configura a aba de histórico de backups."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["Data", "Arquivo", "Tamanho (MB)", "Caminho"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.history_table)

        btn_layout = QHBoxLayout()
        btn_open_folder = QPushButton("Abrir Pasta de Backups")
        btn_open_folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self._default_backup_dir)))
        
        btn_refresh = QPushButton("Atualizar Lista")
        btn_refresh.clicked.connect(lambda: self.vm.refresh_backup_list(self._default_backup_dir))
        
        btn_layout.addWidget(btn_open_folder)
        btn_layout.addWidget(btn_refresh)
        
        layout.addLayout(btn_layout)
        self.tabs.addTab(tab, "📂 Histórico de Backups")

    def _connect_signals(self) -> None:
        """Conecta os sinais do ViewModel."""
        self.vm.backup_started.connect(self._on_operation_started)
        self.vm.backup_progress.connect(self._on_progress)
        self.vm.backup_completed.connect(self._on_operation_completed)
        
        self.vm.restore_started.connect(self._on_operation_started)
        self.vm.restore_completed.connect(self._on_operation_completed)
        
        self.vm.backup_list_updated.connect(self._update_history_table)

    def set_device(self, serial: str) -> None:
        """
        Vincula a página ao dispositivo ativo.
        
        Args:
            serial: Número de série do dispositivo.
        """
        self._serial = serial
        self.vm.set_device(serial)
        self.status_label.setText(f"Dispositivo selecionado: {serial}" if serial else "Nenhum dispositivo selecionado.")

    def _browse_dest_folder(self) -> None:
        """Abre diálogo para selecionar pasta de destino."""
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Destino", self.dest_input.text())
        if folder:
            self.dest_input.setText(folder)

    def _browse_restore_file(self) -> None:
        """Abre diálogo para selecionar arquivo de restauração."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo de Backup", self._default_backup_dir, "Arquivos de Backup (*.ab);;Todos os Arquivos (*)")
        if file_path:
            self.file_input.setText(file_path)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.file_info_label.setText(f"Tamanho: {size_mb:.2f} MB")

    def _start_backup(self) -> None:
        """Inicia o processo de backup com base nas opções selecionadas."""
        if not self._serial:
            QMessageBox.warning(self, "Aviso", "Nenhum dispositivo conectado!")
            return
            
        dest = self.dest_input.text()
        
        if self.chk_full.isChecked():
            self.vm.start_full_backup(dest)
            
        folders_to_pull = []
        if self.chk_photos.isChecked():
            folders_to_pull.extend(["/sdcard/DCIM", "/sdcard/Pictures"])
        if self.chk_docs.isChecked():
            folders_to_pull.extend(["/sdcard/Documents", "/sdcard/Download"])
            
        if folders_to_pull:
            self.vm.start_media_backup(dest, folders_to_pull)

    def _start_restore(self) -> None:
        """Inicia o processo de restauração."""
        if not self._serial:
            QMessageBox.warning(self, "Aviso", "Nenhum dispositivo conectado!")
            return
            
        file_path = self.file_input.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo de backup válido!")
            return
            
        self.vm.start_restore(file_path)

    def _on_operation_started(self, msg: str) -> None:
        """Callback executado ao iniciar operação."""
        self.status_label.setText(msg)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.btn_start_backup.setEnabled(False)
        self.btn_start_restore.setEnabled(False)

    def _on_progress(self, msg: str) -> None:
        """Atualiza a mensagem de progresso."""
        self.status_label.setText(msg)

    def _on_operation_completed(self, success: bool, msg: str) -> None:
        """Callback executado ao concluir operação."""
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        self.status_label.setText(msg)
        self.btn_start_backup.setEnabled(True)
        self.btn_start_restore.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Sucesso", msg)
            self.vm.refresh_backup_list(self._default_backup_dir)
        else:
            QMessageBox.critical(self, "Erro", msg)

    def _update_history_table(self, backups: list) -> None:
        """Atualiza a tabela de histórico de backups."""
        self.history_table.setRowCount(0)
        for i, bk in enumerate(backups):
            self.history_table.insertRow(i)
            self.history_table.setItem(i, 0, QTableWidgetItem(bk["modified_date"]))
            self.history_table.setItem(i, 1, QTableWidgetItem(bk["filename"]))
            self.history_table.setItem(i, 2, QTableWidgetItem(f"{bk['size_mb']:.2f} MB"))
            self.history_table.setItem(i, 3, QTableWidgetItem(bk["full_path"]))
