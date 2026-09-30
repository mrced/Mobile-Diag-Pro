import pyqtgraph as pg
from collections import deque
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from src.core.theme_manager import ThemeManager

class TelemetryChart(QWidget):
    """
    Gráfico em tempo real para telemetria usando pyqtgraph.
    """
    def __init__(self, title: str = "", y_label: str = "", y_range: tuple = (0, 100), 
                 buffer_size: int = 60, line_color: str = "", parent=None):
        super().__init__(parent)
        self._buffer_size = buffer_size
        
        self._tm = ThemeManager()
        self._tm.theme_changed.connect(self._on_theme_changed)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Configurar gráfico
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget(title=title)
        self.plot_widget.setBackground(self._tm.colors.chart_bg)
        self.plot_widget.setYRange(*y_range)
        self.plot_widget.setLabel('left', y_label)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getAxis('bottom').setTicks([])  # Esconder ticks do eixo X
        
        self.layout.addWidget(self.plot_widget)
        
        # Dados de linha única
        self._data = deque([0.0]*buffer_size, maxlen=buffer_size)
        c_accent = line_color if line_color else self._tm.colors.accent
        self._curve = self.plot_widget.plot(list(self._data), pen=pg.mkPen(color=c_accent, width=2))
        
        # Dados multilinhas
        self._multi_data = {}
        self._multi_curves = {}
        # Usar paleta de cores orientada a temas
        self._colors = [
            self._tm.colors.accent, 
            self._tm.colors.warning, 
            self._tm.colors.success, 
            self._tm.colors.danger, 
            self._tm.colors.text_primary
        ]

    def _on_theme_changed(self, theme: str) -> None:
        """Atualiza a cor de fundo do gráfico quando o tema muda."""
        self.plot_widget.setBackground(self._tm.colors.chart_bg)
        # As cores da caneta poderiam ser atualizadas aqui se necessário,
        # mas recriar dados/linhas precisaria de lógica extra. Fundo já ajuda bastante.

    def add_value(self, value: float) -> None:
        """Adiciona um valor para o gráfico de linha única."""
        self._data.append(value)
        self._curve.setData(list(self._data))

    def add_multi_values(self, values: dict[str, float]) -> None:
        """Adiciona valores para múltiplas linhas."""
        if not self._multi_curves:
            self.plot_widget.addLegend()
            self._curve.hide()  # Esconder linha principal se usar multi
            
            for i, (key, _) in enumerate(values.items()):
                color = self._colors[i % len(self._colors)]
                self._multi_data[key] = deque([0.0]*self._buffer_size, maxlen=self._buffer_size)
                self._multi_curves[key] = self.plot_widget.plot(list(self._multi_data[key]), 
                                                              name=key, 
                                                              pen=pg.mkPen(color=color, width=2))
                
        for key, value in values.items():
            if key in self._multi_data:
                self._multi_data[key].append(value)
                self._multi_curves[key].setData(list(self._multi_data[key]))

    def clear(self) -> None:
        """Limpa o gráfico."""
        self._data = deque([0.0]*self._buffer_size, maxlen=self._buffer_size)
        self._curve.setData(list(self._data))
        
        for key in self._multi_data:
            self._multi_data[key] = deque([0.0]*self._buffer_size, maxlen=self._buffer_size)
            self._multi_curves[key].setData(list(self._multi_data[key]))
