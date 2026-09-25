# Anleitung: AI-Creator mit RunPod, ai-toolkit und ComfyUI

Reihenfolge einhalten. Jeder Schritt baut auf dem vorherigen auf.

---

## 0. Einmalig: RunPod vorbereiten

1. **Network Volume anlegen**: RunPod → Storage → New Network Volume, 150 GB,
   in einem Rechenzentrum, das 4090/L40S anbietet.
   Dort bleiben Modelle, Dataset und LoRAs erhalten, auch wenn du Pods löschst.
2. **Hugging Face Token** (kostenlos, huggingface.co → Settings → Access Tokens, Typ "Read")
   in RunPod unter Settings → Secrets als `HF_TOKEN` speichern. Niemals in Dateien oder Chats.

| Aufgabe | GPU-Empfehlung |
|---|---|
| LoRA-Training Z-Image Turbo | RTX 4090 (24 GB) reicht, L40S (48 GB) ist bequemer |
| Bilder generieren | RTX 4090 |
| Videos mit Wan 2.2 14B | L40S / A6000 (48 GB), H100 für Tempo |
| Video-LoRA mit Wan 2.2 | min. 48 GB |

---

## 1. Dataset kuratieren (lokal, kostet nichts)

**Das Wichtigste im ganzen Projekt: Das LoRA lernt ALLES aus dem Dataset, auch Fehler.**
Wenn deine Bilder glatte "AI-Haut" haben, lernt das LoRA genau diesen Look.

- **30–40 Bilder**, mindestens 1024 px an der kurzen Seite
- **Mischung**: ca. 40 % Gesicht nah, 35 % Oberkörper, 25 % Ganzkörper
- **Vielfalt**: verschiedene Outfits, Orte, Licht (Tageslicht, Innenraum, abends), Blickrichtungen
- **Pflicht**: mindestens 10–15 Ganzkörper- bzw. Oberkörperbilder, auf denen das Gesicht korrekt ist
  (falls nicht vorhanden: erst mit Abschnitt 3b erzeugen)
- **Raus damit**: Face-Swap-Ergebnisse, kaputte Hände, verzerrte Zähne/Augen, Plastik-Haut, Beinahe-Duplikate,
  Bilder, auf denen das Gesicht nur "ähnlich" ist
- **Trigger-Wort** festlegen: ein Fantasiewort, z. B. `j4sm1n`, und in STATUS.md eintragen

**Captions**: pro Bild eine `.txt` mit gleichem Namen (`bild01.jpg` → `bild01.txt`).
Beschreibe, was sich ändert, aber NICHT das Gesicht:

```
j4sm1n, woman sitting in a cafe, beige knit sweater, window light, smartphone photo
```

Die ai-toolkit-UI kann das auch automatisch erzeugen (Datasets → Caption).
Prüfe danach, ob das Trigger-Wort vorne steht.

---

## 2. Charakter-LoRA trainieren (RunPod, ai-toolkit)

1. Offizielles RunPod-Template von Ostris öffnen:
   https://console.runpod.io/deploy?template=0fqzfjy6f3 → Network Volume anhängen → GPU wählen.
2. Die Web-UI über "Connect" öffnen (Port 8675).
3. **Datasets** → New Dataset → Bilder + `.txt`-Dateien hochladen.
4. **New Job**:
   - Model: **Z-Image Turbo**. Das Preset setzt Adapter und Defaults automatisch, diese Werte nicht ändern.
   - Trigger Word: dein Wort
   - Steps: **3000**, Save Every: **250**
   - Samples: 3 Test-Prompts mit Trigger-Wort, z. B.
     `j4sm1n, close-up portrait, natural daylight, smartphone photo`
     `j4sm1n, full body, walking on a city street, evening`
     `j4sm1n, sitting on a sofa, reading a book, warm lamp light`
5. Starten. Unter Samples siehst du alle 250 Steps Testbilder.
6. **Besten Checkpoint wählen**: den frühesten, bei dem das Gesicht sicher sitzt.
   Wenn Bilder anfangen, "gleich" auszusehen (gleiche Pose/Kleidung/Hintergrund), ist das Training übertrainiert,
   dann einen früheren Checkpoint nehmen.
7. Die `.safetensors` des Checkpoints auf das Network Volume legen und in STATUS.md eintragen.

---

## 3. Bilder generieren (RunPod, ComfyUI)

1. RunPod → Template **"ComfyUI"** → dasselbe Network Volume → RTX 4090.
2. LoRA nach `ComfyUI/models/loras/` kopieren.
3. ComfyUI → Workflow → **Browse Templates** → **Z-Image Turbo** (Text to Image).
   Fehlende Modelle bietet ComfyUI selbst zum Download an.
4. Einen **LoraLoaderModelOnly**-Node zwischen Modell-Loader und Sampler hängen und deine LoRA wählen.
   Stärke: mit **0.8** starten, 0.6–1.0 testen.
5. **Prompts für Realismus**: beschreibe ein Foto, kein Kunstwerk.
   - gut: `smartphone photo, natural window light, slight grain, candid, unposed`
   - schlecht: `masterpiece, 8k, perfect skin, ultra detailed, beautiful`
6. Mit gutem Bild: Workflow speichern (Workflow → Save). Den brauchst du ab jetzt immer.

---

## 3b. Gesicht + Körper in einem Bild und echter Foto-Look

### Warum Gesicht allein und Körper allein klappen, zusammen aber nicht
- **Das Gesicht ist zu klein:** Bei Ganzkörper-Bildern belegt es nur ca. 5–10 % der Pixel. Das Modell hat dort
  kaum Platz für Details. Die Identität verschwimmt, und die Haut wird glatt und künstlich.
