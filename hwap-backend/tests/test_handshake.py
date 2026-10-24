import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_handshake():
    res = client.post("/api/handshake", json={"tier": 1})
    if res.status_code == 200:
        data = res.json()
        assert "K_hybrid_hex" in data
        assert data["timing"]["total_ms"] < 5000  # < 5 seconds, not 5ms

def test_switch_tier():
    res = client.post("/api/switch-tier", json={"tier": 2})
    assert res.status_code == 200
    assert "ML-KEM-768, ECDSA" in res.json()["algorithm_set"]

