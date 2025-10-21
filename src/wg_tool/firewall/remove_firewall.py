import sys
import yaml
from typing import List, Dict, Any
from wg_tool import storage

import subprocess

def remove_applied_firewall(backend: str = None):
    """Remove applied firewall rules stored in SQLite."""
        
    rows = storage.list_applied_rules(backend)
    

    for row in rows:
        cmd = rows['command']
        backend_name = rows['backend'].lower()
        if backend_name == "iptables":
            # Replace -A with -D to delete iptables rule
            cmd = cmd.replace("-A", "-D", 1)
            print(f"🗑️  Removing iptables rule: {cmd}")
            subprocess.run(cmd, shell=True)
        
        elif backend_name == "ufw":
            # For UFW, prepend 'delete' to the stored command
            if cmd.startswith("ufw "):
                delete_cmd = cmd.replace("ufw ", "ufw delete ", 1)
                print(f"🗑️  Removing UFW rule: {delete_cmd}")
                subprocess.run(delete_cmd, shell=True)
            else:
                print(f"⚠️  Skipping invalid UFW command: {cmd}")
    
    storage.clear_applied_rules(backend)
    print("✅ All applied firewall rules removed and cleared from DB.")
