from __future__ import annotations

import tkinter as tk

from main import create_shell, execute_line, startup_message


COMMAND = "window_old"
DESCRIPTION = "Open the legacy Tkinter PeePiOS desktop."


class LegacyDesktop:
    def __init__(self):
        self.context, self.commands = create_shell()
        self.root = tk.Tk()
        self.root.title("PeePiOS Legacy")
        self.root.geometry("1080x700")
        self.root.minsize(860, 560)
        self.root.configure(bg="#17202B")

        self.desktop = tk.Frame(self.root, bg="#17202B")
        self.desktop.pack(fill="both", expand=True)

        self.terminal_window = tk.Frame(self.desktop, bg="#10161D", highlightbackground="#6FA8DC", highlightthickness=1)
        self.terminal_window.place(x=110, y=70, width=860, height=500)

        title = tk.Label(self.terminal_window, text="Terminal", bg="#223040", fg="#F8FAFC", font=("Segoe UI", 10, "bold"))
        title.pack(fill="x")

        self.output = tk.Text(self.terminal_window, bg="#10161D", fg="#D7E0EA", insertbackground="#D7E0EA", relief="flat", font=("Consolas", 11))
        self.output.pack(fill="both", expand=True)
        self.output.insert("end", startup_message(self.context, self.commands))
        self.output.configure(state="disabled")

        input_row = tk.Frame(self.terminal_window, bg="#151B22")
        input_row.pack(fill="x")

        self.prompt = tk.Label(input_row, text=self.context.prompt(), bg="#151B22", fg="#8BE9FD", font=("Consolas", 11))
        self.prompt.pack(side="left", padx=12, pady=10)

        self.entry = tk.Entry(input_row, bg="#151B22", fg="#F8FAFC", insertbackground="#F8FAFC", relief="flat", font=("Consolas", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=10)
        self.entry.bind("<Return>", self.run_command)

        self.taskbar = tk.Frame(self.root, bg="#1A1F25", height=58)
        self.taskbar.pack(fill="x", side="bottom")
        self.taskbar.pack_propagate(False)

        for label, action in [
            ("Exit", self.root.destroy),
            ("Terminal", self.focus_terminal),
            ("1", lambda: self.open_number_window(1)),
            ("2", lambda: self.open_number_window(2)),
            ("3", lambda: self.open_number_window(3)),
        ]:
            button = tk.Label(self.taskbar, text=label, bg="#1A1F25", fg="#F8FAFC", font=("Segoe UI", 10, "bold"), padx=14, pady=8, cursor="hand2")
            button.pack(side="left", padx=6, pady=8)
            button.bind("<Button-1>", lambda _event, callback=action: callback())

    def append_output(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def run_command(self, _event=None):
        raw = self.entry.get()
        if not raw.strip():
            return
        self.append_output(f"{self.context.prompt()}{raw}\n")
        self.entry.delete(0, "end")
        result = execute_line(self.context, self.commands, raw)
        if result:
            self.append_output(result if result.endswith("\n") else f"{result}\n")
        self.prompt.configure(text=self.context.prompt())
        if not self.context.running:
            self.root.destroy()

    def focus_terminal(self):
        self.entry.focus_set()

    def open_number_window(self, number: int):
        window = tk.Toplevel(self.root)
        window.title(f"App {number}")
        window.geometry("300x200")
        window.configure(bg="#E8EEF5")
        label = tk.Label(window, text=str(number), bg="#E8EEF5", fg="#213547", font=("Segoe UI", 54, "bold"))
        label.pack(expand=True)

    def run(self):
        self.focus_terminal()
        self.root.mainloop()


def execute(context, args, commands):
    LegacyDesktop().run()
