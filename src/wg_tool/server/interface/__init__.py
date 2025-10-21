# wg_tool/server/interface/__init__.py
"""
Facade for interface management functions.
"""
from .start import start_interface
from .stop import stop_interface
from .restart import restart_interface
from .remove import remove_interface

__all__ = ["start_interface", "stop_interface", "restart_interface", "remove_interface"]
