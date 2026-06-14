from textual import on
from textual.containers import VerticalScroll
from textual.widgets import Static, Select, DataTable
from textual.message import Message
from scanpy import AnnData
from typing import List

from pandas.api.types import is_categorical_dtype
from pandas import DataFrame


class MetadataManagerView(VerticalScroll):

    class SelectedMetadata(Message):
        """Posted when a cluster row is selected in the DataTable."""
        def __init__(self, name: str, clusters: List[str], points:List[List[float]]) -> None:
            super().__init__()
            self.name = name
            self.clusters = clusters
            self.points = points

    def __init__(self, id:str, anndata:AnnData):
        super().__init__(id=id)
        self.anndata = anndata
        self.obs = anndata.obs
        self.metadata:List[str] = [
            (metadata, self.get_metadata_type(metadata, anndata.obs) ) for metadata in anndata.obs.columns
        ]
        self.selected_metadata_name: str = ""
        self._cluster_names: List[str] = []
        self._cluster_points: List[List[float]] = []


    def compose(self):
        yield Static("Metadata")
        options = [(f"({dtype}) {metadata}", metadata)for  metadata, dtype, in self.metadata]
        yield Select(options)
        # yield VerticalScroll()
        yield DataTable(
            cursor_type="row",
            zebra_stripes=True
        )


    # === Event handler ===
    @on(Select.Changed)
    def on_select_change(self, event:Select.Changed):
        value = event.value
        self.selected_metadata_name = value
        self.load_clusters()
        self.group_cluster_points()
        # CRITICAL: Create a NEW Message instance each time.
        # Re-posting the same Message object fails because Textual marks
        # messages as processed after delivery — subsequent post_message()
        # calls with the same instance are silently ignored.
        self.post_message(
            self.SelectedMetadata(
                name=self.selected_metadata_name,
                clusters=self._cluster_names.copy(),
                points=self._cluster_points.copy(),
            )
        )
    
    # === Helper ===
    @staticmethod
    def get_metadata_type(metadata:str, df:DataFrame)->str:
        if is_categorical_dtype(df[metadata]):
            return "Category"
        return "Numeric"
    
    def load_clusters(self):
        metadata = self.obs[self.selected_metadata_name]
        clusters = metadata.cat.categories.tolist()
        self._cluster_names = clusters.copy()
        n_cells = [len(metadata[metadata==cluster]) for cluster in clusters]
        cluster_rows = list(zip(clusters, n_cells))

        el = self.query_one(DataTable)
        table_cols = ('Cluster', '# cells')
        table_rows = [(cluster, n_cells) for cluster, n_cells in cluster_rows]

        el.clear(columns=True)
        el.add_columns(*table_cols)
        el.add_rows(table_rows)
    
    def group_cluster_points(self):
        metadata = self.obs[self.selected_metadata_name]
        obsm = self.anndata.obsm['X_umap']
        points = []

        for cluster in self._cluster_names:
            cluster_mask = metadata == cluster
            points.append(
                obsm[cluster_mask].tolist()
            )
        self._cluster_points = points

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        row_index = event.cursor_row
        if 0 <= row_index < len(self._cluster_names):
            cluster_name = self._cluster_names[row_index]
            self.post_message(
                self.SelectedMetadata(
                    name=self.selected_metadata_name,
                    clusters=[cluster_name],
                    points=[self._cluster_points[row_index]] if row_index < len(self._cluster_points) else [],
                )
            )
