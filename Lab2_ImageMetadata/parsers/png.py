import struct
from binary_reader import BinaryReader
from parsers.common import base, damaged, finish

def parse(path):
    m=base(path,"PNG")
    try:
        with BinaryReader(path) as r:
            if r.size < 33 or r.read(8) != b"\x89PNG\r\n\x1a\n": return damaged(m)
            width=height=bit_depth=color_type=None; dpi=None; found_iend=False; interlace=filter_method=compression_method=None
            while r.tell()+12 <= r.size:
                length=r.u32(">"); typ=r.read(4)
                if length > r.size-r.tell()-4: return damaged(m)
                data=r.read(length); r.read(4)
                if typ==b"IHDR":
                    if length != 13: return damaged(m)
                    width,height,bit_depth,color_type,compression_method,filter_method,interlace=struct.unpack(">IIBBBBB",data)
                elif typ==b"pHYs" and length==9:
                    x,y,unit=struct.unpack(">IIB",data)
                    if unit==1 and x and y: dpi=(round(x*0.0254),round(y*0.0254))
                elif typ==b"IEND":
                    if length != 0: return damaged(m)
                    found_iend=True; break
            if not found_iend or not width or not height or bit_depth is None or color_type not in (0,2,3,4,6): return damaged(m)
            channels={0:1,2:3,3:1,4:2,6:4}[color_type]
            m.size=f"{width} × {height}"; m.dpi=f"{dpi[0]} × {dpi[1]}" if dpi else "Не задано"
            m.depth=f"{bit_depth*channels} бит ({bit_depth} бит/канал)"; m.compression="Deflate"
            m.details=f"Color type: {color_type}; filter method: {filter_method}; interlace: {interlace}"
            return finish(m)
    except (OSError, EOFError, ValueError, struct.error): return damaged(m)
