from dataclasses import dataclass
from typing import List

@dataclass
class SelectedMetadata:
    name:str 
    clusters: List[str]
    points: List[List[float]] 