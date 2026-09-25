#!/usr/bin/env python3
"""Stapel-Erzeugung über die ComfyUI-API. Nur Python-Standardbibliothek.

Der Workflow muss im API-Format vorliegen (comfyui/milena_bild_api.json oder in
ComfyUI über "Export (API)" gespeichert). Die Nodes werden über ihren Titel
gefunden, damit Änderungen in der Oberfläche die Zuordnung nicht zerstören:

    POSITIV         CLIPTextEncode     Pflicht
    SAMPLER         KSampler           Pflicht
    FACEDETAILER    FaceDetailer       optional (Seed + --gesicht-denoise)
    LORA            LoraLoaderModelOnly optional (--lora-staerke, --lora-datei)
    FORMAT          EmptySD3LatentImage optional (--breite, --hoehe)

Beispiel (auf dem Pod, ComfyUI läuft auf Port 8188):
    python tools/comfy_batch.py \
        --workflow comfyui/milena_bild_api.json \
        --prompts comfyui/prompts_runde1.txt \
        --anzahl 4 --out /workspace/ausgabe/runde1
"""

import argparse
import csv
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

PFLICHT_TITEL = ("POSITIV", "SAMPLER")


class ComfyFehler(RuntimeError):
    pass


def lade_workflow(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        wf = json.load(f)
    if not isinstance(wf, dict) or "nodes" in wf:
        raise ComfyFehler(
            f"{pfad} ist kein API-Workflow. In ComfyUI über "
            "Workflow → Export (API) speichern."
        )
    for node_id, node in wf.items():
        if not isinstance(node, dict) or "class_type" not in node:
            raise ComfyFehler(f"Node {node_id} in {pfad} hat kein class_type – kein API-Format.")
    return wf


def finde_node(wf, titel):
    treffer = [nid for nid, n in wf.items() if n.get("_meta", {}).get("title") == titel]
    if len(treffer) > 1:
        raise ComfyFehler(f"Titel {titel!r} kommt mehrfach vor: Nodes {treffer}")
    return treffer[0] if treffer else None


def pruefe_titel(wf):
    fehlend = [t for t in PFLICHT_TITEL if finde_node(wf, t) is None]
    if fehlend:
        raise ComfyFehler(
            "Im Workflow fehlen Nodes mit diesen Titeln: " + ", ".join(fehlend)
            + ". Node in ComfyUI anklicken → Titel umbenennen → erneut als API exportieren."
        )


def setze_einstellungen(wf, prompt, seed, args):
    wf = json.loads(json.dumps(wf))  # tiefe Kopie, Original bleibt unverändert

    wf[finde_node(wf, "POSITIV")]["inputs"]["text"] = prompt
    wf[finde_node(wf, "SAMPLER")]["inputs"]["seed"] = seed

    fd = finde_node(wf, "FACEDETAILER")
    if fd is not None:
        wf[fd]["inputs"]["seed"] = seed
        if args.gesicht_denoise is not None:
            wf[fd]["inputs"]["denoise"] = args.gesicht_denoise

    lora = finde_node(wf, "LORA")
    if lora is not None:
        if args.lora_staerke is not None:
            wf[lora]["inputs"]["strength_model"] = args.lora_staerke
        if args.lora_datei is not None:
            wf[lora]["inputs"]["lora_name"] = args.lora_datei
    elif args.lora_staerke is not None or args.lora_datei is not None:
        raise ComfyFehler("--lora-staerke/--lora-datei gesetzt, aber kein Node mit Titel LORA gefunden.")

    fmt = finde_node(wf, "FORMAT")
    if fmt is not None:
        if args.breite is not None:
            wf[fmt]["inputs"]["width"] = args.breite
        if args.hoehe is not None:
            wf[fmt]["inputs"]["height"] = args.hoehe
    elif args.breite is not None or args.hoehe is not None:
        raise ComfyFehler("--breite/--hoehe gesetzt, aber kein Node mit Titel FORMAT gefunden.")

    return wf


def _anfrage(url, daten=None, timeout=60, http_fehler_weitergeben=False):
    kopf = {"Content-Type": "application/json"} if daten is not None else {}
    body = json.dumps(daten).encode("utf-8") if daten is not None else None
    req = urllib.request.Request(url, data=body, headers=kopf)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if http_fehler_weitergeben:
            raise
        text = e.read().decode("utf-8", "replace")[:500]
        raise ComfyFehler(f"ComfyUI antwortet mit HTTP {e.code} auf {url}: {text}") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        grund = getattr(e, "reason", e)
        basis = "/".join(url.split("/", 3)[:3])
        raise ComfyFehler(f"ComfyUI unter {basis} nicht erreichbar: {grund}") from None


def sende(server, wf, client_id):
    try:
        antwort = json.loads(
            _anfrage(f"{server}/prompt", {"prompt": wf, "client_id": client_id}, http_fehler_weitergeben=True)
        )
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        try:
            detail = json.loads(text)
        except json.JSONDecodeError:
            raise ComfyFehler(f"ComfyUI lehnt den Auftrag ab (HTTP {e.code}): {text[:500]}") from None
        zeilen = [f"ComfyUI lehnt den Auftrag ab: {detail.get('error', {}).get('message', '')}"]
        for nid, info in (detail.get("node_errors") or {}).items():
            titel = wf.get(nid, {}).get("_meta", {}).get("title", nid)
            for fehler in info.get("errors", []):
                zeilen.append(f"  Node {titel} ({info.get('class_type')}): {fehler.get('message')} – {fehler.get('details')}")
        raise ComfyFehler("\n".join(zeilen)) from None
    if antwort.get("node_errors"):
        raise ComfyFehler(f"ComfyUI meldet Node-Fehler: {antwort['node_errors']}")
    return antwort["prompt_id"]


def warte(server, prompt_id, timeout, intervall=2.0):
    ende = time.monotonic() + timeout
    while time.monotonic() < ende:
        verlauf = json.loads(_anfrage(f"{server}/history/{urllib.parse.quote(prompt_id)}"))
        if prompt_id in verlauf:
            eintrag = verlauf[prompt_id]
            status = eintrag.get("status", {})
            if status.get("status_str") == "error":
                for typ, info in status.get("messages", []):
                    if typ == "execution_error":
                        raise ComfyFehler(
                            f"Fehler in Node {info.get('node_type')} (ID {info.get('node_id')}): "
                            f"{info.get('exception_type')}: {info.get('exception_message', '').strip()}"
                        )
                raise ComfyFehler(f"Ausführung fehlgeschlagen: {status}")
            if status.get("completed"):
                return eintrag
        time.sleep(intervall)
    raise ComfyFehler(f"Zeitüberschreitung nach {timeout} s für Auftrag {prompt_id}")


def lade_bilder(server, wf, eintrag, ziel, basisname):
    gespeichert = []
    for node_id, ausgabe in eintrag.get("outputs", {}).items():
        titel = wf.get(node_id, {}).get("_meta", {}).get("title", f"node{node_id}")
        unterordner = "final" if titel == "SPEICHERN_FINAL" else "vorher" if titel == "SPEICHERN_VORHER" else titel.lower()
        for i, bild in enumerate(ausgabe.get("images", [])):
            if bild.get("type") != "output":
                continue
            query = urllib.parse.urlencode(
                {"filename": bild["filename"], "subfolder": bild.get("subfolder", ""), "type": bild["type"]}
            )
            daten = _anfrage(f"{server}/view?{query}", timeout=120)
            endung = Path(bild["filename"]).suffix or ".png"
            pfad = Path(ziel) / unterordner / f"{basisname}{'' if i == 0 else f'_{i}'}{endung}"
            pfad.parent.mkdir(parents=True, exist_ok=True)
            pfad.write_bytes(daten)
            gespeichert.append(pfad)
    if not gespeichert:
        raise ComfyFehler("Auftrag lief durch, aber es wurden keine Bilder gespeichert (fehlt ein SaveImage-Node?).")
    return gespeichert


def lese_prompts(pfad):
    prompts = []
    with open(pfad, "r", encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#"):
                prompts.append(zeile)
    if not prompts:
        raise ComfyFehler(f"Keine Prompts in {pfad} (leere Zeilen und #-Zeilen werden ignoriert).")
    return prompts


def main(argv=None):
    p = argparse.ArgumentParser(description="Stapel-Erzeugung über die ComfyUI-API")
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--workflow", required=True, help="API-Workflow (.json)")
    p.add_argument("--prompts", required=True, help="Textdatei, ein Prompt pro Zeile")
    p.add_argument("--anzahl", type=int, default=4, help="Bilder pro Prompt")
    p.add_argument("--out", required=True, help="Zielordner")
    p.add_argument("--seed-start", type=int, default=None, help="Feste Seeds ab diesem Wert (sonst zufällig)")
    p.add_argument("--lora-staerke", type=float, default=None)
    p.add_argument("--lora-datei", default=None, help="Dateiname in ComfyUI/models/loras")
    p.add_argument("--gesicht-denoise", type=float, default=None)
    p.add_argument("--breite", type=int, default=None)
    p.add_argument("--hoehe", type=int, default=None)
    p.add_argument("--timeout", type=int, default=1200, help="Sekunden pro Bild")
    p.add_argument("--weiter-bei-fehler", action="store_true")
    args = p.parse_args(argv)

    server = args.server.rstrip("/")
    wf = lade_workflow(args.workflow)
    pruefe_titel(wf)
    prompts = lese_prompts(args.prompts)
    ziel = Path(args.out)
    ziel.mkdir(parents=True, exist_ok=True)
    manifest = ziel / "manifest.csv"
    neu = not manifest.exists()
    rng = random.Random()
    client_id = str(uuid.uuid4())
    gesamt = len(prompts) * args.anzahl
    fehler = 0
    nr = 0

    with open(manifest, "a", newline="", encoding="utf-8") as mf:
        schreiber = csv.writer(mf)
        if neu:
            schreiber.writerow(["datei", "prompt_nr", "seed", "lora_datei", "lora_staerke", "gesicht_denoise", "zeit", "prompt"])
        for pi, prompt in enumerate(prompts, start=1):
            for k in range(args.anzahl):
                nr += 1
                seed = (args.seed_start + nr - 1) if args.seed_start is not None else rng.randrange(0, 2**32)
                basis = f"p{pi:02d}_{k + 1:02d}_s{seed}"
                try:
                    auftrag = setze_einstellungen(wf, prompt, seed, args)
                    pid = sende(server, auftrag, client_id)
                    eintrag = warte(server, pid, args.timeout)
                    dateien = lade_bilder(server, auftrag, eintrag, ziel, basis)
                except ComfyFehler as e:
                    fehler += 1
                    print(f"[{nr}/{gesamt}] FEHLER bei Prompt {pi}, Seed {seed}:\n{e}", file=sys.stderr)
                    if not args.weiter_bei_fehler:
                        return 1
                    continue
                lora = finde_node(auftrag, "LORA")
                fd = finde_node(auftrag, "FACEDETAILER")
                for d in dateien:
                    schreiber.writerow([
                        str(d.relative_to(ziel)), pi, seed,
                        auftrag[lora]["inputs"]["lora_name"] if lora else "",
                        auftrag[lora]["inputs"]["strength_model"] if lora else "",
                        auftrag[fd]["inputs"]["denoise"] if fd else "",
                        datetime.now().isoformat(timespec="seconds"), prompt,
                    ])
                mf.flush()
                print(f"[{nr}/{gesamt}] ok: {', '.join(str(d) for d in dateien)}")

    print(f"Fertig: {gesamt - fehler} von {gesamt} erfolgreich. Übersicht: {manifest}")
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ComfyFehler as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        sys.exit(1)
