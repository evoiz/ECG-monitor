import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import AutoMinorLocator
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QComboBox, QPushButton, QLineEdit, QLabel, QSlider, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from scipy.fft import fft, ifft, fftfreq
from scipy.signal import find_peaks
from tensorflow.keras.models import load_model
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = QColor(Qt.GlobalColor.gray)
        self.setFixedSize(20, 20)

    def set_color(self, color):
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.color)
        painter.drawEllipse(2, 2, 16, 16)

class ECGApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ECG Monitor")
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_data_from_api)
        self.current_file_path = None
        self.current_data = None
        self.processed_data = None
        self.error_400_shown = False
        self.fs = 125
        self.lowcut = 0.5
        self.highcut = 50
        self.init_ui()
        self.model = load_model("./model.keras")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.ecg_groupbox = QGroupBox("ECG Chart")
        layout.addWidget(self.ecg_groupbox)
        self.ecg_layout = QVBoxLayout(self.ecg_groupbox)
        
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.ax.minorticks_on()
        self.ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        self.ax.grid(which='major', linestyle='-', linewidth='0.4', color='red')
        self.ax.grid(which='minor', linestyle='-', linewidth='0.4', color=(1, 0.7, 0.7))
        self.canvas.draw_idle()
        self.ecg_layout.addWidget(self.canvas)

        self.mode_groupbox = QGroupBox("Mode")
        layout.addWidget(self.mode_groupbox)
        self.mode_layout = QVBoxLayout(self.mode_groupbox)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["online", "offline"])
        self.mode_combo.currentTextChanged.connect(self.update_mode)
        self.mode_layout.addWidget(self.mode_combo)

        self.online_groupbox = QGroupBox("Online")
        layout.addWidget(self.online_groupbox)
        self.online_layout = QHBoxLayout(self.online_groupbox)
        
        self.status_indicator = StatusIndicator()
        self.online_layout.addWidget(self.status_indicator)

        self.ip_label = QLabel("IP")
        self.online_layout.addWidget(self.ip_label)
        
        self.ip_entry = QLineEdit("127.0.0.1:3000")
        self.online_layout.addWidget(self.ip_entry)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect)
        self.online_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect)
        self.disconnect_button.setEnabled(False)
        self.online_layout.addWidget(self.disconnect_button)

        self.offline_groupbox = QGroupBox("Offline")
        layout.addWidget(self.offline_groupbox)
        self.offline_layout = QVBoxLayout(self.offline_groupbox)
        
        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.open_offline)
        self.offline_layout.addWidget(self.open_button)
        
        self.slider_label = QLabel("Number of samples: 500")
        self.offline_layout.addWidget(self.slider_label)
        
        self.lines_slider = QSlider(Qt.Orientation.Horizontal)
        self.lines_slider.setRange(100, 1000)
        self.lines_slider.setValue(500)
        self.lines_slider.valueChanged.connect(self.update_lines)
        self.offline_layout.addWidget(self.lines_slider)

        self.result_groupbox = QGroupBox("Result")
        layout.addWidget(self.result_groupbox)
        self.result_layout = QVBoxLayout(self.result_groupbox)
        
        self.heart_rate_label = QLabel("Heart Rate: -- bpm")
        self.result_layout.addWidget(self.heart_rate_label)

        self.result_label = QLabel("Result: ")
        self.result_layout.addWidget(self.result_label)

        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.analyze_current_data)
        layout.addWidget(self.analyze_button)

        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)

        self.update_mode()

    def process_ecg_data(self, data):
        if self.processed_data is None or len(data) != len(self.processed_data[0]):
            ecg_signal = np.array(data)
            filtered_ecg = self.fft_filter(ecg_signal)
            normalized_ecg = self.normalize_signal(filtered_ecg)
            threshold = 0.6 * np.max(normalized_ecg)
            peaks, _ = find_peaks(normalized_ecg, height=threshold, distance=int(0.2*self.fs))
            self.processed_data = (normalized_ecg, peaks, threshold)
        return self.processed_data

    def normalize_signal(self, signal):
        return (signal - np.min(signal)) / (np.max(signal) - np.min(signal))

    def fft_filter(self, signal):
        N = len(signal)
        yf = fft(signal)
        xf = fftfreq(N, 1/self.fs)
        mask = (np.abs(xf) > self.lowcut) & (np.abs(xf) < self.highcut)
        yf_filtered = yf * mask
        return np.real(ifft(yf_filtered))

    def draw_ecg(self, data):
        normalized_ecg, peaks, threshold = self.process_ecg_data(data)
        self.ax.clear()
        self.ax.plot(normalized_ecg)
        self.ax.plot(peaks, normalized_ecg[peaks], "x")
        self.ax.axhline(y=threshold, color='r', linestyle='--')
        self.ax.set_title('ECG Signal with Detected Peaks')
        self.ax.set_xlabel('Sample')
        self.ax.set_ylabel('Normalized Amplitude')
        self.ax.minorticks_on()
        self.ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        self.ax.grid(which='major', linestyle='-', linewidth='0.4', color='red')
        self.ax.grid(which='minor', linestyle='-', linewidth='0.4', color=(1, 0.7, 0.7))
        self.canvas.draw_idle()

    def connect(self):
        ip = self.ip_entry.text()
        self.error_400_shown = False
        self.timer.start(1000)
        self.update_connection_buttons(connected=True)
        self.ip_entry.setEnabled(False)

    def disconnect(self):
        self.timer.stop()
        self.update_connection_buttons(connected=False)
        self.ip_entry.setEnabled(True)

    def fetch_data_from_api(self):
        ip = self.ip_entry.text()
        try:
            response = requests.get(f"http://{ip}/getECGData", timeout=2.0)
            data = response.json()
            if response.status_code == 400:
                self.status_indicator.set_color(Qt.GlobalColor.red)
                if not self.error_400_shown:
                    self.show_connection_error("Bad Request: The server cannot process the request.")
                    self.error_400_shown = True
                self.handle_connection_error()
            else:
                self.status_indicator.set_color(Qt.GlobalColor.green)
                new_data = data
                if type(self.current_data)!= type(new_data) or self.current_data != new_data:
                    self.current_data = new_data
                    self.processed_data = None
                self.draw_ecg(self.current_data)
                self.analyze_data(self.current_data)
                self.error_400_shown = False
        except requests.exceptions.RequestException as e:
            self.status_indicator.set_color(Qt.GlobalColor.red)
            if not self.error_400_shown:
                self.show_connection_error(str(e))
                self.error_400_shown = True
            self.handle_connection_error()

    def handle_connection_error(self):
        self.disconnect()

    def show_connection_error(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(message)
        msg_box.setWindowTitle("Connection Error")
        msg_box.exec()

    def open_offline(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", "CSV files (*.csv)")
        if file_path:
            self.current_file_path = file_path
            data = pd.read_csv(file_path).values.flatten()
            self.current_data = data[:self.lines_slider.value()]
            self.processed_data = None
            self.draw_ecg(self.current_data)

    def save_data(self):
        if self.current_data is not None:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(self, "Save Data", "", "CSV files (*.csv)")
            if file_path:
                pd.DataFrame(self.current_data).to_csv(file_path, index=False)

    def update_lines(self):
        self.slider_label.setText(f"Number of lines: {self.lines_slider.value()}")
        if self.current_file_path:
            data = pd.read_csv(self.current_file_path).values.flatten()
            self.current_data = data[:self.lines_slider.value()]
            self.processed_data = None
            self.draw_ecg(self.current_data)

    def update_mode(self):
        mode = self.mode_combo.currentText()
        self.online_groupbox.setVisible(mode == "online")
        self.offline_groupbox.setVisible(mode == "offline")
        if mode == "offline":
            self.timer.stop()
            self.status_indicator.set_color(Qt.GlobalColor.gray)
            self.update_connection_buttons(connected=False)
            self.ip_entry.setEnabled(True)

    def update_connection_buttons(self, connected):
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)

    def analyze_current_data(self):
        if self.current_data is not None:
            normalized_ecg, peaks, _ = self.process_ecg_data(self.current_data)
            if len(peaks) < 2:
                QMessageBox.warning(self, "Analysis Error", "Not enough peaks detected for analysis.")
                return
            
            avg_samples_between_peaks = np.mean(np.diff(peaks))
            heart_rate = (self.fs * 60) / avg_samples_between_peaks
            self.heart_rate_label.setText(f"Heart Rate: {heart_rate:.0f} bpm")

            samples_between_peaks = normalized_ecg[peaks[0]:peaks[1]]
            if len(samples_between_peaks) < 187:
                padded_samples = np.pad(samples_between_peaks, (0, 187 - len(samples_between_peaks)), 'constant')
            else:
                padded_samples = samples_between_peaks[:187]

            data_to_analyze = np.array(padded_samples).reshape(1, 187, 1)
            prediction = self.model.predict(data_to_analyze,verbose=2)
            predicted_class = np.argmax(prediction, axis=1)[0]
            classes = ['N', 'S', 'V', 'F', 'Q']
            result = classes[predicted_class]
            self.result_label.setText(f"Result: {result}")

    def analyze_data(self, data):
        normalized_ecg, peaks, _ = self.process_ecg_data(data)
        if len(peaks) < 2:
            self.result_label.setText("Result: Not enough peaks for analysis")
            return
        
        avg_samples_between_peaks = np.mean(np.diff(peaks))
        heart_rate = (self.fs * 60) / avg_samples_between_peaks
        self.heart_rate_label.setText(f"Heart Rate: {heart_rate:.0f} bpm")
        
        samples_between_peaks = normalized_ecg[peaks[0]:peaks[1]]
        if len(samples_between_peaks) < 187:
            padded_samples = np.pad(samples_between_peaks, (0, 187 - len(samples_between_peaks)), 'constant')
        else:
            padded_samples = samples_between_peaks[:187]

        data_to_analyze = np.array(padded_samples).reshape(1, 187, 1)
        prediction = self.model.predict(data_to_analyze,verbose=2)
        predicted_class = np.argmax(prediction, axis=1)[0]
        classes = ['Normal', 'Supra-ventricular premature', 'Ventricular escape', 'Fusion of ventricular and normal', 'Unclassifiable']
        result = classes[predicted_class]
        self.result_label.setText(f"Result: {result}  {(prediction[0][predicted_class] *100):0,.2f}%")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ECGApp()
    window.show()
    sys.exit(app.exec())
