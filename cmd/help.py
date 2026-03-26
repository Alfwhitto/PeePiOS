COMMAND = "help"
DESCRIPTION = "List commands, or use 'help -a' to see what each command does."


def execute(context, args, commands):
    if args == ["-a"]:
        print("Available commands:")
        for name in sorted(commands):
            description = getattr(commands[name], "DESCRIPTION", "No description available.")
            print(f"  {name}: {description}")
        return

    print("Available commands:")
    for name in sorted(commands):
        print(f"  {name}")
