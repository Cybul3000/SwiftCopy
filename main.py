import html
import os
import re
import shlex
from datetime import datetime

from PySide6.QtCore import QProcess, QFileInfo, QSettings, QStandardPaths, Qt, Signal, QUrl
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QFont,
    QIcon,
    QImage,
    QKeySequence,
    QPainter,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFileIconProvider,
    QFileSystemModel,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QAbstractItemView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplashScreen,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "SwiftCopy"
APP_VERSION = "1.0.0"
GITHUB_URL = "https://github.com/Cybul3000/SwiftCopy"
AUTHOR_EMAIL = "maciej@tyaudio.eu"


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

def dark_theme_stylesheet() -> str:
    return """
    QWidget { background-color: #0f131a; color: #d7dde8; }
    QLineEdit, QTextEdit, QTreeView, QComboBox, QSpinBox {
        background-color: #121821; border: 1px solid #273142; selection-background-color: #1f6feb;
        selection-color: #ffffff;
    }
    QGroupBox { border: 1px solid #273142; margin-top: 6px; }
    QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #9fb2c9; }
    QPushButton { background-color: #1a2332; border: 1px solid #2b3a52; padding: 4px 8px; border-radius: 4px; }
    QPushButton:hover { background-color: #202b3e; }
    QToolBar { background: #101621; border-bottom: 1px solid #273142; }
    QStatusBar { background: #101621; border-top: 1px solid #273142; }
    QProgressBar { background: #121821; border: 1px solid #273142; text-align: center; color: #d7dde8; }
    QProgressBar::chunk { background-color: #2ea043; }
    QTextEdit { font-family: Consolas, "Courier New", monospace; }
    QTabWidget::pane { border: 1px solid #273142; }
    QTabBar::tab { background: #1a2332; border: 1px solid #273142; padding: 5px 14px; }
    QTabBar::tab:selected { background: #202b3e; border-bottom-color: #202b3e; }
    QToolTip { background-color: #1a2332; color: #d7dde8; border: 1px solid #273142; padding: 4px; }
    """


# ---------------------------------------------------------------------------
# Splash screen
# ---------------------------------------------------------------------------

