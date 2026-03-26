from __future__ import annotations

import importlib.util
import io
import os
import shlex
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
CMD_DIR = ROOT_DIR / "cmd"
sys.dont_write_bytecode = True


@dataclass
class ShellContext:
    root: Path
    cwd: Path
    running: bool = True

    def prompt_path(self) -> str:
        if self.cwd == self.root:
            return "/"

        relative = self.cwd.relative_to(self.root).as_posix()
        return f"/{relative}"

    def resolve_path(self, raw_path: str | None) -> Path:
        if not raw_path or raw_path == ".":
            return self.cwd

        if raw_path.startswith("/"):
            target = self.root / raw_path.removeprefix("/")
        else:
            target = self.cwd / raw_path

        normalized = Path(os.path.normpath(target))

        try:
            normalized.relative_to(self.root)
        except ValueError:
            raise ValueError("Path escapes PeePiOS root.") from None

        return normalized

    def prompt(self) -> str:
        return f"PeePiOS:{self.prompt_path()} $ "


def load_commands() -> dict[str, object]:
    commands: dict[str, object] = {}

    for file_path in sorted(CMD_DIR.glob("*.py")):
        if file_path.name == "__init__.py":
            continue

        module_name = f"cmd.{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        command_name = getattr(module, "COMMAND", file_path.stem)
        commands[command_name] = module

    return commands


def create_shell() -> tuple[ShellContext, dict[str, object]]:
    return ShellContext(root=ROOT_DIR, cwd=ROOT_DIR), load_commands()


def execute_line(context: ShellContext, commands: dict[str, object], raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""

    output = io.StringIO()

    with redirect_stdout(output):
        try:
            parts = shlex.split(raw)
        except ValueError as error:
            print(f"parse error: {error}")
            return output.getvalue()

        command_name, *args = parts
        command = commands.get(command_name)

        if command is None:
            print(f"{command_name}: command not found")
            return output.getvalue()

        try:
            command.execute(context, args, commands)
        except Exception as error:  # Keep the shell alive on command errors.
            print(error)

    return output.getvalue()


def startup_message(context: ShellContext, commands: dict[str, object]) -> str:
    output = io.StringIO()

    with redirect_stdout(output):
        print("Welcome to PeePiOS")
        print("Type 'help' to list commands.")
        print(f"Current directory: {context.prompt_path()}")
        if "ls" in commands:
            commands["ls"].execute(context, [], commands)

    return output.getvalue()


def run_shell() -> None:
    context, commands = create_shell()
    print(startup_message(context, commands), end="")

    while context.running:
        try:
            raw = input(context.prompt())
        except (EOFError, KeyboardInterrupt):
            print()
            break

        print(execute_line(context, commands, raw), end="")


if __name__ == "__main__":
    run_shell()
