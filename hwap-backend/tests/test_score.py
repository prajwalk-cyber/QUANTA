import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_score():
    client.post("/api/switch-tier", json={"tier": 1})
    res = client.get("/api/score")
    assert res.status_code == 200
    assert res.json()["total_score"] == 94.2

def test_weights_sum():
    from hndlr import WEIGHTS
    assert sum(WEIGHTS.values()) == 1.0
