APP_ID = "settings"
APP_TITLE = "Settings"
DEFAULT_SIZE = (460, 560)


def build_widget(desktop):
    from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    layout.addWidget(scroll)

    panel = QWidget()
    panel_layout = QVBoxLayout(panel)
    panel_layout.setContentsMargins(0, 0, 0, 0)
    panel_layout.setSpacing(8)
    scroll.setWidget(panel)

    panel_layout.addWidget(QLabel("Theme Colors"))

    themes = [
        ("Ocean", "#17202B", "#1A1F25"),
        ("Forest", "#1A241D", "#162119"),
        ("Sunset", "#2A1E1A", "#241815"),
        ("Slate", "#1C2026", "#171B21"),
    ]
    for name, desktop_bg, taskbar_bg in themes:
        button = QPushButton(name)
        button.clicked.connect(lambda _checked=False, d=desktop_bg, t=taskbar_bg: desktop.apply_theme(d, t))
        panel_layout.addWidget(button)

    panel_layout.addWidget(QLabel("Wallpapers"))
    panel_layout.addWidget(QLabel("Drop images into /settings/wallpaper and reopen or refresh Settings."))

    status = QLabel("No wallpaper selected.")
    panel_layout.addWidget(status)

    wallpaper_container = QWidget()
    wallpaper_layout = QVBoxLayout(wallpaper_container)
    wallpaper_layout.setContentsMargins(0, 0, 0, 0)
    wallpaper_layout.setSpacing(6)
    panel_layout.addWidget(wallpaper_container)

    refresh_button = QPushButton("Refresh Wallpapers")
    panel_layout.addWidget(refresh_button)
    panel_layout.addStretch(1)

    def refresh_wallpapers():
        while wallpaper_layout.count():
            item = wallpaper_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        clear_button = QPushButton("Use Theme Background")
        clear_button.clicked.connect(desktop.clear_wallpaper)
        wallpaper_layout.addWidget(clear_button)

        wallpapers = desktop.wallpaper_candidates()
        if wallpapers:
            current = desktop.current_wallpaper_path.name if desktop.current_wallpaper_path else "theme background"
            status.setText(f"Current wallpaper: {current}")
            for path in wallpapers:
                button = QPushButton(path.name)
                button.clicked.connect(lambda _checked=False, value=path: desktop.apply_wallpaper(value))
                wallpaper_layout.addWidget(button)
        else:
            status.setText("No supported wallpapers found in /settings/wallpaper.")

    refresh_button.clicked.connect(refresh_wallpapers)
    root.refresh_view = refresh_wallpapers
    desktop.apply_frosted_style(root)
    refresh_wallpapers()
    return root
