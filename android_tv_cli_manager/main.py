import logging
from typing import Dict, Optional

import typer
from rich.console import Console
from rich.prompt import Prompt

from android_tv_cli_manager import __version__
from android_tv_cli_manager.adb_controller import AdbController
from android_tv_cli_manager.apps import app as apps_app
from android_tv_cli_manager.exceptions import AdbCommandError, AdbConnectionError

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("atv_cli_manager.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class State:
    """A shared state object for the CLI context."""

    def __init__(self):
        self.adb_controller: Optional[AdbController] = None


state = State()
console = Console()

app = typer.Typer(
    name="atv-cli",
    help="A CLI tool to manage Android TV devices via ADB.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Add the new 'apps' subcommand router
app.add_typer(apps_app, name="apps")


def version_callback(value: bool) -> None:
    """Prints the version of the application and exits."""
    if value:
        console.print(f"android-tv-cli-manager version: {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show the application's version and exit.",
    ),
    adb_path: str = typer.Option(
        "adb",
        "--adb-path",
        help="Path to the ADB executable.",
    ),
    device: Optional[str] = typer.Option(
        None,
        "--device",
        "-d",
        help="The target device ID. If not provided, you will be prompted to select one.",
    ),
) -> None:
    """
    Main callback to initialize ADB controller and select a device.
    This runs before any command.
    """
    # This check prevents the callback from running for --version or when no command is passed
    if ctx.invoked_subcommand is None and not version:
        return

    try:
        adb_controller = AdbController(adb_path=adb_path)
        connected_devices: Dict[str, str] = adb_controller.get_connected_devices()

        if not connected_devices:
            console.print("[bold red]No devices found. Please ensure your device is connected and ADB debugging is enabled.[/bold red]")
            raise typer.Exit(code=1)

        target_device_id = device
        if not target_device_id:
            if len(connected_devices) == 1:
                target_device_id = list(connected_devices.keys())[0]
                console.print(f"Auto-selecting the only connected device: [cyan]{target_device_id}[/cyan]")
            else:
                console.print("Multiple devices found. Please select one:")
                device_options = list(connected_devices.keys())
                for i, dev_id in enumerate(device_options, 1):
                    console.print(f"{i}. {dev_id} ({connected_devices[dev_id]})")

                choice_str = Prompt.ask("Enter the number of the device to use", choices=[str(i) for i in range(1, len(device_options) + 1)], default="1")
                target_device_id = device_options[int(choice_str) - 1]

        if target_device_id not in connected_devices:
            console.print(f"[bold red]Error: Device '{target_device_id}' not found or not connected.[/bold red]")
            raise typer.Exit(code=1)

        adb_controller.set_device(target_device_id)
        ctx.obj = {"adb_controller": adb_controller}

    except (AdbConnectionError, AdbCommandError) as e:
        console.print(f"[bold red]ADB Error: {e}[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.critical(f"An unexpected error occurred during initialization: {e}", exc_info=True)
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        raise typer.Exit(code=1)
