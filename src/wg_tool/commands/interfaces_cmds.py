# wg_tool/commands/interface_cmds.py
import click
from wg_tool.server.interface_service import (
    start_interface,
    stop_interface,
    restart_interface,
    remove_interface,
)

@click.group()
def iface():
    """Interface management (start/stop/restart/remove)"""
    pass

@iface.command("start")
@click.argument("name")
@click.option("--enable/--no-enable", default=True, help="Enable the interface at boot")
def start(name, enable):
    """Start a WireGuard interface"""
    ok, msg = start_interface(name, enable=enable)
    if not ok:
        raise click.ClickException(msg)
    click.echo(msg)

@iface.command("stop")
@click.argument("name")
@click.option("--disable/--no-disable", default=False, help="Disable the interface at boot")
def stop(name, disable):
    """Stop a WireGuard interface"""
    ok, msg = stop_interface(name, disable=disable)
    if not ok:
        raise click.ClickException(msg)
    click.echo(msg)

@iface.command("restart")
@click.argument("name")
def restart(name):
    """Restart a WireGuard interface"""
    ok, msg = restart_interface(name)
    if not ok:
        raise click.ClickException(msg)
    click.echo(msg)

@iface.command("remove")
@click.argument("name")
@click.option("--remove-config/--no-remove-config", default=True, help="Remove the config file from /etc/wireguard")
@click.option("--clear-storage/--no-clear-storage", default=False, help="Remove server info from SQLite storage")
def remove(name, remove_config, clear_storage):
    """Remove a WireGuard interface"""
    ok, msg = remove_interface(name, remove_config=remove_config, clear_storage=clear_storage)
    if not ok:
        raise click.ClickException(msg)
    click.echo(msg)
