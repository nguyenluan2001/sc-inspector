from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from sc_inspector.view.main.view import MainView


class ScInspectorApp(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def __init__(self, anndata):
        super().__init__()
        self.anndata = anndata

    def on_mount(self) -> ComposeResult:
        """Create child widgets for the app."""
        self.push_screen(MainView(self.anndata))


    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
