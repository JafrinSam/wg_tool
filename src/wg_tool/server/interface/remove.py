# wg_tool/server/interface/remove.py
from typing import Tuple
from pathlib import Path
from .stop import stop_interface
from .utils import _run, WG_DIR
from wg_tool import storage

def remove_interface(name: str, remove_config: bool = True, clear_storage: bool = False) -> Tuple[bool, str]:
    """
    Remove an interface:
      - wg-quick down <name>
      - systemctl disable wg-quick@<name>
      - optionally remove /etc/wireguard/<name>.conf
      - optionally clear server config in storage (if storage exposes a clear function)
    Returns (success, message).
    """
    ok_down, msg_down = stop_interface(name, disable=True)
    svc = f"wg-quick@{name}"
    ok_disable, out_disable = _run(["sudo", "systemctl", "disable", svc])
    cfg_path = WG_DIR / f"{name}.conf"
    cfg_msg = ""
    if remove_config:
        try:
            if cfg_path.exists():
                cfg_path.unlink()
                cfg_msg = f"Removed config {cfg_path}."
            else:
                cfg_msg = f"Config {cfg_path} not found."
        except Exception as e:
            return False, f"Failed to remove config {cfg_path}: {e}"

    storage_msg = ""
    if clear_storage:
        # optional: storage must provide clear_server_config(name) or clear_server_config()
        if hasattr(storage, "clear_server_config"):
            try:
                storage.remove_server(name)
                storage_msg = "Cleared server config from storage."
            except Exception as e:
                storage_msg = f"Storage clear failed: {e}"
        else:
            storage_msg = "Storage.clear_server_config() not implemented; skipped."

    parts = [f"down: {msg_down}", f"disable: {out_disable}", cfg_msg, storage_msg]
    return True, " | ".join([p for p in parts if p])
