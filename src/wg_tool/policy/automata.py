# wg_tool/policy/automata.py
from .base import get_conn
from .manager import PolicyManager
from wg_tool.policy.firewall import FirewallManager

class AutomataManager:
    def __init__(self):
        self.firewall = FirewallManager()
        self.policy_mgr = PolicyManager()

    def add_transition(self, policy_name: str, from_state: str, event: str, to_state: str):
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO automata_transitions (policy_name, from_state, event, to_state) VALUES (?, ?, ?, ?)",
                (policy_name, from_state, event, to_state)
            )
            conn.commit()
        finally:
            conn.close()

    def get_transitions(self, policy_name: str):
        conn = get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM automata_transitions WHERE policy_name=?", (policy_name,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def trigger_event(self, policy_name: str, event: str):
        policy = self.policy_mgr.get_policy(policy_name)
        if not policy:
            raise ValueError(f"No policy found: {policy_name}")

        # Build transition table
        transitions = {}
        for t in self.get_transitions(policy_name):
            transitions.setdefault(t["from_state"], {})[t["event"]] = t["to_state"]

        if event in transitions.get(policy.state, {}):
            old_state = policy.state
            policy.state = transitions[policy.state][event]
            self.policy_mgr.add_policy(policy)  # persist new state

            # Firewall integration
            if policy.state == "ACTIVE":
                self.firewall.apply_policy(policy)
            elif policy.state == "INACTIVE":
                self.firewall.remove_policy(policy)

            return old_state, policy.state
        else:
            raise ValueError(f"No transition from {policy.state} on {event}")
