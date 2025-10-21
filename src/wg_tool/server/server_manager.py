# wg_tool/server/server_manager.py

import subprocess
from pathlib import Path
from wg_tool import keys, storage, utili

WG_DIR = "/etc/wireguard/"
BASE_PORT = 51820  # starting port for WireGuard servers


class ServerError(Exception):
    """Base class for server-related errors."""
    pass


class ConfigError(ServerError):
    """Raised when configuration generation or saving fails."""
    pass


class InterfaceError(ServerError):
    """Raised when enabling or starting WireGuard interface fails."""
    pass


class DuplicateSubnetError(ServerError):
    """Raised when a server with the same subnet already exists."""
    pass


class DuplicateNameError(ServerError):
    """Raised when a server with the same name already exists."""
    pass


def _get_next_available_port():
    """
    Finds the next free WireGuard port starting from BASE_PORT.
    If no servers exist, returns BASE_PORT.
    """
    try:
        servers = storage.get_all_servers()
        if not servers:  # no servers yet
            return BASE_PORT

        used_ports = []
        for s in servers:
            endpoint = s.get("endpoint")  # endpoint = "IP:PORT"
            if endpoint and ":" in endpoint:
                try:
                    port = int(endpoint.split(":")[-1])
                    used_ports.append(port)
                except ValueError:
                    continue

        port = BASE_PORT
        while port in used_ports:
            port += 1
        return port
    except Exception as e:
        raise ServerError(f"Failed to fetch used ports: {e}")



class ServerConfig:
    def __init__(self, name: str, subnet: str, dns: str = None, port: int = None):
        self.name = name
        self.subnet = subnet  # e.g., "10.13.13.1/24"
        self.dns = dns
        self.private_key = ""
        self.public_key = ""
        self.port = port or _get_next_available_port()

    def generate_keys(self):
        try:
            self.private_key = keys.gen_private_key()
            self.public_key = keys.pubkey_from_private(self.private_key)
        except Exception as e:
            raise ConfigError(f"Key generation failed: {e}")

    def generate_config_text(self):
        if not self.private_key:
            raise ConfigError("Private key not generated yet.")

        config = "[Interface]\n"
        config += f"Address = {self.subnet}\n"
        config += f"PrivateKey = {self.private_key}\n"
        config += f"ListenPort = {self.port}\n"
        if self.dns:
            config += f"DNS = {self.dns}\n"
        return config

    def save_config_file(self):
        try:
            Path(WG_DIR).mkdir(parents=True, exist_ok=True)
            filename = f"{self.name}.conf"
            full_path = Path(WG_DIR) / filename
            if full_path.exists():
                raise DuplicateNameError(f"Config file {filename} already exists in {WG_DIR}")

            with open(full_path, "w") as f:
                f.write(self.generate_config_text())
            full_path.chmod(0o600)  # restrict permissions
            return full_path
        except DuplicateNameError:
            raise
        except Exception as e:
            raise ConfigError(f"Failed to save config file: {e}")

    def enable_interface(self):
        try:
            # Bring down existing interface if it exists
            subprocess.run(["sudo", "wg-quick", "down", self.name], check=False)

            # Enable & start
            subprocess.run(
                ["sudo", "systemctl", "enable", f"wg-quick@{self.name}"],
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                ["sudo", "systemctl", "start", f"wg-quick@{self.name}"],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Interface {self.name} enabled and started on port {self.port}.")
        except subprocess.CalledProcessError as e:
            raise InterfaceError(
                f"Failed to enable/start interface {self.name} "
                f"(exit {e.returncode}): {e.stderr or e.stdout}"
            )


def create_server(name: str, subnet: str, dns: str = None):
    """
    Creates a WireGuard server config:
    - Validates no duplicate subnet or name
    - Generates server keys
    - Writes config to /etc/wireguard/<name>.conf
    - Stores server info in SQLite
    - Enables and starts the interface
    """
    try:
        # 🔍 Check for duplicate subnet or name in DB before creating
        existing_servers = storage.get_all_servers()
        for s in existing_servers:
            if s.get("subnet") == subnet:
                raise DuplicateSubnetError(
                    f"A server with subnet {subnet} already exists (name={s.get('name')})."
                )
            if s.get("name") == name:
                raise DuplicateNameError(
                    f"A server with name '{name}' already exists (subnet={s.get('subnet')})."
                )

        server = ServerConfig(name, subnet, dns)
        server.generate_keys()
        path = server.save_config_file()

        # Save in SQLite servers table
        storage.add_server(
            name=name,
            subnet=subnet,
            private_key=server.private_key,
            public_key=server.public_key,
            endpoint=f"{subnet.split('/')[0]}:{server.port}",
            dns=dns or "1.1.1.1"
        )

        server.enable_interface()
        return server

    except (ConfigError, InterfaceError, DuplicateSubnetError, DuplicateNameError, ServerError) as e:
        print(f"❌ Error: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise


def remove_server(name: str):
    """
    Safely removes a WireGuard server:
    - Stops and disables the interface
    - Removes config file
    - Deletes from SQLite
    """
    server = storage.get_server_by_name(name)
    if not server:
        raise ServerError(f"Server '{name}' does not exist.")

    conf_path = Path(WG_DIR) / f"{name}.conf"
    try:
        # Stop and disable
        subprocess.run(["sudo", "systemctl", "stop", f"wg-quick@{name}"], check=False)
        subprocess.run(["sudo", "systemctl", "disable", f"wg-quick@{name}"], check=False)

        # Remove config file
        if conf_path.exists():
            conf_path.unlink()
        # Remove from DB
        storage.remove_server(name)
        print(f"✅ Server '{name}' removed successfully.")
    except Exception as e:
        raise ServerError(f"Failed to remove server '{name}': {e}")

