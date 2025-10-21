# wg_tool/server/interface/stop.py
from typing import Tuple
from .utils import _run

def stop_interface(name: str, disable: bool = False) -> Tuple[bool, str]:
    """
    Stop a WireGuard interface using `wg-quick down <name>`.
    If disable=True, also run `systemctl disable wg-quick@<name>`.
    Returns (success, message).
    """
    ok, out = _run(["sudo", "wg-quick", "down", name])
    if not ok:
        # wg-quick down may fail if interface not present; report but continue to disable option
        msg = f"wg-quick down returned error: {out}"
    else:
        msg = f"Interface '{name}' stopped."

    if disable:
        svc = f"wg-quick@{name}"
        ok2, out2 = _run(["sudo", "systemctl", "disable", svc])
        if not ok2:
            return False, f"{msg} but systemctl disable failed: {out2}"
        return True, f"{msg} and disabled."
    return ok, msg