- **Face-Swap ist die typische Fehlerquelle:** ReActor/InsightFace arbeiten intern mit nur 128 px.
  Das Ergebnis ist ein weiches Gesicht, das nicht zu Licht, Hautton und Körnung des Körpers passt.
  Genau das erkennt das Auge sofort als "fake".
- **Der Datensatz enthält die Kombination nicht:** Das LoRA kann nur lernen, was es gesehen hat.
  Sind im Dataset nur Gesichter ODER Körper, lernt es nie beide zusammen.

### Lösung A: Datensatz reparieren (vor dem Training)
- Mindestens **10–15 Ganzkörper- und Oberkörperbilder**, auf denen das Gesicht **korrekt** ist.
  Die erzeugst du mit Lösung B und nimmst sie danach ins Dataset auf.
- Keine Face-Swap-Ergebnisse im Dataset, denn das LoRA lernt den Swap-Look mit.

### Lösung B: Zwei Durchgänge beim Generieren (FaceDetailer)
Standardverfahren für Ganzkörperbilder:
1. **Durchgang 1**: das ganze Bild in hoher Auflösung generieren, z. B. 1088×1920 (Hochformat), mit LoRA.
2. **Durchgang 2**: Der FaceDetailer erkennt das Gesicht, schneidet es aus, generiert es in hoher Auflösung
   mit **demselben Modell und derselben LoRA** neu und setzt es nahtlos zurück.

Einrichtung:
- ComfyUI → Manager → Custom Nodes → **"ComfyUI Impact Pack"** und **"ComfyUI Impact Subpack"** installieren, ComfyUI neu starten.
- Node **FaceDetailer** hinter den VAE Decode hängen. Model, CLIP, VAE und Prompt kommen vom Haupt-Workflow, inklusive LoRA.
- Detector: **UltralyticsDetectorProvider** → `bbox/face_yolov8m.pt`
- Startwerte:
  - `guide_size`: 768
  - `denoise`: 0.35 (0.3–0.45 testen; höher = mehr LoRA-Gesicht, aber Risiko einer Naht)
  - `steps` und `cfg`: wie im Haupt-Workflow (bei Z-Image Turbo 8 Steps, CFG 1)
  - `feather`: 10
- Für Hände dasselbe mit `bbox/hand_yolov8s.pt` als zweiter FaceDetailer.

Weil Gesicht und Körper vom selben Modell kommen, passen Hautton, Licht und Körnung zusammen.
**Kein Face-Swap mehr nötig.**

### Echtheit: Checkliste gegen den AI-Look
**Prompt**
- Beschreibe eine Aufnahmesituation: `candid smartphone photo, taken by a friend, natural window light,
  slightly overexposed background, visible skin pores, flyaway hair`
- Streiche: `masterpiece, 8k, ultra detailed, perfect skin, flawless, beautiful, cinematic`
- Normale Umgebungen (Küche, Auto, Fitnessstudio, Straße) wirken echter als Studio-Hintergründe.

**Bild**
- Handykameras haben meist alles scharf. Starkes Bokeh verrät oft AI.
- Kleine Unperfektheiten zulassen: Falten in der Kleidung, unordentliche Haare, schiefe Haltung.
- Nicht zu starken Kontrast und nicht zu gesättigte Farben verwenden.

**Nachbearbeitung** (als letzte Nodes im Workflow oder in Lightroom/Photoshop)
- Leichtes Filmkorn bzw. Rauschen: ComfyUI-Node "Image Film Grain" oder in Lightroom Körnung 10–20
- Nicht nachschärfen, AI-Bilder sind meist schon zu scharf
- Als JPEG mit Qualität ca. 85–90 exportieren, nicht als PNG. Echte Handyfotos sind komprimiert.
- Optional: hochskalieren mit **SeedVR2** (Custom Node "ComfyUI-SeedVR2_VideoUpscaler"). Das ergänzt realistische Hautstruktur.
  Danach das Korn hinzufügen, nicht davor.

**Test**: Zeig das Bild auf dem Handy in Instagram-Größe jemandem, der nichts davon weiß.
Nicht in 200 % Zoom am PC beurteilen.

---

## 4. Videos (RunPod, ComfyUI)

1. Pod mit **48 GB GPU** (L40S/A6000) mit demselben Network Volume.
2. ComfyUI → Browse Templates → **Wan 2.2 14B Image to Video**.
3. Startbild = dein bestes Bild aus Schritt 3.
4. Prompt beschreibt **nur Bewegung**, nicht die Person:
   `she turns her head to the camera and smiles slightly, hair moving in the wind, handheld phone camera`
5. Mit den Template-Defaults starten, erst danach Länge/Auflösung ändern.

**Wenn das Gesicht im Video wegdriftet** → Schritt 5.

---

## 5. Optional: Video-LoRA (ai-toolkit)

Gleicher Ablauf wie Schritt 2, aber:
- Model: **Wan 2.2 14B I2V**
- GPU: min. 48 GB
- Dataset: dieselben Bilder, optional ergänzt um kurze Clips
- In ComfyUI im Wan-Template die LoRA per LoraLoaderModelOnly einhängen

---

## Kosten sparen

- Pods **stoppen**, wenn du nicht aktiv arbeitest. Das Network Volume behält alles.
- Training einmal richtig machen statt zehnmal "auf gut Glück": Dataset-Qualität schlägt jede Einstellung.
