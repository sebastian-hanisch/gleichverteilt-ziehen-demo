"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

FAMILIES = ("Schichtfolgen", "Schichtfolgen mit k Nächten", "Dyck-Wörter (Catalan)", "Motzkin-Wörter", "Mengenpartitionen")
DEFAULT_FAMILY = "Schichtfolgen"
METHODS = ("Rekursions-Sampler", "Rejection", "Boltzmann mit Größenfenster", "Naiver Gang")
DEFAULT_METHOD = "Rekursions-Sampler"
AVAILABLE = {"Schichtfolgen": ("Rekursions-Sampler", "Rejection", "Naiver Gang"),
             "Schichtfolgen mit k Nächten": ("Rekursions-Sampler", "Rejection"),
             "Dyck-Wörter (Catalan)": ("Rekursions-Sampler", "Rejection", "Boltzmann mit Größenfenster", "Naiver Gang"),
             "Motzkin-Wörter": ("Rekursions-Sampler", "Rejection", "Naiver Gang"),
             "Mengenpartitionen": ("Rekursions-Sampler", "Naiver Gang")}

N_MIN, N_MAX, DEFAULT_N = 3, 200, 10
N_CAP = {"Schichtfolgen": 200, "Schichtfolgen mit k Nächten": 200, "Dyck-Wörter (Catalan)": 200, "Motzkin-Wörter": 200, "Mengenpartitionen": 100}   # größtes n je Familie
K_MIN, K_MAX, DEFAULT_K = 0, 120, 4                    # Zahl der Nächte (nur Familie mit Bedingung)
WINDOW_MIN, WINDOW_MAX, DEFAULT_WINDOW = 0, 20, 10     # Größenfenster ± Prozent (nur Boltzmann); 0 = genau n
DRAWS_MIN, DRAWS_MAX, DEFAULT_DRAWS = 1, 20000, 2000
SEED_MIN, SEED_MAX, DEFAULT_SEED = 1, 999, 20

ENUM_MAX = 20000                # bis zu dieser Gesamtzahl werden alle Objekte aufgezählt (exakte Wahrscheinlichkeit, Chi-Quadrat)
MIN_EXPECTED = 5                # Chi-Quadrat nur, wenn jede Zelle im Mittel mindestens so viele Ziehungen erwartet
MAX_STEPS = 1_500_000           # Obergrenze der Rechenschritte für Rejection und Boltzmann in einer Auswertung
MAX_TRIES_PER_OBJECT = 100_000  # Obergrenze der Versuche je Objekt
SHOW_OBJECTS = 6                # so viele gezogene Objekte werden gezeigt
BOLTZMANN_CAP_FACTOR = 1        # Abbruch eines Baums bei Größe über (1 + Fenster)·n; bei Fenster 0 genau n

EXP_SHIFT_N = 7                 # Experiment 1: Schichtfolgen n = 7 und Dyck n = 4, alle Verfahren
EXP_DYCK_N = 4
EXP_DRAWS = 20000
EXP_NAIVE_NS = (3, 5, 8, 10, 12)        # Experiment 2: Totalvariation des naiven Gangs
EXP_NAIVE_DYCK_NS = (3, 5, 8, 10)
EXP_NAIVE_PART_NS = (3, 4, 5, 6, 7, 8)
EXP_REJECT_NS = (10, 20, 30, 40, 60, 100, 200)          # Experiment 3: erwartete Versuche
EXP_REJECT_MEASURE_N = 20
EXP_REJECT_DRAWS = 400
EXP_BOLTZ_DRAWS = 40000          # Experiment 4: Größenverteilung
EXP_BOLTZ_CAP = 2000
EXP_WINDOW_NS = (100, 400, 1000)
EXP_WINDOW_DRAWS = (200, 120, 60)
EXP_WINDOW_EPS = 0.1
EXP_X_TS = (0.80, 0.90, 0.95, 0.98, 0.99, 0.999, 1.0)
EXP_COND_N = 10                  # Experiment 5: Bedingung und Netz
EXP_COND_DRAWS = 20000
EXP_GRID = 7
EXP_GRID_DRAWS = 30000
EXP_GRID_SIZES = (12, 20, 30)
EXP_SEED = 20261102
PLAY_N_MIN, PLAY_N_MAX, PLAY_N_DEFAULT = 20, 200, 100   # Spielwiese: eigene Gleichung
PLAY_C_MAX = 3
PLAY_DRAWS = 20
PLAY_HIST_DRAWS = 4000
PLAY_CAP = 2000

