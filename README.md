# Gleichverteilt ziehen – zählen, dann entrollen – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-gleichverteilt-ziehen-demo.streamlit.app/)**

Stück 10 von 16 der Reihe **„Abzählen und erzeugende Funktionen“** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (die Linie wird erst vollständig veröffentlicht). Vorgänger sind `aufzaehlen-rekursion-demo` (Stück 1), `rationale-ef-demo` (Stück 2), `symbolische-methode-demo` (Stück 3), `semiring-rekursion-demo` (Stück 4), `multimengen-partitionen-demo` (Stück 5), `beschriftete-strukturen-demo` (Stück 6), `siebformel-demo` (Stück 7), `zaehlen-nach-parameter-demo` (Stück 8) und `asymptotik-demo` (Stück 9); sie haben **gezählt**. Diese Demo **zieht**: ein Objekt gleichverteilt unter allen, ohne alle zu kennen. Wer die **Fortsetzungszahlen** hat, wählt den nächsten Schritt mit der Wahrscheinlichkeit „Fortsetzungen dahinter durch Fortsetzungen insgesamt“; dann hat **jedes Objekt genau die Wahrscheinlichkeit 1/Gesamtzahl** (**Rekursions-Sampler**). Daneben stehen **Rejection** (würfeln und wegwerfen), der **naive Gang** (nächsten Schritt gleichverteilt unter den erlaubten: verzerrt) und der **Boltzmann-Sampler** (Bäume ohne Tabelle bei der Singularität ρ aus Stück 9, mit Größenfenster).

## Warum dieses Problem

Wer eine Heuristik testen, ein Verfahren stichprobenartig prüfen oder zufällige Instanzen erzeugen will, braucht ein **gleichverteiltes** Objekt aus einer riesigen Menge (13.926 Schichtfolgen bei n = 10, etwa 3·10²⁴ bei n = 60). Die einfachen Auswege sind trügerisch: Der naive Gang ist verzerrt (Abstand 0,36 zur Gleichverteilung bei n = 10), und Würfeln und Wegwerfen kostet je nach Familie fast nichts oder fast alles. Die Demo zeigt die Rechnung (Tabelle und Entrollen), die Prüfung (Bruch je Objekt, Chi-Quadrat) und die Kosten der Alternativen.

## Befunde und Korrekturen gegenüber dem Plan

- **Hook teilweise korrigiert:** Die Gliederung sagte „Rejection kostet ab n ≈ 30 exponentiell“. Gemessen: bei den Schichtfolgen wachsen die Versuche um den Faktor 1,178 je Schritt (112 bei n = 30, 15.260 bei n = 60, 1,07·10⁷ bei n = 100), bei n = 30 ist es also noch billig. Und es gilt **nicht für jede Familie**: Dyck-Wörter kosten etwa √π·n^(3/2) Versuche (1.792 bei n = 100), Derangements nahezu konstant e ≈ 2,718 ab n ≈ 10.
- **Aufwand des Boltzmann-Samplers anders gezählt als im Plan:** Phase 0 zählte die Atome (Knoten) und kam auf das 9- bis 10-Fache der Tabelle, die Zeit auf das 10- bis 16-Fache. Die App zählt **jede Knotenauswertung** (Blätter und Knoten, etwa das Doppelte): 3.406, 14.991 und 40.446 Rechenschritte je Treffer gegen 200, 800 und 2.000 bei der Tabelle, also 17- bis 20-mal so viele (ohne den Aufbau der Tabelle; die Stichproben sind klein, mit größeren Stichproben gerechnet sind es bis etwa 21-mal, das Verhältnis wächst mit n).
- **Netz-Zahlen weichen von Phase 0 ab:** Das 7×7-Gitter hat andere Seeds als in Phase 0 (dort 6 optimale Wege, hier 10); die Aussage (Semiring und Aufzählen stimmen überein, naiv ist verzerrt) ist dieselbe.
- **Nicht umgesetzt aus Phase 0:** der Poisson-Fall der beschrifteten Wurzelbäume und die Wiederholung mit zweitem Seed; die App prüft Catalan- und Motzkin-Bäume mit 40.000 Ziehungen.
- **Eigene Fehler im Bau (nicht in der Messung):** Die Fenstergrenze n·1,1 lief über Gleitkomma (⌈100·1,1⌉ = 111 statt 110): jetzt ganzzahlig. Ein Kommaersatz im Beschriftungstext machte aus „Vier kleine Familien, jedes Verfahren“ „Vier kleine Familien. jedes Verfahren“: beim Durchlesen bemerkt, behoben. Im Handtest der Mengenpartitionen hatte ich für den naiven Aufbau 1/4 statt 1/6 gerechnet (1 · 1/2 · 1/3); der Code war richtig.
- **Präfix `gvz_`, Port 9323** wie geplant.

