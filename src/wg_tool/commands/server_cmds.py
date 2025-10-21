import click
from wg_tool.server.server_manager import create_server
from wg_tool.server.server_selector import select_server
from wg_tool.server.server_editor import edit_server_interactive, ServerEditError, ServerNotFoundError
from wg_tool.server.server_delete import delete_server_interactive


@click.group()
def server():
    """Server management commands (interactive)"""
    pass


@server.command("create")
@click.option("--name", help="Name of the server/interface")
@click.option("--subnet", help="Server subnet, e.g., 10.13.13.1/24")
@click.option("--dns", help="Optional DNS (default: 1.1.1.1)")
def create(name, subnet, dns):
    """Create a server config and start interface (interactive)"""

    # Ask interactively if options not provided
    if not name:
        name = click.prompt("Enter a server name", type=str)

    if not subnet:
        subnet = click.prompt("Enter a subnet (CIDR format, e.g., 10.13.13.1/24)", type=str)

    if not dns:
        dns_input = click.prompt(
            "Enter DNS server", 
            default="1.1.1.1", 
            show_default=True,
            type=str,
            prompt_suffix=" (leave blank for default 1.1.1.1): "
        )
        dns = dns_input.strip() or "1.1.1.1"

    try:
        server_obj = create_server(name, subnet, dns)
        click.echo(f"\n✅ Server '{name}' created.")
        click.echo(f"📂 Config written to /etc/wireguard/{name}.conf")
        click.echo(f"🔑 Public Key: {server_obj.public_key}")
        click.echo(f"🌐 DNS: {dns}")
    except Exception as e:
        click.echo(f"❌ Failed to create server: {e}")


@server.command("edit")
def edit():
    """Edit an existing WireGuard server interactively"""
    try:
        server = select_server()  # Lists all servers and prompts user
    except ServerNotFoundError as e:
        click.echo(f"❌ {e}")
        return

    try:
        edit_server_interactive(server)
        click.echo(f"✅ Server '{server['name']}' updated successfully.")
    except ServerEditError as e:
        click.echo(f"❌ Edit failed: {e}")
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")


@server.command("delete")
def delete():
    """Interactively delete a WireGuard server"""
    try:
        delete_server_interactive()
        click.echo("✅ Server deleted successfully.")
    except Exception as e:
        click.echo(f"❌ Delete failed: {e}")
