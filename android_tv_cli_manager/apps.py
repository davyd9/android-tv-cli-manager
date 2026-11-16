import logging
from typing import List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from android_tv_cli_manager.exceptions import AdbCommandError

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="apps",
    help="Manage applications on the Android TV device.",
    no_args_is_help=True,
)

console = Console()


@app.command("list", help="List all installed packages on the device.")
def list_apps(ctx: typer.Context) -> None:
    """
    Fetches and displays a list of all installed packages from the connected device.
    """
    adb_controller = ctx.obj.get("adb_controller")
    if not adb_controller:
        console.print("[bold red]Error: ADB controller not initialized.[/bold red]")
        raise typer.Exit(code=1)

    try:
        with console.status("[bold green]Fetching installed packages...[/bold green]", spinner="dots"):
            packages: List[str] = adb_controller.list_packages()

        if not packages:
            console.print("[yellow]No packages found on the device.[/yellow]")
            return

        table = Table(title="Installed Packages", show_header=True, header_style="bold magenta")
        table.add_column("Package Name", style="cyan", no_wrap=True)

        for pkg in packages:
            table.add_row(pkg)

        console.print(table)
        console.print(f"\n[bold green]Total packages found: {len(packages)}[/bold green]")

    except AdbCommandError as e:
        logger.error(f"Failed to list apps: {e}", exc_info=True)
        console.print(f"[bold red]Error listing apps: {e}[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.critical(f"An unexpected error occurred while listing apps: {e}", exc_info=True)
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command("info", help="Show detailed information about a specific package.")
def app_info(
    ctx: typer.Context,
    package_name: str = typer.Argument(..., help="The full package name (e.g., 'com.google.android.youtube.tv')."),
) -> None:
    """
    Fetches and displays detailed 'dumpsys' information for a given package.
    """
    adb_controller = ctx.obj.get("adb_controller")
    if not adb_controller:
        console.print("[bold red]Error: ADB controller not initialized.[/bold red]")
        raise typer.Exit(code=1)

    try:
        with console.status(f"[bold green]Fetching info for '{package_name}'...[/bold green]", spinner="dots"):
            info_dump: str = adb_controller.get_package_info(package_name)

        panel_title = f"[bold cyan]Package Information: {package_name}[/bold cyan]"
        console.print(Panel(info_dump, title=panel_title, border_style="green", expand=True))

    except AdbCommandError as e:
        logger.error(f"Failed to get app info for '{package_name}': {e}", exc_info=True)
        console.print(f"[bold red]Error getting app info: {e}[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.critical(f"An unexpected error occurred while getting app info: {e}", exc_info=True)
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        raise typer.Exit(code=1)
