from pathlib import Path
from typing import List

def list_style_name(root_path:str) -> List[str]:
    dir_path = Path("/path/to/directory")
    return [item.name for item in dir_path.iterdir()]