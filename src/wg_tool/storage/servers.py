# wg_tool/storage/servers.py
from .base import get_conn, init_db
from typing import List, Dict, Any, Optional
import datetime
import ipaddress

init_db()

def add_server(
    name: str,
    subnet: str,
    private_key: str,
    public_key: str,
    endpoint: str,
    dns: str = "1.1.1.1",
    preshared_key: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO servers(name, subnet, private_key, public_key, preshared_key, endpoint, dns, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, subnet, private_key, public_key, preshared_key, endpoint, dns, now),
        )
        conn.commit()
    finally:
        conn.close()

def get_server_by_name(name: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        r = conn.execute("SELECT * FROM servers WHERE name = ?", (name,)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def get_all_servers() -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM servers ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def list_servers() -> List[Dict[str, str]]:
    """Lightweight list for interactive selection."""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT name, subnet, public_key, endpoint, dns FROM servers ORDER BY id").fetchall()
        servers = []
        for r in rows:
            servers.append({
                "name": r["name"],
                "subnet": r["subnet"] or "",
                "public_key": r["public_key"] or "",
                "endpoint": r["endpoint"] or "",
                "dns": r["dns"] or ""
            })
        return servers
    finally:
        conn.close()
        
def get_first_free_ip(subnet: str) -> Optional[str]:
    """
    Return first free IP in subnet, but skip the first host (.1).
    If subnet has no mask, assume /24.
    Excludes already assigned IPs from `users.ip` and `allocations.ip`.
    """
    if not subnet:
        return None

    # If no slash, assume /24
    if "/" not in subnet:
        subnet = f"{subnet}/24"

    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except Exception:
        return None

    conn = get_conn()
    try:
        assigned = set()

        # allocations table (explicit allocations)
        rows = conn.execute("SELECT ip FROM allocations WHERE ip IS NOT NULL").fetchall()
        for r in rows:
            if r["ip"]:
                assigned.add(r["ip"])

        # users table (registered users)
        rows2 = conn.execute("SELECT ip FROM users WHERE ip IS NOT NULL").fetchall()
        for r in rows2:
            ipval = r["ip"]
            if ipval:
                # strip CIDR if stored like "10.0.0.2/32"
                if "/" in ipval:
                    assigned.add(ipval.split("/")[0])
                else:
                    assigned.add(ipval)

        # hosts() yields host addresses (excludes network & broadcast)
        hosts_iter = network.hosts()
        # Skip the first host (typically .1)
        try:
            _first_host = str(next(hosts_iter))
        except StopIteration:
            return None

        # Iterate remaining hosts and return first not assigned
        for host in hosts_iter:
            candidate = str(host)
            if candidate not in assigned:
                return candidate

        return None
    finally:
        conn.close()


# ----- name-aware convenience getters -----
def get_server_pubkey(name: Optional[str] = None) -> Optional[str]:
    conn = get_conn()
    try:
        if name:
            r = conn.execute("SELECT public_key FROM servers WHERE name = ? LIMIT 1", (name,)).fetchone()
        else:
            r = conn.execute("SELECT public_key FROM servers ORDER BY id LIMIT 1").fetchone()
        return r["public_key"] if r else None
    finally:
        conn.close()

def get_server_endpoint(name: Optional[str] = None) -> Optional[str]:
    conn = get_conn()
    try:
        if name:
            r = conn.execute("SELECT endpoint FROM servers WHERE name = ? LIMIT 1", (name,)).fetchone()
        else:
            r = conn.execute("SELECT endpoint FROM servers ORDER BY id LIMIT 1").fetchone()
        return r["endpoint"] if r else None
    finally:
        conn.close()

def get_server_dns(name: Optional[str] = None) -> Optional[str]:
    conn = get_conn()
    try:
        if name:
            r = conn.execute("SELECT dns FROM servers WHERE name = ? LIMIT 1", (name,)).fetchone()
        else:
            r = conn.execute("SELECT dns FROM servers ORDER BY id LIMIT 1").fetchone()
        return r["dns"] if r else None
    finally:
        conn.close()

def remove_server(name: str):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM servers WHERE name=?", (name,))
        conn.commit()
    finally:
        conn.close()

def get_all_server_ports() -> List[int]:
    """
    Get all used server ports by parsing endpoint or the port column if present.
    Returns list[int].
    """
    conn = get_conn()
    try:
        # Prefer explicit port column if available
        cursor = conn.execute("PRAGMA table_info(servers)").fetchall()
        columns = [c[1] for c in cursor]
        ports = []

        if "port" in columns:
            rows = conn.execute("SELECT port FROM servers WHERE port IS NOT NULL").fetchall()
            for r in rows:
                try:
                    ports.append(int(r["port"]))
                except Exception:
                    continue
            return ports

        # Fallback: parse endpoint values like "1.2.3.4:51820"
        rows = conn.execute("SELECT endpoint FROM servers WHERE endpoint IS NOT NULL").fetchall()
        for r in rows:
            endpoint = r["endpoint"] or ""
            if ":" in endpoint:
                try:
                    port = int(endpoint.split(":")[-1])
                    ports.append(port)
                except ValueError:
                    continue
        return ports
    finally:
        conn.close()

def update_server(
    name: str,
    subnet: Optional[str] = None,
    private_key: Optional[str] = None,
    public_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    dns: Optional[str] = None,
    preshared_key: Optional[str] = None,
    port: Optional[int] = None,
    new_name: Optional[str] = None,
) -> None:
    conn = get_conn()
    try:
        fields = []
        values = []

        if new_name is not None:
            fields.append("name = ?")
            values.append(new_name)
        if subnet is not None:
            fields.append("subnet = ?")
            values.append(subnet)
        if private_key is not None:
            fields.append("private_key = ?")
            values.append(private_key)
        if public_key is not None:
            fields.append("public_key = ?")
            values.append(public_key)
        if endpoint is not None:
            fields.append("endpoint = ?")
            values.append(endpoint)
        if dns is not None:
            fields.append("dns = ?")
            values.append(dns)
        if preshared_key is not None:
            fields.append("preshared_key = ?")
            values.append(preshared_key)
        if port is not None:
            fields.append("port = ?")
            values.append(port)

        if not fields:
            return

        values.append(name)
        query = f"UPDATE servers SET {', '.join(fields)} WHERE name = ?"
        conn.execute(query, tuple(values))
        conn.commit()
    finally:
        conn.close()
