# immich_go_gui/ui/local_upload_tab.py

from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QPushButton,
                               QCheckBox, QGroupBox, QVBoxLayout, QLabel,
                               QHBoxLayout, QFileDialog, QDateEdit, QScrollArea, QComboBox)
from PySide6.QtCore import Signal, QDate, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from utils.ui_helpers import create_info_icon

class LocalUploadTab(QWidget):

    run_command_signal = Signal(list)  # Signal for running command

    def __init__(self, settings_manager, update_command_preview_signal, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.update_command_preview_signal = update_command_preview_signal
        self.setup_ui()
        self.load_settings()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        source_group = QGroupBox("Source Folder")
        source_layout = QFormLayout()
        self.local_path_edit = QLineEdit()
        self.local_browse_btn = QPushButton("Browse")
        self.local_path_edit.setAcceptDrops(True)

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
        self.dry_run_check = QCheckBox("Dry Run Mode")
        self.run_local_button = QPushButton("Run Local Upload")

        #New fields
        self.recursive_check = QCheckBox("Recursive")
        self.recursive_check.setChecked(True)
        self.date_from_name_check = QCheckBox("Date From Name")
        self.date_from_name_check.setChecked(True)
        # self.folder_as_album_combo = QComboBox() # Removed
        # self.folder_as_album_combo.addItems(["NONE","FOLDER", "PATH"])


        album_name_row = QHBoxLayout()
        album_name_row.addWidget(self.album_name_edit)
        album_name_row.addWidget(create_info_icon("Specify an album name to upload all media into a single album."))
        album_name_row.addStretch()
        upload_form.addRow("Album Name:", album_name_row)


        dry_run_row = QHBoxLayout()
        dry_run_row.addWidget(self.dry_run_check)
        dry_run_row.addWidget(create_info_icon("Simulate the upload without actually transferring files."))
        dry_run_row.addStretch()
        upload_form.addRow(dry_run_row)
        upload_form.addRow(self.recursive_check)
        upload_form.addRow(self.date_from_name_check)
        # upload_form.addRow("Folder as Album",self.folder_as_album_combo) # Removed


        upload_group.setLayout(upload_form)
        layout.addWidget(upload_group)
        layout.addWidget(self.run_local_button)

        # Wrap in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(layout)
        scroll_area.setWidget(scroll_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def connect_signals(self):
        self.date_check.toggled.connect(self.toggle_dates)
        self.type_check.toggled.connect(lambda checked: self.type_edit.setEnabled(checked))
        self.local_browse_btn.clicked.connect(self.browse_local_folder)
        self.run_local_button.clicked.connect(self.run_command)
        self.local_path_edit.textChanged.connect(self.emit_update_preview)
        # Connect date/type/option changes
        self.date_check.toggled.connect(self.emit_update_preview)
        self.type_check.toggled.connect(self.emit_update_preview)
        self.type_edit.textChanged.connect(self.emit_update_preview)
        self.album_name_edit.textChanged.connect(self.emit_update_preview)
        self.dry_run_check.toggled.connect(self.emit_update_preview)
        #New signals
        self.recursive_check.toggled.connect(self.emit_update_preview)
        self.date_from_name_check.toggled.connect(self.emit_update_preview)
        # self.folder_as_album_combo.currentIndexChanged.connect(self.emit_update_preview) # Removed

    def emit_update_preview(self):
            self.update_command_preview_signal.emit()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            # Assuming single folder drop for local upload
            self.local_path_edit.setText(urls[0].toLocalFile())
            event.acceptProposedAction()
            self.emit_update_preview()


    def toggle_dates(self, enabled):
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)
        self.emit_update_preview()

    def browse_local_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Upload Folder")
        if folder:
            self.local_path_edit.setText(folder)
        self.emit_update_preview()

    def run_command(self):
        self.run_local_button.setEnabled(False)  # Disable button
        command_options = self.get_local_upload_values()
        self.run_command_signal.emit(command_options)

    def load_settings(self):
        settings = self.settings_manager.settings
        self.local_path_edit.setText(settings.value("local_upload_path", ""))
        self.date_check.setChecked(settings.value("local_upload_date_check", False, type=bool))
        self.toggle_dates(self.date_check.isChecked())  # Enable/disable date edits
        self.start_date.setDate(settings.value("local_upload_start_date", QDate.currentDate().addYears(-1)))
        self.end_date.setDate(settings.value("local_upload_end_date", QDate.currentDate()))
        self.type_check.setChecked(settings.value("local_upload_type_check", False, type=bool))
        self.type_edit.setEnabled(self.type_check.isChecked())  # Enable/disable type edit
        self.type_edit.setText(settings.value("local_upload_type_edit", ""))
        self.album_name_edit.setText(settings.value("local_upload_album_name", ""))
        self.dry_run_check.setChecked(settings.value("local_upload_dry_run_check", False, type=bool))

        #New fields
        self.recursive_check.setChecked(settings.value("local_upload_recursive_check",True,type=bool))
        self.date_from_name_check.setChecked(settings.value("local_upload_date_from_name_check", True, type=bool))
        # self.folder_as_album_combo.setCurrentText(settings.value("local_upload_folder_as_album_combo", "NONE")) # Removed


    def get_local_upload_values(self):
        return {
            "local_path": self.local_path_edit.text(),
            "date_filter_enabled": self.date_check.isChecked(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd") if self.date_check.isChecked() else None,
            "end_date": self.end_date.date().toString("yyyy-MM-dd") if self.date_check.isChecked() else None,
            "type_filter_enabled": self.type_check.isChecked(),
            "file_extensions": self.type_edit.text() if self.type_check.isChecked() else None,
            "album_name": self.album_name_edit.text(),
            "dry_run": self.dry_run_check.isChecked(),
            "recursive": self.recursive_check.isChecked(),
            "date_from_name": self.date_from_name_check.isChecked(),
            # "folder_as_album": self.folder_as_album_combo.currentText() # Removed
        }