APP_ID = "files"
APP_TITLE = "Files"
DEFAULT_SIZE = (560, 420)


def build_widget(desktop):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    top = QHBoxLayout()
    path_label = QLabel()
    path_label.setObjectName("pathLabel")
    top.addWidget(path_label, 1)

    up_button = QPushButton("Up")
    top.addWidget(up_button)
    layout.addLayout(top)

    listing = QListWidget()
    listing.setSelectionMode(QListWidget.SingleSelection)
    layout.addWidget(listing, 1)

    actions = QHBoxLayout()
    open_button = QPushButton("Open")
    refresh_button = QPushButton("Refresh")
    actions.addWidget(open_button)
    actions.addWidget(refresh_button)
    actions.addStretch(1)
    layout.addLayout(actions)

    def refresh():
        path_label.setText(desktop.pretty_path(desktop.file_browser_path))
        listing.clear()
        if desktop.file_browser_path != desktop.context.root:
            parent_item = QListWidgetItem("[DIR] ..")
            parent_item.setData(Qt.UserRole, ("dir", ".."))
            listing.addItem(parent_item)

        entries = sorted(desktop.file_browser_path.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
        for entry in entries:
            prefix = "[DIR]" if entry.is_dir() else "[FILE]"
            item = QListWidgetItem(f"{prefix} {entry.name}")
            item.setData(Qt.UserRole, ("dir" if entry.is_dir() else "file", entry.name))
            listing.addItem(item)

    def open_selected():
        item = listing.currentItem()
        if item is None:
            return
        kind, name = item.data(Qt.UserRole)
        if kind == "dir" and name == "..":
            desktop.file_browser_path = desktop.file_browser_path.parent
            refresh()
            return

        target = desktop.file_browser_path / name
        if kind == "dir":
            desktop.file_browser_path = target
            refresh()
            return

        desktop.open_app("notes", target)

    def go_up():
        if desktop.file_browser_path != desktop.context.root:
            desktop.file_browser_path = desktop.file_browser_path.parent
            refresh()

    listing.itemDoubleClicked.connect(lambda _item: open_selected())
    open_button.clicked.connect(open_selected)
    refresh_button.clicked.connect(refresh)
    up_button.clicked.connect(go_up)

    root.refresh_view = refresh
    desktop.apply_frosted_style(root)
    refresh()
    return root
