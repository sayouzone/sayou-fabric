from sayou.core.base_component import BaseComponent

from .renderer.pyvis_renderer import PyVisRenderer
from .tracer.graph_tracer import GraphTracer


class VisualizerPipeline(BaseComponent):
    """
    The main facade for Sayou Visualization.

    It manages the internal Tracer (recording events) and Renderer (drawing graphs),
    providing a simple interface for the user.
    """

    component_name = "VisualizerPipeline"

    def __init__(self):
        super().__init__()
        self._tracer = GraphTracer()
        self._renderer = PyVisRenderer()

    def attach_to(self, target_pipeline: BaseComponent):
        """
        Connects this visualizer to a target pipeline (Connector, Refinery, etc.).
        """
        target_pipeline.add_callback(self._tracer)
        self._log(f"Visualizer attached to {target_pipeline.component_name}")

    def report(self, output_path: str = "report.html", **kwargs):
        """
        Generates the visualization report based on recorded events.
        """
        if self._tracer.graph.number_of_nodes() == 0:
            self._log("No events recorded. The graph is empty.", level="warning")
            return

        self._log(
            f"Generating report with {self._tracer.graph.number_of_nodes()} nodes..."
        )
        self._renderer.render(self._tracer.graph, output_path, **kwargs)
