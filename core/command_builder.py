# immich_go_gui/core/command_builder.py
import shlex

class CommandBuilder:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager

    def build_command(self, current_tab_text, main_window):
        """Builds the command string based on the current tab and settings."""
        parts = []

        if current_tab_text == "Google Takeout":
            parts += self._get_google_takeout_options(main_window.takeout_tab)
        elif current_tab_text == "Local Upload":
            parts += self._get_local_upload_options(main_window.local_upload_tab)

        # Add config options after main commands
        parts += self._get_config_options(main_window.config_tab)

        # Quote each part for an accurate command preview
        quoted_parts = [shlex.quote(part) for part in parts]
        command_text = " ".join(quoted_parts)

        # Add error messages for missing config
        if not main_window.config_tab.server_url_edit.text():
            command_text += "\n\n⚠️ MISSING SERVER URL"
        if not main_window.config_tab.api_key_edit.text():
            command_text += "\n⚠️ MISSING API KEY"

        return command_text


    def _get_config_options(self, config_tab):
        """Gets general configuration options."""
        values = config_tab.get_config_values()
        options = []
        if values["server_url"]:
            options.append(f"--server={values['server_url']}")
        if values["api_key"]:
            options.append(f"--api-key={values['api_key']}")
        if values["skip_ssl"]:
            options.append("--skip-verify-ssl")
        if values["api_url"]:
            options.append(f"--api-url={values['api_url']}")
        if values["client_timeout"] != 1:
            options.append(f"--client-timeout={values['client_timeout']}")
        if values["log_level"] != "ERROR":
            options.append(f"--log-level={values['log_level']}")
        if values["device_uuid"]:
            options.append(f"--device-uuid={values['device_uuid']}")
        return options


    def _get_google_takeout_options(self, takeout_tab):
        """Gets options specific to the Google Takeout tab."""
        values = takeout_tab.get_takeout_values()
        options = ["upload", "from-google-photos"]
        flag_options = []

        if values["create_albums"]:
            flag_options.append("--create-albums")
        if values["auto_archive"]:
            flag_options.append("--auto-archive")
        if values["keep_untitled_albums"]:
            flag_options.append("--keep-untitled-albums")
        if values["dry_run"]:
            flag_options.append("--dry-run")
        if values["upload_missing_json"]:
            flag_options.append("--upload-when-missing-JSON")
        if values["use_album_folder_name"]:
            flag_options.append("--use-album-folder-as-name")
        if values["discard_archived"]:
            flag_options.append("--discard-archived")

        source_path = values["source_path"]
        if values["zip_mode"]:
            zip_files = [path.strip() for path in source_path.split(";") if path.strip()]
            options += flag_options
            options += zip_files  # Add zip files after flags
        elif source_path:
            options += flag_options
            options.append(source_path) # Add the path at last
        else:
            options += flag_options #Add the rest of the options
        return options


    def _get_local_upload_options(self, local_upload_tab):
        """Gets options specific to the Local Upload tab."""
        values = local_upload_tab.get_local_upload_values()
        options = ["upload", "from-folder"]
        flag_options = []

        if values["date_filter_enabled"]:
            flag_options.append(f"--date-filter={values['start_date']},{values['end_date']}")
        if values["type_filter_enabled"] and values["file_extensions"]:
            exts = values["file_extensions"].replace(" ", "").strip()
            if exts:
                flag_options.append(f'--file-filter="{exts}"')

        if values["album_name"]:
            flag_options.append(f'--album="{values["album_name"]}"')
        if values["create_album_from_folder"]:
            flag_options.append("--create-album-folder")
        if values["dry_run"]:
            flag_options.append("--dry-run")

        source_path = values["local_path"]
        if source_path:
            options += flag_options
            options.append(source_path)  # Add the path at last
        else:
            options += flag_options #Add the rest of the options
        return options