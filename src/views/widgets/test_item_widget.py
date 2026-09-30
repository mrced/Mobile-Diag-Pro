import json
from enum import Enum
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QSizePolicy, QToolButton
)
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFont, QColor

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"

class TestItemWidget(QFrame):
    """
    Widget visual para um item de teste de diagnóstico individual.
    Exibe o nome do teste, descrição, status e detalhes expansíveis.
    """
    
    def __init__(self, test_id: str, name: str, description: str, category_icon: str = "⚙️", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.test_id = test_id
        self.name = name
        self.description = description
        self.category_icon = category_icon
        self.current_status = TestStatus.PENDING
        self._is_expanded = False
        
        self._setup_ui()
        self._apply_styles()
        self.reset()
        
    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)
        
        # Header (Sempre visível)
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(12)
        
        # Ícone
        self.icon_label = QLabel(self.category_icon)
        self.icon_label.setFont(QFont("Segoe UI", 16))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(32, 32)
        self.header_layout.addWidget(self.icon_label)
        
        # Textos (Nome e Descrição)
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(2)
        
        self.name_label = QLabel(self.name)
        font_name = self.name_label.font()
        font_name.setBold(True)
        font_name.setPointSize(11)
        self.name_label.setFont(font_name)
        
        self.desc_label = QLabel(self.description)
        self.desc_label.setWordWrap(True)
        font_desc = self.desc_label.font()
        font_desc.setPointSize(9)
        self.desc_label.setFont(font_desc)
        
        self.text_layout.addWidget(self.name_label)
        self.text_layout.addWidget(self.desc_label)
        self.header_layout.addLayout(self.text_layout)
        
        self.header_layout.addStretch()
        
        # Status Badge
        self.status_badge = QLabel()
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setContentsMargins(12, 4, 12, 4)
        font_badge = self.status_badge.font()
        font_badge.setBold(True)
        self.status_badge.setFont(font_badge)
        self.header_layout.addWidget(self.status_badge)
        
        # Botão expandir
        self.expand_btn = QToolButton()
        self.expand_btn.setText("▼")
        self.expand_btn.setFixedSize(24, 24)
        self.expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_btn.clicked.connect(self.toggle_details)
        self.header_layout.addWidget(self.expand_btn)
        
        self.main_layout.addWidget(self.header_widget)
        
        # Detalhes (Oculto por padrão)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(44, 0, 0, 0) # Identado
        
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.hide()
        
        self.raw_data_label = QLabel()
        self.raw_data_label.setWordWrap(True)
        self.raw_data_label.setTextFormat(Qt.TextFormat.PlainText)
        self.raw_data_label.setStyleSheet("font-family: monospace; background: rgba(128, 128, 128, 0.1); padding: 8px; border-radius: 4px;")
        self.raw_data_label.hide()
        
        self.details_layout.addWidget(self.message_label)
        self.details_layout.addWidget(self.raw_data_label)
        
        self.details_widget.hide()
        self.main_layout.addWidget(self.details_widget)
        
    def _apply_styles(self):
        self.setProperty("class", "test-item")
        self.setStyleSheet("""
            QFrame.test-item {
                background-color: transparent;
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 8px;
            }
            QFrame.test-item:hover {
                background-color: rgba(128, 128, 128, 0.05);
            }
            QToolButton {
                border: none;
                background: transparent;
                border-radius: 12px;
            }
            QToolButton:hover {
                background: rgba(128, 128, 128, 0.2);
            }
        """)

    def set_status(self, status: TestStatus, message: str = "", details: Optional[Dict[str, Any]] = None):
        """
        Atualiza o status, mensagem e detalhes do teste.
        """
        self.current_status = status
        
        # Atualizar badge
        badge_style = "border-radius: 12px; color: white; "
        badge_text = ""
        
        if status == TestStatus.PENDING:
            badge_text = "Aguardando"
            badge_style += "background-color: #6c757d; color: white;" # Cinza
        elif status == TestStatus.RUNNING:
            badge_text = "Executando..."
            badge_style += "background-color: #0d6efd; color: white;" # Azul
        elif status == TestStatus.PASSED:
            badge_text = "Aprovado ✓"
            badge_style += "background-color: #198754; color: white;" # Verde
        elif status == TestStatus.WARNING:
            badge_text = "Atenção ⚠️"
            badge_style += "background-color: #fd7e14; color: white;" # Laranja
        elif status == TestStatus.FAILED:
            badge_text = "Falhou ✗"
            badge_style += "background-color: #dc3545; color: white;" # Vermelho
        elif status == TestStatus.SKIPPED:
            badge_text = "Ignorado"
            badge_style += "background-color: #adb5bd; color: #212529;" # Cinza claro
            
        self.status_badge.setText(badge_text)
        self.status_badge.setStyleSheet(badge_style)
        
        # Atualizar detalhes
        if message:
            self.message_label.setText(message)
            self.message_label.show()
        else:
            self.message_label.hide()
            
        if details:
            try:
                formatted_data = json.dumps(details, indent=2, ensure_ascii=False)
                self.raw_data_label.setText(formatted_data)
                self.raw_data_label.show()
            except Exception:
                self.raw_data_label.setText(str(details))
                self.raw_data_label.show()
        else:
            self.raw_data_label.hide()
            
        # Se houver erro/aviso e não estiver expandido, expandir automaticamente
        if status in [TestStatus.FAILED, TestStatus.WARNING] and not self._is_expanded:
            self.toggle_details()

    def reset(self):
        """
        Restaura o widget para o estado inicial.
        """
        self.set_status(TestStatus.PENDING)
        if self._is_expanded:
            self.toggle_details()

    def toggle_details(self):
        """
        Alterna a visibilidade dos detalhes do teste.
        """
        self._is_expanded = not self._is_expanded
        self.details_widget.setVisible(self._is_expanded)
        self.expand_btn.setText("▲" if self._is_expanded else "▼")
