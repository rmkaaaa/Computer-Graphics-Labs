from binary_reader import BinaryReader
from parsers.common import base, damaged, finish

def parse(path):
    m = base(path, "BMP")
    try:
        with BinaryReader(path) as r:
            if r.size < 54 or r.read(2) != b"BM": return damaged(m)
            file_size = r.u32(); r.seek(10); pixel_offset = r.u32(); dib = r.u32()
            if dib < 40 or file_size > r.size or pixel_offset > r.size: return damaged(m)
            width = r.i32(); height_raw = r.i32(); planes = r.u16(); bpp = r.u16(); compression = r.u32()
            r.seek(38); xppm = r.i32(); yppm = r.i32(); r.seek(46); colors_used = r.u32()
            if width <= 0 or height_raw == 0 or planes != 1: return damaged(m)
            height = abs(height_raw)
            names = {0:"BI_RGB",1:"BI_RLE8",2:"BI_RLE4",3:"BI_BITFIELDS",4:"BI_JPEG",5:"BI_PNG",6:"BI_ALPHABITFIELDS"}
            colors = colors_used or ((1 << bpp) if bpp <= 8 else 0)
            m.size=f"{width} × {height}"; m.depth=f"{bpp} бит"; m.compression=names.get(compression,f"Код {compression}")
            m.dpi=f"{round(xppm*0.0254)} × {round(yppm*0.0254)}" if xppm>0 and yppm>0 else "Не задано"
            m.details=f"DIB: {dib} байт; смещение пикселей: {pixel_offset}; цветов палитры: {colors}"
            return finish(m)
    except (OSError, EOFError, ValueError, OverflowError): return damaged(m)
