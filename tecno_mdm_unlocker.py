import subprocess
import sys
import os
import platform
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QTextEdit, QMessageBox, QSystemTrayIcon, QStatusBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import json

class ADBWorker(QThread):
    """Worker thread to handle ADB commands in the background"""
    status_message = pyqtSignal(str)
    error_message = pyqtSignal(str)

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self.running = False

    def run(self):
        try:
            self.running = True
            # Execute ADB command
            result = subprocess.run(
                self.cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Decode output
            try:
                output = result.stdout
                error = result.stderr
            except Exception as e:
                output = str(e)
            
            self.status_message.emit(f"ADB Command Output:\n{output}\n" + f"Error:\n{error}" if error else f"Command Output:\n{output}")
            self.error_message.emit(f"Error: {output}" if output else f"Error: {result.stderr.decode()}")
            
        except Exception as e:
            self.error_message.emit(f"Exception: {str(e)}")
        finally:
            self.running = False

class MDMUnlockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tecno Spark 40 (KM5) MDM & Security Plugin Unlocker")
        self.setMinimumSize(900, 600)
        
        # Central Widget Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        main_layout = QVBoxLayout(central_widget)
        self.main_layout = main_layout
        
        # Title Label
        title_label = QLabel("Tecno Spark 40 (KM5) MDM Unlocker")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; font-family: Arial;")
        main_layout.addWidget(title_label)
        
        # Instructions
        instructions = QLabel("This app attempts to bypass MDM locks and remove security plugins using ADB commands.")
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)
        
        # Input Section
        input_group = QVBoxLayout()
        
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Enter Device Serial Number (e.g., A1B2C3D4)")
        self.serial_input.setMinimumHeight(40)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter Device IP Address (e.g., 192.168.1.100)")
        self.ip_input.setMinimumHeight(40)
        
        # Status Text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("background-color: #f0f0f0; font-family: monospace;")
        
        # Buttons
        self.connect_btn = QPushButton("Check Device Connection")
        self.unlock_btn = QPushButton("Remove MDM & Security Plugin")
        
        # Layout Logic
        input_group.addWidget(self.serial_input)
        input_group.addWidget(self.ip_input)
        input_group.addSpacing(10)
        input_group.addWidget(self.status_text)
        input_group.addStretch()
        input_group.addWidget(self.connect_btn)
        input_group.addWidget(self.unlock_btn)
        
        main_layout.addLayout(input_group)
        
        # Connect Signals
        self.connect_btn.clicked.connect(self.check_connection)
        self.unlock_btn.clicked.connect(self.run_unlocker)
        
        # ADB Server Management
        self.adb_server_thread = QThread()
        self.adb_server_thread.moveToThread(self)
        
        # ADB Commands
        self.adb_cmd = "adb server"
        self.adb_cmd_start = f"adb server start"
        self.adb_cmd_stop = f"adb server stop"
        self.adb_cmd_disconnect = f"adb disconnect"
        
        # ADB commands for MDM Removal
        self.mdm_uninstall_cmd = """adb shell cmd package uninstall -k --user 0 com.tecno.android.security"""
        
    def start_adb_server(self):
        """Starts the ADB server"""
        try:
            self.adb_server_thread.start()
            self.status_message.emit("ADB Server started.")
            return True
        except Exception as e:
            self.status_message.emit(f"Failed to start ADB Server: {e}")
            return False

    def stop_adb_server(self):
        """Stops the ADB server"""
        try:
            if self.adb_server_thread.isRunning():
                self.adb_server_thread.stop()
                self.adb_server_thread.wait(1000)
            return True
        except Exception as e:
            self.status_message.emit(f"Failed to stop ADB Server: {e}")
            return False

    def check_connection(self):
        """Checks if ADB is connected to the device"""
        if not self.start_adb_server():
            return
        
        cmd = f"adb devices"
        self.worker = ADBWorker(cmd, self)
        self.worker.status_message.connect(self.update_status)
        self.worker.error_message.connect(self.update_error)
        self.worker.start()
        
        self.status_message.emit("Checking connection...")

    def update_status(self, message):
        """Updates the status text with ADB output"""
        self.status_text.append(message)
        self.status_text.moveCursor(QTextCursor.End)
        self.unlock_btn.setEnabled(False)

    def update_error(self, message):
        """Updates the error text"""
        QMessageBox.critical(self, "Connection Error", message)
        self.unlock_btn.setEnabled(False)

    def run_unlocker(self):
        """Executes the MDM removal commands"""
        serial = self.serial_input.text().strip()
        ip = self.ip_input.text().strip()
        
        if not serial and not ip:
            QMessageBox.warning(self, "Missing Info", "Please enter a Serial Number or IP Address.")
            return

        if not self.start_adb_server():
            return

        self.status_message.emit("Starting MDM Unlocker process...")
        
        # Step 1: Connect to device
        cmd = f"adb connect {ip}" if ip else f"adb connect {serial}"
        self.worker = ADBWorker(cmd, self)
        self.worker.status_message.connect(self.update_status)
        self.worker.error_message.connect(self.update_error)
        self.worker.start()

        # Step 2: Check connection status
        cmd = "adb devices"
        self.worker = ADBWorker(cmd, self)
        self.worker.status_message.connect(self.update_status)
        self.worker.error_message.connect(self.update_error)
        self.worker.start()

        # Step 3: Uninstall MDM Package
        cmd = f"{self.mdm_uninstall_cmd}"
        self.worker = ADBWorker(cmd, self)
        self.worker.status_message.connect(self.update_status)
        self.worker.error_message.connect(self.update_error)
        self.worker.start()

        # Step 4: Reboot device
        cmd = "adb reboot"
        self.worker = ADBWorker(cmd, self)
        self.worker.status_message.connect(self.update_status)
        self.worker.error_message.connect(self.update_error)
        self.worker.start()
        
        # Wait for reboot
        self.status_message.emit("Device is rebooting. Please wait 2 minutes...")
        QTimer.singleShot(120000, lambda: self.stop_adb_server())

    def update_status(self, message):
        """Updates the status text with output"""
        self.status_text.append(message)
        self.status_text.moveCursor(QTextCursor.End)
        self.unlock_btn.setEnabled(True)

    def update_error(self, message):
        """Updates the error text"""
        QMessageBox.critical(self, "Error", message)
        self.unlock_btn.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    # Set Window Icon (Optional - can be a path to an icon file)
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = MDMUnlockApp()
    window.show()
    
    sys.exit(app.exec())
