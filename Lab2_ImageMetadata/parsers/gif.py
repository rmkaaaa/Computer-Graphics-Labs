from binary_reader import BinaryReader
from parsers.common import base, damaged, finish

def parse(path):
    m=base(path,"GIF")
    try:
        with BinaryReader(path) as r:
            if r.size < 13: return damaged(m)
            sig=r.read(6)
            if sig not in (b"GIF87a",b"GIF89a"): return damaged(m)
            width=r.u16(); height=r.u16(); packed=r.u8(); bg=r.u8(); aspect=r.u8()
            gct=bool(packed&0x80); gct_bits=(packed&7)+1; gct_colors=1<<gct_bits if gct else 0
            if gct:
                r.read(3*gct_colors)
            image_bits=None; found_image=False; found_trailer=False
            while r.tell()<r.size:
                marker=r.u8()
                if marker==0x3B:
                    found_trailer=True; break
                if marker==0x2C:
                    if r.size-r.tell()<9: return damaged(m)
                    r.read(8); ip=r.u8(); lct=bool(ip&0x80); lct_bits=(ip&7)+1
                    if lct: r.read(3*(1<<lct_bits))
                    image_bits=lct_bits if lct else gct_bits
                    found_image=True
                    r.u8()
                    while True:
                        n=r.u8()
                        if n==0: break
                        r.read(n)
                elif marker==0x21:
                    r.u8()
                    while True:
                        n=r.u8()
                        if n==0: break
                        r.read(n)
                else: return damaged(m)
            if not width or not height or not found_image or not found_trailer: return damaged(m)
            m.size=f"{width} × {height}"; m.depth=f"{image_bits or 1} бит/пиксель"; m.compression="LZW"; m.dpi="Не задано"
            m.details=f"{sig.decode()}; глобальная палитра: {'да' if gct else 'нет'}; цветов: {gct_colors}; background index: {bg}; aspect: {aspect}"
            return finish(m)
    except (OSError, EOFError, ValueError): return damaged(m)
