# wg_tool/commands/user_cmds.py
import click
from pathlib import Path
from wg_tool import storage, keys, config_gen, peer_manager

@click.group()
def user():
    """User management commands (fully interactive)"""
    pass


# ----------------------------
# Interactive add user
# ----------------------------
@user.command("add")
def add_user():
    """
    Add a new VPN user interactively.
    Checks if the user exists; if not, creates and registers the user.
    """
    # Step 1: Username
    username = click.prompt("Enter username for the VPN user")

    # Step 2: Check if user exists
    existing_user = storage.get_user(username)
    if existing_user:
        click.echo(f"✅ User '{username}' already exists.")
        click.echo(f"Username: {existing_user['username']}")
        click.echo(f"IP: {existing_user['ip']}")
        click.echo(f"Server: {existing_user['server']}")
        return

    # Step 3: Select server
    servers = storage.list_servers()
    if not servers:
        click.echo("❌ No servers available. Please create a server first.")
        return

    click.echo("Available servers:")
    for idx, srv in enumerate(servers, 1):
        click.echo(f"  [{idx}] {srv['name']} ({srv.get('subnet','')})")

    server_idx = click.prompt("Select server index", type=int, default=1)
    if server_idx < 1 or server_idx > len(servers):
        click.echo("❌ Invalid server index.")
        return
    server = servers[server_idx - 1]

    # Step 4: Assign IP
    use_custom_ip = click.confirm(f"Do you want to assign a specific IP in {server.get('subnet','')}?", default=False)
    if use_custom_ip:
        ip = click.prompt("Enter IP address to assign", type=str)
    else:
        ip = storage.get_first_free_ip(server.get('subnet',''))
        if not ip:
            click.echo("❌ No free IPs available.")
            return
        click.echo(f"Assigned IP: {ip}")

    # Step 5: Role
    role = click.prompt("Enter role for the user (client/admin/etc.)", default="client")

    # Step 6: Generate keys
    private_key = keys.gen_private_key()
    public_key = keys.pubkey_from_private(private_key)

    # Step 7: Optional PresharedKey
    use_psk = click.confirm("Do you want to use a PresharedKey?", default=False)
    psk = keys.gen_preshared_key() if use_psk else None

    # Step 8: Allowed IPs
    allowed_ips = click.prompt("Allowed IPs (default 0.0.0.0/0, ::/0)", default="0.0.0.0/0, ::/0")

    # Step 9: Generate client config
    conf_text = config_gen.gen_client_conf(
        private_key=private_key,
        server_pubkey=server.get("public_key",""),
        endpoint=server.get("endpoint",""),
        address=ip,
        allowed_ips=allowed_ips,
        dns=server.get("dns","1.1.1.1"),
        psk=psk
    )

    # Step 10: Save config
    use_custom_path = click.confirm("Do you want to save config in a custom path?", default=False)
    output_dir = click.prompt("Enter full path", type=str) if use_custom_path else "./config"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    conf_path = Path(output_dir) / f"{username}.conf"
    with open(conf_path, "w") as f:
        f.write(conf_text)
    click.echo(f"✅ Config saved at {conf_path}")

    # Step 11: Register user in DB
    storage.add_user(username=username, pubkey=public_key, privkey=private_key,role=role, ip=ip, server=server['name'])
    click.echo(f"✅ User '{username}' registered in DB.")

    click.echo(f"user config: {conf_text}")

    # Step 12: Optional peer activation
    if click.confirm("Do you want to activate the peer immediately?", default=False):
        config_gen.activate_peer_permanent(public_key,ip,server.get("name",""))

# ----------------------------
# Interactive generate config (alias for add)
# ----------------------------
@user.command("gen-config")
def gen_config():
    """
    Alias for 'add': fully interactive user creation with config.
    """
    add_user()
