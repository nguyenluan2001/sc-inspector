import scanpy as sc
def read_data(path:str)->sc.AnnData:
    return sc.read(path, backed="r")
