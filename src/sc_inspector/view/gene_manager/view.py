from textual import on
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Static,Select,SelectionList, Pretty, Input
from textual.widgets.selection_list import Selection
from scanpy import AnnData
from typing import List, Tuple, Dict

class GeneManagerView(VerticalScroll):

    def __init__(self, id:str, anndata:AnnData):
        super().__init__(id=id)
        self.genes:List[str] = anndata.var_names
        self.gene_hash: Dict[str, int] = {gene:i  for i, gene in enumerate(anndata.var_names)}
        self.selected_genes:List[str] = []


    def compose(self):
        yield Static("Query genes")
        yield Input(placeholder="Search gene")
        options = self._create_options(self.genes)

        yield SelectionList(*options)
        yield Pretty([])

    @on(Input.Changed)
    def on_input_change(self, event:Input.Changed):
        value = event.value
        # genes = filter(lambda x: x.starWidth(value), genes)
        genes = [gene for gene in self.genes if gene.lower().startswith(value.lower())]
        self.query_one(SelectionList).set_options(
            self._create_options(genes)
        )

    
    # === Selection ===
    def _create_options(self, genes:List[str])->List[Selection]:
        return  [Selection(gene, self.gene_hash[gene])for i, gene in enumerate(genes)]

    @on(SelectionList.SelectedChanged)
    def update_selected_view(self) -> None:
        self.query_one(Pretty).update(self.query_one(SelectionList).selected)
        self.selected_genes = self.query_one(SelectionList).selected
