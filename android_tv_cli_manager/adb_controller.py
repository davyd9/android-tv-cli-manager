import logging
import re
import subprocess
from typing import Dict, List, Optional

from android_tv_cli_manager.exceptions import AdbCommandError, AdbConnectionError

logger = logging.getLogger(__name__)


class AdbController:
    """A controller to interact with Android Debug Bridge (ADB)."""

    DEVICE_PATTERN = re.compile(r"^(\S+)\s+(device|offline|unauthorized)\s+.*$")

    def __init__(self, adb_path: str = "adb"):
        """
        Initializes the AdbController.

        Args:
            adb_path: The path to the ADB executable. Defaults to 'adb'.
        """
        self.adb_path = adb_path
        self.device_id: Optional[str] = None
        logger.debug(f"AdbController initialized with adb_path: '{self.adb_path}'")

    def set_device(self, device_id: str) -> None:
        """Sets the target device ID for subsequent commands."""
        self.device_id = device_id
        logger.info(f"Target device set to: '{self.device_id}'")

    def _run_command(self, command: List[str]) -> str:
        """
        Executes an ADB command and returns its output.

        Args:
            command: A list of strings representing the command and its arguments.

        Returns:
            The standard output of the command as a string.

        Raises:
            AdbConnectionError: If the adb executable is not found.
            AdbCommandError: If the command returns a non-zero exit code.
        """
        try:
            logger.debug(f"Running ADB command: {' '.join(command)}")
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,  # We check the return code manually
                encoding="utf-8",
            )
            if process.returncode != 0:
                error_message = process.stderr.strip() or process.stdout.strip()
                raise AdbCommandError(f"ADB command failed: {error_message}")
            return process.stdout
        except FileNotFoundError:
            raise AdbConnectionError(
                f"ADB executable not found at '{self.adb_path}'. "
                "Please ensure it is installed and in your system's PATH."
            )

    def get_connected_devices(self) -> Dict[str, str]:
        """
        Retrieves a list of connected Android devices and their statuses.

        Returns:
            A dictionary mapping device IDs to their connection status.
        """
        logger.info("Discovering connected devices...")
        command = [self.adb_path, "devices", "-l"]
        output = self._run_command(command)

        devices: Dict[str, str] = {}
        lines = output.strip().splitlines()
        if len(lines) <= 1 and "List of devices attached" in lines[0]:
            logger.warning("No devices found.")
            return {}

        for line in lines[1:]:  # Skip the "List of devices attached" header
            match = self.DEVICE_PATTERN.match(line)
            if match:
                device_id, status = match.groups()
                devices[device_id] = status
                logger.debug(f"Found device: {device_id} with status: {status}")

        if not devices:
            logger.warning("No devices parsed from ADB output.")
        else:
            logger.info(f"Found {len(devices)} device(s).")
        return devices

    def list_packages(self) -> List[str]:
        """
        Lists all installed packages on the selected device.

        Returns:
            A list of package names.

        Raises:
            AdbCommandError: If the adb command fails.
            AdbConnectionError: If the ADB connection fails.
        """
        if not self.device_id:
            raise AdbCommandError("No device selected. Please select a device first.")

        logger.info(f"Listing all packages for device '{self.device_id}'")
        command = [self.adb_path, "-s", self.device_id, "shell", "pm", "list", "packages"]
        try:
            output = self._run_command(command)
            # Output format is "package:com.example.app"
            packages = [line.split(":", 1)[1] for line in output.strip().splitlines() if line]
            logger.info(f"Found {len(packages)} packages on device '{self.device_id}'")
            return sorted(packages)
        except AdbCommandError as e:
            logger.error(f"Failed to list packages for device '{self.device_id}': {e}")
            raise

    def get_package_info(self, package_name: str) -> str:
        """
        Retrieves detailed information about a specific package.

        Args:
            package_name: The name of the package to query.

        Returns:
            A string containing the raw output from the 'dumpsys package' command.

        Raises:
            AdbCommandError: If the adb command fails or the package is not found.
            AdbConnectionError: If the ADB connection fails.
        """
        if not self.device_id:
            raise AdbCommandError("No device selected. Please select a device first.")

        logger.info(f"Getting package info for '{package_name}' on device '{self.device_id}'")
        command = [self.adb_path, "-s", self.device_id, "shell", "dumpsys", "package", package_name]
        try:
            output = self._run_command(command)
            if not output.strip() or "Unable to find package" in output:
                raise AdbCommandError(f"Package '{package_name}' not found on device '{self.device_id}'.")
            return output
        except AdbCommandError as e:
            if "Unable to find package" in str(e):
                raise AdbCommandError(f"Package '{package_name}' not found on device '{self.device_id}'.") from e
            logger.error(f"Failed to get info for package '{package_name}': {e}")
            raise
