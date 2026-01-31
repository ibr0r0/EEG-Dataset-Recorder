# EEG Dataset Recorder

The **EEG Dataset Recorder** provides a set of Python scripts for recording, simulating, and managing EEG (Electroencephalography) data.
It supports both direct data capture and UDP-based data streaming, producing timestamped CSV datasets for further analysis, preprocessing, or machine learning applications.

---

## Demo

<video src="https://github.com/user-attachments/assets/bceea453-045a-4a84-9e2e-fc6a8c3cb640" width="600" autoplay loop muted playsinline></video>

---

## Project Structure

```
EEG_DATASET/
│
├── eeg_recorder.py            # Records EEG data locally
├── eeg_udp_recorder.py        # Records EEG data over UDP (NOT WORKING)
├── producer.py                # Simulates EEG data (NOT WORKING)
│
├── eeg_dataset.csv            # Primary EEG dataset
├── eeg_dataset1.csv           # Secondary dataset
├── eeg_dataset_udp_fixed.csv  # Cleaned/processed UDP dataset
│
├── requirements.txt           # Python dependencies
└── setup.md                   # Virtual environment setup guide
```

---

## Requirements

* Python 3.8 or higher
* All dependencies listed in `requirements.txt`

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Usage

### Record EEG Data Locally

```bash
python eeg_recorder.py
```

### Record EEG Data via UDP

```bash
python eeg_udp_recorder.py
```

### Generate Synthetic EEG Data

```bash
python producer.py
```

---

## Output

Each script generates one or more `.csv` files containing EEG readings with timestamps.
These files can be used for:

* Signal analysis
* Feature extraction
* Machine learning training and evaluation

---

## Python Virtual Environment Setup

### 1. Create the Environment

```bash
python3 -m venv venv
```

### 2. Activate the Environment

**macOS / Linux:**

```bash
source venv/bin/activate
```

**Windows (CMD):**

```bash
venv\Scripts\activate
```

**Windows (PowerShell):**

```bash
venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Deactivate

```bash
deactivate
```

**Notes:**

* The `venv/` folder should not be pushed to GitHub.
* Always activate the virtual environment before running the project.
* Packages installed inside `venv` are isolated from your system Python installation.

---

## Author

Developed by **Aether!**
EEG Dataset Recorder — A streamlined EEG data acquisition and recording toolkit for research and analysis.

