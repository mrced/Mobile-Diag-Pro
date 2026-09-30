from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QProgressBar, QComboBox,
    QCheckBox, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

from src.core.constants import DeviceMode
from src.viewmodels.diagnostic_vm import DiagnosticViewModel, TestResult, DiagnosticReport
from src.views.widgets.test_item_widget import TestItemWidget, TestStatus
from src.views.widgets.action_guide_card import ActionGuideCard

class DiagnosticPage(QWidget):
    """
    Página completa de Diagnóstico Avançado.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.view_model = DiagnosticViewModel(self)
        self.test_widgets: Dict[str, TestItemWidget] = {}
        
        self._setup_ui()
        self._connect_signals()
        self._populate_mock_tests() # Para visualização
        
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)
        
        # --- Header Section ---
        self.header_layout = QHBoxLayout()
        
        # Títulos
        self.title_layout = QVBoxLayout()
        self.title_label = QLabel("Diagnóstico Avançado")
        font_title = self.title_label.font()
        font_title.setPointSize(24)
        font_title.setBold(True)
        self.title_label.setFont(font_title)
        
        self.subtitle_label = QLabel("Bateria, Hardware, Sensores, Desempenho e Integridade")
        self.subtitle_label.setStyleSheet("color: gray;")
        
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addWidget(self.subtitle_label)
        self.header_layout.addLayout(self.title_layout)
        
        self.header_layout.addStretch()
        
        # Estatísticas (Summary Bar)
        self.stats_layout = QHBoxLayout()
        
        self.score_label = QLabel("Saúde: 100%")
        font_score = self.score_label.font()
        font_score.setPointSize(16)
        font_score.setBold(True)
        self.score_label.setFont(font_score)
        self.score_label.setStyleSheet("color: #198754;")
        
        self.lbl_passed = self._create_badge("Aprovados: 0", "#198754")
        self.lbl_warning = self._create_badge("Atenção: 0", "#fd7e14")
        self.lbl_failed = self._create_badge("Falhas: 0", "#dc3545")
        self.lbl_total = self._create_badge("Total: 0", "#6c757d")
        
        self.stats_layout.addWidget(self.score_label)
        self.stats_layout.addWidget(self.lbl_passed)
        self.stats_layout.addWidget(self.lbl_warning)
        self.stats_layout.addWidget(self.lbl_failed)
        self.stats_layout.addWidget(self.lbl_total)
        
        self.header_layout.addLayout(self.stats_layout)
        self.main_layout.addLayout(self.header_layout)
        
        # --- Guia de Ações & Prontidão ---
        self.action_guide = ActionGuideCard(self)
        self.main_layout.addWidget(self.action_guide)
        
        # --- Controls Section ---
        self.controls_layout = QHBoxLayout()
        
        self.btn_run_all = QPushButton("Executar Todos")
        self.btn_run_all.setStyleSheet("background-color: #0d6efd; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        
        self.btn_run_selected = QPushButton("Executar Selecionados")
        self.btn_run_selected.setStyleSheet("padding: 8px 16px; border-radius: 4px;")
        
        self.btn_stop = QPushButton("Parar")
        self.btn_stop.setStyleSheet("background-color: #dc3545; color: white; padding: 8px 16px; border-radius: 4px;")
        self.btn_stop.setEnabled(False)
        
        self.btn_export = QPushButton("Exportar Relatório")
        self.btn_export.setStyleSheet("padding: 8px 16px; border-radius: 4px;")
        
        self.btn_toggle_expand = QPushButton("Expandir Todos")
        self.btn_toggle_expand.setStyleSheet("padding: 8px 16px; border-radius: 4px;")
        self.btn_toggle_expand.clicked.connect(self._toggle_expand_all)

        self.controls_layout.addWidget(self.btn_run_all)
        self.controls_layout.addWidget(self.btn_run_selected)
        self.controls_layout.addWidget(self.btn_stop)
        self.controls_layout.addWidget(self.btn_toggle_expand)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.btn_export)
        
        self.main_layout.addLayout(self.controls_layout)
        
        # --- Filter Section ---
        self.filter_layout = QHBoxLayout()
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Bateria", "CPU & RAM", "Armazenamento", "Sensores", "Térmico", "Sistema", "Rede"])
        
        self.chk_select_all = QCheckBox("Selecionar Todos")
        self.chk_select_all.setChecked(True)
        
        self.filter_layout.addWidget(QLabel("Categoria:"))
        self.filter_layout.addWidget(self.filter_combo)
        self.filter_layout.addStretch()
        self.filter_layout.addWidget(self.chk_select_all)
        
        self.main_layout.addLayout(self.filter_layout)
        
        # --- Test List Section ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.list_widget)
        self.main_layout.addWidget(self.scroll_area, 1) # proportion 1 para expandir
        
        # --- Progress Section ---
        self.progress_layout = QHBoxLayout()
        self.progress_label = QLabel("Pronto")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        self.progress_layout.addWidget(self.progress_label)
        self.progress_layout.addWidget(self.progress_bar, 1)
        
        self.main_layout.addLayout(self.progress_layout)

    def _create_badge(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background-color: {color}; color: white; padding: 4px 8px; border-radius: 12px; font-weight: bold;")
        return lbl

    def _connect_signals(self):
        self.btn_run_all.clicked.connect(self._on_run_all_clicked)
        self.btn_run_selected.clicked.connect(self._on_run_selected_clicked)
        self.btn_stop.clicked.connect(self.view_model.stop_diagnostic)
        self.btn_export.clicked.connect(self._on_export_clicked)
        
        self.view_model.diagnostic_started.connect(self._on_diagnostic_started)
        self.view_model.test_progress.connect(self._on_test_progress)
        self.view_model.test_completed.connect(self._on_test_completed)
        self.view_model.diagnostic_finished.connect(self._on_diagnostic_finished)
        self.view_model.error_occurred.connect(self._on_error)
        self.view_model.stats_updated.connect(self._update_stats)

    def _populate_mock_tests(self):
        """Preenche a lista com todos os 50+ testes do DiagnosticEngine."""
        from src.core.diagnostic_engine import DiagnosticEngine
        
        category_icons = {
            "battery": "🔋",
            "cpu": "🧠",
            "memory": "⚡",
            "storage": "💾",
            "display": "📱",
            "sensors": "🧭",
            "thermal": "🌡️",
            "network": "📶",
            "system": "🛡️",
            "apps": "📦",
            "processes": "⚙️",
            "connectivity": "🔌",
        }
        
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
            self.view_model.available_tests.append(tid)

    def _update_stats(self, passed: int, warning: int, failed: int, total: int):
        self.lbl_passed.setText(f"Aprovados: {passed}")
        self.lbl_warning.setText(f"Atenção: {warning}")
        self.lbl_failed.setText(f"Falhas: {failed}")
        self.lbl_total.setText(f"Total: {total}")
        
        if total > 0:
            score = max(0, int(((passed + (warning * 0.5)) / total) * 100))
            self.score_label.setText(f"Saúde: {score}%")
            if score >= 80:
                self.score_label.setStyleSheet("color: #198754;") # Verde
            elif score >= 50:
                self.score_label.setStyleSheet("color: #fd7e14;") # Laranja
            else:
                self.score_label.setStyleSheet("color: #dc3545;") # Vermelho

        # ... o resto continua igual ...
    def set_device(self, serial: str):
        self.current_serial = serial

    def set_device_info(self, device_info):
        self.action_guide.update_status(device_info)
        mode = getattr(device_info, 'mode', DeviceMode.UNKNOWN)
        if mode == DeviceMode.ADB_NORMAL:
            self.btn_run_all.setEnabled(True)
            self.btn_run_selected.setEnabled(True)
        else:
            self.btn_run_all.setEnabled(False)
            self.btn_run_selected.setEnabled(False)

    def clear(self):
        self.current_serial = ""
        self.action_guide.set_disconnected()
        self.btn_run_all.setEnabled(False)
        self.btn_run_selected.setEnabled(False)

    @Slot()
    def _on_run_all_clicked(self):
        for widget in self.test_widgets.values():
            widget.reset()
        serial_to_use = getattr(self, 'current_serial', '')
        if not serial_to_use:
            QMessageBox.warning(self, "Aviso", "Nenhum dispositivo conectado.")
            return
        self.view_model.start_diagnostic(serial_to_use, self.view_model.available_tests)

    @Slot()
    def _on_run_selected_clicked(self):
        self._on_run_all_clicked()

    @Slot()
    def _toggle_expand_all(self):
        is_expanding = self.btn_toggle_expand.text() == "Expandir Todos"
        for widget in self.test_widgets.values():
            widget.set_expanded(is_expanding)
        self.btn_toggle_expand.setText("Recolher Todos" if is_expanding else "Expandir Todos")

    @Slot()
    def _on_export_clicked(self):
        path = self.view_model.export_report()
        if path:
            QMessageBox.information(self, "Exportar", f"Relatório salvo em: {path}")

    @Slot(int)
    def _on_diagnostic_started(self, total: int):
        self.btn_run_all.setEnabled(False)
        self.btn_run_selected.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Iniciando...")

    @Slot(int, str)
    def _on_test_progress(self, index: int, test_id: str):
        self.progress_bar.setValue(index)
        widget = self.test_widgets.get(test_id)
        if widget:
            widget.set_status(TestStatus.RUNNING)
            self.progress_label.setText(f"Executando {widget.name}...")

    @Slot(object)
    def _on_test_completed(self, result: TestResult):
        widget = self.test_widgets.get(result.test_id)
        if widget:
            widget.set_status(result.status, result.message, result.details)

    @Slot(object)
    def _on_diagnostic_finished(self, report: DiagnosticReport):
        self.btn_run_all.setEnabled(True)
        self.btn_run_selected.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.progress_label.setText("Concluído")
        QMessageBox.information(self, "Diagnóstico", "Diagnóstico finalizado com sucesso.")

    @Slot(str)
    def _on_error(self, message: str):
        self.btn_run_all.setEnabled(True)
        self.btn_run_selected.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_label.setText("Erro / Cancelado")
        QMessageBox.warning(self, "Erro", message)
