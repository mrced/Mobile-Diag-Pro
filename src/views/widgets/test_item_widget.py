"""
Linha Compacta de Diagnóstico (TestItemWidget).
Apresenta o resultado técnico diretamente inline de forma limpa, moderna e compacta.
Elimina caixas expansíveis desnecessárias para leitura rápida e profissional em tela cheia.
"""
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Enum única e compartilhada com o motor (uma cópia local causava linhas presas em "Testando...")
from src.core.constants import TestStatus


class TestItemWidget(QFrame):
    """
    Linha individual de teste para a lista de diagnóstico.
    Exibe: Ícone + Nome do Teste | Métrica/Achado Técnico em Tempo Real | Badge de Status.
    """

    def __init__(
        self,
        test_id: str,
        name: str,
        description: str,
        category_icon: str = "⚙️",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.test_id = test_id
        self.name = name
        self.description = description
        self.category_icon = category_icon
        self.current_status = TestStatus.PENDING

        self._setup_ui()
        self.reset()

    def _setup_ui(self):
        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.06);
                border-color: rgba(10, 132, 255, 0.3);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)

        # 1. Ícone
        self.icon_label = QLabel(self.category_icon)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 13))
        self.icon_label.setFixedWidth(22)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.icon_label)

        # 2. Nome do Teste (Largura fixa para alinhamento uniforme em tabela)
        self.name_label = QLabel(self.name)
        self.name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #f5f5f7; border: none; background: transparent;")
        self.name_label.setFixedWidth(210)
        self.name_label.setToolTip(self.description)
        layout.addWidget(self.name_label)

        # Divisor sutil
        divider = QLabel("|")
        divider.setStyleSheet("color: rgba(255, 255, 255, 0.15); border: none; background: transparent;")
        layout.addWidget(divider)

        # 3. Leitura / Achado Técnico (Diretamente visível inline!)
        self.result_label = QLabel("Aguardando execução...")
        self.result_label.setFont(QFont("Segoe UI", 10))
        self.result_label.setStyleSheet("color: #98989d; border: none; background: transparent;")
        self.result_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.result_label, 1)

        # 4. Badge de Status (Pílula compacta)
        self.status_badge = QLabel("Aguardando")
        self.status_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setFixedHeight(22)
        self.status_badge.setMinimumWidth(85)
        layout.addWidget(self.status_badge)

    def set_status(
        self,
        status: TestStatus,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Atualiza o resultado técnico inline e a pílula de status.
        """
        self.current_status = status

        if status == TestStatus.PENDING:
            self.status_badge.setText("Aguardando")
            self.status_badge.setStyleSheet("""
                background-color: rgba(128, 128, 128, 0.15);
                color: #8e8e93;
                border-radius: 11px;
                padding: 0 8px;
                border: none;
            """)
            self.result_label.setText("Pronto para teste")
            self.result_label.setStyleSheet("color: #636366; border: none; background: transparent;")

        elif status == TestStatus.RUNNING:
            self.status_badge.setText("Testando...")
            self.status_badge.setStyleSheet("""
                background-color: rgba(10, 132, 255, 0.2);
                color: #0a84ff;
                border-radius: 11px;
                padding: 0 8px;
                border: 1px solid rgba(10, 132, 255, 0.4);
            """)
            self.result_label.setText("Analisando dados coletados do aparelho...")
            self.result_label.setStyleSheet("color: #0a84ff; font-style: italic; border: none; background: transparent;")

        elif status == TestStatus.PASSED:
            self.status_badge.setText("Aprovado ✓")
            self.status_badge.setStyleSheet("""
                background-color: rgba(48, 209, 88, 0.18);
                color: #30d158;
                border-radius: 11px;
                padding: 0 8px;
                border: none;
            """)
            self._render_result_text(message, details, "#e5e5ea")

        elif status == TestStatus.WARNING:
            self.status_badge.setText("Atenção ⚠️")
            self.status_badge.setStyleSheet("""
                background-color: rgba(255, 159, 10, 0.2);
                color: #ff9f0a;
                border-radius: 11px;
                padding: 0 8px;
                border: none;
            """)
            self._render_result_text(message, details, "#ffd60a")

        elif status == TestStatus.FAILED:
            self.status_badge.setText("Falha ✗")
            self.status_badge.setStyleSheet("""
                background-color: rgba(255, 69, 58, 0.2);
                color: #ff453a;
                border-radius: 11px;
                padding: 0 8px;
                border: none;
            """)
            self._render_result_text(message, details, "#ff453a")

        elif status == TestStatus.SKIPPED:
            self.status_badge.setText("Não medido")
            self.status_badge.setStyleSheet("""
                background-color: rgba(128, 128, 128, 0.12);
                color: #8e8e93;
                border-radius: 11px;
                padding: 0 8px;
                border: none;
            """)
            self._render_result_text(message or "Não foi possível medir neste aparelho", details, "#8e8e93")

        elif status == TestStatus.INFO:
            self.status_badge.setText("Info")
            self.status_badge.setStyleSheet("""
                background-color: rgba(10, 132, 255, 0.14);
                color: #64b5ff;
                border-radius: 11px;
                padding: 0 8px;
                border: none;
            """)
            self._render_result_text(message, details, "#c7d7ea")

    def _render_result_text(self, message: str, details: Optional[Dict[str, Any]], color: str):
        """Formata o texto de resultado inline e prepara o tooltip completo com todos os dados."""
        # Se temos detalhes em dicionário, montamos uma linha de métricas limpa
        display_text = message or ""
        tooltip_lines = [f"<b>{self.name}</b>", f"<i>{self.description}</i>", ""]

        if details and isinstance(details, dict):
            # Sintetizar métricas em formato legível: Chave: Valor • Chave: Valor
            parts = []
            for k, v in details.items():
                if isinstance(v, (dict, list)):
                    continue
                parts.append(f"{k}: <b>{v}</b>")
                tooltip_lines.append(f"• <b>{k}:</b> {v}")

            if parts and not display_text:
                display_text = " • ".join(parts[:4])
            elif parts:
                tooltip_lines.insert(2, f"<b>Achado:</b> {display_text}")

        if not display_text:
            display_text = "—"

        self.result_label.setText(display_text)
        self.result_label.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        self.setToolTip("<br>".join(tooltip_lines))

    def reset(self):
        """Restaura o item de teste para o estado inicial."""
        self.set_status(TestStatus.PENDING)

    def set_expanded(self, expand: bool = True):
        """Mantido para compatibilidade."""
        pass