def _build_splash_pixmap() -> QPixmap:
    w, h = 480, 260
    pixmap = QPixmap(w, h)
    pixmap.fill(QColor("#0f131a"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Border
    painter.setPen(QColor("#273142"))
    painter.drawRect(0, 0, w - 1, h - 1)

    # Title
    f = QFont("Segoe UI", 34, QFont.Bold)
    painter.setFont(f)
    painter.setPen(QColor("#d7dde8"))
    painter.drawText(0, 30, w, 70, Qt.AlignCenter, APP_NAME)

    # Tagline
    f2 = QFont("Segoe UI", 12)
    painter.setFont(f2)
    painter.setPen(QColor("#9fb2c9"))
    painter.drawText(0, 110, w, 30, Qt.AlignCenter, "Safe file recovery from failing drives")

    # Version
    painter.drawText(0, 150, w, 25, Qt.AlignCenter, f"Version {APP_VERSION}")

    # Author
    f3 = QFont("Segoe UI", 10)
    painter.setFont(f3)
    painter.setPen(QColor("#58a6ff"))
    painter.drawText(0, 200, w, 25, Qt.AlignCenter, f"by Maciej  ·  {AUTHOR_EMAIL}")

    painter.end()
    return pixmap


# ---------------------------------------------------------------------------
# About dialog
# ---------------------------------------------------------------------------

class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(440, 340)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 16)

        title = QLabel(f"<h2 style='margin:0'>{APP_NAME}</h2>")
        title.setAlignment(Qt.AlignCenter)

        version = QLabel(f"Version {APP_VERSION}")
        version.setAlignment(Qt.AlignCenter)

        desc = QLabel(
            "Safe file copying from failing and unreliable drives.\n"
            "Built after Windows crashed mid-copy from a dying hard drive —\n"
            "SwiftCopy uses robocopy's fault-tolerant mode to keep going\n"
            "where Windows Explorer gives up or freezes."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #273142;")

        author = QLabel(
            f'By <b>Maciej</b> &nbsp;·&nbsp; '
            f'<a href="mailto:{AUTHOR_EMAIL}" style="color:#58a6ff;">{AUTHOR_EMAIL}</a>'
        )
        author.setAlignment(Qt.AlignCenter)
        author.setOpenExternalLinks(True)

        github = QLabel(
            f'<a href="{GITHUB_URL}" style="color:#58a6ff;">'
            f'GitHub: {GITHUB_URL.replace("https://", "")}</a>'
        )
        github.setAlignment(Qt.AlignCenter)
        github.setOpenExternalLinks(True)

        license_lbl = QLabel("Released under the MIT License")
        license_lbl.setAlignment(Qt.AlignCenter)
        license_lbl.setStyleSheet("color: #9fb2c9; font-size: 11px;")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(desc)
        layout.addWidget(separator)
        layout.addWidget(author)
        layout.addWidget(github)
        layout.addWidget(license_lbl)
        layout.addStretch()
        layout.addWidget(buttons)


# ---------------------------------------------------------------------------
# Help dialog
# ---------------------------------------------------------------------------

_HELP_CSS = (
    "body { background:#0f131a; color:#d7dde8; font-family:'Segoe UI',sans-serif; "
    "font-size:13px; margin:12px; }"
    "h2 { color:#58a6ff; margin-bottom:6px; }"
    "h3 { color:#9fb2c9; margin-bottom:4px; }"
    "p, li { line-height:1.6; }"
    "table { border-collapse:collapse; width:100%; }"
    "th { background:#121821; color:#9fb2c9; padding:6px 8px; text-align:left; "
    "border:1px solid #273142; }"
    "td { padding:5px 8px; border:1px solid #1e2c3d; vertical-align:top; }"
    "tr:nth-child(even) { background:#121821; }"
    "code { background:#1a2332; color:#79c0ff; padding:1px 5px; border-radius:3px; }"
    ".tag { display:inline-block; background:#1a2332; color:#58a6ff; "
    "border:1px solid #273142; border-radius:3px; padding:1px 6px; font-size:11px; }"
)


def _html_page(body: str) -> str:
    return f"<html><head><style>{_HELP_CSS}</style></head><body>{body}</body></html>"


_GETTING_STARTED = _html_page("""
<h2>Getting Started</h2>

<h3>Why SwiftCopy exists</h3>
<p>Windows Explorer freezes — or the whole system crashes — when you try to copy files from a
<b>failing or unreliable drive</b>. That happens because Explorer retries indefinitely on every
read error, stalling the I/O queue until the OS gives up. SwiftCopy uses Windows'
<b>robocopy</b> utility under the hood with fault-tolerant settings (zero retries, skip locked
files, restartable mode) so it keeps moving instead of hanging. You get your files out before
the drive gets worse.</p>

<h3>Step 1 — Choose your source</h3>
<p>Use the <b>Left</b> or <b>Right</b> pane to navigate to the folder (or files) you want to copy.
You can type a path directly in the address bar and press <b>Enter</b>, click <b>…</b> to browse,
click <b>Up</b> (or press <b>Backspace</b>) to go up one level, or double-click a folder to open it.</p>

<h3>Step 2 — Choose your destination</h3>
<p>Navigate the <i>opposite</i> pane to the folder where you want the files to land.
You only need to select the destination folder — no need to select files there.</p>

<h3>Step 3 — Start copying</h3>
<p>Press <b>F5</b> (or click <b>Copy →</b> / <b>← Copy</b> in the toolbar) to start.
For a failing drive, select the <b>Failing drive (safe)</b> preset first — it applies the
safest combination of options automatically.</p>
<p>You can also drag files from one pane and drop them onto the other.</p>

<h3>Monitoring progress</h3>
<p>The status bar at the bottom shows live file counts, bytes transferred, speed, and a progress bar.
The log panel shows all robocopy output — use the <b>All / Errors / Warnings</b> filter to focus on problems.</p>

<h3>Job queue</h3>
<p>You can queue multiple copy operations. Each new copy request is added to the queue and processed
in order. The <b>Queue</b> counter in the status bar shows how many jobs are waiting.</p>

<h3>Tip: run a second pass</h3>
<p>After rescuing files from a failing drive, run the same copy again. Files that were busy or
skipped on the first pass may be available on the second. SwiftCopy will skip already-copied
files and only pick up what's missing.</p>
""")

_OPTIONS_REFERENCE = _html_page("""
<h2>Options Reference</h2>
<table>
<tr><th>Option</th><th>What it does</th><th>robocopy flag</th></tr>
<tr><td><b>Preserve timestamps/permissions</b></td>
    <td>Copies file timestamps and security info (ACLs). Recommended for backups.</td>
    <td><code>/COPY:DATS /DCOPY:DAT</code></td></tr>
<tr><td><b>Conservative mode</b></td>
    <td>Copies only data and timestamps — no ACLs. Safest for cross-account copies.</td>
    <td><code>/COPY:DAT /DCOPY:DAT</code></td></tr>
<tr><td><b>Include auditing info</b></td>
    <td>Also copies the auditing ACE entries. Requires elevated privileges.</td>
    <td><code>/COPYALL</code></td></tr>
<tr><td><b>Retry tuning</b></td>
    <td>Enables the Retries (R) and Wait (W) spinboxes below.</td>
    <td><code>/R:n /W:m</code></td></tr>
<tr><td><b>Retries (R)</b></td>
    <td>How many times to retry a failed file. 0 = never retry (best for failing drives).</td>
    <td><code>/R:n</code></td></tr>
<tr><td><b>Wait (W)</b></td>
    <td>Seconds to wait between retries. 0 = no delay.</td>
    <td><code>/W:m</code></td></tr>
<tr><td><b>Skip locked files</b></td>
    <td>Forces R=0 and W=0 so robocopy never hangs waiting on locked/busy files.</td>
    <td><code>/R:0 /W:0</code></td></tr>
<tr><td><b>Backup mode (/B)</b></td>
    <td>Uses backup semantics to copy files even if you lack normal read permission.
    Requires the SeBackupPrivilege right (usually admin).</td>
    <td><code>/ZB</code></td></tr>
<tr><td><b>Logging</b></td>
    <td>Appends robocopy output to a timestamped log file on disk.</td>
    <td><code>/LOG+:file</code></td></tr>
<tr><td><b>Mode: Mirror</b></td>
    <td>Makes destination an exact mirror of source — <b>deletes</b> files at dest not in source.</td>
    <td><code>/MIR</code></td></tr>
<tr><td><b>Mode: Copy (append)</b></td>
    <td>Copies everything including subdirectories without deleting anything at the destination.</td>
    <td><code>/E</code></td></tr>
</table>
""")

_PRESETS = _html_page("""
<h2>Presets</h2>
<h3>Custom</h3>
<p>All options are set manually. Nothing changes when you select this preset.</p>

<h3>Failing drive (safe)</h3>
<p>Best choice when copying from a drive that is <b>failing or very slow</b>:
<ul>
  <li>R = 0, W = 0 — never wait or retry a stuck file, just skip and move on.</li>
  <li>Skip locked files — same effect, prevents hanging on in-use files.</li>
  <li>Mode: Copy (append) — never deletes anything at the destination.</li>
  <li>Preserve timestamps/permissions — keeps all metadata.</li>
</ul>
Use this when the drive is making clicking noises or progress stalls frequently.</p>

<h3>Failing drive (fast)</h3>
<p>Slightly faster variant: R = 1, W = 1 — makes one quick retry before skipping.
Useful when errors are occasional rather than systematic.</p>

<p><b>Tip:</b> After rescuing files from a failing drive, run a second pass with the same settings
to pick up any files that were busy during the first run.</p>
""")

_SHORTCUTS = _html_page("""
<h2>Keyboard Shortcuts</h2>
<table>
<tr><th>Key</th><th>Action</th></tr>
<tr><td><span class="tag">F5</span></td><td>Copy left → right (same as clicking Copy →)</td></tr>
<tr><td><span class="tag">F6</span></td><td>Move left → right (files are deleted from source after copy)</td></tr>
<tr><td><span class="tag">Escape</span></td><td>Stop the current running job</td></tr>
<tr><td><span class="tag">F1</span></td><td>Open this User Guide</td></tr>
<tr><td><span class="tag">Backspace</span></td><td>Go up one directory in the focused pane</td></tr>
<tr><td><span class="tag">Enter</span></td><td>Navigate into a folder (in path bar: go to typed path)</td></tr>
<tr><td><span class="tag">Double-click</span></td><td>Open a folder in the file tree</td></tr>
</table>

<h3>Drag & Drop</h3>
<p>Drag files or folders from either pane and drop them onto the other pane's file tree.
A prompt will ask whether to <b>Copy</b> or <b>Move</b> the dropped items.</p>
""")


class HelpDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — User Guide")
        self.resize(700, 520)

        tabs = QTabWidget()
        for label, content in [
            ("Getting Started", _GETTING_STARTED),
            ("Options Reference", _OPTIONS_REFERENCE),
            ("Presets", _PRESETS),
            ("Shortcuts", _SHORTCUTS),
        ]:
            view = QTextEdit()
            view.setReadOnly(True)
            view.setHtml(content)
            view.setStyleSheet("QTextEdit { border: none; }")
            tabs.addTab(view, label)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)


# ---------------------------------------------------------------------------
# File browser components
# ---------------------------------------------------------------------------

class FileView(QTreeView):
    dropped = Signal(list)

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths:
                self.dropped.emit(paths)
                event.acceptProposedAction()
                return
        super().dropEvent(event)


class BrightIconProvider(QFileIconProvider):
    def icon(self, info):
        if isinstance(info, QFileInfo) and info.isDir():
            base = super().icon(info)
            return self._brighten_icon(base)
        return super().icon(info)

    @staticmethod
    def _brighten_icon(icon: QIcon, factor: float = 1.2) -> QIcon:
        pixmap = icon.pixmap(20, 20)
        if pixmap.isNull():
            return icon
        image = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixelColor(x, y)
                if pixel.alpha() == 0:
                    continue
                pixel.setRed(min(255, int(pixel.red() * factor)))
                pixel.setGreen(min(255, int(pixel.green() * factor)))
                pixel.setBlue(min(255, int(pixel.blue() * factor)))
                image.setPixelColor(x, y, pixel)
        return QIcon(QPixmap.fromImage(image))


class FilePane(QWidget):
    def __init__(self, label_text: str, start_path: str) -> None:
        super().__init__()
        self.label = QLabel(label_text)
        self.path_edit = QLineEdit(start_path)
        self.path_edit.setToolTip("Current folder path. Type a path and press Enter to navigate.")
        self.browse_button = QPushButton("...")
        self.browse_button.setFixedWidth(32)
        self.browse_button.setToolTip("Browse for a folder")
        self.up_button = QPushButton("Up")
        self.up_button.setFixedWidth(48)
        self.up_button.setToolTip("Go up one directory level (Backspace)")

        self.model = QFileSystemModel(self)
        self.model.setIconProvider(BrightIconProvider())
        self.model.setRootPath(start_path)

        self.view = FileView(self)
        self.view.setModel(self.model)
        self.view.setRootIndex(self.model.index(start_path))
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(0, Qt.AscendingOrder)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setDragEnabled(True)
        self.view.setAcceptDrops(True)
        self.view.setDropIndicatorShown(True)
        self.view.setDefaultDropAction(Qt.CopyAction)
        self.view.setToolTip(
            "File browser. Click to select files/folders.\n"
            "Double-click a folder to open it.\n"
            "Drag items here to copy or move them."
        )
        self.view.doubleClicked.connect(self._open_item)

        path_row = QHBoxLayout()
        path_row.addWidget(self.label)
        path_row.addWidget(self.path_edit)
        path_row.addWidget(self.up_button)
        path_row.addWidget(self.browse_button)

        layout = QVBoxLayout(self)
        layout.addLayout(path_row)
        layout.addWidget(self.view)

        self.browse_button.clicked.connect(self._browse)
        self.path_edit.returnPressed.connect(self._set_root_from_edit)
        self.up_button.clicked.connect(self._go_up)

    def _browse(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose Folder", self.path_edit.text())
        if directory:
            self.set_root_path(directory)

    def _set_root_from_edit(self) -> None:
        path = self.path_edit.text().strip()
        if path and os.path.isdir(path):
            self.set_root_path(path)

    def set_root_path(self, path: str) -> None:
        self.path_edit.setText(path)
        self.view.setRootIndex(self.model.index(path))

    def _open_item(self, index) -> None:
        if not index.isValid():
            return
        file_path = self.model.filePath(index)
        if os.path.isdir(file_path):
            self.set_root_path(file_path)

    def _go_up(self) -> None:
        current = self.path_edit.text().strip()
        if not current:
            return
        parent = os.path.dirname(current.rstrip(os.sep))
        if parent and os.path.isdir(parent):
            self.set_root_path(parent)

    def get_selection(self) -> list[str]:
        indexes = self.view.selectionModel().selectedRows()
        return [self.model.filePath(idx) for idx in indexes]


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1200, 720)

        self.settings = QSettings("SwiftCopy", "SwiftCopy")
        left_path = self.settings.value("paths/left", "", str)
        right_path = self.settings.value("paths/right", "", str)

        home = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        self.left_pane = FilePane("Left", left_path or home)
        self.right_pane = FilePane("Right", right_path or home)

        splitter = QSplitter()
        splitter.addWidget(self.left_pane)
        splitter.addWidget(self.right_pane)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setAcceptRichText(True)

        self.log_entries: list[tuple[str, str]] = []
        self.log_filter = QComboBox()
        self.log_filter.addItems(["All", "Errors", "Warnings"])
        self.log_filter.setToolTip("Filter log output by severity")
        self.log_filter.currentIndexChanged.connect(self._refresh_log_view)
        self.log_clear = QPushButton("Clear Log")
        self.log_clear.setToolTip("Clear all log entries")
        self.log_clear.clicked.connect(self._clear_log)

        self.log_container = QWidget()
        log_layout = QVBoxLayout(self.log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_row = QHBoxLayout()
        log_row.addWidget(QLabel("Log"))
        log_row.addWidget(self.log_filter)
        log_row.addStretch(1)
        log_row.addWidget(self.log_clear)
        log_layout.addLayout(log_row)
        log_layout.addWidget(self.output)

        self.total_bytes: int | None = None
        self.copied_bytes = 0
        self.job_queue: list[dict] = []
        self.current_job: dict | None = None
        self.total_files: int | None = None
        self.copied_files = 0

        self.copy_options = self._build_options_box()
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.status_label = QLabel("Idle")
        self.phase_label = QLabel("Phase: Idle")
        self.stats_label = QLabel("Files: -")
        self.bytes_label = QLabel("Bytes: -")
        self.speed_label = QLabel("Speed: -")
        self.queue_label = QLabel("Queue: 0")
        self.queue_label.setToolTip("Number of copy jobs waiting in queue")
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.phase_label)
        self.status_bar.addPermanentWidget(self.stats_label)
        self.status_bar.addPermanentWidget(self.bytes_label)
        self.status_bar.addPermanentWidget(self.speed_label)
        self.status_bar.addPermanentWidget(self.queue_label)
        self.status_bar.addPermanentWidget(self.progress)

        # Author credit — permanent right-side label
        credit = QLabel(
            f'<a href="{GITHUB_URL}" style="color:#9fb2c9; text-decoration:none;">'
            f'{APP_NAME} v{APP_VERSION} · by Maciej</a>'
        )
        credit.setOpenExternalLinks(True)
        credit.setToolTip(f"Visit {GITHUB_URL}")
        self.status_bar.addPermanentWidget(credit)

        central = QWidget()
        layout = QVBoxLayout(central)

        # First-run welcome bar (inserted at top if applicable)
        tip_bar = self._build_first_run_tip()
        if tip_bar is not None:
            layout.addWidget(tip_bar)

        layout.addWidget(splitter)
        layout.addWidget(self.copy_options)
        current_row = QHBoxLayout()
        self.current_file_label = QLabel("Current: -")
        self.current_file_pct = QLabel("0%")
        self.file_count_label = QLabel("Files: -")
        current_row.addWidget(self.current_file_label)
        current_row.addStretch(1)
        current_row.addWidget(self.current_file_pct)
        current_row.addWidget(self.file_count_label)
        layout.addLayout(current_row)
        layout.addWidget(self.log_container)
        self.setCentralWidget(central)

        self._build_toolbar()
        self._build_menu_bar()
        self._setup_shortcuts()
        self._apply_theme()
        self._toggle_log_visibility(self.show_log.isChecked())

        self.left_pane.view.dropped.connect(lambda paths: self._handle_drop(paths, self.left_pane))
        self.right_pane.view.dropped.connect(lambda paths: self._handle_drop(paths, self.right_pane))

    # ------------------------------------------------------------------
    # First-run welcome bar
    # ------------------------------------------------------------------

    def _build_first_run_tip(self) -> QFrame | None:
        if self.settings.value("first_run_shown", False, bool):
            return None
        self.settings.setValue("first_run_shown", True)

        bar = QFrame()
        bar.setObjectName("tipBar")
        bar.setStyleSheet(
            "QFrame#tipBar { background-color: #0d2b18; border: 1px solid #2ea043; "
            "border-radius: 4px; }"
        )
        row = QHBoxLayout(bar)
        row.setContentsMargins(10, 5, 6, 5)

        msg = QLabel(
            "<b>Welcome to SwiftCopy!</b> Copying from a failing drive? Select the "
            "<b>Failing drive (safe)</b> preset, pick your source on the left and destination "
            "on the right, then press <b>F5</b>. Press <b>F1</b> for the full User Guide."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("QLabel { color: #d7dde8; border: none; background: transparent; }")

        dismiss = QPushButton("×")
        dismiss.setFixedSize(22, 22)
        dismiss.setToolTip("Dismiss")
        dismiss.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: #9fb2c9; font-size: 14px; }"
            "QPushButton:hover { color: #d7dde8; }"
        )
        dismiss.clicked.connect(bar.hide)

        row.addWidget(msg, 1)
        row.addWidget(dismiss)
        return bar

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        copy_ltr = QAction("Copy →", self)
        copy_ltr.setToolTip("Copy selected items from left pane to right pane (F5)")
        copy_rtl = QAction("← Copy", self)
        copy_rtl.setToolTip("Copy selected items from right pane to left pane")
        stop_action = QAction("Stop", self)
        stop_action.setToolTip("Stop the current running job (Escape)")
        stop_all_action = QAction("Stop All", self)
        stop_all_action.setToolTip("Stop the current job and clear the entire queue")

        copy_ltr.triggered.connect(lambda: self._start_copy(self.left_pane, self.right_pane))
        copy_rtl.triggered.connect(lambda: self._start_copy(self.right_pane, self.left_pane))
        stop_action.triggered.connect(self._stop_copy)
        stop_all_action.triggered.connect(self._stop_all)

        toolbar.addAction(copy_ltr)
        toolbar.addAction(copy_rtl)
        toolbar.addAction(stop_action)
        toolbar.addAction(stop_all_action)

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _build_menu_bar(self) -> None:
        menubar = self.menuBar()
        help_menu = menubar.addMenu("&Help")

        guide_action = QAction("User Guide\tF1", self)
        guide_action.triggered.connect(self._show_help)
        help_menu.addAction(guide_action)

        help_menu.addSeparator()

        github_action = QAction("View on GitHub", self)
        github_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        help_menu.addAction(github_action)

        help_menu.addSeparator()

        about_action = QAction(f"About {APP_NAME}", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("F5"), self).activated.connect(
            lambda: self._start_copy(self.left_pane, self.right_pane)
        )
        QShortcut(QKeySequence("F6"), self).activated.connect(
            lambda: self._start_move(self.left_pane, self.right_pane)
        )
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._stop_copy)
        QShortcut(QKeySequence("F1"), self).activated.connect(self._show_help)
        QShortcut(QKeySequence("Backspace"), self).activated.connect(self._go_up_focused_pane)

    def _go_up_focused_pane(self) -> None:
        focus = QApplication.focusWidget()
        if focus is None:
            return
        for pane in (self.left_pane, self.right_pane):
            if pane.isAncestorOf(focus) or focus is pane:
                pane._go_up()
                return

    # ------------------------------------------------------------------
    # Dialog helpers
    # ------------------------------------------------------------------

    def _show_help(self) -> None:
        dlg = HelpDialog(self)
        dlg.setStyleSheet(dark_theme_stylesheet())
        dlg.exec()

    def _show_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.setStyleSheet(dark_theme_stylesheet())
        dlg.exec()

    # ------------------------------------------------------------------
    # Options panel
    # ------------------------------------------------------------------

    def _build_options_box(self) -> QGroupBox:
        box = QGroupBox("Robocopy Options")

        self.copy_all = QCheckBox("Preserve timestamps/permissions")
        self.copy_all.setChecked(True)
        self.copy_all.setToolTip(
            "Copy file timestamps and ACLs alongside data.\n"
            "Robocopy flag: /COPY:DATS /DCOPY:DAT"
        )

        self.conservative_mode = QCheckBox("Conservative mode (minimize metadata)")
        self.conservative_mode.setChecked(False)
        self.conservative_mode.setToolTip(
            "Copy only data and timestamps — no ACLs.\n"
            "Safest option for cross-account or cross-domain copies.\n"
            "Robocopy flag: /COPY:DAT /DCOPY:DAT"
        )

        self.include_audit = QCheckBox("Include auditing info")
        self.include_audit.setChecked(False)
        self.include_audit.setToolTip(
            "Copy auditing ACE entries in addition to all other metadata.\n"
            "Requires elevated (admin) privileges.\n"
            "Robocopy flag: /COPYALL"
        )

        self.retry_tuning = QCheckBox("Retry tuning")
        self.retry_tuning.setChecked(True)
        self.retry_tuning.setToolTip(
            "Enable the Retries (R) and Wait (W) controls below.\n"
            "When off, robocopy defaults are used (1 retry, 30s wait)."
        )

        self.skip_locked = QCheckBox("Skip locked files")
        self.skip_locked.setChecked(True)
        self.skip_locked.setToolTip(
            "Force R=0 W=0 — never wait on locked or busy files, just skip them.\n"
            "Essential for copying from live systems or failing drives."
        )

        self.backup_mode = QCheckBox("Backup mode (/B)")
        self.backup_mode.setChecked(False)
        self.backup_mode.setToolTip(
            "Use backup semantics (/ZB) to read files even without normal read permission.\n"
            "Requires SeBackupPrivilege (usually admin). Falls back to /Z if unavailable."
        )

        self.logging = QCheckBox("Logging")
        self.logging.setChecked(True)
        self.logging.setToolTip(
            "Append robocopy output to a timestamped log file on disk.\n"
            "Useful for auditing and post-run review."
        )

        self.show_log = QCheckBox("Show log")
        self.show_log.setChecked(True)
        self.show_log.setToolTip("Show or hide the log panel below")
        self.show_log.toggled.connect(self._toggle_log_visibility)

        preset_label = QLabel("Preset")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom",
            "Failing drive (safe)",
            "Failing drive (fast)",
        ])
        self.preset_combo.setToolTip(
            "Quick-apply a set of options for a common scenario.\n"
            "• Failing drive (safe): R=0 W=0, skip locked, copy mode\n"
            "• Failing drive (fast): R=1 W=1, skip locked, copy mode\n"
            "Press F1 for detailed preset descriptions."
        )
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)

        self.retry_count = QSpinBox()
        self.retry_count.setRange(0, 100)
        self.retry_count.setValue(3)
        self.retry_count.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.retry_count.setToolTip("Number of retries per failed file (R). 0 = never retry.")
        self.retry_dec = QPushButton("-")
        self.retry_inc = QPushButton("+")
        self.retry_dec.setFixedWidth(24)
        self.retry_inc.setFixedWidth(24)
        self.retry_dec.setToolTip("Decrease retry count")
        self.retry_inc.setToolTip("Increase retry count")
        self.retry_dec.clicked.connect(lambda: self._adjust_spin(self.retry_count, -1))
        self.retry_inc.clicked.connect(lambda: self._adjust_spin(self.retry_count, 1))
        self.wait_time = QSpinBox()
        self.wait_time.setRange(0, 600)
        self.wait_time.setValue(5)
        self.wait_time.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.wait_time.setToolTip("Seconds to wait between retries (W). 0 = no delay.")
        self.wait_dec = QPushButton("-")
        self.wait_inc = QPushButton("+")
        self.wait_dec.setFixedWidth(24)
        self.wait_inc.setFixedWidth(24)
        self.wait_dec.setToolTip("Decrease wait time")
        self.wait_inc.setToolTip("Increase wait time")
        self.wait_dec.clicked.connect(lambda: self._adjust_spin(self.wait_time, -1))
        self.wait_inc.clicked.connect(lambda: self._adjust_spin(self.wait_time, 1))

        self.log_path = QLineEdit(self._default_log_path())
        self.log_path.setToolTip("Path to the log file. A date suffix is added automatically.")
        self.log_browse = QPushButton("...")
        self.log_browse.setFixedWidth(32)
        self.log_browse.setToolTip("Browse for log file location")
        self.log_browse.clicked.connect(self._pick_log_path)

        mode_label = QLabel("Mode")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Mirror (source truth)", "Copy (append)"])
        self.mode_combo.setCurrentIndex(1)
        self.mode_combo.setToolTip(
            "Mirror: destination becomes an exact copy of source — extra files at dest are DELETED (/MIR).\n"
            "Copy: copies everything without deleting anything at the destination (/E)."
        )

        retry_r_label = QLabel("R")
        retry_r_label.setToolTip("Retries — how many times to retry a failed file")
        retry_w_label = QLabel("W")
        retry_w_label.setToolTip("Wait — seconds between retries")

        row_one = QHBoxLayout()
        row_one.addWidget(self.copy_all)
        row_one.addWidget(self.conservative_mode)
        row_one.addWidget(self.include_audit)
        row_one.addWidget(self.retry_tuning)
        row_one.addWidget(retry_r_label)
        row_one.addWidget(self.retry_count)
        row_one.addWidget(self.retry_dec)
        row_one.addWidget(self.retry_inc)
        row_one.addWidget(retry_w_label)
        row_one.addWidget(self.wait_time)
        row_one.addWidget(self.wait_dec)
        row_one.addWidget(self.wait_inc)
        row_one.addWidget(self.skip_locked)
        row_one.addWidget(self.backup_mode)

        row_two = QHBoxLayout()
        row_two.addWidget(self.logging)
        row_two.addWidget(self.show_log)
        row_two.addWidget(self.log_path)
        row_two.addWidget(self.log_browse)
        row_two.addWidget(mode_label)
        row_two.addWidget(self.mode_combo)
        row_two.addWidget(preset_label)
        row_two.addWidget(self.preset_combo)

        options_layout = QVBoxLayout()
        options_layout.addLayout(row_one)
        options_layout.addLayout(row_two)

        box.setLayout(options_layout)
        return box

    def _default_log_path(self) -> str:
        app_data = QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
        if not app_data:
            app_data = os.getcwd()
        os.makedirs(app_data, exist_ok=True)
        return os.path.join(app_data, "robocopy.log")

    def _pick_log_path(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Log File", self.log_path.text(), "Log (*.log)")
        if path:
            self.log_path.setText(path)

    # ------------------------------------------------------------------
    # Copy / Move logic
    # ------------------------------------------------------------------

    def _start_copy(self, source_pane: FilePane, dest_pane: FilePane) -> None:
        dest_path = dest_pane.path_edit.text().strip()
        if not dest_path or not os.path.isdir(dest_path):
            QMessageBox.warning(self, "Destination Needed", "Select a valid destination folder.")
            return

        jobs = self._build_jobs_from_pane(source_pane, dest_path, move=False)
        if not jobs:
            QMessageBox.warning(self, "Source Needed", "Select a valid source folder or file.")
            return

        self._enqueue_jobs(jobs)
        self._start_next_job()

    def _start_move(self, source_pane: FilePane, dest_pane: FilePane) -> None:
        dest_path = dest_pane.path_edit.text().strip()
        if not dest_path or not os.path.isdir(dest_path):
            QMessageBox.warning(self, "Destination Needed", "Select a valid destination folder.")
            return

        jobs = self._build_jobs_from_pane(source_pane, dest_path, move=True)
        if not jobs:
            QMessageBox.warning(self, "Source Needed", "Select a valid source folder or file.")
            return

        self._enqueue_jobs(jobs)
        self._start_next_job()

    def _resolve_source(self, pane: FilePane) -> tuple[str | None, list[str]]:
        selection = pane.get_selection()
        if not selection:
            return pane.path_edit.text().strip(), []

        files = [path for path in selection if os.path.isfile(path)]
        dirs = [path for path in selection if os.path.isdir(path)]

        if dirs:
            return dirs[0], []

        parent = os.path.dirname(files[0]) if files else ""
        names = [os.path.basename(path) for path in files]
        return parent, names

    def _build_jobs_from_pane(self, pane: FilePane, dest_path: str, move: bool) -> list[dict]:
        selection = pane.get_selection()
        if not selection:
            source_path = pane.path_edit.text().strip()
            if not source_path or not os.path.isdir(source_path):
                return []
            return [self._make_job(source_path, dest_path, [], move, is_dir=True)]

        dirs = sorted([path for path in selection if os.path.isdir(path)])
        files = sorted([path for path in selection if os.path.isfile(path)])
        jobs: list[dict] = []

        for folder in dirs:
            folder_dest = os.path.join(dest_path, os.path.basename(folder))
            jobs.append(self._make_job(folder, folder_dest, [], move, is_dir=True))

        file_groups: dict[str, list[str]] = {}
        for file_path in files:
            parent = os.path.dirname(file_path)
            file_groups.setdefault(parent, []).append(os.path.basename(file_path))

        for parent, names in sorted(file_groups.items()):
            jobs.append(self._make_job(parent, dest_path, sorted(names), move, is_dir=False))

        return jobs

    def _build_jobs_from_paths(self, paths: list[str], dest_path: str, move: bool) -> list[dict]:
        dirs = sorted([path for path in paths if os.path.isdir(path)])
        files = sorted([path for path in paths if os.path.isfile(path)])
        jobs: list[dict] = []

        for folder in dirs:
            folder_dest = os.path.join(dest_path, os.path.basename(folder))
            jobs.append(self._make_job(folder, folder_dest, [], move, is_dir=True))

        file_groups: dict[str, list[str]] = {}
        for file_path in files:
            parent = os.path.dirname(file_path)
            file_groups.setdefault(parent, []).append(os.path.basename(file_path))

        for parent, names in sorted(file_groups.items()):
            jobs.append(self._make_job(parent, dest_path, sorted(names), move, is_dir=False))

        return jobs

    def _make_job(self, source: str, dest: str, files: list[str], move: bool, is_dir: bool) -> dict:
        return {"source": source, "dest": dest, "files": files, "move": move, "is_dir": is_dir}

    def _enqueue_jobs(self, jobs: list[dict]) -> None:
        def sort_key(job: dict) -> tuple[int, str]:
            return (0 if job["is_dir"] else 1, job["source"].lower())

        self.job_queue.extend(sorted(jobs, key=sort_key))
        self.queue_label.setText(f"Queue: {len(self.job_queue)}")

    def _start_next_job(self) -> None:
        if self.process.state() != QProcess.NotRunning:
            return
        if not self.job_queue:
            self.current_job = None
            self.queue_label.setText("Queue: 0")
            return

        self.current_job = self.job_queue.pop(0)
        self.queue_label.setText(f"Queue: {len(self.job_queue)}")

        source = self.current_job["source"]
        dest = self.current_job["dest"]
        files = self.current_job["files"]
        move = self.current_job["move"]
        is_dir = self.current_job["is_dir"]

        args = self._build_robocopy_args(source, dest, files, move, is_dir)
        self.total_bytes = None
        self.copied_bytes = 0
        self.total_files = None
        self.copied_files = 0
        self._append_log_line(self._format_command(args))
        self.status_label.setText("Running")
        self.phase_label.setText("Phase: Scanning")
        self.stats_label.setText("Files: -")
        self.bytes_label.setText("Bytes: -")
        self.speed_label.setText("Speed: -")
        self.current_file_label.setText("Current: -")
        self.current_file_pct.setText("0%")
        self.file_count_label.setText("Files: -")
        self.progress.setRange(0, 0)
        self.process.start("robocopy", args)

    def _build_robocopy_args(
        self,
        source: str,
        dest: str,
        files: list[str],
        move: bool = False,
        is_dir: bool = True,
    ) -> list[str]:
        args = [source, dest]
        args.extend(files)

        if is_dir:
            if self.mode_combo.currentIndex() == 0:
                args.append("/MIR")
            else:
                args.append("/E")

        if self.conservative_mode.isChecked():
            args.append("/COPY:DAT")
            args.append("/DCOPY:DAT")
        elif self.copy_all.isChecked():
            if self.include_audit.isChecked():
                args.append("/COPYALL")
            else:
                args.append("/COPY:DATS")
            args.append("/DCOPY:DAT")
        else:
            args.append("/COPY:DAT")
            args.append("/DCOPY:DAT")

        retry_count = self.retry_count.value() if self.retry_tuning.isChecked() else 1
        wait_time = self.wait_time.value() if self.retry_tuning.isChecked() else 1
        if self.skip_locked.isChecked():
            retry_count = 0
            wait_time = 0

        args.append(f"/R:{retry_count}")
        args.append(f"/W:{wait_time}")
        if self.backup_mode.isChecked():
            args.append("/ZB")
        else:
            args.append("/Z")
        args.append("/XJ")
        args.append("/TEE")

        if move:
            args.append("/MOVE")

        if self.logging.isChecked():
            timestamp = datetime.now().strftime("%Y%m%d")
            log_path = self.log_path.text().strip()
            if log_path:
                base, ext = os.path.splitext(log_path)
                log_file = f"{base}_{timestamp}{ext or '.log'}"
                args.append(f"/LOG+:{log_file}")

        return args

    def _format_command(self, args: list[str]) -> str:
        safe_args = ["robocopy"] + args
        return "> " + " ".join(shlex.quote(part) for part in safe_args)

    # ------------------------------------------------------------------
    # Output parsing
    # ------------------------------------------------------------------

    def _handle_output(self, text: str) -> None:
        if not text:
            return
        for line in text.splitlines():
            self._parse_status_line(line)
            self._append_log_line(line)

    def _parse_status_line(self, line: str) -> None:
        match = re.match(r"^\s*Files\s*:\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
        if match:
            groups = match.groups()
            total, copied, skipped, failed = groups[0], groups[1], groups[2], groups[4]
            self.total_files = int(total)
            self.copied_files = int(copied)
            self.stats_label.setText(
                f"Files: {total} | Copied: {copied} | Skipped: {skipped} | Failed: {failed}"
            )
            self.file_count_label.setText(f"Files: {copied}/{total}")
            return

        if line.lstrip().startswith("Bytes"):
            parts = line.split(":", 1)[1].strip().split()
            sizes = []
            idx = 0
            for _ in range(6):
                if idx >= len(parts):
                    break
                token = parts[idx]
                if idx + 1 < len(parts) and parts[idx + 1].isalpha():
                    token = token + parts[idx + 1]
                    idx += 2
                else:
                    idx += 1
                sizes.append(token)
            if len(sizes) >= 2:
                total = self._parse_size_token(sizes[0])
                copied = self._parse_size_token(sizes[1])
                if total is not None and total > 0:
                    self.total_bytes = total
                if copied is not None:
                    self.copied_bytes = copied
                self._update_progress()
                if self.total_bytes:
                    self.bytes_label.setText(
                        f"Bytes: {self._format_bytes(self.copied_bytes)} / {self._format_bytes(self.total_bytes)}"
                    )
                self.phase_label.setText("Phase: Copying")
            return

        if line.lstrip().startswith("Speed"):
            speed = line.split(":", 1)[1].strip()
            self.speed_label.setText(f"Speed: {speed}")
            return

        percent_match = re.match(r"^\s*(\d+)%\s+(.*)$", line)
        if percent_match:
            pct, name = percent_match.groups()
            self.current_file_label.setText(f"Current: {name}")
            self.current_file_pct.setText(f"{pct}%")
            return

    def _read_stdout(self) -> None:
        data = self.process.readAllStandardOutput().data().decode(errors="ignore")
        self._handle_output(data.rstrip())

    def _read_stderr(self) -> None:
        data = self.process.readAllStandardError().data().decode(errors="ignore")
        self._handle_output(data.rstrip())

    def _process_finished(self) -> None:
        exit_code = self.process.exitCode()
        summary = self._robocopy_exit_summary(exit_code)
        self._append_log_line(f"Robocopy finished with exit code {exit_code}: {summary}.")
        self.status_label.setText(summary)
        self.phase_label.setText("Phase: Done")
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self._start_next_job()

    def _stop_copy(self) -> None:
        if self.process.state() == QProcess.NotRunning:
            return
        self.process.terminate()
        if not self.process.waitForFinished(2000):
            self.process.kill()

    def _stop_all(self) -> None:
        self.job_queue.clear()
        self.current_job = None
        self.queue_label.setText("Queue: 0")
        self._stop_copy()
        self.status_label.setText("Stopped")
        self.phase_label.setText("Phase: Stopped")

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        self.setStyleSheet(dark_theme_stylesheet())

    def _toggle_log_visibility(self, visible: bool) -> None:
        self.log_container.setVisible(visible)
        self.log_filter.setEnabled(visible)
        self.log_clear.setEnabled(visible)

    def _adjust_spin(self, spin: QSpinBox, delta: int) -> None:
        spin.setValue(spin.value() + delta)

    def _clear_log(self) -> None:
        self.log_entries.clear()
        self.output.clear()

    def _refresh_log_view(self) -> None:
        self.output.clear()
        for level, line in self.log_entries:
            if self._filter_allows(level):
                self.output.append(self._format_log_html(level, line))

    def _append_log_line(self, line: str) -> None:
        level = self._log_level_for_line(line)
        self.log_entries.append((level, line))
        if self._filter_allows(level):
            self.output.append(self._format_log_html(level, line))

    def _format_log_html(self, level: str, line: str) -> str:
        color = {"error": "#ff6b6b", "warning": "#f2c879", "info": "#cbd5e1"}.get(level, "#cbd5e1")
        return f"<span style=\"color:{color}\">{html.escape(line)}</span>"

    def _log_level_for_line(self, line: str) -> str:
        upper = line.upper()
        if "ERROR" in upper or "FATAL" in upper:
            return "error"
        if "WARNING" in upper or "WARN" in upper or "NOTE" in upper:
            return "warning"
        return "info"

    def _filter_allows(self, level: str) -> bool:
        mode = self.log_filter.currentText()
        if mode == "Errors":
            return level == "error"
        if mode == "Warnings":
            return level == "warning"
        return True

    def _parse_size_token(self, token: str) -> int | None:
        match = re.match(r"^([0-9.]+)([kmgt]?)(b)?$", token.lower())
        if not match:
            return None
        number, unit, _ = match.groups()
        value = float(number)
        scale = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}.get(unit, 1)
        return int(value * scale)

    def _format_bytes(self, value: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(value)
        idx = 0
        while size >= 1024 and idx < len(units) - 1:
            size /= 1024
            idx += 1
        return f"{size:.2f} {units[idx]}"

    def _update_progress(self) -> None:
        if self.total_bytes and self.total_bytes > 0:
            ratio = min(self.copied_bytes / self.total_bytes, 1.0)
            self.progress.setRange(0, 1000)
            self.progress.setValue(int(ratio * 1000))
        else:
            self.progress.setRange(0, 0)

    def _handle_drop(self, paths: list[str], dest_pane: FilePane) -> None:
        dest_path = dest_pane.path_edit.text().strip()
        if not dest_path or not os.path.isdir(dest_path):
            QMessageBox.warning(self, "Destination Needed", "Select a valid destination folder.")
            return

        action = self._prompt_drag_action()
        if action is None:
            return

        jobs = self._build_jobs_from_paths(paths, dest_path, move=action == "move")
        if not jobs:
            return

        self._enqueue_jobs(jobs)
        self._start_next_job()

    def _prompt_drag_action(self) -> str | None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Drop Action")
        dialog.setText("Copy or move the dropped items?")
        copy_button = dialog.addButton("Copy", QMessageBox.AcceptRole)
        move_button = dialog.addButton("Move", QMessageBox.AcceptRole)
        dialog.addButton("Cancel", QMessageBox.RejectRole)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked == copy_button:
            return "copy"
        if clicked == move_button:
            return "move"
        return None

    def closeEvent(self, event) -> None:
        self.settings.setValue("paths/left", self.left_pane.path_edit.text().strip())
        self.settings.setValue("paths/right", self.right_pane.path_edit.text().strip())
        super().closeEvent(event)

    def _robocopy_exit_summary(self, exit_code: int) -> str:
        if exit_code >= 16:
            return "Fatal error"
        if exit_code >= 8:
            return "Some files or directories failed to copy"
        summaries = {
            0: "No files copied",
            1: "Files copied successfully",
            2: "Extra files or directories present",
            3: "Files copied and extras detected",
            5: "Mismatched files detected",
            6: "Extras and mismatches detected",
            7: "Copied files, extras, and mismatches detected",
        }
        return summaries.get(exit_code, "Completed with warnings")

    def _apply_preset(self) -> None:
        preset = self.preset_combo.currentText()
        if preset == "Custom":
            return

        self.copy_all.setChecked(True)
        self.logging.setChecked(True)
        self.skip_locked.setChecked(True)
        self.retry_tuning.setChecked(True)

        if preset == "Failing drive (safe)":
            self.retry_count.setValue(0)
            self.wait_time.setValue(0)
            self.mode_combo.setCurrentIndex(1)
        elif preset == "Failing drive (fast)":
            self.retry_count.setValue(1)
            self.wait_time.setValue(1)
            self.mode_combo.setCurrentIndex(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app = QApplication([])
    app.setStyleSheet(dark_theme_stylesheet())

    # Splash screen
    splash_pix = _build_splash_pixmap()
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    window = MainWindow()
    window.show()
    splash.finish(window)

    app.exec()


if __name__ == "__main__":
    main()
