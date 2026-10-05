"""
Diálogo de Laudo Técnico e Causas Raiz.
Exibe em janela dedicada e rolável todas as conclusões técnicas, evidências e ações recomendadas,
sem espremer nem cobrir a tabela principal de testes.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.core.diagnostic_engine import DiagnosticReport


class FindingsDialog(QDialog):
    """
    Janela modal para exibição do Laudo Técnico completo de causas de lentidão e travamentos.
    """

    def __init__(self, report: DiagnosticReport, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.report = report
        self.setWindowTitle("Laudo Técnico — Análise de Causas de Travamento & Lentidão")
        self.resize(880, 680)
        self.setMinimumSize(750, 500)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1c1c1e;
                color: #f5f5f7;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        icon_lbl = QLabel("🩺")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 24))
        header_layout.addWidget(icon_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        title_lbl = QLabel("Laudo Técnico de Causas Raiz")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #f5f5f7;")

        sub_lbl = QLabel(
            f"Diagnóstico profundo baseado em 22 coletas de kernel, memória, processos e histórico do sistema • {self.report.device_serial}"
        )
        sub_lbl.setStyleSheet("color: #8e8e93; font-size: 12px;")

        title_vbox.addWidget(title_lbl)
        title_vbox.addWidget(sub_lbl)
        header_layout.addLayout(title_vbox, 1)

        # Score Pill
        score_pill = QLabel(f"Saúde: {self.report.overall_score}%")
        score_pill.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        score_color = "#30d158" if self.report.overall_score >= 80 else "#ff9f0a" if self.report.overall_score >= 50 else "#ff453a"
        score_pill.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 0.05);
            color: {score_color};
            border: 1px solid {score_color};
            border-radius: 12px;
            padding: 6px 14px;
        """)
        header_layout.addWidget(score_pill)

        layout.addLayout(header_layout)

        # 2. Área de Rolagem com os Achados
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 10, 0)
        c_layout.setSpacing(12)

        if not self.report.findings:
            no_issues = QLabel("✅ Nenhuma anomalia crítica foi identificada nas medições executadas.")
            no_issues.setStyleSheet("color: #30d158; font-weight: bold; font-size: 13px; padding: 12px;")
            c_layout.addWidget(no_issues)
        else:
            for f in self.report.findings:
                c_layout.addWidget(self._create_finding_widget(f))

        c_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # 3. Rodapé com Botões de Ação
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        summary_lbl = QLabel(self.report.summary)
        summary_lbl.setStyleSheet("color: #8e8e93; font-size: 11px;")
        summary_lbl.setWordWrap(True)
        footer_layout.addWidget(summary_lbl, 1)

        btn_optimize = QPushButton("⚡ Corrigir & Otimizar Agora (1-Clique)")
        btn_optimize.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_optimize.setStyleSheet("""
            QPushButton {
                background-color: #30d158;
                color: #000000;
                font-weight: 800;
                font-size: 13px;
                padding: 8px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #28b84c;
            }
        """)
        btn_optimize.clicked.connect(self._open_optimizer)
        footer_layout.addWidget(btn_optimize)

        btn_close = QPushButton("Fechar")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #f5f5f7;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 22px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        btn_close.clicked.connect(self.accept)
        footer_layout.addWidget(btn_close)

        layout.addLayout(footer_layout)

    def _open_optimizer(self):
        from src.views.dialogs.optimizer_dialog import OptimizerDialog
        dlg = OptimizerDialog(self.report.device_serial, self)
        dlg.exec()


    def _create_finding_widget(self, finding) -> QFrame:
        frame = QFrame()

        if finding.severity == "critical":
            bg = "rgba(255, 69, 58, 0.12)"
            border = "rgba(255, 69, 58, 0.4)"
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

        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)

        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(14, 12, 14, 12)
        vbox.setSpacing(8)

        # Título com Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        badge = QLabel(badge_txt)
        badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        badge.setStyleSheet(f"""
            background-color: {badge_bg};
            color: #ffffff;
            border-radius: 4px;
            padding: 2px 8px;
            border: none;
        """)
        top_row.addWidget(badge)

        title = QLabel(finding.title)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        title.setWordWrap(True)
        top_row.addWidget(title, 1)

        vbox.addLayout(top_row)

        # Evidência Real Medida
        if finding.evidence:
            ev_lbl = QLabel(f"<span style='color: #8e8e93;'>Evidência Medida:</span> <span style='color: #f5f5f7;'>{finding.evidence}</span>")
            ev_lbl.setWordWrap(True)
            ev_lbl.setFont(QFont("Segoe UI", 10))
            ev_lbl.setStyleSheet("border: none; background: transparent;")
            vbox.addWidget(ev_lbl)

        # Impacto no Sintoma (Por que o celular trava/fica lento/tela apaga)
        if finding.impact:
            imp_lbl = QLabel(f"<span style='color: #ff9f0a; font-weight: bold;'>Impacto nos Sintomas:</span> <span style='color: #ffd60a;'>{finding.impact}</span>")
            imp_lbl.setWordWrap(True)
            imp_lbl.setFont(QFont("Segoe UI", 10))
            imp_lbl.setStyleSheet("border: none; background: transparent;")
            vbox.addWidget(imp_lbl)

        # Ação Recomendada
        if finding.action:
            act_lbl = QLabel(f"<span style='color: #0a84ff; font-weight: bold;'>Ação Técnica Recomendada:</span> <span style='color: #64b5ff;'>{finding.action}</span>")
            act_lbl.setWordWrap(True)
            act_lbl.setFont(QFont("Segoe UI", 10))
            act_lbl.setStyleSheet("border: none; background: transparent;")
            vbox.addWidget(act_lbl)

        return frame
