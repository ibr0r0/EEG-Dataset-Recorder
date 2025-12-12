## Python Virtual Environment Activation Guide

### 1. Create the Virtual Environment

Open the terminal inside your project folder.

Run:

```bash
python3 -m venv venv
```

This creates a folder named `venv` containing the environment files.

---

### 2. Activate the Environment

**On macOS / Linux:**

```bash
source venv/bin/activate
```

**On Windows CMD:**

```bat
venv\Scripts\activate
```

**On Windows PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

After activation, you will see `(venv)` at the beginning of the command line.

---

### 3. Install Dependencies Inside the Environment

Once the environment is active, install the required packages:

```bash
pip install -r requirements.txt
```

---

### 4. Find the Serial Port (macOS – MacBook)

Before running the EEG recorder, you must identify the **OpenBCI USB dongle port**.

1. Plug in the OpenBCI USB Dongle.
2. Open Terminal.
3. Run:

```bash
ls /dev/cu.*
```

You should see something similar to:

```text
/dev/cu.usbserial-DP04W01L
```

This is the serial port.

Use this value in the app:

```text
/dev/cu.usbserial-DP04W01L
```

⚠️ **Important:**

* Always prefer `/dev/cu.*` over `/dev/tty.*` on macOS.
* If nothing appears, unplug and re-plug the dongle and run the command again.
* Do **not** run OpenBCI GUI at the same time.

---

### 5. Run the Application

With the environment activated:

```bash
streamlit run app.py
```

(Replace `app.py` with your script name.)

---

### 6. Deactivate the Environment

When done, type:

```bash
deactivate
```

to exit the virtual environment and return to the system Python.

---

### 7. Important Notes

* All packages installed inside the environment are isolated from the system.
* Each time you open a new terminal to run your project, **activate the environment first**.
* The serial port name may change if you use a different USB hub or device.


