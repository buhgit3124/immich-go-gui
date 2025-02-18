# immich_go_gui/core/settings_manager.py

from PySide6.QtCore import QSettings, QDate

class SettingsManager:
    def __init__(self):
        self.settings = QSettings("YourOrganization", "ImmichGoGUI")

    def save_settings(self, main_window):
        """Saves all application settings."""
        config_values = main_window.config_tab.get_config_values()
        takeout_values = main_window.takeout_tab.get_takeout_values()
        local_upload_values = main_window.local_upload_tab.get_local_upload_values()

        for key, value in config_values.items():
            self.settings.setValue(key, value)
        for key, value in takeout_values.items():
            self.settings.setValue(f"google_takeout_{key}", value) # Prefix keys
        for key, value in local_upload_values.items():
            # Special handling for date values
            if key in ("start_date", "end_date") and value is not None:
                self.settings.setValue(f"local_upload_{key}", QDate.fromString(value, "yyyy-MM-dd"))
            elif key not in ("start_date", "end_date") and key != "folder_as_album": # Remove folder_as_album
                self.settings.setValue(f"local_upload_{key}", value) #Prefix keys


    def load_settings(self, main_window):
        """Loads all application settings."""
        main_window.config_tab.load_settings()  # Delegate to tabs
        main_window.takeout_tab.load_settings()
        main_window.local_upload_tab.load_settings()