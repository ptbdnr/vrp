from datastore.node_manager import NodeManager
from schemas.route import Route
from utils.logger import Logger


class NaiveSequencer:
    """Class for naive sequencing algorithm."""

    logger: Logger
    node_manager: NodeManager

    def __init__(
            self,
            logger: Logger,
            node_manager: NodeManager,
        ) -> None:
        """Initialise the instance."""
        self.logger = logger
        self.node_manager = node_manager

    def optimise(self) -> Route:
        """Perform naive sequencing to create a route."""
        all_nodes = self.node_manager.all_nodes()
        if not all_nodes:
            self.logger.warning("No nodes available for optimisation.")
            return Route(nodes=[])
        origin = all_nodes[0]
        destination = all_nodes[-1]
        even_indexed_nodes = [node for index, node in enumerate(all_nodes[1:-1]) if index % 2 == 0]
        even_indexed_nodes.sort(key=lambda node: node.id, reverse=True)
        odd_indexed_nodes = [node for index, node in enumerate(all_nodes[1:-1]) if index % 2 != 0]
        sequenced_nodes = [origin, *even_indexed_nodes, *odd_indexed_nodes, destination]
        return Route(name="naive", sequence=sequenced_nodes)
