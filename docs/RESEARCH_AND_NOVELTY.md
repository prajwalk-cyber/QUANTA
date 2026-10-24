# QUANTA — Research Findings, Prior Art, and Novelty Assessment

> **Document:** RESEARCH_AND_NOVELTY.md  
> **Status:** Academic & Research Reference  
> **Repository:** [github.com/prajwalk-cyber/QUANTA](https://github.com/prajwalk-cyber/QUANTA)  
> **Date:** October 2026

---

## 1. Prior Art and Related Systems

To establish a defensible contribution, QUANTA was systematically compared against five established post-quantum secure-channel and cryptographic architectures:

### 1.1 Standard TLS 1.3 with Hybrid Post-Quantum Key Exchange (Chromium / BoringSSL)
- **Mechanism:** Google and Cloudflare deployed `X25519Kyber768Draft00` and subsequently migrated to RFC 10024 `X25519MLKEM768`.
- **Limitation for Custom Applications:** Browsers and WebPKI do not provide application-level policy control, programmatic socket lifecycle hooks, bounded binary framing, or customizable compliance profiles for internal service-to-service networks.
- **QUANTA Differentiation:** QUANTA provides a reusable Python-native secure-channel abstraction with programmable zero-downgrade policy governance, safe observability, and bounded framing.

### 1.2 Open Quantum Safe (liboqs / oqs-provider)
- **Mechanism:** Open Quantum Safe provides C libraries and an OpenSSL 3.x provider for broad experimental benchmarking of candidate algorithms.
- **Limitation:** Focuses on algorithm benchmarking rather than high-level application secure channels, session resilience, or framed peer-to-peer data streaming.
- **QUANTA Differentiation:** QUANTA treats the underlying provider as a swappable cryptographic engine and focuses on the higher-level secure channel, policy enforcement, and application integration layer.

### 1.3 Rosenpass (Post-Quantum WireGuard Auxiliary Protocol)
- **Mechanism:** Rosenpass runs alongside WireGuard to establish a post-quantum pre-shared key (PSK) using Classic McEliece and Kyber.
- **Limitation:** Operates strictly at Layer 3 (IP network tunneling); requires kernel WireGuard setup, root network configuration, and fixed pre-shared identity keys.
- **QUANTA Differentiation:** QUANTA is an application-layer secure-channel library designed for service-to-service, client-server, and microservice architectures that does not require root privileges or kernel VPN configuration.

### 1.4 Signal PQXDH (Post-Quantum Extended Diffie-Hellman)
- **Mechanism:** Asynchronous messaging protocol combining X3DH with Kyber-1024 for asynchronous, disconnected communication.
- **Limitation:** Designed specifically for store-and-forward asynchronous chat messages with pre-keys, not real-time streaming, interactive socket communication, or TLS-compatible web infrastructure.
- **QUANTA Differentiation:** QUANTA provides synchronous, stream-oriented secure channels over TLS 1.3 for interactive workloads.

---

## 2. Objective Novelty Classification

In academic and industrial security engineering, novelty must be evaluated with strict objectivity:

| Potential Claim | Technical Defense | Novelty Classification |
|---|---|---|
| "Invented a new hybrid cryptographic algorithm" | **False.** QUANTA uses standardized primitives: X25519, ML-KEM-768 (NIST FIPS 203), and ML-DSA-65 (NIST FIPS 204). | **Zero Novelty** (Intentionally avoided for security assurance). |
| "Invented a custom hybrid key-exchange handshake" | **False.** QUANTA implements IETF Standards Track RFC 9954 and RFC 10024 over standard TLS 1.3. | **Zero Novelty** (Adherence to standards prevents custom handshake vulnerabilities). |
| "A formal, adaptive policy engine enforcing zero-downgrade invariants via native group inspection with bounded framing" | **True.** QUANTA uniquely bridges the gap between low-level OpenSSL 3.6+ C APIs (`SSL_get0_group_name`) and high-level Python application channels, enforcing machine-checkable invariants, session resilience tokens (SHST), and privacy-preserving audit logs. | **Defensible Engineering & Architectural Contribution.** |

---

## 3. Disproof Criteria (Falsification Hypothesis)

An architecture claim is scientific only if it defines what evidence would disprove it:

1. **Claim:** `X25519MLKEM768` in QUANTA introduces less than 1 network round-trip overhead compared to classical TLS 1.3.
   - *Falsification:* If empirical packet capture demonstrates additional round trips due to TCP segmentation beyond standard initial congestion window thresholds ($10 \times \text{MSS}$), the claim is disproven.
2. **Claim:** The Adaptive Policy Engine prevents all downgrade attacks in `STRICT_HYBRID` mode.
   - *Falsification:* If an active MITM can force a client configured for `STRICT_HYBRID` to accept a classical curve or cipher without triggering a connection termination, the claim is disproven.
3. **Claim:** QUANTA exposes zero secret material across all observation surfaces.
   - *Falsification:* If any shared secret, private key, or traffic secret appears in API responses, logs, or UI elements, the claim is disproven.
