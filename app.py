import sys
import os
import re  # For input validation
import subprocess  # For running external commands
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QCheckBox, QComboBox, QPushButton, QFileDialog,
    QTextEdit, QTabWidget, QGroupBox, QSpinBox, QDateEdit, QSizePolicy,
    QScrollArea, QRadioButton, QMessageBox
)
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QDesktopServices, QIcon
from PySide6.QtCore import Qt, QDate, QTimer, QUrl, QSettings


class ImmichGoGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Immich-Go GUI")
        self.setGeometry(100, 100, 900, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Improved margins and spacing for a clean layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                background: #546E7A;
                padding: 10px 24px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                color: white;
                font-weight: 500;
                margin-right: 2px;
                border: none;
            }
            QTabBar::tab:selected {
                background: #37474F;
                color: white;
                border-bottom: 2px solid #263238;
            }
            QTabBar::tab:hover:!selected {
                background: #455A64;
            }
            QPushButton {
                background: #546E7A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #455A64;
            }
            QPushButton:pressed {
                background: #37474F;
            }
            QPushButton:disabled {
                background: #B0BEC5;
                color: #90A4AE;
            }
        """)
        # Add the tab widget to the main layout
        self.main_layout.addWidget(self.tab_widget)

        self.create_menu_bar()
        self.create_configuration_tab()
        self.create_google_takeout_tab()
        self.create_local_upload_tab()

        # Command Preview Section with refined size policy
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setMaximumHeight(80)
        self.command_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.main_layout.addWidget(QLabel("Command Preview:"))
        self.main_layout.addWidget(self.command_preview)

        # Status Indicator
        self.status_indicator = QLabel()
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_indicator)

        # Timer for command preview update
        self.command_update_timer = QTimer(self)
        self.command_update_timer.timeout.connect(self.update_command_preview)
        self.command_update_timer.start(300)

        self.settings = QSettings("YourOrganization", "ImmichGoGUI")
        
        # Check for and update (or download) the immich-go binary
        self.update_binary()

        self.load_configuration()

    def update_binary(self):
        """
        Checks whether the immich-go binary exists in the designated folder.
        If not, informs the user to manually place the binary in that folder.
        """
        binary_folder = os.path.join(os.getcwd(), "immich-go")
        if not os.path.exists(binary_folder):
            os.makedirs(binary_folder)
        if sys.platform.startswith("win"):
            binary_filename = "immich-go.exe"
        else:
            binary_filename = "immich-go"
        binary_path = os.path.join(binary_folder, binary_filename)
        self.binary_path = binary_path  # Store for later use
        if not os.path.exists(binary_path):
            QMessageBox.information(
                self,
                "Binary Not Found",
                f"The immich-go binary was not found in:\n{binary_folder}\n\n"
                "Please download the appropriate binary from the GitHub releases and place it in this folder."
            )

    def run_command(self, command_parts):
        binary = self.binary_path if hasattr(self, "binary_path") else "./immich-go"
        command = [binary] + self.get_config_options() + command_parts
        cmd_string = " ".join(command)
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", cmd_string], shell=True)
            elif sys.platform.startswith("darwin"):
                # On macOS, tell Terminal to run the command and keep the window open.
                apple_script = f'tell application "Terminal" to do script "{cmd_string}; exec bash"'
                subprocess.Popen(["osascript", "-e", apple_script])
            else:  # Linux
                # First try if the TERMINAL env variable is set.
                terminal = os.environ.get("TERMINAL")
                if terminal:
                    if "xterm" in terminal.lower():
                        subprocess.Popen([terminal, "-hold", "-e", cmd_string])
                    else:
                        subprocess.Popen([terminal, "-e", "bash", "-c", f"{cmd_string}; exec bash"])
                else:
                    # Try a list of common terminal emulators.
                    possible_terminals = [
                        ("gnome-terminal", ["--", "bash", "-c", f"{cmd_string}; exec bash"]),
                        ("konsole", ["-e", f"bash -c '{cmd_string}; exec bash'"]),
                        ("xfce4-terminal", ["-e", f"bash -c '{cmd_string}; exec bash'"]),
                        ("xterm", ["-hold", "-e", cmd_string])
                    ]
                    terminal_found = False
                    for term, args in possible_terminals:
                        try:
                            subprocess.Popen([term] + args)
                            terminal_found = True
                            break
                        except FileNotFoundError:
                            continue
                    if not terminal_found:
                        QMessageBox.critical(self, "Error", "No suitable terminal emulator found. Please install one.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run command: {e}")

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        save_action = QAction(QIcon("icons/save.png"), "Save Configuration", self)
        save_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_action)

        load_action = QAction("Load Configuration", self)
        load_action.triggered.connect(self.load_configuration)
        file_menu.addAction(load_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About Immich-Go", self)
        about_action.triggered.connect(self.open_github_link)
        help_menu.addAction(about_action)

    def create_configuration_tab(self):
        config_tab = QWidget()
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setWidget(config_tab)

        layout = QVBoxLayout(config_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        def create_info_icon(tooltip):
            label = QLabel("(i)")
            label.setToolTip(tooltip)
            label.setStyleSheet("color: #666; font-style: italic;")
            return label

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
        adv_group.setChecked(False)
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

        layout.addStretch()
        self.tab_widget.addTab(config_scroll, "Configuration")

        self.server_url_edit.textChanged.connect(self.validate_inputs)
        self.api_key_edit.textChanged.connect(self.validate_inputs)
        self.server_url_edit.textChanged.connect(self.update_status)
        self.api_key_edit.textChanged.connect(self.update_status)

    def create_google_takeout_tab(self):
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)

        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        def create_info_icon(tooltip):
            label = QLabel("(i)")
            label.setToolTip(tooltip)
            label.setStyleSheet("color: #666; font-style: italic;")
            return label

        def create_help_button(text):
            btn = QPushButton("?")
            btn.setFixedSize(20, 20)
            btn.setStyleSheet("font-weight: bold;")
            btn.clicked.connect(lambda: QMessageBox.information(self, "Help", text, QMessageBox.Ok))
            return btn

        file_group = QGroupBox("Source Selection")
        file_layout = QFormLayout()
        self.source_path_edit = QLineEdit()
        self.browse_btn = QPushButton("Browse ZIPs")
        self.source_path_edit.setAcceptDrops(True)
        self.source_path_edit.dragEnterEvent = self.dragEnterEvent
        self.source_path_edit.dropEvent = self.dropEvent

        source_row = QHBoxLayout()
        source_row.addWidget(self.source_path_edit)
        source_row.addWidget(create_info_icon("Path to Google Takeout ZIP files or extracted folder."))
        source_row.addStretch()

        file_layout.addRow("Path:", source_row)
        file_layout.addRow(self.browse_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        source_group = QGroupBox("Source Type")
        source_layout = QVBoxLayout()
        self.zip_radio = QRadioButton("Process ZIP archives")
        self.folder_radio = QRadioButton("Process extracted folder")
        self.zip_radio.setChecked(True)

        source_layout.addWidget(self.zip_radio)
        source_layout.addWidget(self.folder_radio)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        core_group = QGroupBox("Processing Options")
        core_form = QFormLayout()
        self.create_albums_check = QCheckBox("Create Albums")
        self.create_albums_check.setChecked(True)
        self.auto_archive_check = QCheckBox("Auto Archive")
        self.auto_archive_check.setChecked(True)
        self.untitled_albums_check = QCheckBox("Keep Untitled Albums")
        self.takeout_dry_run_check = QCheckBox("Dry Run Mode")
        self.run_takeout_button = QPushButton("Run Google Takeout")

        def add_form_row(form, widget, tooltip):
            row = QHBoxLayout()
            row.addWidget(widget)
            row.addWidget(create_info_icon(tooltip))
            row.addStretch()
            form.addRow(row)

        add_form_row(core_form, self.create_albums_check, "Create albums in Immich based on Takeout albums.")
        add_form_row(core_form, self.auto_archive_check, "Automatically archive uploaded assets in Immich.")
        add_form_row(core_form, self.untitled_albums_check, "Keep albums that have no title (usually event albums).")
        add_form_row(core_form, self.takeout_dry_run_check, "Simulate the upload without actually transferring files.")
        core_group.setLayout(core_form)
        layout.addWidget(core_group)
        layout.addWidget(self.run_takeout_button)

        adv_group = QGroupBox("Advanced Options")
        adv_group.setObjectName("Advanced Options")
        adv_group.setCheckable(True)
        adv_group.setChecked(False)
        adv_form = QFormLayout()

        self.missing_json_check = QCheckBox("Upload Missing JSON")
        self.album_folder_check = QCheckBox("Use Album Folder as Name")
        self.discard_archived_check = QCheckBox("Discard Archived Photos")

        add_form_row(adv_form, self.missing_json_check, "Upload JSON files even if corresponding media is missing.")
        add_form_row(adv_form, self.album_folder_check, "Use the name of the Takeout album folder as the album name in Immich.")
        add_form_row(adv_form, self.discard_archived_check, "Do not upload photos that are marked as archived in Takeout data.")
        adv_group.setLayout(adv_form)
        layout.addWidget(adv_group)

        layout.addStretch()
        self.tab_widget.addTab(scroll, "Google Takeout")

        self.browse_btn.clicked.connect(self.browse_takeout_source)
        self.zip_radio.toggled.connect(self.update_browse_mode)
        self.folder_radio.toggled.connect(self.update_browse_mode)
        self.run_takeout_button.clicked.connect(lambda: self.run_command(self.get_google_takeout_options()))

    def create_local_upload_tab(self):
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)

        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        def create_info_icon(tooltip):
            label = QLabel("(i)")
            label.setToolTip(tooltip)
            label.setStyleSheet("color: #666; font-style: italic;")
            return label

        source_group = QGroupBox("Source Folder")
        source_layout = QFormLayout()
        self.local_path_edit = QLineEdit()
        self.local_browse_btn = QPushButton("Browse")
        self.local_path_edit.setAcceptDrops(True)
        self.local_path_edit.dragEnterEvent = self.dragEnterEvent
        self.local_path_edit.dropEvent = self.dropEvent

        local_path_row = QHBoxLayout()
        local_path_row.addWidget(self.local_path_edit)
        local_path_row.addWidget(create_info_icon("Path to the local folder containing media to upload."))
        local_path_row.addStretch()
        source_layout.addRow("Path:", local_path_row)
        source_layout.addRow(self.local_browse_btn)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        date_group = QGroupBox("Date Filter")
        date_layout = QVBoxLayout()
        self.date_check = QCheckBox("Enable Date Filter")
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.end_date.setDate(QDate.currentDate())
        self.start_date.setEnabled(False)
        self.end_date.setEnabled(False)

        date_check_row = QHBoxLayout()
        date_check_row.addWidget(self.date_check)
        date_check_row.addWidget(create_info_icon("Filter media files based on their EXIF date range."))
        date_check_row.addStretch()
        date_layout.addLayout(date_check_row)
        date_layout.addWidget(QLabel("Start Date:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("End Date:"))
        date_layout.addWidget(self.end_date)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        type_group = QGroupBox("File Type Filter")
        type_layout = QVBoxLayout()
        self.type_check = QCheckBox("Filter by Extensions")
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText(".jpg,.png,.heic")
        self.type_edit.setEnabled(False)

        type_check_row = QHBoxLayout()
        type_check_row.addWidget(self.type_check)
        type_check_row.addWidget(create_info_icon("Filter media files by their file extensions."))
        type_check_row.addStretch()
        type_layout.addLayout(type_check_row)
        type_edit_row = QHBoxLayout()
        type_edit_row.addWidget(self.type_edit)
        type_edit_row.addWidget(create_info_icon("Enter comma-separated file extensions (e.g., .jpg,.mp4)."))
        type_edit_row.addStretch()
        type_layout.addLayout(type_edit_row)
        type_preset_layout = QHBoxLayout()
        photo_preset = QPushButton("Photos")
        photo_preset.clicked.connect(lambda: self.type_edit.setText(".jpg,.jpeg,.png,.heic"))
        video_preset = QPushButton("Videos")
        video_preset.clicked.connect(lambda: self.type_edit.setText(".mp4,.mov,.avi"))
        type_preset_layout.addWidget(photo_preset)
        type_preset_layout.addWidget(video_preset)
        type_layout.addLayout(type_preset_layout)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        upload_group = QGroupBox("Upload Options")
        upload_form = QFormLayout()
        self.album_name_edit = QLineEdit()
        self.create_folder_check = QCheckBox("Create Album from Folders")
        self.dry_run_check = QCheckBox("Dry Run Mode")
        
        album_name_row = QHBoxLayout()
        album_name_row.addWidget(self.album_name_edit)
        album_name_row.addWidget(create_info_icon("Specify an album name to upload all media into a single album."))
        album_name_row.addStretch()
        upload_form.addRow("Album Name:", album_name_row)
        
        create_folder_row = QHBoxLayout()
        create_folder_row.addWidget(self.create_folder_check)
        create_folder_row.addWidget(create_info_icon("Create albums in Immich based on the folder structure in the source path."))
        create_folder_row.addStretch()
        upload_form.addRow(create_folder_row)
        
        dry_run_row = QHBoxLayout()
        dry_run_row.addWidget(self.dry_run_check)
        dry_run_row.addWidget(create_info_icon("Simulate the upload without actually transferring files."))
        dry_run_row.addStretch()
        upload_form.addRow(dry_run_row)
        
        upload_group.setLayout(upload_form)
        layout.addWidget(upload_group)
        self.run_local_button = QPushButton("Run Local Upload")
        layout.addWidget(self.run_local_button)

        layout.addStretch()
        self.tab_widget.addTab(scroll, "Local Upload")

        self.date_check.toggled.connect(lambda checked: self.toggle_dates(checked))
        self.type_check.toggled.connect(lambda checked: self.type_edit.setEnabled(checked))
        self.local_browse_btn.clicked.connect(self.browse_local_folder)
        self.run_local_button.clicked.connect(lambda: self.run_command(self.get_local_upload_options()))

    def validate_inputs(self):
        required = [
            (self.server_url_edit, r"^https?://.+"),
            (self.api_key_edit, r".+")
        ]
        for field, pattern in required:
            if not re.match(pattern, field.text()):
                field.setStyleSheet("border: 1px solid red;")
            else:
                field.setStyleSheet("")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        target = self.sender() if self.sender() else event.widget()
        if isinstance(target, QLineEdit):
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            if target == self.source_path_edit:
                current_text = self.source_path_edit.text()
                separator = "; " if current_text else ""
                self.source_path_edit.setText(current_text + separator + "; ".join(paths))
            elif target == self.local_path_edit:
                self.local_path_edit.setText(paths[0])
            event.acceptProposedAction()

    def browse_takeout_source(self):
        if self.zip_radio.isChecked():
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Google Takeout ZIPs", "", "ZIP Files (*.zip)"
            )
            if files:
                self.source_path_edit.setText("; ".join(files))
                self.update_command_preview()
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Extracted Folder")
            if folder:
                self.source_path_edit.setText(folder)
                self.update_command_preview()

    def update_browse_mode(self, checked):
        self.source_path_edit.clear()
        self.browse_btn.setText("Browse ZIPs" if checked else "Browse Folder")
        self.update_command_preview()

    def toggle_dates(self, enabled):
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)
        self.update_command_preview()

    def browse_local_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Upload Folder")
        if folder:
            self.local_path_edit.setText(folder)
            self.update_command_preview()

    def update_command_preview(self):
        parts = [self.binary_path if hasattr(self, "binary_path") else "./immich-go"]
        parts += self.get_config_options()
        current_tab = self.tab_widget.tabText(self.tab_widget.currentIndex())
        if current_tab == "Google Takeout":
            parts += self.get_google_takeout_options()
        elif current_tab == "Local Upload":
            parts += self.get_local_upload_options()

        command_text = " ".join(parts)

        if not self.server_url_edit.text():
            command_text += "\n\n⚠️ MISSING SERVER URL"
        if not self.api_key_edit.text():
            command_text += "\n⚠️ MISSING API KEY"

        self.command_preview.setPlainText(command_text)

    def get_config_options(self):
        options = []
        if self.server_url_edit.text():
            options.append(f"--server={self.server_url_edit.text()}")
        if self.api_key_edit.text():
            options.append(f"--key={self.api_key_edit.text()}")
        if self.skip_ssl_checkbox.isChecked():
            options.append("--skip-verify-ssl")
        if self.api_url_edit.text():
            options.append(f"--api-url={self.api_url_edit.text()}")
        if self.client_timeout_spin.value() != 1:
            options.append(f"--client-timeout={self.client_timeout_spin.value()}")
        if self.log_level_combo.currentText() != "ERROR":
            options.append(f"--log-level={self.log_level_combo.currentText()}")
        if self.device_uuid_edit.text():
            options.append(f"--device-uuid={self.device_uuid_edit.text()}")
        return options

    def get_google_takeout_options(self):
        options = ["upload", "--google-photos"]

        source_path = self.source_path_edit.text()
        if self.zip_radio.isChecked():
            zip_files = [path.strip() for path in source_path.split(";") if path.strip()]
            if zip_files:
                options += zip_files
        elif source_path:
            options.append(source_path)

        if self.create_albums_check.isChecked():
            options.append("--create-albums")
        if self.auto_archive_check.isChecked():
            options.append("--auto-archive")
        if self.untitled_albums_check.isChecked():
            options.append("--keep-untitled-albums")
        if self.takeout_dry_run_check.isChecked():
            options.append("--dry-run")

        if self.missing_json_check.isChecked():
            options.append("--upload-when-missing-json")
        if self.album_folder_check.isChecked():
            options.append("--use-album-folder-as-name")
        if self.discard_archived_check.isChecked():
            options.append("--discard-archived")

        return options

    def get_local_upload_options(self):
        options = ["upload"]

        source_path = self.local_path_edit.text()
        if source_path:
            options.append(source_path)

        if self.date_check.isChecked():
            start = self.start_date.date().toString("yyyy-MM-dd")
            end = self.end_date.date().toString("yyyy-MM-dd")
            options.append(f"--date-filter={start},{end}")

        if self.type_check.isChecked() and self.type_edit.text():
            exts = self.type_edit.text().replace(" ", "").strip()
            if exts:
                options.append(f'--file-filter="{exts}"')

        if self.album_name_edit.text():
            options.append(f'--album="{self.album_name_edit.text()}"')
        if self.create_folder_check.isChecked():
            options.append("--create-album-folder")
        if self.dry_run_check.isChecked():
            options.append("--dry-run")

        return options

    def update_status(self):
        errors = []
        if not self.server_url_edit.text():
            errors.append("Server URL required")
        if not self.api_key_edit.text():
            errors.append("API Key required")

        if errors:
            self.status_indicator.setText("❌ " + ", ".join(errors))
            self.status_indicator.setStyleSheet("color: red;")
        else:
            self.status_indicator.setText("✓ Ready to go!")
            self.status_indicator.setStyleSheet("color: green;")
        self.validate_inputs()

    def open_github_link(self):
        url = QUrl("https://github.com/simulot/immich-go")
        QDesktopServices.openUrl(url)

    def save_configuration(self):
        self.settings.setValue("server_url", self.server_url_edit.text())
        self.settings.setValue("api_key", self.api_key_edit.text())
        self.settings.setValue("skip_ssl", self.skip_ssl_checkbox.isChecked())
        self.settings.setValue("api_url", self.api_url_edit.text())
        self.settings.setValue("client_timeout", self.client_timeout_spin.value())
        self.settings.setValue("log_level", self.log_level_combo.currentText())
        self.settings.setValue("device_uuid", self.device_uuid_edit.text())

        self.settings.setValue("google_takeout_zip_radio", self.zip_radio.isChecked())
        self.settings.setValue("google_takeout_folder_radio", self.folder_radio.isChecked())
        self.settings.setValue("google_takeout_source_path", self.source_path_edit.text())
        self.settings.setValue("google_takeout_create_albums", self.create_albums_check.isChecked())
        self.settings.setValue("google_takeout_auto_archive", self.auto_archive_check.isChecked())
        self.settings.setValue("google_takeout_untitled_albums", self.untitled_albums_check.isChecked())
        self.settings.setValue("google_takeout_dry_run", self.takeout_dry_run_check.isChecked())
        self.settings.setValue("google_takeout_missing_json", self.missing_json_check.isChecked())
        self.settings.setValue("google_takeout_album_folder_name", self.album_folder_check.isChecked())
        self.settings.setValue("google_takeout_discard_archived", self.discard_archived_check.isChecked())
        adv_group_config = self.tab_widget.widget(0).widget().findChild(QGroupBox, "Advanced Configuration")
        if adv_group_config is not None:
            self.settings.setValue("config_adv_group_checked", adv_group_config.isChecked())
        adv_group_google_takeout = self.tab_widget.widget(1).widget().findChild(QGroupBox, "Advanced Options")
        if adv_group_google_takeout is not None:
            self.settings.setValue("google_takeout_adv_group_checked", adv_group_google_takeout.isChecked())

        self.settings.setValue("local_upload_path", self.local_path_edit.text())
        self.settings.setValue("local_upload_date_check", self.date_check.isChecked())
        self.settings.setValue("local_upload_start_date", self.start_date.date())
        self.settings.setValue("local_upload_end_date", self.end_date.date())
        self.settings.setValue("local_upload_type_check", self.type_check.isChecked())
        self.settings.setValue("local_upload_type_edit", self.type_edit.text())
        self.settings.setValue("local_upload_album_name", self.album_name_edit.text())
        self.settings.setValue("local_upload_create_folder_check", self.create_folder_check.isChecked())
        self.settings.setValue("local_upload_dry_run_check", self.dry_run_check.isChecked())

    def load_configuration(self):
        self.server_url_edit.setText(self.settings.value("server_url", ""))
        self.api_key_edit.setText(self.settings.value("api_key", ""))
        self.skip_ssl_checkbox.setChecked(self.settings.value("skip_ssl", False, type=bool))
        self.api_url_edit.setText(self.settings.value("api_url", ""))
        self.client_timeout_spin.setValue(self.settings.value("client_timeout", 1, type=int))
        self.log_level_combo.setCurrentText(self.settings.value("log_level", "ERROR"))
        self.device_uuid_edit.setText(self.settings.value("device_uuid", ""))

        self.zip_radio.setChecked(self.settings.value("google_takeout_zip_radio", True, type=bool))
        self.folder_radio.setChecked(self.settings.value("google_takeout_folder_radio", False, type=bool))
        self.update_browse_mode(self.zip_radio.isChecked())
        self.source_path_edit.setText(self.settings.value("google_takeout_source_path", ""))
        self.create_albums_check.setChecked(self.settings.value("google_takeout_create_albums", True, type=bool))
        self.auto_archive_check.setChecked(self.settings.value("google_takeout_auto_archive", True, type=bool))
        self.untitled_albums_check.setChecked(self.settings.value("google_takeout_untitled_albums", False, type=bool))
        self.takeout_dry_run_check.setChecked(self.settings.value("google_takeout_dry_run", False, type=bool))
        self.missing_json_check.setChecked(self.settings.value("google_takeout_missing_json", False, type=bool))
        self.album_folder_check.setChecked(self.settings.value("google_takeout_album_folder_name", False, type=bool))
        self.discard_archived_check.setChecked(self.settings.value("google_takeout_discard_archived", False, type=bool))
        adv_group_google_takeout = self.tab_widget.widget(1).widget().findChild(QGroupBox, "Advanced Options")
        if adv_group_google_takeout is not None:
            adv_group_google_takeout.setChecked(self.settings.value("google_takeout_adv_group_checked", False, type=bool))

        self.local_path_edit.setText(self.settings.value("local_upload_path", ""))
        self.date_check.setChecked(self.settings.value("local_upload_date_check", False, type=bool))
        self.toggle_dates(self.date_check.isChecked())
        self.start_date.setDate(self.settings.value("local_upload_start_date", QDate.currentDate().addYears(-1)))
        self.end_date.setDate(self.settings.value("local_upload_end_date", QDate.currentDate()))
        self.type_check.setChecked(self.settings.value("local_upload_type_check", False, type=bool))
        self.type_edit.setEnabled(self.type_check.isChecked())
        self.type_edit.setText(self.settings.value("local_upload_type_edit", ""))
        self.album_name_edit.setText(self.settings.value("local_upload_album_name", ""))
        self.create_folder_check.setChecked(self.settings.value("local_upload_create_folder_check", False, type=bool))
        self.dry_run_check.setChecked(self.settings.value("local_upload_dry_run_check", False, type=bool))
        adv_group_config = self.tab_widget.widget(0).widget().findChild(QGroupBox, "Advanced Configuration")
        if adv_group_config is not None:
            adv_group_config.setChecked(self.settings.value("config_adv_group_checked", False, type=bool))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    from PySide6.QtGui import QFont
    app.setFont(QFont("Segoe UI", 10))
    window = ImmichGoGUI()
    window.show()
    window.update_status()
    sys.exit(app.exec())
