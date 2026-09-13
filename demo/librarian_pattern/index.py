from .models import CanonicalArtifact, IndexedArtifact


class DerivedIndex:
    """
    In-memory derived retrieval index.

    The index reflects retrieval-eligible canonical state. It does not decide
    whether information is true, canonical, active, or eligible for retrieval.
    """

    def __init__(self) -> None:
        self._items: dict[str, IndexedArtifact] = {}

    def upsert(
        self,
        artifact: CanonicalArtifact,
    ) -> IndexedArtifact:
        if not artifact.retrieval_eligible:
            raise ValueError(
                "only retrieval-eligible canonical artifacts may be indexed"
            )

        indexed = IndexedArtifact(
            artifact_id=artifact.artifact_id,
            content=artifact.content,
            metadata={
                "domain": artifact.domain.value,
                "artifact_type": artifact.artifact_type,
            },
        )

        self._items[artifact.artifact_id] = indexed

        return indexed

    def delete(
        self,
        artifact_id: str,
    ) -> None:
        self._items.pop(artifact_id, None)

    def get(
        self,
        artifact_id: str,
    ) -> IndexedArtifact | None:
        return self._items.get(artifact_id)

    def sync(
        self,
        artifact: CanonicalArtifact,
    ) -> IndexedArtifact | None:
        """
        Synchronize derived retrieval state with canonical lifecycle state.
        """

        if artifact.retrieval_eligible:
            return self.upsert(artifact)

        self.delete(artifact.artifact_id)

        return None