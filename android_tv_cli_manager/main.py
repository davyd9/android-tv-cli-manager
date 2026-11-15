"""Main entry point for the Android TV CLI Manager application."""

from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from android_tv_cli_manager import __version__
from android_tv_cli_manager.adb_controller import AdbController, Device
from android_tv_cli_manager.exceptions import AdbCommandError

app = typer.Typer(
    name="atv-cli",
    help="A command-line tool to manage Android TV and Google TV devices.",
    add_completion=False,
)

console = Console()
state = {"device_id": None}


def version_callback(value: bool) -> None:
    """Prints the application version and exits."""
    if value:
        console.print(f"Android TV CLI Manager Version: {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    device_id: Optional[str] = typer.Option(
        None,
        "--device",
        "-d",
        help="The target device ID (serial number). Bypasses interactive selection.",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show the application's version and exit.",
    ),
) -> None:
    """Manage Android TV devices from the command line."""
    if ctx.invoked_subcommand is None:
        console.print("[bold yellow]Welcome to Android TV CLI Manager![/bold yellow]")
        console.print("Run [bold cyan]atv-cli --help[/bold cyan] to see available commands.")
        return

    if device_id:
        state["device_id"] = device_id
        console.print(f"Targeting device specified via option: [bold cyan]{device_id}[/bold cyan]")
        return

    try:
        adb_controller = AdbController()
        devices = adb_controller.get_devices()
    except AdbCommandError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    if not devices:
        console.print("[bold red]Error:[/bold red] No devices found. Please connect a device and enable USB debugging.")
        raise typer.Exit(code=1)

    if len(devices) == 1:
        selected_device = devices[0]
        state["device_id"] = selected_device.serial
        console.print(f"Auto-selected only available device: [bold cyan]{selected_device.model}[/bold cyan] ({selected_device.serial})")
    else:
        console.print("[bold]Multiple devices found. Please select one:[/bold]")
        table = Table(title="Connected Devices")
        table.add_column("#", style="magenta")
        table.add_column("Model", style="green")
        table.add_column("Serial", style="cyan")
        table.add_column("Status", style="yellow")

        for i, device in enumerate(devices):
            table.add_row(str(i + 1), device.model, device.serial, device.status)

        console.print(table)
        choice_str = Prompt.ask("Enter the number of the device to manage", choices=[str(i + 1) for i in range(len(devices))])
        choice = int(choice_str) - 1
        selected_device = devices[choice]
        state["device_id"] = selected_device.serial
        console.print(f"Selected device: [bold cyan]{selected_device.model}[/bold cyan] ({selected_device.serial})")


@app.command()
def info() -> None:
    """Displays information about the selected device."""
    device_id = state.get("device_id")
    if not device_id:
        # This case should ideally not be reached due to the callback logic
        console.print("[bold red]Error: No device selected. This is an unexpected error.[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"Successfully connected to device: [bold green]{device_id}[/bold green]")
    console.print("Ready to execute commands.")
