"""
Diálogo de Otimização e Limpeza em 1-Clique (Estilo CCleaner / Advanced SystemCare).
Permite ao técnico suspender tarefas em segundo plano, aliviar processador e RAM,
limpar caches acumulados e acelerar a responsividade do dispositivo.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QProgressBar, QWidget, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from src.core.optimizer_engine import OptimizerEngine


class OptimizationWorker(QThread):
    """Worker em thread separada para não congelar a interface enquanto otimiza."""
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, engine: OptimizerEngine, serial: str, options: dict):
        super().__init__()
        self.engine = engine
        self.serial = serial
        self.options = options

    def run(self):
        try:
            def on_progress(pct: int, msg: str):
                self.progress.emit(pct, msg)

            result = self.engine.run_optimization(
                self.serial,
                options=self.options,
                progress_cb=on_progress
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class OptimizerDialog(QDialog):
    """
    Janela de Otimização e Limpeza do Dispositivo Android.
    """

    def __init__(self, serial: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.serial = serial
        self.engine = OptimizerEngine()
        self.worker: Optional[OptimizationWorker] = None

        self.setWindowTitle("Otimizador de Sistema & Desempenho (1-Clique)")
        self.resize(780, 640)
        self.setMinimumSize(700, 560)
        self._setup_ui()
        self._load_current_state()

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
            QCheckBox {
                color: #f5f5f7;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                background-color: rgba(255, 255, 255, 0.05);
            }
            QCheckBox::indicator:checked {
                background-color: #0a84ff;
                border-color: #0a84ff;
            }
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.3);
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #30d158;
                border-radius: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        icon_lbl = QLabel("⚡")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 26))
        header_layout.addWidget(icon_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        title_lbl = QLabel("Otimizador de Desempenho & Limpeza (1-Clique)")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #f5f5f7;")

        sub_lbl = QLabel(f"Desative tarefas em segundo plano, libere CPU/RAM e purgue caches acumulados • {self.serial}")
        sub_lbl.setStyleSheet("color: #8e8e93; font-size: 12px;")

        title_vbox.addWidget(title_lbl)
        title_vbox.addWidget(sub_lbl)
        header_layout.addLayout(title_vbox, 1)

        layout.addLayout(header_layout)

        # 2. Painel de Status Atual (Cards rápidos)
        self.status_panel = QHBoxLayout()
        self.status_panel.setSpacing(10)

        self.card_ram = self._create_metric_card("RAM Disponível", "Carregando...", "#0a84ff")
        self.card_swap = self._create_metric_card("Uso de Swap / ZRAM", "Carregando...", "#ff9f0a")
        self.card_apps = self._create_metric_card("Apps em Segundo Plano", "Carregando...", "#ff453a")

        self.status_panel.addWidget(self.card_ram)
        self.status_panel.addWidget(self.card_swap)
        self.status_panel.addWidget(self.card_apps)
        layout.addLayout(self.status_panel)

        # 3. Lista de Opções de Otimização (Checkboxes estilo CCleaner)
        opts_box = QFrame()
        opts_box.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
        """)
        opts_layout = QVBoxLayout(opts_box)
        opts_layout.setContentsMargins(16, 14, 16, 14)
        opts_layout.setSpacing(10)

        opts_title = QLabel("Selecione as ações de otimização:")
        opts_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        opts_title.setStyleSheet("color: #0a84ff; border: none; background: transparent;")
        opts_layout.addWidget(opts_title)

        self.chk_kill_bg = QCheckBox("🧹 Encerrar processos ociosos e tarefas zumbis em cache (am kill-all)")
        self.chk_kill_bg.setChecked(True)
        opts_layout.addWidget(self.chk_kill_bg)

        self.chk_stop_apps = QCheckBox("⏸️ Suspender aplicativos pesados de terceiros ativos em segundo plano (Redes sociais, lojas)")
        self.chk_stop_apps.setChecked(True)
        opts_layout.addWidget(self.chk_stop_apps)

        self.chk_trim_cache = QCheckBox("🗑️ Purgar caches de armazenamento do sistema e de aplicativos (pm trim-caches)")
        self.chk_trim_cache.setChecked(True)
        opts_layout.addWidget(self.chk_trim_cache)

        self.chk_compact_ram = QCheckBox("🗜️ Compactar memória RAM e disparar liberação de páginas órfãs (am trim-memory)")
        self.chk_compact_ram.setChecked(True)
        opts_layout.addWidget(self.chk_compact_ram)

        self.chk_clear_logs = QCheckBox("🧼 Limpar buffers de logcat e histórico de falhas (alivia a carga da CPU no processo logd)")
        self.chk_clear_logs.setChecked(True)
        opts_layout.addWidget(self.chk_clear_logs)

        self.chk_speed_anim = QCheckBox("🚀 Modo Turbo: Acelerar escala de animações para 0.5x (Aumenta fluidez e resposta visual)")
        self.chk_speed_anim.setChecked(False)
        opts_layout.addWidget(self.chk_speed_anim)

        layout.addWidget(opts_box)

        # 4. Área de Resultado / Apps Ativos
        self.result_frame = QFrame()
        self.result_frame.hide()
        self.result_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(48, 209, 88, 0.1);
                border: 1px solid rgba(48, 209, 88, 0.4);
                border-radius: 8px;
            }
        """)
        self.result_layout = QVBoxLayout(self.result_frame)
        self.result_layout.setContentsMargins(16, 12, 16, 12)
        self.result_layout.setSpacing(6)

        self.result_title = QLabel("✨ Otimização Concluída!")
        self.result_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.result_title.setStyleSheet("color: #30d158; border: none; background: transparent;")
        self.result_layout.addWidget(self.result_title)

        self.result_details = QLabel("")
        self.result_details.setFont(QFont("Segoe UI", 10))
        self.result_details.setStyleSheet("color: #f5f5f7; border: none; background: transparent;")
        self.result_details.setWordWrap(True)
        self.result_layout.addWidget(self.result_details)

        layout.addWidget(self.result_frame)

        # 5. Barra de Progresso e Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setFont(QFont("Segoe UI", 10))
        self.lbl_status.setStyleSheet("color: #ff9f0a;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.hide()
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # 6. Rodapé com Botões de Ação
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(12)

        self.btn_cancel = QPushButton("Fechar")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f5f5f7;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 20px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)

        footer_layout.addStretch()

        self.btn_optimize = QPushButton("⚡ OTIMIZAR AGORA (1-CLIQUE)")
        self.btn_optimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_optimize.setStyleSheet("""
            QPushButton {
                background-color: #30d158;
                color: #000000;
                font-weight: 800;
                font-size: 14px;
                padding: 10px 28px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #28b84c;
            }
            QPushButton:disabled {
                background-color: rgba(48, 209, 88, 0.3);
                color: rgba(0, 0, 0, 0.5);
            }
        """)
        self.btn_optimize.clicked.connect(self._start_optimization)
        footer_layout.addWidget(self.btn_optimize)

        layout.addLayout(footer_layout)

    def _create_metric_card(self, title: str, initial_val: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setFont(QFont("Segoe UI", 9))
        t_lbl.setStyleSheet("color: #8e8e93; border: none; background: transparent;")
        vbox.addWidget(t_lbl)

        v_lbl = QLabel(initial_val)
        v_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        v_lbl.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        vbox.addWidget(v_lbl)

        card.value_label = v_lbl
        return card

    def _load_current_state(self):
        """Carrega métricas iniciais do aparelho em segundo plano."""
        try:
            snap = self.engine.get_system_snapshot(self.serial)
            avail = snap.get("mem_available_mb", 0)
            total = snap.get("mem_total_mb", 0)
            swap_used = snap.get("swap_used_mb", 0)
            swap_total = snap.get("swap_total_mb", 0)
            apps_count = snap.get("running_third_party_count", 0)

            self.card_ram.value_label.setText(f"{avail} MB / {total} MB livres")
            self.card_swap.value_label.setText(f"{swap_used} MB / {swap_total} MB em uso")
            self.card_apps.value_label.setText(f"{apps_count} apps ativos")
        except Exception as e:
            self.card_ram.value_label.setText("Indisponível")
            self.card_swap.value_label.setText("Indisponível")
            self.card_apps.value_label.setText("Indisponível")

    def _start_optimization(self):
        """Dispara a rotina de otimização."""
        options = {
            "kill_background": self.chk_kill_bg.isChecked(),
            "stop_heavy_apps": self.chk_stop_apps.isChecked(),
            "trim_caches": self.chk_trim_cache.isChecked(),
            "compact_ram": self.chk_compact_ram.isChecked(),
            "clear_logs": self.chk_clear_logs.isChecked(),
            "speed_animations": self.chk_speed_anim.isChecked(),
        }

        self.btn_optimize.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(5)
        self.lbl_status.show()
        self.lbl_status.setText("Iniciando rotinas de alívio do sistema...")
        self.result_frame.hide()

        self.worker = OptimizationWorker(self.engine, self.serial, options)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def _on_finished(self, result: dict):
        self.progress_bar.setValue(100)
        self.lbl_status.setText("Concluído!")
        self.btn_optimize.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.btn_cancel.setText("Concluir e Fechar")

        # Atualizar cartões
        after = result.get("after", {})
        avail = after.get("mem_available_mb", 0)
        total = after.get("mem_total_mb", 0)
        swap_used = after.get("swap_used_mb", 0)
        swap_total = after.get("swap_total_mb", 0)
        apps_count = after.get("running_third_party_count", 0)

        self.card_ram.value_label.setText(f"{avail} MB / {total} MB livres")
        self.card_swap.value_label.setText(f"{swap_used} MB / {swap_total} MB em uso")
        self.card_apps.value_label.setText(f"{apps_count} apps ativos")

        # Exibir relatório
        ram_freed = result.get("ram_freed_mb", 0)
        swap_freed = result.get("swap_freed_mb", 0)
        stopped_count = result.get("stopped_apps_count", 0)

        details_text = (
            f"• <b>Memória RAM liberada:</b> +{ram_freed} MB adicionais disponíveis imediatamente.<br>"
            f"• <b>Swap / ZRAM aliviada:</b> +{swap_freed} MB de memória swap recuperados.<br>"
            f"• <b>Processos suspensos:</b> {stopped_count} aplicativos em segundo plano foram finalizados.<br>"
            f"• <b>Caches do sistema:</b> Arquivos temporários e logs do logcat foram purgados com sucesso."
        )
        if result.get("animations_applied"):
            details_text += "<br>• <b>Modo Turbo:</b> Escalas de animação configuradas para 0.5x."

        self.result_details.setText(details_text)
        self.result_frame.show()

    def _on_error(self, err: str):
        self.lbl_status.setText(f"Erro na otimização: {err}")
        self.btn_optimize.setEnabled(True)
        self.btn_cancel.setEnabled(True)
