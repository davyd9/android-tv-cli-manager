"""Module for controlling and interacting with Android Debug Bridge (ADB)."""

import re
import subprocess
from dataclasses import dataclass
from typing import List

from android_tv_cli_manager.exceptions import AdbCommandError


@dataclass(frozen=True)
class Device:
    """Represents a connected Android device."""

    serial: str
    status: str
    model: str


class AdbController:
    """A controller to execute and handle ADB commands."""

    _DEVICE_LINE_RE = re.compile(r"^(\S+?)\s+(device|offline|unauthorized).*?model:(\S+?)\s+")

    def get_devices(self) -> List[Device]:
        """Retrieves a list of connected Android devices.

        Raises:
            AdbCommandError: If the ADB command is not found or fails to execute.

        Returns:
            A list of Device objects representing the connected devices.
        """
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
            )
        except FileNotFoundError:
            raise AdbCommandError(
                "ADB command not found. Please ensure 'adb' is installed and in your system's PATH."
            )

        if result.returncode != 0:
            error_message = result.stderr.strip()
            raise AdbCommandError(f"ADB command failed: {error_message}")

        return self._parse_devices_output(result.stdout)

    def _parse_devices_output(self, output: str) -> List[Device]:
        """Parses the output of 'adb devices -l' into a list of Device objects."""
        devices: List[Device] = []
        lines = output.strip().splitlines()

        for line in lines:
            match = self._DEVICE_LINE_RE.match(line)
            if match:
                serial, status, model = match.groups()
                devices.append(Device(serial=serial, status=status, model=model))

        return devices
