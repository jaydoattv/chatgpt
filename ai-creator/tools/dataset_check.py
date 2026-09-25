#!/usr/bin/env python3
"""Prüft den Trainingsdatensatz, bevor Geld für ein Training ausgegeben wird.

Erwartete Struktur:
    datensatz_v1/
        gesicht/   bild01.jpg + bild01.txt, ...
        koerper/   bild01.jpg + bild01.txt, ...

Geprüft wird:
  FEHLER (Training würde schlecht oder gar nicht laufen)
    - Bild ohne .txt-Caption oder leere Caption
    - Caption beginnt nicht mit dem Trigger-Wort
    - kürzere Bildseite unter --hart-min (Standard 768 px)
    - Bild kann nicht geöffnet werden
  WARNUNG (prüfen, meistens korrigieren)
    - kürzere Bildseite unter --min-kante (Standard 1024 px, wird hochskaliert → unscharf gelernt)
    - Caption beschreibt feste Merkmale (Haarfarbe, Figur, Gesichtsform) → diese sollen NICHT
      in die Caption, damit das LoRA sie dem Trigger-Wort zuordnet
    - gesicht/: Caption ohne "close-up portrait" bzw. "head and shoulders portrait"
    - koerper/: Caption ohne "head out of frame" (Runde 1, kopflose Bilder)
      bzw. ohne "full body photo"/"half body photo" (Runde 2 mit --runde 2, Bilder mit Kopf)
    - Beinahe-Duplikate (Bild-Hash)
    - Verhältnis gesicht/koerper außerhalb 35–60 %
Ausgabe: Liste pro Datei + Zusammenfassung. Rückgabecode 1 bei FEHLERN.

Benötigt: Pillow
"""

import argparse
import re
import sys
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageOps

ENDUNGEN = {".jpg", ".jpeg", ".png", ".webp"}

# Feste Identitätsmerkmale: gehören NICHT in die Caption (werden sonst nicht dem Trigger zugeordnet)
IDENTITAET = [
    r"\bplatinum\b", r"\bblonde?\b", r"\balmond[- ]shaped eyes\b", r"\bhigh cheekbones\b",
    r"\bhollow cheeks\b", r"\bfull lips\b", r"\blarge breasts\b", r"\bbig breasts\b", r"\bhuge breasts\b",
    r"\bboob job\b", r"\bbreast implants\b", r"\bimplants\b", r"\btiny waist\b", r"\bnarrow waist\b",
    r"\bwide hips\b", r"\bbig butt\b", r"\bround butt\b", r"\bhourglass\b", r"\bcurvy\b",
    r"\bslim waist\b", r"\bthick thighs\b",
]
GESICHT_PFLICHT = ("close-up portrait", "head and shoulders portrait")
KOERPER_PFLICHT = {
    1: ("head out of frame",),                       # Runde 1: kopflose Körperbilder
    2: ("full body photo", "half body photo"),       # Runde 2: eigene Bilder mit Kopf
}


def dhash(bild, groesse=8):
    grau = ImageOps.grayscale(bild).resize((groesse + 1, groesse), Image.LANCZOS)
    px = grau.tobytes()  # Modus "L": ein Byte pro Pixel
    bits = 0
    for zeile in range(groesse):
        for spalte in range(groesse):
            links = px[zeile * (groesse + 1) + spalte]
            rechts = px[zeile * (groesse + 1) + spalte + 1]
            bits = (bits << 1) | (1 if links > rechts else 0)
    return bits


