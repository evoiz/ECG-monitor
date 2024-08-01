import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks

def read_ecg_data(file_path, start_row, end_row):
    data = pd.read_csv(file_path, header=None, names=['col1', 'col2', 'ecg', 'col4'], 
                       skiprows=start_row, nrows=end_row-start_row)
    return data['ecg'].values

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def process_ecg(ecg_signal, fs, lowcut, highcut):
    filtered_ecg = butter_bandpass_filter(ecg_signal, lowcut, highcut, fs)
    peaks, _ = find_peaks(filtered_ecg, height=0.1, distance=50)
    return filtered_ecg, peaks

def plot_ecg(ecg_signal, filtered_ecg, peaks, title):
    plt.figure(figsize=(10, 4))
    plt.plot(ecg_signal, label='Original')
    plt.plot(filtered_ecg, label='Filtered')
    plt.plot(peaks, filtered_ecg[peaks], "x", color='red', label='QRS Peaks')
    plt.title(title)
    plt.xlabel('Samples')
    plt.ylabel('Voltage (mV)')
    plt.legend()
    plt.tight_layout()

# Main processing
file_path = 'ecg2.csv'
start_row = 0
end_row = 1000  # Adjust as needed

ecg_signal = read_ecg_data(file_path, start_row, end_row)
fs = 150.0  # Sampling frequency

# Define ranges for lowcut and highcut
lowcuts = [1, 3, 5, 7]
highcuts = [15, 20, 25, 30]

plt.figure(figsize=(20, 15))

for i, lowcut in enumerate(lowcuts):
    for j, highcut in enumerate(highcuts):
        filtered_ecg, peaks = process_ecg(ecg_signal, fs, lowcut, highcut)
        
        plt.subplot(len(lowcuts), len(highcuts), i*len(highcuts) + j + 1)
        plt.plot(ecg_signal, alpha=0.5, label='Original')
        plt.plot(filtered_ecg, label='Filtered')
        plt.plot(peaks, filtered_ecg[peaks], "x", color='red', label='QRS Peaks')
        plt.title(f'Lowcut: {lowcut} Hz, Highcut: {highcut} Hz')
        plt.xlabel('Samples')
        plt.ylabel('Voltage (mV)')
        plt.legend()

plt.tight_layout()
plt.show()