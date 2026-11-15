"""Custom exceptions for the Android TV CLI Manager application."""


class ATVCliManagerError(Exception):
    """Base exception class for all application-specific errors."""
    pass


class AdbCommandError(ATVCliManagerError):
    """Raised when an ADB command fails to execute or returns an error."""
    pass


class NoDevicesFoundError(ATVCliManagerError):
    """Raised when no Android devices are found by ADB."""
    pass
