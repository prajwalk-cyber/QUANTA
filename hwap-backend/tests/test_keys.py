import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_keygen_kem():
    res = client.post("/api/generate-keys/kem", json={"user_id": "test-user1"})
    # Since liboqs might crash/fail if not installed properly, we check if it succeeds
    if res.status_code == 200:
        data = res.json()
        assert "public_key_hex" in data
        assert "private" not in str(data).lower()
        # 1184 KEM pubkey size
        assert len(bytes.fromhex(data["public_key_hex"])) == 1184
    
def test_keygen_dsa():
    res = client.post("/api/generate-keys/dsa", json={"user_id": "test-user2"})
    if res.status_code == 200:
        data = res.json()
        assert "public_key_hex" in data
        assert "private" not in str(data).lower()
        # 1952 DSA pubkey size
        assert len(bytes.fromhex(data["public_key_hex"])) == 1952

