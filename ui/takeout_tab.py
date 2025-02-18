# immich_go_gui/ui/takeout_tab.py

from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QPushButton,
                               QCheckBox, QGroupBox, QVBoxLayout, QLabel,
                               QHBoxLayout, QFileDialog, QRadioButton, QScrollArea)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from utils.ui_helpers import create_info_icon

class TakeoutTab(QWidget):

    run_command_signal = Signal(list)  # Signal to emit the command

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


        file_group = QGroupBox("Source Selection")
        file_layout = QFormLayout()
        self.source_path_edit = QLineEdit()
        self.browse_btn = QPushButton("Browse ZIPs")
        self.source_path_edit.setAcceptDrops(True)

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
        self.zip_radio.setChecked(True)  # Default to ZIP

        source_layout.addWidget(self.zip_radio)
        source_layout.addWidget(self.folder_radio)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)


        core_group = QGroupBox("Processing Options")
        core_form = QFormLayout()
        # self.create_albums_check = QCheckBox("Create Albums") # Replaced with --sync-albums
        # self.create_albums_check.setChecked(True)
        # self.auto_archive_check = QCheckBox("Auto Archive") # Replaced with --include-archived
        # self.auto_archive_check.setChecked(True)
        # self.untitled_albums_check = QCheckBox("Keep Untitled Albums") #Replaced
        self.takeout_dry_run_check = QCheckBox("Dry Run Mode")
        self.run_takeout_button = QPushButton("Run Google Takeout")

        #New options
        self.include_archived_check = QCheckBox("Include Archived")
        self.include_archived_check.setChecked(True)
        self.include_trashed_check = QCheckBox("Include Trashed")
        self.include_untitled_albums_check = QCheckBox("Include Untitled Albums")
        self.include_untitled_albums_check.setChecked(True)
        self.include_unmatched_check = QCheckBox("Include Unmatched")
        self.from_album_name_edit = QLineEdit()
        self.partner_shared_album_edit = QLineEdit()
        self.sync_albums_check = QCheckBox("Sync Albums")
        self.sync_albums_check.setChecked(True)
        self.takeout_tag_check = QCheckBox("Takeout Tag")
        self.takeout_tag_check.setChecked(True)
        self.people_tag_check = QCheckBox("People Tag")
        self.people_tag_check.setChecked(True)
        self.session_tag_check = QCheckBox("Session Tag")



        def add_form_row(form, widget, tooltip):
            row = QHBoxLayout()
            row.addWidget(widget)
            row.addWidget(create_info_icon(tooltip))
            row.addStretch()
            form.addRow(row)

        # add_form_row(core_form, self.create_albums_check, "Create albums in Immich based on Takeout albums.") #Removed
        # add_form_row(core_form, self.auto_archive_check, "Automatically archive uploaded assets in Immich.") #Removed
        # add_form_row(core_form, self.untitled_albums_check, "Keep albums that have no title (usually event albums).")#Removed
        add_form_row(core_form, self.takeout_dry_run_check, "Simulate the upload without actually transferring files.")
        add_form_row(core_form, self.include_archived_check, "Include archived photos.")
        add_form_row(core_form, self.include_trashed_check, "Include trashed photos.")
        add_form_row(core_form, self.include_untitled_albums_check, "Include photos from untitled albums.")
        add_form_row(core_form, self.include_unmatched_check, "Include photos without matching JSON.")
        add_form_row(core_form, self.sync_albums_check, "Create Immich albums to match Takeout albums.")
        add_form_row(core_form, self.takeout_tag_check, "Add a takeout tag to uploaded photos.")
        add_form_row(core_form, self.people_tag_check, "Add people tags based on Takeout data.")
        add_form_row(core_form, self.session_tag_check, "Add a session tag to uploaded photos.")
        core_form.addRow("From Album Name:", self.from_album_name_edit)
        core_form.addRow("Partner Shared Album:", self.partner_shared_album_edit)



        core_group.setLayout(core_form)
        layout.addWidget(core_group)
        layout.addWidget(self.run_takeout_button)

        #Remove advanced options
        # adv_group = QGroupBox("Advanced Options")
        # adv_group.setObjectName("Advanced Options")
        # adv_group.setCheckable(True)
        # adv_group.setChecked(False)
        # adv_form = QFormLayout()

        # self.missing_json_check = QCheckBox("Upload Missing JSON")
        # self.album_folder_check = QCheckBox("Use Album Folder as Name")
        # self.discard_archived_check = QCheckBox("Discard Archived Photos")

        # add_form_row(adv_form, self.missing_json_check, "Upload JSON files even if corresponding media is missing.")
        # add_form_row(adv_form, self.album_folder_check, "Use the name of the Takeout album folder as the album name in Immich.")
        # add_form_row(adv_form, self.discard_archived_check, "Do not upload photos that are marked as archived in Takeout data.")
        # adv_group.setLayout(adv_form)
        # layout.addWidget(adv_group)

        # Wrap in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(layout)
        scroll_area.setWidget(scroll_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def connect_signals(self):
        self.browse_btn.clicked.connect(self.browse_takeout_source)
        self.zip_radio.toggled.connect(self.update_browse_mode)
        self.folder_radio.toggled.connect(self.update_browse_mode)
        self.run_takeout_button.clicked.connect(self.run_command)
        self.source_path_edit.textChanged.connect(self.emit_update_preview)

        # Connect other checkbox/option changes to update preview
        # self.create_albums_check.toggled.connect(self.emit_update_preview) #Removed
        # self.auto_archive_check.toggled.connect(self.emit_update_preview) #Removed
        # self.untitled_albums_check.toggled.connect(self.emit_update_preview) #Removed
        self.takeout_dry_run_check.toggled.connect(self.emit_update_preview)
        # self.missing_json_check.toggled.connect(self.emit_update_preview) #Removed
        # self.album_folder_check.toggled.connect(self.emit_update_preview) #Removed
        # self.discard_archived_check.toggled.connect(self.emit_update_preview) #Removed
        self.include_archived_check.toggled.connect(self.emit_update_preview)
        self.include_trashed_check.toggled.connect(self.emit_update_preview)
        self.include_untitled_albums_check.toggled.connect(self.emit_update_preview)
        self.include_unmatched_check.toggled.connect(self.emit_update_preview)
        self.from_album_name_edit.textChanged.connect(self.emit_update_preview)
        self.partner_shared_album_edit.textChanged.connect(self.emit_update_preview)
        self.sync_albums_check.toggled.connect(self.emit_update_preview)
        self.takeout_tag_check.toggled.connect(self.emit_update_preview)
        self.people_tag_check.toggled.connect(self.emit_update_preview)
        self.session_tag_check.toggled.connect(self.emit_update_preview)

    def emit_update_preview(self):
        self.update_command_preview_signal.emit()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            # Handle dropping multiple files/folders
            current_text = self.source_path_edit.text()
            separator = "; " if current_text else ""
            self.source_path_edit.setText(current_text + separator + "; ".join(paths))
            event.acceptProposedAction()
            self.emit_update_preview()


    def browse_takeout_source(self):
        if self.zip_radio.isChecked():
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Google Takeout ZIPs", "", "ZIP Files (*.zip)"
            )
            if files:
                self.source_path_edit.setText("; ".join(files))
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Extracted Folder")
            if folder:
                self.source_path_edit.setText(folder)
        self.emit_update_preview()

    def update_browse_mode(self):
        checked = self.zip_radio.isChecked()
        self.source_path_edit.clear()
        self.browse_btn.setText("Browse ZIPs" if checked else "Browse Folder")
        self.emit_update_preview()

    def run_command(self):
        # Disable the button while the command is running.
        self.run_takeout_button.setEnabled(False)
        command_options = self.get_takeout_values()
        self.run_command_signal.emit(command_options)

    def load_settings(self):
        # Use the settings manager
        settings = self.settings_manager.settings
        self.zip_radio.setChecked(settings.value("google_takeout_zip_radio", True, type=bool))
        self.folder_radio.setChecked(settings.value("google_takeout_folder_radio", False, type=bool))
        self.update_browse_mode()  # To set the initial browse button text
        self.source_path_edit.setText(settings.value("google_takeout_source_path", ""))
        # self.create_albums_check.setChecked(settings.value("google_takeout_create_albums", True, type=bool)) #Removed
        # self.auto_archive_check.setChecked(settings.value("google_takeout_auto_archive", True, type=bool))#Removed
        # self.untitled_albums_check.setChecked(settings.value("google_takeout_untitled_albums", False, type=bool))#Removed
        self.takeout_dry_run_check.setChecked(settings.value("google_takeout_dry_run", False, type=bool))
        # self.missing_json_check.setChecked(settings.value("google_takeout_missing_json", False, type=bool))#Removed
        # self.album_folder_check.setChecked(settings.value("google_takeout_album_folder_name", False, type=bool))#Removed
        # self.discard_archived_check.setChecked(settings.value("google_takeout_discard_archived", False, type=bool))#Removed

        # Load advanced group checked state
        # adv_group_checked = settings.value("google_takeout_adv_group_checked", False, type=bool) #Removed
        # adv_group = self.findChild(QGroupBox, "Advanced Options")
        # if adv_group:
        #     adv_group.setChecked(adv_group_checked)

        #New fields
        self.include_archived_check.setChecked(settings.value("google_takeout_include_archived", True, type=bool))
        self.include_trashed_check.setChecked(settings.value("google_takeout_include_trashed", False, type=bool))
        self.include_untitled_albums_check.setChecked(settings.value("google_takeout_include_untitled_albums", True, type=bool))
        self.include_unmatched_check.setChecked(settings.value("google_takeout_include_unmatched",False,type=bool))
        self.from_album_name_edit.setText(settings.value("google_takeout_from_album_name", ""))
        self.partner_shared_album_edit.setText(settings.value("google_takeout_partner_shared_album", ""))
        self.sync_albums_check.setChecked(settings.value("google_takeout_sync_albums", True, type=bool))
        self.takeout_tag_check.setChecked(settings.value("google_takeout_takeout_tag", True, type=bool))
        self.people_tag_check.setChecked(settings.value("google_takeout_people_tag",True,type=bool))
        self.session_tag_check.setChecked(settings.value("google_takeout_session_tag", False, type=bool))


    def get_takeout_values(self):
        # Helper method
        return {
            "source_path": self.source_path_edit.text(),
            "zip_mode": self.zip_radio.isChecked(),
            # "create_albums": self.create_albums_check.isChecked(), #Removed
            # "auto_archive": self.auto_archive_check.isChecked(),#Removed
            # "keep_untitled_albums": self.untitled_albums_check.isChecked(),#Removed
            "dry_run": self.takeout_dry_run_check.isChecked(),
            # "upload_missing_json": self.missing_json_check.isChecked(),#Removed
            # "use_album_folder_name": self.album_folder_check.isChecked(),#Removed
            # "discard_archived": self.discard_archived_check.isChecked(),#Removed
            # "adv_group_checked": self.findChild(QGroupBox, "Advanced Options").isChecked()#Removed
             "include_archived" : self.include_archived_check.isChecked(),
             "include_trashed" : self.include_trashed_check.isChecked(),
             "include_untitled_albums" : self.include_untitled_albums_check.isChecked(),
             "include_unmatched" : self.include_unmatched_check.isChecked(),
             "from_album_name" : self.from_album_name_edit.text(),
             "partner_shared_album" : self.partner_shared_album_edit.text(),
             "sync_albums" : self.sync_albums_check.isChecked(),
             "takeout_tag" : self.takeout_tag_check.isChecked(),
             "people_tag" : self.people_tag_check.isChecked(),
             "session_tag" : self.session_tag_check.isChecked()
        }