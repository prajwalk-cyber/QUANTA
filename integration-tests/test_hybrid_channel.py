"""Multi-process integration tests for quanta-channel hybrid TLS 1.3."""
import subprocess
import time
import os
import signal
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_BIN = os.environ.get("PYTHON_BIN", "python3")
SERVER_SCRIPT = os.path.join(BASE_DIR, "examples", "server.py")
CLIENT_SCRIPT = os.path.join(BASE_DIR, "examples", "client.py")

PORT_BASE = 44350

def run_server_client_pair(port, srv_args=None, client_args=None):
    """Launches server and client in independent OS processes and collects output."""
    srv_cmd = [PYTHON_BIN, SERVER_SCRIPT, "--port", str(port)] + (srv_args or [])
    client_cmd = [PYTHON_BIN, CLIENT_SCRIPT, "--port", str(port)] + (client_args or [])

    srv_proc = subprocess.Popen(srv_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(0.4)

    try:
        client_res = subprocess.run(client_cmd, capture_output=True, text=True, timeout=10)
        srv_stdout, srv_stderr = srv_proc.communicate(timeout=5)
        return client_res, srv_proc.returncode, srv_stdout, srv_stderr
    finally:
        if srv_proc.poll() is None:
            srv_proc.terminate()
            srv_proc.wait(timeout=2)

def test_independent_processes_hybrid_handshake_success():
    """Verifies that separate client and server processes negotiate X25519MLKEM768."""
    port = PORT_BASE + 1
    client_res, srv_code, srv_out, srv_err = run_server_client_pair(
        port,
        srv_args=["--policy", "STRICT_HYBRID"],
        client_args=["--policy", "STRICT_HYBRID", "--message", "HYBRID_INTEGRATION_TEST_PAYLOAD"]
    )

    assert client_res.returncode == 0, f"Client failed: {client_res.stderr}"
    assert srv_code == 0, f"Server failed: {srv_err}"

    # Verify negotiated group is X25519MLKEM768 on both endpoints
    assert "Negotiated Group:  X25519MLKEM768" in client_res.stdout
    assert "Negotiated Group:  X25519MLKEM768" in srv_out

    # Verify TLS version is 1.3
    assert "TLS Version:       TLSv1.3" in client_res.stdout
    assert "TLS Version:       TLSv1.3" in srv_out

    # Verify data exchange
    assert "PQC_ACK: HYBRID_INTEGRATION_TEST_PAYLOAD" in client_res.stdout

def test_untrusted_certificate_rejected():
    """Verifies that a server presenting an untrusted certificate is rejected by the client."""
    port = PORT_BASE + 2
    client_res, srv_code, srv_out, srv_err = run_server_client_pair(
        port,
        srv_args=["--cert", "certs/untrusted_server.crt", "--key", "certs/untrusted_server.key"],
        client_args=["--ca", "certs/quanta_root_ca.crt"]
    )

    # Client must fail certificate verification
    assert client_res.returncode != 0
    assert "certificate verify failed" in client_res.stderr.lower()

def test_hostname_mismatch_rejected():
    """Verifies that a server certificate with mismatched SAN hostname is rejected."""
    port = PORT_BASE + 3
    client_res, srv_code, srv_out, srv_err = run_server_client_pair(
        port,
        srv_args=["--cert", "certs/wrong_host.crt", "--key", "certs/wrong_host.key"],
        client_args=["--ca", "certs/quanta_root_ca.crt", "--server-hostname", "localhost"]
    )

    # Client must fail hostname verification
    assert client_res.returncode != 0
    err_text = client_res.stderr.lower()
    assert "hostname" in err_text or "match" in err_text or "ip address" in err_text

def test_strict_hybrid_downgrade_rejection():
    """Verifies that in STRICT_HYBRID mode, negotiating a classical-only group aborts the connection."""
    port = PORT_BASE + 4

    # Run custom server that only advertises classical X25519
    import threading
    import socket
    import ssl
    from quanta_channel.native_tls import set_ssl_context_groups

    srv_hit = threading.Event()

    def classical_only_server():
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(
            os.path.join(BASE_DIR, "certs", "server.crt"),
            os.path.join(BASE_DIR, "certs", "server.key")
        )
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        # Force classical only!
        set_ssl_context_groups(ctx, ["X25519"])

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", port))
            s.listen(1)
            srv_hit.set()
            try:
                conn, _ = s.accept()
                with ctx.wrap_socket(conn, server_side=True) as ss:
                    ss.recv(1024)
            except Exception:
                pass

    t = threading.Thread(target=classical_only_server, daemon=True)
    t.start()
    srv_hit.wait(timeout=2)
    time.sleep(0.2)

    # Now launch client in STRICT_HYBRID mode pointing to this server
    client_cmd = [
        PYTHON_BIN, CLIENT_SCRIPT,
        "--port", str(port),
        "--policy", "STRICT_HYBRID",
        "--ca", "certs/quanta_root_ca.crt"
    ]
    client_res = subprocess.run(client_cmd, capture_output=True, text=True, timeout=5)

    # Client MUST fail because the server lacks hybrid groups (alert handshake failure)
    # or fails post-handshake group validation
    assert client_res.returncode != 0
    err_lower = client_res.stderr.lower()
    assert "handshake_failure" in err_lower or "downgrade rejected" in err_lower or "cryptographicdowngradeerror" in err_lower
