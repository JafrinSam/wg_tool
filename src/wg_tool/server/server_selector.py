# wg_tool/server/server_selector.py

from wg_tool import storage
from wg_tool.server.server_editor import ServerNotFoundError

def list_servers() -> list:
    """List all servers with index and name."""
    servers = storage.get_all_servers()
    if not servers:
        print("No servers found.")
        return []
    print("Available servers:")
    for idx, s in enumerate(servers):
        print(f"[{idx}] {s['name']} (subnet: {s['subnet']}, DNS: {s.get('dns', '')})")
    return servers

def select_server() -> dict:
    """Prompt user to select a server by index."""
    servers = list_servers()
    if not servers:
        raise ServerNotFoundError("No servers available to edit.")
    
    while True:
        try:
            index = int(input("Enter the index of the server to edit: "))
            if 0 <= index < len(servers):
                return servers[index]
            print("Invalid index. Try again.")
        except ValueError:
            print("Please enter a valid number.")
