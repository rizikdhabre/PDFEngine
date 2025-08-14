# A4 → A5/A6/A7 Imposition Tool

This project contains a PyQt6 GUI and core PDF imposition logic using PyMuPDF (fitz).
The code has been refactored into a modular structure:
- `gui/` : PyQt6 GUI code (App)
- `core/`: signature planning, geometry helpers, and imposition functions
- `cli/` : optional CLI runner
- `utils/`: helpers such as logger
- `styles/`: QSS styles

Requirements: see requirements.txt

To run:
```
pip install -r requirements.txt
python main.py
```
