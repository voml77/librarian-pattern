from __future__ import annotations

from collections.abc import Iterable

from .models import CanonicalArtifact, Domain, PolicyDecision


class PromotionPolicy:
    """
    Determines whether a governed candidate may become canonical.

    Confidence may contribute to this deterministic decision, but confidence
    itself never grants authority.
    """

    def __init__(self, minimum_confidence: float = 0.90) -> None:
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be between 0.0 and 1.0"
            )

        self._minimum_confidence = minimum_confidence

    def evaluate(self, confidence: float) -> PolicyDecision:
        if confidence < self._minimum_confidence:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"confidence {confidence:.2f} is below the deterministic "
                    f"promotion threshold {self._minimum_confidence:.2f}"
                ),
            )

        return PolicyDecision(
            allowed=True,
            reason="candidate satisfies deterministic promotion policy",
        )


class PersonalMemoryActivationPolicy:
    """
    Example domain policy: personal memory requires explicit user consent.
    """

    def evaluate(
        self,
        artifact: CanonicalArtifact,
        *,
        user_consent: bool,
    ) -> PolicyDecision:
        if artifact.domain is not Domain.PERSONAL_MEMORY:
            return PolicyDecision(
                allowed=False,
                reason="artifact is not personal memory",
            )

        if not user_consent:
            return PolicyDecision(
                allowed=False,
                reason="explicit user consent is required",
            )

        return PolicyDecision(
            allowed=True,
            reason="explicit user consent granted",
        )


class KnowledgeActivationPolicy:
    """
    Example domain policy: canonical knowledge requires trusted provenance.
    """

    def __init__(
        self,
        trusted_pipeline_types: Iterable[str],
    ) -> None:
        self._trusted_pipeline_types = frozenset(
            trusted_pipeline_types
        )

    def evaluate(
        self,
        artifact: CanonicalArtifact,
    ) -> PolicyDecision:
        if artifact.domain is not Domain.KNOWLEDGE:
            return PolicyDecision(
                allowed=False,
                reason="artifact is not knowledge",
            )

        if (
            artifact.provenance.pipeline_type
            not in self._trusted_pipeline_types
        ):
            return PolicyDecision(
                allowed=False,
                reason=(
                    "knowledge provenance is not trusted for activation: "
                    f"{artifact.provenance.pipeline_type!r}"
                ),
            )

        return PolicyDecision(
            allowed=True,
            reason="trusted provenance permits knowledge activation",
        )


class RetrievalEligibilityPolicy:
    """
    Derives retrieval eligibility from canonical lifecycle state.

    The policy deliberately ignores vector similarity, Librarian confidence,
    and candidate state.
    """

    def evaluate(
        self,
        artifact: CanonicalArtifact,
    ) -> PolicyDecision:
        if not artifact.is_active:
            return PolicyDecision(
                allowed=False,
                reason="canonical artifact is not active",
            )

        return PolicyDecision(
            allowed=True,
            reason="active canonical artifact is retrieval-eligible",
        )