import click
from wg_tool.policy.manager import PolicyManager
from wg_tool.policy.firewall import FirewallManager

policy_mgr = PolicyManager()
fw_mgr = FirewallManager()

@click.group()
def firewall():
    """Manage firewall enforcement of user policies"""
    pass

@firewall.command("apply")
@click.argument("policy_name")
def apply_firewall(policy_name):
    """Apply firewall rules for a specific policy"""
    try:
        policy = policy_mgr.get_policy(policy_name)
        fw_mgr.apply_policy(policy)
        click.echo(f"✅ Firewall rules applied for policy '{policy_name}'")
    except Exception as e:
        click.echo(f"❌ Failed: {e}")

@firewall.command("remove")
@click.argument("policy_name")
def remove_firewall(policy_name):
    """Remove firewall rules for a specific policy"""
    try:
        policy = policy_mgr.get_policy(policy_name)
        fw_mgr.remove_policy(policy)
        click.echo(f"✅ Firewall rules removed for policy '{policy_name}'")
    except Exception as e:
        click.echo(f"❌ Failed: {e}")
