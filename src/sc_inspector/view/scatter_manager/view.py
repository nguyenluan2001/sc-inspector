from ..metadata_manager.view import MetadataManagerView
from ..scatter_manager.projection import ProjectionView
from .projection import ProjectionView
from ...constant.color import COLOR_SCHEMA

from textual.containers import Container, Center
from textual.widgets import Static
from scanpy import AnnData
from rich.text import Text
import plotille


class ScatterManagerView(Container):
    def __init__(self, id: str, anndata: AnnData):
        self.anndata = anndata
        super().__init__(id=id)

    def compose(self):
        yield ProjectionView(id="projection_manager", anndata=self.anndata)

        yield Container(Static(id="scatter_plot"), id="scatter_container")

    def _on_mount(self, event):
        pass
        # self.update_plot(MetadataManagerView.SelectedMetadata(
        #     name="louvain",
        #     clusters=[],
        #     points=[]
        # ))

    def update_plot(
        self,
        selected_metadata: MetadataManagerView.SelectedMetadata,
        selected_projection: ProjectionView.SelectedProjection,
    ):
        print("update_plot ===", selected_metadata.name)

        fig = plotille.Figure()

        fig.height = int(self.size.height * 0.8)
        fig.color_mode = "rgb"
        fig.background = (0, 0, 0)
        fig.with_x_axis = False
        fig.with_y_axis = False
        fig.origin = False
        fig.x_formatter = lambda val, chars: f"{val:.2f}"
        fig.y_formatter = lambda val, chars: f"{val:.2f}"

        for i, cluster in enumerate(selected_metadata.clusters):
            # x, y = map(list,zip(*selected_metadata.points[i]))
            points = selected_metadata.points[i]
            x = [p[0] for p in points]
            y = [p[1] for p in points]
            fig.scatter(
                x, y, lc=COLOR_SCHEMA["category"]["cloudscape"][i], label=cluster, marker="⬤"
            )

        el = self.query_one("#scatter_plot", Static)
        # Clear old content first to reset virtual size, then set new content
        el.update("")
        el.update(Text.from_ansi(fig.show()))
        # Force the container to recalculate layout so old plot characters are cleared
        self.refresh(layout=True)
