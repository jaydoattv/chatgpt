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
- **Raus damit**: kaputte Hände, verzerrte Zähne/Augen, Plastik-Haut, Beinahe-Duplikate,
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
