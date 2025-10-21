# wg_tool/hooks.py
from wg_tool import storage
from wg_tool.policy.parser import parse_policy_file
from wg_tool.policy.compiler import compile_role_rules_for_user
from wg_tool import nftables

def on_peer_connect(pubkey: str):
    """Hook for WireGuard PostUp when peer connects"""
    user = storage.get_user_by_pubkey(pubkey)
    if not user:
        print(f"No user found for pubkey {pubkey}")
        return
    role = user["role"]
    ip = user["ip"]
    # Load latest policy for role
    policy_text = storage.get_latest_policy_for_role(role)
    if not policy_text:
        print(f"No policy found for role {role}")
        return
    # parse policy
    tmp_file = "/tmp/tmp_policy.txt"
    with open(tmp_file, "w") as f:
        f.write(policy_text)
    rules = parse_policy_file(tmp_file)
    # compile nftables commands
    cmds = compile_role_rules_for_user(role, rules, ip)
    # apply
    nftables.apply_commands(cmds)
    print(f"Applied policies for user {user['username']} ({ip})")

def on_peer_disconnect(pubkey: str):
    """Hook for WireGuard PostDown"""
    # optional: remove user-specific rules
    pass
