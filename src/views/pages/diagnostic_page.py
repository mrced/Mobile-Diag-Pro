"""
Página de Diagnóstico Avançado.
Interface limpa, compacta e orientada a inspeção técnica de hardware e sistema Android.
Com painel de causas raiz e correlação de evidências reais coletadas via ADB/kernel.
"""
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QProgressBar, QComboBox,
    QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

from src.core.constants import DeviceMode, TestStatus
from src.viewmodels.diagnostic_vm import DiagnosticViewModel, TestResult, DiagnosticReport
from src.views.widgets.test_item_widget import TestItemWidget
from src.views.widgets.action_guide_card import ActionGuideCard
from src.views.dialogs.findings_dialog import FindingsDialog


class DiagnosticPage(QWidget):
    """
    Página de Diagnóstico Avançado com layout de tabela de inspeção e painel de causas raiz.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.view_model = DiagnosticViewModel(self)
        self.test_widgets: Dict[str, TestItemWidget] = {}
        self.test_categories: Dict[str, str] = {}
        self.current_serial: str = ""
        
        self._setup_ui()
        self._connect_signals()
        self._populate_tests()
        
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setSpacing(10)
        
        # --- 1. Header Compacto com Métricas de Resumo ---
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(16)
        
        # Título e Subtítulo
        self.title_layout = QVBoxLayout()
        self.title_layout.setSpacing(2)
        
        self.title_label = QLabel("Diagnóstico Técnico de Hardware & Sistema")
        self.title_label.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #f5f5f7;")
        
        self.subtitle_label = QLabel("Medições reais de hardware, kernel, memória RAM, CPU, disco e análise de causas de lentidão")
        self.subtitle_label.setStyleSheet("color: #98989d; font-size: 12px;")
        
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addWidget(self.subtitle_label)
        self.header_layout.addLayout(self.title_layout)
        
        self.header_layout.addStretch()
        
        # Badges de Resumo
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(6)
        
        self.score_label = QLabel("Saúde: 100%")
        self.score_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.score_label.setStyleSheet("color: #30d158; padding: 4px 8px;")
        
        self.lbl_passed = self._create_badge("✓ 0 Aprovados", "#30d158")
        self.lbl_warning = self._create_badge("⚠️ 0 Atenção", "#ff9f0a")
        self.lbl_failed = self._create_badge("✗ 0 Falhas", "#ff453a")
        self.lbl_info = self._create_badge("ℹ️ 0 Info", "#64b5ff")
        self.lbl_total = self._create_badge("Total: 0", "#8e8e93")
        
        self.stats_layout.addWidget(self.score_label)
        self.stats_layout.addWidget(self.lbl_passed)
        self.stats_layout.addWidget(self.lbl_warning)
        self.stats_layout.addWidget(self.lbl_failed)
        self.stats_layout.addWidget(self.lbl_info)
        self.stats_layout.addWidget(self.lbl_total)
        
        self.header_layout.addLayout(self.stats_layout)
        self.main_layout.addLayout(self.header_layout)
        
        # --- 2. Guia de Ações (Aparece SOMENTE se o aparelho precisar de intervenção) ---
        self.action_guide = ActionGuideCard(self)
        self.action_guide.hide()
        self.main_layout.addWidget(self.action_guide)
        
        # --- 3. Barra de Ferramentas Unificada (Single-Row Toolbar) ---
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(10, 6, 10, 6)
        toolbar_layout.setSpacing(10)
        
        self.btn_run_all = QPushButton("▶ Iniciar Diagnóstico Completo")
        self.btn_run_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run_all.setStyleSheet("""
            QPushButton {
                background-color: #0a84ff;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 6px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0071e3;
            }
            QPushButton:disabled {
                background-color: rgba(10, 132, 255, 0.3);
                color: #8e8e93;
            }
        """)
        toolbar_layout.addWidget(self.btn_run_all)
        
        self.btn_stop = QPushButton("⏹ Parar")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #ff453a;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 6px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:disabled {
                background-color: rgba(255, 69, 58, 0.2);
                color: #636366;
            }
        """)
        toolbar_layout.addWidget(self.btn_stop)
        
        self.btn_optimize = QPushButton("⚡ Otimizar Aparelho (1-Clique)")
        self.btn_optimize.setEnabled(False)
        self.btn_optimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_optimize.setStyleSheet("""
            QPushButton {
                background-color: #30d158;
                color: #000000;
                font-weight: 800;
                font-size: 13px;
                padding: 6px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #28b84c;
            }
            QPushButton:disabled {
                background-color: rgba(48, 209, 88, 0.25);
                color: #636366;
            }
        """)
        self.btn_optimize.clicked.connect(self._open_optimizer_dialog)
        toolbar_layout.addWidget(self.btn_optimize)

        # Divisor
        div = QLabel("|")
        div.setStyleSheet("color: rgba(255, 255, 255, 0.2); border: none;")
        toolbar_layout.addWidget(div)
        
        # Filtro de Categoria
        toolbar_layout.addWidget(QLabel("Categoria:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Todas as Categorias", 
            "Memória RAM & Swap", 
            "Processador (CPU)", 
            "Armazenamento & Disco", 
            "Bateria & Energia", 
            "Térmico", 
            "Tela & Display", 
            "Sensores", 
            "Rede & Wi-Fi", 
            "Sistema & Segurança", 
            "Aplicativos", 
            "Processos & Falhas"
        ])
        self.filter_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                background-color: rgba(0, 0, 0, 0.2);
                color: #f5f5f7;
                font-size: 12px;
                min-width: 150px;
            }
        """)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self.filter_combo)
        
        # Campo de Busca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filtrar teste...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                background-color: rgba(0, 0, 0, 0.2);
                color: #f5f5f7;
                font-size: 12px;
                min-width: 130px;
            }
        """)
        self.search_input.textChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self.search_input)
        
        toolbar_layout.addStretch()
        
        self.btn_export = QPushButton("💾 Exportar Relatório Técnico")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f5f5f7;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 14px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        toolbar_layout.addWidget(self.btn_export)
        
        self.main_layout.addWidget(toolbar_frame)
        
        # --- 4. Banner Compacto de Laudo Técnico (Apenas 40px de altura, não ocupa a tela!) ---
        self.findings_banner = QFrame()
        self.findings_banner.setFixedHeight(40)
        self.findings_banner.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 69, 58, 0.15);
                border: 1px solid rgba(255, 69, 58, 0.4);
                border-radius: 8px;
            }
        """)
        banner_layout = QHBoxLayout(self.findings_banner)
        banner_layout.setContentsMargins(14, 0, 14, 0)
        banner_layout.setSpacing(10)

        self.banner_icon = QLabel("🩺")
        self.banner_icon.setFont(QFont("Segoe UI Emoji", 13))
        self.banner_icon.setStyleSheet("border: none; background: transparent;")
        banner_layout.addWidget(self.banner_icon)

        self.banner_text = QLabel("Laudo de Causas Raiz: Anomalias identificadas no aparelho")
        self.banner_text.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.banner_text.setStyleSheet("color: #f5f5f7; border: none; background: transparent;")
        banner_layout.addWidget(self.banner_text, 1)

        self.btn_view_findings = QPushButton("🔍 Abrir Laudo Técnico Completo")
        self.btn_view_findings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_view_findings.setStyleSheet("""
            QPushButton {
                background-color: #0a84ff;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                padding: 5px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0071e3;
            }
        """)
        self.btn_view_findings.clicked.connect(self._open_findings_dialog)
        banner_layout.addWidget(self.btn_view_findings)

        self.btn_banner_optimize = QPushButton("⚡ Corrigir & Otimizar Agora")
        self.btn_banner_optimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_banner_optimize.setStyleSheet("""
            QPushButton {
                background-color: #30d158;
                color: #000000;
                font-weight: 800;
                font-size: 11px;
                padding: 5px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #28b84c;
            }
        """)
        self.btn_banner_optimize.clicked.connect(self._open_optimizer_dialog)
        banner_layout.addWidget(self.btn_banner_optimize)

        self.findings_banner.hide()
        self.main_layout.addWidget(self.findings_banner)
        
        # --- 5. Cabeçalho de Colunas da Tabela de Testes ---
        cols_frame = QFrame()
        cols_frame.setFixedHeight(24)
        cols_frame.setStyleSheet("background: transparent; border: none;")
        cols_layout = QHBoxLayout(cols_frame)
        cols_layout.setContentsMargins(14, 0, 14, 0)
        cols_layout.setSpacing(12)
        
        lbl_col_name = QLabel("TESTE / COMPONENTE")
        lbl_col_name.setStyleSheet("color: #8e8e93; font-size: 11px; font-weight: bold; border: none;")
        lbl_col_name.setFixedWidth(246)
        
        lbl_col_reading = QLabel("MEDIÇÃO REAL & CRITÉRIO TÉCNICO")
        lbl_col_reading.setStyleSheet("color: #8e8e93; font-size: 11px; font-weight: bold; border: none;")
        
        lbl_col_status = QLabel("STATUS")
        lbl_col_status.setStyleSheet("color: #8e8e93; font-size: 11px; font-weight: bold; border: none;")
        lbl_col_status.setFixedWidth(85)
        lbl_col_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        cols_layout.addWidget(lbl_col_name)
        cols_layout.addWidget(lbl_col_reading, 1)
        cols_layout.addWidget(lbl_col_status)
        self.main_layout.addWidget(cols_frame)
        
        # --- 6. Lista de Testes com Rolagem Suave ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")
        
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.list_widget)
        self.main_layout.addWidget(self.scroll_area, 1)
        
        # --- 7. Barra de Progresso ---
        self.progress_layout = QHBoxLayout()
        self.progress_layout.setSpacing(12)
        
        self.progress_label = QLabel("Pronto para iniciar análise técnica")
        self.progress_label.setStyleSheet("color: #98989d; font-size: 12px; min-width: 250px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #0a84ff;
                border-radius: 5px;
            }
        """)
        
        self.progress_layout.addWidget(self.progress_label)
        self.progress_layout.addWidget(self.progress_bar, 1)
        self.main_layout.addLayout(self.progress_layout)

    def _create_badge(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.05); color: {color}; padding: 4px 10px; border-radius: 8px; font-weight: bold; font-size: 12px; border: 1px solid rgba(255, 255, 255, 0.08);")
        return lbl

    def _connect_signals(self):
        self.btn_run_all.clicked.connect(self._on_run_all_clicked)
        self.btn_stop.clicked.connect(self.view_model.stop_diagnostic)
        self.btn_export.clicked.connect(self._on_export_clicked)
        
        self.view_model.diagnostic_started.connect(self._on_diagnostic_started)
        self.view_model.collection_phase.connect(self._on_collection_phase)
        self.view_model.test_progress.connect(self._on_test_progress)
        self.view_model.test_completed.connect(self._on_test_completed)
        self.view_model.diagnostic_finished.connect(self._on_diagnostic_finished)
        self.view_model.error_occurred.connect(self._on_error)
        self.view_model.stats_updated.connect(self._update_stats)

    def _populate_tests(self):
        """Preenche a lista com todos os testes reais do motor."""
        from src.core.diagnostic_engine import DiagnosticEngine
        
        category_icons = {
            "memory": "⚡",
            "cpu": "🧠",
            "storage": "💾",
            "battery": "🔋",
            "thermal": "🌡️",
            "display": "📱",
            "sensors": "🧭",
            "network": "📶",
            "system": "🛡️",
            "apps": "📦",
            "processes": "⚙️",
        }
        
        # Limpar widgets anteriores se houver
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.test_widgets.clear()
        self.test_categories.clear()
        self.view_model.available_tests.clear()
        
        engine = DiagnosticEngine()
        available_tests = engine.get_available_tests()
        
        for t in available_tests:
            tid = t["id"]
            name = t["name"]
            desc = t.get("desc", "")
            cat = t.get("category", "system")
            icon = category_icons.get(cat, "🔬")
            
            widget = TestItemWidget(tid, name, desc, icon)
            self.list_layout.addWidget(widget)
            self.test_widgets[tid] = widget
            self.test_categories[tid] = cat
            self.view_model.available_tests.append(tid)

    def _on_filter_changed(self):
        cat_filter = self.filter_combo.currentText()
        cat_map = {
            "Memória RAM & Swap": "memory",
            "Processador (CPU)": "cpu",
            "Armazenamento & Disco": "storage",
            "Bateria & Energia": "battery",
            "Térmico": "thermal",
            "Tela & Display": "display",
            "Sensores": "sensors",
            "Rede & Wi-Fi": "network",
            "Sistema & Segurança": "system",
            "Aplicativos": "apps",
            "Processos & Falhas": "processes",
        }
        target_cat = cat_map.get(cat_filter, None)
        query = self.search_input.text().strip().lower()

        for tid, widget in self.test_widgets.items():
            cat = self.test_categories.get(tid, "")
            matches_cat = True
            if target_cat:
                matches_cat = (cat == target_cat)
            
            matches_query = True
            if query:
                matches_query = (
                    query in widget.name.lower() or 
                    query in widget.description.lower() or 
                    query in widget.result_label.text().lower()
                )

            widget.setVisible(matches_cat and matches_query)

    def _update_stats(self, passed: int, warning: int, failed: int, info: int, skipped: int, total: int):
        self.lbl_passed.setText(f"✓ {passed} Aprovados")
        self.lbl_warning.setText(f"⚠️ {warning} Atenção")
        self.lbl_failed.setText(f"✗ {failed} Falhas")
        self.lbl_info.setText(f"ℹ️ {info} Info")
        self.lbl_total.setText(f"Total: {total}")
        
        tested = passed + warning + failed
        if tested > 0:
            score = max(0, int(((passed * 100) + (warning * 50)) / tested))
            self.score_label.setText(f"Saúde: {score}%")
            if score >= 80:
                self.score_label.setStyleSheet("color: #30d158; padding: 4px 8px;")
            elif score >= 50:
                self.score_label.setStyleSheet("color: #ff9f0a; padding: 4px 8px;")
            else:
                self.score_label.setStyleSheet("color: #ff453a; padding: 4px 8px;")

    def set_device(self, serial: str):
        self.current_serial = serial

    def set_device_info(self, device_info):
        self.action_guide.update_status(device_info)
        mode = getattr(device_info, 'mode', DeviceMode.UNKNOWN)
        if mode == DeviceMode.ADB_NORMAL:
            self.btn_run_all.setEnabled(True)
            self.btn_optimize.setEnabled(True)
            self.action_guide.hide()
            m = getattr(device_info, 'model', '')
            man = getattr(device_info, 'manufacturer', '')
            self.subtitle_label.setText(f"Aparelho conectado: {man} {m} (ADB Operacional) • Rotinas técnicas de hardware liberadas")
        else:
            self.btn_run_all.setEnabled(False)
            self.btn_optimize.setEnabled(False)
            self.action_guide.show()
            self.subtitle_label.setText("Aguardando dispositivo pronto para análise...")

    def clear(self):
        self.current_serial = ""
        self.action_guide.set_disconnected()
        self.action_guide.show()
        self.findings_banner.hide()
        self.btn_run_all.setEnabled(False)
        self.btn_optimize.setEnabled(False)
        self.subtitle_label.setText("Conecte um dispositivo Android via USB para iniciar")

    def _open_findings_dialog(self):
        """Abre o laudo técnico completo com as causas de lentidão e travamentos."""
        if getattr(self, '_last_report', None):
            dlg = FindingsDialog(self._last_report, self)
            dlg.exec()

    def _open_optimizer_dialog(self):
        """Abre o diálogo de otimização e limpeza do sistema em 1-clique."""
        serial_to_use = getattr(self, 'current_serial', '')
        if not serial_to_use:
            QMessageBox.warning(self, "Aviso", "Nenhum dispositivo conectado para otimização.")
            return
        from src.views.dialogs.optimizer_dialog import OptimizerDialog
        dlg = OptimizerDialog(serial_to_use, self)
        dlg.exec()


    @Slot()
    def _on_run_all_clicked(self):
        self.findings_banner.hide()
        for widget in self.test_widgets.values():
            widget.reset()
        serial_to_use = getattr(self, 'current_serial', '')
        if not serial_to_use:
            QMessageBox.warning(self, "Aviso", "Nenhum dispositivo conectado.")
            return
        self.view_model.start_diagnostic(serial_to_use, self.view_model.available_tests)

    @Slot()
    def _on_export_clicked(self):
        path = self.view_model.export_report()
        if path:
            QMessageBox.information(self, "Exportar", f"Relatório salvo em: {path}")

    @Slot(int)
    def _on_diagnostic_started(self, total: int):
        self.btn_run_all.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.findings_banner.hide()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Iniciando coletas de baixo nível no aparelho...")

    @Slot(int, int, str)
    def _on_collection_phase(self, step: int, total_steps: int, label: str):
        pct = int(step * 50 / max(1, total_steps))
        self.progress_bar.setValue(pct)
        self.progress_label.setText(f"[Coleta no Aparelho {step+1}/{total_steps}] {label}...")

    @Slot(int, str)
    def _on_test_progress(self, index: int, test_id: str):
        total = max(1, len(self.test_widgets))
        pct = 50 + int(index * 50 / total)
        self.progress_bar.setValue(pct)
        widget = self.test_widgets.get(test_id)
        if widget:
            widget.set_status(TestStatus.RUNNING)
            self.progress_label.setText(f"[Análise Técnica {index+1}/{total}] {widget.name}...")

    @Slot(object)
    def _on_test_completed(self, result: TestResult):
        widget = self.test_widgets.get(result.test_id)
        if widget:
            widget.set_status(result.status, result.message, result.details)

    @Slot(object)
    def _on_diagnostic_finished(self, report: DiagnosticReport):
        self._last_report = report
        self.btn_run_all.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_label.setText(
            f"Diagnóstico concluído ({report.passed_count} aprovados, {report.warning_count} alertas, {report.failed_count} falhas, {report.info_count} informativos)"
        )

        # Atualiza e exibe o banner compacto no topo da lista sem roubar o espaço da tabela
        if report.failed_count > 0:
            self.findings_banner.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 69, 58, 0.16);
                    border: 1px solid rgba(255, 69, 58, 0.45);
                    border-radius: 8px;
                }
            """)
            self.banner_icon.setText("🚨")
            self.banner_text.setText(
                f"Laudo Crítico: {report.failed_count} Problemas Críticos e {report.warning_count} Alertas de Atenção identificados"
            )
        elif report.warning_count > 0:
            self.findings_banner.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 159, 10, 0.16);
                    border: 1px solid rgba(255, 159, 10, 0.45);
                    border-radius: 8px;
                }
            """)
            self.banner_icon.setText("⚠️")
            self.banner_text.setText(
                f"Laudo de Atenção: {report.warning_count} Pontos de Atenção identificados no aparelho"
            )
        else:
            self.findings_banner.setStyleSheet("""
                QFrame {
                    background-color: rgba(48, 209, 88, 0.16);
                    border: 1px solid rgba(48, 209, 88, 0.45);
                    border-radius: 8px;
                }
            """)
            self.banner_icon.setText("✓")
            self.banner_text.setText("Laudo de Conformidade: Parâmetros validados com sucesso")

        self.findings_banner.show()
        # Abre o Laudo Técnico completo em janela dedicada com espaço confortável
        self._open_findings_dialog()

    @Slot(str)
    def _on_error(self, message: str):
        self.btn_run_all.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_label.setText("Diagnóstico cancelado ou com erro")
        QMessageBox.warning(self, "Erro no Diagnóstico", message)

