from typing import Protocol

from .models import LibrarianProposal, Source


class Librarian(Protocol):
    """
    Probabilistic interpretation boundary.

    A Librarian may interpret source material and propose structured
    information. It has no authority to validate, persist, promote,
    activate, or index anything.
    """

    def propose(self, source: Source) -> LibrarianProposal:
        ...


class MockLibrarian:
    """
    Deterministic stand-in for an LLM.

    The demo intentionally does not require an API key or local model.
    A real LLM adapter would implement the same Librarian protocol.
    """

    def __init__(self, proposal: LibrarianProposal) -> None:
        self._proposal = proposal

    def propose(self, source: Source) -> LibrarianProposal:
        # The source is accepted because a real Librarian would interpret it.
        # The mock returns a predefined proposal so the demo stays reproducible.
        _ = source
        return self._proposal