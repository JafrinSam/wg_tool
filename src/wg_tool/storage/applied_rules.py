from typing import Dict, List, Any
import datetime, json
from .base import get_conn, init_db

def store_rule(backend: str, command: str):
    """Store a single applied firewall rule in SQLite."""
    init_db()
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO applied_rule (backend, command) VALUES (?, ?)", (backend, command))
    conn.commit()
    conn.close()

def list_applied_rules(backend: str = None) -> List[Dict[str, Any]]:
    """List all applied firewall rules optionally filtered by backend."""
    conn = get_conn()
    c = conn.cursor()
    if backend:
        c.execute("SELECT id, backend, command, timestamp FROM applied_rule WHERE backend = ?", (backend,))
    else:
        c.execute("SELECT id, backend, command, timestamp FROM applied_rule")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "backend": r[1], "command": r[2], "timestamp": r[3]}
        for r in rows
    ]

def clear_applied_rules(backend: str = None):
    """Delete applied rules from SQLite, optionally filtered by backend."""
    conn = get_conn()
    c = conn.cursor()
    if backend:
        c.execute("DELETE FROM applied_rule WHERE backend = ?", (backend,))
    else:
        c.execute("DELETE FROM applied_rule")
    conn.commit()
    conn.close()