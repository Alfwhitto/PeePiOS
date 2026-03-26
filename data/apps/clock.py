APP_ID = "clock"
APP_TITLE = "Clock"
DEFAULT_SIZE = (240, 180)


def build_widget(desktop):
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
    from PySide6.QtCore import Qt

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    title = QLabel("Current Time")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    clock = QLabel()
    clock.setObjectName("clockLabel")
    clock.setAlignment(Qt.AlignCenter)
    layout.addWidget(clock, 1)

    def refresh():
        clock.setText(desktop.current_time_string())

    root.refresh_view = refresh
    root.clock_label = clock
    desktop.apply_frosted_style(root)
    refresh()
    return root
