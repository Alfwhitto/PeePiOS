APP_ID = "about"
APP_TITLE = "About"
DEFAULT_SIZE = (320, 280)


def build_widget(desktop):
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    title = QLabel("PeePiOS")
    title.setObjectName("appTitle")
    layout.addWidget(title)
    layout.addWidget(QLabel("A tiny Python desktop shell built with PySide6."))

    info = QLabel()
    info.setWordWrap(True)
    layout.addWidget(info, 1)

    def refresh():
        lines = [
            "Version: 0.2 PySide desktop",
            f"Root: {desktop.pretty_path(desktop.context.root)}",
            f"Current shell path: {desktop.context.prompt_path()}",
            f"Commands loaded: {len(desktop.commands)}",
            f"Open windows: {len(desktop.windows)}",
        ]
        info.setText("\n".join(lines))

    root.refresh_view = refresh
    desktop.apply_frosted_style(root)
    refresh()
    return root
