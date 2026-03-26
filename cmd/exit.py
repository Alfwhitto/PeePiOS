COMMAND = "exit"
DESCRIPTION = "Close the PeePiOS shell."


def execute(context, args, commands):
    context.running = False
