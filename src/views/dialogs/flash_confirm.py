from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

class FlashConfirmDialog(QDialog):
    """
    Diálogo de confirmação para operações de Flash (estilo macOS).
    Exige que o usuário confirme explicitamente os riscos e pré-requisitos
    antes de prosseguir com a escrita no dispositivo.
    """
    
    def __init__(self, serial: str, partition: str, image_path: str, parent=None):
        """
        Inicializa o diálogo.
        
        Args:
            serial: Número de série do dispositivo alvo.
            partition: Partição que será modificada.
            image_path: Caminho da imagem que será aplicada.
            parent: Widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Atenção - Confirmação de Flash")
        self.setFixedSize(500, 350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: #F5F5F7; color: #1D1D1F; border-radius: 10px;")
        
        self.serial = serial
        self.partition = partition
        self.image_path = image_path
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Configura a interface do usuário."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Título
        title_label = QLabel("Aviso de Segurança")
        title_font = QFont("San Francisco", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FF3B30;")
        layout.addWidget(title_label)
        
        # Informações da operação
        info_text = (
            f"Você está prestes a realizar uma modificação no firmware do dispositivo.\n\n"
            f"<b>Dispositivo:</b> {self.serial}\n"
            f"<b>Partição Alvo:</b> {self.partition}\n"
            f"<b>Arquivo:</b> {self.image_path}"
        )
        info_label = QLabel(info_text)
        info_label.setFont(QFont("San Francisco", 11))
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)
        
        # Linha separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #D1D1D6;")
        layout.addWidget(line)
        
        # Checkboxes de confirmação
        self.check_risks = QCheckBox("Entendo os riscos de modificação de firmware")
        self.check_battery = QCheckBox("Bateria do dispositivo acima de 40%")
        self.check_backup = QCheckBox("Backup dos dados essenciais realizado")
        
        checkbox_style = """
            QCheckBox { font-family: 'San Francisco'; font-size: 11pt; margin-top: 4px; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #C7C7CC; background-color: #FFFFFF; }
            QCheckBox::indicator:checked { background-color: #007AFF; border: 1px solid #007AFF; }
        """
        for cb in (self.check_risks, self.check_battery, self.check_backup):
            cb.setStyleSheet(checkbox_style)
            layout.addWidget(cb)
            
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Botões
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_confirm = QPushButton("Confirmar e Flashear")
        
        btn_base_style = """
            QPushButton { padding: 8px 16px; border-radius: 6px; font-family: 'San Francisco'; font-size: 11pt; font-weight: bold; }
        """
        self.btn_cancel.setStyleSheet(btn_base_style + """
            QPushButton { background-color: #E5E5EA; color: #007AFF; border: none; }
            QPushButton:hover { background-color: #D1D1D6; }
        """)
        
        self.btn_confirm.setStyleSheet(btn_base_style + """
            QPushButton { background-color: #FF3B30; color: white; border: none; }
            QPushButton:hover { background-color: #FF453A; }
            QPushButton:disabled { background-color: #FFB3B0; color: #FFFFFF; }
        """)
        self.btn_confirm.setEnabled(False)
        
        btn_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        """Conecta os sinais aos slots."""
        self.check_risks.toggled.connect(self._validate_checks)
        self.check_battery.toggled.connect(self._validate_checks)
        self.check_backup.toggled.connect(self._validate_checks)
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_confirm.clicked.connect(self.accept)

    def _validate_checks(self):
        """Valida se todas as checkboxes estão marcadas para ativar o botão de confirmar."""
        all_checked = (
            self.check_risks.isChecked() and
            self.check_battery.isChecked() and
            self.check_backup.isChecked()
        )
        self.btn_confirm.setEnabled(all_checked)
