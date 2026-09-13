from librarian_pattern.index import DerivedIndex
from librarian_pattern.librarian import MockLibrarian
from librarian_pattern.lifecycle import (
    CandidateFactory,
    CandidateStore,
    CanonicalStore,
)
from librarian_pattern.models import (
    LibrarianProposal,
    Provenance,
    Source,
)
from librarian_pattern.policies import (
    KnowledgeActivationPolicy,
    PersonalMemoryActivationPolicy,
    PromotionPolicy,
    RetrievalEligibilityPolicy,
)
from librarian_pattern.validation import (
    ProposalValidationError,
    ProposalValidator,
)


def section(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)


def print_decision(
    label: str,
    allowed: bool,
    reason: str,
) -> None:
    state = "ALLOWED" if allowed else "DENIED"
    print(f"{label}: {state} — {reason}")


def run_personal_memory_demo() -> None:
    section("1. Personal Memory — promotion is not activation")

    source = Source(
        source_id="conversation-001",
        content="The user prefers concise architecture diagrams.",
        source_type="conversation",
    )

    librarian = MockLibrarian(
        LibrarianProposal(
            content="The user prefers concise architecture diagrams.",
            proposed_domain="personal_memory",
            proposed_type="preference",
            confidence=0.96,
            importance=0.80,
            tags=("architecture", "preference"),
        )
    )

    validator = ProposalValidator()
    candidate_factory = CandidateFactory()
    candidate_store = CandidateStore()
    canonical_store = CanonicalStore()
    promotion_policy = PromotionPolicy(
        minimum_confidence=0.90
    )
    activation_policy = PersonalMemoryActivationPolicy()

    proposal = librarian.propose(source)
    print("Librarian produced proposal")

    validated = validator.validate(proposal)
    print("Deterministic validation passed")

    provenance = Provenance(
        source_id=source.source_id,
        source_type=source.source_type,
        pipeline_type="conversation_extraction",
        extraction_run_id="run-personal-memory-001",
    )

    candidate = candidate_factory.create(
        validated,
        provenance,
    )
    candidate_store.persist(candidate)

    print(f"Candidate persisted: {candidate.candidate_id}")

    decision = promotion_policy.evaluate(
        candidate.proposal.confidence
    )
    print_decision(
        "Promotion",
        decision.allowed,
        decision.reason,
    )

    if not decision.allowed:
        return

    artifact = canonical_store.create_from_candidate(
        candidate
    )

    print(
        f"Canonical artifact created: {artifact.artifact_id}"
    )
    print(
        "Active immediately after promotion: "
        f"{artifact.is_active}"
    )

    decision = activation_policy.evaluate(
        artifact,
        user_consent=False,
    )
    print_decision(
        "Activation without consent",
        decision.allowed,
        decision.reason,
    )

    decision = activation_policy.evaluate(
        artifact,
        user_consent=True,
    )
    print_decision(
        "Activation with consent",
        decision.allowed,
        decision.reason,
    )

    if decision.allowed:
        canonical_store.set_active(
            artifact.artifact_id,
            True,
        )

    print(
        f"Active after explicit consent: {artifact.is_active}"
    )


def run_knowledge_demo() -> None:
    section(
        "2. Knowledge — trusted provenance and derived retrieval state"
    )

    source = Source(
        source_id="document-042",
        content=(
            "Canonical state must remain authoritative "
            "over derived indexes."
        ),
        source_type="trusted_document",
    )

    librarian = MockLibrarian(
        LibrarianProposal(
            content=(
                "Canonical state must remain authoritative "
                "over derived indexes."
            ),
            proposed_domain="knowledge",
            proposed_type="concept",
            confidence=0.97,
            importance=0.90,
            tags=("governance", "retrieval"),
        )
    )

    validator = ProposalValidator()
    candidate_factory = CandidateFactory()
    candidate_store = CandidateStore()
    canonical_store = CanonicalStore()

    promotion_policy = PromotionPolicy(
        minimum_confidence=0.90
    )

    activation_policy = KnowledgeActivationPolicy(
        trusted_pipeline_types={"verified_research"}
    )

    retrieval_policy = RetrievalEligibilityPolicy()
    derived_index = DerivedIndex()

    proposal = librarian.propose(source)
    print("Librarian produced proposal")

    validated = validator.validate(proposal)
    print("Deterministic validation passed")

    provenance = Provenance(
        source_id=source.source_id,
        source_type=source.source_type,
        pipeline_type="verified_research",
        extraction_run_id="run-knowledge-001",
    )

    candidate = candidate_factory.create(
        validated,
        provenance,
    )
    candidate_store.persist(candidate)

    print(f"Candidate persisted: {candidate.candidate_id}")

    decision = promotion_policy.evaluate(
        candidate.proposal.confidence
    )
    print_decision(
        "Promotion",
        decision.allowed,
        decision.reason,
    )

    if not decision.allowed:
        return

    artifact = canonical_store.create_from_candidate(
        candidate
    )

    print(
        f"Canonical artifact created: {artifact.artifact_id}"
    )

    decision = activation_policy.evaluate(artifact)
    print_decision(
        "Knowledge activation",
        decision.allowed,
        decision.reason,
    )

    if decision.allowed:
        canonical_store.set_active(
            artifact.artifact_id,
            True,
        )

    decision = retrieval_policy.evaluate(artifact)
    print_decision(
        "Retrieval eligibility",
        decision.allowed,
        decision.reason,
    )

    canonical_store.set_retrieval_eligible(
        artifact.artifact_id,
        decision.allowed,
    )

    indexed = derived_index.sync(artifact)

    print(
        "Indexed after eligibility decision: "
        f"{indexed is not None}"
    )

    # Canonical state changes first.
    # The derived index merely follows that authoritative state.
    canonical_store.set_active(
        artifact.artifact_id,
        False,
    )
    derived_index.sync(artifact)

    print(
        "Indexed after canonical deactivation: "
        f"{derived_index.get(artifact.artifact_id) is not None}"
    )


def run_invalid_proposal_demo() -> None:
    section(
        "3. Invalid Proposal — proposal is not candidate"
    )

    source = Source(
        source_id="external-999",
        content=(
            "An untrusted source proposes "
            "an unsupported domain."
        ),
        source_type="external",
    )

    librarian = MockLibrarian(
        LibrarianProposal(
            content="This should never become a candidate.",
            proposed_domain="system_authority",
            proposed_type="fact",
            confidence=0.99,
            importance=0.99,
            tags=("invalid",),
        )
    )

    validator = ProposalValidator()
    candidate_factory = CandidateFactory()
    candidate_store = CandidateStore()

    proposal = librarian.propose(source)

    try:
        validated = validator.validate(proposal)

    except ProposalValidationError as exc:
        print(
            f"Validation rejected proposal: {exc}"
        )
        print("Candidate created: False")
        return

    # This path should never be reached in this example.
    candidate = candidate_factory.create(
        validated,
        Provenance(
            source_id=source.source_id,
            source_type=source.source_type,
            pipeline_type="external_extraction",
            extraction_run_id="run-invalid-001",
        ),
    )

    candidate_store.persist(candidate)
    print("Candidate created: True")


def main() -> None:
    print("The Librarian Pattern — Reference Demo")
    print(
        "Probabilistic interpretation, "
        "deterministic authority."
    )

    run_personal_memory_demo()
    run_knowledge_demo()
    run_invalid_proposal_demo()


if __name__ == "__main__":
    main()