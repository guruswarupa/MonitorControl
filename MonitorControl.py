import sys
import subprocess
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QComboBox, QMessageBox, QGridLayout, QGroupBox, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt

class MonitorManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Monitor Manager")
        self.setGeometry(100, 100, 500, 400)
        
        self.initUI()
        
    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QGridLayout(main_widget)

        # Detect connected monitors
        self.connected_monitors = self.detect_connected_monitors()
        self.resolution_widgets = {}

        row = 0
        for monitor in self.connected_monitors:
            monitor_label = QLabel(f"{monitor} Resolution:")
            monitor_resolution_var = QComboBox()
            monitor_resolution_var.setFixedWidth(150)
            monitor_resolutions = self.get_unique_resolutions(monitor)
            monitor_resolution_var.addItems(monitor_resolutions)
            monitor_resolution_var.setCurrentText(self.get_current_resolution(monitor))

            layout.addWidget(monitor_label, row, 0)
            layout.addWidget(monitor_resolution_var, row, 1)
            self.resolution_widgets[monitor] = monitor_resolution_var
            row += 1

        # Add set resolutions button
        self.set_resolutions_button = QPushButton("Set Resolutions")
        self.set_resolutions_button.setFixedWidth(150)
        self.set_resolutions_button.clicked.connect(self.set_resolutions)
        layout.addWidget(self.set_resolutions_button, row, 1)
        row += 1

        # Group related buttons for display configuration
        resolution_group = QGroupBox("Display Actions")
        resolution_layout = QVBoxLayout()
        resolution_group.setLayout(resolution_layout)

        duplicate_button = QPushButton("Duplicate Displays")
        duplicate_button.setFixedWidth(150)
        duplicate_button.clicked.connect(self.duplicate_displays)
        resolution_layout.addWidget(duplicate_button)

        extend_button = QPushButton("Extend Displays")
        extend_button.setFixedWidth(150)
        extend_button.clicked.connect(self.extend_displays)
        resolution_layout.addWidget(extend_button)

        layout.addWidget(resolution_group, row, 0, 1, 2)
        row += 1

        # Add display control buttons
        display_group = QGroupBox("Display Controls")
        display_layout = QVBoxLayout()
        display_group.setLayout(display_layout)

        self.enable_primary_button = QPushButton("Enable Primary Monitor")
        self.enable_primary_button.setFixedWidth(200)
        self.enable_primary_button.clicked.connect(self.enable_primary_monitor)
        display_layout.addWidget(self.enable_primary_button)

        self.enable_secondary_button = QPushButton("Enable Secondary Monitor")
        self.enable_secondary_button.setFixedWidth(200)
        self.enable_secondary_button.clicked.connect(self.enable_secondary_monitor)
        display_layout.addWidget(self.enable_secondary_button)

        self.auto_button = QPushButton("Auto Detect Displays")
        self.auto_button.setFixedWidth(200)
        self.auto_button.clicked.connect(self.auto_detect_displays)
        display_layout.addWidget(self.auto_button)

        self.disable_primary_button = QPushButton("Disable Primary Monitor")
        self.disable_primary_button.setFixedWidth(200)
        self.disable_primary_button.clicked.connect(self.disable_primary_monitor)
        display_layout.addWidget(self.disable_primary_button)

        self.disable_secondary_button = QPushButton("Disable Secondary Monitor")
        self.disable_secondary_button.setFixedWidth(200)
        self.disable_secondary_button.clicked.connect(self.disable_secondary_monitor)
        display_layout.addWidget(self.disable_secondary_button)

        layout.addWidget(display_group, row, 0, 1, 2)
        row += 1

        # Add quit button
        self.quit_button = QPushButton("Quit")
        self.quit_button.setFixedWidth(100)
        self.quit_button.clicked.connect(self.close)
        layout.addWidget(self.quit_button, row, 1, Qt.AlignRight)

        # Add vertical spacer for better spacing
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), row, 0, 1, 2)

    def execute_command(self, command):
        try:
            subprocess.check_call(command.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Command Error", f"An error occurred while executing the command: {e}")
            print(f"Command failed: {command}")
            print(e)

    def duplicate_displays(self):
        for monitor in self.connected_monitors:
            if monitor != "eDP-1":
                self.execute_command(f"xrandr --output {monitor} --same-as eDP-1")

    def extend_displays(self):
        previous_monitor = None
        for monitor in self.connected_monitors:
            if previous_monitor:
                self.execute_command(f"xrandr --output {monitor} --right-of {previous_monitor}")
            previous_monitor = monitor

    def auto_detect_displays(self):
        self.execute_command("xrandr --auto")

        if len(self.connected_monitors) > 1:
            common_resolutions = self.get_common_resolutions(self.connected_monitors)
            if common_resolutions:
                highest_common_resolution = common_resolutions[-1]
                print(f"Setting all monitors to {highest_common_resolution}")
                for monitor in self.connected_monitors:
                    self.execute_command(f"xrandr --output {monitor} --mode {highest_common_resolution}")
            else:
                QMessageBox.information(self, "Resolution Info", "No common resolution found among connected monitors.")

    def disable_primary_monitor(self):
        self.execute_command("xrandr --output eDP-1 --off")

    def disable_secondary_monitor(self):
        for monitor in self.connected_monitors:
            if monitor != "eDP-1":
                self.execute_command(f"xrandr --output {monitor} --off")

    def enable_primary_monitor(self):
        self.execute_command("xrandr --output eDP-1 --auto")

    def enable_secondary_monitor(self):
        for monitor in self.connected_monitors:
            if monitor != "eDP-1":
                common_resolutions = self.get_common_resolutions([monitor, 'eDP-1'])
                if common_resolutions:
                    highest_common_resolution = common_resolutions[-1]
                    self.execute_command(f"xrandr --output {monitor} --mode {highest_common_resolution}")
                    print(f"Setting {monitor} to the highest common resolution: {highest_common_resolution}")
                else:
                    self.execute_command(f"xrandr --output {monitor} --auto")

    def set_resolutions(self):
        base_resolution = None
        for monitor, widget in self.resolution_widgets.items():
            resolution = widget.currentText()
            if base_resolution is None:
                base_resolution = resolution
            print(f"Setting {monitor} to {resolution}")
            self.execute_command(f"xrandr --output {monitor} --mode {resolution}")
        
        if base_resolution:
            base_width, base_height = map(int, base_resolution.split('x'))
            for monitor in self.connected_monitors:
                current_resolution = self.get_current_resolution(monitor)
                current_width, current_height = map(int, current_resolution.split('x'))
                if current_width > base_width or current_height > base_height:
                    scale_factor_x = base_width / current_width
                    scale_factor_y = base_height / current_height
                    scale_factor = min(scale_factor_x, scale_factor_y)
                    print(f"Scaling {monitor} by {scale_factor}")
                    self.execute_command(f"xrandr --output {monitor} --scale {scale_factor}x{scale_factor}")

    def detect_connected_monitors(self):
        output = subprocess.check_output("xrandr").decode("utf-8")
        print(f"xrandr output for detecting monitors:\n{output}")
        matches = re.findall(r"(\w+-\d+) connected", output)
        print(f"Connected monitors: {matches}")
        return matches

    def get_current_resolution(self, monitor):
        output = subprocess.check_output("xrandr").decode("utf-8")
        print(f"Current xrandr output: {output}")
        match = re.search(rf"{monitor} connected primary (\d+x\d+)", output)
        if not match:
            match = re.search(rf"{monitor} connected (\d+x\d+)", output)
        return match.group(1) if match else "Unknown"

    def get_unique_resolutions(self, monitor):
        output = subprocess.check_output("xrandr").decode("utf-8")
        print(f"Resolutions for {monitor}:")
        print(output)
        matches = re.findall(rf"{monitor} connected.*?\n((?:\s+\d+x\d+.*?\n)+)", output, re.DOTALL)
        if matches:
            resolutions = re.findall(r"(\d+x\d+)", matches[0])
            unique_resolutions = list(dict.fromkeys(resolutions))
            print(f"Unique resolutions for {monitor}: {unique_resolutions}")
            return unique_resolutions
        else:
            return ["No resolutions found"]

    def get_common_resolutions(self, monitors):
        if not monitors:
            return []
        
        common_resolutions = set(self.get_unique_resolutions(monitors[0]))
        for monitor in monitors[1:]:
            common_resolutions &= set(self.get_unique_resolutions(monitor))
        
        common_resolutions = list(common_resolutions)
        common_resolutions.sort(key=lambda x: (int(x.split('x')[0]), int(x.split('x')[1])))
        return common_resolutions

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MonitorManagerApp()
    window.show()
    sys.exit(app.exec_())
