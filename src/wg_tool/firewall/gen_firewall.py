import subprocess
import sys
import yaml
from typing import List, Dict, Any
from wg_tool import storage

def cidr_of(subnets: Dict[str, Dict], name: str) -> str:
    """Get CIDR notation for a subnet by name."""
    return subnets[name]['cidr']

def proto_part(rule: Dict[str, Any], backend: str) -> str:
    """Generate protocol and port part of the rule depending on backend."""
    if backend == "iptables":
        parts = []
        if 'proto' in rule:
            parts.append(f"-p {rule['proto']}")
        if 'dst_ports' in rule:
            ports = ",".join(str(p) for p in rule['dst_ports'])
            parts.append(f"--dport {ports}")
        return " ".join(parts)
    elif backend == "ufw":
        parts = []
        if 'proto' in rule:
            parts.append(f"proto {rule['proto']}")
        if 'dst_ports' in rule:
            ports = ",".join(str(p) for p in rule['dst_ports'])
            parts.append(f"port {ports}")
        return " ".join(parts)
    return ""

def render_rule(src_cidr: str, dst_cidr: str, proto_str: str, action: str, comment: str, backend: str, chain: str = "VPN_SUBNETS") -> str:
    """Render a complete rule for iptables or ufw."""
    if backend == "iptables":
        iptables_action = "ACCEPT" if action.lower() == "allow" else action.upper()
        comment_str = f'-m comment --comment "{comment}"' if comment else ""
        cmd = f"iptables -A {chain} -s {src_cidr} -d {dst_cidr} {proto_str} {comment_str} -j {iptables_action}"
        return " ".join(cmd.split())
    elif backend == "ufw":
        ufw_action = "allow" if action.lower() == "allow" else "deny"
        comment_str = f' comment "{comment}"' if comment else ""
        cmd = f"ufw {ufw_action} from {src_cidr} to {dst_cidr} {proto_str}{comment_str}"
        return " ".join(cmd.split())
    else:
        raise ValueError(f"Unsupported backend: {backend}")

def emit_rules(policy: Dict[str, Any], backend: str) -> List[str]:
    """Generate commands based on the backend."""
    subnets = policy['subnets']
    rules = policy.get('rules', [])
    cmds = []

    if backend == "iptables":
        chain = policy.get('chain', 'FORWARD')
        cmds.append("iptables -N VPN_SUBNETS 2>/dev/null || true")
        cmds.append("iptables -F VPN_SUBNETS 2>/dev/null || true")
        cmds.append(f"iptables -I {chain} -j VPN_SUBNETS 2>/dev/null || true")

    created_rules = set()

    # Generate explicit rules
    for r in rules:
        src = r['from']
        dst = r['to']
        action = r.get('action', 'deny')
        proto_str = proto_part(r, backend)

        dst_targets = subnets.keys() if dst == "any" else [dst]

        for dst_name in dst_targets:
            if src == dst_name and dst != src:
                continue  # skip self unless explicitly allowed
            src_cidr = cidr_of(subnets, src)
            dst_cidr = cidr_of(subnets, dst_name)
            key = f"{src_cidr}->{dst_cidr}:{proto_str}"
            if key in created_rules:
                continue
            comment = f"{src} -> {dst_name}"
            cmds.append(render_rule(src_cidr, dst_cidr, proto_str, action, comment, backend))
            created_rules.add(key)

    # Default deny rules
    for src_name, src_meta in subnets.items():
        src_cidr = src_meta['cidr']
        for dst_name, dst_meta in subnets.items():
            if src_name == dst_name:
                continue
            dst_cidr = dst_meta['cidr']
            key = f"{src_cidr}->{dst_cidr}:"
            if key not in created_rules:
                comment = f"default-deny {src_name} -> {dst_name}"
                cmds.append(render_rule(src_cidr, dst_cidr, "", "deny", comment, backend))

    return cmds

def apply_firewall(policy: Dict[str, Any], backend: str) -> List[str]:
    """Apply firewall rules using the selected backend."""
    cmds = emit_rules(policy, backend)
    successful_cmds = []

    print(f"🔧 Applying firewall rules using {backend}...")
    for cmd in cmds:
        print(f"⚡ Executing: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr.strip()}")
        else:
            successful_cmds.append(cmd)
            storage.store_rule(backend, cmd)


    print(f"✅ {backend} rules applied successfully! ({len(successful_cmds)} rules)")
    return successful_cmds

def show_rules(policy: Dict[str, Any], backend: str) -> List[str]:
    """Dry run: Show rules without applying them."""
    cmds = emit_rules(policy, backend)
    print(f"📋 Generated commands for {backend} (dry run):")
    for cmd in cmds:
        print(f"  {cmd}")
    print(f"\nTotal: {len(cmds)} rules generated")
    return cmds

def load_policy_from_yaml(yaml_file: str) -> Dict[str, Any]:
    """Load policy from YAML file."""
    try:
        import yaml
        with open(yaml_file, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        print("❌ PyYAML not installed. Install with: pip install PyYAML")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ File not found: {yaml_file}")
 
        sys.exit(1)












""" 
if __name__ == "__main__":
    # Default example policy
    policy = {
        'subnets': {
            'student': {'cidr': '10.10.0.0/24'},
            'faculty': {'cidr': '10.20.0.0/24'},
            'admin': {'cidr': '10.30.0.0/24'},
            'mgmt': {'cidr': '10.40.0.0/24'}
        },
        'rules': [
            {'from': 'admin', 'to': 'any', 'action': 'allow'},
            {'from': 'faculty', 'to': 'faculty', 'action': 'allow'},
            {'from': 'faculty', 'to': 'mgmt', 'action': 'allow'},
            {'from': 'faculty', 'to': 'student', 'proto': 'tcp', 'dst_ports': [80], 'action': 'allow'},
            {'from': 'student', 'to': 'student', 'action': 'allow'},
            {'from': 'student', 'to': 'mgmt', 'action': 'allow'}
        ]
    }

    backend = "iptables"  # default
    yaml_file = None
    dry_run = False

    # Parse command-line arguments
    args = sys.argv[1:]
    for arg in args:
        if arg in ["--dry-run", "-d"]:
            dry_run = True
        elif arg.startswith("--backend="):
            backend = arg.split("=", 1)[1]
        elif arg.endswith(".yaml") or arg.endswith(".yml"):
            yaml_file = arg

    if yaml_file:
        policy = load_policy_from_yaml(yaml_file)

    if dry_run:
        show_rules(policy, backend)
    else:
        apply_firewall(policy, backend)
 """