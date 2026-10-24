"""Cryptographic policy engine for QUANTA secure channels."""
from enum import Enum
from typing import List, Optional
from quanta_channel.errors import CryptographicDowngradeError

class PolicyMode(str, Enum):
    STRICT_HYBRID = "STRICT_HYBRID"
    CLASSICAL_PERMITTED = "CLASSICAL_PERMITTED"

DEFAULT_HYBRID_GROUPS = ["X25519MLKEM768", "SecP256r1MLKEM768"]
DEFAULT_CLASSICAL_GROUPS = ["X25519", "prime256v1"]

class ChannelPolicy:
    """Defines cryptographic policy invariants for secure channels."""

    def __init__(
        self,
        mode: PolicyMode = PolicyMode.STRICT_HYBRID,
        allowed_groups: Optional[List[str]] = None,
        require_tls13: bool = True,
        enforce_peer_identity: bool = True,
    ):
        self.mode = mode
        self.require_tls13 = require_tls13
        self.enforce_peer_identity = enforce_peer_identity

        if allowed_groups is not None:
            self.allowed_groups = allowed_groups
        elif mode == PolicyMode.STRICT_HYBRID:
            self.allowed_groups = list(DEFAULT_HYBRID_GROUPS)
        else:
            self.allowed_groups = list(DEFAULT_HYBRID_GROUPS) + list(DEFAULT_CLASSICAL_GROUPS)

    def validate_negotiated_group(self, group_name: str) -> None:
        """Enforces that the group actually negotiated satisfies the active policy.

        Raises:
            CryptographicDowngradeError: If negotiated group violates policy constraints.
        """
        if not group_name:
            raise CryptographicDowngradeError("Negotiated group could not be verified from TLS stack.")

        normalized_group = group_name.lower()
        hybrid_normalized = [g.lower() for g in DEFAULT_HYBRID_GROUPS]
        allowed_normalized = [g.lower() for g in self.allowed_groups]

        if self.mode == PolicyMode.STRICT_HYBRID:
            if normalized_group not in hybrid_normalized:
                raise CryptographicDowngradeError(
                    f"Downgrade rejected: Policy '{self.mode.value}' requires a hybrid post-quantum "
                    f"group (e.g., {DEFAULT_HYBRID_GROUPS}), but observed '{group_name}'."
                )

        if normalized_group not in allowed_normalized:
            raise CryptographicDowngradeError(
                f"Policy violation: Negotiated group '{group_name}' is not in allowed list {self.allowed_groups}."
            )


ChannelPolicy.STRICT_HYBRID = ChannelPolicy(mode=PolicyMode.STRICT_HYBRID)
ChannelPolicy.CLASSICAL_PERMITTED = ChannelPolicy(mode=PolicyMode.CLASSICAL_PERMITTED)

