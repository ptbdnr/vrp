import matplotlib.pyplot as plt

from schemas.node import Node
from schemas.route import Route
from utils.logger import Logger


class PlotBuilder:
    """Builder class for plotting routes."""

    logger: Logger
    figure: plt.Figure
    nodes: list[Node]

    def __init__(
            self,
            nodes: list[Node],
            logger: Logger | None,
        ) -> None:
        """Initialize the PlotBuilder."""
        self.nodes = nodes
        self.logger = logger or Logger(__name__)
        self.figure = plt.figure(figsize=(10, 6))

    def route_to_file(
            self,
            route: Route,
            filepath: str,
            title: str | None = None,
        ) -> plt.Figure:
        """Rebuild the plot builder."""
        self._clear_plot()
        self._plot_nodes()
        self._plot_route(route=route)
        self._save_plot(
            filepath=filepath,
            title=title,
        )
        return self

    def _clear_plot(self) -> None:
        """Clear the current plot."""
        plt.clf()

    def _plot_nodes(self) -> None:
        """Plot the nodes."""
        x_coords = [node.x for node in self.nodes]
        y_coords = [node.y for node in self.nodes]

        plt.scatter(x_coords, y_coords, color="blue")
        for i, node in enumerate(self.nodes):
            plt.text(node.x, node.y, str(node.id))

    def _plot_route(self, route: Route) -> None:
        """Plot the given route."""
        x_coords = [node.x for node in route.sequence]
        y_coords = [node.y for node in route.sequence]

        plt.plot(x_coords, y_coords, color="red", marker="o")

    def _save_plot(
            self,
            filepath: str,
            title: str | None = None,
        ) -> None:
        """Save the plot to the specified filepath."""
        title = title or "Route Plot"
        plt.title(title)
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.grid()
        plt.savefig(filepath)
        plt.close()
