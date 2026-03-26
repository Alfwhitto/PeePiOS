APP_ID = "notes"
APP_TITLE = "Notes"
DEFAULT_SIZE = (620, 460)


def build_widget(desktop):
    from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    top = QHBoxLayout()
    top.addWidget(QLabel("File:"))
    path_edit = QLineEdit()
    top.addWidget(path_edit, 1)
    load_button = QPushButton("Load")
    save_button = QPushButton("Save")
    top.addWidget(load_button)
    top.addWidget(save_button)
    layout.addLayout(top)

    status = QLabel("Ready")
    layout.addWidget(status)

    editor = QTextEdit()
    layout.addWidget(editor, 1)

    def load_target(path=None):
        if path is not None:
            desktop.note_target_path = path
        if desktop.note_target_path is None:
            desktop.note_target_path = desktop.context.root / "notes.txt"

        target = desktop.note_target_path
        path_edit.setText(desktop.pretty_path(target))
        if target.exists() and target.is_file():
            editor.setPlainText(target.read_text(encoding="utf-8"))
            status.setText(f"Loaded {desktop.pretty_path(target)}")
        else:
            editor.setPlainText("")
            status.setText(f"New file {desktop.pretty_path(target)}")

        window = desktop.windows.get(APP_ID)
        if window is not None:
            window.setWindowTitle(f"Notes - {target.name}")

    def load_from_entry():
        try:
            desktop.note_target_path = desktop.context.resolve_path(path_edit.text())
            load_target()
        except Exception as error:
            status.setText(str(error))

    def save_file():
        try:
            desktop.note_target_path = desktop.context.resolve_path(path_edit.text())
            desktop.note_target_path.parent.mkdir(parents=True, exist_ok=True)
            desktop.note_target_path.write_text(editor.toPlainText(), encoding="utf-8")
            status.setText(f"Saved {desktop.pretty_path(desktop.note_target_path)}")
            desktop.refresh_app("files")
        except Exception as error:
            status.setText(str(error))

    load_button.clicked.connect(load_from_entry)
    save_button.clicked.connect(save_file)

    root.load_target = load_target
    desktop.apply_frosted_style(root)
    load_target()
    return root
