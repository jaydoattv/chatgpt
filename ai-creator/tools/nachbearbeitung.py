#!/usr/bin/env python3
"""Nachbearbeitung für Posts: Zuschnitt, Instagram-Größe, feines Korn, JPEG ohne Metadaten.

Warum: ComfyUI-PNGs sind verlustfrei, rauschfrei und enthalten den kompletten
Workflow samt Prompt in den Metadaten. Echte Handyfotos sind JPEG-komprimiert,
leicht verrauscht und haben keine Generierungsdaten. Dieses Skript bringt die
Bilder in genau diesen Zustand. Es schärft bewusst NICHT nach.

Beispiele:
    python tools/nachbearbeitung.py ausgabe/runde1/final --out posts/
    python tools/nachbearbeitung.py bild.png --format 9:16 --korn 2.5 --out stories/

Benötigt: Pillow, numpy
"""

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

FORMATE = {"4:5": (4, 5), "9:16": (9, 16), "1:1": (1, 1), "original": None}
ENDUNGEN = {".png", ".jpg", ".jpeg", ".webp"}


def zuschneiden(bild, verhaeltnis):
    if verhaeltnis is None:
        return bild
    rw, rh = verhaeltnis
    b, h = bild.size
    if b * rh > h * rw:  # zu breit
        neue_b = round(h * rw / rh)
        links = (b - neue_b) // 2
        return bild.crop((links, 0, links + neue_b, h))
    neue_h = round(b * rh / rw)
    oben = (h - neue_h) // 2
    return bild.crop((0, oben, b, oben + neue_h))


def korn(arr, staerke, rng):
    """Monochromes, leicht weichgezeichnetes Rauschen, in den Mitteltönen am stärksten."""
    if staerke <= 0:
        return arr
    h, b, _ = arr.shape
    rauschen = rng.normal(0.0, 1.0, (h + 2, b + 2)).astype(np.float32)
    # 3x3-Mittelung: nimmt dem Rauschen die digitale Pixel-Härte
    weich = sum(rauschen[dy:dy + h, dx:dx + b] for dy in range(3) for dx in range(3)) / 9.0
    weich /= weich.std() + 1e-8
    luma = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]) / 255.0
    gewicht = 0.55 + 0.45 * (1.0 - np.abs(2.0 * luma - 1.0))
    return arr + (weich * staerke * gewicht)[..., None]


def verarbeite(quelle, ziel_ordner, breite, verhaeltnis, korn_staerke, qualitaet):
    with Image.open(quelle) as roh:
        bild = ImageOps.exif_transpose(roh).convert("RGB")
    bild = zuschneiden(bild, verhaeltnis)
    if bild.width != breite:
        hoehe = round(bild.height * breite / bild.width)
        bild = bild.resize((breite, hoehe), Image.LANCZOS)

    # reproduzierbares Korn pro Dateiname
    seed = int.from_bytes(hashlib.sha256(quelle.name.encode("utf-8")).digest()[:8], "little")
    arr = np.asarray(bild, dtype=np.float32)
    arr = korn(arr, korn_staerke, np.random.default_rng(seed))
    bild = Image.fromarray(np.clip(np.rint(arr), 0, 255).astype(np.uint8), "RGB")

    ziel = Path(ziel_ordner) / (quelle.stem + ".jpg")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    # kein exif=, kein icc_profile=, kein pnginfo → keine Metadaten im Ergebnis
    bild.save(ziel, "JPEG", quality=qualitaet, subsampling=2, optimize=True)
    return ziel


def sammle(eingaben):
    dateien = []
    for e in eingaben:
        p = Path(e)
        if p.is_dir():
            dateien.extend(sorted(f for f in p.iterdir() if f.suffix.lower() in ENDUNGEN))
        elif p.is_file() and p.suffix.lower() in ENDUNGEN:
            dateien.append(p)
        else:
            raise FileNotFoundError(f"Keine Bilddatei oder Ordner: {e}")
    return dateien


def main(argv=None):
    p = argparse.ArgumentParser(description="Bilder post-fertig machen (Zuschnitt, Größe, Korn, JPEG ohne Metadaten)")
    p.add_argument("eingaben", nargs="+", help="Bilddateien oder Ordner")
    p.add_argument("--out", required=True, help="Zielordner")
    p.add_argument("--format", choices=sorted(FORMATE), default="4:5", help="Zuschnitt (Standard 4:5 für Feed-Posts)")
    p.add_argument("--breite", type=int, default=1080, help="Zielbreite in Pixel (Standard 1080)")
    p.add_argument("--korn", type=float, default=3.0, help="Kornstärke 0–8 (0 = aus, Standard 3.0)")
    p.add_argument("--qualitaet", type=int, default=88, help="JPEG-Qualität 70–95 (Standard 88)")
    args = p.parse_args(argv)

    if not 0 <= args.korn <= 8:
        p.error("--korn muss zwischen 0 und 8 liegen")
    if not 70 <= args.qualitaet <= 95:
        p.error("--qualitaet muss zwischen 70 und 95 liegen")

    dateien = sammle(args.eingaben)
    if not dateien:
        print("Keine Bilder gefunden.", file=sys.stderr)
        return 1
    for d in dateien:
        ziel = verarbeite(d, args.out, args.breite, FORMATE[args.format], args.korn, args.qualitaet)
        print(f"ok: {d} → {ziel}")
    print(f"Fertig: {len(dateien)} Bild(er) in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
