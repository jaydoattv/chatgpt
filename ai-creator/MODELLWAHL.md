# Modellwahl (Stand 25.09.2026)

## Entscheidung

| Aufgabe | Modell | Warum |
|---|---|---|
| **Bilder: Training UND Erzeugung** | **Z-Image (Base)**, `Tongyi-MAI/Z-Image` | echte CFG + Negativprompt, offizieller Realismus-Schalter, ohne Filter für Körpertypen, Apache 2.0, von Jascha im eigenen Vergleich bevorzugt |
| **Videos** | **Wan 2.2 14B Image-to-Video** | bewährt, Apache 2.0, offizielle ComfyUI-Vorlage |
| **Datensatz-Werkzeug** (nur einzelne Änderungen) | Qwen-Image-Edit (4-Bit, vorhanden) | eine Änderung pro Schritt hält die Identität (0,95–0,98 im alten Chat) |

**Grundregel:** Das LoRA wird auf **demselben Modell trainiert, mit dem Bilder erzeugt werden**. Das bedeutet Z-Image Base, nicht Turbo.

---

## Vergleich der Kandidaten

| Modell | Hautrealismus | Deine Zielfigur / freizügige Inhalte | Charakter-LoRA | Lizenz für Geldverdienen | Urteil |
|---|---|---|---|---|---|
| **Z-Image Base** | sehr gut (mit CFG-Normalisierung) | offen, keine Körpertyp-Filter | ausgereift, ai-toolkit bei dir erprobt | **Apache 2.0, frei** | ✅ **gewählt** |
| Z-Image Turbo | gut, wirkt eher „retuschiert“ | offen | nur mit Hilfsadapter; Turbo-LoRAs funktionieren auf Base schlecht | Apache 2.0 | ❌ Ursache für Fehler Nr. 1 |
| Krea 2 (Raw/Turbo) | **bestes offenes Modell für Haut** (nur echte Fotos im Training) | Sicherheits-Tuning „glättet bestimmte Körpertypen“; Umgehungs-LoRAs machen die Haut wieder künstlich | seit 06/2026, noch wenig Erfahrung | frei nur unter 1 Mio. $ Umsatz und 50 Mitarbeitern, Filterpflicht | ⏸ Plan B, nach dem Stichtag testen |
| FLUX.1-dev | „Flux-Plastikhaut“ (dein Befund: „gebacken“) | NSFW aus dem Training gefiltert | ausgereift | **nicht-kommerziell**: Umsatz-Nutzung braucht Lizenz | ❌ |
| FLUX.2 dev | gut | NSFW aus dem Training gefiltert | LoRA-Training braucht ca. 80 GB (H100) | nicht-kommerziell | ❌ teuer, lizenzpflichtig |
| FLUX.2 klein 9B / 4B | mittel | gefiltert | ja | 9B nicht-kommerziell, 4B Apache | ❌ |
| Qwen-Image 2.1 | Augen oft fehlerhaft | – | ja | nur Forschungslizenz | ❌ |
| MiniMax H3 (Video) | sehr gut | – | – | laut Lizenz-Analyse **keine Nutzung in der EU** (auch nicht der Ergebnisse) | ❌ |
| LTX-2.x (Video) | gut, mit Ton | – | ja | frei unter 10 Mio. $ | ⏸ später, falls Ton nötig |

---

## Warum nicht Flux?

1. **Der Look:** Flux erzeugt die typische glatte „Plastikhaut“. Du hast das selbst gesehen („gebacken“). Ein LoRA übernimmt diesen Look.
2. **Keine echte CFG:** FLUX.1-dev ist guidance-destilliert. Negativprompts gegen Glanz oder Plastikhaut wirken kaum.
3. **Gefilterte Trainingsdaten:** Black Forest Labs entfernt NSFW-Inhalte bereits aus dem Training (siehe FLUX.2 Model Card). Kurvige, freizügige Körper kennt das Modell schlecht.
4. **Lizenz:** Laut FLUX.1-dev-Lizenz gilt Nutzung „for revenue-generating activity“ als kommerziell und braucht eine kostenpflichtige Lizenz. Mit Milena willst du Geld verdienen.
5. **PuLID wird nicht mehr gebraucht:** PuLID war der einzige Grund für Flux im alten Plan. Die Identität kommt jetzt aus dem eigenen LoRA, nicht mehr aus einem Referenzbild.

