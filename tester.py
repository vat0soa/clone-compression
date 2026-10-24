import contextlib
import io
import os
import shutil
import sys
import tempfile
import time

import importlib

import bzip2
import lzma

sevenzip = importlib.import_module("7zip")


def identiques(a, b):
    return open(a, "rb").read() == open(b, "rb").read()


def tester_bzip2(src, tmp):
    archive, retour = os.path.join(tmp, "a.bz"), os.path.join(tmp, "retour")
    debut = time.time()
    bzip2.compress(src, archive)
    duree = time.time() - debut
    bzip2.decompress(archive, retour)
    return os.path.getsize(archive), identiques(src, retour), duree


def tester_lzma(src, tmp):
    archive, retour = os.path.join(tmp, "a.lz"), os.path.join(tmp, "retour")
    debut = time.time()
    lzma.compress(src, archive)
    duree = time.time() - debut
    lzma.decompress(archive, retour)
    return os.path.getsize(archive), identiques(src, retour), duree


def tester_sevenzip(src, tmp):
    nom = os.path.basename(src)
    copie = os.path.join(tmp, nom)
    shutil.copy(src, copie)
    archive, dossier = os.path.join(tmp, "a.msz"), os.path.join(tmp, "sortie")
    ancien = os.getcwd()
    os.chdir(tmp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            debut = time.time()
            sevenzip.creer(archive, [nom])
            duree = time.time() - debut
            sevenzip.extraire(archive, dossier)
    finally:
        os.chdir(ancien)
    return os.path.getsize(archive), identiques(src, os.path.join(dossier, nom)), duree


OUTILS = [("bzip2", tester_bzip2), ("lzma", tester_lzma), ("7-zip", tester_sevenzip)]


def main(fichiers):
    print(f"{'Fichier':<22}{'Outil':<8}{'Avant':>10}{'Après':>10}{'Gain':>9}{'Temps':>9}  Intact")
    print("-" * 78)
    for src in fichiers:
        src = os.path.abspath(src)
        avant = os.path.getsize(src)
        for nom, fonction in OUTILS:
            with tempfile.TemporaryDirectory() as tmp:
                apres, ok, duree = fonction(src, tmp)
            gain = (1 - apres / avant) * 100 if avant else 0
            print(f"{os.path.basename(src)[:21]:<22}{nom:<8}{avant:>10}{apres:>10}{gain:>8.1f}%{duree:>8.1f}s  {'oui' if ok else 'NON'}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python tester.py fichier1 fichier2 ...")
    else:
        main(sys.argv[1:])
