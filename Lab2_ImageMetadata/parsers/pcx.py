from binary_reader import BinaryReader
from parsers.common import base, damaged, finish

def parse(path):
    m=base(path,"PCX")
    try:
        with BinaryReader(path) as r:
            if r.size < 128 or r.u8()!=0x0A: return damaged(m)
            version=r.u8(); encoding=r.u8(); bpp=r.u8(); xmin=r.u16(); ymin=r.u16(); xmax=r.u16(); ymax=r.u16(); hdpi=r.u16(); vdpi=r.u16()
            r.seek(65); planes=r.u8(); bytes_per_line=r.u16(); palette_info=r.u16()
            width=xmax-xmin+1; height=ymax-ymin+1
            if width<=0 or height<=0 or encoding not in (0,1) or planes==0: return damaged(m)
            m.size=f"{width} × {height}"; m.dpi=f"{hdpi} × {vdpi}" if hdpi and vdpi else "Не задано"; m.depth=f"{bpp*planes} бит"; m.compression="RLE" if encoding==1 else "Без сжатия"
            m.details=f"PCX version: {version}; planes: {planes}; bits/plane: {bpp}; bytes/line: {bytes_per_line}; palette info: {palette_info}"
            return finish(m)
    except (OSError, EOFError, ValueError): return damaged(m)
