"""
storage.py
SQLite-based storage helper for wg-rbac-tool.

Usage:
    from wg_tool import storage
    storage.init_db()                   # create DB + tables if missing
    storage.set_server_config(pubkey=..., endpoint=..., dns=...)
    storage.add_role("student", ["10.0.0.0/24"], "notes")
    storage.add_user("bob", pubkey, role="student", ip="10.13.13.2/32")
    storage.get_user("bob")
    storage.list_users()
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "wg_rbac.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# We'll open connections per-call (safe for concurrency)
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # enforce foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# -------------------------
# Migrations / initialization
# -------------------------
_SCHEMA = """
BEGIN;

CREATE TABLE IF NOT EXISTS server_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    name TEXT PRIMARY KEY,
    allowed_ips TEXT,        -- JSON array string e.g. '["10.0.0.0/24"]'
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    pubkey TEXT NOT NULL UNIQUE,
    client_pubkey TEXT,
    role TEXT NOT NULL,
    ip TEXT,                 -- assigned IP (e.g. "10.13.13.2/32")
    created_at TEXT NOT NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    policy_text TEXT NOT NULL,    -- DSL source
    created_at TEXT NOT NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ip_pools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    start_ip TEXT NOT NULL,
    end_ip TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS allocations (
    ip TEXT PRIMARY KEY,       -- e.g. "10.13.13.2"
    role TEXT NOT NULL,
    username TEXT,
    assigned_at TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE SET NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS applied_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary TEXT,              -- JSON/text describing applied rules
    applied_at TEXT NOT NULL
);

-- Servers table
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    subnet TEXT UNIQUE NOT NULL,
    private_key TEXT NOT NULL,
    public_key TEXT NOT NULL,
    preshared_key TEXT,
    endpoint TEXT NOT NULL,  -- format: IP:PORT
    dns TEXT,
    created_at TEXT NOT NULL
);

COMMIT;
"""

def init_db():
    """Create DB file + tables if missing. Safe to call multiple times."""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()

# -------------------------
# Server config helpers (key-value style)
# -------------------------
def set_server_config(key: str, value: str):
    """Set a key/value pair for server config (e.g., key='server_pubkey', value='AAA...')."""
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO server_config(key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value, now)
        )
        conn.commit()
    finally:
        conn.close()

def get_server_config(key: str) -> Optional[str]:
    init_db()
    conn = get_conn()
    try:
        r = conn.execute("SELECT value FROM server_config WHERE key = ?", (key,)).fetchone()
        return r["value"] if r else None
    finally:
        conn.close()

# Convenience wrappers
def set_server_pubkey(pubkey: str):
    set_server_config("server_pubkey", pubkey)

def get_server_pubkey() -> Optional[str]:
    return get_server_config("server_pubkey")

def set_server_endpoint(endpoint: str):
    set_server_config("endpoint", endpoint)

def get_server_endpoint() -> Optional[str]:
    return get_server_config("endpoint")

def set_server_dns(dns: str):
    set_server_config("dns", dns)

def get_server_dns() -> Optional[str]:
    return get_server_config("dns")

# -------------------------
# Multi-server management
# -------------------------
def add_server(name: str, subnet: str, private_key: str, public_key: str, endpoint: str, dns: str = "1.1.1.1", preshared_key: Optional[str] = None):
    """Add a new server to the servers table."""
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO servers(name, subnet, private_key, public_key, preshared_key, endpoint, dns, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, subnet, private_key, public_key, preshared_key, endpoint, dns, now)
        )
        conn.commit()
    finally:
        conn.close()

def update_server(name: str, **kwargs):
    """Update server fields. Valid kwargs: subnet, private_key, public_key, preshared_key, endpoint, dns."""
    init_db()
    conn = get_conn()
    try:
        valid_fields = {"subnet", "private_key", "public_key", "preshared_key", "endpoint", "dns"}
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in valid_fields:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if updates:
            values.append(name)
            query = f"UPDATE servers SET {', '.join(updates)} WHERE name = ?"
            conn.execute(query, values)
            conn.commit()
    finally:
        conn.close()

def get_all_servers() -> List[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM servers ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_all_server_ports() -> List[int]:
    """Extract ports from endpoint (IP:PORT)"""
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT endpoint FROM servers").fetchall()
        ports = []
        for r in rows:
            try:
                ports.append(int(r["endpoint"].split(":")[-1]))
            except Exception:
                continue
        return ports
    finally:
        conn.close()

def get_all_subnets() -> List[str]:
    """Return list of all subnets assigned to servers"""
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT subnet FROM servers").fetchall()
        return [r["subnet"] for r in rows]
    finally:
        conn.close()

def get_all_server_names() -> List[str]:
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT name FROM servers").fetchall()
        return [r["name"] for r in rows]
    finally:
        conn.close()

def get_server_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Return server dict by name"""
    init_db()
    conn = get_conn()
    try:
        r = conn.execute("SELECT * FROM servers WHERE name=?", (name,)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def remove_server(name: str):
    """Delete server by name"""
    init_db()
    conn = get_conn()
    try:
        conn.execute("DELETE FROM servers WHERE name=?", (name,))
        conn.commit()
    finally:
        conn.close()

# -------------------------
# Role management
# -------------------------
def add_role(name: str, allowed_ips: Optional[List[str]] = None, notes: Optional[str] = None):
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    allowed_json = json.dumps(allowed_ips or [])
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO roles(name, allowed_ips, notes, created_at) VALUES (?, ?, ?, ?)",
            (name, allowed_json, notes or "", now)
        )
        conn.commit()
    finally:
        conn.close()

