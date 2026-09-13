from librarian_pattern.index import DerivedIndex
from librarian_pattern.lifecycle import (
    CandidateFactory,
    CanonicalStore,
)
from librarian_pattern.models import (
    CandidateStatus,
    LibrarianProposal,
    Provenance,
)
from librarian_pattern.policies import (
    PersonalMemoryActivationPolicy,
    PromotionPolicy,
    RetrievalEligibilityPolicy,
)
from librarian_pattern.validation import (
    ProposalValidationError,
    ProposalValidator,
)


def test_invalid_proposal_does_not_become_candidate() -> None:
    validator = ProposalValidator()

    proposal = LibrarianProposal(
        content="Invalid authority claim.",
        proposed_domain="system_authority",
        proposed_type="fact",
        confidence=0.99,
        importance=0.99,
    )

    try:
        validator.validate(proposal)
    except ProposalValidationError:
        pass
    else:
        raise AssertionError(
            "invalid proposal unexpectedly passed validation"
        )


def test_candidate_is_not_canonical_truth() -> None:
    validator = ProposalValidator()
    factory = CandidateFactory()
    canonical_store = CanonicalStore()

    proposal = LibrarianProposal(
        content="Canonical state must be governed.",
        proposed_domain="knowledge",
        proposed_type="concept",
        confidence=0.95,
        importance=0.80,
    )

    validated = validator.validate(proposal)

    candidate = factory.create(
        validated,
        Provenance(
            source_id="source-001",
            source_type="document",
            pipeline_type="verified_research",
            extraction_run_id="run-001",
        ),
    )

    assert candidate.status is CandidateStatus.CANDIDATE

    artifact = canonical_store.create_from_candidate(candidate)

    assert candidate.status is CandidateStatus.PROMOTED
    assert artifact.candidate_id == candidate.candidate_id


def test_provenance_is_system_owned() -> None:
    proposal = LibrarianProposal(
        content="Some interpreted information.",
        proposed_domain="knowledge",
        proposed_type="fact",
        confidence=0.90,
        importance=0.50,
    )

    assert not hasattr(proposal, "source_id")
    assert not hasattr(proposal, "pipeline_type")
    assert not hasattr(proposal, "extraction_run_id")


def test_promotion_does_not_activate_personal_memory() -> None:
    validator = ProposalValidator()
    factory = CandidateFactory()
    canonical_store = CanonicalStore()
    promotion_policy = PromotionPolicy(
        minimum_confidence=0.90
    )

    proposal = LibrarianProposal(
        content="The user prefers short examples.",
        proposed_domain="personal_memory",
        proposed_type="preference",
        confidence=0.95,
        importance=0.70,
    )

    validated = validator.validate(proposal)

    candidate = factory.create(
        validated,
        Provenance(
            source_id="conversation-001",
            source_type="conversation",
            pipeline_type="conversation_extraction",
            extraction_run_id="run-002",
        ),
    )

    decision = promotion_policy.evaluate(
        candidate.proposal.confidence
    )

    assert decision.allowed is True

    artifact = canonical_store.create_from_candidate(candidate)

    assert artifact.is_active is False


def test_personal_memory_requires_explicit_consent() -> None:
    validator = ProposalValidator()
    factory = CandidateFactory()
    canonical_store = CanonicalStore()
    activation_policy = PersonalMemoryActivationPolicy()

    proposal = LibrarianProposal(
        content="The user prefers architecture diagrams.",
        proposed_domain="personal_memory",
        proposed_type="preference",
        confidence=0.97,
        importance=0.80,
    )

    validated = validator.validate(proposal)

    candidate = factory.create(
        validated,
        Provenance(
            source_id="conversation-002",
            source_type="conversation",
            pipeline_type="conversation_extraction",
            extraction_run_id="run-003",
        ),
    )

    artifact = canonical_store.create_from_candidate(candidate)

    denied = activation_policy.evaluate(
        artifact,
        user_consent=False,
    )

    allowed = activation_policy.evaluate(
        artifact,
        user_consent=True,
    )

    assert denied.allowed is False
    assert allowed.allowed is True


def test_confidence_does_not_override_validation() -> None:
    validator = ProposalValidator()

    proposal = LibrarianProposal(
        content="High confidence does not grant authority.",
        proposed_domain="forbidden_domain",
        proposed_type="fact",
        confidence=1.00,
        importance=1.00,
    )

    try:
        validator.validate(proposal)
    except ProposalValidationError:
        pass
    else:
        raise AssertionError(
            "confidence incorrectly bypassed validation"
        )


def test_inactive_artifact_is_not_retrieval_eligible() -> None:
    validator = ProposalValidator()
    factory = CandidateFactory()
    canonical_store = CanonicalStore()
    retrieval_policy = RetrievalEligibilityPolicy()

    proposal = LibrarianProposal(
        content="Retrieval depends on canonical lifecycle state.",
        proposed_domain="knowledge",
        proposed_type="concept",
        confidence=0.95,
        importance=0.85,
    )

    validated = validator.validate(proposal)

    candidate = factory.create(
        validated,
        Provenance(
            source_id="document-001",
            source_type="document",
            pipeline_type="verified_research",
            extraction_run_id="run-004",
        ),
    )

    artifact = canonical_store.create_from_candidate(candidate)

    decision = retrieval_policy.evaluate(artifact)

    assert decision.allowed is False


def test_derived_index_reflects_canonical_state() -> None:
    validator = ProposalValidator()
    factory = CandidateFactory()
    canonical_store = CanonicalStore()
    retrieval_policy = RetrievalEligibilityPolicy()
    derived_index = DerivedIndex()

    proposal = LibrarianProposal(
        content="The index reflects canonical state.",
        proposed_domain="knowledge",
        proposed_type="concept",
        confidence=0.98,
        importance=0.90,
    )

    validated = validator.validate(proposal)

    candidate = factory.create(
        validated,
        Provenance(
            source_id="document-002",
            source_type="document",
            pipeline_type="verified_research",
            extraction_run_id="run-005",
        ),
    )

    artifact = canonical_store.create_from_candidate(candidate)

    canonical_store.set_active(
        artifact.artifact_id,
        True,
    )

    decision = retrieval_policy.evaluate(artifact)

    canonical_store.set_retrieval_eligible(
        artifact.artifact_id,
        decision.allowed,
    )

    derived_index.sync(artifact)

    assert derived_index.get(artifact.artifact_id) is not None

    canonical_store.set_active(
        artifact.artifact_id,
        False,
    )

    derived_index.sync(artifact)

    assert derived_index.get(artifact.artifact_id) is None