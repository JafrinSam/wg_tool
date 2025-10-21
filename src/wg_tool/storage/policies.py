from typing import Optional, List, Dict
import datetime
from .base import get_conn, init_db

def add_policy(role: str, policy_text: str):
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO policies(role, policy_text, created_at) VALUES (?, ?, ?)", (role, policy_text, now))
        conn.commit()
    finally:
        conn.close()
