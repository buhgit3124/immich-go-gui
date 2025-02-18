# immich_go_gui/core/command_builder.py
import shlex
from core.binary_manager import BinaryManager

class CommandBuilder:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.binary_manager = BinaryManager()

    def build_command(self, current_tab_text, main_window):
        """Builds the command string based on current tab and settings."""
        parts = []

        parts.append(self.binary_manager.binary_path)  # Binary path first

        # --- Global Flags --- (Always come before the subcommand)
        parts += self._get_config_options(main_window.config_tab)

        if current_tab_text == "Google Takeout":
            parts += self._get_google_takeout_options(main_window.takeout_tab)
        elif current_tab_text == "Local Upload":
            parts += self._get_local_upload_options(main_window.local_upload_tab)

        # Quote for accurate preview
        quoted_parts = [shlex.quote(part) for part in parts]
        command_text = " ".join(quoted_parts)

        # Error messages
        if not main_window.config_tab.server_url_edit.text():
            command_text += "\n\n⚠️ MISSING SERVER URL"
        if not main_window.config_tab.api_key_edit.text():
            command_text += "\n⚠️ MISSING API KEY"

        return command_text

    def _get_config_options(self, config_tab):
        """Gets general configuration options (Global Flags)."""
        values = config_tab.get_config_values()
        options = []
        if values["server_url"]:
            options.append(f"--server={values['server_url']}")
        if values["api_key"]:
            options.append(f"--api-key={values['api_key']}")  # Correct flag name
        if values["skip_ssl"]:
            options.append("--skip-verify-ssl")
        if values["api_url"]:
             options.append(f"--api-url={values['api_url']}")
        if values["client_timeout"] != 1:
            options.append(f"--client-timeout={values['client_timeout']}m")
        if values["log_level"] != "ERROR":
            options.append(f"--log-level={values['log_level']}")
        if values["device_uuid"]:
            options.append(f"--device-uuid={values['device_uuid']}")
        return options

    def _get_google_takeout_options(self, takeout_tab):
        """Gets options for Google Takeout (with correct flag names)."""
        values = takeout_tab.get_takeout_values()
        options = ["upload"]  # Start with 'upload'

        # --- Positional Argument (ZIP file(s) or folder) COMES RIGHT AFTER SUBCOMMAND---
        source_path = values["source_path"]
        if source_path:
            if values["zip_mode"]:
                # Split multiple ZIP files correctly
                zip_files = [path.strip() for path in source_path.split(";") if path.strip()]
                options.append("from-google-photos") #Subcommand
                options.extend(zip_files)  # Add *before* flags
            else:
                options.append("from-google-photos") #Subcommand
                options.append(source_path)  # Single folder path *before* flags

        # --- Subcommand-Specific Flags --- (After the path)
        if values["dry_run"]:
            options.append("--dry-run")
        if not values["include_archived"]:
            options.append("--no-include-archived")
        if values["include_trashed"]:
            options.append("--include-trashed")
        if not values["include_untitled_albums"]:
             options.append("--no-include-untitled-albums")
        if values["include_unmatched"]:
            options.append("--include-unmatched")
        if values["from_album_name"]:
            options.append(f"--from-album-name={values['from_album_name']}")
        if values["partner_shared_album"]:
             options.append(f"--partner-shared-album={values['partner_shared_album']}")
        if not values["sync_albums"]:
            options.append("--no-sync-albums")
        if values["takeout_tag"]:
            options.append("--takeout-tag")
        if not values["people_tag"]:
            options.append("--no-people-tag")
        if values["session_tag"]:
             options.append("--session-tag")

        return options

    def _get_local_upload_options(self, local_upload_tab):
        """Gets options for Local Upload (with correct flag names)."""
        values = local_upload_tab.get_local_upload_values()
        options = ["upload"]  # Start with 'upload'

        # --- Positional Argument (Folder path) COMES RIGHT AFTER SUBCOMMAND ---
        if values["local_path"]:
            options.append("from-folder") #Subcommand
            options.append(values["local_path"])  # Add path *before* flags

        # --- Subcommand-Specific Flags --- (After the path)
        if values["dry_run"]:
            options.append("--dry-run")
        if values["recursive"]:
            options.append("--recursive")
        if values["date_filter_enabled"]:
            options.append(f"--date-range={values['start_date']},{values['end_date']}")
        if values["type_filter_enabled"] and values["file_extensions"]:
            exts = values["file_extensions"].replace(" ", "").strip()
            options.append(f'--include-extensions="{exts}"')
        if values["album_name"]:
            options.append(f'--into-album="{values["album_name"]}"')

        if values["date_from_name"]:
            options.append(f'--date-from-name')
        # if values["folder_as_album"]: # Removed
        #     options.append(f'--folder-as-album={values["folder_as_album"]}')
        return options