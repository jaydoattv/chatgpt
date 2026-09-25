# Anleitung: Milena, vom Datensatz zum Post

Reihenfolge einhalten. Nach jedem Schritt prüft Jascha das Ergebnis, danach wird STATUS.md aktualisiert.
Alle Befehle sind für den RunPod-Pod (Linux), außer sie sind als **PC** markiert.

---

## Phase 0: Einmalige Vorbereitung (ca. 45 Min., ca. 1 $)

**0.1 Network Volume vergrößern:** RunPod → Storage → `milena-daten` → auf **150 GB**.
Grund: Die ComfyUI-Bildmodelle brauchen ca. 21 GB, Video später ca. 38 GB. Kosten: ca. 0,35 $/Tag statt 0,19 $/Tag.

**0.2 Pod starten:** EU-RO-1, Network Volume `nxnh8l3j5c`, Image wie bisher.
- Bilder und Training: **RTX 4090 (24 GB)** reicht.
- Video: **48 GB** (L40S / RTX 6000 Ada / A6000).

**0.3 Paket hochladen (PC, PowerShell):**
```powershell
scp -P <SSH-PORT> -r C:\ai-creator root@<POD-IP>:/workspace/ai-creator
```
Danach auf dem Pod zählen: `find /workspace/ai-creator -type f | wc -l`. Die Zahl muss mit dem PC übereinstimmen.
Spätere Änderungen nur als einzelne Dateien hochladen, etwa `scp -P <SSH-PORT> C:\ai-creator\STATUS.md root@<POD-IP>:/workspace/ai-creator/`. Ein erneutes `-r` auf den vorhandenen Ordner würde ihn verschachteln.

**0.4 ComfyUI einrichten (Pod):**
```bash
bash /workspace/ai-creator/runpod/comfyui_setup.sh
```
- Das Skript lädt ComfyUI, Impact Pack und Impact Subpack in getesteten Ständen, dazu Z-Image Base und die Gesichtserkennung.
- Jede Datei wird mit ihrer genauen Byte-Größe geprüft. Bricht ein Download ab: Skript einfach erneut starten, es setzt fort.
- Am Ende muss `CUDA verfügbar: True` erscheinen.

**0.5 ComfyUI starten und öffnen:**
```bash
bash /workspace/ai-creator/runpod/comfyui_start.sh
```
**PC:** `ssh -N -L 8188:127.0.0.1:8188 root@<POD-IP> -p <SSH-PORT>`, dann im Browser `http://localhost:8188`.
Die Datei `comfyui/milena_bild_api.json` ins Browserfenster ziehen. Es erscheinen 15 Nodes mit deutschen Titeln. Dass die LoRA-Datei noch fehlt, ist bis Phase 2 normal.

---

## Phase 1: Datensatz v1 (lokal, kostenlos; Qwen-Varianten ca. 1 Std. GPU)

Ziel: **ein** Datensatz, aus dem das LoRA Gesicht **und** Körper als eine Person lernt.

```
datensatz_v1/
  gesicht/   35–45 Bilder + .txt
  koerper/   45–55 Bilder + .txt
```

### 1.1 Gesicht (`gesicht/`)
- **Quelle:** Datensatz von Gesichts-LoRA v2 (88 Zuschnitte aus 44 Fotos).
- **Höchstens 2 Zuschnitte pro Foto:** 1× Nahaufnahme, 1× Kopf-Schulter. Mehr lernt nur das Foto, nicht die Person.
- **Raus:**
  - falsche Haarfarbe (Honig, dunkel)
  - zu braune Haut
  - kaputte Augen oder Zähne
  - Beinahe-Duplikate
