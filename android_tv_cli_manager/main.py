import sys
from typing import Optional

import typer
from rich.console import Console

from android_tv_cli_manager import __version__

app = typer.Typer(
    name="atv-cli",
    help="A robust CLI tool to manage apps, packages, and permissions on Android/Google TV devices.",
    add_completion=False,
    rich_markup_mode="markdown",
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


def version_callback(value: bool) -> None:
    """Prints the application version and exits."""
    if value:
        console.print(f"[bold green]Android TV CLI Manager[/bold green] version [cyan]{__version__}[/cyan]")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show application version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    Android TV CLI Manager: Your ultimate tool for taming Android TV devices.
    """
    if ctx.invoked_subcommand is None:
        console.print("[bold yellow]No command specified.[/bold yellow]")
        console.print("Use '[bold]atv-cli --help[/bold]' to see available commands.")
        sys.exit(1)


if __name__ == "__main__":
    app()
