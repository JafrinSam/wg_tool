import click
from wg_tool.commands import server_cmds, user_cmds, interfaces_cmds, policy_cmds, firewall_cli
from wg_tool.logger import setup_logging
from wg_tool.commands import role_cmds
# setup_logging()  # enable later if needed

@click.group()
def cli():
    """wgtool — WireGuard RBAC management CLI"""
    pass

# Register groups
cli.add_command(server_cmds.server)
cli.add_command(user_cmds.user)
cli.add_command(interfaces_cmds.iface)
cli.add_command(policy_cmds.policy)
cli.add_command(firewall_cli.firewall)
cli.add_command(role_cmds.role)

@cli.command("manual")
def manual():
    """Show all commands with descriptions"""
    ctx = click.get_current_context()
    click.echo("WireGuard RBAC Tool - Manual\n")
    for command in cli.list_commands(ctx=ctx):
        cmd_obj = cli.get_command(ctx, command)
        if isinstance(cmd_obj, click.Group):
            click.echo(f"\n{command} commands:")
            for sub in cmd_obj.list_commands(ctx=ctx):
                sub_obj = cmd_obj.get_command(ctx, sub)
                desc = sub_obj.help or "No description"
                click.echo(f"  {sub}: {desc}")
        else:
            desc = cmd_obj.help or "No description"
            click.echo(f"{command}: {desc}")

if __name__ == "__main__":
    cli()