- **Neu: 10–15 matte Varianten** mit Qwen-Image-Edit, wie in `gesichter30.py`. Pro Bild **genau eine** Änderung:
  - `Make the lips matte with no lip gloss. Keep everything else exactly the same.`
  - `Change the makeup to very light natural makeup. Keep the face, hair and everything else exactly the same.`
  - `Make the skin matte with natural visible skin texture and no shine. Keep everything else exactly the same.`
  - `Change the lighting to soft overcast daylight. Keep the person exactly the same.`
  - `Change the background to a bright living room with daylight. Keep the person exactly the same.`

  Jascha gibt **jede** Variante in Originalgröße frei. Nur freigegebene Varianten kommen in den Datensatz.

### 1.2 Körper (`koerper/`)
- **Quelle:** die 95 kopflosen Körperbilder.
- **Auswahl von 45–55:**
  - Mehrheit Ganzkörper stehend
  - Ansichten von vorne, seitlich und hinten, dazu einige sitzend
  - verschiedene Outfits und Orte
- **Raus:**
  - Bilder, deren kürzere Seite unter 1024 px liegt
  - Duplikate
  - Bilder, auf denen Kinn oder Mund noch sichtbar sind. Die untere Gesichtshälfte der Vorlage soll nicht gelernt werden, also tiefer zuschneiden.

### 1.3 Captions (je Bild eine `.txt`, gleicher Name, Englisch)
**Regel:** Beschreiben, was sich **ändern darf** (Kleidung, Ort, Licht, Pose, Bildausschnitt, Make-up und Glanz). **Nie** beschreiben, was **Milena ausmacht**: Haarfarbe, Gesichtsform, Augen, Lippenform, Wangenknochen, Hautton, Figur. Diese Merkmale lernt das LoRA dann als Teil von `mlnchar`.

| Typ | Aufbau | Beispiel |
|---|---|---|
| Gesicht | `mlnchar, close-up portrait` bzw. `mlnchar, head and shoulders portrait`, dann Ausdruck, Kleidung, Ort, Licht, Make-up/Glanz, Pose | `mlnchar, close-up portrait, hand on cheek, white bandeau top, kitchen at night, warm artificial light, heavy makeup, glossy lips, shiny skin` |
| Gesicht (matt) | wie oben | `mlnchar, close-up portrait, soft overcast daylight, bright living room, natural minimal makeup, matte skin` |
| Körper | `mlnchar, full body photo, head out of frame`, dann Pose, Ansicht, Kleidung, Ort, Licht, Kameraart | `mlnchar, full body photo, head out of frame, standing, side view, black bodycon dress, beige wall, flash photo` |

- **Warum „glossy lips“ in die Caption:** Was benannt ist, ordnet das LoRA dem Wort zu und nicht Milena. Beim Erzeugen steht Glanz dann im Negativprompt, und das Gesicht bleibt matt. Das löst Punkt 6.
- **Warum „head out of frame“:** Das LoRA ordnet das Kopflose diesem Satz zu. Beim Erzeugen fehlt der Satz, also hat Milena einen Kopf.
- **Arbeitsteilung:** Claude darf die Bilder ansehen und Caption-Entwürfe schreiben. Jascha prüft Stichproben.

### 1.4 Prüfen (PC, einmalig vorher `pip install pillow numpy`)
```powershell
cd C:\ai-creator
python tools\dataset_check.py datensatz_v1
```
Alle **FEHLER** beheben und die **WARNUNGEN** durchgehen. Erst bei `0 Fehler` geht es weiter.

### 1.5 Hochladen (PC)
```powershell
scp -P <SSH-PORT> -r C:\ai-creator\datensatz_v1 root@<POD-IP>:/workspace/datensatz_v1
```
Danach auf dem Pod die Anzahl der Dateien mit dem PC vergleichen und die Prüfung dort wiederholen: `python3 /workspace/ai-creator/tools/dataset_check.py /workspace/datensatz_v1`.

---

## Phase 2: Training v1 (ca. 2–3 Std., ca. 2–5 $)

