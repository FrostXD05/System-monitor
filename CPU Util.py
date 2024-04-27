import sys
import psutil
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QThreadPool, QRunnable, QEvent
from PyQt5.QtGui import QFont

class SystemInfoWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.cpu_label_static = QLabel("CPU Info:")
        self.cpu_label = QLabel("")
        self.memory_label_static = QLabel("Memory Info:")
        self.memory_label = QLabel("")
        self.swap_label_static = QLabel("Swap Info:")
        self.swap_label = QLabel("")
        self.interface_label_static = QLabel("Interface Info:")
        self.interface_label = QLabel("")
        self.exit_button = QLabel("X")
        self.exit_button.setAlignment(Qt.AlignCenter)
        self.exit_button.setStyleSheet("background-color: red; color: white;")
        self.exit_button.installEventFilter(self)

        layout = QVBoxLayout()
        layout.addWidget(self.cpu_label_static)
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.memory_label_static)
        layout.addWidget(self.memory_label)
        layout.addWidget(self.swap_label_static)
        layout.addWidget(self.swap_label)
        layout.addWidget(self.interface_label_static)
        layout.addWidget(self.interface_label)
        layout.addWidget(self.exit_button)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)

        self.thread_pool = QThreadPool.globalInstance()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        font = QFont("Helvetica", 10)
        self.cpu_label_static.setFont(font)
        self.cpu_label.setFont(font)
        self.memory_label_static.setFont(font)
        self.memory_label.setFont(font)
        self.swap_label_static.setFont(font)
        self.swap_label.setFont(font)
        self.interface_label_static.setFont(font)
        self.interface_label.setFont(font)

        palette = self.cpu_label.palette()
        palette.setColor(palette.WindowText, Qt.white)
        self.cpu_label_static.setPalette(palette)
        self.cpu_label.setPalette(palette)
        self.memory_label_static.setPalette(palette)
        self.memory_label.setPalette(palette)
        self.swap_label_static.setPalette(palette)
        self.swap_label.setPalette(palette)
        self.interface_label_static.setPalette(palette)
        self.interface_label.setPalette(palette)

        self.setStyleSheet("background-color: black;")
        self.dragPosition = None

    def eventFilter(self, source, event):
        if source is self.exit_button and event.type() == QEvent.MouseButtonRelease:
            self.close()
            return True
        elif source is self.exit_button and event.type() == QEvent.Enter:
            self.exit_button.setStyleSheet("background-color: darkred; color: white;")
            return True
        elif source is self.exit_button and event.type() == QEvent.Leave:
            self.exit_button.setStyleSheet("background-color: red; color: white;")
            return True
        return super().eventFilter(source, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPosition = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.dragPosition is not None:
            self.move(self.pos() + event.globalPos() - self.dragPosition)
            self.dragPosition = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPosition = None

    def update_info(self):
        runnable = SystemInfoRunnable(self)
        self.thread_pool.start(runnable)

    def set_info(self, cpu_info, memory_info, swap_info, interface_info):
        self.cpu_label.setText(cpu_info)
        self.memory_label.setText(memory_info)
        self.swap_label.setText(swap_info)
        self.interface_label.setText(interface_info)

class SystemInfoRunnable(QRunnable):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def run(self):
        cpu_info = self.get_cpu_info()
        memory_info = self.get_memory_info()
        swap_info = self.get_swap_info()
        interface_info = self.get_interface_info()

        self.widget.set_info(cpu_info, memory_info, swap_info, interface_info)

    def get_cpu_info(self):
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpufreq = psutil.cpu_freq()
        cpu_percent = psutil.cpu_percent(percpu=True, interval=1)

        info = f"Physical cores: {cpu_count_physical}\n"
        info += f"Total cores: {cpu_count_logical}\n"
        info += f"Max Frequency: {cpufreq.max:.2f}Mhz\n"
        info += f"Min Frequency: {cpufreq.min:.2f}Mhz\n"
        info += f"Current Frequency: {cpufreq.current:.2f}Mhz\n"
        info += "CPU Usage Per Core:\n"
        for i, percentage in enumerate(cpu_percent):
            info += f"Core {i}: {percentage}%\n"
        info += f"Total CPU Usage: {psutil.cpu_percent()}%\n"

        return info

    def get_memory_info(self):
        svmem = psutil.virtual_memory()

        info = f"Total: {get_size(svmem.total)}\n"
        info += f"Available: {get_size(svmem.available)}\n"
        info += f"Used: {get_size(svmem.used)}\n"
        info += f"Percentage: {svmem.percent}%\n"

        return info

    def get_swap_info(self):
        swap = psutil.swap_memory()

        info = f"Total: {get_size(swap.total)}\n"
        info += f"Free: {get_size(swap.free)}\n"
        info += f"Used: {get_size(swap.used)}\n"
        info += f"Percentage: {swap.percent}%\n"

        return info

    def get_interface_info(self):
        info = ""
        for interface_name, interface in psutil.net_if_stats().items():
            info += f"Interface: {interface_name}\n"
            info += f"Is Up: {interface.isup}\n"
            info += f"MTU: {interface.mtu}\n"
            info += f"Speed: {interface.speed}\n"
            info += f" Duplex: {interface.duplex}\n"

        return info

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = SystemInfoWidget()
    widget.show()

    sys.exit(app.exec_())