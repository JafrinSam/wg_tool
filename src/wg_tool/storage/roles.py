import json
import datetime
from typing import Optional, List, Dict
from .base import get_conn, init_db

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

def get_role(name: str) -> Optional[Dict[str, any]]:
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
