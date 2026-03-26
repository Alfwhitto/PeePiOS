COMMAND = "window"
DESCRIPTION = "Open the new PySide6 PeePiOS desktop."


def execute(context, args, commands):
    from data.desktop import run_desktop

    run_desktop()
