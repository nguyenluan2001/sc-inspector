from sc_inspector.controller.app import ScInspectorApp
from .utils.parser import parser
from .utils.io import read_data
from rich.progress import Progress
import time
import os


def main():
    args = parser()
    anndata= None

    with Progress() as progress:
        _ = progress.add_task("Loading...", total=None)  
        anndata = read_data(args.filepath)
        while not anndata:
            time.sleep(0.01)
    app = ScInspectorApp(anndata=anndata)
    app.run()

if __name__ == "__main__":
    main()
