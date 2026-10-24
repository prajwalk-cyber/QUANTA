# QUANTA — Architecture Decision Records (ADRs)

> **Document:** ARCHITECTURE_DECISIONS.md  
> **Status:** Accepted Standards Baseline  
> **Repository:** [github.com/prajwalk-cyber/QUANTA](https://github.com/prajwalk-cyber/QUANTA)  
> **Date:** October 2026

---

## ADR-001: Standardization on TLS 1.3 as Transport Boundary

### Context
Prior prototypes evaluated custom application-layer key exchanges over HTTP REST endpoints.

### Decision
QUANTA adopts **standard TLS 1.3 (RFC 8446)** with PQ/T hybrid key agreement (**RFC 10024**) as its cryptographic transport boundary.

### Rationale
Custom cryptographic handshakes over HTTP introduce severe vulnerabilities:
- Lack of standardized transcript binding.
- Vulnerability to MITM manipulation.
- High serialization and HTTP latency overhead.
TLS 1.3 has undergone extensive formal verification, incorporates dual-direction traffic secrets, provides 1-RTT connection latency, and handles record layer AEAD natively.

### Trade-offs
- Requires managing X.509 certificates and trust roots.
- Requires C-level integration with OpenSSL 3.6+ to inspect negotiated groups.

---

## ADR-002: Selection of `X25519MLKEM768` as Primary Hybrid Group

### Context
Multiple post-quantum KEMs and hybrid groups exist, including Classic McEliece, HQC, and various ML-KEM parameter sets (512, 768, 1024).

### Decision
QUANTA standardizes on **`X25519MLKEM768`** (IETF RFC 10024, IANA codepoint `0x11ec`) as its primary hybrid key-exchange group.

### Rationale
- **NIST Security Category 3:** Equivalent to AES-192 in quantum security margin, providing an optimal balance between security and performance.
- **Wire Size:** ML-KEM-768 public key (1,184 B) and ciphertext (1,088 B) fit comfortably within a single MTU segment alongside X25519 (32 B).
- **Standardization:** Adopted by major browser engines, Cloudflare, and standardized by the IETF TLS Working Group in RFC 10024.

### Trade-offs
- Does not achieve Category 5 (ML-KEM-1024), but Category 5 incurs significantly larger packet sizes with diminishing practical security returns.

---

## ADR-003: Rejection of Redundant Application-Layer Encryption

### Context
A common pattern in experimental security libraries is to encrypt payloads with AES-GCM before sending them over a TLS connection that already encrypts them with AES-GCM.

### Decision
QUANTA **explicitly rejects redundant application-layer encryption**. Data transmitted over the established `quanta-channel` relies directly on the TLS 1.3 Record Layer AEAD.

### Rationale
- Double encryption doubles CPU usage and memory copies with zero cryptographic gain (if TLS 1.3 AEAD is broken, the attacker already has key recovery capability or the underlying cipher is compromised).
- Simplifies the architecture and prevents key synchronization bugs.

### Trade-offs
- Application data is decrypted at the TLS termination boundary. In scenarios requiring end-to-end multi-hop proxy traversal, an explicit message-level encryption layer would be needed.

---

## ADR-004: Strict Zero-Downgrade Invariant via Runtime Group Inspection

### Context
Standard TLS client libraries typically accept whatever cipher suite or group the server selects if it is within the configured list. In mixed environments, an active attacker can tamper with ClientHello to force a classical group.

### Decision
QUANTA implements **native runtime group inspection** using `SSL_get0_group_name()` on the established socket. In `STRICT_HYBRID` mode, if the negotiated group is not an authorized post-quantum hybrid group, the connection is **immediately aborted before any application bytes are transmitted**.

### Rationale
Prevents silent downgrade attacks and configuration drifts, guaranteeing that application data only flows over verified post-quantum connections.
