# THIS IS FOR TESTING, NOT WORKING PERFECTLY 


import os
import csv
import json
import time
import random
import socket
import threading
import queue
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox



UDP_IP = "0.0.0.0"      
UDP_PORT = 12345         
CHANNEL_COUNT = 8      
SAVE_DIR = "data"     
SUBJECT_ID = "subject01" 
SESSION_ID = "session01" 
SAMPLE_RATE_HINT = 250  
TRIALS_PER_CLASS = 10    
CUE_DURATION_SEC = 3.0   
REST_DURATION_SEC = 2.0  
RANDOMIZE = True         
INCLUDE_REST = True     

CLASSES = [
    ("فتح اليد اليمنى", "right_open"),
    ("إغلاق اليد اليمنى", "right_close"),
    ("فتح اليد اليسرى", "left_open"),
    ("إغلاق اليد اليسرى", "left_close"),
]

REST_DISPLAY = "استراحة"
REST_LABEL = "rest"


os.makedirs(SAVE_DIR, exist_ok=True)
ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
base_name = f"{SUBJECT_ID}_{SESSION_ID}_{ts_str}"
CSV_PATH = os.path.join(SAVE_DIR, base_name + ".csv")
META_PATH = os.path.join(SAVE_DIR, base_name + "_metadata.json")


class UDPReceiver(threading.Thread):
    """
    Receives UDP packets from OpenBCI GUI.
    Tries to parse JSON first; if fails, falls back to CSV-like numeric split.
    Puts standardized tuples on a queue: (timestamp, sample_index, channels:list[float])
    """
    def __init__(self, ip, port, ch_count, out_queue, stop_event):
        super().__init__(daemon=True)
        self.ip = ip
        self.port = port
        self.ch_count = ch_count
        self.out_queue = out_queue
        self.stop_event = stop_event
        self.sock = None
        self.recv_errors = 0

    def bind_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # increase buffer if needed
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        self.sock.bind((self.ip, self.port))
        self.sock.settimeout(1.0)

    def parse_packet(self, raw_bytes):
        s = raw_bytes.decode("utf-8", errors="ignore").strip()

        # Try JSON
        try:
            obj = json.loads(s)
            sample_idx = obj.get("sample") or obj.get("sampleNumber") or obj.get("n")
            ts = obj.get("timestamp") or time.time()
            eeg = obj.get("eeg") or obj.get("data") or obj.get("channels") or None
            if eeg and isinstance(eeg, list):
                vals = [float(x) for x in eeg[:self.ch_count]]
                if len(vals) < self.ch_count:
                    vals += [float('nan')] * (self.ch_count - len(vals))
                return float(ts), (int(sample_idx) if sample_idx is not None else None), vals
            ch_keys = [f"ch{i+1}" for i in range(self.ch_count)]
            if all(k in obj for k in ch_keys):
                vals = [float(obj[k]) for k in ch_keys]
                ts = obj.get("timestamp") or time.time()
                sample_idx = obj.get("sample") or obj.get("sampleNumber")
                return float(ts), (int(sample_idx) if sample_idx is not None else None), vals
        except Exception:
            pass

        try:
            parts = [p for p in s.replace(";", ",").replace("\t", ",").split(",") if p.strip() != ""]
            floats = []
            for p in parts:
                try:
                    floats.append(float(p))
                except ValueError:
                    pass
            if len(floats) >= self.ch_count:
                if len(floats) >= self.ch_count + 1:
                    samp = int(floats[0])
                    vals = floats[1:self.ch_count+1]
                    return time.time(), samp, vals
                else:
                    vals = floats[:self.ch_count]
                    return time.time(), None, vals
        except Exception:
            pass

        return None

    def run(self):
        self.bind_socket()
        while not self.stop_event.is_set():
            try:
                data, _ = self.sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            parsed = self.parse_packet(data)
            if parsed is None:
                self.recv_errors += 1
                if self.recv_errors % 100 == 0:
                    # print occasional warning to console
                    print(f"[WARN] UDP parse errors so far: {self.recv_errors}")
                continue
            ts, sample_idx, channels = parsed
            self.out_queue.put((ts, sample_idx, channels))

        try:
            self.sock.close()
        except Exception:
            pass


