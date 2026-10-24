# quanta-channel

> **Standards-Compliant Post-Quantum Hybrid TLS 1.3 Secure Channel Library**

`quanta-channel` is a high-performance Python secure-channel library that enforces RFC 10024 hybrid post-quantum key exchange (`X25519MLKEM768`) over standard TLS 1.3 with bounded binary application framing (`QNT1`) and zero-downgrade policy governance.

## Key Features

- **Standardized PQ/T Hybrid Key Exchange:** Uses IETF RFC 10024 / RFC 9954 `X25519MLKEM768` via OpenSSL 3.6+.
- **Zero-Downgrade Invariant:** Inspects native TLS negotiation directly (`SSL_get0_group_name`) and fails closed on unauthorized classical fallback.
- **Strict Peer Validation:** Enforces X.509 certificate validation and Subject Alternative Name hostname matching by default.
- **Bounded Binary Framing (`QNT1`):** Length-prefixed framing up to 16 MiB with automatic keepalive PING/PONG.
- **Leak-Free Telemetry:** Surfaces verified group names, ciphers, and latencies with zero secret disclosure.

## Quickstart

### Server Example

```python
from quanta_channel import QuantaServer, ChannelPolicy, PolicyMode

server = QuantaServer(
    certfile="certs/server.crt",
    keyfile="certs/server.key",
    policy=ChannelPolicy(mode=PolicyMode.STRICT_HYBRID),
)
server.bind_and_listen("127.0.0.1", 4433)
print("Listening for TLS 1.3 hybrid connections...")

channel, addr = server.accept_channel()
print(f"Connected from {addr}, negotiated group: {channel.negotiated_group}")

msg = channel.receive_message()
print(f"Received: {msg.decode()}")
channel.send_message(b"ECHO: " + msg)
channel.close()
```

### Client Example

```python
from quanta_channel import QuantaClient, ChannelPolicy, PolicyMode

client = QuantaClient(
    cafile="certs/quanta_root_ca.crt",
    policy=ChannelPolicy(mode=PolicyMode.STRICT_HYBRID),
)

with client.connect("127.0.0.1", 4433, server_hostname="localhost") as channel:
    print(f"Secure channel established! Negotiated group: {channel.negotiated_group}")
    channel.send_message(b"Hello Quantum-Safe World")
    reply = channel.receive_message()
    print(f"Reply: {reply.decode()}")
```
