import json
import os
import struct
import sys

from lzma import compress_bytes, decompress_bytes


def lire(archive):
    blob = open(archive, "rb").read()
    lt, lc = struct.unpack(">II", blob[:8])
    infos = json.loads(blob[8:8 + lt])
    return infos, decompress_bytes(blob[8 + lt:], lc)


def creer(archive, chemins):
    fichiers = []
    for c in chemins:
        if os.path.isdir(c):
            for dossier, _, noms in os.walk(c):
                fichiers += [os.path.join(dossier, n) for n in sorted(noms)]
        else:
            fichiers.append(c)
    infos, morceaux = [], []
    for f in fichiers:
        d = open(f, "rb").read()
        infos.append([os.path.normpath(f).replace(os.sep, "/"), len(d)])
        morceaux.append(d)
    corps = b"".join(morceaux)
    tete = json.dumps(infos).encode()
    open(archive, "wb").write(struct.pack(">II", len(tete), len(corps)) + tete + compress_bytes(corps))
    print(f"{len(fichiers)} fichier(s) : {len(corps)} -> {os.path.getsize(archive)} octets")


def extraire(archive, dest):
    infos, corps = lire(archive)
    racine, pos = os.path.abspath(dest), 0
    for nom, taille in infos:
        cible = os.path.abspath(os.path.join(racine, nom))
        if not cible.startswith(racine + os.sep):
            raise ValueError("Chemin refusé : " + nom)
        os.makedirs(os.path.dirname(cible), exist_ok=True)
        open(cible, "wb").write(corps[pos:pos + taille])
        pos += taille
        print("extrait :", nom)


def lister(archive):
    for nom, taille in lire(archive)[0]:
        print(f"{taille:>12}  {nom}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "create":
        creer(a[1], a[2:])
    elif len(a) == 3 and a[0] == "extract":
        extraire(a[1], a[2])
    elif len(a) == 2 and a[0] == "list":
        lister(a[1])
    else:
        print("Usage : python 7zip.py create|extract|list archive ...")
