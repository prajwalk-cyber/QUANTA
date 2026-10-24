"""In-memory server-side private key store (Phase-2)."""
from typing import Dict, Any

# Keys are formatted like: "user_id:algorithm".
_KEYSTORE: Dict[str, Any] = {}

def store_private_key(user_id: str, algorithm: str, private_key: Any) -> None:
    """Stores a private key for a user and algorithm."""
    _KEYSTORE[f"{str(user_id)}:{algorithm}"] = private_key

def retrieve_private_key(user_id: str, algorithm: str) -> Any:
    """Retrieves a stored private key for a user and algorithm."""
    key = f"{str(user_id)}:{algorithm}"
    if key not in _KEYSTORE:
        raise ValueError(f"No {algorithm} private key found for user {user_id}")
    return _KEYSTORE[key]

def delete_private_key(user_id: str, algorithm: str) -> None:
    """Deletes a stored private key."""
    _KEYSTORE.pop(f"{str(user_id)}:{algorithm}", None)
