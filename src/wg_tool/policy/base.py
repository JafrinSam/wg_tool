# wg_tool/policy/base.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "wg_rbac.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_SCHEMA = """
BEGIN;

CREATE TABLE IF NOT EXISTS roles (
    name TEXT PRIMARY KEY,
    allowed_ips TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    policy_text TEXT NOT NULL,
    state TEXT DEFAULT 'PENDING',
    created_at TEXT NOT NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS automata_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name TEXT NOT NULL,
    from_state TEXT NOT NULL,
    event TEXT NOT NULL,
    to_state TEXT NOT NULL,
    FOREIGN KEY(policy_name) REFERENCES policies(role) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    pubkey TEXT NOT NULL UNIQUE,
    client_pubkey TEXT,
    role TEXT NOT NULL,
    ip TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE SET NULL
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
    ip TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    username TEXT,
    assigned_at TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE SET NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS applied_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary TEXT,
    applied_at TEXT NOT NULL
);

COMMIT;
"""

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
