"""SHST formatting."""
import secrets

def generate_shst_token() -> str:
    """Generates a random SHST token."""
    return f"quanta-shst-{secrets.token_hex(16)}"