def update_role(name: str, allowed_ips: Optional[List[str]] = None, notes: Optional[str] = None):
    init_db()
    allowed_json = json.dumps(allowed_ips) if allowed_ips is not None else None
    conn = get_conn()
    try:
        if allowed_json is not None and notes is not None:
            conn.execute("UPDATE roles SET allowed_ips=?, notes=? WHERE name=?", (allowed_json, notes, name))
        elif allowed_json is not None:
            conn.execute("UPDATE roles SET allowed_ips=? WHERE name=?", (allowed_json, name))
        elif notes is not None:
            conn.execute("UPDATE roles SET notes=? WHERE name=?", (notes, name))
        conn.commit()
    finally:
        conn.close()

def get_role(name: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        r = conn.execute("SELECT name, allowed_ips, notes, created_at FROM roles WHERE name=?", (name,)).fetchone()
        if not r:
            return None
        return {
            "name": r["name"],
            "allowed_ips": json.loads(r["allowed_ips"] or "[]"),
            "notes": r["notes"],
            "created_at": r["created_at"]
        }
    finally:
        conn.close()

def list_roles() -> List[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT name, allowed_ips, notes, created_at FROM roles ORDER BY name").fetchall()
        return [
            {"name": row["name"], "allowed_ips": json.loads(row["allowed_ips"] or "[]"), "notes": row["notes"], "created_at": row["created_at"]}
            for row in rows
        ]
    finally:
        conn.close()

# -------------------------
# User management
# -------------------------
def add_user(username: str, pubkey: str, role: str, ip: Optional[str] = None, client_pubkey: Optional[str] = None):
    """Create a user record. ip can be None (for future dynamic allocator)."""
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users(username, pubkey, client_pubkey, role, ip, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, pubkey, client_pubkey or None, role, ip, now)
        )
        conn.commit()
    finally:
        conn.close()

def update_user_ip(username: str, ip: str):
    init_db()
    conn = get_conn()
    try:
        conn.execute("UPDATE users SET ip=? WHERE username=?", (ip, username))
        conn.commit()
    finally:
        conn.close()

def set_client_pubkey(username: str, client_pubkey: str):
    init_db()
    conn = get_conn()
    try:
        conn.execute("UPDATE users SET client_pubkey=? WHERE username=?", (client_pubkey, username))
        conn.commit()
    finally:
        conn.close()

def remove_user(username: str):
    init_db()
    conn = get_conn()
    try:
        conn.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
    finally:
        conn.close()

def get_user(username: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        r = conn.execute("SELECT username, pubkey, client_pubkey, role, ip, created_at FROM users WHERE username=?", (username,)).fetchone()
        if not r:
            return None
        return {
            "username": r["username"],
            "pubkey": r["pubkey"],
            "client_pubkey": r["client_pubkey"],
            "role": r["role"],
            "ip": r["ip"],
            "created_at": r["created_at"]
        }
    finally:
        conn.close()

def get_user_by_pubkey(pubkey: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        r = conn.execute("SELECT username, pubkey, client_pubkey, role, ip, created_at FROM users WHERE pubkey=?", (pubkey,)).fetchone()
        if not r:
            return None
        return {
            "username": r["username"],
            "pubkey": r["pubkey"],
            "client_pubkey": r["client_pubkey"],
            "role": r["role"],
            "ip": r["ip"],
            "created_at": r["created_at"]
        }
    finally:
        conn.close()

def list_users() -> List[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT username, pubkey, client_pubkey, role, ip, created_at FROM users ORDER BY username").fetchall()
        return [
            {"username": row["username"], "pubkey": row["pubkey"], "client_pubkey": row["client_pubkey"], "role": row["role"], "ip": row["ip"], "created_at": row["created_at"]}
            for row in rows
        ]
    finally:
        conn.close()

# -------------------------
# Policies
# -------------------------
def add_policy(role: str, policy_text: str):
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO policies(role, policy_text, created_at) VALUES (?, ?, ?)", (role, policy_text, now))
        conn.commit()
    finally:
        conn.close()

def list_policies(role: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        if role:
            rows = conn.execute("SELECT id, role, policy_text, created_at FROM policies WHERE role=? ORDER BY id DESC", (role,)).fetchall()
        else:
            rows = conn.execute("SELECT id, role, policy_text, created_at FROM policies ORDER BY id DESC").fetchall()
        return [{"id": r["id"], "role": r["role"], "policy_text": r["policy_text"], "created_at": r["created_at"]} for r in rows]
    finally:
        conn.close()

def get_latest_policy_for_role(role: str) -> Optional[str]:
    init_db()
    conn = get_conn()
    try:
        r = conn.execute("SELECT policy_text FROM policies WHERE role=? ORDER BY id DESC LIMIT 1", (role,)).fetchone()
        return r["policy_text"] if r else None
    finally:
        conn.close()

# -------------------------
# IP pools & allocations (for future dynamic allocator)
# -------------------------
def add_ip_pool(role: str, start_ip: str, end_ip: str):
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO ip_pools(role, start_ip, end_ip, created_at) VALUES (?, ?, ?, ?)", (role, start_ip, end_ip, now))
        conn.commit()
    finally:
        conn.close()

def list_ip_pools(role: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        if role:
            rows = conn.execute("SELECT id, role, start_ip, end_ip, created_at FROM ip_pools WHERE role=?", (role,)).fetchall()
        else:
            rows = conn.execute("SELECT id, role, start_ip, end_ip, created_at FROM ip_pools ORDER BY role").fetchall()
        return [{"id": r["id"], "role": r["role"], "start_ip": r["start_ip"], "end_ip": r["end_ip"], "created_at": r["created_at"]} for r in rows]
    finally:
        conn.close()

def allocate_ip(ip: str, role: str, username: Optional[str] = None):
    """Record allocation. This does not check for conflicts — caller should ensure IP free."""
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO allocations(ip, role, username, assigned_at) VALUES (?, ?, ?, ?)", (ip, role, username, now))
        conn.commit()
    finally:
        conn.close()

def release_ip(ip: str):
    init_db()
    conn = get_conn()
    try:
        conn.execute("DELETE FROM allocations WHERE ip=?", (ip,))
        conn.commit()
    finally:
        conn.close()

def get_all_allocations() -> List[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT ip, role, username, assigned_at FROM allocations ORDER BY assigned_at DESC").fetchall()
        return [{"ip": r["ip"], "role": r["role"], "username": r["username"], "assigned_at": r["assigned_at"]} for r in rows]
    finally:
        conn.close()

def is_ip_allocated(ip: str) -> bool:
    init_db()
    conn = get_conn()
    try:
        r = conn.execute("SELECT 1 FROM allocations WHERE ip=?", (ip,)).fetchone()
        return bool(r)
    finally:
        conn.close()

# -------------------------
# Applied rules recording
# -------------------------
def record_applied_rules(summary: Dict[str, Any]):
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO applied_rules(summary, applied_at) VALUES (?, ?)", (json.dumps(summary), now))
        conn.commit()
    finally:
        conn.close()

def list_applied_rules(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT id, summary, applied_at FROM applied_rules ORDER BY applied_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": r["id"], "summary": json.loads(r["summary"]) if r["summary"] else None, "applied_at": r["applied_at"]} for r in rows]
    finally:
        conn.close()