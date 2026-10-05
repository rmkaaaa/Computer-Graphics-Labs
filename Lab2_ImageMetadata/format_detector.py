from pathlib import Path
from metadata import ImageMetadata
from parsers import bmp,png,jpeg,gif,tiff,pcx

PARSERS={"BMP":bmp.parse,"PNG":png.parse,"JPEG":jpeg.parse,"GIF":gif.parse,"TIFF":tiff.parse,"PCX":pcx.parse}
EXTS={"BMP":{'.bmp'},"PNG":{'.png'},"JPEG":{'.jpg','.jpeg','.jpe'},"GIF":{'.gif'},"TIFF":{'.tif','.tiff'},"PCX":{'.pcx'}}

def detect(path):
    try:
        with open(path,"rb",buffering=0) as f: head=f.read(16)
    except OSError:
        return None
    if head.startswith(b"BM"): return "BMP"
    if head.startswith(b"\x89PNG\r\n\x1a\n"): return "PNG"
    if head.startswith(b"\xff\xd8"): return "JPEG"
    if head.startswith((b"GIF87a",b"GIF89a")): return "GIF"
    if head.startswith((b"II*\x00",b"MM\x00*")): return "TIFF"
    if len(head)>=4 and head[0]==0x0A and head[2] in (0,1) and head[3] in (1,2,4,8): return "PCX"
    return None

def parse_file(path):
    fmt=detect(path)
    if not fmt:
        return ImageMetadata(path=str(path),file_name=Path(path).name,status="Неверная сигнатура / неподдерживаемый файл")
    m=PARSERS[fmt](path)
    ext=Path(path).suffix.lower()
    if m.ok and ext not in EXTS[fmt]: m.status="OK, расширение не соответствует содержимому"
    return m
