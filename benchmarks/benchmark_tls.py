#!/usr/bin/env python3
"""Reproducible benchmark comparing Classical TLS 1.3 vs Hybrid PQC TLS 1.3 (X25519MLKEM768)."""
import sys
import os
import time
import socket
import threading
import statistics
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "quanta-channel", "src")))

from quanta_channel import QuantaServer, QuantaClient, ChannelPolicy, PolicyMode

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CERT = os.path.join(BASE_DIR, "certs", "server.crt")
KEY = os.path.join(BASE_DIR, "certs", "server.key")
CA = os.path.join(BASE_DIR, "certs", "quanta_root_ca.crt")

def benchmark_handshakes(group_name: str, trials: int = 50, port: int = 44360) -> Dict[str, float]:
    """Runs N sequential connection handshakes using client and worker thread server."""
    policy = ChannelPolicy(
        mode=PolicyMode.STRICT_HYBRID if "MLKEM" in group_name else PolicyMode.CLASSICAL_PERMITTED,
        allowed_groups=[group_name],
    )

    server = QuantaServer(certfile=CERT, keyfile=KEY, policy=policy)
    server.bind_and_listen("127.0.0.1", port)

    latencies: List[float] = []

    def server_worker():
        for _ in range(trials):
            try:
                raw_conn, _ = server._server_sock.accept()
                tls_conn = server._ctx.wrap_socket(raw_conn, server_side=True)
                data = tls_conn.recv(1024)
                tls_conn.sendall(b"ACK:" + data)
                tls_conn.close()
            except Exception:
                break

    srv_thread = threading.Thread(target=server_worker, daemon=True)
    srv_thread.start()
    time.sleep(0.1)

    client = QuantaClient(cafile=CA, policy=policy)

    try:
        for _ in range(trials):
            start = time.perf_counter()
            with client.connect("127.0.0.1", port, server_hostname="localhost", timeout=5.0) as channel:
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
                channel._sock.sendall(b"BENCH")
                resp = channel._sock.recv(1024)
                assert resp == b"ACK:BENCH"
    finally:
        server.close()
        srv_thread.join(timeout=1.0)

    return {
        "group": group_name,
        "trials": trials,
        "mean_ms": round(statistics.mean(latencies), 3),
        "median_ms": round(statistics.median(latencies), 3),
        "min_ms": round(min(latencies), 3),
        "max_ms": round(max(latencies), 3),
        "p95_ms": round(statistics.quantiles(latencies, n=20)[18], 3),
    }

def main():
    print("=" * 68)
    print(" QUANTA Benchmark: Classical TLS 1.3 vs Hybrid PQC (RFC 10024)")
    print("=" * 68)
    print(f"Host: Linux x86_64 | OpenSSL 3.6.5 | Python {sys.version.split()[0]}")
    print("Running 50 sequential handshakes per group...\n")

    pqc_results = benchmark_handshakes("X25519MLKEM768", trials=50, port=44365)
    classical_results = benchmark_handshakes("X25519", trials=50, port=44366)

    print(f"{'Metric':<20} | {'X25519MLKEM768 (Hybrid)':<22} | {'X25519 (Classical)':<20}")
    print("-" * 70)
    print(f"{'Mean Latency':<20} | {pqc_results['mean_ms']:>18} ms | {classical_results['mean_ms']:>16} ms")
    print(f"{'Median Latency':<20} | {pqc_results['median_ms']:>18} ms | {classical_results['median_ms']:>16} ms")
    print(f"{'Min Latency':<20} | {pqc_results['min_ms']:>18} ms | {classical_results['min_ms']:>16} ms")
    print(f"{'P95 Latency':<20} | {pqc_results['p95_ms']:>18} ms | {classical_results['p95_ms']:>16} ms")
    print(f"{'Max Latency':<20} | {pqc_results['max_ms']:>18} ms | {classical_results['max_ms']:>16} ms")
    print("-" * 70)
    delta_ms = pqc_results['median_ms'] - classical_results['median_ms']
    pct_overhead = ((pqc_results['median_ms'] / classical_results['median_ms']) - 1) * 100
    print(f"Empirical Median Delta: {delta_ms:+.3f} ms ({pct_overhead:+.1f}% compute overhead)")
    print("=" * 68)

if __name__ == "__main__":
    main()
