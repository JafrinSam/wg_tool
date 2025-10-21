from typing import Optional, List, Dict
import datetime
from .base import get_conn, init_db

def add_ip_pool(role: str, start_ip: str, end_ip: str):
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO ip_pools(role, start_ip, end_ip, created_at) VALUES (?, ?, ?, ?)", (role, start_ip, end_ip, now))
        conn.commit()
    finally:
        conn.close()

def allocate_ip(ip: str, role: str, username: Optional[str] = None):
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
