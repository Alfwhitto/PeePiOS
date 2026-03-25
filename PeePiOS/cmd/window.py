from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from main import create_shell, execute_line, startup_message

try:
    from PIL import Image, ImageTk
except ImportError:  # Fallback to Tkinter-only image support.
    Image = None
    ImageTk = None


COMMAND = "window"
DESCRIPTION = "Open a Tkinter desktop with draggable internal windows and built-in PeePiOS apps."


class InternalWindow:
    def __init__(
        self,
        app,
        title: str,
        x: int,
        y: int,
        width: int,
        height: int,
        close_callback=None,
    ):
        self.app = app
        self.title = title
        self.close_callback = close_callback
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.hidden = False
        self.closed = False

        self.frame = tk.Frame(
            app.desktop,
            bg="#111417",
            highlightbackground="#5A6572",
            highlightthickness=1,
        )
        self.frame.place(x=x, y=y, width=width, height=height)

        self.title_bar = tk.Frame(self.frame, bg="#20262D", height=34, cursor="fleur")
        self.title_bar.pack(fill="x", side="top")

        self.title_label = tk.Label(
            self.title_bar,
            text=title,
            bg="#20262D",
            fg="#F8FAFC",
            font=("Segoe UI", 10, "bold"),
            padx=12,
        )
        self.title_label.pack(side="left", pady=7)

        self.close_button = tk.Button(
            self.title_bar,
            text="x",
            command=self.close,
            bg="#C05656",
            fg="#FFFFFF",
            activebackground="#9B2C2C",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            width=3,
            font=("Segoe UI", 9, "bold"),
        )
        self.close_button.pack(side="right", padx=8, pady=5)

        self.content = tk.Frame(self.frame, bg="#111417")
        self.content.pack(fill="both", expand=True)

        for widget in (self.frame, self.title_bar, self.title_label):
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.on_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)

        self.frame.bind("<Button-1>", self.focus)
        self.content.bind("<Button-1>", self.focus)

    def start_drag(self, event):
        self.focus()
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root

    def on_drag(self, event):
        current_x = self.frame.winfo_x()
        current_y = self.frame.winfo_y()
        delta_x = event.x_root - self.drag_start_x
        delta_y = event.y_root - self.drag_start_y

        desktop_width = max(self.app.desktop.winfo_width(), 1)
        desktop_height = max(self.app.desktop.winfo_height(), 1)
        width = self.frame.winfo_width()
        height = self.frame.winfo_height()

        new_x = max(0, min(current_x + delta_x, desktop_width - width))
        new_y = max(0, min(current_y + delta_y, desktop_height - height))

        self.frame.place(x=new_x, y=new_y)
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root

    def stop_drag(self, _event):
        self.focus()

    def focus(self, _event=None):
        if not self.closed:
            self.app.focus_window(self)

    def set_active(self, active: bool):
        title_color = "#2D3742" if active else "#20262D"
        border_color = "#7DD3FC" if active else "#5A6572"
        self.title_bar.configure(bg=title_color)
        self.title_label.configure(bg=title_color)
        self.frame.configure(highlightbackground=border_color)

    def set_title(self, title: str):
        self.title = title
        self.title_label.configure(text=title)

    def show(self):
        if self.closed:
            return
        self.hidden = False
        self.frame.place_configure()
        self.frame.lift()
        self.focus()

    def hide(self):
        if self.closed:
            return
        self.hidden = True
        self.frame.place_forget()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.frame.destroy()
        if self.close_callback is not None:
            self.close_callback()


