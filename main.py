import html
import os
import re
import shlex
from datetime import datetime

from PySide6.QtCore import QProcess, QSettings, QSize, QStandardPaths, Qt, Signal
from PySide6.QtGui import QAction, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFileIconProvider,
    QFileSystemModel,
    QFileInfo,
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
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

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
    """


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
        self.browse_button = QPushButton("...")
        self.browse_button.setFixedWidth(32)
        self.up_button = QPushButton("Up")
        self.up_button.setFixedWidth(48)

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


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CopyRobo")
        self.resize(1200, 720)

        self.settings = QSettings("CopyRobo", "CopyRobo")
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
        self.log_filter.currentIndexChanged.connect(self._refresh_log_view)
        self.log_clear = QPushButton("Clear Log")
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
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.phase_label)
        self.status_bar.addPermanentWidget(self.stats_label)
        self.status_bar.addPermanentWidget(self.bytes_label)
        self.status_bar.addPermanentWidget(self.speed_label)
        self.status_bar.addPermanentWidget(self.queue_label)
        self.status_bar.addPermanentWidget(self.progress)

        central = QWidget()
        layout = QVBoxLayout(central)
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
        self._apply_theme()
        self._toggle_log_visibility(self.show_log.isChecked())

        self.left_pane.view.dropped.connect(lambda paths: self._handle_drop(paths, self.left_pane))
        self.right_pane.view.dropped.connect(lambda paths: self._handle_drop(paths, self.right_pane))

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        copy_left_to_right = QAction("Copy ->", self)
        copy_right_to_left = QAction("<- Copy", self)
        stop_action = QAction("Stop", self)
        stop_all_action = QAction("Stop All", self)

        copy_left_to_right.triggered.connect(lambda: self._start_copy(self.left_pane, self.right_pane))
        copy_right_to_left.triggered.connect(lambda: self._start_copy(self.right_pane, self.left_pane))
        stop_action.triggered.connect(self._stop_copy)
        stop_all_action.triggered.connect(self._stop_all)

        toolbar.addAction(copy_left_to_right)
        toolbar.addAction(copy_right_to_left)
        toolbar.addAction(stop_action)
        toolbar.addAction(stop_all_action)

    def _build_options_box(self) -> QGroupBox:
        box = QGroupBox("Robocopy Options")

        self.copy_all = QCheckBox("Preserve timestamps/permissions")
        self.copy_all.setChecked(True)

        self.conservative_mode = QCheckBox("Conservative mode (minimize metadata)")
        self.conservative_mode.setChecked(False)

        self.include_audit = QCheckBox("Include auditing info")
        self.include_audit.setChecked(False)

        self.retry_tuning = QCheckBox("Retry tuning")
        self.retry_tuning.setChecked(True)

        self.skip_locked = QCheckBox("Skip locked files")
        self.skip_locked.setChecked(True)

        self.backup_mode = QCheckBox("Backup mode (/B)")
        self.backup_mode.setChecked(False)

        self.logging = QCheckBox("Logging")
        self.logging.setChecked(True)

        self.show_log = QCheckBox("Show log")
        self.show_log.setChecked(True)
        self.show_log.toggled.connect(self._toggle_log_visibility)

        preset_label = QLabel("Preset")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom",
            "Failing drive (safe)",
            "Failing drive (fast)",
        ])
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)

        self.retry_count = QSpinBox()
        self.retry_count.setRange(0, 100)
        self.retry_count.setValue(3)
        self.retry_dec = QPushButton("-")
        self.retry_inc = QPushButton("+")
        self.retry_dec.setFixedWidth(24)
        self.retry_inc.setFixedWidth(24)
        self.retry_dec.clicked.connect(lambda: self._adjust_spin(self.retry_count, -1))
        self.retry_inc.clicked.connect(lambda: self._adjust_spin(self.retry_count, 1))
        self.wait_time = QSpinBox()
        self.wait_time.setRange(0, 600)
        self.wait_time.setValue(5)
        self.wait_dec = QPushButton("-")
        self.wait_inc = QPushButton("+")
        self.wait_dec.setFixedWidth(24)
        self.wait_inc.setFixedWidth(24)
        self.wait_dec.clicked.connect(lambda: self._adjust_spin(self.wait_time, -1))
        self.wait_inc.clicked.connect(lambda: self._adjust_spin(self.wait_time, 1))

        self.log_path = QLineEdit(self._default_log_path())
        self.log_browse = QPushButton("...")
        self.log_browse.setFixedWidth(32)
        self.log_browse.clicked.connect(self._pick_log_path)

        mode_label = QLabel("Mode")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Mirror (source truth)", "Copy (append)"])
        self.mode_combo.setCurrentIndex(1)

        row_one = QHBoxLayout()
        row_one.addWidget(self.copy_all)
        row_one.addWidget(self.conservative_mode)
        row_one.addWidget(self.include_audit)
        row_one.addWidget(self.retry_tuning)
        row_one.addWidget(QLabel("R"))
        row_one.addWidget(self.retry_count)
        row_one.addWidget(self.retry_dec)
        row_one.addWidget(self.retry_inc)
        row_one.addWidget(QLabel("W"))
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
        return {
            "source": source,
            "dest": dest,
            "files": files,
            "move": move,
            "is_dir": is_dir,
        }

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

    def _handle_output(self, text: str) -> None:
        if not text:
            return
        for line in text.splitlines():
            self._parse_status_line(line)
            self._append_log_line(line)

    def _parse_status_line(self, line: str) -> None:
        match = re.match(r"^\s*Files\s*:\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
        if match:
            total, copied, skipped, mismatch, failed, extras = match.groups()
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


def main() -> None:
    app = QApplication([])
    app.setStyleSheet(dark_theme_stylesheet())
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
