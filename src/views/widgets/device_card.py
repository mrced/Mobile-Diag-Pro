from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.core.theme_manager import ThemeManager
from src.core.constants import DeviceMode


class DeviceCard(QFrame):
    """Cartão informativo exibindo os dados básicos do dispositivo conectado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "device-card")
        self._tm = ThemeManager()
        self._setup_ui()
        self._apply_placeholder()
        # Reagir a mudanças de tema
        self._tm.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # Header: icon + model + mode badge
        header = QHBoxLayout()
        header.setSpacing(12)

        self.icon_label = QLabel("📱")
        self.icon_label.setStyleSheet("font-size: 36px; background: transparent;")

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        self.model_label = QLabel("")
        self.model_label.setObjectName("deviceModel")

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("deviceDetail")

        info_col.addWidget(self.model_label)
        info_col.addWidget(self.detail_label)

        header.addWidget(self.icon_label)
        header.addLayout(info_col, 1)

        self.mode_badge = QLabel("")
        self.mode_badge.setObjectName("modeBadge")
        header.addWidget(self.mode_badge, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        layout.addLayout(header)

        # Info row
        info_row = QHBoxLayout()
        info_row.setSpacing(24)

        self.serial_label = QLabel("")
        self.serial_label.setObjectName("deviceSerial")
        self.android_label = QLabel("")
        self.android_label.setObjectName("deviceAndroid")
        self.patch_label = QLabel("")
        self.patch_label.setObjectName("devicePatch")

        info_row.addWidget(self.serial_label)
        info_row.addWidget(self.android_label)
        info_row.addWidget(self.patch_label)
        info_row.addStretch()

        layout.addLayout(info_row)

    def _apply_styles(self):
        """Aplica estilos dinâmicos baseados no tema atual."""
        c = self._tm.colors
        self.model_label.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {c.text_primary}; background: transparent;")
        self.detail_label.setStyleSheet(f"font-size: 13px; color: {c.text_secondary}; background: transparent;")
        for lbl in [self.serial_label, self.android_label, self.patch_label]:
            lbl.setStyleSheet(f"font-size: 12px; color: {c.text_secondary}; background: transparent;")

    def _apply_placeholder(self):
        """Mostra estado desconectado."""
        c = self._tm.colors
        self.icon_label.setText("🔌")
        self.model_label.setText("Nenhum dispositivo conectado")
        self.model_label.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {c.muted}; background: transparent;")
        self.detail_label.setText("Conecte um dispositivo Android via USB")
        self.detail_label.setStyleSheet(f"font-size: 13px; color: {c.muted}; background: transparent;")
        self.serial_label.setText("")
        self.android_label.setText("")
        self.patch_label.setText("")
        self.mode_badge.setText("")
        self.mode_badge.setStyleSheet("background: transparent;")

    def update_device(self, device_info) -> None:
        """Atualiza o cartão com as informações do dispositivo."""
        c = self._tm.colors
        self.icon_label.setText("📱")

        model = getattr(device_info, 'model', 'Desconhecido')
        manufacturer = getattr(device_info, 'manufacturer', '')
        brand = getattr(device_info, 'brand', '')

        self.model_label.setText(model)
        self._apply_styles()

        detail_parts = [p for p in [manufacturer, brand] if p]
        self.detail_label.setText(" · ".join(detail_parts) if detail_parts else "")

        serial = getattr(device_info, 'serial', '')
        android = getattr(device_info, 'android_version', '')
        patch = getattr(device_info, 'security_patch', '')

        self.serial_label.setText(f"SN: {serial}" if serial else "")
        self.android_label.setText(f"Android {android}" if android else "")
        self.patch_label.setText(f"Patch: {patch}" if patch else "")

        # Mode badge
        mode = getattr(device_info, 'mode', DeviceMode.UNKNOWN)
        mode_config = {
            DeviceMode.ADB_NORMAL: ("● Conectado", c.success),
            DeviceMode.ADB_UNAUTHORIZED: ("● Não Autorizado", c.danger),
            DeviceMode.RECOVERY: ("● Recovery", c.warning),
            DeviceMode.SIDELOAD: ("● Sideload", c.warning),
            DeviceMode.FASTBOOT: ("● Fastboot", "#ff9500"),
            DeviceMode.FASTBOOTD: ("● Fastbootd", "#ff9500"),
            DeviceMode.DRIVER_MISSING: ("● Driver Ausente (Cód 28)", c.danger),
            DeviceMode.USB_NO_DEBUGGING: ("● Sem Depuração USB", c.warning),
            DeviceMode.QUALCOMM_EDL: ("● Modo EDL 9008", c.warning),
            DeviceMode.SAMSUNG_DOWNLOAD: ("● Download (Odin)", "#ff9500"),
            DeviceMode.MEDIATEK_BROM: ("● MediaTek BROM", c.warning),
        }
        text, color = mode_config.get(mode, ("● Desconhecido", c.muted))
        self.mode_badge.setText(text)
        self.mode_badge.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 13px; background: transparent;")

    def clear(self):
        """Reseta o cartão para o estado desconectado."""
        self._apply_placeholder()

    def _on_theme_changed(self, theme: str) -> None:
        """Reaplica estilos quando o tema muda."""
        if self.model_label.text() == "Nenhum dispositivo conectado":
            self._apply_placeholder()
        else:
            self._apply_styles()
