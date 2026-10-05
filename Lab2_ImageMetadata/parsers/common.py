from pathlib import Path
from metadata import ImageMetadata

def base(path, fmt):
    return ImageMetadata(path=str(path), file_name=Path(path).name, format=fmt)

def damaged(m, text="Файл поврежден"):
    m.status = text
    m.ok = False
    return m

def finish(m):
    m.status = "OK"
    m.ok = True
    return m
