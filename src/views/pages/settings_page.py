"""
Settings Page for Mobile-Diag-Pro.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
                               QRadioButton, QCheckBox, QLineEdit, QFileDialog, QGroupBox, QButtonGroup, QComboBox)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from src.viewmodels.settings_vm import SettingsViewModel
from src.views.dialogs.about_dialog import AboutDialog

class SettingsPage(QWidget):
    """
    Página de configurações da aplicação.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view_model = SettingsViewModel()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Configurações")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        subtitle = QLabel("Preferências da Aplicação, Temas e Ferramentas de Sistema")
        subtitle.setStyleSheet("color: gray;")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # 1. Aparência
        group_appearance = QGroupBox("Aparência")
        appearance_layout = QVBoxLayout(group_appearance)
        self.radio_dark = QRadioButton("Modo Escuro (Dark)")
        self.radio_light = QRadioButton("Modo Claro (Light)")
        self.radio_dark.setChecked(True)
        self.theme_group = QButtonGroup(self)
        self.theme_group.addButton(self.radio_dark)
        self.theme_group.addButton(self.radio_light)
        appearance_layout.addWidget(self.radio_dark)
        appearance_layout.addWidget(self.radio_light)
        
        self.radio_dark.toggled.connect(lambda c: self.view_model.theme_changed.emit("dark") if c else None)
        self.radio_light.toggled.connect(lambda c: self.view_model.theme_changed.emit("light") if c else None)
        main_layout.addWidget(group_appearance)

        # 2. Diagnóstico & Telemetria
        group_diag = QGroupBox("Diagnóstico & Telemetria")
        diag_layout = QVBoxLayout(group_diag)
        
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Intervalo padrão de atualização:"))
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["500ms", "1000ms", "2000ms"])
        combo_layout.addWidget(self.combo_interval)
        combo_layout.addStretch()
        diag_layout.addLayout(combo_layout)

        self.check_auto_check = QCheckBox("Executar checagem automática ao conectar dispositivo")
        diag_layout.addWidget(self.check_auto_check)
        main_layout.addWidget(group_diag)

        # 3. Android Platform Tools
        group_adb = QGroupBox("Android Platform Tools (ADB & Fastboot)")
        adb_layout = QVBoxLayout(group_adb)
        
        path_layout = QHBoxLayout()
        self.input_adb_path = QLineEdit()
        self.input_adb_path.setPlaceholderText("Caminho para o adb...")
        btn_browse = QPushButton("Procurar...")
        btn_auto = QPushButton("Auto-Detectar")
        path_layout.addWidget(self.input_adb_path)
        path_layout.addWidget(btn_browse)
        path_layout.addWidget(btn_auto)
        adb_layout.addLayout(path_layout)
        
        self.btn_test_adb = QPushButton("Testar Conexão ADB")
        self.label_adb_status = QLabel("")
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.btn_test_adb)
        status_layout.addWidget(self.label_adb_status)
        status_layout.addStretch()
        adb_layout.addLayout(status_layout)
        
        btn_auto.clicked.connect(self._auto_detect_adb)
        self.btn_test_adb.clicked.connect(self._test_adb)
        main_layout.addWidget(group_adb)

        # 4. Diretório Padrão de Backups e Relatórios
        group_dir = QGroupBox("Diretório Padrão de Backups e Relatórios")
        dir_layout = QHBoxLayout(group_dir)
        self.input_backup_dir = QLineEdit()
        btn_browse_dir = QPushButton("Selecionar Pasta")
        btn_browse_dir.clicked.connect(self._browse_backup_dir)
        dir_layout.addWidget(self.input_backup_dir)
        dir_layout.addWidget(btn_browse_dir)
        main_layout.addWidget(group_dir)

        # 5. Sobre o Desenvolvedor & Sistema
        group_about = QGroupBox("Sobre o Desenvolvedor & Sistema")
        about_layout = QHBoxLayout(group_about)
        btn_about = QPushButton("Sobre o Mobile-Diag-Pro...")
        btn_repo = QPushButton("Abrir Repositório no GitHub")
        
        btn_about.clicked.connect(self._show_about)
        btn_repo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/mrced/Mobile-Diag-Pro")))
        
        about_layout.addWidget(btn_about)
        about_layout.addWidget(btn_repo)
        about_layout.addStretch()
        main_layout.addWidget(group_about)

        main_layout.addStretch()

        # Bottom action bar
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        btn_restore = QPushButton("Restaurar Padrões")
        btn_save = QPushButton("Salvar Preferências")
        btn_save.setStyleSheet("background-color: #007bff; color: white;")
        
        btn_restore.clicked.connect(self.view_model.reset_to_defaults)
        btn_save.clicked.connect(self._save_settings)
        
        action_layout.addWidget(btn_restore)
        action_layout.addWidget(btn_save)
        main_layout.addLayout(action_layout)

    def _auto_detect_adb(self):
        status = self.view_model.detect_platform_tools()
        self.label_adb_status.setText(status)

    def _test_adb(self):
        status = self.view_model.detect_platform_tools()
        self.label_adb_status.setText(status)
        if "Detectado" in status:
            self.label_adb_status.setStyleSheet("color: green;")
        else:
            self.label_adb_status.setStyleSheet("color: red;")

    def _browse_backup_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecione o diretório")
        if directory:
            self.input_backup_dir.setText(directory)

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _save_settings(self):
        settings = {
            "theme": "dark" if self.radio_dark.isChecked() else "light",
            "interval": self.combo_interval.currentText(),
            "auto_check": self.check_auto_check.isChecked(),
            "adb_path": self.input_adb_path.text(),
            "backup_dir": self.input_backup_dir.text()
        }
        self.view_model.save_settings(settings)
