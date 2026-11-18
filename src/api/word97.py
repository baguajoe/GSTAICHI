"""
The text of an old Word file (.doc, Word 97 to 2003), in plain Python, for the admin's Bulk import.

Render cannot install LibreOffice or antiword, so this reads the file directly: the OLE2 container, then the
Word "piece table" that says where each run of text is. It keeps the words and the paragraphs only. Bold,
italics and Word's automatic list numbers ("I.", "A.") are not kept; for those, save the file as .docx first.

paragraphs(data) -> ["first paragraph", "second paragraph", ...]
"""
import struct

OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
END_OF_CHAIN = 0xFFFFFFFE
FREE = 0xFFFFFFFF
MAX_SECTORS = 1_000_000


class DocReadError(Exception):
    """Plain-English reason the .doc file cannot be read."""


class _Ole:
    def __init__(self, data):
        if data[:8] != OLE_SIGNATURE or len(data) < 512:
            raise DocReadError("This does not look like a Word .doc file.")
        self.data = data
        self.sector_size = 1 << struct.unpack_from("<H", data, 0x1E)[0]
        self.mini_size = 1 << struct.unpack_from("<H", data, 0x20)[0]
        first_dir, = struct.unpack_from("<I", data, 0x30)
        self.mini_cutoff, = struct.unpack_from("<I", data, 0x38)
        first_minifat, num_minifat = struct.unpack_from("<II", data, 0x3C)
        first_difat, num_difat = struct.unpack_from("<II", data, 0x44)

        difat = [s for s in struct.unpack_from("<109I", data, 0x4C) if s < END_OF_CHAIN - 2]
        sector, seen = first_difat, 0
        while sector < END_OF_CHAIN - 2 and seen < num_difat:
            entries = struct.unpack_from(f"<{self.sector_size // 4}I", self._sector(sector))
            difat.extend(s for s in entries[:-1] if s < END_OF_CHAIN - 2)
            sector, seen = entries[-1], seen + 1

        self.fat = []
        for s in difat:
            self.fat.extend(struct.unpack_from(f"<{self.sector_size // 4}I", self._sector(s)))

        directory = self._chain(first_dir, self.fat, self._sector)
        self.entries = {}
        root = None
        for i in range(len(directory) // 128):
            raw = directory[i * 128:(i + 1) * 128]
            name_len, = struct.unpack_from("<H", raw, 0x40)
            kind = raw[0x42]
            if kind == 0:
                continue
            name = raw[:max(name_len - 2, 0)].decode("utf-16-le", "replace")
            start, size = struct.unpack_from("<II", raw, 0x74)
            if kind == 5:
                root = (start, size)
            elif kind == 2:
                self.entries[name] = (start, size)
        if root is None:
            raise DocReadError("This Word file is damaged (no root entry).")
        self.mini_stream = self._chain(root[0], self.fat, self._sector)[:root[1]]
        self.minifat = []
        if num_minifat:
            raw = self._chain(first_minifat, self.fat, self._sector)
            self.minifat = list(struct.unpack_from(f"<{len(raw) // 4}I", raw))

    def _sector(self, n):
        offset = (n + 1) * self.sector_size
        if offset + self.sector_size > len(self.data) + self.sector_size:
            raise DocReadError("This Word file is damaged (it is cut short).")
        return self.data[offset:offset + self.sector_size]

    def _mini_sector(self, n):
        return self.mini_stream[n * self.mini_size:(n + 1) * self.mini_size]

    @staticmethod
    def _chain(start, fat, read):
        out, sector, steps = [], start, 0
        while sector < END_OF_CHAIN - 2:
            if sector >= len(fat) or steps > MAX_SECTORS:
                raise DocReadError("This Word file is damaged (broken sector chain).")
            out.append(read(sector))
            sector, steps = fat[sector], steps + 1
        return b"".join(out)

    def stream(self, name):
        if name not in self.entries:
            return None
        start, size = self.entries[name]
        if size < self.mini_cutoff:
            return self._chain(start, self.minifat, self._mini_sector)[:size]
        return self._chain(start, self.fat, self._sector)[:size]


def _main_text(data):
    ole = _Ole(data)
    word = ole.stream("WordDocument")
    if not word or len(word) < 0x1A6 + 4:
        raise DocReadError("This does not look like a Word .doc file.")
    ident, nfib = struct.unpack_from("<HH", word, 0)
    if ident != 0xA5EC:
        raise DocReadError("This does not look like a Word .doc file.")
    if nfib < 101:
        raise DocReadError("This Word file is too old (Word 95 or earlier). Please save it again as .docx.")
    flags, = struct.unpack_from("<H", word, 0x0A)
    if flags & 0x0100:
        raise DocReadError("This Word file is password protected. Please remove the password and try again.")
    table = ole.stream("1Table" if flags & 0x0200 else "0Table")
    if table is None:
        raise DocReadError("This Word file is damaged (no table stream).")
    ccp_text, = struct.unpack_from("<I", word, 0x4C)
    fc_clx, lcb_clx = struct.unpack_from("<II", word, 0x1A2)
    clx = table[fc_clx:fc_clx + lcb_clx]

    i = 0
    while i < len(clx) and clx[i] == 0x01:  # Prc: formatting we do not need
        cb, = struct.unpack_from("<h", clx, i + 1)
        i += 3 + cb
    if i >= len(clx) or clx[i] != 0x02:
        raise DocReadError("This Word file is damaged (no text table).")
    lcb, = struct.unpack_from("<I", clx, i + 1)
    plc = clx[i + 5:i + 5 + lcb]
    count = (len(plc) - 4) // 12
    cps = struct.unpack_from(f"<{count + 1}I", plc, 0)
    out, total = [], 0
    for n in range(count):
        if total >= ccp_text:
            break
        fc, = struct.unpack_from("<I", plc, (count + 1) * 4 + n * 8 + 2)
        length = min(cps[n + 1] - cps[n], ccp_text - total)
        if fc & 0x40000000:
            start = (fc & ~0x40000000) // 2
            out.append(word[start:start + length].decode("cp1252", "replace"))
        else:
            out.append(word[fc:fc + 2 * length].decode("utf-16-le", "replace"))
        total += length
    return "".join(out)


def _strip_fields(text):
    """Fields (page numbers, links, tables of contents) are \x13 code \x14 result \x15: keep only the result."""
    out, stack = [], []  # stack: True while inside a field's code part
    for ch in text:
        if ch == "\x13":
            stack.append(True)
        elif ch == "\x14":
            if stack:
                stack[-1] = False
        elif ch == "\x15":
            if stack:
                stack.pop()
        elif not any(stack):
            out.append(ch)
    return "".join(out)


def paragraphs(data):
    text = _strip_fields(_main_text(data))
    text = text.replace("\x1e", "-").replace("\x1f", "").replace("\xa0", " ")
    text = text.replace("\x0b", "\n").replace("\x07", "\r").replace("\x0c", "\r").replace("\t", " ")
    text = "".join(ch for ch in text if ch in "\r\n" or ord(ch) >= 32)
    out = []
    for p in text.split("\r"):
        lines = [" ".join(l.split()) for l in p.split("\n")]
        p = "\n".join(l for l in lines if l)
        if p:
            out.append(p)
    return out
