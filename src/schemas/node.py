from pydantic import BaseModel, ConfigDict


class Node(BaseModel):
    """A node."""

    model_config = ConfigDict(frozen=True)

    id: int
    x: float
    y: float

    def __hash__(self) -> int:
        """Make Node hashable for use in sets and dicts.

        Returns:
            Hash value based on node id, x, and y coordinates

        """
        return hash((self.id, self.x, self.y))
