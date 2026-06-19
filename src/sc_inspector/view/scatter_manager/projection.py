from textual import on
from textual.containers import Container
from textual.widgets import Select
from textual.message import Message
from scanpy import AnnData


class ProjectionView(Container):
    class SelectedProjection(Message):
        def __init__(self, name: str, projection: str) -> None:
            super().__init__()
            self.projection = projection

    def __init__(self, id: str, anndata: AnnData):
        super().__init__(id=id)
        self.anndata = anndata
        self.options = self.buildOptions()

    def compose(self):
        yield Select(self.options)

    def buildOptions(self):
        projections = list(self.anndata.obsm)
        options = [
            (f"{projection} ({self.anndata.obsm[projection].shape[1]} dimensions)", projection)
            for projection in projections
        ]
        return options

    def _on_mount(self, event):
        self.query_one(Select).value = self.options[0][1]

    @on(Select.Changed)
    def on_select_change(self, event: Select.Changed):
        value = event.value
        self.post_message(self.SelectedProjection(projection=value))
