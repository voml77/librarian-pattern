from __future__ import annotations

from uuid import uuid4

from .models import (
    Candidate,
    CandidateStatus,
    CanonicalArtifact,
    Provenance,
    ValidatedProposal,
)


class CandidateFactory:
    """
    Creates governed candidates from validated proposals.

    Candidate identity and provenance are owned by the system, not by the
    Librarian proposal.
    """

    def create(
        self,
        proposal: ValidatedProposal,
        provenance: Provenance,
        *,
        candidate_id: str | None = None,
    ) -> Candidate:
        return Candidate(
            candidate_id=candidate_id or self._new_id("cand"),
            proposal=proposal,
            provenance=provenance,
        )

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"


class CandidateStore:
    """
    In-memory candidate store used by the reference implementation.

    Persisting a candidate does not make it canonical.
    """

    def __init__(self) -> None:
        self._items: dict[str, Candidate] = {}

    def persist(self, candidate: Candidate) -> None:
        if candidate.candidate_id in self._items:
            raise ValueError(
                f"candidate already exists: {candidate.candidate_id}"
            )

        self._items[candidate.candidate_id] = candidate

    def get(self, candidate_id: str) -> Candidate:
        try:
            return self._items[candidate_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown candidate: {candidate_id}"
            ) from exc

    def update_status(
        self,
        candidate_id: str,
        status: CandidateStatus,
    ) -> Candidate:
        candidate = self.get(candidate_id)
        candidate.status = status
        return candidate


class CanonicalStore:
    """
    In-memory authoritative store.

    The store owns canonical lifecycle state. Derived indexes may reflect this
    state later, but they do not define it.
    """

    def __init__(self) -> None:
        self._items: dict[str, CanonicalArtifact] = {}

    def create_from_candidate(
        self,
        candidate: Candidate,
        *,
        artifact_id: str | None = None,
    ) -> CanonicalArtifact:
        if candidate.status is not CandidateStatus.CANDIDATE:
            raise ValueError(
                "only candidates in CANDIDATE state may be promoted"
            )

        artifact = CanonicalArtifact(
            artifact_id=artifact_id or self._new_id("artifact"),
            candidate_id=candidate.candidate_id,
            content=candidate.proposal.content,
            domain=candidate.proposal.domain,
            artifact_type=candidate.proposal.candidate_type,
            provenance=candidate.provenance,
        )

        if artifact.artifact_id in self._items:
            raise ValueError(
                f"artifact already exists: {artifact.artifact_id}"
            )

        self._items[artifact.artifact_id] = artifact
        candidate.status = CandidateStatus.PROMOTED

        return artifact

    def get(self, artifact_id: str) -> CanonicalArtifact:
        try:
            return self._items[artifact_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown artifact: {artifact_id}"
            ) from exc

    def set_active(
        self,
        artifact_id: str,
        active: bool,
    ) -> CanonicalArtifact:
        artifact = self.get(artifact_id)
        artifact.is_active = active

        if not active:
            artifact.retrieval_eligible = False

        return artifact

    def set_retrieval_eligible(
        self,
        artifact_id: str,
        eligible: bool,
    ) -> CanonicalArtifact:
        artifact = self.get(artifact_id)

        if eligible and not artifact.is_active:
            raise ValueError(
                "inactive canonical artifacts cannot become retrieval-eligible"
            )

        artifact.retrieval_eligible = eligible

        return artifact

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"