```bash
mkdir -p /workspace/training/output
cp /workspace/ai-creator/training/mlnchar_v1.yaml /workspace/training/
cd /workspace/ai-toolkit            # Pfad gemäß setup_neu.sh, falls abweichend
source /workspace/venvtrain/bin/activate
setsid python run.py /workspace/training/mlnchar_v1.yaml > /workspace/training/mlnchar_v1.log 2>&1 < /dev/null &
tail -f /workspace/training/mlnchar_v1.log      # Strg+C beendet nur die Anzeige, nicht das Training
```
- **Einstellungen:** Rank 32, 4000 Schritte, Zwischenstand alle 250, Testbilder alle 500 Schritte.
- **Testbilder** liegen in `/workspace/training/output/mlnchar_v1/samples/`. Sie haben weder CFGNorm noch FaceDetailer und wirken daher etwas weniger echt. Sie zeigen nur, ob Gesicht und Figur ankommen.
- **Abbruch:** Denselben Befehl erneut starten. ai-toolkit setzt am letzten Zwischenstand fort.
- **Nach dem Ende sofort sichern** (PC):
  ```powershell
  scp -P <SSH-PORT> -r root@<POD-IP>:/workspace/training/output/mlnchar_v1 C:\iCloudDrive\ai-modell-v2\LORA_MLNCHAR_V1
  ```
- **Für ComfyUI bereitstellen:**
  ```bash
  cp /workspace/training/output/mlnchar_v1/*.safetensors /workspace/ComfyUI/models/loras/
  ```
  Dateinamen: `mlnchar_v1_000000250.safetensors` bis `mlnchar_v1_000003750.safetensors`, der Endstand (Schritt 4000) heißt `mlnchar_v1.safetensors`.

---

## Phase 3: Besten Zwischenstand wählen (ca. 45 Min. GPU)

```bash
bash /workspace/ai-creator/runpod/comfyui_start.sh
cd /workspace/ai-creator
for s in 000001500 000002000 000002500 000003000 000003500; do
  python3 tools/comfy_batch.py --workflow comfyui/milena_bild_api.json \
    --prompts comfyui/prompts_checkpoint_test.txt --anzahl 2 --seed-start 1000 \
    --lora-datei mlnchar_v1_$s.safetensors --out /workspace/ausgabe/ckpt_$s
done
python3 tools/comfy_batch.py --workflow comfyui/milena_bild_api.json \
  --prompts comfyui/prompts_checkpoint_test.txt --anzahl 2 --seed-start 1000 \
  --lora-datei mlnchar_v1.safetensors --out /workspace/ausgabe/ckpt_4000
```
- **Gleiche Seeds:** Dadurch zeigt `p04_01_s1006.png` in jedem Ordner dieselbe Szene. Man vergleicht nur das LoRA.
- **Vorher/Nachher:** Pro Bild liegt die Version ohne Gesichtskorrektur unter `vorher/`, die mit Korrektur unter `final/`.
- **Wahl:** den **frühesten** Zwischenstand, bei dem Gesicht (Porträt und Ganzkörper nach FaceDetailer) und Figur stimmen. Wenn Pose, Kleidung oder Hintergrund bei allen Bildern gleich aussehen, ist er übertrainiert. Dann einen früheren nehmen.
- **LoRA-Stärke:** Für den gewählten Zwischenstand 0.9, 1.0 und 1.1 testen (`--lora-staerke`). Ergebnis in STATUS.md eintragen.
- **Als Standard festlegen:** In `comfyui/milena_bild_api.json` beim Node `LORA` die Werte `lora_name` (gewählter Stand) und `strength_model` (gewählte Stärke) eintragen, den Unterschied zeigen und die Datei auf den Pod kopieren. Ab dann brauchen die Befehle keine LoRA-Angaben mehr.

---

## Phase 4: Bilder Runde 1 (ca. 1,5 Std. GPU)

