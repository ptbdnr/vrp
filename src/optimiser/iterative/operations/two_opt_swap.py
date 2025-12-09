from random import SystemRandom

from eval.route_eval import RouteEvaluator
from optimiser.iterative.operations.operation import Operation
from schemas.route import Route
from utils.logger import Logger

MIN_ROUTE_LENGTH = 4


class TwoOptSwap(Operation):
    """Class for two-opt swap operation.

    The 2-opt swap reverses a segment of the route to potentially reduce crossings.

    procedure 2optSwap(route, v1, v2) {
        1. take route[0] to route[v1] and add them in order to new_route
        2. take route[v1+1] to route[v2] and add them in reverse order to new_route
        3. take route[v2+1] to route[end] and add them in order to new_route
        return new_route;
    }
    """

    logger: Logger
    rnd_seed: int
    rnd_generator: SystemRandom
    route_eval: RouteEvaluator

    def __init__(
            self,
            route_eval: RouteEvaluator,
            logger: Logger | None = None,
            rnd_seed: int = 42,
        ) -> None:
        """Initialise the operation."""
        self.route_eval = route_eval
        self.rnd_seed = rnd_seed
        self.rnd_generator = SystemRandom(x=self.rnd_seed)
        self.logger = logger or Logger(__name__)

    def apply(
            self,
            route: Route,
            v1: int | None = None,
            v2: int | None = None,
            *,
            inplace: bool = False,
        ) -> Route:
        """Apply the 2-opt swap operation to the given route.

        Args:
            route: The route to apply the operation to
            v1: First index for the swap (if None, randomly selected)
            v2: Second index for the swap (if None, randomly selected)
            inplace: If True, modify the route in place; otherwise create a new route

        Returns:
            The modified route (either new or the same object if inplace=True)

        """
        route_length = len(route.sequence)

        # Need at least 4 nodes to perform 2-opt (start, 2 intermediate, end)
        if route_length < MIN_ROUTE_LENGTH:
            self.logger.warning(f"Route too short for 2-opt swap (length={route_length})")
            return route if inplace else route.copy()

        # Generate random indices if not provided
        # We exclude the first and last nodes (depot nodes)
        if v1 is None or v2 is None:
            v1 = self.rnd_generator.randint(1, route_length - 3)
            v2 = self.rnd_generator.randint(v1 + 1, route_length - 2)
        else:
            # Ensure v1 < v2
            if v1 > v2:
                v1, v2 = v2, v1
            # Validate indices
            if v1 < 1 or v2 >= route_length - 1 or v1 >= v2:
                self.logger.error(
                    f"Invalid indices for 2-opt: v1={v1}, v2={v2}, "
                    f"route_length={route_length}",
                )
                return route if inplace else route.copy()

        self.logger.debug(
            f"Applying 2-opt swap: reversing segment between indices {v1} and {v2}",
        )

        # Perform the 2-opt swap
        if inplace:
            # Reverse the segment in place
            route.sequence[v1:v2 + 1] = reversed(route.sequence[v1:v2 + 1])
            self.logger.debug(f"Applied 2-opt swap in place at indices [{v1}:{v2}]")
            return route

        # else: Create a new route with the reversed segment
        new_sequence = (
            route.sequence[:v1] +  # Keep first part as is
            list(reversed(route.sequence[v1:v2 + 1])) +  # Reverse middle segment
            route.sequence[v2 + 1:]  # Keep last part as is
        )
        new_route = Route(name=route.name, sequence=new_sequence, logger=self.logger)
        self.logger.debug(
            f"Created new route with 2-opt swap at indices [{v1}:{v2}]",
        )
        return new_route

    def apply_best_improvement(
            self,
            route: Route,
            *,
            only_valid: bool = True,
        ) -> Route:
        """Apply the best 2-opt improvement to the route.

        Tries all possible 2-opt swaps and returns the one with the best improvement.

        Args:
            route: The route to improve

        Returns:
            The improved route (or original if no improvement found)

        """
        best_route = route.copy()
        orig_value = best_value = self.route_eval.calculate_objective_value(route)
        improved = False

        route_length = len(route.sequence)

        # Try all possible 2-opt swaps
        for v1 in range(1, route_length - 2):
            for v2 in range(v1 + 1, route_length - 1):
                # Create new route with this swap
                new_route = self.apply(route, v1=v1, v2=v2, inplace=False)
                if only_valid and not self.route_eval.is_valid_route(route=new_route):
                    continue
                new_value = self.route_eval.calculate_objective_value(route=new_route)

                # Check if this is an improvement
                if new_value < best_value:
                    best_route = new_route
                    best_value = new_value
                    improved = True
                    self.logger.debug(
                        f"Found improvement with 2-opt [{v1}:{v2}]: "
                        f"value reduced to {new_value:.2f}",
                    )

        if improved:
            self.logger.info(
                f"Best 2-opt improvement found: "
                f"value reduced from {orig_value} to {best_value:.2f}",
            )
        else:
            self.logger.debug("No 2-opt improvement found")

        return best_route

    def apply_first_improvement(
            self,
            route: Route,
            *,
            only_valid: bool = True,
        ) -> Route:
        """Apply the first 2-opt improvement found.

        Stops as soon as an improvement is found (faster than best improvement).

        Args:
            route: The route to improve

        Returns:
            The improved route (or original if no improvement found)

        """
        curr_value = self.route_eval.calculate_objective_value(route)
        route_length = len(route.sequence)

        # Try 2-opt swaps until we find an improvement
        for v1 in range(1, route_length - 2):
            for v2 in range(v1 + 1, route_length - 1):
                # Create new route with this swap
                new_route = self.apply(route, v1=v1, v2=v2, inplace=False)
                if only_valid and not self.route_eval.is_valid_route(route=new_route):
                    continue
                new_value = self.route_eval.calculate_objective_value(route=new_route)

                # Return immediately if we find an improvement
                if new_value < curr_value:
                    self.logger.info(
                        f"First 2-opt improvement found at [{v1}:{v2}]: "
                        f"value reduced from {curr_value:.2f} to {new_value:.2f}",
                    )
                    return new_route

        self.logger.debug("No 2-opt improvement found")
        return route
