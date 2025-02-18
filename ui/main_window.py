# immich_go_gui/ui/main_window.py

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
                               QTabWidget, QTextEdit, QSizePolicy, QProgressBar)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QCloseEvent
from PySide6.QtCore import QUrl

from ui.config_tab import ConfigTab
from ui.takeout_tab import TakeoutTab
from ui.local_upload_tab import LocalUploadTab
from ui.styles import apply_tab_styles
from core.binary_manager import BinaryManager
from core.process_manager import ProcessManager
from core.settings_manager import SettingsManager
from core.command_builder import CommandBuilder
import webbrowser  # Import webbrowser


class MainWindow(QMainWindow):

    update_command_preview_signal = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Immich-Go GUI")
        self.setGeometry(100, 100, 900, 700)

        self.binary_manager = BinaryManager()
        self.process_manager = ProcessManager()
        self.settings_manager = SettingsManager()
        self.command_builder = CommandBuilder(self.settings_manager)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.tab_widget = QTabWidget()
        apply_tab_styles(self.tab_widget)  # Apply styles from styles.py
        self.main_layout.addWidget(self.tab_widget)

        self.create_menu_bar()
        self.create_tabs()

        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setMaximumHeight(80)
        self.command_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.main_layout.addWidget(QLabel("Command Preview:"))
        self.main_layout.addWidget(self.command_preview)

        self.status_indicator = QLabel()
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_indicator)

        # Timer for command preview.
        self.command_update_timer = QTimer(self)
        self.command_update_timer.timeout.connect(self.update_command_preview)
        self.command_update_timer.start(300)

        # Check for and update (or download) the immich-go binary.
        self.binary_manager.update_binary(self.show_download_progress)

        # Load settings after binary manager (important for binary path).
        self.settings_manager.load_settings(self)
        self.update_command_preview_signal.connect(self.update_command_preview)

        # Connect tab changes to update command preview
        self.tab_widget.currentChanged.connect(self.update_command_preview)

        # Connect the run command signal
        self.takeout_tab.run_command_signal.connect(self.run_command_from_tab)
        self.local_upload_tab.run_command_signal.connect(self.run_command_from_tab)


    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        save_action = QAction(QIcon("icons/save.png"), "Save Configuration", self)
        save_action.triggered.connect(lambda: self.settings_manager.save_settings(self))
        file_menu.addAction(save_action)

        load_action = QAction("Load Configuration", self)
        load_action.triggered.connect(lambda: self.settings_manager.load_settings(self))
        file_menu.addAction(load_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About Immich-Go", self)
        about_action.triggered.connect(self.open_github_link)
        help_menu.addAction(about_action)

    def create_tabs(self):
        self.config_tab = ConfigTab(self.settings_manager, self.update_command_preview_signal)
        self.takeout_tab = TakeoutTab(self.settings_manager, self.update_command_preview_signal)
        self.local_upload_tab = LocalUploadTab(self.settings_manager, self.update_command_preview_signal)

        self.tab_widget.addTab(self.config_tab, "Configuration")
        self.tab_widget.addTab(self.takeout_tab, "Google Takeout")
        self.tab_widget.addTab(self.local_upload_tab, "Local Upload")

    def show_download_progress(self, progress, total_size):
        # Simple progress display in the status indicator
        if total_size > 0:
            percentage = (progress / total_size) * 100
            self.status_indicator.setText(f"Downloading immich-go: {percentage:.1f}%")
        else:
            self.status_indicator.setText("Downloading immich-go...")
        self.status_indicator.setStyleSheet("color: blue;")

    def update_command_preview(self):
        current_tab_index = self.tab_widget.currentIndex()
        current_tab_text = self.tab_widget.tabText(current_tab_index)
        command = self.command_builder.build_command(current_tab_text, self)
        self.command_preview.setPlainText(command)

        # Update status based on command validity
        if "MISSING" in command:
            self.status_indicator.setText("❌ Configuration incomplete")
            self.status_indicator.setStyleSheet("color: red;")
        else:
            self.status_indicator.setText("✓ Ready to go!")
            self.status_indicator.setStyleSheet("color: green;")


    def run_command_from_tab(self, command_parts):
        """
        Handles the run command signal from the tabs.
        Prepends the binary path and combines with config options.
        """

        if not self.binary_manager.binary_path:
            # Handle the case where binary is missing.
            self.status_indicator.setText("❌ immich-go binary not found!")
            self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
            return

        full_command = [self.binary_manager.binary_path] + command_parts
        self.process_manager.run_command(full_command, self.command_finished)


    def command_finished(self):
        """
        Callback function to handle the completion of the command execution.
        """
        self.status_indicator.setText("✓ Ready to go!")
        self.status_indicator.setStyleSheet("color: green; font-weight: bold;")
        self.takeout_tab.run_takeout_button.setEnabled(True)  # Re-enable the button
        self.local_upload_tab.run_local_button.setEnabled(True)


    def open_github_link(self):
        url = QUrl("https://github.com/simulot/immich-go")
        QDesktopServices.openUrl(url)

    def closeEvent(self, event: QCloseEvent):
        """Handle close events, ensure settings are saved."""
        self.settings_manager.save_settings(self)
        event.accept()  # Accept the close event