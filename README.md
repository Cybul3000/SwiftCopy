# SwiftCopy

**Safe file recovery from failing and unreliable drives — a fault-tolerant robocopy GUI for Windows.**

![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The problem this solves

When a hard drive starts failing, Windows Explorer freezes — or the entire system crashes — the moment you try to copy files off it. Explorer retries every read error indefinitely, stalling the I/O queue until the OS locks up. By the time you reboot, the drive may be worse than before.

SwiftCopy was built to fix exactly this. It wraps Windows' built-in `robocopy` utility with a clean dual-pane GUI and applies fault-tolerant settings: **zero retries, skip locked files, restartable copy mode**. Instead of hanging, it skips problem files and keeps going — getting your data out before the drive deteriorates further.

---

## Features

- **Failing drive presets** — one-click configuration for safe or fast recovery from dying drives
- **Dual-pane file browser** — navigate source and destination side by side, Total Commander-style
- **Fault-tolerant by default** — skip locked files and zero-retry mode prevent system freezes
- **F5 to copy, F6 to move** — familiar keyboard shortcuts for power users
- **Drag-and-drop** — drag files between panes with copy or move prompt
- **Job queue** — queue multiple operations and process them in sequence
- **Real-time progress** — per-file progress, byte counts, transfer speed, status bar
- **Full robocopy control** — ACLs, timestamps, backup mode, mirror vs copy, retry tuning
- **Color-coded log** — live output with error/warning/info filtering
- **Built-in help** — press F1 for a full user guide and options reference

---

## Download

**[Download SwiftCopy.exe](https://github.com/Cybul3000/SwiftCopy/releases/latest)** — standalone, no Python required.

> Requires Windows 10/11. `robocopy` is built into Windows and available by default.

---

## Quick start for failing drive recovery

1. Launch SwiftCopy
2. Select **Failing drive (safe)** from the Preset dropdown
3. Navigate to the failing drive in the **Left** pane
4. Navigate to your recovery destination in the **Right** pane
5. Press **F5** — SwiftCopy starts copying immediately, skipping problem files instead of hanging
6. When done, run a **second pass** to pick up any files that were busy the first time

---

## Screenshots

*(Screenshots coming soon — star the repo to get notified)*

---

## Build from Source

```bash
# 1. Clone
git clone https://github.com/Cybul3000/SwiftCopy.git
cd SwiftCopy

# 2. Set up virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

### Build standalone .exe

```bash
pip install -r requirements-dev.txt
build.bat
# Output: dist\SwiftCopy.exe
```

> **Windows note:** If `python` is not on PATH, use the full path from `Get-Command python`.
> If `python3` fails, disable the `python3.exe` App Execution Alias in Windows Settings → App Execution Aliases.

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F5` | Copy left → right |
| `F6` | Move left → right |
| `F1` | Open User Guide |
| `Escape` | Stop current job |
| `Backspace` | Go up one directory |
| `Enter` (path bar) | Navigate to typed path |
| Double-click | Open folder |

---

## Robocopy Options

| Option | Flag | Description |
|--------|------|-------------|
| Preserve timestamps/permissions | `/COPY:DATS /DCOPY:DAT` | Copy ACLs and timestamps |
| Conservative mode | `/COPY:DAT` | Data and timestamps only, no ACLs |
| Include auditing info | `/COPYALL` | Copy audit ACEs (requires admin) |
| Skip locked files | `/R:0 /W:0` | Never hang on busy or unreadable files |
| Backup mode | `/ZB` | Read files even without normal permission |
| Mirror | `/MIR` | Exact sync — deletes extras at destination |
| Copy (append) | `/E` | Copy without deleting anything at destination |

---

## Why not just use robocopy directly?

You can — and SwiftCopy does exactly that under the hood. But getting the right flags for a failing drive requires knowing `/R:0 /W:0 /Z /XJ /COPY:DATS` and more. SwiftCopy puts the right combination one click away, adds a visual file browser so you don't have to type paths, and shows live progress without reading dense terminal output.

---

## License

MIT © Maciej — [maciej@tyaudio.eu](mailto:maciej@tyaudio.eu)

---

*Built with [PySide6](https://doc.qt.io/qtforpython/) (Qt 6)*
