from .models import Domain, LibrarianProposal, ValidatedProposal


class ProposalValidationError(ValueError):
    """Raised when a Librarian proposal violates deterministic system rules."""


class ProposalValidator:
    """
    Deterministically validates Librarian proposals.

    The validator owns the admissible taxonomy and structural constraints.
    It does not decide whether validated information is true, canonical,
    active, or retrieval-eligible.
    """

    _ALLOWED_TYPES: dict[Domain, set[str]] = {
        Domain.PERSONAL_MEMORY: {"preference", "fact"},
        Domain.KNOWLEDGE: {"fact", "concept"},
    }

    def validate(self, proposal: LibrarianProposal) -> ValidatedProposal:
        content = proposal.content.strip()
        if not content:
            raise ProposalValidationError("content must not be empty")

        try:
            domain = Domain(proposal.proposed_domain)
        except ValueError as exc:
            raise ProposalValidationError(
                f"unsupported domain: {proposal.proposed_domain!r}"
            ) from exc

        allowed_types = self._ALLOWED_TYPES[domain]
        if proposal.proposed_type not in allowed_types:
            raise ProposalValidationError(
                f"unsupported type {proposal.proposed_type!r} "
                f"for domain {domain.value!r}"
            )

        self._validate_score("confidence", proposal.confidence)
        self._validate_score("importance", proposal.importance)

        tags = tuple(tag.strip() for tag in proposal.tags if tag.strip())

        return ValidatedProposal(
            content=content,
            domain=domain,
            candidate_type=proposal.proposed_type,
            confidence=proposal.confidence,
            importance=proposal.importance,
            tags=tags,
        )

    @staticmethod
    def _validate_score(name: str, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ProposalValidationError(
                f"{name} must be between 0.0 and 1.0, got {value!r}"
            )