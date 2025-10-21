# wg_tool/keys.py
import subprocess

def gen_private_key() -> str:
    """Generate WireGuard private key"""
    return subprocess.check_output("wg genkey", shell=True).decode().strip()

def pubkey_from_private(private_key: str) -> str:
    """Generate WireGuard public key from private key"""
    return subprocess.check_output(f"echo {private_key} | wg pubkey", shell=True).decode().strip()

def gen_preshared_key() -> str:
    """Generate WireGuard preshared key"""
    return subprocess.check_output("wg genpsk", shell=True).decode().strip()
