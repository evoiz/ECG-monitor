
# ECG Monitoring System

## Overview

This project is an ECG (Electrocardiogram) monitoring system with a graphical user interface built using PyQt and a TensorFlow model for analyzing ECG data to classify heart electrical activity.

## Features

- **Graphical User Interface (GUI)**: Interactive interface designed with PyQt6.
- **Online and Offline Modes**: Switch between real-time data fetching from an API and loading data from a CSV file.
- **ECG Data Processing**: Apply FFT for filtering and normalize the signal.
- **Machine Learning Analysis**: Use a TensorFlow model to classify heart activity.
- **User Interaction**: Connect to live data, load offline data, and view analysis results.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```bash
   cd <project-directory>
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python GUI_pyQT.py
   ```

2. **Online Mode**:
   - Select "online" mode from the dropdown.
   - Enter the IP address of the ECG data source.
   - Click "Connect" to start receiving and displaying ECG data.

3. **Offline Mode**:
   - Select "offline" mode from the dropdown.
   - Click "Open" to load a CSV file containing ECG data.
   - Use the slider to select the number of lines to display.
   - Click "Analyze" to process and classify the loaded ECG data.

## File Structure

- `GUI_pyQT.py`: Main script containing the PyQt GUI implementation.
- `model.keras`: Pre-trained TensorFlow model for ECG data classification.
- `requirements.txt`: List of required Python packages.

## Dependencies

- Python 3.x
- PyQt6
- Matplotlib
- NumPy
- Pandas
- SciPy
- TensorFlow
- Requests

## License

This project is licensed under the MIT License.
