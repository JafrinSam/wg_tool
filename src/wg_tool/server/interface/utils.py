# wg_tool/server/interface/utils.py
"""
Utility helpers used by the interface modules.
"""
from pathlib import Path
import subprocess
from typing import Tuple

WG_DIR = Path("/etc/wireguard")

def _run(cmd: list) -> Tuple[bool, str]:
    """
    Run a command and return (success, combined_output).
    Does not raise — caller handles failures.
    """
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = (proc.stdout or "") + (proc.stderr or "")
        return True, out.strip()
    except subprocess.CalledProcessError as e:
        out = (e.stdout or "") + (e.stderr or "")
        return False, out.strip()

def ensure_wg_dir():
    """Ensure /etc/wireguard exists (caller may need root)."""
    WG_DIR.mkdir(parents=True, exist_ok=True)
