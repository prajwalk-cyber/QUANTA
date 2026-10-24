"""Pure-Python Shor's algorithm simulator.

Supports arbitrary semi-prime N values and coprime bases a.
Returns a realistic measurement histogram, recovered factors,
and circuit metadata computed dynamically from the inputs.

Mathematical background:
  - Find r = ord_N(a): smallest r > 0 where a^r ≡ 1 (mod N)
  - QFT peaks in a t-qubit control register at multiples of 2^t / r
  - Factors derived: gcd(a^(r/2) ± 1, N)
"""
import random
import math
from typing import Dict, List, Optional


def _find_order(a: int, n: int) -> int:
    """Find the multiplicative order of a mod n (smallest r > 0 where a^r ≡ 1 mod n)."""
    if math.gcd(a, n) != 1:
        return -1  # a must be coprime to n
    r = 1
    val = a % n
    while val != 1:
        val = (val * a) % n
        r += 1
        if r > n * n:  # Safety bound
            return -1
    return r


def _get_factors_from_order(a: int, r: int, n: int) -> List[int]:
    """Derive prime factors from the order r using Shor's classical post-processing."""
    if r == -1 or r % 2 != 0:
        return []
    x = pow(a, r // 2, n)
    candidates = [math.gcd(x - 1, n), math.gcd(x + 1, n)]
    factors = [f for f in candidates if 1 < f < n]
    return sorted(set(factors))


def _get_control_register_size(n: int) -> int:
    """Return number of control qubits (t) for the quantum phase estimation register."""
    return max(4, math.ceil(math.log2(n)) + 1)


def _get_target_register_size(n: int) -> int:
    """Return number of target/ancilla qubits needed (at least ceil(log2(n)))."""
    return max(4, math.ceil(math.log2(n)))


def _compute_circuit_depth(n: int, t: int, r: int) -> int:
    """Estimate circuit depth: Hadamards + controlled-U gates + QFT inverse."""
    base = t + r * 3
    size_penalty = int(math.log2(n)) * 2
    return base + size_penalty


def validate_shor_inputs(n: int, a: int) -> Optional[str]:
    """
    Validate that N and a are suitable for Shor's demo.
    Returns None if valid, or an error string if not.
    """
    if n < 4:
        return "N must be at least 4."
    if n > 200:
        return "N must be <= 200 for this educational simulator."
    if n % 2 == 0:
        return f"N={n} is even — factor 2 is trivially extracted. Choose an odd composite."
    if a < 2:
        return "Base a must be >= 2."
    if a >= n:
        return f"Base a must be less than N (a < {n})."
    g = math.gcd(a, n)
    if g != 1:
        return (f"gcd(a={a}, N={n}) = {g} != 1. "
                f"Choose a coprime to N. Hint: factor trivially revealed: {g}")
    # Check N is composite
    if all(n % i != 0 for i in range(2, int(math.sqrt(n)) + 1)):
        return f"N={n} appears to be prime. Shor's algorithm factors composite integers only."
    return None


def run_shor_demo(n: int = 15, a: int = 7, shots: int = 1024) -> dict:
    """
    Simulates Shor's algorithm for factoring N using coprime base a.

    Dynamically computes:
    - Order r = ord_N(a) via classical modular arithmetic
    - Prime factors via Shor's post-processing: gcd(a^(r/2) +/- 1, N)
    - Control register size t based on N
    - QFT measurement histogram with realistic shot noise
    - Circuit depth estimate

    Args:
        n: Integer to factor (composite, 4 <= n <= 200)
        a: Coprime base (2 <= a < n, gcd(a,n)=1)
        shots: Number of simulated measurement shots

    Returns:
        dict with: n, a, factors, measurement_counts, circuit_depth,
                   num_qubits, control_qubits, target_qubits, period_found
    """
    err = validate_shor_inputs(n, a)
    if err:
        raise ValueError(err)

    # Step 1: Compute the order of a mod n
    r = _find_order(a, n)
    if r == -1:
        raise ValueError(
            f"Could not find the order of {a} mod {n}. "
            f"Try a different base a coprime to {n}."
        )

    # Step 2: Derive factors from the order
    factors = _get_factors_from_order(a, r, n)
    if not factors:
        # Try other bases as fallback (Shor retry with different a)
        for alt_a in range(2, n):
            if math.gcd(alt_a, n) == 1 and alt_a != a:
                alt_r = _find_order(alt_a, n)
                if alt_r != -1:
                    alt_factors = _get_factors_from_order(alt_a, alt_r, n)
                    if alt_factors:
                        factors = alt_factors
                        break
    if not factors:
        # Last resort: trial division
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                factors = sorted([i, n // i])
                break

    # Step 3: Compute qubit counts
    t = _get_control_register_size(n)
    num_target = _get_target_register_size(n)
    num_qubits = t + num_target

    # Step 4: Simulate measurement histogram
    # Peaks at multiples of floor(2^t / r)
    period_unit = max(1, (2 ** t) // r)
    peak_states_raw = [i * period_unit for i in range(min(r, 2 ** t))]
    peak_states = sorted(set(s % (2 ** t) for s in peak_states_raw))

    # Distribute shots among peaks with realistic noise
    base_count = shots // len(peak_states)
    measurement_counts: Dict[str, int] = {}
    remaining = shots

    for i, state in enumerate(peak_states):
        bitstring = format(state, f'0{t}b')
        noise_range = max(1, int(base_count * 0.07))
        noise = random.randint(-noise_range, noise_range)
        if i == len(peak_states) - 1:
            count = max(remaining, 1)
        else:
            count = max(base_count + noise, 1)
        measurement_counts[bitstring] = count
        remaining -= count

    # Add realistic decoherence noise to non-peak states
    all_states = list(range(2 ** t))
    non_peak_states = [s for s in all_states if s not in peak_states]
    num_noise = min(max(2, r // 2), len(non_peak_states), 8)
    if non_peak_states and num_noise > 0:
        noise_states = random.sample(non_peak_states, num_noise)
        for state in noise_states:
            bitstring = format(state, f'0{t}b')
            measurement_counts[bitstring] = random.randint(1, max(2, base_count // 20))

    # Sort by integer value for consistent display
    measurement_counts = dict(
        sorted(measurement_counts.items(), key=lambda x: int(x[0], 2))
    )

    # Step 5: Compute circuit metadata
    circuit_depth = _compute_circuit_depth(n, t, r)

    return {
        "n": n,
        "a": a,
        "factors": factors,
        "measurement_counts": measurement_counts,
        "circuit_depth": circuit_depth,
        "num_qubits": num_qubits,
        "control_qubits": t,
        "target_qubits": num_target,
        "period_found": r,
    }