COLOR_MAIN = "#2F6B65"
COLOR_ALL = "rgba(150,150,150,0.75)"
COLOR_WARN = "#c0504d"
COLOR_LINE = "#4c78a8"

PRESETS = {
    "Standardfall: Schichtfolgen, n = 10": {"family": "Schichtfolgen", "method": "Rekursions-Sampler", "n": 10, "k": 4, "window": 10, "draws": 2000, "seed": 20},
    "Naiver Gang ist verzerrt, n = 8": {"family": "Schichtfolgen", "method": "Naiver Gang", "n": 8, "k": 4, "window": 10, "draws": 5000, "seed": 20},
    "Rejection wird teuer: n = 40": {"family": "Schichtfolgen", "method": "Rejection", "n": 40, "k": 4, "window": 10, "draws": 5, "seed": 20},
    "Genau k Nächte: k = 7, n = 10": {"family": "Schichtfolgen mit k Nächten", "method": "Rekursions-Sampler", "n": 10, "k": 7, "window": 10, "draws": 2000, "seed": 20},
    "Catalan-Bäume per Boltzmann, n = 100": {"family": "Dyck-Wörter (Catalan)", "method": "Boltzmann mit Größenfenster", "n": 100, "k": 4, "window": 10, "draws": 50, "seed": 20},
    "Dyck-Wörter exakt, n = 6": {"family": "Dyck-Wörter (Catalan)", "method": "Rekursions-Sampler", "n": 6, "k": 4, "window": 10, "draws": 5000, "seed": 20},
    "Motzkin-Wörter, n = 8": {"family": "Motzkin-Wörter", "method": "Rekursions-Sampler", "n": 8, "k": 4, "window": 10, "draws": 5000, "seed": 20},
    "Mengenpartitionen, n = 7": {"family": "Mengenpartitionen", "method": "Rekursions-Sampler", "n": 7, "k": 4, "window": 10, "draws": 5000, "seed": 20},
}
PRESET_HELP = {
    "Standardfall: Schichtfolgen, n = 10": "13.926 gültige Schichtfolgen; der Rekursions-Sampler zieht jede mit genau der Wahrscheinlichkeit 1/13.926 (als Bruch gerechnet, nicht nur gemessen).",
    "Naiver Gang ist verzerrt, n = 8": "Wer den nächsten Buchstaben gleichverteilt unter den erlaubten wählt, zieht nicht gleichverteilt: Abstand zur Gleichverteilung 0,336, das häufigste Wort 9,9-mal so oft wie gerecht.",
    "Rejection wird teuer: n = 40": "Würfeln und Wegwerfen: bei n = 40 sind im Mittel 577 Versuche je Schichtfolge nötig, bei n = 100 schon rund 10 Millionen (Faktor 1,178 je Schritt).",
    "Genau k Nächte: k = 7, n = 10": "Nur 4 der 13.926 Schichtfolgen haben sieben Nächte; per Rejection aus der Gesamtmenge wären im Mittel 3.481,5 Versuche nötig, die Tabelle zieht gezielt.",
    "Catalan-Bäume per Boltzmann, n = 100": "Zufallsbäume ohne Tabelle bei x = ρ = 1/4: erwartet etwa 170 Versuche je Treffer im Fenster 90 bis 110, zusammen rund 3.400 Rechenschritte, das 17-Fache der 200 Rechenschritte der Tabelle.",
    "Dyck-Wörter exakt, n = 6": "132 Dyck-Wörter der Länge 12 (Catalan C₆); mit 5.000 Ziehungen wird jedes im Mittel etwa 38-mal gezogen.",
    "Motzkin-Wörter, n = 8": "323 Wege mit Schritten hoch, flach, runter; die Tabelle der Fortsetzungen zieht gleichverteilt.",
    "Mengenpartitionen, n = 7": "877 Mengenpartitionen von sieben Elementen (Bell B₇); der Stirling-Sampler zieht gleichverteilt, der naive Aufbau nicht.",
}
