import struct
import sys


class Codeur:
    def __init__(self, data=None):
        self.dec = data is not None
        self.range = 0xFFFFFFFF
        if self.dec:
            self.data, self.pos = data, 5
            self.code = int.from_bytes(data[1:5], "big")
        else:
            self.low, self.cache, self.taille, self.out = 0, 0, 1, bytearray()

    def decaler(self):
        if (self.low & 0xFFFFFFFF) < 0xFF000000 or self.low >> 32:
            retenue, t = self.low >> 32, self.cache
            while True:
                self.out.append((t + retenue) & 0xFF)
                t = 0xFF
                self.taille -= 1
                if self.taille == 0:
                    break
            self.cache = (self.low >> 24) & 0xFF
        self.taille += 1
        self.low = (self.low & 0xFFFFFF) << 8

    def normaliser(self):
        while self.range < 1 << 24:
            self.range = (self.range << 8) & 0xFFFFFFFF
            if self.dec:
                octet = self.data[self.pos] if self.pos < len(self.data) else 0
                self.pos += 1
                self.code = ((self.code << 8) | octet) & 0xFFFFFFFF
            else:
                self.decaler()

    def bit(self, probs, i, b=0):
        p = probs[i]
        borne = (self.range >> 11) * p
        if self.dec:
            b = int(self.code >= borne)
        if b == 0:
            self.range = borne
            probs[i] = p + ((2048 - p) >> 5)
        else:
            if self.dec:
                self.code -= borne
            else:
                self.low += borne
            self.range -= borne
            probs[i] = p - (p >> 5)
        self.normaliser()
        return b

    def direct(self, v, n):
        r = 0
        for k in range(n - 1, -1, -1):
            self.range >>= 1
            if self.dec:
                b = int(self.code >= self.range)
                if b:
                    self.code -= self.range
            else:
                b = (v >> k) & 1
                if b:
                    self.low += self.range
            r = (r << 1) | b
            self.normaliser()
        return r

    def arbre(self, probs, n, v=0):
        m = 1
        for k in range(n - 1, -1, -1):
            m = (m << 1) | self.bit(probs, m, (v >> k) & 1)
        return m - (1 << n)

    def fin(self):
        for _ in range(5):
            self.decaler()
        return bytes(self.out)


def modeles():
    return [1024] * 2, [[1024] * 256 for _ in range(8)], [1024] * 256, [1024] * 32


def compress_bytes(data):
    n, rc = len(data), Codeur()
    est_copie, lit, longueur, dist = modeles()
    tete, prec = {}, [-1] * n

    def ajouter(p):
        cle = data[p:p + 3]
        if len(cle) == 3:
            prec[p], tete[cle] = tete.get(cle, -1), p

    i, etat = 0, 0
    while i < n:
        meilleur, pos_m = 0, 0
        pos, essais = tete.get(data[i:i + 3], -1), 0
        while pos >= 0 and essais < 24 and i - pos <= 1 << 18:
            l = 0
            while l < min(258, n - i) and data[pos + l] == data[i + l]:
                l += 1
            if l > meilleur:
                meilleur, pos_m = l, pos
            pos, essais = prec[pos], essais + 1
        if meilleur >= 3:
            rc.bit(est_copie, etat, 1)
            rc.arbre(longueur, 8, meilleur - 3)
            d = i - pos_m - 1
            nb = d.bit_length()
            rc.arbre(dist, 5, nb)
            if nb > 1:
                rc.direct(d & ((1 << (nb - 1)) - 1), nb - 1)
            for j in range(meilleur):
                ajouter(i + j)
            i, etat = i + meilleur, 1
        else:
            rc.bit(est_copie, etat, 0)
            rc.arbre(lit[data[i - 1] >> 5 if i else 0], 8, data[i])
            ajouter(i)
            i, etat = i + 1, 0
    return rc.fin()


def decompress_bytes(blob, total):
    rc, out, etat = Codeur(blob), bytearray(), 0
    est_copie, lit, longueur, dist = modeles()
    while len(out) < total:
        if rc.bit(est_copie, etat) == 0:
            out.append(rc.arbre(lit[out[-1] >> 5 if out else 0], 8))
            etat = 0
        else:
            l = rc.arbre(longueur, 8) + 3
            nb = rc.arbre(dist, 5)
            d = nb if nb <= 1 else (1 << (nb - 1)) | rc.direct(0, nb - 1)
            debut = len(out) - d - 1
            for k in range(l):
                out.append(out[debut + k])
            etat = 1
    return bytes(out)


def compress(src, dst):
    data = open(src, "rb").read()
    open(dst, "wb").write(struct.pack(">I", len(data)) + compress_bytes(data))


def decompress(src, dst):
    blob = open(src, "rb").read()
    open(dst, "wb").write(decompress_bytes(blob[4:], struct.unpack(">I", blob[:4])[0]))


if __name__ == "__main__" and len(sys.argv) == 4 and sys.argv[1] in ("compress", "decompress"):
    (compress if sys.argv[1] == "compress" else decompress)(sys.argv[2], sys.argv[3])
elif __name__ == "__main__":
    print("Usage : python lzma.py compress|decompress entree sortie")
