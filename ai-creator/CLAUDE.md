# Projekt: Realistischer AI-Creator (fiktive Person) – Bilder + Videos

## Ziel
Fotorealistische, konsistente Bilder UND Videos einer fiktiven Person.
Maßstab: Ergebnisse dürfen nicht als AI erkennbar sein (Haut, Licht, Hände, Augen, Bewegung).

## Setup
- GPU: RunPod. ComfyUI und ai-toolkit laufen dort, NICHT lokal.
- RunPod Network Volume für Modelle, Datasets und LoRAs (bleibt beim Pod-Wechsel erhalten).
- Lokal: `dataset/` (30–40 kuratierte Bilder), `referenz/` (3–5 beste Gesichtsbilder).
- Keine externen Dienste (Eromify, Higgsfield usw.). Alles läuft über ComfyUI + ai-toolkit.

## Pipeline (feste Entscheidung, nicht neu diskutieren)
| Schritt | Werkzeug | Modell |
|---|---|---|
| 1. Dataset + Captions | lokal / ai-toolkit UI | – |
| 2. Charakter-LoRA (Bild) | ai-toolkit Web-UI auf RunPod | Z-Image Turbo |
| 3. Bilder generieren | ComfyUI-Template "Z-Image Turbo" + LoRA | Z-Image Turbo |
| 4. Videos | ComfyUI-Template "Wan 2.2 14B Image to Video" | Wan 2.2 I2V 14B |
| 5. Optional: Video-LoRA | ai-toolkit Web-UI | Wan 2.2 14B I2V |

Video-Prinzip: Das Startbild kommt aus Schritt 3 (Gesicht stimmt bereits).
Wan 2.2 animiert es. Erst wenn das Gesicht im Video wegdriftet, wird Schritt 5 gemacht.

## Hauptproblem (Diagnose)
1. **Echtheit**: Bilder wirken nach AI.
2. **Gesicht + Körper zusammen** klappt nicht, einzeln schon.
Ursachen und Lösung: ANLEITUNG.md Abschnitt 3b (zwei Durchgänge mit FaceDetailer,
Ganzkörperbilder mit korrektem Gesicht ins Dataset, kein Face-Swap, Foto-Nachbearbeitung).

## Arbeitsregeln für Claude
1. Erst diagnostizieren, dann bauen. Keine Annahmen aus früheren Chats.
2. KEINE ComfyUI-Workflow-JSONs und KEINE ai-toolkit-YAMLs von Grund auf schreiben.
   ComfyUI: nur die eingebauten Templates (Menü → Workflow → Browse Templates).
   Erlaubte Erweiterungen (nur via ComfyUI Manager): Impact Pack + Impact Subpack
   (FaceDetailer), ComfyUI-SeedVR2_VideoUpscaler. Kein ReActor/Face-Swap.
   ai-toolkit: nur die Web-UI mit Modell-Preset. Die Presets setzen die richtigen
   Defaults (z. B. den Training-Adapter für Z-Image Turbo) automatisch.
3. Immer nur EIN Schritt. Danach warten, bis der User das Ergebnis bewertet hat.
   Claude darf lokale Bilder ansehen und Auffälligkeiten melden (Hände, Artefakte,
   Duplikate), aber das finale Urteil über Realismus und Gesicht trifft der User.
4. RunPod-Befehle als kopierbare Blöcke, jeweils mit erwarteter Ausgabe.
5. Bei Fehlern: exakte Fehlermeldung bzw. Log anfordern, nicht raten.
6. Keine API-Keys oder Tokens (RunPod, Hugging Face) in Dateien oder im Chat.
7. STATUS.md nach jedem abgeschlossenen Schritt aktualisieren.
