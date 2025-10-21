import subprocess
from typing import Optional

def restart_interface(interface: str) -> bool:
    """
    Restart a WireGuard interface safely.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"[INFO] Bringing down interface {interface}...")
        subprocess.run(["sudo", "wg-quick", "down", interface], check=True)

        print(f"[INFO] Bringing up interface {interface}...")
        subprocess.run(["sudo", "wg-quick", "up", interface], check=True)

        print(f"[SUCCESS] Interface {interface} restarted successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to restart {interface}:\n{e.stderr}")
        return False


def activate_peer(interface: str, conf_path: Optional[str] = None) -> bool:
    """
    Activate a peer connection.
    If conf_path is provided, temporarily use it with wg-quick.
    """
    if conf_path:
        # Use a temporary config file to bring up the peer
        try:
            print(f"[INFO] Activating peer using config {conf_path}...")
            subprocess.run(["sudo", "wg-quick", "down", conf_path], check=False)  # ignore errors if already down
            subprocess.run(["sudo", "wg-quick", "up", conf_path], check=True)
            print(f"[SUCCESS] Peer activated from {conf_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to activate peer from {conf_path}:\n{e.stderr}")
            return False
    else:
        # Default behavior: just restart the main interface
        return restart_interface(interface)
