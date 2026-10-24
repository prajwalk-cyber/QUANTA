# QUANTA — IEEE Research Paper

This directory contains the complete publication-quality LaTeX source code, BibTeX references, and build instructions for the IEEE conference paper:

> **QUANTA: A Policy-Governed Secure-Channel Architecture for Hybrid Post-Quantum TLS 1.3**  
> *Author:* Prajwal K (`prajjuk.in.com@gmail.com`)  
> *Repository:* [https://github.com/prajwalk-cyber/QUANTA](https://github.com/prajwalk-cyber/QUANTA)

---

## 📑 Paper Overview & Scientific Evidence

- **Track / Target:** Applied Cryptography, Network Protocol Security, Post-Quantum Systems Engineering (IEEE S&P / ACM CCS / IEEE EuroS&P / IEEE CNS style).
- **Core Research Question:** How can application endpoints reliably enforce post-quantum hybrid key exchange over standardized TLS 1.3 without trusting intermediary proxies, preventing silent cryptographic downgrade, and containing denial-of-service exposure under bounded application framing?
- **Format:** IEEE Two-Column Conference Format (`IEEEtran.cls`).
- **Target Length:** Approximately 6 pages including tables, formulas, and references.

### Empirical Results Summary (Tested on Physical Hardware)
- **Workload:** 50 consecutive multi-process TLS 1.3 handshakes on physical AMD Ryzen 7 5800H hardware with Linux 6.17 and OpenSSL 3.6.5.
- **Classical TLS 1.3 (`X25519`):** 0.510 ms median latency.
- **Hybrid PQC (`X25519MLKEM768`):** 0.655 ms median latency.
- **Compute Overhead:** **+145 µs (+28.4%)** CPU compute delta.
- **Network Invariant:** **Exact same 1-RTT**; key exchange payload (+2,304 bytes) easily fits within the standard 10-MSS TCP initial congestion window ($\le 14.6$ KiB).

---

## 🛠️ Build & Compilation Instructions

### Option 1: Compiling with TeX Live / MacTeX (Local CLI)

Ensure `texlive-core` (or equivalent) and `texlive-bibtexextra` are installed:

```bash
cd paper/

# Step 1: Initial LaTeX compilation
pdflatex quanta_ieee_paper.tex

# Step 2: Generate bibliography
bibtex quanta_ieee_paper

# Step 3: Resolve cross-references (run twice)
pdflatex quanta_ieee_paper.tex
pdflatex quanta_ieee_paper.tex
```

Or using `latexmk`:
```bash
latexmk -pdf quanta_ieee_paper.tex
```

### Option 2: Overleaf (Zero-Install Online Compiler)

1. Create a new blank project on [Overleaf](https://www.overleaf.com/).
2. Upload the contents of the `paper/` folder:
   - `quanta_ieee_paper.tex`
   - `references.bib`
   - `figures/` (if any image files are added)
3. Set Compiler to **pdfLaTeX** and TeX Live version to **2024 or later**.
4. Click **Recompile**.

### Option 3: Docker-Based Compilation

```bash
docker run --rm -v $(pwd):/work -w /work texlive/texlive:latest pdflatex quanta_ieee_paper.tex
docker run --rm -v $(pwd):/work -w /work texlive/texlive:latest bibtex quanta_ieee_paper
docker run --rm -v $(pwd):/work -w /work texlive/texlive:latest pdflatex quanta_ieee_paper.tex
```

---

## 📋 Scientific Integrity & Verification Checklist

- [x] **No Fabricated Data:** Every number in Table II and Section VI corresponds to the empirical 50-handshake benchmarking run in `benchmarks/benchmark_tls.py`.
- [x] **Accurate Standards Attribution:** Cites official NIST standards (FIPS 203, FIPS 204, FIPS 205) and IETF RFCs (RFC 8446, RFC 9954, RFC 10024).
- [x] **Accurate Cryptographic Scope:** Explicitly distinguishes hybrid post-quantum key establishment (`X25519MLKEM768`) from post-quantum authentication (FIPS 204 ML-DSA-65). Acknowledges that the primary channel currently authenticates via classical X.509 PKI while protecting confidentiality against Harvest-Now-Decrypt-Later adversaries.
- [x] **Separation of Claims:** Formally separates verified systems achievements (10/10 passing tests, runtime C-introspection, bounded framing) from future work (full PQC PKI certificate chains, formal ProVerif verification).
