from wg_tool.server.server_selector import select_server
from pathlib import Path
import subprocess
from wg_tool import storage

WG_DIR = "/etc/wireguard/"

class ServerDeleteError(Exception):
    """Base class for errors when deleting a server."""
    pass

def delete_server_interactive():
    """
    Interactive deletion of a WireGuard server:
    - Lists all servers
    - Prompts user to select by index
    - Stops & disables interface
    - Removes config file
    - Deletes from DB
    """
    try:
        server = select_server()  # <- Uses your server_selector module
        name = server["name"]
        conf_path = Path(WG_DIR) / f"{name}.conf"

        # Stop and disable systemd service
        subprocess.run(["sudo", "systemctl", "stop", f"wg-quick@{name}"], check=False)
        subprocess.run(["sudo", "systemctl", "disable", f"wg-quick@{name}"], check=False)

        # Delete interface if it exists
        subprocess.run(["sudo", "ip", "link", "delete", name], check=False)

        # Remove config file
        if conf_path.exists():
            conf_path.unlink()
            print(f"✅ Config file '{conf_path}' removed.")

        # Remove from DB
        storage.remove_server(name)
        print(f"✅ Server '{name}' removed from database.")

        return True

    except Exception as e:
        raise ServerDeleteError(f"Failed to delete server '{name}': {e}")
