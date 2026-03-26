from __future__ import annotations

import importlib
import json
import site
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT_DIR / "vendor"
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    site.addsitedir(user_site)

from PySide6.QtCore import QDateTime, QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsBlurEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMdiArea,
    QMdiSubWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from main import create_shell, execute_line, startup_message


class PeePiOSDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.context, self.commands = create_shell()
        self.setWindowTitle("PeePiOS")
        self.resize(1180, 760)
        self.setMinimumSize(900, 600)

        self.file_browser_path = self.context.root
        self.note_target_path = None
        self.current_wallpaper_path = None
        self.original_wallpaper = None
        self.scaled_wallpaper = None
        self.browser_profile = None
        self.browser_data_dir = self.context.root / "data" / "browser_profile"
        self.browser_cache_dir = self.browser_data_dir / "cache"
        self.browser_storage_dir = self.browser_data_dir / "storage"
        self.browser_history_path = self.browser_data_dir / "history.json"
        self.browser_cache_dir.mkdir(parents=True, exist_ok=True)
        self.browser_storage_dir.mkdir(parents=True, exist_ok=True)
        self.calculator_expression = ""
        self.windows: dict[str, QMdiSubWindow] = {}
        self.app_modules = {}
        self.frosted_targets: list[dict[str, object]] = []

        self._load_app_modules()

        self.wallpaper_dir = self.context.root / "settings" / "wallpaper"
        self.wallpaper_dir.mkdir(parents=True, exist_ok=True)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.mdi = QMdiArea()
        self.mdi.setViewMode(QMdiArea.SubWindowView)
        self.mdi.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True)
        self.mdi.setStyleSheet("QMdiArea { background: #17202B; border: none; }")
        outer.addWidget(self.mdi, 1)

        self.wallpaper_label = QLabel(self.mdi.viewport())
        self.wallpaper_label.setAlignment(Qt.AlignCenter)
        self.wallpaper_label.setScaledContents(True)
        self.wallpaper_label.hide()
        self.wallpaper_label.lower()

        self.taskbar = QFrame()
        self.taskbar.setFixedHeight(58)
        self.taskbar_background = QLabel(self.taskbar)
        self.taskbar_background.setScaledContents(True)
        self.taskbar_background.setGeometry(self.taskbar.rect())
        self.taskbar_background.lower()
        self._attach_blur(self.taskbar_background, 22)

        taskbar_layout = QHBoxLayout(self.taskbar)
        taskbar_layout.setContentsMargins(12, 8, 12, 8)
        taskbar_layout.setSpacing(8)
        outer.addWidget(self.taskbar)

        self.taskbar_buttons: list[QPushButton] = []
        for label, app_id in [
            ("Exit", None),
            ("Terminal", "terminal"),
            ("Browser", "browser"),
            ("Launcher", "launcher"),
            ("Files", "files"),
            ("Notes", "notes"),
            ("Settings", "settings"),
            ("About", "about"),
            ("Calc", "calculator"),
            ("Monitor", "monitor"),
            ("Clock", "clock"),
            ("App 1", "app1"),
            ("App 2", "app2"),
            ("App 3", "app3"),
        ]:
            button = QPushButton(label)
            if app_id is None:
                button.clicked.connect(self.close)
            else:
                button.clicked.connect(lambda _checked=False, value=app_id: self.open_app(value))
            taskbar_layout.addWidget(button)
            self.taskbar_buttons.append(button)

        taskbar_layout.addStretch(1)
        self.clock_label = QLabel()
        taskbar_layout.addWidget(self.clock_label)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.refresh_clocks)
        self.clock_timer.start(1000)

        self.frost_refresh_timer = QTimer(self)
        self.frost_refresh_timer.setSingleShot(True)
        self.frost_refresh_timer.timeout.connect(self.refresh_all_frosted)

        self.apply_theme("#17202B", "#1A1F25")
        self.install_frosted_widget(self.taskbar, self.taskbar_background, mode="taskbar")
        self.open_app("terminal")
        self.refresh_clocks()
        self.schedule_frosted_refresh()

    def _load_app_modules(self):
        for module_name in ["launcher", "files", "notes", "settings", "about", "calculator", "monitor", "clock", "browser"]:
            module = importlib.import_module(f"data.apps.{module_name}")
            self.app_modules[module.APP_ID] = module

    def launchable_app_ids(self):
        return ["terminal", "browser", "files", "notes", "settings", "about", "calculator", "monitor", "clock", "app1", "app2", "app3"]

    def app_title(self, app_id: str) -> str:
        if app_id == "terminal":
            return "Terminal"
        if app_id.startswith("app"):
            return f"App {app_id[-1]}"
        module = self.app_modules[app_id]
        return module.APP_TITLE

    def pretty_path(self, path: Path) -> str:
        if path == self.context.root:
            return "/"
        return "/" + path.relative_to(self.context.root).as_posix()

    def current_time_string(self) -> str:
        return QDateTime.currentDateTime().toString("HH:mm:ss")

    def get_browser_profile(self):
        if self.browser_profile is None:
            from PySide6.QtWebEngineCore import QWebEngineProfile

            profile = QWebEngineProfile("PeePiOSBrowser", self)
            profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
            profile.setPersistentStoragePath(str(self.browser_storage_dir))
            profile.setCachePath(str(self.browser_cache_dir))
            profile.setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36 PeePiOS/0.2"
            )
            self.browser_profile = profile

        return self.browser_profile

    def refresh_clocks(self):
        now = self.current_time_string()
        self.clock_label.setText(now)
        self.refresh_app("clock")

    def get_browser_history(self):
        if not self.browser_history_path.exists():
            return []

        try:
            return json.loads(self.browser_history_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def add_browser_history(self, title: str, url: str):
        if not url or url.startswith("data:"):
            return

        history = self.get_browser_history()
        entry = {
            "title": title or url,
            "url": url,
            "visited_at": QDateTime.currentDateTime().toString(Qt.ISODate),
        }

        history = [item for item in history if item.get("url") != url]
        history.insert(0, entry)
        history = history[:200]

        try:
            self.browser_history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except OSError:
            return

    def wallpaper_candidates(self):
        return sorted(
            [
                path
                for path in self.wallpaper_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".png", ".gif", ".ppm", ".pgm", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif"}
            ],
            key=lambda item: item.name.lower(),
        )

    def apply_theme(self, desktop_bg: str, taskbar_bg: str):
        viewport_color = "transparent" if self.original_wallpaper is not None else desktop_bg
        self.mdi.setStyleSheet(
            f"""
            QMdiArea {{
                background: {desktop_bg};
                border: none;
            }}
            QMdiArea > QWidget {{
                background: {viewport_color};
                border: none;
            }}
            """
        )
        self.taskbar.setStyleSheet("QFrame { background: transparent; border-top: 1px solid rgba(255,255,255,0.08); }")
        for button in self.taskbar_buttons:
            button.setFlat(True)
            button.setStyleSheet(
                """
                QPushButton {
                    background: transparent;
                    color: white;
                    border: none;
                    padding: 8px 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    color: #bfdbfe;
                }
                """
            )
        self.clock_label.setStyleSheet("background: transparent; color: white; font-weight: 700;")
        self.schedule_frosted_refresh()

    def apply_wallpaper(self, path: Path):
        image = QImage(str(path))
        if image.isNull():
            return
        self.current_wallpaper_path = path
        self.original_wallpaper = image
        self.apply_theme("#17202B", "#1A1F25")
        self._refresh_wallpaper()
        self.schedule_frosted_refresh()

    def clear_wallpaper(self):
        self.current_wallpaper_path = None
        self.original_wallpaper = None
        self.scaled_wallpaper = None
        self.wallpaper_label.clear()
        self.wallpaper_label.hide()
        self.apply_theme("#17202B", "#1A1F25")
        self.schedule_frosted_refresh()

    def _refresh_wallpaper(self):
        if self.original_wallpaper is None:
            return
        viewport_size = self.mdi.viewport().size()
        scaled = self.original_wallpaper.scaled(viewport_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.scaled_wallpaper = QPixmap.fromImage(scaled)
        self.wallpaper_label.setGeometry(0, 0, viewport_size.width(), viewport_size.height())
        self.wallpaper_label.setPixmap(self.scaled_wallpaper)
        self.wallpaper_label.show()
        self.wallpaper_label.lower()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.wallpaper_label.setGeometry(0, 0, self.mdi.viewport().width(), self.mdi.viewport().height())
        self.taskbar_background.setGeometry(self.taskbar.rect())
        if self.original_wallpaper is not None:
            self._refresh_wallpaper()
        self.schedule_frosted_refresh()

    def _attach_blur(self, label: QLabel, radius: float):
        blur = QGraphicsBlurEffect(label)
        blur.setBlurRadius(radius)
        label.setGraphicsEffect(blur)

    def install_frosted_widget(self, widget: QWidget, background_label: QLabel | None = None, mode: str = "widget"):
        if background_label is None:
            background_label = QLabel(widget)
            background_label.setScaledContents(True)
            background_label.setGeometry(widget.rect())
            background_label.lower()
            blur_radius = 22 if mode == "terminal" else 18
            self._attach_blur(background_label, blur_radius)
        widget.installEventFilter(self)
        target = {"widget": widget, "background": background_label, "mode": mode}
        self.frosted_targets.append(target)
        widget.destroyed.connect(lambda _obj=None, value=target: self._remove_frosted_target(value))
        background_label.destroyed.connect(lambda _obj=None, value=target: self._remove_frosted_target(value))

    def apply_frosted_style(self, widget: QWidget, mode: str = "widget"):
        widget.setObjectName("FrostRoot")
        widget.setAutoFillBackground(False)
        self.install_frosted_widget(widget, mode=mode)
        if mode == "terminal":
            widget.setStyleSheet(
                """
                QWidget#FrostRoot {
                    background: transparent;
                    color: #d7e0ea;
                    border: none;
                }
                QLabel {
                    background: transparent;
                    color: #8be9fd;
                }
                QTextEdit, QLineEdit {
                    background: rgba(10, 14, 20, 176);
                    color: #d7e0ea;
                    border: 1px solid rgba(139, 233, 253, 0.14);
                    border-radius: 10px;
                    padding: 10px;
                }
                """
            )
            return

        widget.setStyleSheet(
            """
            QWidget#FrostRoot {
                background: transparent;
                color: #172033;
                border: none;
            }
            QLabel {
                background: transparent;
                color: #172033;
            }
            QLabel#appTitle {
                font-size: 26px;
                font-weight: 700;
            }
            QLabel#bigNumber {
                font-size: 60px;
                font-weight: 700;
            }
            QLabel#clockLabel {
                font-size: 28px;
                font-weight: 700;
            }
            QPushButton {
                background: rgba(255, 255, 255, 76);
                padding: 8px 12px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 118);
            }
            QLineEdit, QTextEdit, QListWidget {
                background: rgba(255, 255, 255, 92);
                border-radius: 10px;
                padding: 8px;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            """
        )

    def _make_subwindow(self, app_id: str, title: str, widget: QWidget, size: tuple[int, int]):
        subwindow = QMdiSubWindow()
        subwindow.setAttribute(Qt.WA_DeleteOnClose)
        subwindow.setWidget(widget)
        subwindow.setWindowTitle(title)
        subwindow.resize(*size)
        subwindow.installEventFilter(self)
        self.mdi.addSubWindow(subwindow)
        subwindow.destroyed.connect(lambda _obj=None, value=app_id: self.windows.pop(value, None))
        self.windows[app_id] = subwindow
        return subwindow

    def open_app(self, app_id: str, payload=None):
        existing = self.windows.get(app_id)
        if existing is not None:
            existing.show()
            existing.raise_()
            existing.setFocus()
            if payload is not None and hasattr(existing.widget(), "load_target"):
                existing.widget().load_target(payload)
            if hasattr(existing.widget(), "refresh_view"):
                existing.widget().refresh_view()
            return existing

        if app_id == "terminal":
            widget = self._build_terminal()
            subwindow = self._make_subwindow(app_id, "Terminal", widget, (900, 520))
        elif app_id.startswith("app"):
            from data.apps.placeholder import DEFAULT_SIZE, build_placeholder

            number = int(app_id[-1])
            widget = build_placeholder(self, number)
            subwindow = self._make_subwindow(app_id, f"App {number}", widget, DEFAULT_SIZE)
        else:
            module = self.app_modules[app_id]
            widget = module.build_widget(self)
            subwindow = self._make_subwindow(app_id, module.APP_TITLE, widget, module.DEFAULT_SIZE)
            if payload is not None and hasattr(widget, "load_target"):
                widget.load_target(payload)

        subwindow.show()
        subwindow.raise_()
        self.schedule_frosted_refresh()
        return subwindow

    def refresh_app(self, app_id: str):
        window = self.windows.get(app_id)
        if window is not None and hasattr(window.widget(), "refresh_view"):
            window.widget().refresh_view()

    def _remove_frosted_target(self, target):
        self.frosted_targets = [item for item in self.frosted_targets if item is not target]

    def _widget_is_usable(self, widget):
        return widget is not None and isValid(widget)

    def schedule_frosted_refresh(self, delay_ms: int = 16):
        if self.frost_refresh_timer.isActive():
            return
        self.frost_refresh_timer.start(delay_ms)

    def eventFilter(self, watched, event):
        if event.type() in {QEvent.Move, QEvent.Resize, QEvent.Show}:
            self.schedule_frosted_refresh(16)
        return super().eventFilter(watched, event)

    def refresh_all_frosted(self):
        if self.scaled_wallpaper is None:
            for target in self.frosted_targets:
                widget = target["widget"]
                background = target["background"]
                if widget is None or background is None:
                    continue
                if isinstance(widget, QWidget) and widget.isVisible():
                    background.setGeometry(widget.rect())
                    background.setPixmap(QPixmap())
                    fallback = "rgba(26, 31, 37, 170)" if target["mode"] == "taskbar" else "rgba(235, 241, 248, 120)"
                    background.setStyleSheet(f"background: {fallback}; border: none;")
                    background.show()
            return

        for window in self.windows.values():
            widget = window.widget()
            if widget is not None:
                widget.update()

        viewport = self.mdi.viewport()
        viewport_origin = viewport.mapToGlobal(QPoint(0, 0))

        active_targets = []
        for target in self.frosted_targets:
            widget = target["widget"]
            background = target["background"]
            if not self._widget_is_usable(widget) or not self._widget_is_usable(background):
                continue
            if not isinstance(widget, QWidget) or not isinstance(background, QLabel):
                continue
            if not widget.isVisible():
                active_targets.append(target)
                continue

            background.setGeometry(widget.rect())
            if target["mode"] == "taskbar":
                strip_height = max(1, self.taskbar.height())
                y = max(0, self.scaled_wallpaper.height() - strip_height)
                patch = self.scaled_wallpaper.copy(0, y, self.scaled_wallpaper.width(), strip_height)
            else:
                top_left = widget.mapToGlobal(QPoint(0, 0))
                relative = top_left - viewport_origin
                x = max(0, relative.x())
                y = max(0, relative.y())
                width = min(max(1, widget.width()), max(1, self.scaled_wallpaper.width() - x))
                height = min(max(1, widget.height()), max(1, self.scaled_wallpaper.height() - y))
                patch = self.scaled_wallpaper.copy(x, y, width, height)
                if patch.size() != widget.size():
                    patch = patch.scaled(widget.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            background.setStyleSheet("background: rgba(255,255,255,0.02); border: none;")
            background.setPixmap(patch)
            background.lower()
            background.show()
            active_targets.append(target)

        self.frosted_targets = active_targets

    def _build_terminal(self):
        from PySide6.QtGui import QTextCursor

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        output = QTextEdit()
        output.setReadOnly(True)
        output.setPlainText(startup_message(self.context, self.commands))
        layout.addWidget(output, 1)

        input_row = QWidget()
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)
        prompt = QLabel(self.context.prompt())
        entry = QLineEdit()
        input_layout.addWidget(prompt)
        input_layout.addWidget(entry, 1)
        layout.addWidget(input_row)

        self.apply_frosted_style(root, mode="terminal")
        root.setStyleSheet(
            root.styleSheet()
            + """
            QLabel {
                color: #8be9fd;
                font-family: Consolas;
            }
            QTextEdit, QLineEdit {
                font-family: Consolas;
            }
            """
        )

        def run_command():
            raw = entry.text()
            if not raw.strip():
                return
            output.moveCursor(QTextCursor.End)
            output.insertPlainText(f"{self.context.prompt()}{raw}\n")
            entry.clear()
            result = execute_line(self.context, self.commands, raw)
            if result:
                output.moveCursor(QTextCursor.End)
                output.insertPlainText(result)
                if not result.endswith("\n"):
                    output.insertPlainText("\n")
            output.moveCursor(QTextCursor.End)
            prompt.setText(self.context.prompt())
            self.refresh_app("files")
            self.refresh_app("about")
            self.refresh_app("monitor")
            if not self.context.running:
                self.close()

        entry.returnPressed.connect(run_command)
        return root


def run_desktop():
    app = QApplication.instance() or QApplication([])
    window = PeePiOSDesktop()
    window.show()
    app.exec()
