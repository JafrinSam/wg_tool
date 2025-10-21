# wg_tool/policy/model.py
from typing import Optional
import datetime

class Role:
    def __init__(self, name: str, allowed_ips: Optional[list[str]] = None, notes: str = ""):
        self.name = name
        self.allowed_ips = allowed_ips or []
        self.notes = notes
        self.created_at = datetime.datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "name": self.name,
            "allowed_ips": self.allowed_ips,
            "notes": self.notes,
            "created_at": self.created_at
        }


class UserPolicy:
    def __init__(self, role: str, policy_text: str, state: str = "INACTIVE",
                 subnets=None, allowed_ports=None, created_at=None):
        self.role = role
        self.policy_text = policy_text
        self.state = state
        self.subnets = subnets or []          # List of allowed subnets
        self.allowed_ports = allowed_ports or []  # List of allowed ports
        self.created_at = created_at or datetime.datetime.utcnow().isoformat()
        self.id = None

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "policy_text": self.policy_text,
            "state": self.state,
            "subnets": self.subnets,
            "allowed_ports": self.allowed_ports,
            "created_at": self.created_at
        }