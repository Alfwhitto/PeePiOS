APP_ID = "browser"
APP_TITLE = "Browser"
DEFAULT_SIZE = (980, 680)
HOME_URL = "https://duckduckgo.com/"


class QuietWebEnginePage:
    def __new__(cls, *args, **kwargs):
        from PySide6.QtWebEngineCore import QWebEnginePage

        class _Page(QWebEnginePage):
            def javaScriptConsoleMessage(self, level, message, line_number, source_id):
                return

        return _Page(*args, **kwargs)


def build_widget(desktop):
    from urllib.parse import quote_plus

    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QSplitter,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    controls = QHBoxLayout()
    back_button = QPushButton("<")
    forward_button = QPushButton(">")
    reload_button = QPushButton("Reload")
    home_button = QPushButton("Home")
    new_tab_button = QPushButton("+ Tab")
    close_tab_button = QPushButton("- Tab")
    url_bar = QLineEdit()
    url_bar.setPlaceholderText("Enter a URL or search the web")

    controls.addWidget(back_button)
    controls.addWidget(forward_button)
    controls.addWidget(reload_button)
    controls.addWidget(home_button)
    controls.addWidget(new_tab_button)
    controls.addWidget(close_tab_button)
    controls.addWidget(url_bar, 1)
    layout.addLayout(controls)

    splitter = QSplitter()
    layout.addWidget(splitter, 1)

    history_panel = QWidget()
    history_layout = QVBoxLayout(history_panel)
    history_layout.setContentsMargins(0, 0, 0, 0)
    history_layout.setSpacing(8)
    history_layout.addWidget(QLabel("History"))
    history_list = QListWidget()
    history_layout.addWidget(history_list, 1)

    tabs = QTabWidget()
    tabs.setTabsClosable(True)
    splitter.addWidget(history_panel)
    splitter.addWidget(tabs)
    splitter.setSizes([220, 740])

    def normalize_url(value: str) -> QUrl:
        text = value.strip()
        if not text:
            return QUrl(HOME_URL)

        has_scheme = "://" in text
        looks_like_url = "." in text and " " not in text

        if not has_scheme and looks_like_url:
            text = f"https://{text}"
        elif not has_scheme:
            text = f"https://duckduckgo.com/?q={quote_plus(text)}"

        return QUrl(text)

    def current_view():
        return tabs.currentWidget()

    def sync_url(url):
        if current_view() is not None and current_view().url() == url:
            url_bar.setText(url.toString())

    def sync_title(title):
        index = tabs.currentIndex()
        if index >= 0:
            tabs.setTabText(index, title[:24] if title else "New Tab")

    def record_page():
        view = current_view()
        if view is None:
            return
        desktop.add_browser_history(view.title(), view.url().toString())
        refresh_history()

    def create_tab(url: str | None = None):
        view = QWebEngineView()
        view.setPage(QuietWebEnginePage(desktop.get_browser_profile(), view))
        view.setContextMenuPolicy(Qt.DefaultContextMenu)
        index = tabs.addTab(view, "New Tab")
        tabs.setCurrentIndex(index)
        view.urlChanged.connect(sync_url)
        view.titleChanged.connect(sync_title)
        view.loadFinished.connect(lambda _ok=False, browser=view: (desktop.add_browser_history(browser.title(), browser.url().toString()), refresh_history()))
        view.setUrl(QUrl(url or HOME_URL))
        return view

    def close_current_tab(index=None):
        if tabs.count() <= 1:
            return
        if index is None:
            index = tabs.currentIndex()
        widget = tabs.widget(index)
        tabs.removeTab(index)
        widget.deleteLater()

    def navigate():
        view = current_view()
        if view is None:
            view = create_tab()
        view.setUrl(normalize_url(url_bar.text()))

    def go_home():
        view = current_view()
        if view is None:
            view = create_tab()
        view.setUrl(QUrl(HOME_URL))

    def tab_changed(index):
        view = tabs.widget(index)
        if view is not None:
            url_bar.setText(view.url().toString())

    def refresh_history():
        history_list.clear()
        for entry in desktop.get_browser_history():
            item = QListWidgetItem(entry.get("title") or entry.get("url") or "Untitled")
            item.setToolTip(entry.get("url", ""))
            item.setData(Qt.UserRole, entry.get("url", ""))
            history_list.addItem(item)

    def open_history_item(item):
        url = item.data(Qt.UserRole)
        if not url:
            return
        view = current_view()
        if view is None:
            view = create_tab(url)
            return
        view.setUrl(QUrl(url))

    back_button.clicked.connect(lambda: current_view().back() if current_view() else None)
    forward_button.clicked.connect(lambda: current_view().forward() if current_view() else None)
    reload_button.clicked.connect(lambda: current_view().reload() if current_view() else None)
    home_button.clicked.connect(go_home)
    new_tab_button.clicked.connect(lambda: create_tab())
    close_tab_button.clicked.connect(close_current_tab)
    url_bar.returnPressed.connect(navigate)
    tabs.currentChanged.connect(tab_changed)
    tabs.tabCloseRequested.connect(close_current_tab)
    history_list.itemDoubleClicked.connect(open_history_item)

    root.refresh_view = refresh_history
    desktop.apply_frosted_style(root)
    create_tab(HOME_URL)
    refresh_history()
    return root
