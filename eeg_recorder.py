import streamlit as st
import pandas as pd
import time
import numpy as np
from datetime import datetime

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import (
    DataFilter,
    FilterTypes,
    DetrendOperations,
    NoiseTypes
)

# ======================
# Streamlit config
# ======================
st.set_page_config(page_title="EEG Recorder", page_icon="🧠")
st.title("🧠 EEG Recorder – Session Mode")

# ======================
# Session State
# ======================
if "recording" not in st.session_state:
    st.session_state.recording = False

# ======================
# Settings
# ======================
serial_port = st.text_input(
    "Serial Port",
    "/dev/cu.usbserial-DP04W01L"
)

duration = st.number_input("Duration per class (sec)", 1, 30, 10)
FS = 250

channels = ["FC3","C3","CP3","Cz","FCz","FC4","C4","CP4"]
session_name = st.text_input(
    "Session name (file name)",
    value="session_01"
)

SAVE_FILE = f"{session_name}.csv"
# ======================
# Visuals (صور فقط)
# ======================
right_img = "https://media.tenor.com/mOZeQBMuRAIAAAAM/the-only-reallaz-hand.gif"
left_img  = "https://media.tenor.com/mOZeQBMuRAIAAAAM/the-only-reallaz-hand.gif"
idle_img  = "https://img.icons8.com/win10/512/FFFFFF/plus.png"

visual = st.empty()
status = st.empty()

# ======================
# Preprocessing
# ======================
def preprocess_like_gui(df):
    out = df.copy()
    for ch in channels:
        x = out[ch].to_numpy(dtype=np.float64)

        DataFilter.detrend(x, DetrendOperations.LINEAR.value)
        DataFilter.remove_environmental_noise(x, FS, NoiseTypes.FIFTY.value)
        DataFilter.perform_bandpass(
            x, FS, 1.0, 40.0, 4,
            FilterTypes.BUTTERWORTH.value, 0
        )
        out[ch] = x
    return out

# ======================
# Recorder
# ======================
def record_blocking(duration, label, port):
    BoardShim.disable_board_logger()

    params = BrainFlowInputParams()
    params.serial_port = port

    board = BoardShim(BoardIds.CYTON_BOARD.value, params)
    board.prepare_session()
    board.start_stream(450000)

    start = time.time()
    while time.time() - start < duration:
        time.sleep(0.01)

    data = board.get_board_data()
    board.stop_stream()
    board.release_session()

    eeg_ch = board.get_eeg_channels(BoardIds.CYTON_BOARD.value)
    ts_ch  = board.get_timestamp_channel(BoardIds.CYTON_BOARD.value)

    cyton_map = {
        "FC3": eeg_ch[0],
        "C3":  eeg_ch[1],
        "CP3": eeg_ch[2],
        "Cz":  eeg_ch[3],
        "FCz": eeg_ch[4],
        "FC4": eeg_ch[5],
        "C4":  eeg_ch[6],
        "CP4": eeg_ch[7],
    }

    rows = []
    for i in range(data.shape[1]):
        row = {
            "timestamp": datetime.fromtimestamp(data[ts_ch][i]),
            "label": label
        }
        for name in channels:
            row[name] = data[cyton_map[name]][i]
        rows.append(row)

    return pd.DataFrame(rows)

# ======================
# Session Button
# ======================
if st.session_state.recording is False and pd.io.common.file_exists(SAVE_FILE):
    st.warning(f"⚠️ File {SAVE_FILE} already exists. Choose a different session name.")

if st.button("🚀 Start Session") and not st.session_state.recording:
    st.session_state.recording = True

    session_order = [
        ("Right", right_img),
        ("Left",  left_img),
        ("Idle",  idle_img)
    ]

    for label, img in session_order:

        # ⏸️ فاصل قبل التسجيل
        status.info(f"Get ready for {label}")
        visual.image(img, width=350)
        time.sleep(3)

        # 🎬 أثناء التسجيل (الصورة تظل ظاهرة)
        status.warning(f"Recording {label}...")
        visual.image(img, width=350)

        df_raw = record_blocking(duration, label, serial_port)
        df_clean = preprocess_like_gui(df_raw)

        df_clean.to_csv(
            SAVE_FILE,
            index=False,
            mode="a",
            header=not pd.io.common.file_exists(SAVE_FILE)
        )

        status.success(f"{label} saved ({len(df_clean)} samples)")
        time.sleep(3)

    visual.empty()
    status.success("✅ Session completed — all data saved in ONE file")
    st.session_state.recording = False
