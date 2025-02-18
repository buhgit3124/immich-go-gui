# immich_go_gui/core/process_manager.py

import subprocess
import sys
import shlex
import psutil
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtWidgets import QMessageBox

class ProcessManager(QObject):  # Inherit from QObject for signals

    process_finished = Signal() # Signal to emit on process completion

    def __init__(self):
        super().__init__()
        self.running_process = None
        self.check_process_timer = None


    def run_command(self, command, callback=None):
        """Runs the given command in a new terminal window."""
        try:
            if sys.platform.startswith("win"):
                cmd_string = subprocess.list2cmdline(command)
                proc = subprocess.Popen(
                    ['cmd', '/c', 'start', 'cmd', '/k', cmd_string],
                    shell=True,  # Use shell=True for 'start' command
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.running_process = proc.pid # Store the PID

            elif sys.platform.startswith("darwin"):
                apple_script = f'tell application "Terminal" to do script "{shlex.join(command)}; exec bash"'
                proc = subprocess.Popen(["osascript", "-e", apple_script])
                self.running_process = proc  # Store Popen object

            else:  # Linux
                terminals = [
                    ("gnome-terminal", "--", "bash", "-c", f"{shlex.join(command)}; exec bash"),
                    ("konsole", "-e", "bash", "-c", f"{shlex.join(command)}; exec bash"),
                    ("xfce4-terminal", "-e", "bash", "-c", f"{shlex.join(command)}; exec bash"),
                    ("xterm", "-hold", "-e", shlex.join(command))
                ]
                for term in terminals:
                    try:
                        proc = subprocess.Popen(term)
                        self.running_process = proc # Store Popen object
                        break
                    except FileNotFoundError:
                        continue
                else:
                    QMessageBox.critical(None, "Error", "No suitable terminal emulator found.")
                    return

            # Use a QTimer to periodically check if process is still running
            self.check_process_timer = QTimer()
            self.check_process_timer.timeout.connect(self.check_if_process_running)
            self.check_process_timer.start(1000)  # Check every second
            self.callback = callback # Store for later

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
            self.check_process_timer.stop()  # Stop timer
            self.running_process = None
            if self.callback: # Call the callback function
                self.callback()
            self.process_finished.emit() # Emit signal