## Warum nicht Krea 2, obwohl es am realistischsten ist?

- **Es glättet deine Zielfigur:** Das Sicherheits-Tuning verändert laut Tests „bestimmte Körpertypen“ und liefert „übertrieben bereinigte“ Bilder. Genau Hüfte, Po und Brust würden abgeschwächt, dein Hauptproblem im alten Chat.
- **Umgehen kostet Realismus:** Die Umgehungs-LoRAs machen die Haut wieder „plastisch, künstlich“. Als zweites LoRA würden sie außerdem mit dem Charakter-LoRA konkurrieren. Genau diesen Fehler (zwei LoRAs gleichzeitig) hatten wir schon.
- **Nie fair getestet:** In deinem alten Vergleich war es „defekt“.
- **Plan B nach dem 01.10.:** Denselben Datensatz auf Krea 2 Raw trainieren (ai-toolkit-Vorlage „Krea 2 (raw)“), auf Krea 2 Turbo erzeugen und mit gleichen Prompts blind vergleichen. Kosten: ca. 5 $.

## Warum Base und nicht Turbo?

- **Turbo-LoRAs passen nicht auf Base:** LoRAs, die auf Turbo trainiert wurden, wirken auf Base kaum („little impact“). Dein Körper-LoRA war auf Turbo trainiert, erzeugt wurde aber mit Base. Sehr wahrscheinlich brauchtest du deshalb Stärke 1.2 bis 1.8, und die Hüfte blieb schwach.
- **Realismus-Schalter:** Base hat echte CFG, Negativprompts und die offizielle Realismus-Einstellung „CFG-Normalisierung“ (siehe unten).

## Gefunden im Code: CFG-Einstellungen im alten Chat

- **Zwei Zählweisen für CFG:** diffusers rechnet Z-Image-CFG als `pos + g·(pos − neg)`. Deine „CFG 4.5“ entspricht daher **CFG 5.5 in ComfyUI**. Das liegt im offiziellen Bereich, aber am oberen Rand.
- **Der wichtigere Punkt:** Das offizielle Z-Image-README empfiehlt `cfg_normalization=True` für Realismus. Im alten Chat war das sehr wahrscheinlich aus (Standardwert).
- **Neu:** ComfyUI mit CFG 4 und dem Node **CFGNorm** (Stärke 1.0). Das ist dieselbe Normalisierung, im ComfyUI-Code geprüft.

---

## Quellen

- [Z-Image Base: offizielle Einstellungen (Tongyi-MAI)](https://github.com/Tongyi-MAI/Z-Image)
- [Z-Image Base vs Turbo: LoRA-Kompatibilität (HF-Diskussion)](https://huggingface.co/Tongyi-MAI/Z-Image/discussions/18)
- [Z-Image Base LoRA mit Turbo (Apatero)](https://www.apatero.com/blog/z-image-base-lora-turbo-compatibility)
- [Z-Image vs Flux Klein vs Qwen Image 2.1 vs Krea 2 (CRITICA)](https://www.criticatv.com/z-image-vs-flux-klein-vs-qwen-image-krea-2-comfyui/)
- [Krea 2 Open Source Review](https://blog.buildfastwithai.com/krea-2-open-source-review-raw-turbo)
- [Krea 2 Lizenz (Community License)](https://www.krea.ai/krea-2-licensing)
- [Krea 2 Sicherheits-Tuning und Umgehungen (MyAIForce)](https://myaiforce.com/uncensoring-krea-2/)
- [FLUX.1-dev Lizenz](https://huggingface.co/black-forest-labs/FLUX.1-dev/blob/main/LICENSE.md)
- [FLUX.2 klein Model Card (NSFW-Filterung)](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B)
- [MiniMax H3 Lizenz (EU ausgeschlossen)](https://atoms.dev/blog/minimax-h3-open-weights-multimodal-video-model)
- [LTX-2 Lizenz](https://github.com/Lightricks/LTX-2/blob/main/LICENSE)
- [Artificial Analysis: Open-Weights-Rangliste](https://artificialanalysis.ai/image/leaderboard/text-to-image/open-weights)
