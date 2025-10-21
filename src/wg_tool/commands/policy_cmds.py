import click
from wg_tool.policy.manager import PolicyManager, UserPolicy

pm = PolicyManager()

@click.group()
def policy():
    """Policy management commands"""
    pass

@policy.command("add")
@click.option("--role", required=True, help="Role to assign the policy to")
@click.option("--text", required=True, help="Policy text or rules")
def add(role, text):
    """Add a new policy"""
    policy_obj = UserPolicy(role=role, policy_text=text)
    pm.add_policy(policy_obj)
    click.echo(f"✅ Policy added for role '{role}'.")

@policy.command("list")
def list_policies():
    """List all policies"""
    policies = pm.list_policies()
    if not policies:
        click.echo("No policies found.")
        return
    for p in policies:
        click.echo(f"- ID={p['id']} | Role={p['role']} | {p['policy_text']} (at {p['created_at']})")

@policy.command("delete")
@click.argument("role")
def delete(role):
    """Delete policies for a role"""
    pm.delete_policy(role)
    click.echo(f"🗑️  Policies for role '{role}' deleted.")
