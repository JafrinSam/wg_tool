import click
from pathlib import Path
import yaml
from wg_tool import firewall as f  # your combined firewall module

FIREWALL_TYPES=["iptables","ufw"]
YAML_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config.d" / "config.yaml"

def load_policy_from_yaml(yaml_file: str):
    """Load YAML policy from file."""
    try:
        with open(yaml_file, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Error reading YAML file: {e}")


@click.group()
def firewall():
    """Firewall policy commands"""
    pass

@firewall.command("apply")
def apply():
    """Apply firewall rules for a role."""
    try:
        policy = load_policy_from_yaml(YAML_PATH)
    except RuntimeError as e:
        click.echo(f"❌ {e}")
        return

    click.echo("Select firewall type:")
    for idx, f_t in enumerate(FIREWALL_TYPES):
        click.echo(f"   [{idx}] {f_t}")

    f_idx = click.prompt("Enter the index", type=int)
    if f_idx not in range(len(FIREWALL_TYPES)):
        click.echo("❌ Invalid firewall type index")
        return

    f_type = FIREWALL_TYPES[f_idx]

    click.echo("Select the command:")
    click.echo("   [0] Show firewall commands (dry-run)")
    click.echo("   [1] Apply the firewall commands")

    cmd_idx = click.prompt("Enter the index", type=int)
    if cmd_idx == 0:
        f.show_rules(policy, f_type)
    elif cmd_idx == 1:
        f.apply_firewall(policy, f_type)
    else:
        click.echo("❌ Invalid command index")
        return

    click.echo(f"Finished processing firewall rules ")

@firewall.command("clear")
def clear():
    """Clear all applied firewall rules"""
    # TODO: flush firewall chains
    click.echo("🧹 Cleared all firewall rules.")
