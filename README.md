# Clone de bzip2, lzma et 7-zip

Examen de codage et traitement du signal.

- `bzip2.py` : BWT, puis Move-To-Front, puis Huffman
- `lzma.py` : LZ77 et codage par intervalles (range coder)
- `7zip.py` : archive de plusieurs fichiers, compressée avec lzma.py
- `tester.py` : compresse des fichiers avec les trois outils et affiche les gains

## Utilisation

```
python bzip2.py compress fichier.txt fichier.bz
python bzip2.py decompress fichier.bz fichier_restaure.txt

python lzma.py compress fichier.txt fichier.lz
python lzma.py decompress fichier.lz fichier_restaure.txt

python 7zip.py create archive.msz dossier fichier.txt
python 7zip.py list archive.msz
python 7zip.py extract archive.msz dossier_destination

python tester.py texte.txt audio.wav image.bmp video.mp4
```

Python 3 suffit, aucune bibliothèque à installer.
