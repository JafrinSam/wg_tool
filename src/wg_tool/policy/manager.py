# wg_tool/policy/manager.py
from .base import get_conn, init_db
from .model import UserPolicy
import datetime
import subprocess
import click

init_db()  # ensure DB exists

class PolicyManager:
    def add_policy(self, policy: UserPolicy):
        """Add a new policy and optionally set firewall info."""
        conn = get_conn()
        try:
            # 1️⃣ Check if role exists
            row = conn.execute("SELECT name FROM roles WHERE name=?", (policy.role,)).fetchone()
            if not row:
                create = input(f"❌ Role '{policy.role}' does not exist. Create it now? [y/N]: ").strip().lower()
                if create == 'y':
                    subprocess.run(["wgtool", "role", "add", "--name", policy.role], check=True)
                    print(f"✅ Role '{policy.role}' created.")
                else:
                    print("⚠️ Cannot add policy without a valid role. Aborting.")
                    return

            # 2️⃣ Ask for firewall info if not provided
            if not policy.subnets:
                subnets_input = input("Enter allowed subnets (comma separated, e.g., 10.13.13.0/24): ").strip()
                policy.subnets = [s.strip() for s in subnets_input.split(",") if s.strip()]

            if not policy.allowed_ports:
                ports_input = input("Enter allowed ports (comma separated, e.g., 22,80,443): ").strip()
                policy.allowed_ports = [int(p.strip()) for p in ports_input.split(",") if p.strip()]

            # 3️⃣ Insert into DB
            conn.execute(
                """INSERT INTO policies (role, policy_text, state, subnets, allowed_ports, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (policy.role, policy.policy_text, policy.state,
                 ",".join(policy.subnets), ",".join(map(str, policy.allowed_ports)), policy.created_at)
            )
            conn.commit()
            print(f"✅ Policy added for role '{policy.role}' with subnets {policy.subnets} and ports {policy.allowed_ports}.")
        finally:
            conn.close()

    def list_policies(self):
        conn = get_conn()
        try:
            rows = conn.execute("SELECT * FROM policies").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_policy(self, role_name: str):
        conn = get_conn()
        try:
            row = conn.execute("SELECT * FROM policies WHERE role=?", (role_name,)).fetchone()
            if row:
                subnets = row["subnets"].split(",") if row["subnets"] else []
                ports = [int(p) for p in row["allowed_ports"].split(",")] if row["allowed_ports"] else []
                policy = UserPolicy(row["role"], row["policy_text"], row["state"],
                                    subnets=subnets, allowed_ports=ports, created_at=row["created_at"])
                policy.id = row["id"]
                return policy
            return None
        finally:
            conn.close()

    def delete_policy(self, role_name: str):
        conn = get_conn()
        try:
            conn.execute("DELETE FROM policies WHERE role=?", (role_name,))
            conn.commit()
            print(f"🗑️  Deleted all policies for role '{role_name}'.")
        finally:
            conn.close()
