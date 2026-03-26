APP_ID = "launcher"
APP_TITLE = "Launcher"
DEFAULT_SIZE = (320, 420)


def build_widget(desktop):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton, QScrollArea, QVBoxLayout, QWidget

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    container = QWidget()
    container.setAttribute(Qt.WA_StyledBackground, True)
    container.setStyleSheet("background: transparent;")
    container_layout = QVBoxLayout(container)
    container_layout.setContentsMargins(0, 0, 0, 0)
    container_layout.setSpacing(8)

    for app_id in desktop.launchable_app_ids():
        button = QPushButton(desktop.app_title(app_id))
        button.clicked.connect(lambda _checked=False, value=app_id: desktop.open_app(value))
        container_layout.addWidget(button)

    container_layout.addStretch(1)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollArea > QWidget > QWidget { background: transparent; }")
    scroll.setWidget(container)
    layout.addWidget(scroll)

    desktop.apply_frosted_style(root)
    return root
