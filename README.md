# A4 → A5/A6/A7 Imposition Tool

This project contains a PyQt6 GUI and core PDF imposition logic using PyMuPDF (fitz).  
The code has been refactored into a modular structure:
- `gui/` : PyQt6 GUI code (App)
- `core/`: signature planning, geometry helpers, and imposition functions
- `cli/` : optional CLI runner
- `utils/`: helpers such as logger
- `styles/`: QSS styles

## Download / Clone the Repository

### Option A — Clone with Git
1. Install Git: https://git-scm.com/downloads  
2. Open a terminal (Windows: Command Prompt/PowerShell, macOS/Linux: Terminal).  
3. Run:
   ```bash
   git clone https://github.com/rizikdhabre/PDFEngine.git
   cd PDFEngine
````

### Option B — Download ZIP

1. Go to [PDFEngine on GitHub](https://github.com/rizikdhabre/PDFEngine).
2. Click the green "Code" button → "Download ZIP".
3. Extract the ZIP and open a terminal inside the extracted folder.

## Setup Python Virtual Environment

A virtual environment keeps the project dependencies separate from your system.

### Step 1 — Check Python & pip

* macOS/Linux:

  ```bash
  python3 --version
  python3 -m pip --version
  ```
* Windows:

  ```powershell
  py --version
  py -m pip --version
  ```

### Step 2 — Create the virtual environment

* macOS/Linux:

  ```bash
  python3 -m venv venv
  ```
* Windows:

  ```powershell
  py -m venv venv
  ```

### Step 3 — Activate the virtual environment

* macOS/Linux:

  ```bash
  source venv/bin/activate
  ```
* Windows (PowerShell):

  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* Windows (CMD):

  ```cmd
  venv\Scripts\activate.bat
  ```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Run the app

* macOS/Linux:

  ```bash
  python3 main.py
  ```
* Windows:

  ```powershell
  py main.py
  ```