class PeePiOSWindow:
    def __init__(self):
        self.context, self.commands = create_shell()
        self.root = tk.Tk()
        self.root.title("PeePiOS")
        self.root.geometry("1180x760")
        self.root.minsize(900, 600)

        self.theme = {
            "root_bg": "#121519",
            "desktop_bg": "#17202B",
            "glow_bg": "#203349",
            "taskbar_bg": "#1A1F25",
            "taskbar_button": "#2C3642",
            "taskbar_button_active": "#3C4957",
            "taskbar_fg": "#F8FAFC",
            "window_bg": "#111417",
            "window_title": "#20262D",
            "window_title_active": "#2D3742",
            "window_border": "#5A6572",
            "window_border_active": "#7DD3FC",
            "terminal_bg": "#0F1317",
            "terminal_input_bg": "#151B22",
            "terminal_fg": "#D7E0EA",
            "prompt_fg": "#8BE9FD",
        }

        self.root.configure(bg=self.theme["root_bg"])
        self.clock_after_id = None
        self.closing = False
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self.active_window = None
        self.windows = {}
        self.number_windows = {}
        self.note_target_path = None
        self.file_browser_path = self.context.root
        self.wallpaper_dir = self.context.root / "settings" / "wallpaper"
        self.wallpaper_dir.mkdir(parents=True, exist_ok=True)
        self.wallpaper_image = None
        self.current_wallpaper_path = None
        self.original_wallpaper = None
        self.calculator_expression = tk.StringVar(value="")
        self.clock_taskbar_var = tk.StringVar(value="")
        self.clock_window_var = tk.StringVar(value="")

        style = ttk.Style(self.root)
        style.theme_use("clam")
        self.configure_taskbar_style()

        self.desktop = tk.Frame(self.root, bg=self.theme["desktop_bg"])
        self.desktop.pack(fill="both", expand=True)

        self.wallpaper_label = tk.Label(self.desktop, bg=self.theme["desktop_bg"], bd=0)
        self.wallpaper_label.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0)
        self.wallpaper_label.lower()
        self.desktop.bind("<Configure>", self.on_desktop_resize)

        self.taskbar = ttk.Frame(self.root, style="Taskbar.TFrame", padding=(10, 8))
        self.taskbar.pack(fill="x", side="bottom")

        self.build_taskbar()
        self.create_terminal_window()
        self.update_clock()
        self.root.after(120, self.focus_terminal)

    def build_taskbar(self):
        ttk.Button(self.taskbar, text="Exit", style="Taskbar.TButton", command=self.shutdown).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="Terminal", style="Taskbar.TButton", command=self.show_terminal).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="Launcher", style="Taskbar.TButton", command=self.open_launcher).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="Files", style="Taskbar.TButton", command=self.open_files).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="Notes", style="Taskbar.TButton", command=self.open_notes).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="Settings", style="Taskbar.TButton", command=self.open_settings).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="About", style="Taskbar.TButton", command=self.open_about).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="Calc", style="Taskbar.TButton", command=self.open_calculator).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="Monitor", style="Taskbar.TButton", command=self.open_process_monitor).pack(side="left", padx=5)
        ttk.Button(self.taskbar, text="Clock", style="Taskbar.TButton", command=self.open_clock).pack(side="left", padx=5)

        self.clock_label = tk.Label(
            self.taskbar,
            textvariable=self.clock_taskbar_var,
            bg=self.theme["taskbar_bg"],
            fg="#E2E8F0",
            font=("Segoe UI", 10, "bold"),
            padx=12,
        )
        self.clock_label.pack(side="right")

    def configure_taskbar_style(self):
        style = ttk.Style(self.root)
        style.configure("Taskbar.TFrame", background=self.theme["taskbar_bg"])
        style.configure(
            "Taskbar.TButton",
            background=self.theme["taskbar_button"],
            foreground=self.theme["taskbar_fg"],
            borderwidth=0,
            padding=(14, 9),
        )
        style.map(
            "Taskbar.TButton",
            background=[("active", self.theme["taskbar_button_active"])],
            foreground=[("active", self.theme["taskbar_fg"])],
        )

    def create_internal_window(self, key: str, title: str, x: int, y: int, width: int, height: int):
        existing = self.windows.get(key)
        if existing is not None and not existing.closed:
            existing.show()
            return existing

        window = InternalWindow(
            self,
            title=title,
            x=x,
            y=y,
            width=width,
            height=height,
            close_callback=lambda window_key=key: self.on_window_closed(window_key),
        )
        self.windows[key] = window
        return window

    def on_window_closed(self, key: str):
        if self.active_window is self.windows.get(key):
            self.active_window = None
        self.windows.pop(key, None)
        if key.startswith("app-"):
            try:
                self.number_windows.pop(int(key.split("-")[1]), None)
            except ValueError:
                pass

    def focus_window(self, window: InternalWindow):
        if self.active_window is not None and self.active_window is not window and not self.active_window.closed:
            self.active_window.set_active(False)

        self.active_window = window
        self.active_window.set_active(True)
        self.active_window.frame.lift()

    def append_output(self, text: str) -> None:
        if not text:
            return
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def refresh_prompt(self) -> None:
        self.prompt_label.config(text=self.context.prompt())

    def create_terminal_window(self):
        self.terminal_window = self.create_internal_window("terminal", "Terminal", 110, 70, 900, 520)
        self.terminal_window.close_callback = self.hide_terminal
        self.terminal_window.content.configure(bg=self.theme["window_bg"])

        self.output = tk.Text(
            self.terminal_window.content,
            bg=self.theme["terminal_bg"],
            fg=self.theme["terminal_fg"],
            insertbackground=self.theme["terminal_fg"],
            relief="flat",
            wrap="word",
            font=("Consolas", 11),
            padx=16,
            pady=16,
        )

        self.input_frame = tk.Frame(self.terminal_window.content, bg=self.theme["terminal_input_bg"])
        self.input_frame.pack(side="bottom", fill="x")

        self.prompt_label = tk.Label(
            self.input_frame,
            text=self.context.prompt(),
            bg=self.theme["terminal_input_bg"],
            fg=self.theme["prompt_fg"],
            font=("Consolas", 11),
            padx=16,
            pady=12,
        )
        self.prompt_label.pack(side="left")

        self.entry = tk.Entry(
            self.input_frame,
            bg=self.theme["terminal_input_bg"],
            fg="#F8FAFC",
            insertbackground="#F8FAFC",
            relief="flat",
            font=("Consolas", 11),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 16), pady=10)
        self.entry.bind("<Return>", self.run_command)
        self.entry.bind("<Button-1>", self.focus_terminal)

        self.output.pack(side="top", fill="both", expand=True)
        self.output.insert("end", startup_message(self.context, self.commands))
        self.output.configure(state="disabled")

        self.output.bind("<Button-1>", self.focus_terminal)
        self.input_frame.bind("<Button-1>", self.focus_terminal)
        self.prompt_label.bind("<Button-1>", self.focus_terminal)
        self.terminal_window.content.bind("<Button-1>", self.focus_terminal)
        self.focus_window(self.terminal_window)

    def run_command(self, _event=None):
        raw = self.entry.get()
        prompt_line = f"{self.context.prompt()}{raw}\n"
        self.append_output(prompt_line)
        self.entry.delete(0, "end")

        result = execute_line(self.context, self.commands, raw)
        if result:
            self.append_output(result)

        self.refresh_prompt()

        if not self.context.running:
            self.shutdown()
            return

        self.refresh_open_files_view()
        self.focus_terminal()

    def focus_terminal(self, _event=None):
        if self.terminal_window.closed:
            self.create_terminal_window()

        self.terminal_window.show()
        self.focus_window(self.terminal_window)
        self.entry.focus_force()

    def hide_terminal(self):
        if not self.terminal_window.closed:
            self.terminal_window.hide()
        self.active_window = None

    def show_terminal(self):
        if self.terminal_window.closed:
            self.create_terminal_window()
        self.terminal_window.show()
        self.root.after(10, self.focus_terminal)

    def make_panel(self, parent, bg="#F4F7FB"):
        panel = tk.Frame(parent, bg=bg)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        return panel

    def open_number_window(self, number: int):
        key = f"app-{number}"
        existing = self.windows.get(key)
        if existing is not None and not existing.closed:
            existing.show()
            self.number_windows[number] = existing
            return

        window = self.create_internal_window(key, f"App {number}", 190 + (number * 28), 120 + (number * 28), 320, 230)
        card = self.make_panel(window.content)

        label = tk.Label(card, text=str(number), font=("Segoe UI", 58, "bold"), bg="#F4F7FB", fg="#213547")
        label.pack(expand=True)
        subtitle = tk.Label(card, text=f"Placeholder app window {number}", font=("Segoe UI", 12), bg="#F4F7FB", fg="#52606D")
        subtitle.pack(pady=(0, 18))

        label.bind("<Button-1>", window.focus)
        subtitle.bind("<Button-1>", window.focus)
        self.number_windows[number] = window
        window.show()

    def open_launcher(self):
        window = self.create_internal_window("launcher", "Launcher", 70, 90, 310, 420)
        if getattr(window, "built", False):
            window.show()
            return

        panel = self.make_panel(window.content)
        tk.Label(panel, text="Launch Apps", font=("Segoe UI", 20, "bold"), bg="#F4F7FB", fg="#22303C").pack(anchor="w", pady=(0, 14))

        apps = [
            ("Files", self.open_files),
            ("Notes", self.open_notes),
            ("Settings", self.open_settings),
            ("About", self.open_about),
            ("Calculator", self.open_calculator),
            ("Process Monitor", self.open_process_monitor),
            ("Clock", self.open_clock),
            ("App 1", lambda: self.open_number_window(1)),
            ("App 2", lambda: self.open_number_window(2)),
            ("App 3", lambda: self.open_number_window(3)),
        ]

        for label, callback in apps:
            tk.Button(
                panel,
                text=label,
                command=callback,
                relief="flat",
                bg="#DCE6F2",
                fg="#1F2937",
                activebackground="#C8D6E5",
                font=("Segoe UI", 11, "bold"),
                pady=8,
            ).pack(fill="x", pady=5)

        window.built = True
        window.show()

    def open_files(self):
        window = self.create_internal_window("files", "Files", 180, 100, 560, 420)
        if getattr(window, "built", False):
            self.refresh_files_view()
            window.show()
            return

        outer = self.make_panel(window.content)
        header = tk.Frame(outer, bg="#F4F7FB")
        header.pack(fill="x")

        self.files_path_var = tk.StringVar()
        tk.Label(header, textvariable=self.files_path_var, font=("Consolas", 11), bg="#F4F7FB", fg="#334155").pack(side="left", fill="x", expand=True)
        tk.Button(header, text="Up", command=self.files_up, relief="flat", bg="#DCE6F2", activebackground="#C8D6E5").pack(side="right")

        body = tk.Frame(outer, bg="#F4F7FB")
        body.pack(fill="both", expand=True, pady=(14, 0))

        self.files_list = tk.Listbox(body, font=("Consolas", 11), bg="#FFFFFF", fg="#1F2937", relief="flat", activestyle="none")
        self.files_list.pack(fill="both", expand=True, side="left")
        self.files_list.bind("<Double-Button-1>", self.files_open_selected)

        scrollbar = tk.Scrollbar(body, command=self.files_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.files_list.configure(yscrollcommand=scrollbar.set)

        actions = tk.Frame(outer, bg="#F4F7FB")
        actions.pack(fill="x", pady=(12, 0))
        tk.Button(actions, text="Open", command=self.files_open_selected, relief="flat", bg="#DCE6F2", activebackground="#C8D6E5").pack(side="left", padx=(0, 8))
        tk.Button(actions, text="Refresh", command=self.refresh_files_view, relief="flat", bg="#DCE6F2", activebackground="#C8D6E5").pack(side="left")

        window.built = True
        self.refresh_files_view()
        window.show()

    def refresh_open_files_view(self):
        files_window = self.windows.get("files")
        if files_window is not None and not files_window.closed and getattr(files_window, "built", False):
            self.refresh_files_view()

        about_window = self.windows.get("about")
        if about_window is not None and not about_window.closed and getattr(about_window, "refresh", None):
            about_window.refresh()

        monitor_window = self.windows.get("monitor")
        if monitor_window is not None and not monitor_window.closed and getattr(monitor_window, "refresh", None):
            monitor_window.refresh()

    def refresh_files_view(self):
        if not hasattr(self, "files_list"):
            return

        self.files_path_var.set(self.pretty_path(self.file_browser_path))
        self.files_list.delete(0, "end")

        if self.file_browser_path != self.context.root:
            self.files_list.insert("end", "[DIR] ..")

        entries = sorted(self.file_browser_path.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
        for entry in entries:
            prefix = "[DIR]" if entry.is_dir() else "[FILE]"
            self.files_list.insert("end", f"{prefix} {entry.name}")

    def files_up(self):
        if self.file_browser_path != self.context.root:
            self.file_browser_path = self.file_browser_path.parent
            self.refresh_files_view()

    def files_open_selected(self, _event=None):
        selection = self.files_list.curselection()
        if not selection:
            return

        value = self.files_list.get(selection[0])
        if value == "[DIR] ..":
            self.files_up()
            return

        entry_name = value.split(" ", 1)[1]
        target = self.file_browser_path / entry_name

        if target.is_dir():
            self.file_browser_path = target
            self.refresh_files_view()
            return

        self.open_notes(target)

    def open_notes(self, target=None):
        if target is not None:
            self.note_target_path = target

        window = self.create_internal_window("notes", "Notes", 260, 130, 600, 450)
        if getattr(window, "built", False):
            if target is not None:
                self.load_note_target()
            window.show()
            return

        outer = self.make_panel(window.content)

        top = tk.Frame(outer, bg="#F4F7FB")
        top.pack(fill="x")

        tk.Label(top, text="File:", bg="#F4F7FB", fg="#334155", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.notes_path_var = tk.StringVar(value="/notes.txt")
        self.notes_path_entry = tk.Entry(top, textvariable=self.notes_path_var, relief="flat", font=("Consolas", 11))
        self.notes_path_entry.pack(side="left", fill="x", expand=True, padx=10)

        tk.Button(top, text="Load", command=self.load_note_from_entry, relief="flat", bg="#DCE6F2", activebackground="#C8D6E5").pack(side="left", padx=(0, 8))
        tk.Button(top, text="Save", command=self.save_note, relief="flat", bg="#DCE6F2", activebackground="#C8D6E5").pack(side="left")

        self.notes_status_var = tk.StringVar(value="Ready")
        tk.Label(outer, textvariable=self.notes_status_var, bg="#F4F7FB", fg="#64748B", font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 8))

        self.notes_text = tk.Text(outer, wrap="word", relief="flat", bg="#FFFFFF", fg="#1F2937", insertbackground="#1F2937", font=("Consolas", 11), padx=12, pady=12)
        self.notes_text.pack(fill="both", expand=True)

        window.built = True
        self.load_note_target()
        window.show()

    def load_note_target(self):
        if self.note_target_path is None:
            self.note_target_path = self.context.root / "notes.txt"

        self.notes_path_var.set(self.pretty_path(self.note_target_path))
        if self.note_target_path.exists() and self.note_target_path.is_file():
            content = self.note_target_path.read_text(encoding="utf-8")
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", content)
            self.notes_status_var.set(f"Loaded {self.pretty_path(self.note_target_path)}")
        else:
            self.notes_text.delete("1.0", "end")
            self.notes_status_var.set(f"New file {self.pretty_path(self.note_target_path)}")

        notes_window = self.windows.get("notes")
        if notes_window is not None and not notes_window.closed:
            notes_window.set_title(f"Notes - {self.note_target_path.name}")

    def load_note_from_entry(self):
        try:
            self.note_target_path = self.context.resolve_path(self.notes_path_var.get())
            self.load_note_target()
        except Exception as error:
            self.notes_status_var.set(str(error))

    def save_note(self):
        try:
            self.note_target_path = self.context.resolve_path(self.notes_path_var.get())
            self.note_target_path.parent.mkdir(parents=True, exist_ok=True)
            self.note_target_path.write_text(self.notes_text.get("1.0", "end-1c"), encoding="utf-8")
            self.notes_status_var.set(f"Saved {self.pretty_path(self.note_target_path)}")
            self.refresh_open_files_view()
        except Exception as error:
            self.notes_status_var.set(str(error))

    def open_settings(self):
        window = self.create_internal_window("settings", "Settings", 390, 90, 430, 520)
        if getattr(window, "built", False):
            self.refresh_wallpaper_buttons()
            window.show()
            return

        outer = tk.Frame(window.content, bg="#F4F7FB")
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        canvas = tk.Canvas(outer, bg="#F4F7FB", highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        panel = tk.Frame(canvas, bg="#F4F7FB")

        panel.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=panel, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(panel, text="Theme Colors", font=("Segoe UI", 18, "bold"), bg="#F4F7FB", fg="#22303C").pack(anchor="w", pady=(0, 14))
        tk.Label(panel, text="Pick a desktop mood:", font=("Segoe UI", 10), bg="#F4F7FB", fg="#52606D").pack(anchor="w", pady=(0, 10))

        themes = [
            ("Ocean", "#17202B", "#203349", "#1A1F25"),
            ("Forest", "#1A241D", "#294235", "#162119"),
            ("Sunset", "#2A1E1A", "#5B3A29", "#241815"),
            ("Slate", "#1C2026", "#364152", "#171B21"),
        ]

        for name, desktop_bg, glow_bg, taskbar_bg in themes:
            tk.Button(
                panel,
                text=name,
                command=lambda d=desktop_bg, g=glow_bg, t=taskbar_bg: self.apply_theme(d, g, t),
                relief="flat",
                bg="#DCE6F2",
                activebackground="#C8D6E5",
                font=("Segoe UI", 11, "bold"),
                pady=6,
            ).pack(fill="x", pady=5)

        tk.Label(panel, text="Wallpapers", font=("Segoe UI", 16, "bold"), bg="#F4F7FB", fg="#22303C").pack(anchor="w", pady=(18, 8))
        tk.Label(
            panel,
            text="Drop PNG/GIF/PPM files into /settings/wallpaper and reopen Settings.",
            font=("Segoe UI", 9),
            bg="#F4F7FB",
            fg="#52606D",
        ).pack(anchor="w", pady=(0, 8))

        self.wallpaper_status_var = tk.StringVar(value="No wallpaper selected.")
        tk.Label(panel, textvariable=self.wallpaper_status_var, font=("Segoe UI", 9), bg="#F4F7FB", fg="#64748B").pack(anchor="w", pady=(0, 8))

        self.wallpaper_buttons_frame = tk.Frame(panel, bg="#F4F7FB")
        self.wallpaper_buttons_frame.pack(fill="x")

        tk.Button(
            panel,
            text="Refresh Wallpapers",
            command=self.refresh_wallpaper_buttons,
            relief="flat",
            bg="#DCE6F2",
            activebackground="#C8D6E5",
            font=("Segoe UI", 10, "bold"),
            pady=6,
        ).pack(fill="x", pady=(10, 0))

        window.built = True
        self.refresh_wallpaper_buttons()
        window.show()

    def apply_theme(self, desktop_bg: str, glow_bg: str, taskbar_bg: str):
        self.theme["desktop_bg"] = desktop_bg
        self.theme["glow_bg"] = glow_bg
        self.theme["taskbar_bg"] = taskbar_bg
        self.theme["taskbar_button"] = self.adjust_color(taskbar_bg, 18)
        self.theme["taskbar_button_active"] = self.adjust_color(taskbar_bg, 34)
        self.theme["taskbar_fg"] = self.contrast_text_color(taskbar_bg)
        self.desktop.configure(bg=desktop_bg)
        self.wallpaper_label.configure(bg=desktop_bg)
        self.taskbar.configure(style="Taskbar.TFrame")
        self.configure_taskbar_style()
        self.clock_label.configure(bg=taskbar_bg)
        self.clock_label.configure(fg=self.theme["taskbar_fg"])

    def get_wallpaper_candidates(self):
        if Image is not None and ImageTk is not None:
            supported_suffixes = {".png", ".gif", ".ppm", ".pgm", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif"}
        else:
            supported_suffixes = {".png", ".gif", ".ppm", ".pgm"}
        return sorted(
            [path for path in self.wallpaper_dir.iterdir() if path.is_file() and path.suffix.lower() in supported_suffixes],
            key=lambda item: item.name.lower(),
        )

    def refresh_wallpaper_buttons(self):
        if not hasattr(self, "wallpaper_buttons_frame"):
            return

        for child in self.wallpaper_buttons_frame.winfo_children():
            child.destroy()

        tk.Button(
            self.wallpaper_buttons_frame,
            text="Use Theme Background",
            command=self.clear_wallpaper,
            relief="flat",
            bg="#DCE6F2",
            activebackground="#C8D6E5",
            font=("Segoe UI", 10, "bold"),
            pady=6,
        ).pack(fill="x", pady=3)

        wallpapers = self.get_wallpaper_candidates()
        if not wallpapers:
            self.wallpaper_status_var.set("No supported wallpapers found in /settings/wallpaper.")
            return

        current_name = self.current_wallpaper_path.name if self.current_wallpaper_path else "theme background"
        self.wallpaper_status_var.set(f"Current wallpaper: {current_name}")

        for path in wallpapers:
            tk.Button(
                self.wallpaper_buttons_frame,
                text=path.name,
                command=lambda wallpaper_path=path: self.apply_wallpaper(wallpaper_path),
                relief="flat",
                bg="#DCE6F2",
                activebackground="#C8D6E5",
                font=("Segoe UI", 10),
                pady=6,
            ).pack(fill="x", pady=3)

    def apply_wallpaper(self, path: Path):
        try:
            if Image is not None and ImageTk is not None:
                with Image.open(path) as loaded:
                    self.original_wallpaper = loaded.copy()
                image = self.build_wallpaper_image()
            else:
                self.original_wallpaper = None
                image = tk.PhotoImage(file=str(path))
        except (tk.TclError, OSError) as error:
            if hasattr(self, "wallpaper_status_var"):
                self.wallpaper_status_var.set(f"Could not load {path.name}: {error}")
            return

        self.wallpaper_image = image
        self.current_wallpaper_path = path
        self.wallpaper_label.configure(image=self.wallpaper_image, text="")
        self.wallpaper_label.lower()
        self.apply_taskbar_color_from_wallpaper()

        if hasattr(self, "wallpaper_status_var"):
            self.wallpaper_status_var.set(f"Current wallpaper: {path.name}")

    def clear_wallpaper(self):
        self.wallpaper_image = None
        self.current_wallpaper_path = None
        self.original_wallpaper = None
        self.wallpaper_label.configure(image="", text="", bg=self.theme["desktop_bg"])
        self.apply_theme(self.theme["desktop_bg"], self.theme["glow_bg"], "#1A1F25")
        if hasattr(self, "wallpaper_status_var"):
            self.wallpaper_status_var.set("Current wallpaper: theme background")

    def build_wallpaper_image(self):
        if self.original_wallpaper is None or Image is None or ImageTk is None:
            return None

        desktop_width = max(self.desktop.winfo_width(), 1)
        desktop_height = max(self.desktop.winfo_height(), 1)

        resized = self.original_wallpaper.copy()
        resized = resized.resize((desktop_width, desktop_height), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(resized)

    def on_desktop_resize(self, _event=None):
        if self.current_wallpaper_path is None:
            return

        if self.original_wallpaper is None or Image is None or ImageTk is None:
            return

        image = self.build_wallpaper_image()
        if image is None:
            return

        self.wallpaper_image = image
        self.wallpaper_label.configure(image=self.wallpaper_image)

    def apply_taskbar_color_from_wallpaper(self):
        if self.original_wallpaper is None or Image is None:
            return

        sample = self.original_wallpaper.copy().convert("RGB").resize((1, 1), Image.Resampling.BILINEAR)
        red, green, blue = sample.getpixel((0, 0))
        taskbar_bg = f"#{red:02X}{green:02X}{blue:02X}"
        self.theme["taskbar_bg"] = taskbar_bg
        self.theme["taskbar_button"] = self.adjust_color(taskbar_bg, 18)
        self.theme["taskbar_button_active"] = self.adjust_color(taskbar_bg, 34)
        self.theme["taskbar_fg"] = self.contrast_text_color(taskbar_bg)
        self.configure_taskbar_style()
        self.clock_label.configure(bg=taskbar_bg, fg=self.theme["taskbar_fg"])

    def adjust_color(self, hex_color: str, delta: int) -> str:
        red = int(hex_color[1:3], 16)
        green = int(hex_color[3:5], 16)
        blue = int(hex_color[5:7], 16)

        def clamp(value):
            return max(0, min(255, value))

        adjusted = (
            clamp(red + delta),
            clamp(green + delta),
            clamp(blue + delta),
        )
        return f"#{adjusted[0]:02X}{adjusted[1]:02X}{adjusted[2]:02X}"

    def contrast_text_color(self, hex_color: str) -> str:
        red = int(hex_color[1:3], 16)
        green = int(hex_color[3:5], 16)
        blue = int(hex_color[5:7], 16)
        luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
        return "#111827" if luminance > 150 else "#F8FAFC"

    def open_about(self):
        window = self.create_internal_window("about", "About PeePiOS", 780, 110, 320, 280)
        if getattr(window, "built", False):
            window.refresh()
            window.show()
            return

        panel = self.make_panel(window.content)
        tk.Label(panel, text="PeePiOS", font=("Segoe UI", 24, "bold"), bg="#F4F7FB", fg="#22303C").pack(anchor="w")
        tk.Label(panel, text="A tiny Python desktop shell.", font=("Segoe UI", 11), bg="#F4F7FB", fg="#52606D").pack(anchor="w", pady=(0, 16))

        window.info_var = tk.StringVar()
        tk.Label(panel, textvariable=window.info_var, justify="left", anchor="w", bg="#F4F7FB", fg="#334155", font=("Consolas", 10)).pack(fill="both", expand=True, anchor="w")

        def refresh_about():
            info = [
                "Version: 0.1 desktop prototype",
                f"Root: {self.pretty_path(self.context.root)}",
                f"Current shell path: {self.context.prompt_path()}",
                f"Commands loaded: {len(self.commands)}",
                f"Open windows: {len(self.get_open_windows())}",
            ]
            window.info_var.set("\n".join(info))

        window.refresh = refresh_about
        window.built = True
        window.refresh()
        window.show()

    def open_calculator(self):
        window = self.create_internal_window("calculator", "Calculator", 600, 180, 340, 420)
        if getattr(window, "built", False):
            window.show()
            return

        panel = self.make_panel(window.content)
        display = tk.Entry(panel, textvariable=self.calculator_expression, justify="right", relief="flat", font=("Consolas", 18), bg="#FFFFFF", fg="#111827")
        display.pack(fill="x", pady=(0, 16), ipady=10)

        grid = tk.Frame(panel, bg="#F4F7FB")
        grid.pack(fill="both", expand=True)

        buttons = [
            "7", "8", "9", "/",
            "4", "5", "6", "*",
            "1", "2", "3", "-",
            "0", ".", "=", "+",
        ]

        for index, label in enumerate(buttons):
            row = index // 4
            col = index % 4
            tk.Button(
                grid,
                text=label,
                command=lambda value=label: self.press_calculator(value),
                relief="flat",
                bg="#DCE6F2",
                activebackground="#C8D6E5",
                font=("Segoe UI", 12, "bold"),
                height=2,
            ).grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

        tk.Button(panel, text="Clear", command=self.clear_calculator, relief="flat", bg="#FCA5A5", activebackground="#F87171", font=("Segoe UI", 11, "bold")).pack(fill="x", pady=(10, 0))

        for column in range(4):
            grid.grid_columnconfigure(column, weight=1)
        for row in range(4):
            grid.grid_rowconfigure(row, weight=1)

        window.built = True
        window.show()

    def press_calculator(self, value: str):
        if value == "=":
            expression = self.calculator_expression.get()
            try:
                allowed = set("0123456789.+-*/() ")
                if not set(expression) <= allowed:
                    raise ValueError("Only basic math is allowed.")
                result = eval(expression, {"__builtins__": {}}, {})
                self.calculator_expression.set(str(result))
            except Exception:
                self.calculator_expression.set("error")
            return

        self.calculator_expression.set(self.calculator_expression.get() + value)

    def clear_calculator(self):
        self.calculator_expression.set("")

    def open_process_monitor(self):
        window = self.create_internal_window("monitor", "Process Monitor", 720, 180, 360, 360)
        if getattr(window, "built", False):
            window.refresh()
            window.show()
            return

        panel = self.make_panel(window.content)
        tk.Label(panel, text="Open Windows", font=("Segoe UI", 18, "bold"), bg="#F4F7FB", fg="#22303C").pack(anchor="w", pady=(0, 10))

        window.listbox = tk.Listbox(panel, font=("Consolas", 11), relief="flat", bg="#FFFFFF", fg="#1F2937")
        window.listbox.pack(fill="both", expand=True)
        tk.Button(panel, text="Refresh", command=lambda: window.refresh(), relief="flat", bg="#DCE6F2", activebackground="#C8D6E5").pack(fill="x", pady=(10, 0))

        def refresh_monitor():
            window.listbox.delete(0, "end")
            for item in self.get_open_windows():
                status = "hidden" if item.hidden else "visible"
                window.listbox.insert("end", f"{item.title} [{status}]")

        window.refresh = refresh_monitor
        window.built = True
        window.refresh()
        window.show()

    def open_clock(self):
        window = self.create_internal_window("clock", "Clock", 860, 420, 240, 180)
        if getattr(window, "built", False):
            window.show()
            return

        panel = self.make_panel(window.content)
        tk.Label(panel, text="Current Time", font=("Segoe UI", 14, "bold"), bg="#F4F7FB", fg="#334155").pack(pady=(10, 8))
        tk.Label(panel, textvariable=self.clock_window_var, font=("Consolas", 28, "bold"), bg="#F4F7FB", fg="#1D4ED8").pack(expand=True)

        window.built = True
        window.show()

    def get_open_windows(self):
        return [window for window in self.windows.values() if not window.closed]

    def pretty_path(self, path) -> str:
        if path == self.context.root:
            return "/"
        return "/" + path.relative_to(self.context.root).as_posix()

    def update_clock(self):
        if self.closing or not self.root.winfo_exists():
            return

        now = self.root.tk.call("clock", "format", self.root.tk.call("clock", "seconds"), "-format", "%H:%M:%S")
        self.clock_taskbar_var.set(now)
        self.clock_window_var.set(now)
        self.clock_after_id = self.root.after(1000, self.update_clock)

    def shutdown(self):
        if self.closing:
            return

        self.closing = True

        if self.clock_after_id is not None:
            try:
                self.root.after_cancel(self.clock_after_id)
            except tk.TclError:
                pass
            self.clock_after_id = None

        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()


def execute(context, args, commands):
    PeePiOSWindow().run()
