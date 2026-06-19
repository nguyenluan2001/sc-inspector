from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Static
from textual.screen import Screen
from textual import on

from ..gene_manager.view import GeneManagerView
from ..metadata_manager.view import MetadataManagerView
from ..scatter_manager.view import ScatterManagerView
from ..scatter_manager.projection import ProjectionView


class MainView(Screen):
    CSS_PATH = [
        "../style/main.tcss",
        "../style/gene-manager.tcss",
        "../style/metadata-manager.tcss",
        "../style/scatter-manager.tcss",
    ]

    def __init__(self, anndata):
        super().__init__()
        self.anndata = anndata
        self.scatter_manager = None
        self.metadata_manager = None

    def compose(self) -> ComposeResult:
        self.scatter_manager = ScatterManagerView(
            id="scatter-manager",
            anndata=self.anndata,
        )
        self.metadata_manager = MetadataManagerView(
            id="metadata-manager",
            anndata=self.anndata,
        )
        yield Header()
        yield Horizontal(
            self.scatter_manager,
            Container(
                GeneManagerView(id="gene-manager", anndata=self.anndata),
                self.metadata_manager,
                id="right-panel",
            ),
            id="app",
        )

    @on(MetadataManagerView.SelectedMetadata)
    def on_metadata_selected(self, event: MetadataManagerView.SelectedMetadata):
        event.stop()  # Don't bubble further
        self.scatter_manager.update_plot(event)

    @on(ProjectionView.SelectedProjection)
    def on_projection_selected(self, event: ProjectionView.SelectedProjection):
        event.stop()  # Don't bubble further
        self.scatter_manager.update_plot(event)
