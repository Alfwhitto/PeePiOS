APP_ID = "monitor"
APP_TITLE = "Process Monitor"
DEFAULT_SIZE = (360, 360)


def build_widget(desktop):
    from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    layout.addWidget(QLabel("Open Windows"))
    listing = QListWidget()
    layout.addWidget(listing, 1)
    refresh_button = QPushButton("Refresh")
    layout.addWidget(refresh_button)

    def refresh():
        listing.clear()
        for app_id, window in desktop.windows.items():
            listing.addItem(f"{window.windowTitle()} [{app_id}]")

    refresh_button.clicked.connect(refresh)
    root.refresh_view = refresh
    desktop.apply_frosted_style(root)
    refresh()
    return root
