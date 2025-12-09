from datastore.distance_manager import EuclidianDistanceManager
from datastore.edge_manager import EdgeManager
from datastore.node_manager import NodeManager
from schemas.route import Route
from utils.logger import Logger


class GreedySequencer:
    """Class for greedy optimisation algorithm."""

    logger: Logger
    node_manager: NodeManager
    edge_manager: EdgeManager
    distance_manager: EuclidianDistanceManager

    def __init__(
            self,
            logger: Logger,
            node_manager: NodeManager,
            edge_manager: EdgeManager,
            distance_manager: EuclidianDistanceManager,
        ) -> None:
        """Initialise the instance."""
        self.logger = logger
        self.node_manager = node_manager
        self.edge_manager = edge_manager
        self.distance_manager = distance_manager

    def optimise(self) -> Route:
        """Perform greedy optimisation to create a route."""

        all_nodes = self.node_manager.all_nodes()
        if not all_nodes:
            self.logger.warning("No nodes available for optimisation.")
            return Route(nodes=[])

        curr_node = all_nodes[0]  # Start at the depot
        route_nodes = [curr_node]
        unvisited_nodes = all_nodes[1:-1]  # Exclude start and end depot
        while unvisited_nodes:
            """Find the closest unvisited node."""
            closest_unvisited_nodes = self.edge_manager.neighbors(
                node_id=curr_node.id,
                candidates=unvisited_nodes,
                max_neighbors=len(unvisited_nodes),
                sort_by_distance=True,
                distance_manager=self.distance_manager,
            )
            closest_node = closest_unvisited_nodes[0] if closest_unvisited_nodes else None
            if closest_node is None:
                self.logger.debug("No more reachable unvisited nodes.")
                break
            route_nodes.append(closest_node)
            unvisited_nodes.remove(closest_node)
            curr_node = closest_node

        route_nodes.append(all_nodes[-1])  # End at the depot
        self.logger.debug(f"Optimised route with {len(route_nodes)} nodes.")
        return Route(name="greedy", sequence=route_nodes)
