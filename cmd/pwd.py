COMMAND = "pwd"
DESCRIPTION = "Print the current location, where '/' is the PeePiOS folder."


def execute(context, args, commands):
    print(context.prompt_path())
