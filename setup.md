Python Virtual Environment Activation Guide

1. Create the Virtual Environment

Open the terminal inside your project folder.

Run:

python3 -m venv venv


This creates a folder named venv containing the environment files.

2. Activate the Environment

On macOS / Linux:

python3 -m venv venv


On Windows CMD:

venv\Scripts\activate


On Windows PowerShell:

venv\Scripts\Activate.ps1


After activation, you will see (venv) at the beginning of the command line.

3. Install Dependencies Inside the Environment

Once the environment is active, install the required packages:

pip install -r requirements.txt


4. Deactivate the Environment

When done, type:

deactivate


to exit the virtual environment and return to the system Python.

5. Important Notes

All packages installed inside the environment are isolated from the system.

Each time you open a new terminal to run your project, activate the environment first.