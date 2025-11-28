import streamlit as st
import pandas as pd
import socket
import time
import json
from datetime import datetime

st.set_page_config(page_title="EEG Hand Movement Recorder", page_icon="🧠", layout="centered")

st.title("🧠 EEG Hand Movement Recorder")

st.sidebar.header("🧩 Settings")
udp_ip = st.sidebar.text_input("UDP IP", "127.0.0.1")
udp_port = st.sidebar.number_input("UDP Port", 12345)
duration = st.sidebar.number_input("Recording Duration (seconds)", 5, 60, 10)
save_path = st.sidebar.text_input("CSV Save Path", "eeg_dataset_udp_fixed.csv")
sampling_rate = st.sidebar.number_input("Sampling Rate (Hz)", 100, 1000, 250)

channel_names = ["FC3", "FC4", "C3", "C4", "CP3", "CP4", "FCz", "Pz"]

st.markdown("### 🧩 EEG Electrode Placement (8-channel Motor Cortex Montage)")
ch_df = pd.DataFrame({
    "Channel": channel_names,
    "Description": [
        "Frontal-Central Left (motor planning)",
        "Frontal-Central Right (motor planning)",
        "Central Left (motor execution - Left Hand)",
        "Central Right (motor execution - Right Hand)",
        "Centro-Parietal Left (somatosensory feedback)",
        "Centro-Parietal Right (somatosensory feedback)",
        "Fronto-Central Midline (motor control reference)",
        "Parietal Midline (feedback/reference)"
    ]
})
st.table(ch_df)

montage_img_path = "https://www.researchgate.net/publication/340680978/figure/fig4/AS:963526076137508@1606733926908/The-eight-channel-electrode-system-in-the-International-10-20-system-The-green-marked.png"
st.image(
    montage_img_path,
    caption="Highlighted: FC3, FC4, C3, C4, CP3, CP4, FCz, Pz",
    width=500
)

st.markdown("### ✋ Choose Mode")
hand = st.radio("Select Mode:", ["Left", "Right", "Idle"], horizontal=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    hand_gif = st.empty()
    status_placeholder = st.empty()

def receive_udp_json(ip, port, duration, ch_names, hand, sampling_rate=250):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    sock.settimeout(1.0)

    data_list = []
    start_time = time.time()
    sample_interval = 1.0 / sampling_rate

    while time.time() - start_time < duration:
        try:
            data, _ = sock.recvfrom(32768)
            msg = data.decode(errors="ignore").strip()
            if not msg:
                continue
            try:
                obj = json.loads(msg)
            except json.JSONDecodeError:
                continue

            values = None
            if isinstance(obj, dict):
                if "data" in obj:
                    values = obj["data"]
                elif "rawEeg" in obj:
                    values = obj["rawEeg"]
                elif "eeg" in obj:
                    values = obj["eeg"]

            if isinstance(values, list) and all(isinstance(v, list) for v in values):
                base_time = datetime.now().timestamp()
                for i, sample in enumerate(values):
                    if len(sample) >= len(ch_names):
                        ts = base_time + (i * sample_interval)
                        ts_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S.%f")
                        row = [ts_str, hand] + sample[:len(ch_names)]
                        data_list.append(row)
            elif isinstance(values, list) and len(values) >= len(ch_names):
                ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                row = [ts_str, hand] + values[:len(ch_names)]
                data_list.append(row)

        except socket.timeout:
            continue

    sock.close()
    cols = ["timestamp", "hand"] + ch_names
    return pd.DataFrame(data_list, columns=cols)

if st.button("🎬 Start Recording"):
    st.success(f"Recording for {duration} seconds ({hand} mode)...")

    idle_gif = "https://img.icons8.com/win10/512/FFFFFF/plus.png"
    open_gif = "https://media.tenor.com/mOZeQBMuRAIAAAAM/the-only-reallaz-hand.gif"
    close_gif = "https://media.tenor.com/UtL_5N-UBVoAAAAM/hand-close.gif"

    if hand == "Idle":
        hand_gif.image(idle_gif, caption="Idle - Focus on the +")
        status_placeholder.info("Focus on the +")
        time.sleep(duration)
    else:
        half = duration / 2
        hand_gif.image(open_gif, caption=f"{hand} hand - OPEN")
        status_placeholder.info("Hand Open - Keep it open!")
        time.sleep(half)
        hand_gif.image(close_gif, caption=f"{hand} hand - CLOSE")
        status_placeholder.warning("Hand Close - Keep it closed!")
        time.sleep(half)

    st.write(f"📡 Listening on {udp_ip}:{udp_port} ...")

    df = receive_udp_json(udp_ip, udp_port, duration, channel_names, hand, sampling_rate)

    if df.empty:
        st.error("❌ No JSON data received.")
    else:
        df.to_csv(save_path, mode='a', index=False, header=not pd.io.common.file_exists(save_path))
        actual_rate = df.shape[0] / duration
        st.success(f"Saved {df.shape[0]} samples to {save_path}")
        st.info(f"Actual Sampling Rate ≈ {actual_rate:.2f} Hz")
        st.dataframe(df.head(10))

st.markdown("---")
st.caption("Developed by Aether ⚡")
