"""
usb_sync.py — Re-exportación para retrocompatibilidad hacia src/core/usb.
"""

from core.usb import (
    USBDrive,
    USBDetector,
    USBSyncConfig,
    USBNotFoundError,
    USBSyncError,
    USBSync,
)

__all__ = [
    "USBDrive",
    "USBDetector",
    "USBSyncConfig",
    "USBNotFoundError",
    "USBSyncError",
    "USBSync",
]
