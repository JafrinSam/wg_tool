import click
from wg_tool.policy.base import get_conn
import datetime

@click.group()
def role():
    """Role management commands"""
    pass

@role.command("add")
@click.option("--name", required=True, help="Name of the role to add")
def add_role(name):
    """Add a new role"""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO roles (name, created_at) VALUES (?, ?)",
            (name, datetime.datetime.utcnow().isoformat())
        )
        conn.commit()
        click.echo(f"✅ Role '{name}' added successfully.")
    except Exception as e:
        click.echo(f"❌ Failed to add role: {e}")
    finally:
        conn.close()

@role.command("list")
def list_roles():
    """List all roles"""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT name, created_at FROM roles").fetchall()
        for r in rows:
            click.echo(f"- {r['name']} (created at {r['created_at']})")
    finally:
        conn.close()

@role.command("delete")
@click.argument("name")
def delete_role(name):
    """Delete a role"""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM roles WHERE name=?", (name,))
        conn.commit()
        click.echo(f"🗑️  Role '{name}' deleted.")
    finally:
        conn.close()