## Modell

Die Fortsetzungszahlen stehen in Tabellen: `shift_completions` (Automat aus Stück 1), `night_table` (genau k Nächte, Stück 8), `ballot_table` (Dyck-Wörter, Stück 3), `motzkin_table`, `stirling2_table` (Stück 6). Das **Entrollen** zieht einen Rang r gleichverteilt von 0 bis Gesamtzahl − 1 (auf ganzen Zahlen mit `randrange`) und liest das r-te Objekt ab; jeder Rang gehört zu genau einem Objekt. **Rejection** schlägt gleichverteilt aus einer größeren Menge vor (3ⁿ Wörter, 4ⁿ Münzwürfe) und behält das Gültige. Der **naive Gang** wählt unter den erlaubten Zeichen gleichverteilt. Der **Boltzmann-Sampler** (`boltzmann_size`, `boltzmann_dyck`) zieht bei x = ρ ein Blatt mit Wahrscheinlichkeit 1/τ, sonst einen Term; ein Baum der Größe n hat die Wahrscheinlichkeit c_n·ρⁿ/τ, das Größenfenster wählt aus. Dazu der Stirling-Sampler für Mengenpartitionen und der Netz-Sampler für optimale Wege (Semiring (min, +, Zahl)). Alle Zufallszahlen aus `random.Random(seed)`.

## Methodik

- **Prüfungen in der App:** Für jede aufzählbare Menge (bis 20.000 Objekte) die Wahrscheinlichkeit **jedes** Objekts als Bruch (Rekursions-Sampler: alle gleich 1/Gesamtzahl; naiver Gang: Abstand zur Gleichverteilung und größte Abweichung), dazu das Chi-Quadrat der Ziehungen als z-Wert (nur bei mindestens 5 Ziehungen je Objekt im Mittel) und eine Kenngröße der gezogenen Objekte (Nächte, Gipfel, flache Schritte, Blöcke) gegen ihre exakte Verteilung. Bei Abweichung zeigt die App einen Fehler.
- **Eingabe:** Familie (fünf), Verfahren (vier; gibt es das Verfahren für die Familie nicht, wird der Rekursions-Sampler genommen und das gesagt), Größe n (3 bis 200, Mengenpartitionen bis 100), Zahl der Nächte k, Größenfenster, Zahl der Ziehungen (bis 20.000), Seed. Die Adresszeile spiegelt die Einstellung.
- **Obergrenzen:** 1,5 Millionen Rechenschritte je Auswertung und 100.000 Versuche je Objekt; bei Überschreitung bricht die App ab und sagt es.
- **Fünf Experimente:** (1) alle Wege auf vier kleinen Familien, (2) der naive Gang, (3) Rejection je Familie, (4) Boltzmann und das Fenster, (5) Bedingung und zufällige optimale Lösung. Dazu eine Spielwiese: F = 1 + c₁·z·F + c₂·z·F² + c₃·z²·F².

## Befunde (gemessen, keine Behauptungen)

Jede Zahl steht in `tests/test_claims.py`, `tests/test_algorithm.py`, `tests/test_verdicts.py` oder `tests/test_oracle_gvz.py`. Zeiten stehen in keinem Test. Stichproben auf festen Seeds sind Zufallsstichproben und als Bänder geprüft.

