# QUANTA — Formal Threat Model & Security Properties

> **Document:** THREAT_MODEL.md  
> **Status:** Architecture Reference  
> **Repository:** [github.com/prajwalk-cyber/QUANTA](https://github.com/prajwalk-cyber/QUANTA)  
> **Date:** October 2026

---

## 1. Adversary Model & Assumptions

QUANTA models adversaries across four operational tiers:

```text
+--------------------------------------------------------------------------+
| Tier 4: Future Cryptanalytically Relevant Quantum Computer (CRQC)       |
| - Can execute Shor's algorithm in polynomial time against RSA & ECC      |
| - Can execute Grover's search algorithm with quadratic speedup           |
+--------------------------------------------------------------------------+
| Tier 3: Active Man-in-the-Middle (MITM) Network Adversary               |
| - Can intercept, modify, replay, inject, and drop packets                |
| - Can manipulate protocol capabilities to attempt downgrade attacks      |
+--------------------------------------------------------------------------+
| Tier 2: Passive Global Network Adversary (Harvest-Now-Decrypt-Later)     |
| - Can record, store, and analyze unlimited encrypted network traffic     |
| - Archives traffic today for retrospective quantum decryption tomorrow    |
+--------------------------------------------------------------------------+
| Tier 1: Local / Host Process Boundary                                   |
| - Non-privileged local processes attempting side-channel inspection      |
+--------------------------------------------------------------------------+
```

### Trust Assumptions
1. **Endpoint Host Integrity:** The host machine running the client and server processes is not root-compromised. If an adversary has kernel memory access on the endpoint, no cryptographic protocol can protect in-flight session keys.
2. **Cryptographic Randomness:** The host operating system provides a cryptographically secure random number generator (CSPRNG via `/dev/urandom` / `getrandom`).
3. **CA Trust Store Integrity:** The client maintains a trustworthy list of root certificate authorities or pinned identities.
4. **Underlying Primitives Hardness:**
   - Elliptic Curve Discrete Logarithm Problem (ECDLP) over Curve25519 remains hard for classical adversaries.
   - Module Learning With Errors (M-LWE) over polynomial lattices (FIPS 203 ML-KEM-768) remains hard for both classical and quantum adversaries.
   - AES-256 and SHA-256 provide at least 128 bits of post-quantum security against Grover-accelerated search.

---

## 2. In-Scope vs. Out-of-Scope Security Properties

| Property | In Scope? | Exact Guarantee Provided | Non-Guarantee / Limitation |
|---|---|---|---|
| **Confidentiality against Classical Attackers** | **Yes** | Protected by AES-256-GCM / ChaCha20-Poly1305 with keys derived from X25519 + ML-KEM-768. | None within computational limits. |
| **Confidentiality against Quantum Attackers (HNDL)** | **Yes** | Protected by NIST FIPS 203 ML-KEM-768. An adversary recording traffic cannot decrypt it with a future CRQC. | Assumes lattice M-LWE hardness holds. |
| **Integrity & Authenticity** | **Yes** | 128-bit AEAD authentication tags on every TLS record; length-prefixed QNT1 frames. | None. |
| **Forward Secrecy** | **Yes** | Ephemeral keys generated per handshake. Compromise of long-term server cert does not compromise past sessions. | If session ticket is reused without fresh key exchange. |
| **Downgrade Resistance** | **Yes** | In strict hybrid mode, connection aborts if negotiated group != `X25519MLKEM768`. | In classical-permitted mode, classical sessions are allowed by policy. |
| **Post-Quantum Authentication** | **Conditional** | Supported when ML-DSA-65 certificate chains are configured. Standard mode uses classical X.509 certs. | Hybrid key exchange does NOT make classical RSA/ECDSA certificates quantum-safe against real-time MITM. |
| **Traffic Analysis / Metadata Privacy** | **Partial** | SNI, packet sizes, and timing are visible to network observers unless encapsulated in ECH or VPN. | Underlying transport metadata is not obfuscated. |
| **Physical Side-Channel Attacks** | **Out of Scope** | Power analysis, fault injection, and electromagnetic emission attacks on physical hardware. | Requires specialized HSM hardware. |

---

## 3. Cryptographic Invariants Enforced by Architecture

1. **Fail-Closed Invariant:** If `STRICT_HYBRID` policy is selected, under no circumstances will the socket deliver or accept application bytes if `SSL_get0_group_name()` is not an authorized hybrid group (`X25519MLKEM768`).
2. **Key Isolation Invariant:** Private keys, pre-master secrets, traffic secrets, and session keys are never returned across API interfaces, logged into audit files, or exposed to the dashboard UI.
3. **No Double-Encryption Invariant:** Application data is encrypted solely by the TLS 1.3 Record Layer; no redundant custom AES layers are layered on top without separate cryptographic justification.
4. **Bounded Allocation Invariant:** Application frames cannot exceed 16 MiB. Frames violating this bound trigger immediate stream termination without buffer allocation.
5. **Transcript Authentication Invariant:** Derived traffic keys are strictly bound to the full handshake transcript hash per RFC 8446 Section 4.4.
