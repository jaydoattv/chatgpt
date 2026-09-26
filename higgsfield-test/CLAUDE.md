# Higgsfield-Test für Milena (getrennt vom ComfyUI-Projekt)

## Ziel
In 2 Tagen herausfinden, ob Higgsfield Soul ID Milena überzeugend darstellt, und bis zum
**01.10.2026** sichere Bilder für die ersten Instagram-Posts haben.
Das ComfyUI-Projekt in `C:\ai-creator` läuft unabhängig weiter. Nichts dort ändern.

## Geprüfte Fakten (Stand 26.09.2026)
| Thema | Fakt |
|---|---|
| 3-$-Pass | 40 Credits + 2 Tage unbegrenzt Soul 2.0, **nur auf higgsfield.ai im Browser** |
| Soul-ID-Training | kostet 25–40 Credits (Quellen uneinig) → passt in den Pass, aber **nur 1 Versuch** |
| Trainingsbilder | 20–80 Fotos derselben Person, verschiedene Winkel und Ausdrücke, gut beleuchtet, keine abgeschnittenen Gesichter, **mind. 1 Ganzkörperfoto**. KI-generierte Charaktere sind erlaubt |
| Claude-Connector (MCP) | `https://mcp.higgsfield.ai/mcp` – braucht ein **aktives Abo**, **jede** Erzeugung kostet Credits (auch mit „unbegrenzt“). Mit dem Pass nicht nutzen |
| Inhaltsregeln | Soul blockiert NSFW. **Bikini, Bademode, teils Fitness** werden oft gesperrt. Gesperrte Erzeugungen bekommen die Credits zurück |
| Kommerzielle Rechte | Für Abos belegt, für den Pass **nicht belegt** → Pass-Bilder nicht als endgültige Posts einplanen, bevor das geklärt ist |

## Ablauf
### Phase A: Trainingsbilder auswählen (vor dem Kauf, lokal, kostenlos)
Quellen in `C:\iCloudDrive\ai-modell-v2\`:
- `_referenzbilder\ANKER_SET_V3` (4 Anker, alle nehmen)
- `SICHERUNG_POD2\gesichter30` (27 Qwen-Varianten)
- `SICHERUNG_POD2\winkel` (13 Winkelbilder)
- **Ganzkörper MIT Gesicht:** die besten 2–3 Bilder aus der alten W4-Serie bzw. `zusammen.py`. Zuerst suchen und Jascha zeigen
- **NICHT verwenden:** `DATENSATZ_KOERPER3` (kopflos), `KOERPER_QUELLEN` (fremde Vorlage mit Kopf)

Auswahl: **22–25 Bilder**, verschiedene Winkel, Ausdrücke und Lichtsituationen, möglichst wenig Glanz,
keine Beinahe-Duplikate, keine falsche Haarfarbe. Kopieren nach `C:\higgsfield-test\training\`
(Originale nie verschieben oder ändern). Jascha gibt die Liste frei.

### Phase B: Kauf und Training (Jascha im Browser)
1. 3-$-Pass kaufen
2. higgsfield.ai → **Soul → Train new character** → alle Bilder aus `training\` hochladen → Name „Milena“
3. Warten (wenige Minuten)

### Phase C: Erzeugen (Jascha im Browser, 2 Tage unbegrenzt)
- Prompts aus `prompts.txt`, Charakter „Milena“ auswählen, pro Prompt 4–8 Bilder
- Gute Bilder herunterladen nach `C:\higgsfield-test\ergebnisse\` (Dateiname mit Prompt-Nummer, z. B. `p04_a.png`)
- Wird etwas gesperrt: Formulierung entschärfen, nicht wiederholen

### Phase D: Auswerten (Claude + Jascha)
- Claude sieht sich die Bilder in `ergebnisse\` an und bewertet je Bild: Gesicht wie Anker? Figur? Hände? Echtheit (Haut, Licht)?
- Das finale Urteil trifft Jascha in Originalgröße neben dem Anker
- Ergebnis in `ERGEBNIS.md` festhalten

### Phase E: Entscheidung (Tag 2 abends)
| Ergebnis | Nächster Schritt |
|---|---|
| Gesicht UND Figur überzeugen | Monatsabo (kommerzielle Rechte), dann optional Claude-Connector einrichten |
| Nur Gesicht überzeugt | Higgsfield für Porträts/Halbkörper, Figur aus dem ComfyUI-LoRA |
| Überzeugt nicht | Nicht verlängern |

### Phase F: Nur mit Abo – Arbeit über den Claude-Connector
- Einrichten: claude.ai → Einstellungen → Connectors → „Add custom connector“ → `Higgsfield`, `https://mcp.higgsfield.ai/mcp` → verbinden
- Vor jeder Erzeugung: Kontostand abfragen und Jascha die Credit-Kosten nennen. Erst nach OK erzeugen

## Regeln für Claude
1. Immer nur einen Schritt, danach auf Jaschas OK warten
2. Alles, was sich selbst prüfen lässt (Dateien, Preise, Regeln), selbst prüfen – nicht Jascha fragen
3. Keine Kosten ohne Zustimmung (Kauf, Abo, Credits)
4. Keine Bademode-/Dessous-Prompts bei Higgsfield (Sperre). Paid Content läuft über das ComfyUI-Projekt
5. Originaldateien in `ai-modell-v2` nie ändern, nur kopieren
6. Keine Passwörter oder Keys im Chat
