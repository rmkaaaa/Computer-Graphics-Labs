import struct
from binary_reader import BinaryReader
from parsers.common import base, damaged, finish

SIZES={1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8}

def parse_values(r, endian, typ, count, raw, offset):
    size=SIZES.get(typ)
    if not size or count<0 or count>1000000 or size*count>16_000_000: raise ValueError
    total=size*count
    data=raw[:total] if total<=4 else _read_at(r,offset,total)
    prefix="<" if endian=="<" else ">"
    if typ==3: return list(struct.unpack(prefix+"H"*count,data))
    if typ==4: return list(struct.unpack(prefix+"I"*count,data))
    if typ==5:
        out=[]
        for i in range(count):
            a,b=struct.unpack(prefix+"II",data[i*8:i*8+8]); out.append(a/b if b else 0)
        return out
    if typ in (1,6,7): return list(data)
    return []

def _read_at(r, offset, count):
    pos=r.tell(); r.seek(offset); data=r.read(count); r.seek(pos); return data

def parse(path):
    m=base(path,"TIFF")
    try:
        with BinaryReader(path) as r:
            if r.size<8: return damaged(m)
            order=r.read(2)
            if order==b"II": endian="<"
            elif order==b"MM": endian=">"
            else: return damaged(m)
            if r.u16(endian)!=42: return damaged(m)
            ifd=r.u32(endian); visited=set(); tags={}; ifds=0
            while ifd and ifds<32:
                if ifd in visited or ifd+2>r.size: return damaged(m)
                visited.add(ifd); ifds+=1; r.seek(ifd); count=r.u16(endian)
                if count>4096 or r.tell()+count*12+4>r.size: return damaged(m)
                for _ in range(count):
                    tag=r.u16(endian); typ=r.u16(endian); n=r.u32(endian); raw=r.read(4); off=int.from_bytes(raw,"little" if endian=="<" else "big")
                    if tag in (256,257,258,259,277,282,283,296):
                        vals=parse_values(r,endian,typ,n,raw,off)
                        if vals: tags[tag]=vals
                ifd=r.u32(endian)
            width=int(tags.get(256,[0])[0]); height=int(tags.get(257,[0])[0]); bits=tags.get(258,[]); comp=int(tags.get(259,[1])[0]); spp=int(tags.get(277,[len(bits) or 1])[0])
            if not width or not height: return damaged(m)
            total=int(sum(bits)) if bits else 8*spp
            xr=float(tags.get(282,[0])[0]); yr=float(tags.get(283,[0])[0]); unit=int(tags.get(296,[2])[0])
            if unit==3: xr*=2.54; yr*=2.54
            elif unit!=2: xr=yr=0
            names={1:"Без сжатия",2:"CCITT 1D",3:"Group 3 Fax",4:"Group 4 Fax",5:"LZW",6:"JPEG old",7:"JPEG",8:"Deflate",32773:"PackBits"}
            m.size=f"{width} × {height}"; m.dpi=f"{round(xr)} × {round(yr)}" if xr>0 and yr>0 else "Не задано"; m.depth=f"{total} бит"; m.compression=names.get(comp,f"TIFF compression {comp}")
            m.details=f"Endian: {'Little' if endian=='<' else 'Big'}; SamplesPerPixel: {spp}; IFD обработано: {ifds}"
            return finish(m)
    except (OSError, EOFError, ValueError, struct.error, OverflowError): return damaged(m)
