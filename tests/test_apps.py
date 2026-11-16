from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from android_tv_cli_manager.main import app
from android_tv_cli_manager.exceptions import AdbCommandError

runner = CliRunner()


@pytest.fixture
def mock_adb_controller() -> MagicMock:
    """Fixture to create a mock AdbController."""
    controller = MagicMock()
    controller.list_packages.return_value = [
        "com.google.android.youtube.tv",
        "com.netflix.ninja",
        "com.amazon.firetv.launcher",
    ]
    controller.get_package_info.return_value = "DUMP OF PACKAGE com.netflix.ninja"
    return controller


@patch("android_tv_cli_manager.main.AdbController")
def test_apps_list_success(mock_adb_class, mock_adb_controller):
    """Test the 'apps list' command with a successful response."""
    # Mock the AdbController instantiation and its methods
    mock_adb_class.return_value = mock_adb_controller
    mock_adb_controller.get_connected_devices.return_value = {"emulator-5554": "device"}

    result = runner.invoke(app, ["--device", "emulator-5554", "apps", "list"])

    assert result.exit_code == 0
    assert "Installed Packages" in result.stdout
    assert "com.google.android.youtube.tv" in result.stdout
    assert "com.netflix.ninja" in result.stdout
    assert "Total packages found: 3" in result.stdout
    mock_adb_controller.list_packages.assert_called_once()


@patch("android_tv_cli_manager.main.AdbController")
def test_apps_list_no_packages(mock_adb_class, mock_adb_controller):
    """Test the 'apps list' command when no packages are found."""
    mock_adb_class.return_value = mock_adb_controller
    mock_adb_controller.get_connected_devices.return_value = {"emulator-5554": "device"}
    mock_adb_controller.list_packages.return_value = []

    result = runner.invoke(app, ["--device", "emulator-5554", "apps", "list"])

    assert result.exit_code == 0
    assert "No packages found on the device." in result.stdout
    mock_adb_controller.list_packages.assert_called_once()


@patch("android_tv_cli_manager.main.AdbController")
def test_apps_list_adb_error(mock_adb_class, mock_adb_controller):
    """Test the 'apps list' command when AdbController raises an error."""
    mock_adb_class.return_value = mock_adb_controller
    mock_adb_controller.get_connected_devices.return_value = {"emulator-5554": "device"}
    mock_adb_controller.list_packages.side_effect = AdbCommandError("Failed to connect")

    result = runner.invoke(app, ["--device", "emulator-5554", "apps", "list"])

    assert result.exit_code == 1
    assert "Error listing apps: Failed to connect" in result.stdout
    mock_adb_controller.list_packages.assert_called_once()


@patch("android_tv_cli_manager.main.AdbController")
def test_app_info_success(mock_adb_class, mock_adb_controller):
    """Test the 'apps info' command with a valid package name."""
    mock_adb_class.return_value = mock_adb_controller
    mock_adb_controller.get_connected_devices.return_value = {"emulator-5554": "device"}
    package_name = "com.netflix.ninja"

    result = runner.invoke(app, ["--device", "emulator-5554", "apps", "info", package_name])

    assert result.exit_code == 0
    assert f"Package Information: {package_name}" in result.stdout
    assert "DUMP OF PACKAGE com.netflix.ninja" in result.stdout
    mock_adb_controller.get_package_info.assert_called_once_with(package_name)


@patch("android_tv_cli_manager.main.AdbController")
def test_app_info_package_not_found(mock_adb_class, mock_adb_controller):
    """Test the 'apps info' command for a package that does not exist."""
    mock_adb_class.return_value = mock_adb_controller
    mock_adb_controller.get_connected_devices.return_value = {"emulator-5554": "device"}
    package_name = "com.nonexistent.app"
    error_message = f"Package '{package_name}' not found on device 'emulator-5554'."
    mock_adb_controller.get_package_info.side_effect = AdbCommandError(error_message)

    result = runner.invoke(app, ["--device", "emulator-5554", "apps", "info", package_name])

    assert result.exit_code == 1
    assert f"Error getting app info: {error_message}" in result.stdout
    mock_adb_controller.get_package_info.assert_called_once_with(package_name)


@patch("android_tv_cli_manager.main.AdbController")
def test_app_info_missing_argument(mock_adb_class, mock_adb_controller):
    """Test the 'apps info' command without providing a package name."""
    mock_adb_class.return_value = mock_adb_controller
    mock_adb_controller.get_connected_devices.return_value = {"emulator-5554": "device"}

    result = runner.invoke(app, ["--device", "emulator-5554", "apps", "info"])

    assert result.exit_code != 0  # Typer handles this, exit code is 2
    assert "Missing argument 'PACKAGE_NAME'" in result.stdout
    mock_adb_controller.get_package_info.assert_not_called()
