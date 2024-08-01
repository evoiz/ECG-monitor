import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks
from scipy.fft import fft, ifft, fftfreq
import tkinter as tk

def read_ecg_data(file_path, start_row, end_row):
    data = pd.read_csv(file_path, header=None, names=['col1', 'ecg', 'ecg_f', 'col4'])#,skiprows=start_row, nrows=end_row-start_row)
    return data['ecg'].values

def normalize_signal(signal):
    return (signal - np.min(signal)) / (np.max(signal) - np.min(signal))

def fft_filter(signal, fs, low_cutoff, high_cutoff):
    N = len(signal)
    yf = fft(signal)
    xf = fftfreq(N, 1/fs)
    
    # Create a mask for the desired frequency range
    mask = (np.abs(xf) > low_cutoff) & (np.abs(xf) < high_cutoff)
    
    # Apply the mask to the FFT
    yf_filtered = yf * mask
    
    # Inverse FFT to get the filtered signal
    filtered_signal = np.real(ifft(yf_filtered))
    
    return filtered_signal, xf, yf, yf_filtered

def compute_fft(signal, fs):
    N = len(signal)
    yf = fft(signal)
    xf = fftfreq(N, 1/fs)[:N//2]
    return xf, 2.0/N * np.abs(yf[0:N//2])

def process_ecg(file_path, start_row, end_row, fs, lowcut, highcut):
    ecg_signal = read_ecg_data(file_path, start_row, end_row)
    
    # Apply FFT filter
    filtered_ecg, xf_full, yf_original, yf_filtered = fft_filter(ecg_signal, fs, lowcut, highcut)
    
    # Apply normalization after filtering
    normalized_ecg = normalize_signal(filtered_ecg)
    
    # Calculate threshold as 80% of the maximum signal value
    threshold = 0.6 * np.max(normalized_ecg)
    
    # Find peaks using the calculated threshold
    peaks, _ = find_peaks(normalized_ecg, height=threshold, distance=int(0.2*fs))
    
    # Compute FFT for plotting
    xf, yf_mag_original = compute_fft(ecg_signal, fs)
    _, yf_mag_filtered = compute_fft(normalized_ecg, fs)
    
    return ecg_signal, filtered_ecg, normalized_ecg, peaks, xf, yf_mag_original, yf_mag_filtered, threshold, xf_full, yf_original, yf_filtered

# Get screen dimensions
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()

# Calculate figure size
fig_width = screen_width / 100  # Convert pixels to inches
fig_height = screen_height * 0.9 / 100  # 90% of screen height, converted to inches

# Main processing
file_path = 'ecg.csv'
start_row = 5647
end_row = 5887 # 10 seconds of data at 125 Hz
fs = 125.0  # Sampling frequency
lowcut = 0.5  # Lower cutoff frequency
highcut = 50  # Upper cutoff frequency

ecg_signal, filtered_ecg, normalized_ecg, peaks, xf, yf_mag_original, yf_mag_filtered, threshold, xf_full, yf_original, yf_filtered = process_ecg(file_path, start_row, end_row, fs, lowcut, highcut)

# Plotting
fig, axs = plt.subplots(5, 1, figsize=(fig_width, fig_height))

# Original signal
axs[0].plot(ecg_signal)
axs[0].set_title('Original ECG Signal')
axs[0].set_ylabel('Voltage (mV)')

# Filtered signal
axs[1].plot(filtered_ecg)
axs[1].set_title('Filtered ECG Signal')
axs[1].set_ylabel('Amplitude')

# Normalized filtered signal with QRS peaks and threshold
axs[2].plot(normalized_ecg)
axs[2].plot(peaks, normalized_ecg[peaks], "x", color='red')
axs[2].axhline(y=threshold, color='g', linestyle='--', label='Threshold (60% of max)')
axs[2].set_title('Normalized Filtered ECG Signal with QRS Peaks and Threshold')
axs[2].set_ylabel('Normalized Amplitude')
axs[2].set_ylim(0, 1)  # Set y-axis limits to 0-1
axs[2].legend()

# Frequency spectrum
axs[3].plot(xf, yf_mag_original, label='Original')
axs[3].plot(xf, yf_mag_filtered, label='Filtered and Normalized')
axs[3].set_title('Frequency Spectrum')
axs[3].set_xlabel('Frequency (Hz)')
axs[3].set_ylabel('Magnitude')
axs[3].set_xlim(0.5, 50)
axs[3].set_ylim(0,5) 
axs[3].legend()

#Full FFT before and after filtering
axs[4].plot(xf_full, np.abs(yf_original), label='Before Filtering', alpha=0.5)
axs[4].plot(xf_full, np.abs(yf_filtered), label='After Filtering', alpha=0.5)
axs[4].set_title('Full FFT Before and After Filtering')
axs[4].set_xlabel('Frequency (Hz)')
axs[4].set_ylabel('Magnitude')
axs[4].set_xlim(0.5, 50)
axs[4].set_ylim(0,30000) 
axs[4].legend()
plt.tight_layout()
plt.show()