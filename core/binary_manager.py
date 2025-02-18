# immich_go_gui/core/binary_manager.py

import os
import sys
import platform
import requests
import io
import zipfile  # Import zipfile
import tarfile # Import tarfile
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PySide6.QtCore import QThread, Signal
import subprocess #Import subprocess

class BinaryManager:
    def __init__(self):
        self.binary_path = self._get_binary_path()

    def _get_binary_path(self):
        """Determine the correct binary path based on OS."""
        binary_folder = os.path.abspath(os.path.join(os.getcwd(), "immich-go"))
        binary_filename = "immich-go.exe" if sys.platform.startswith("win") else "immich-go"
        return os.path.join(binary_folder, binary_filename)

    def get_latest_release_info(self):
        """Fetch the latest release information from GitHub."""
        try:
            api_url = "https://api.github.com/repos/simulot/immich-go/releases/latest"
            response = requests.get(api_url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            release_data = response.json()
            return release_data['tag_name']
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch release information: {e}")
            return None

    def get_download_url(self, version=None):
        """Generate the appropriate download URL based on the system."""
        os_name = sys.platform
        arch = platform.machine().lower()

        download_mapping = {
            ('win32', 'amd64'): 'immich-go_Windows_x86_64.zip',
            ('win32', 'x86_64'): 'immich-go_Windows_x86_64.zip',
            ('win32', 'arm64'): 'immich-go_Windows_arm64.zip',
            ('darwin', 'x86_64'): 'immich-go_Darwin_x86_64.tar.gz',
            ('darwin', 'arm64'): 'immich-go_Darwin_arm64.tar.gz',
            ('linux', 'x86_64'): 'immich-go_Linux_x86_64.tar.gz',
            ('linux', 'arm64'): 'immich-go_Linux_arm64.tar.gz',
            ('freebsd', 'x86_64'): 'immich-go_Freebsd_x86_64.tar.gz'
        }

        if arch in ['x64', 'x86_64']:
            arch = 'x86_64'

        key = (os_name, arch)
        if key in download_mapping:
            version = version or self.get_latest_release_info() or '0.22.1'
            filename = download_mapping[key]
            return f'https://github.com/simulot/immich-go/releases/download/{version}/{filename}'
        return None

    def update_binary(self, progress_callback):
        """Downloads and updates the immich-go binary if necessary."""
        binary_folder = os.path.dirname(self.binary_path)
        if not os.path.exists(binary_folder):
            os.makedirs(binary_folder)

        if not os.path.exists(self.binary_path):
            if not self.download_binary(progress_callback):
                return False  # Download failed

        return True #Binary exists


    def download_binary(self, progress_callback):
        """Downloads the immich-go binary."""
        download_url = self.get_download_url()
        if not download_url:
            QMessageBox.critical(None, "Download Error", "Could not determine download URL.")
            return False

        # Use a QThread for downloading to avoid freezing the UI
        self.download_thread = DownloadThread(download_url)
        self.download_thread.download_progress.connect(lambda val, total: progress_callback(val, total))
        self.download_thread.download_complete.connect(self.handle_download_complete)
        self.download_thread.download_error.connect(self.handle_download_error)
        self.download_thread.start()
        return True



    def handle_download_complete(self, content, download_url):
        """Handles the completion of the binary download."""
        try:
            if download_url.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    for filename in z.namelist():
                        if filename.endswith('immich-go') or filename.endswith('immich-go.exe'):
                            with z.open(filename) as source, open(self.binary_path, 'wb') as target:
                                target.write(source.read())
                            break  # Exit loop after extracting the binary
            elif download_url.endswith('.tar.gz'):
                with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as tar:
                    for member in tar.getmembers():
                        if member.name.endswith('immich-go') or member.name.endswith('immich-go.exe'):
                            source = tar.extractfile(member)
                            with open(self.binary_path, 'wb') as target:
                                target.write(source.read())
                            break # Exit loop
            else:
                QMessageBox.critical(None, "Extraction Error", "Unsupported archive type.")
                return

            if not sys.platform.startswith("win"):
                os.chmod(self.binary_path, 0o755)

            QMessageBox.information(None, "Download Complete", "immich-go binary downloaded successfully.")

        except Exception as e:
            QMessageBox.critical(None, "Extraction Error", f"Failed to extract binary: {e}")



    def handle_download_error(self, error):
        """Handles errors during the binary download."""
        QMessageBox.critical(None, "Download Error", f"Failed to download binary: {error}")



class DownloadThread(QThread):
    """Thread for downloading files in the background."""
    download_progress = Signal(int, int)  # value, total_size
    download_complete = Signal(bytes, str) # Pass back the URL with downloaded content
    download_error = Signal(str)

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            content = io.BytesIO() # Store the content

            for data in response.iter_content(chunk_size=8192):
                downloaded_size += len(data)
                content.write(data)
                self.download_progress.emit(downloaded_size, total_size)

            # Pass the URL with the downloaded content
            self.download_complete.emit(content.getvalue(), self.download_url)

        except requests.exceptions.RequestException as e:
            self.download_error.emit(str(e))