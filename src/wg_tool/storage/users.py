from .base import get_conn, init_db
from typing import List, Dict,Optional
import datetime

def list_servers() -> List[Dict[str, str]]:
    """Return a list of servers (roles with allowed IPs)"""
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM roles").fetchall()
        servers = []
        for row in rows:
            servers.append({
                "name": row["name"],
                "subnet": row["allowed_ips"] or "",
                "notes": row["notes"] or ""
            })
        return servers
    finally:
        conn.close()


def get_first_free_ip(subnet: str) -> str:
    """Return the first free IP in a given subnet"""
    init_db()
    conn = get_conn()
    try:
        # Simple logic: find first IP not assigned in allocations
        rows = conn.execute("SELECT ip FROM allocations").fetchall()
        assigned_ips = {r["ip"] for r in rows}
        # For demo purposes, assume subnet like "10.13.13.0/24"
        base = subnet.split("/")[0].rsplit(".", 1)[0]
        for i in range(2, 255):
            candidate = f"{base}.{i}"
            if candidate not in assigned_ips:
                return candidate
        return None
    finally:
        conn.close()

def add_user(
    username: str,
    pubkey: str,
    privkey: Optional[str] = None,
    role: str = "client",
    ip: Optional[str] = None,
    server: Optional[str] = None,
) -> None:
    """
    Register a new user. privkey optional (if you only store pubkey).
    """
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, pubkey, client_pubkey, role, ip, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, pubkey, privkey, role, ip, now)
        )
        conn.commit()
    finally:
        conn.close()


def remove_user(username: str) -> None:
    """Remove a user from the database"""
    init_db()
    conn = get_conn()
    try:
        conn.execute(
            "DELETE FROM users WHERE username=?",
            (username,)
        )
        conn.commit()
    finally:
        conn.close()

def get_user(username: str) -> Optional[Dict]:
    """Retrieve a user by username"""
    init_db()
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def add_user(username: str, pubkey: str, privkey : str , server: str, ip: str, role: str = "client"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (username, pubkey, privkey, server, ip, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, pubkey, privkey, server, ip, role, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
