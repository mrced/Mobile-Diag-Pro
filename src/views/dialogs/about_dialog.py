"""
About Dialog for Mobile-Diag-Pro.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QFont, QDesktopServices

class AboutDialog(QDialog):
    """
    Diálogo "Sobre" com estilo macOS.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre o Mobile-Diag-Pro")
        self.setFixedSize(QSize(460, 360))
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon_label = QLabel("📱")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 64px;")
        layout.addWidget(icon_label)

        name_label = QLabel("Mobile-Diag-Pro")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        name_label.setFont(font)
        layout.addWidget(name_label)

        version_label = QLabel("Versão 1.0.0 (Release)")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        subtitle_label = QLabel("Suíte Profissional de Diagnóstico, Telemetria e Manutenção Android")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: gray;")
        layout.addWidget(subtitle_label)

        dev_label = QLabel("Desenvolvido com dedicação por <b>Onyalan S. Almeida</b>")
        dev_label.setTextFormat(Qt.TextFormat.RichText)
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(dev_label)

        btn_github = QPushButton("⭐ Ver no GitHub")
        btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/mrced/Mobile-Diag-Pro")))
        btn_github.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border-radius: 5px;
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        gh_layout = QHBoxLayout()
        gh_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gh_layout.addWidget(btn_github)
        layout.addLayout(gh_layout)

        tech_label = QLabel("Python · PySide6 · ADB Socket · PyQtGraph")
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_label.setStyleSheet("font-size: 10px; border: 1px solid gray; border-radius: 10px; padding: 2px 6px;")
        
        tech_layout = QHBoxLayout()
        tech_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_layout.addWidget(tech_label)
        layout.addLayout(tech_layout)

        license_label = QLabel("Distribuído sob licença de código aberto (Open Source)")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        license_label.setStyleSheet("font-size: 10px; color: gray;")
        layout.addWidget(license_label)

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
