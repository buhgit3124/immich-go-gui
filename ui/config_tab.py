# immich_go_gui/ui/config_tab.py

from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QCheckBox,
                               QComboBox, QSpinBox, QGroupBox, QVBoxLayout,
                               QLabel, QHBoxLayout, QScrollArea)
from PySide6.QtCore import Signal, QSettings
from utils.ui_helpers import create_info_icon
from utils.validators import validate_server_url, validate_api_key

class ConfigTab(QWidget):
    def __init__(self, settings_manager, update_command_preview_signal, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.update_command_preview_signal = update_command_preview_signal
        self.setup_ui()
        self.load_settings()  # Load settings when the tab is created
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        server_group = QGroupBox("Server Settings")
        server_form = QFormLayout()
        self.server_url_edit = QLineEdit()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.skip_ssl_checkbox = QCheckBox("Skip SSL Verification")

        server_url_row = QHBoxLayout()
        server_url_row.addWidget(self.server_url_edit)
        server_url_row.addWidget(create_info_icon("Immich server URL (e.g. http://your-server:2283)"))
        server_url_row.addStretch()

        server_form.addRow("Server URL *:", server_url_row)
        server_form.addRow("API Key *:", self.api_key_edit)
        server_form.addRow(self.skip_ssl_checkbox)
        server_group.setLayout(server_form)
        layout.addWidget(server_group)

        adv_group = QGroupBox("Advanced Configuration")
        adv_group.setObjectName("Advanced Configuration")
        adv_group.setCheckable(True)
        adv_group.setChecked(False)  # Initially collapsed
        adv_form = QFormLayout()

        self.api_url_edit = QLineEdit()
        self.client_timeout_spin = QSpinBox()
        self.client_timeout_spin.setRange(1, 1440)
        self.client_timeout_spin.setSuffix(" minutes")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["ERROR", "WARNING", "INFO"])
        self.device_uuid_edit = QLineEdit()

        adv_form.addRow("API URL:", self.api_url_edit)
        adv_form.addRow("Client Timeout:", self.client_timeout_spin)
        adv_form.addRow("Log Level:", self.log_level_combo)
        adv_form.addRow("Device UUID:", self.device_uuid_edit)
        adv_group.setLayout(adv_form)
        layout.addWidget(adv_group)

        # Wrap in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(layout)
        scroll_area.setWidget(scroll_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)


    def connect_signals(self):
        self.server_url_edit.textChanged.connect(self.validate_and_update)
        self.api_key_edit.textChanged.connect(self.validate_and_update)
        # Add connections for other fields if needed

    def validate_and_update(self):
        is_valid = self.validate_inputs()
        self.update_command_preview_signal.emit()


    def validate_inputs(self):
        is_valid = True
        if not validate_server_url(self.server_url_edit.text()):
            self.server_url_edit.setStyleSheet("border: 1px solid red;")
            is_valid = False
        else:
            self.server_url_edit.setStyleSheet("")

        if not validate_api_key(self.api_key_edit.text()):
            self.api_key_edit.setStyleSheet("border: 1px solid red;")
            is_valid = False
        else:
            self.api_key_edit.setStyleSheet("")
        return is_valid

    def load_settings(self):
        # Use the settings manager to load settings
        settings = self.settings_manager.settings
        self.server_url_edit.setText(settings.value("server_url", ""))
        self.api_key_edit.setText(settings.value("api_key", ""))
        self.skip_ssl_checkbox.setChecked(settings.value("skip_ssl", False, type=bool))
        self.api_url_edit.setText(settings.value("api_url", ""))
        self.client_timeout_spin.setValue(settings.value("client_timeout", 1, type=int))
        self.log_level_combo.setCurrentText(settings.value("log_level", "ERROR"))
        self.device_uuid_edit.setText(settings.value("device_uuid", ""))

        # Load advanced group checked state
        adv_group_checked = settings.value("config_adv_group_checked", False, type=bool)
        adv_group = self.findChild(QGroupBox, "Advanced Configuration")
        if adv_group:
            adv_group.setChecked(adv_group_checked)


    def get_config_values(self):
        # Helper to get all values in a dict.
        return {
            "server_url": self.server_url_edit.text(),
            "api_key": self.api_key_edit.text(),
            "skip_ssl": self.skip_ssl_checkbox.isChecked(),
            "api_url": self.api_url_edit.text(),
            "client_timeout": self.client_timeout_spin.value(),
            "log_level": self.log_level_combo.currentText(),
            "device_uuid": self.device_uuid_edit.text(),
            "adv_group_checked": self.findChild(QGroupBox, "Advanced Configuration").isChecked()
        }