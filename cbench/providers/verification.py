from __future__ import annotations

from cbench.providers.capabilities import ProviderCapability, validate_capability


def verify_capability_fixture(capability: ProviderCapability, *, expected_sha256: str) -> bool:
    validate_capability(capability, require_exact=True)
    return capability.verification_fixture_sha256 == expected_sha256
