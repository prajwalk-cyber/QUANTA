import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_channel_info_endpoint():
    res = client.get("/api/channel/info")
    assert res.status_code == 200
    data = res.json()
    assert data["channel_version"] == "1.0.0"
    assert "openssl_version" in data
    assert data["has_x25519_mlkem768"] is True
    assert "X25519MLKEM768" in data["supported_pqc_groups"]
    assert "ZERO" in data["key_exposure_risk"]


def test_channel_handshake_demo_endpoint():
    res = client.post("/api/channel/handshake-demo")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["verified_secure_channel"] is True
    assert "ECHO: b'QUANTA_LIVE_DEMO_PAYLOAD'" in data["payload_echo"]

    telemetry = data["telemetry"]
    assert telemetry["tls_version"] == "TLSv1.3"
    assert telemetry["is_pqc_hybrid"] is True
    assert telemetry["negotiated_group"].lower() == "x25519mlkem768"
    assert telemetry["peer_subject"] == "localhost"
    assert telemetry["handshake_latency_ms"] > 0

    audit = data["audit"]
    assert audit["private_keys_exposed"] is False
    assert audit["shared_secrets_exposed"] is False
    assert audit["downgrade_permitted"] is False
