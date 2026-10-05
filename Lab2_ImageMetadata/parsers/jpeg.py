import struct
from binary_reader import BinaryReader
from parsers.common import base, damaged, finish

SOF={0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}
STANDALONE={0x01,0xD0,0xD1,0xD2,0xD3,0xD4,0xD5,0xD6,0xD7,0xD8,0xD9}

def has_eoi(r):
    if r.size<2: return False
    window=min(r.size,65536); r.seek(r.size-window); data=r.read(window)
    return b"\xff\xd9" in data

def parse(path):
    m=base(path,"JPEG")
    try:
        with BinaryReader(path) as r:
            if r.size<4 or r.read(2)!=b"\xff\xd8": return damaged(m)
            width=height=precision=components=None; dpi=None; dqt=0
            while r.tell()<r.size:
                b=r.u8()
                if b!=0xFF: continue
                while r.tell()<r.size and (marker:=r.u8())==0xFF: pass
                if marker==0xD9: break
                if marker in STANDALONE: continue
                if r.tell()+2>r.size: return damaged(m)
                length=r.u16(">")
                if length<2 or length-2>r.size-r.tell(): return damaged(m)
                data=r.read(length-2)
                if marker in SOF and len(data)>=6:
                    precision=data[0]; height=int.from_bytes(data[1:3],"big"); width=int.from_bytes(data[3:5],"big"); components=data[5]
                elif marker==0xE0 and len(data)>=14 and data[:5]==b"JFIF\x00":
                    unit=data[7]; xd=int.from_bytes(data[8:10],"big"); yd=int.from_bytes(data[10:12],"big")
                    if unit==1 and xd and yd: dpi=(xd,yd)
                    elif unit==2 and xd and yd: dpi=(round(xd*2.54),round(yd*2.54))
                elif marker==0xDB:
                    dqt+=1
                elif marker==0xDA:
                    break
            if not width or not height or precision is None or not components or not has_eoi(r): return damaged(m)
            m.size=f"{width} × {height}"; m.dpi=f"{dpi[0]} × {dpi[1]}" if dpi else "Не задано"; m.depth=f"{precision*components} бит ({precision} бит/компоненту)"; m.compression="JPEG"
            m.details=f"Компонентов: {components}; DQT-сегментов: {dqt}"
            return finish(m)
    except (OSError, EOFError, ValueError): return damaged(m)
