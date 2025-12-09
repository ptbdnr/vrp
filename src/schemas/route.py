from pydantic import BaseModel

from schemas.node import Node


class Route(BaseModel):
    """A class representing a route consisting of multiple nodes."""

    name: str
    sequence: list[Node]

    def __str__(self) -> str:
        """Get the route as a string representation.

        Returns:
            String in format "0-3-1-2-4-5"

        """
        return "-".join([str(node.id) for node in self.sequence])

    def __repr__(self) -> str:
        """Representation the route as a string."""
        return f"Route({self.__str__()})"

    def __len__(self) -> int:
        """Return the number of nodes in the route."""
        return len(self.sequence)

    def copy(self) -> "Route":
        """Create a deep copy of the route."""
        return Route(name=self.name, sequence=self.sequence.copy())
