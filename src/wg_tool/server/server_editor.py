# wg_tool/server/server_editor.py

import subprocess
from pathlib import Path
from wg_tool import storage, keys

WG_DIR = "/etc/wireguard/"

class ServerEditError(Exception):
    """Base class for errors when editing servers."""
    pass

class ServerNotFoundError(ServerEditError):
    """Raised when the server does not exist."""
    pass

def prompt_update_field(field_name: str, current_value: str) -> str:
    """Ask the user to keep current value or enter a new one."""
    new_value = input(f"{field_name} [current: '{current_value}'] (leave blank to keep current): ").strip()
    return new_value or current_value

def edit_server_interactive(server: dict):
    old_name = server["name"]
    print(f"Editing server '{old_name}'")

    # Prompt for each field
    new_name = prompt_update_field("Server Name", old_name)
    new_subnet = prompt_update_field("Subnet", server["subnet"])
    new_dns = prompt_update_field("DNS", server.get("dns", ""))

    # Extract current port from endpoint (fallback 51820)
    current_port = "51820"
    if server.get("endpoint"):
        try:
            current_port = server["endpoint"].split(":")[-1]
        except Exception:
            pass

    new_port = prompt_update_field("Port", current_port)
    regenerate_keys_input = input("Regenerate keys? (y/N): ").strip().lower()
    regenerate_keys = regenerate_keys_input == "y"

    # Duplicate checks
    if new_name != old_name and new_name in storage.get_all_server_names():
        raise ServerEditError(f"Server name '{new_name}' already exists.")

    if new_subnet != server["subnet"]:
        for s in storage.get_all_servers():
            if s["name"] != old_name and s["subnet"] == new_subnet:
                raise ServerEditError(f"Subnet '{new_subnet}' already used by server '{s['name']}'.")

    # Generate keys if requested
    private_key = server["private_key"]
    public_key = server["public_key"]
    if regenerate_keys:
        private_key = keys.gen_private_key()
        public_key = keys.pubkey_from_private(private_key)

    # Build new endpoint (always subnet_ip:port)
    new_endpoint = f"{new_subnet.split('/')[0]}:{new_port}"

    # Rename config file if name changed
    old_conf_path = Path(WG_DIR) / f"{old_name}.conf"
    new_conf_path = Path(WG_DIR) / f"{new_name}.conf"
    if new_name != old_name and old_conf_path.exists():
        old_conf_path.rename(new_conf_path)

    # Update DB (note: no port column, only endpoint)
    storage.update_server(
        old_name,
        subnet=new_subnet,
        private_key=private_key,
        public_key=public_key,
        dns=new_dns,
        endpoint=new_endpoint,
        new_name=new_name
    )

    # Update config file
    config_text = "[Interface]\n"
    config_text += f"Address = {new_subnet}\n"
    config_text += f"PrivateKey = {private_key}\n"
    config_text += f"ListenPort = {new_port}\n"
    if new_dns:
        config_text += f"DNS = {new_dns}\n"

    new_conf_path.write_text(config_text)
    new_conf_path.chmod(0o600)

    # Restart interface
    try:
        subprocess.run(["sudo", "wg-quick", "down", old_name], check=False)
        subprocess.run(["sudo", "systemctl", "disable", f"wg-quick@{old_name}"], check=False)
        subprocess.run(["sudo", "systemctl", "enable", f"wg-quick@{new_name}"], check=True)
        subprocess.run(["sudo", "systemctl", "restart", f"wg-quick@{new_name}"], check=True)
        print(f"✅ Server '{old_name}' updated successfully as '{new_name}' (port {new_port})")
    except subprocess.CalledProcessError as e:
        raise ServerEditError(f"Failed to restart interface '{new_name}': {e}")
