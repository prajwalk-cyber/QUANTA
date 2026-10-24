import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_signing_flow():
    keys_res = client.post("/api/generate-keys/dsa", json={"user_id": "u1"})
    if keys_res.status_code == 200:
        pub = keys_res.json()["public_key_hex"]
        
        sign_res = client.post("/api/sign", json={"user_id": "u1", "message": "msg"})
        assert sign_res.status_code == 200
        
        sig_id = sign_res.json()["signature_id"]
        sig_bytes = sign_res.json()["sig_size_bytes"]
        assert sig_bytes == 3293
        
        valid_res = client.post("/api/verify", json={"signature_id": sig_id, "message": "msg", "public_key_hex": pub})
        assert valid_res.json()["valid"] == True
        
        invalid_res = client.post("/api/verify", json={"signature_id": sig_id, "message": "edited msg", "public_key_hex": pub})
        assert invalid_res.json()["valid"] == False