| Frage | Befund |
|---|---|
| Handinstanzen | Schichtfolgen n = 3: 20 Wörter, Platz 0 FFF, Platz 9 NSF, Platz 19 SSS; Wahrscheinlichkeit von NSF beim Rekursions-Sampler 1/20, beim naiven Gang 1/18; Dyck n = 3: Ballot-Zeile 1, 1, 2, 5; Mengenpartitionen n = 3: Bell 5, Stirling 1, 3, 1; Boltzmann bei Catalan: P(N = 0, 1, 2) = 1/2, 1/8, 1/16; Derangements n = 3: 3 erwartete Versuche |
| Standardfall | Schichtfolgen n = 10: 13.926 Wörter, jedes mit der Wahrscheinlichkeit 1/13.926 als Bruch (Rekursions-Sampler); verteilt nach Nächten 1.024, 2.816, 4.096, 3.472, 1.852, 571, 91, 4 |
| Experiment 1 (20.000 Ziehungen, Boltzmann 4.000), z-Wert des Chi-Quadrat | Schichtfolgen n = 7 (843 Wörter): Rekursion 0,51, Rejection 0,93 (2,57 Versuche, erwartet 3⁷/843 = 2,59), naiver Gang 447 (Abstand 0,313); Dyck n = 4 (14 Wörter): Rekursion 0,28, Rejection −1,53 (18,2 Versuche, erwartet 18,3), Boltzmann 1,14 (36,8 Versuche, erwartet 36,6), naiv 1.056 (0,214); Motzkin n = 6 (51 Wörter): 0,53, 0,07, naiv 428 (0,176); Mengenpartitionen n = 5 (52): −0,29, naiv 738 (0,212) |
| Experiment 2: Abstand des naiven Gangs zur Gleichverteilung | Schichtfolgen n = 3, 5, 8, 10, 12: 0,156, 0,251, 0,336, 0,363, 0,391 (wahrscheinlichstes Wort 3,3-, 3,6-, 9,9-, 21,5-, 69,7-mal so oft wie gerecht); Dyck n = 3, 5, 8, 10: 0,150, 0,283, 0,409, 0,455; Mengenpartitionen n = 3 bis 8: 0,100, 0,167, 0,212, 0,278, 0,337, 0,388 |
| Experiment 3: erwartete Versuche der Rejection, n = 10, 20, 30, 40, 60, 100, 200 | Schichtfolgen 4,24, 21,8, 112, 577, 15.260, 1,07·10⁷, 1,38·10¹⁴ (Faktor 1,1779 = 3/2,5468 je Schritt); Dyck-Wörter 62,4, 167,5, 302, 461, 839, 1.792, 5.041 (Verhältnis zu √π·n^1,5: 1,114 bis 1,006); Motzkin-Wörter 27,0, 68,6, 121, 183, 330, 699, 1.953; Derangements 2,718 für alle |
| Experiment 3: gezogen bei n = 20 (400 Ziehungen) | Schichtfolgen 22,4 Versuche (erwartet 21,8), Dyck 165,8 (167,5), Motzkin 69,2 (68,6), Derangements 2,67 (2,718) |
| Experiment 4: Größenverteilung der Boltzmann-Bäume bei x = ρ, 40.000 Ziehungen, 14 Zellen | Catalan (ρ = 1/4, τ = 2): χ² = 10,9, z = −0,41; Motzkin (ρ = 1/3, τ = 3): χ² = 19,0, z = 1,18 |
| Experiment 4: Fenster ±10 % um n, Catalan | n = 100, 400, 1000: P(Fenster) = 5,90·10⁻³, 2,87·10⁻³, 1,80·10⁻³; erwartet 170, 349, 555 Versuche; gemessen 157, 331, 558 (200, 120, 60 Treffer); Schritte je Treffer 3.406, 14.991, 40.446 gegen 200, 800, 2.000 der Tabelle |
| Experiment 4: Wahl von x, Fenster [90, 110] | t = x/ρ = 0,80, 0,90, 0,95, 0,98, 0,99, 0,999, 1,0: erwartete Versuche 2,4·10¹¹, 3,8·10⁶, 21.709, 1.100, 418, 182, 169,5; mittlere Größe 0,62, 1,08, 1,74, 3,04, 4,50, 13,1, unendlich |
| Experiment 5: genau k Nächte, n = 10 | k = 0 bis 7: 1.024, 2.816, 4.096, 3.472, 1.852, 571, 91, 4 Wörter; Rejection aus der Gesamtmenge 13,6, 4,95, 3,40, 4,01, 7,52, 24,4, 153, 3.481,5 Versuche; n = 100 mit k = 38 (Mittel + 4σ): Anteil 2,88·10⁻⁵, 34.694 Versuche; n = 400 mit k = 118: 2,09·10⁻⁵, 47.890 |
| Experiment 5: Netz 7×7, Kosten 1 oder 2, Seed 20261109 | 924 Wege, kleinste Kosten 14, 10 optimale Wege (Aufzählen und Semiring); Sampler z = −0,75; naiv Abstand 0,150 (Faktor 2 zwischen größter und kleinster Wahrscheinlichkeit); 12×12: 705.432 Wege, 26 optimale; 20×20: 3,5·10¹⁰, 126; 30×30: 3,0·10¹⁶, 139.320 |
| Spielwiese (n = 100, Fenster 90 bis 110) | F = 1 + z·F²: ρ = 0,25, τ = 2, erwartet 170 Versuche je Treffer; F = 1 + z·F + z·F² + z²·F²: ρ = 0,154701, τ = 2,366025, erwartet 139; F = 1 + 2z·F + 3z²·F² (n = 150): ρ = 0,183013, τ = 3,154701, erwartet 119 |

