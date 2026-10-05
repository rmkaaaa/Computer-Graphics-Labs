import os
import struct

class BinaryReader:
    def __init__(self, path):
        self.path = path
        self.file = open(path, "rb", buffering=0)
        self.size = os.fstat(self.file.fileno()).st_size

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def tell(self):
        return self.file.tell()

    def seek(self, offset, whence=0):
        if whence == 0 and not 0 <= offset <= self.size:
            raise ValueError("Некорректное смещение")
        self.file.seek(offset, whence)

    def read(self, count):
        if count < 0 or count > self.size - self.tell():
            raise EOFError("Недостаточно данных")
        data = self.file.read(count)
        if len(data) != count:
            raise EOFError("Недостаточно данных")
        return data

    def unpack(self, fmt, endian="<"):
        size = struct.calcsize(endian + fmt)
        return struct.unpack(endian + fmt, self.read(size))

    def u8(self): return self.unpack("B")[0]
    def u16(self, endian="<"): return self.unpack("H", endian)[0]
    def i16(self, endian="<"): return self.unpack("h", endian)[0]
    def u32(self, endian="<"): return self.unpack("I", endian)[0]
    def i32(self, endian="<"): return self.unpack("i", endian)[0]
