APP_ID = "calculator"
APP_TITLE = "Calculator"
DEFAULT_SIZE = (340, 430)


def build_widget(desktop):
    from PySide6.QtWidgets import QGridLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    display = QLineEdit()
    display.setReadOnly(False)
    display.setText(desktop.calculator_expression)
    layout.addWidget(display)

    grid_widget = QWidget()
    grid = QGridLayout(grid_widget)
    grid.setSpacing(6)
    layout.addWidget(grid_widget, 1)

    buttons = [
        "7", "8", "9", "/",
        "4", "5", "6", "*",
        "1", "2", "3", "-",
        "0", ".", "=", "+",
    ]

    def press(value):
        if value == "=":
            expression = display.text()
            try:
                allowed = set("0123456789.+-*/() ")
                if not set(expression) <= allowed:
                    raise ValueError("Only basic math is allowed.")
                result = eval(expression, {"__builtins__": {}}, {})
                desktop.calculator_expression = str(result)
            except Exception:
                desktop.calculator_expression = "error"
        else:
            desktop.calculator_expression = display.text() + value
        display.setText(desktop.calculator_expression)

    for index, label in enumerate(buttons):
        button = QPushButton(label)
        button.clicked.connect(lambda _checked=False, value=label: press(value))
        grid.addWidget(button, index // 4, index % 4)

    clear_button = QPushButton("Clear")
    clear_button.clicked.connect(lambda: (setattr(desktop, "calculator_expression", ""), display.setText("")))
    layout.addWidget(clear_button)

    desktop.apply_frosted_style(root)
    return root