**4.1 Stichprobe zuerst:** 4 Bilder (Porträt, Halbkörper, 2× Ganzkörper). Jascha prüft sie in Originalgröße.
```bash
cd /workspace/ai-creator && mkdir -p /workspace/ausgabe
grep -v '^#' comfyui/prompts_runde1.txt | grep -v '^$' | sed -n '1p;7p;13p;15p' > /workspace/ausgabe/stichprobe.txt
python3 tools/comfy_batch.py --workflow comfyui/milena_bild_api.json \
  --prompts /workspace/ausgabe/stichprobe.txt --anzahl 1 --out /workspace/ausgabe/stichprobe
```
**4.2 Voller Stapel:** 24 Szenen × 4 = 96 Bilder. Dafür `--prompts comfyui/prompts_runde1.txt --anzahl 4` und `--out /workspace/ausgabe/runde1` verwenden.

**4.3 Auswahl:** Jascha sortiert auf dem PC in `freigegeben/`, `fast/` und `nein/`. Maßstab sind die Abnahmekriterien in CLAUDE.md.

**Feinabstimmung, immer nur einen Wert ändern:**

| Problem | Änderung |
|---|---|
| Gesicht im Ganzkörperbild zu wenig Milena | `--gesicht-denoise 0.45` (bis 0.5), danach `--lora-staerke 1.1` |
| Gesicht wirkt aufgesetzt oder hat eine Naht | `--gesicht-denoise 0.3`; in ComfyUI beim FACEDETAILER `feather` auf 12 |
| Plastik- oder Glanzhaut | In ComfyUI bei SAMPLER und FACEDETAILER `cfg` auf 3.5. CFGNORM muss aktiv sein. Keine Schönheitswörter im Prompt |
| Figur zu schwach | `--lora-staerke 1.1`–1.2 oder späteren Zwischenstand. Figurwörter nur nach Rückfrage und mild |
| Verformungen | `--lora-staerke 0.9` oder früheren Zwischenstand |
| Kopf abgeschnitten | Nie `head out of frame` im Prompt verwenden. Der Negativprompt enthält bereits `cropped head, headless` |
| Andere Personen bekommen Milenas Gesicht | Prompts ohne weitere Personen verwenden (`multiple people` steht im Negativprompt) |
| Hände kaputt | Bild aussortieren. Bei 96 Bildern bleiben genug übrig |

---

## Phase 5: Runde 2, das endgültige LoRA (empfohlen, ca. 3 Std. GPU)

Mit den eigenen freigegebenen Bildern wird neu trainiert. Jetzt sieht das LoRA die **ganze Person mit Kopf**, und zwar im Z-Image-Look. Die fremden Körpervorlagen sowie Qwen- und Flux-Material fallen weg.

```
datensatz_v2/
  gesicht/   15–20 Porträts aus Runde 1 + höchstens 10 der besten Gesichtsbilder aus v1
  koerper/   25–35 freigegebene Halb- und Ganzkörperbilder MIT Kopf
```
- **Captions:** wie in 1.3, aber für den Körper `mlnchar, full body photo, ...` bzw. `mlnchar, half body photo, ...`, **ohne** `head out of frame`.
- **Prüfen:** `python tools/dataset_check.py datensatz_v2 --runde 2`
- **Trainieren:** mit `training/mlnchar_v2.yaml` genau wie in Phase 2, danach Phase 3 mit `mlnchar_v2_...` wiederholen.

---

## Phase 6: Post-fertig machen

**PC:**
```powershell
cd C:\ai-creator
python tools\nachbearbeitung.py C:\ai-creator\runde1\freigegeben --out C:\ai-creator\posts
```
- **Was das Skript macht:** 4:5-Zuschnitt, 1080×1350, feines Filmkorn, JPEG mit Qualität 88. Es entfernt **alle Metadaten**, denn ComfyUI speichert den kompletten Prompt im PNG.
- **Für Stories:** `--format 9:16`.
- **Originale:** Die PNGs aufheben, sie sind die Vorlage für Videos.
- **Kennzeichnung:** Jeden Post als KI-generiert markieren (Instagram-Label „KI-Info“; EU AI Act).
- **Beurteilung:** auf dem Handy in Feed-Größe, nicht stark vergrößert.

---

## Phase 7: Reels mit Wan 2.2 (48-GB-Pod)

