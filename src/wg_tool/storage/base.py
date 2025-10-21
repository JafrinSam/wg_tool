import sqlite3
from pathlib import Path
import datetime

# Database file path
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "wg_rbac.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Full schema
_SCHEMA = """
BEGIN;

-- Generic key-value config table
CREATE TABLE IF NOT EXISTS server_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Servers table
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    subnet TEXT UNIQUE NOT NULL,
    private_key TEXT NOT NULL,
    public_key TEXT NOT NULL,
    preshared_key TEXT,
    endpoint TEXT NOT NULL,
    dns TEXT,
    created_at TEXT NOT NULL
);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    name TEXT PRIMARY KEY,
    allowed_ips TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

-- Users table (merged properly with server and client_pubkey)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    pubkey TEXT NOT NULL,
    privkey TEXT,
    server TEXT,
    role TEXT,
    ip TEXT,
    created_at TEXT NOT NULL
   
);

-- Policies table
CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    policy_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE CASCADE
);

-- IP pools table
CREATE TABLE IF NOT EXISTS ip_pools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    start_ip TEXT NOT NULL,
    end_ip TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE CASCADE
);

-- IP allocations table
CREATE TABLE IF NOT EXISTS allocations (
    ip TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    username TEXT,
    assigned_at TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE SET NULL,
    FOREIGN KEY (role) REFERENCES roles(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS applied_rule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backend TEXT NOT NULL,
            command TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );

COMMIT;
"""

def get_conn():
    """Return a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize the database with all tables."""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
