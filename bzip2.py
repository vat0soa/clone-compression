import heapq
import struct
import sys

BLOC = 8192


def bwt(b):
    ordre = sorted(range(len(b)), key=lambda i: b[i:] + b[:i])
    return bytes(b[i - 1] for i in ordre), ordre.index(0)


def ibwt(dernier, k):
    ordre = sorted(range(len(dernier)), key=lambda i: dernier[i])
    out, i = bytearray(), ordre[k]
    for _ in dernier:
        out.append(dernier[i])
        i = ordre[i]
    return bytes(out)


def mtf(data, inverse=False):
    t, out = list(range(256)), bytearray()
    for x in data:
        i = x if inverse else t.index(x)
        out.append(t[i] if inverse else i)
        t.insert(0, t.pop(i))
    return bytes(out)


def huffman(freq):
    tas = [(f, s, s) for s, f in enumerate(freq) if f]
    if len(tas) == 1:
        return {tas[0][2]: "0"}
    heapq.heapify(tas)
    n = 256
    while len(tas) > 1:
        a, b = heapq.heappop(tas), heapq.heappop(tas)
        heapq.heappush(tas, (a[0] + b[0], n, (a[2], b[2])))
        n += 1
    table = {}

    def parcours(noeud, code=""):
        if isinstance(noeud, int):
            table[noeud] = code
        else:
            parcours(noeud[0], code + "0")
            parcours(noeud[1], code + "1")

    parcours(tas[0][2])
    return table


def compress(src, dst):
    data = open(src, "rb").read()
    with open(dst, "wb") as f:
        f.write(struct.pack(">I", len(data)))
        for i in range(0, len(data), BLOC):
            dernier, k = bwt(data[i:i + BLOC])
            m = mtf(dernier)
            freq = [m.count(c) for c in range(256)]
            table = huffman(freq)
            bits = "".join(table[x] for x in m)
            bits += "0" * (-len(bits) % 8)
            payload = int(bits, 2).to_bytes(len(bits) // 8, "big")
            f.write(struct.pack(">III256H", len(m), k, len(payload), *freq) + payload)


def decompress(src, dst):
    blob = open(src, "rb").read()
    total, pos, out = struct.unpack(">I", blob[:4])[0], 4, bytearray()
    while len(out) < total:
        n, k, taille, *freq = struct.unpack(">III256H", blob[pos:pos + 524])
        payload = blob[pos + 524:pos + 524 + taille]
        pos += 524 + taille
        inverse = {c: s for s, c in huffman(freq).items()}
        bits = bin(int.from_bytes(payload, "big"))[2:].zfill(taille * 8)
        m, cur = bytearray(), ""
        for bit in bits:
            cur += bit
            if cur in inverse:
                m.append(inverse[cur])
                cur = ""
                if len(m) == n:
                    break
        out += ibwt(mtf(bytes(m), True), k)
    open(dst, "wb").write(out)


if __name__ == "__main__" and len(sys.argv) == 4 and sys.argv[1] in ("compress", "decompress"):
    (compress if sys.argv[1] == "compress" else decompress)(sys.argv[2], sys.argv[3])
elif __name__ == "__main__":
    print("Usage : python bzip2.py compress|decompress entree sortie")