class CSVWriter(threading.Thread):
    """
    Consumes samples from a queue and writes to CSV with current label + trial_id.
    """
    def __init__(self, in_queue, stop_event, label_state_getter, csv_path, ch_count):
        super().__init__(daemon=True)
        self.in_queue = in_queue
        self.stop_event = stop_event
        self.get_label_state = label_state_getter
        self.csv_path = csv_path
        self.ch_count = ch_count
        self.file = None
        self.writer = None
        self.rows_written = 0

    def open_file(self):
        self.file = open(self.csv_path, "w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        header = ["timestamp", "sample_index"] + [f"ch{i+1}" for i in range(self.ch_count)] + ["label", "trial_id"]
        self.writer.writerow(header)

    def run(self):
        self.open_file()
        while not self.stop_event.is_set():
            try:
                item = self.in_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            ts, sample_idx, channels = item
            label, trial_id = self.get_label_state()
            row = [f"{ts:.6f}", sample_idx] + [f"{v:.6f}" if isinstance(v, (int, float)) else "" for v in channels] + [label, trial_id]
            self.writer.writerow(row)
            self.rows_written += 1

        while True:
            try:
                item = self.in_queue.get_nowait()
            except queue.Empty:
                break
            ts, sample_idx, channels = item
            label, trial_id = self.get_label_state()
            row = [f"{ts:.6f}", sample_idx] + [f"{v:.6f}" if isinstance(v, (int, float)) else "" for v in channels] + [label, trial_id]
            self.writer.writerow(row)

        self.file.flush()
        self.file.close()


class LabelManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._current_label = REST_LABEL
        self._current_trial_id = -1

    def set(self, label, trial_id):
        with self._lock:
            self._current_label = label
            self._current_trial_id = trial_id

    def get(self):
        with self._lock:
            return self._current_label, self._current_trial_id

class TrialScheduler:
    def __init__(self, root, label_widget, label_manager, start_btn, stop_btn, progress_var):
        self.root = root
        self.label_widget = label_widget
        self.label_manager = label_manager
        self.start_btn = start_btn
        self.stop_btn = stop_btn
        self.progress_var = progress_var

        self.trials = []
        for disp, lab in CLASSES:
            for _ in range(TRIALS_PER_CLASS):
                self.trials.append((disp, lab))
        if RANDOMIZE:
            random.shuffle(self.trials)

        self.total_trials = len(self.trials)
        self.current_index = -1
        self.running = False
        self.trial_id_counter = 0

    def _show_text(self, text):
        self.label_widget.config(text=text)

    def start(self):
        if self.running:
            return
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.current_index = -1
        self.progress_var.set(0)
        self.root.after(200, self.next_trial)

    def stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.label_manager.set(REST_LABEL, -1)
        self._show_text("تم الإيقاف")
        self.progress_var.set(0)

    def next_trial(self):
        if not self.running:
            return

        self.current_index += 1
        if self.current_index >= self.total_trials:
            self.running = False
            self._show_text("انتهت الجلسة ✅")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.label_manager.set(REST_LABEL, -1)
            self.progress_var.set(100)
            return

        prog = int((self.current_index / self.total_trials) * 100)
        self.progress_var.set(prog)

        disp, lab = self.trials[self.current_index]
        self.trial_id_counter += 1
        trial_id = self.trial_id_counter

        self._show_text(disp)
        self.label_manager.set(lab, trial_id)

        def after_cue():
            if INCLUDE_REST:
                self._show_text(REST_DISPLAY)
                self.label_manager.set(REST_LABEL, trial_id)
                self.root.after(int(REST_DURATION_SEC * 1000), self.next_trial)
            else:
                self.next_trial()

        self.root.after(int(CUE_DURATION_SEC * 1000), after_cue)

class App:
    def __init__(self, root):
        self.root = root
        root.title("OpenBCI EEG Recorder - Hand Motor Imagery")

        self.stop_event = threading.Event()
        self.sample_queue = queue.Queue(maxsize=5000)
        self.label_manager = LabelManager()

        self.udp_thread = UDPReceiver(UDP_IP, UDP_PORT, CHANNEL_COUNT, self.sample_queue, self.stop_event)
        self.writer_thread = CSVWriter(self.sample_queue, self.stop_event, self.label_manager.get, CSV_PATH, CHANNEL_COUNT)

        main = ttk.Frame(root, padding=16)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="تجربة فتح/إغلاق اليدين (Cyton)", font=("Arial", 18, "bold"))
        title.pack(pady=(0, 12))

        self.cue_label = ttk.Label(main, text="اضغط بدء لبدء الجلسة", anchor="center")
        self.cue_label.config(font=("Arial", 48, "bold"))
        self.cue_label.pack(fill="x", pady=16)

        self.progress_var = tk.IntVar(value=0)
        prog = ttk.Progressbar(main, orient="horizontal", mode="determinate", variable=self.progress_var, maximum=100)
        prog.pack(fill="x", pady=8)

        btns = ttk.Frame(main)
        btns.pack(pady=8)

        self.start_btn = ttk.Button(btns, text="بدء الجلسة", command=self.start_session)
        self.stop_btn = ttk.Button(btns, text="إيقاف", command=self.stop_session, state="disabled")
        self.exit_btn = ttk.Button(btns, text="حفظ وخروج", command=self.on_close)

        self.start_btn.grid(row=0, column=0, padx=6)
        self.stop_btn.grid(row=0, column=1, padx=6)
        self.exit_btn.grid(row=0, column=2, padx=6)

        info = ttk.Label(main, text=self.build_info_text(), justify="left", foreground="#444")
        info.pack(fill="x", pady=(10, 0))

        self.scheduler = TrialScheduler(root, self.cue_label, self.label_manager, self.start_btn, self.stop_btn, self.progress_var)

        self.udp_thread.start()
        self.writer_thread.start()

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_info_text(self):
        return (
            f"UDP: {UDP_IP}:{UDP_PORT} | قنوات: {CHANNEL_COUNT}\n"
            f"ملف الناتج: {CSV_PATH}\n"
            f"التجارب لكل حالة: {TRIALS_PER_CLASS} | زمن الإشارة: {CUE_DURATION_SEC}s | الراحة: {REST_DURATION_SEC}s\n"
            f"الوسوم: {[lab for _, lab in CLASSES]} + '{REST_LABEL}'"
        )

    def start_session(self):
        self.scheduler.start()

    def stop_session(self):
        self.scheduler.stop()

    def on_close(self):
        if messagebox.askokcancel("خروج", "هل تريد حفظ الملف وإنهاء الجلسة؟"):
            self.scheduler.stop()
            self.stop_event.set()
            time.sleep(0.8)
            self.write_metadata()
            try:
                self.root.destroy()
            except Exception:
                pass

    def write_metadata(self):
        meta = {
            "subject_id": SUBJECT_ID,
            "session_id": SESSION_ID,
            "created_at": datetime.now().isoformat(),
            "csv_path": os.path.abspath(CSV_PATH),
            "channels": CHANNEL_COUNT,
            "sample_rate_hint": SAMPLE_RATE_HINT,
            "udp_ip": UDP_IP,
            "udp_port": UDP_PORT,
            "classes": [{"display": d, "label": l} for d, l in CLASSES],
            "rest_label": REST_LABEL,
            "trials_per_class": TRIALS_PER_CLASS,
            "cue_duration_sec": CUE_DURATION_SEC,
            "rest_duration_sec": REST_DURATION_SEC,
            "randomize": RANDOMIZE,
            "include_rest": INCLUDE_REST,
        }
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Metadata saved to: {META_PATH}")

def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()