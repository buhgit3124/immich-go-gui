# immich_go_gui/core/process_manager.py

import subprocess
import sys
import shlex
import psutil
import platform
import os
import tempfile
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtWidgets import QMessageBox

class ProcessManager(QObject):
    process_finished = Signal()

    def __init__(self):
        super().__init__()
        self.running_process = None
        self.check_process_timer = None

    def run_command(self, command, callback=None):
        """Runs the given command in a new terminal window."""
        try:
            # Create a temporary script file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".bat" if sys.platform.startswith("win") else ".sh") as f:
                script_path = f.name

                if sys.platform.startswith("win"):
                    # Windows batch script
                    f.write(f'@echo off\n{subprocess.list2cmdline(command)}\npause\n')
                else:
                    # Bash script (for macOS and Linux)
                    f.write(f'#!/bin/bash\n{shlex.join(command)}\nread -p "Press Enter to close..."\n')

            # Make the script executable (for macOS and Linux)
            if not sys.platform.startswith("win"):
                os.chmod(script_path, 0o755)

            # Run the script in a new terminal
            if sys.platform.startswith("win"):
                proc = subprocess.Popen(
                    ['cmd', '/c', 'start', 'cmd', '/k', script_path],
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.running_process = proc.pid

            elif sys.platform.startswith("darwin"):
                # macOS command: Use 'bash -c' to execute the script
                apple_script = f'tell application "Terminal" to do script "bash -c \\"{script_path}\\""'
                proc = subprocess.Popen(["osascript", "-e", apple_script])
                self.running_process = proc

            else:  # Linux
                # Corrected Linux commands: Execute the script using 'bash -c "script_path"'
                terminals = [
                    ("gnome-terminal", "--", "bash", "-c", f'"{script_path}"'),  # Corrected quoting
                    ("konsole", "-e", "bash", "-c", f'"{script_path}"'),       # Corrected quoting
                    ("xfce4-terminal", "--hold", "-e", "bash", "-c", f'"{script_path}"'), # Corrected quoting
                    ("xterm", "-hold", "-e", "bash", "-c", f'"{script_path}"')    # Corrected quoting
                ]
                for term in terminals:
                    try:
                        proc = subprocess.Popen(term)
                        self.running_process = proc
                        break
                    except FileNotFoundError:
                        continue
                else:
                    QMessageBox.critical(None, "Error", "No suitable terminal emulator found.")
                    return

            self.check_process_timer = QTimer()
            self.check_process_timer.timeout.connect(self.check_if_process_running)
            self.check_process_timer.start(1000)
            self.callback = callback

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to run command: {e}")
            self.running_process = None

    def check_if_process_running(self):
        """Checks if the external process is still running."""
        still_running = False
        if sys.platform.startswith("win"):
            if psutil.pid_exists(self.running_process):
                still_running = True
        else:  # Linux/macOS
            if self.running_process and self.running_process.poll() is None:
                still_running = True

        if not still_running:
            self.check_process_timer.stop()
            self.running_process = None
            if self.callback:
                self.callback()
            self.process_finished.emit()