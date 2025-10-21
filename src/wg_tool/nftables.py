# wg_tool/nftables.py
import subprocess
from typing import List

def apply_commands(cmds: List[List[str]]):
    """Apply a list of nft command arrays"""
    for cmd in cmds:
        subprocess.run(cmd, check=True)

def delete_table(table_name: str):
    """Delete a table safely"""
    subprocess.run(["sudo", "nft", "delete", "table", table_name], check=False)

def ensure_table(table_name: str):
    """Ensure table exists"""
    subprocess.run(["sudo", "nft", "add", "table", table_name], check=False)