## Ehrliche Grenzen

- **Literaturwerte aus dem Gedächtnis:** Boltzmann-Sampler (Duchon, Flajolet, Louchard, Schaeffer), die rekursive Methode (Nijenhuis, Wilf; Flajolet, Zimmermann, Van Cutsem) und der Stirling-Sampler wurden nicht an einer Quelle gelesen. Der Bruch je Objekt, das Aufzählen und die Chi-Quadrat-Bänder stützen sie, das ersetzt keine Quelle.
- **Stichproben beweisen nichts:** Ein exakter Sampler liegt in etwa 4 bis 5 % der Fälle außerhalb von ±2 Standardabweichungen; der Beweis der Gleichverteilung ist der Bruch je Objekt (bis 20.000 Objekte), darüber nur die Kenngröße.
- **Nur gezählte Familien:** Ohne Fortsetzungszahlen (zum Beispiel bei #P-schweren Mengen) bleibt nur Rejection oder ein Markov-Ketten-Sampler (nur im Grenzwert gleichverteilt, Stück 15); beides ist nicht Teil der Demo.
- **Boltzmann nur für Catalan-Bäume als Objekt:** Für Motzkin-Bäume und die eigene Gleichung wird nur die Größenverteilung gezogen, nicht ein Wort.
- **Obergrenzen:** 1,5 Millionen Rechenschritte je Auswertung; n bis 200 (Mengenpartitionen bis 100); Objekte werden nur bis 20.000 aufgezählt.
- **Aufwand als Schritte**, nicht als Zeit; die Zeiten aus Phase 0 sind Python-Messungen dieses Rechners und stehen in keinem Test.
- **Browser:** Seitentext, Zahlen, Diagrammbreiten, Preset-Klick im Browser geprüft; Handy-Breite nicht.
- Alles gerechnet, keine echten Daten.

## Verifikation

- **Kern:** Handinstanzen (Schichtfolgen n = 3 mit Rang und beiden Wahrscheinlichkeiten, Dyck n = 3, Mengenpartitionen n = 3, Derangements n = 3, Boltzmann-Wahrscheinlichkeiten, 2×2-Netz), Aufzählen aller Objekte durch Brute Force, Bijektion von Rang und Objekt für jede Familie (der Sampler mit festem Rang liefert genau das r-te Objekt), Wahrscheinlichkeit jedes Objekts als Bruch, naiver Gang gegen eine unabhängige Verzweigung, Stirling-Zahlen gegen die Summenformel, Boltzmann-Größenverteilung gegen die Verzweigungsgleichung (nicht gegen die Catalan-Formel), Netz-Semiring gegen das Aufzählen aller Wege.
- **Eigenschaften:** jede Familie mit jedem Verfahren zieht nur gültige Objekte; gleicher Seed gleiche Ziehungen; Abstand des naiven Gangs wächst mit n; erwartete Versuche der Rejection gleich Vorschläge durch Objekte und monoton in n; Kenngröße passt zur exakten Verteilung (und der naive Gang nicht); Bedingung liefert nur Wörter mit k Nächten; Fenstergrenzen ganzzahlig; Chi-Quadrat nur bei genug Ziehungen.
- **Randfälle:** Größen unter und über den Grenzen, Verfahren ohne Familie mit Hinweis, k über dem Möglichen, Schrittgrenze und Abbruch mit Meldung, Zahlen über der 4300-Stellen-Grenze nur formatiert, Spielwiese mit 27 Koeffizientenkombinationen (trivial, periodisch, linear, Wurzel), Formatierung.
- **Urteilstexte:** genauer Wortlaut für alle Voreinstellungen und Experimente.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum), jede Familie, jedes Preset, Permalink mit Müll, Spielwiese, PDF, eindeutige Diagrammschlüssel; Footer-Test; Layout-Test.
- **Nicht gemacht:** Mutationstests (seit 2026-10-28 nicht mehr verlangt), Docker-Lauf der Linux-CI (Docker fehlt auf diesem Rechner; die CI nach dem Push entscheidet).

