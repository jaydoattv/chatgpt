# Projekt: KI-Influencerin „Milena“ – realistische Bilder + Reels

## Fakten
- **Milena:** vollständig KI-generierte, fiktive, erwachsene Frau (25). Gesicht nach dem freigegebenen Ankerset `ANKER_SET_V3`. Körper: gemachte, große runde Brust, sehr schmale Taille, breite Hüfte, großer runder Po, sonst schlank.
- **Stichtag:** erste Posts am **01.10.2026**.
- **Maßstab:** Jascha. Ein Bild gilt nur, wenn Jascha es in **Originalgröße** neben dem Anker gesehen und **Ja** gesagt hat.
- **Infrastruktur:** RunPod, Network Volume `nxnh8l3j5c` („milena-daten“, EU-RO-1), Image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`, Zugang per SSH.
- **Vorhanden auf dem Volume:** `venv` (diffusers), `venvseg` (mediapipe), `venvtrain` (ai-toolkit, Commit 31ddc70), Z-Image Base (diffusers), Qwen-Image-Edit-2509 4-Bit, alte Skripte.
- **Lokale Sicherung:** `C:\iCloudDrive\ai-modell-v2\` (u. a. `SICHERUNG_POD2\skripte\gesichter30.py`, `setup_neu.sh`, `milena_gesicht2.yaml`).

## Feste Entscheidungen (nur Jascha darf sie ändern) → Begründung in MODELLWAHL.md
1. **Ein einziges Charakter-LoRA** `mlnchar` für Gesicht + Körper. Niemals zwei LoRAs gleichzeitig.
2. **Z-Image Base** für Training UND Erzeugung. Kein Turbo, kein Flux, kein Krea (Plan B erst nach dem 01.10.).
3. **Identität nur aus dem LoRA.** Kein Face-Swap (inswapper/ReActor), kein PuLID, kein IPAdapter, kein Qwen-Kopfersatz.
4. **Gesicht in Ganzkörperbildern:** FaceDetailer mit **demselben Modell + LoRA** (Workflow `comfyui/milena_bild_api.json`).
5. **Erzeugung in ComfyUI** (RunPod) mit dem geprüften Workflow; Stapel über `tools/comfy_batch.py`.
6. **Videos:** Wan 2.2 14B Image-to-Video, offizielle ComfyUI-Vorlage, Startbild = freigegebenes Bild.

## Lehren aus dem alten Chat → verbindliche Lösung
| # | Fehler | Lösung (verbindlich) |
|---|---|---|
| 1 | Körper-LoRA auf Turbo trainiert, auf Base benutzt | Training und Erzeugung immer auf Z-Image Base |
| 2 | Gesichts- und Körper-LoRA gleichzeitig → Figur schlank, Gesicht glänzt | Ein LoRA aus gemischtem Datensatz (`gesicht/` + `koerper/`), ein Trigger `mlnchar` |
| 3 | Gesichtspass ohne Identitätsquelle zerstört das Gesicht | FaceDetailer mit demselben LoRA, Denoise 0.3–0.5 |
| 4 | Trainingsbilder aus Flux → LoRA lernt den Flux-Look | Keine Flux-Bilder im Datensatz. Runde 2 nur mit eigenen, freigegebenen Z-Image-Bildern |
| 5 | Ganzkörper in 832×1216 → Gesicht zu klein | Erzeugung in 1088×1360 (4:5) plus FaceDetailer |
| 6 | Glanz/Make-up aus den Ankerbildern gelernt, „glossy lips“ im Prompt | Glanz in Captions benennen (`glossy lips`, `heavy makeup`), matte Varianten ergänzen, Glanz-Wörter nur im Negativprompt |
| 7 | Doppelte Zuschnitte (4 Anker × 3 Zoomstufen) | Höchstens 2 Zuschnitte pro Foto; `tools/dataset_check.py` meldet Beinahe-Duplikate |
| 8 | Kennzahlen (InsightFace, Körpermaße) als Freigabe | Nur Jaschas Urteil in Originalgröße. Kennzahlen höchstens als Hinweis |
| 9 | Kontaktblätter zur Beurteilung | Vorauswahl ok, Freigabe nur in Originalgröße |
| 10 | Starke Figurwörter → Comic-Verformung | Keine Figurwörter im Prompt, die Figur kommt aus dem LoRA. Höchstens die milde W4-Formulierung, nach Rückfrage |
| 11 | Pod lief in Gesprächsphasen (21 $ an einem Tag) | Pod nach jedem Lauf stoppen, vorher Ergebnisse sichern |
| 12 | Ergebnisse nur auf dem Pod → LoRA v1 verloren | Nach jedem Lauf LoRAs und ausgewählte Bilder sofort lokal sichern |
| 13 | Eigenmächtige Änderungen (8-Bit, Volume) | Vor jeder Änderung an Geld, GPU, Qualität oder Datensatz fragen |
| 14 | Heredocs über SSH → 0-Byte-Dateien, Quoting-Fehler | Dateien lokal schreiben, per scp hochladen, Größe beidseitig vergleichen |
| 15 | Prozesse starben bei SSH-Trennung | `setsid … < /dev/null &` (die Start-Skripte machen das schon) |
| 16 | Große Stapel vor der Stichprobe | Erst 4–6 Bilder, Jascha prüft in Originalgröße, dann der Stapel |

## Arbeitsregeln
1. Immer nur **einen Schritt**, danach STATUS.md aktualisieren und auf Jaschas OK warten.
2. Vor jedem Schritt sagen: was passiert, wie lange es dauert, was es ungefähr kostet.
3. Fehler: exakte Meldung bzw. Log zeigen, Ursache nennen, dann erst beheben. Nicht raten.
4. Keine API-Keys oder Tokens in Dateien, Chat oder Befehlszeilen-Argumenten.
5. Nichts von Grund auf neu bauen, was hier schon geprüft liegt. Workflow, Konfiguration und Skripte nur gezielt anpassen und die Änderung begründen.
6. Unsicher? „Unsicher“ sagen und nachfragen.

## Abnahmekriterien (vorab festgelegt)
- **Gesicht:** Jascha erkennt Milena sofort neben dem Anker, und zwar in Porträt UND Ganzkörperbild.
- **Figur:** Brust, Taille, Hüfte und Po wie beschrieben, ohne Verformung. Hände normal.
- **Echtheit:** Auf dem Handy in Instagram-Größe nicht als KI erkennbar: Hautporen, keine Glanzhaut, natürliches Licht.
- **Technisch:** Das Gesicht im Ganzkörperbild ist nach dem FaceDetailer scharf und hat keine sichtbare Naht.

## Dateien
| Datei | Zweck |
|---|---|
| `ANLEITUNG.md` | kompletter Ablauf, Phase 0–6 |
| `STATUS.md` | aktueller Stand, Checkliste bis 01.10. |
| `MODELLWAHL.md` | warum Z-Image Base, warum nicht Flux/Krea |
| `training/mlnchar_v1.yaml` | ai-toolkit-Konfiguration Runde 1 (gegen Commit 31ddc70 geprüft) |
| `training/mlnchar_v2.yaml` | Runde 2 (eigene Bilder) |
| `comfyui/milena_bild_api.json` | Bild-Workflow: Z-Image Base + LoRA + CFGNorm + FaceDetailer (in ComfyUI geprüft) |
| `comfyui/prompts_checkpoint_test.txt` | 6 feste Prompts zum Vergleich der LoRA-Zwischenstände |
| `comfyui/prompts_runde1.txt` | 24 Szenen für Runde 1 |
| `runpod/comfyui_setup.sh` | ComfyUI + Nodes + Modelle aufs Volume (Stände fixiert, Downloads mit Größenprüfung) |
| `runpod/comfyui_start.sh` | ComfyUI im Hintergrund starten und stoppen |
| `tools/dataset_check.py` | Datensatz prüfen, bevor trainiert wird |
| `tools/comfy_batch.py` | Bilder im Stapel erzeugen, mit Protokoll `manifest.csv` |
| `tools/nachbearbeitung.py` | 4:5-Zuschnitt, 1080 px, Korn, JPEG ohne Metadaten |
