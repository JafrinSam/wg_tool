from typing import Optional
from pathlib import Path
import click
from wg_tool import storage, utili
import subprocess

def gen_client_conf(
    private_key: str,
    server_pubkey: str,
    endpoint: str,
    address: str,
    allowed_ips: str = "0.0.0.0/0, ::/0",
    dns: Optional[str] = "1.1.1.1",
    psk: Optional[str] = None
) -> str:
    """
    Generate a WireGuard client configuration as text
    """

    server_pubkey = server_pubkey or storage.get_server_pubkey()
    endpoint = endpoint or storage.get_server_endpoint()
    dns = dns or storage.get_server_dns() or "1.1.1.1"
    port = int(endpoint.split(":")[-1])
    server_local_ip=utili.get_local_ip()

    conf = "[Interface]\n"
    conf += f"PrivateKey = {private_key}\n"
    conf += f"Address = {address}\n"
    conf += f"DNS = {dns}\n\n"
    conf += "[Peer]\n"
    conf += f"PublicKey = {server_pubkey}\n"
    if psk:
        conf += f"PresharedKey = {psk}\n"
    conf += f"Endpoint = {server_local_ip}:{port}\n"
    conf += f"AllowedIPs = {allowed_ips}\n"
    conf += "PersistentKeepalive = 25\n"
    return conf

def write_client_conf(username: str, conf_text: str, output_dir: Optional[str] = None) -> Path:
    """Write client config file to chosen folder or default ./config folder"""
    if output_dir is None:
        output_dir = "./config"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    file_path = Path(output_dir) / f"{username}.conf"
    with open(file_path, "w") as f:
        f.write(conf_text)
    return file_path

WG_DIR = "/etc/wireguard/"

def activate_peer_permanent(peer_publickey: str, peer_ip: str, server_name: str) -> bool:
    """
    Permanently add a peer to a WireGuard server by writing directly to the server config file
    and reloading the interface.

    Args:
        peer_publickey (str): Peer public key.
        peer_ip (str): Allowed IPs for the peer (e.g., 10.13.13.2/32).
        server_conf_path (str): Path to server config file (e.g., /etc/wireguard/wg0.conf).
        interface (str): WireGuard interface name (default: wg0).

    Returns:
        bool: True if successful, False otherwise.
    """
    filename = f"{server_name}.conf"
    full_path = Path(WG_DIR) / filename
    server_conf = Path(full_path)

    if not server_conf.exists():
        print(f"❌ Server config file not found: {server_conf}")
        return False

    try:
        # Build peer block
        peer_block = f"""
[Peer]
PublicKey = {peer_publickey}
AllowedIPs = {peer_ip}
"""

        # Append peer config to server config file
        with open(server_conf, "a") as sc:
            sc.write("\n")
            sc.write(peer_block)

        # Restart WireGuard interface so changes take effect
        subprocess.run(["wg-quick", "down", server_name], check=True)
        subprocess.run(["wg-quick", "up", server_name], check=True)

        print(f"✅ Peer with key {peer_publickey[:10]}... added successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error restarting interface: {e}")
        return False
    except Exception as e:
        print(f"❌ Error adding peer: {e}")
        return False



def interactive_client_config():
    """Interactively generate a WireGuard client config"""
    # List available servers
    servers = storage.list_servers()
    if not servers:
        click.echo("❌ No servers available. Please create a server first.")
        return

    click.echo("Available servers:")
    for idx, srv in enumerate(servers, 1):
        click.echo(f"  [{idx}] {srv['name']} ({srv['subnet']})")

    # Ask for server index
    server_idx = click.prompt("Enter the index of the server to connect", type=int, default=1)
    if server_idx < 1 or server_idx > len(servers):
        click.echo("❌ Invalid index.")
        return
    server = servers[server_idx - 1]

    # Ask for username
    username = click.prompt("Enter username for the client")

    # Ask if user wants a specific IP
    use_specific_ip = click.confirm(f"Do you want to assign a specific IP in {server['subnet']}?", default=False)
    if use_specific_ip:
        ip = click.prompt("Enter the IP address to assign", type=str)
    else:
        # Allocate first free IP in subnet
        ip = storage.get_first_free_ip(server['subnet'])
        if not ip:
            click.echo("❌ No free IPs available in this subnet.")
            return
        click.echo(f"Assigned first free IP: {ip}")

    # Ask for path to save config
    use_custom_path = click.confirm("Do you want to save the config in a custom path?", default=False)
    if use_custom_path:
        output_dir = click.prompt("Enter the full path to save the config", type=str)
    else:
        output_dir = "./config"

    # Optional preshared key
    use_psk = click.confirm("Do you want to use a PresharedKey?", default=False)
    psk = storage.generate_psk() if use_psk else None

    # Optional allowed IPs
    allowed_ips = click.prompt("Allowed IPs (default 0.0.0.0/0, ::/0)", default="0.0.0.0/0, ::/0")

    # Generate private key
    private_key = storage.generate_private_key()

    # Generate config
    conf_text = gen_client_conf(private_key, ip, allowed_ips, psk)
    file_path = write_client_conf(username, conf_text, output_dir)
    click.echo(f"✅ Client config generated at {file_path}")

    # Optionally register user
    if click.confirm("Register this client in database?", default=True):
        storage.add_user(username=username, server=server['name'], ip=ip, pubkey=private_key)
        click.echo(f"✅ User '{username}' registered.")

