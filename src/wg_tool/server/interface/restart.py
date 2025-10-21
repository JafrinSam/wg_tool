# wg_tool/server/interface/restart.py
from typing import Tuple
from .stop import stop_interface
from .start import start_interface

def restart_interface(name: str) -> Tuple[bool, str]:
    """
    Restart an interface: stop (no disable) then start (enable).
    Returns (success, message).
    """
    ok_stop, out_stop = stop_interface(name, disable=False)
    # attempt start even if stop reported errors (best-effort)
    ok_start, out_start = start_interface(name, enable=True)
    if ok_start:
        return True, f"Interface '{name}' restarted."
    return False, f"Restart issues: stop: {out_stop}; start: {out_start}"
