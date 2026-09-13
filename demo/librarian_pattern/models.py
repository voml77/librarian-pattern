from dataclasses import dataclass
from enum import Enum
from typing import Any


class Domain(str, Enum):
    PERSONAL_MEMORY = "personal_memory"
    KNOWLEDGE = "knowledge"


class CandidateStatus(str, Enum):
    CANDIDATE = "candidate"
    PROMOTED = "promoted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Source:
    source_id: str
    content: str
    source_type: str


@dataclass(frozen=True)
class LibrarianProposal:
    """
    Probabilistic interpretation produced by the Librarian.

    A proposal has no system authority. In particular, it does not own
    candidate identity, provenance, lifecycle state, or retrieval state.
    """

    content: str
    proposed_domain: str
    proposed_type: str
    confidence: float
    importance: float
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidatedProposal:
    """
    A proposal that has crossed deterministic validation.

    Validation does not make the information canonical or authoritative.
    """

    content: str
    domain: Domain
    candidate_type: str
    confidence: float
    importance: float
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Provenance:
    """
    System-owned provenance.

    These fields are deliberately not supplied by LibrarianProposal.
    """

    source_id: str
    source_type: str
    pipeline_type: str
    extraction_run_id: str


@dataclass
class Candidate:
    candidate_id: str
    proposal: ValidatedProposal
    provenance: Provenance
    status: CandidateStatus = CandidateStatus.CANDIDATE


@dataclass
class CanonicalArtifact:
    artifact_id: str
    candidate_id: str
    content: str
    domain: Domain
    artifact_type: str
    provenance: Provenance
    is_active: bool = False
    retrieval_eligible: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class IndexedArtifact:
    """
    Derived retrieval state.

    This object reflects canonical state; it does not create authority.
    """

    artifact_id: str
    content: str
    metadata: dict[str, Any]