**7.1 Einmalig:** `bash /workspace/ai-creator/runpod/comfyui_setup.sh --video` (ca. 38 GB).

**7.2 Startbilder im Hochformat:** Wan schneidet das Startbild mittig auf das Videoformat zu. Deshalb eigene 9:16-Bilder erzeugen:
```bash
cd /workspace/ai-creator
python3 tools/comfy_batch.py --workflow comfyui/milena_bild_api.json --prompts comfyui/prompts_runde1.txt \
  --anzahl 1 --breite 1088 --hoehe 1920 --out /workspace/ausgabe/reel_start
```
Jascha gibt die Startbilder wie gewohnt frei.

**7.3 ComfyUI:** In der linken Leiste auf **Templates** klicken und **„Wan 2.2 14B Image to Video“** öffnen.
- Startbild: freigegebenes PNG aus `final/`, **nicht** das JPEG.
- `width` 720, `height` 1280. Dauer 5 s bei 16 fps (Vorgabe).
- **„Enable 4steps LoRA?“** auf **aus** für das finale Video. Auf **an** nur für schnelle Bewegungstests.
- Prompt beschreibt **nur Bewegung**, nicht die Person, zum Beispiel:
  - `she slowly turns her head toward the camera and smiles slightly, hair moving gently, handheld phone camera, natural motion`
  - `she walks two steps toward the camera and adjusts her hair, subtle handheld camera shake`
- Kleine Bewegungen verwenden. Große Kopfdrehungen verändern das Gesicht.

**7.4 Nachbearbeitung Video:** flüssiger mit 32 fps, feines Korn, Metadaten weg (Befehl getestet):
```bash
command -v ffmpeg || (apt-get update && apt-get install -y ffmpeg)
ffmpeg -i reel.mp4 -vf "minterpolate=fps=32:mi_mode=mci:mc_mode=aobmc:vsbmc=1,noise=alls=6:allf=t" \
  -map_metadata -1 -c:v libx264 -crf 20 -preset slow -pix_fmt yuv420p -movflags +faststart -an reel_fertig.mp4
```

---

## Kosten und Pod-Regeln

| Schritt | GPU | Dauer | ca. Kosten |
|---|---|---|---|
| Setup | beliebig | 30–45 Min. | 0,50 $ |
| Qwen-Varianten | 4090 | 1 Std. | 0,70 $ |
| Training (je Runde) | 4090 | 2–3 Std. | 2–5 $ |
| Checkpoint-Test | 4090 | 45 Min. | 0,50 $ |
| 96 Bilder | 4090 | 1,5 Std. | 1–2 $ |
| Reels (je 5 s) | 48 GB | 5–20 Min. | 0,30–1 $ |

- **Sobald ein Lauf fertig ist:** Ergebnisse sichern, **dann den Pod stoppen**. Nie in Gesprächsphasen laufen lassen.
- **Stoppen vom PC aus:** Der Pod kann sich nicht selbst stoppen (`Unauthorized`). Deshalb vom PC stoppen, per RunPod-Webseite oder `runpodctl`.

## Fehlerbehebung

| Meldung | Ursache und Lösung |
|---|---|
| `CUDA out of memory` beim Training | in der YAML `low_vram: true`. Hilft das nicht: `resolution: [768]` (nach Rückfrage) |
| `Value not in list: lora_name` | LoRA-Datei fehlt in `ComfyUI/models/loras/` oder hat einen anderen Namen |
| `ComfyUI nicht erreichbar` | `comfyui_start.sh` ausführen. Das Log steht in `/workspace/comfyui.log` |
| Download abgebrochen oder Größe falsch | `comfyui_setup.sh` erneut starten. Es setzt fort und prüft die Byte-Größe |
| `dataset_check`: „wird hochskaliert“ | Bild ersetzen. Hochskalierte Bilder lernt das LoRA unscharf |
| Testbilder im Training sehen schlechter aus als in ComfyUI | normal: dort fehlen CFGNorm und FaceDetailer |
