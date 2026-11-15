"""Unit tests for the AdbController module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from android_tv_cli_manager.adb_controller import AdbController, Device
from android_tv_cli_manager.exceptions import AdbCommandError


class TestAdbController:
    """Test suite for the AdbController class."""

    @pytest.fixture
    def adb_controller(self) -> AdbController:
        """Returns an instance of AdbController for testing."""
        return AdbController()

    @patch("subprocess.run")
    def test_get_devices_success_multiple_devices(self, mock_run: MagicMock, adb_controller: AdbController) -> None:
        """Test successful discovery of multiple devices."""
        mock_output = (
            "List of devices attached\n"
            "192.168.1.101:5555   device product:shieldu model:SHIELD_Android_TV device:foster transport_id:2\n"
            "emulator-5554        device product:sdk_gphone_x86 model:Android_SDK_built_for_x86 device:generic_x86 transport_id:1\n"
        )
        mock_run.return_value = subprocess.CompletedProcess(
            args=["adb", "devices", "-l"], returncode=0, stdout=mock_output, stderr=""
        )

        devices = adb_controller.get_devices()

        assert len(devices) == 2
        assert devices[0] == Device(serial="192.168.1.101:5555", status="device", model="SHIELD_Android_TV")
        assert devices[1] == Device(serial="emulator-5554", status="device", model="Android_SDK_built_for_x86")
        mock_run.assert_called_once_with(
            ["adb", "devices", "-l"], capture_output=True, text=True, check=False, encoding="utf-8"
        )

    @patch("subprocess.run")
    def test_get_devices_success_no_devices(self, mock_run: MagicMock, adb_controller: AdbController) -> None:
        """Test handling of no attached devices."""
        mock_output = "List of devices attached\n"
        mock_run.return_value = subprocess.CompletedProcess(
            args=["adb", "devices", "-l"], returncode=0, stdout=mock_output, stderr=""
        )

        devices = adb_controller.get_devices()

        assert len(devices) == 0

    @patch("subprocess.run")
    def test_get_devices_unauthorized_and_offline(self, mock_run: MagicMock, adb_controller: AdbController) -> None:
        """Test parsing of devices with 'unauthorized' and 'offline' statuses."""
        mock_output = (
            "List of devices attached\n"
            "ABCDEF123456         unauthorized transport_id:3 model:Some_Device\n"
            "ZYXWVU987654         offline transport_id:4 model:Another_Device\n"
        )
        mock_run.return_value = subprocess.CompletedProcess(
            args=["adb", "devices", "-l"], returncode=0, stdout=mock_output, stderr=""
        )

        devices = adb_controller.get_devices()

        assert len(devices) == 2
        assert devices[0] == Device(serial="ABCDEF123456", status="unauthorized", model="Some_Device")
        assert devices[1] == Device(serial="ZYXWVU987654", status="offline", model="Another_Device")

    @patch("subprocess.run")
    def test_get_devices_adb_not_found(self, mock_run: MagicMock, adb_controller: AdbController) -> None:
        """Test exception handling when 'adb' command is not found."""
        mock_run.side_effect = FileNotFoundError

        with pytest.raises(AdbCommandError) as exc_info:
            adb_controller.get_devices()

        assert "ADB command not found" in str(exc_info.value)

    @patch("subprocess.run")
    def test_get_devices_adb_command_fails(self, mock_run: MagicMock, adb_controller: AdbController) -> None:
        """Test exception handling when 'adb' command returns a non-zero exit code."""
        mock_error = "error: device not found"
        mock_run.return_value = subprocess.CompletedProcess(
            args=["adb", "devices", "-l"], returncode=1, stdout="", stderr=mock_error
        )

        with pytest.raises(AdbCommandError) as exc_info:
            adb_controller.get_devices()

        assert f"ADB command failed: {mock_error}" in str(exc_info.value)
