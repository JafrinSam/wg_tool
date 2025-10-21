# wg_tool/server/interface/start.py
from typing import Tuple
from .utils import _run, ensure_wg_dir

def start_interface(name: str, enable: bool = True) -> Tuple[bool, str]:
    """
    Start a WireGuard interface by name using `wg-quick up <name>`.
    If enable=True, also run `systemctl enable/start wg-quick@<name>`.
    Returns (success, message).
    """
    ensure_wg_dir()
    # Bring up interface
    ok, out = _run(["sudo", "wg-quick", "up", name])
    if not ok:
        return False, f"wg-quick up failed: {out}"

    if enable:
        svc = f"wg-quick@{name}"
        ok_en, out_en = _run(["sudo", "systemctl", "enable", svc])
        if not ok_en:
            return False, f"Interface up but enable failed: {out_en}"
        ok_st, out_st = _run(["sudo", "systemctl", "start", svc])
        if not ok_st:
            return False, f"Interface up but service start failed: {out_st}"
        return True, f"Interface '{name}' started and enabled."
    return True, f"Interface '{name}' started."
