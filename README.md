# CopyRobo

A small Windows 11 desktop app that wraps `robocopy` with a two-pane, Total Commander-like layout.

## Features
- Dual-pane file browser
- Copy left->right or right->left
- Robocopy presets for mirror/copy modes
- Logging and retry tuning

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

### Windows note
If `python` is not on PATH, run with the full path shown by:
```bash
Get-Command python
```
Example:
```bash
"C:/Program Files/Python312/python.exe" main.py
```
If `python3` fails on Windows, disable the `python3.exe` App Execution Alias in Windows Settings.

## Notes
- Robocopy must be available in PATH (default on Windows 11).
- For failing drives, consider `Retry tuning` and `Skip locked files` together.
