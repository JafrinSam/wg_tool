import subprocess
from .model import UserPolicy

class FirewallManager:
    """Manage firewall rules per policy using iptables."""

    def __init__(self):
        self.backend = "iptables"  # Future: nftables support

    def _run_cmd(self, cmd):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[FIREWALL] Ran: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            print(f"[FIREWALL ERROR] {e.stderr.decode().strip()}")

    def apply_policy(self, policy: UserPolicy):
        """Apply firewall rules for a given policy."""
        for subnet in policy.subnets:
            for port in policy.allowed_ports:
                # Allow traffic for allowed subnets & ports
                self._run_cmd([
                    "sudo", "iptables", "-A", "FORWARD",
                    "-s", subnet, "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"
                ])
                self._run_cmd([
                    "sudo", "iptables", "-A", "FORWARD",
                    "-s", subnet, "-p", "udp", "--dport", str(port), "-j", "ACCEPT"
                ])
            # Deny everything else for that subnet
            self._run_cmd([
                "sudo", "iptables", "-A", "FORWARD",
                "-s", subnet, "-j", "DROP"
            ])

    def remove_policy(self, policy: UserPolicy):
        """Remove firewall rules for a given policy."""
        for subnet in policy.subnets:
            for port in policy.allowed_ports:
                self._run_cmd([
                    "sudo", "iptables", "-D", "FORWARD",
                    "-s", subnet, "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"
                ])
                self._run_cmd([
                    "sudo", "iptables", "-D", "FORWARD",
                    "-s", subnet, "-p", "udp", "--dport", str(port), "-j", "ACCEPT"
                ])
            self._run_cmd([
                "sudo", "iptables", "-D", "FORWARD",
                "-s", subnet, "-j", "DROP"
            ])