121 Tests (`pytest tests`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Ergebnis, Kernfrage, fünf Experimente, Spielwiese, Grenzen, Formeln |
| `gvz_algorithm.py` | Kern: Tabellen, Entrollen, Rejection, naiver Gang, Boltzmann, Stirling-Sampler, Netz |
| `gvz_constants.py` | Regler-Grenzen, Experiment-Konstanten, Farben, Presets |
| `gvz_evaluation.py` | Analyse, Experimente, Urteilstexte, Formatierung |
| `gvz_layout.py` | Fester Kopf (Stylesheet) |
| `gvz_pdf_export.py` | PDF der aktuellen Ziehung (fpdf2) |
| `gvz_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben) |
| `gvz_scenario.py` | Familie aus der Auswahl: Tabellen, Aufzählen, Ziehung je Verfahren |
| `gvz_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handwerte, Orakel, Eigenschaften, Randfälle, Urteilstexte, Claims, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Markov-Ketten-Sampler (MCMC, Mischzeit, Kopplung aus der Vergangenheit), approximative Sampler, Ziehen aus #P-schweren Mengen:** Stück 15 (Schätzen).
- **Boltzmann-Sampler für Multimengen, Zyklen und Mengen (Pólya):** Stück 11.
- **Zufallspermutationen (Fisher–Yates) und Wilsons Algorithmus für Spannbäume:** `random-spanning-tree-demo` (nur verwiesen).
- **Beweise der Sampler:** Die Demo rechnet die Wahrscheinlichkeit jedes Objekts nach; die Beweise stehen in der Literatur.
- **Verwandte Demos:** `symbolische-methode-demo` (Gleichung und Bäume), `zaehlen-nach-parameter-demo` (Bedingung), `semiring-rekursion-demo` (optimale Lösungen zählen), `asymptotik-demo` (ρ, τ, Fenster); nur Verweise.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python-Version nach der Voreinstellung der Plattform (lokal `3.14`, CI `3.12`); der Code nutzt nur Merkmale, die in `3.12` laufen.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Abzählen: von der Rekursion zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-abzaehlen.html).