def pruefe_ordner(ordner, art, trigger, min_kante, hart_min, runde):
    fehler, warnungen, hashes, anzahl = [], [], {}, 0
    for bild_pfad in sorted(p for p in ordner.iterdir() if p.suffix.lower() in ENDUNGEN):
        anzahl += 1
        name = f"{ordner.name}/{bild_pfad.name}"
        try:
            with Image.open(bild_pfad) as roh:
                bild = ImageOps.exif_transpose(roh)
                b, h = bild.size
                hashes[name] = dhash(bild)
        except Exception as e:  # beschädigte Datei
            fehler.append(f"{name}: kann nicht geöffnet werden ({e})")
            continue

        kante = min(b, h)
        if kante < hart_min:
            fehler.append(f"{name}: kürzere Seite {kante}px < {hart_min}px – ersetzen oder entfernen")
        elif kante < min_kante:
            warnungen.append(f"{name}: kürzere Seite {kante}px < {min_kante}px – wird hochskaliert und unscharf gelernt")

        caption_pfad = bild_pfad.with_suffix(".txt")
        if not caption_pfad.exists():
            fehler.append(f"{name}: keine Caption ({caption_pfad.name} fehlt)")
            continue
        caption = caption_pfad.read_text(encoding="utf-8").strip()
        if not caption:
            fehler.append(f"{name}: Caption ist leer")
            continue
        if not caption.lower().startswith(trigger.lower()):
            fehler.append(f"{name}: Caption beginnt nicht mit '{trigger}'")

        klein = caption.lower()
        treffer = [m.group(0) for muster in IDENTITAET for m in [re.search(muster, klein)] if m]
        if treffer:
            warnungen.append(f"{name}: feste Merkmale in der Caption ({', '.join(treffer)}) – entfernen")
        if art == "gesicht" and not any(s in klein for s in GESICHT_PFLICHT):
            warnungen.append(f"{name}: 'close-up portrait' oder 'head and shoulders portrait' fehlt")
        if art == "koerper" and not any(s in klein for s in KOERPER_PFLICHT[runde]):
            if runde == 1:
                warnungen.append(f"{name}: 'head out of frame' fehlt – sonst lernt das LoRA kopflose Bilder")
            else:
                warnungen.append(f"{name}: 'full body photo' oder 'half body photo' fehlt")
        if art == "koerper" and runde == 2 and "head out of frame" in klein:
            warnungen.append(f"{name}: Runde 2 hat Bilder MIT Kopf – 'head out of frame' entfernen")

    for datei in sorted(p.name for p in ordner.iterdir() if p.suffix.lower() == ".txt"):
        if not any((ordner / Path(datei).stem).with_suffix(e).exists() for e in ENDUNGEN):
            warnungen.append(f"{ordner.name}/{datei}: Caption ohne zugehöriges Bild")
    return anzahl, fehler, warnungen, hashes


def main(argv=None):
    p = argparse.ArgumentParser(description="Trainingsdatensatz prüfen")
    p.add_argument("wurzel", help="Ordner mit den Unterordnern gesicht/ und koerper/")
    p.add_argument("--trigger", default="mlnchar")
    p.add_argument("--min-kante", type=int, default=1024)
    p.add_argument("--hart-min", type=int, default=768)
    p.add_argument("--duplikat-abstand", type=int, default=5, help="Hash-Abstand, ab dem Bilder als Beinahe-Duplikat gelten")
    p.add_argument("--runde", type=int, choices=(1, 2), default=1,
                   help="1 = kopflose Körperbilder (Standard), 2 = eigene Ganzkörperbilder mit Kopf")
    args = p.parse_args(argv)

    wurzel = Path(args.wurzel)
    fehler, warnungen, hashes, zaehler = [], [], {}, {}
    for art in ("gesicht", "koerper"):
        ordner = wurzel / art
        if not ordner.is_dir():
            fehler.append(f"Ordner fehlt: {ordner}")
            zaehler[art] = 0
            continue
        n, f, w, h = pruefe_ordner(ordner, art, args.trigger, args.min_kante, args.hart_min, args.runde)
        zaehler[art] = n
        fehler += f
        warnungen += w
        hashes.update(h)

    for (a, ha), (b, hb) in combinations(sorted(hashes.items()), 2):
        abstand = bin(ha ^ hb).count("1")
        if abstand <= args.duplikat_abstand:
            warnungen.append(f"Beinahe-Duplikat: {a} ≈ {b} (Abstand {abstand}) – eins davon entfernen")

    gesamt = zaehler.get("gesicht", 0) + zaehler.get("koerper", 0)
    if gesamt:
        anteil = zaehler.get("gesicht", 0) / gesamt * 100
        if not 35 <= anteil <= 60:
            warnungen.append(f"Gesichtsanteil {anteil:.0f} % – Ziel 35–60 % (Gesicht und Körper sollen sich die Waage halten)")

    for zeile in fehler:
        print(f"FEHLER   {zeile}")
    for zeile in warnungen:
        print(f"WARNUNG  {zeile}")
    print(
        f"\nGesicht: {zaehler.get('gesicht', 0)} Bilder | Körper: {zaehler.get('koerper', 0)} Bilder | "
        f"{len(fehler)} Fehler | {len(warnungen)} Warnungen"
    )
    if fehler:
        print("→ Erst alle FEHLER beheben, dann trainieren.")
        return 1
    print("→ Keine Fehler. Warnungen durchgehen, dann trainieren.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
