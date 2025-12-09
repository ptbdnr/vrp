from abc import ABC, abstractmethod

from schemas.route import Route


class Operation(ABC):
    """Abstract base class for operations in an iterative optimiser."""

    @abstractmethod
    def apply(self, route: Route) -> Route:
        """Apply the operation to the given solution."""
        raise NotImplementedError

    @abstractmethod
    def apply_best_improvement(self, route: Route) -> Route:
        """Apply the operation and return the best improvement found."""
        raise NotImplementedError

    @abstractmethod
    def apply_first_improvement(self, route: Route) -> Route:
        """Apply the operation and return the first improvement found."""
        raise NotImplementedError
