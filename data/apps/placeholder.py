DEFAULT_SIZE = (320, 220)


def build_placeholder(desktop, number: int):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    label = QLabel(str(number))
    label.setAlignment(Qt.AlignCenter)
    label.setObjectName("bigNumber")
    layout.addWidget(label, 1)

    subtitle = QLabel(f"Placeholder app window {number}")
    subtitle.setAlignment(Qt.AlignCenter)
    layout.addWidget(subtitle)

    desktop.apply_frosted_style(root)
    return root
