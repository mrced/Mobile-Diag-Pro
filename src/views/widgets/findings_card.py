"""
Widget de Apresentação das Causas Raiz e Diagnóstico Técnico.
Apresenta visualmente o diagnóstico correlacionado, explicando exatamente os motivos
de lentidão, travamentos e congelamentos identificados no aparelho.
"""
from typing import List, Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.core.diagnostic_engine import Finding, DiagnosticReport


class FindingsCard(QFrame):
    """
    Card de diagnóstico de causas raiz gerado pelo motor com evidências técnicas reais.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame#FindingsCardRoot {
                background-color: rgba(26, 26, 44, 0.95);
                border: 1px solid rgba(10, 132, 255, 0.4);
                border-radius: 10px;
            }
        """)
        self.setObjectName("FindingsCardRoot")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 14)
        self.layout.setSpacing(10)

        # Cabeçalho do Card
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.icon_lbl = QLabel("🩺")
        self.icon_lbl.setFont(QFont("Segoe UI Emoji", 16))
        header_layout.addWidget(self.icon_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        self.title_lbl = QLabel("Diagnóstico Técnico de Causas Raiz (Identificadas no Aparelho)")
        self.title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #f5f5f7;")

        self.subtitle_lbl = QLabel("Correlação de 22 medições profundas via kernel, procfs, logcat e DropBox")
        self.subtitle_lbl.setStyleSheet("color: #8e8e93; font-size: 11px;")

        title_vbox.addWidget(self.title_lbl)
        title_vbox.addWidget(self.subtitle_lbl)
        header_layout.addLayout(title_vbox, 1)

        self.layout.addLayout(header_layout)

        # Área de Conteúdo dos Achados
        self.findings_container = QWidget()
        self.findings_container.setStyleSheet("background: transparent;")
        self.findings_layout = QVBoxLayout(self.findings_container)
        self.findings_layout.setContentsMargins(0, 4, 0, 0)
        self.findings_layout.setSpacing(8)

        self.layout.addWidget(self.findings_container)

    def display_report(self, report: DiagnosticReport):
        """Preenche o card com os achados do diagnóstico."""
        # Limpar achados anteriores
        while self.findings_layout.count():
            item = self.findings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not report.findings:
            no_issues = QLabel("✅ Nenhuma anomalia crítica foi identificada nas rotinas executadas.")
            no_issues.setStyleSheet("color: #30d158; font-weight: bold; font-size: 12px; padding: 6px;")
            self.findings_layout.addWidget(no_issues)
            self.show()
            return

        for finding in report.findings:
            item_frame = QFrame()
            
            # Cores por gravidade
            if finding.severity == "critical":
                bg = "rgba(255, 69, 58, 0.12)"
                border = "rgba(255, 69, 58, 0.35)"
                badge_bg = "#ff453a"
                badge_txt = "CRÍTICO"
            elif finding.severity == "warning":
                bg = "rgba(255, 159, 10, 0.10)"
                border = "rgba(255, 159, 10, 0.35)"
                badge_bg = "#ff9f0a"
                badge_txt = "ATENÇÃO"
            else:
                bg = "rgba(10, 132, 255, 0.08)"
                border = "rgba(10, 132, 255, 0.25)"
                badge_bg = "#0a84ff"
                badge_txt = "DESCARTADO"

            item_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg};
                    border: 1px solid {border};
                    border-radius: 6px;
                }}
            """)

            vbox = QVBoxLayout(item_frame)
            vbox.setContentsMargins(12, 10, 12, 10)
            vbox.setSpacing(6)

            # Linha de Título com Badge
            top_row = QHBoxLayout()
            top_row.setSpacing(8)

            badge = QLabel(badge_txt)
            badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            badge.setStyleSheet(f"""
                background-color: {badge_bg};
                color: #ffffff;
                border-radius: 4px;
                padding: 2px 6px;
            """)
            top_row.addWidget(badge)

            title = QLabel(finding.title)
            title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            title.setStyleSheet("color: #ffffff; border: none; background: transparent;")
            top_row.addWidget(title, 1)

            vbox.addLayout(top_row)

            # Evidência
            if finding.evidence:
                ev_lbl = QLabel(f"<b>Evidência medida:</b> {finding.evidence}")
                ev_lbl.setWordWrap(True)
                ev_lbl.setStyleSheet("color: #e5e5ea; font-size: 11px; border: none; background: transparent;")
                vbox.addWidget(ev_lbl)

            # Impacto no sintoma (Por que o celular trava/fica lento)
            if finding.impact:
                imp_lbl = QLabel(f"<b>Por que o aparelho trava/fica lento:</b> {finding.impact}")
                imp_lbl.setWordWrap(True)
                imp_lbl.setStyleSheet("color: #ffd60a; font-size: 11px; border: none; background: transparent;")
                vbox.addWidget(imp_lbl)

            # Ação recomendada
            if finding.action:
                act_lbl = QLabel(f"<b>Ação recomendada:</b> {finding.action}")
                act_lbl.setWordWrap(True)
                act_lbl.setStyleSheet("color: #64b5ff; font-size: 11px; border: none; background: transparent;")
                vbox.addWidget(act_lbl)

            self.findings_layout.addWidget(item_frame)

        self.show()
