"""Jede Zahl aus der README und aus den Texten der App, nachgerechnet (DEMO-PLAYBOOK §4). Stichproben auf festen Seeds sind Bänder; Zeiten kommen nicht vor."""

import math
from fractions import Fraction
from pathlib import Path

import pytest

import gvz_algorithm as A
import gvz_constants as C
import gvz_evaluation as ev
import gvz_scenario as S

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
SETTINGS = ev.Settings


def test_readme_hand_instances():
    comp = A.shift_completions(3)
    assert comp[3][0] == 20 and A.shift_unrank(3, 0, comp) == "FFF" and A.shift_unrank(3, 9, comp) == "NSF" and A.shift_unrank(3, 19, comp) == "SSS"
    assert A.shift_recursion_probability("NSF", comp) == Fraction(1, 20) and A.shift_naive_probability("NSF") == Fraction(1, 18)
    assert [A.ballot_table(3)[i][0] for i in (0, 2, 4, 6)] == [1, 1, 2, 5] and A.bell_number(3) == 5 and A.stirling2_table(3)[3] == [0, 1, 3, 1]
    assert A.derangement_expected_tries(3) == 3


def test_readme_standard_case():
    a = ev.analyse(SETTINGS(**C.PRESETS["Standardfall: Schichtfolgen, n = 10"]))
    assert a.total == 13926 and a.exact_uniform is True
    assert A.night_counts(10) == [1024, 2816, 4096, 3472, 1852, 571, 91, 4]
    assert A.digit_count(A.shift_completions(60)[60][0]) == 25


def test_readme_experiment_1_table():
    rows = {(r["Familie"], r["Verfahren"]): r for r in ev.uniformity_rows()}
    shift = lambda m: rows[("Schichtfolgen", m)]
    assert shift("Rekursions-Sampler")["Objekte"] == 843 and [round(shift(m)["z"], 2) for m in ("Rekursions-Sampler", "Rejection")] == [0.51, 0.93]
    assert round(shift("Rejection")["Versuche"], 2) == 2.57 and round(3 ** 7 / 843, 2) == 2.59 and round(shift("Naiver Gang")["z"]) == 447 and round(shift("Naiver Gang")["TV"], 3) == 0.313
    dyck = lambda m: rows[("Dyck-Wörter (Catalan)", m)]
    assert dyck("Rekursions-Sampler")["Objekte"] == 14
    assert [round(dyck(m)["z"], 2) for m in ("Rekursions-Sampler", "Rejection", "Boltzmann mit Größenfenster")] == [0.28, -1.53, 1.14]
    assert round(dyck("Rejection")["Versuche"], 1) == 18.2 and round(256 / 14, 1) == 18.3 and round(dyck("Boltzmann mit Größenfenster")["Versuche"], 1) == 36.8 and round(2 * 256 / 14, 1) == 36.6
    assert round(dyck("Naiver Gang")["z"]) == 1056 and round(dyck("Naiver Gang")["TV"], 3) == 0.214
    mot = lambda m: rows[("Motzkin-Wörter", m)]
    assert mot("Rekursions-Sampler")["Objekte"] == 51 and [round(mot(m)["z"], 2) for m in ("Rekursions-Sampler", "Rejection")] == [0.53, 0.07]
    assert round(mot("Naiver Gang")["z"]) == 428 and round(mot("Naiver Gang")["TV"], 3) == 0.176
    part = lambda m: rows[("Mengenpartitionen", m)]
    assert part("Rekursions-Sampler")["Objekte"] == 52 and round(part("Rekursions-Sampler")["z"], 2) == -0.29 and round(part("Naiver Gang")["z"]) == 738 and round(part("Naiver Gang")["TV"], 3) == 0.212


def test_readme_experiment_2_naive_distances():
    rows = ev.naive_rows()
    pick = lambda fam: [r for r in rows if r["Familie"] == fam]
    assert [round(r["TV"], 3) for r in pick("Schichtfolgen")] == [0.156, 0.251, 0.336, 0.363, 0.391]
    assert [round(r["häufigstes Objekt (mal gerecht)"], 1) for r in pick("Schichtfolgen")] == [3.3, 3.6, 9.9, 21.5, 69.7]
    assert [round(r["TV"], 3) for r in pick("Dyck-Wörter (Catalan)")] == [0.15, 0.283, 0.409, 0.455]
    assert [round(r["TV"], 3) for r in pick("Mengenpartitionen")] == [0.1, 0.167, 0.212, 0.278, 0.337, 0.388]
    assert all(r["Summe"] == pytest.approx(1) for r in rows)


def test_readme_experiment_3_rejection():
    res = ev.rejection_rows()
    by = {r["n"]: r for r in res["rows"]}
    assert [float(f"{by[n]['Schichtfolgen']:.3g}") for n in C.EXP_REJECT_NS] == [4.24, 21.8, 112.0, 577.0, 15300.0, 1.07e7, 1.38e14]
    assert round(by[60]["Schichtfolgen"]) == 15260 and round(res["growth"], 4) == 1.1779 and round(3 / 2.5468, 4) == 1.1779
    assert [round(by[n]["Dyck-Wörter"], 1) for n in (10, 20, 30, 40, 60, 100, 200)] == [62.4, 167.5, 302.2, 461.0, 839.2, 1792.4, 5041.5]
    assert [round(by[n]["Dyck / (√π·n^1,5)"], 3) for n in (10, 200)] == [1.114, 1.006]
    assert [round(by[n]["Motzkin-Wörter"], 1) for n in (10, 20, 30, 40, 60, 100, 200)] == [27.0, 68.6, 121.3, 183.2, 330.0, 698.9, 1953.2]
    assert all(round(r["Derangements"], 3) == 2.718 for r in res["rows"])
    meas = {m["Familie"]: m for m in res["measured"]}
    assert [round(meas[f]["gemessen"], 1) for f in ("Schichtfolgen", "Dyck-Wörter (Catalan)", "Motzkin-Wörter")] == [22.4, 165.8, 69.2] and round(meas["Derangements"]["gemessen"], 2) == 2.67
    assert [round(meas[f]["erwartet"], 1) for f in ("Schichtfolgen", "Dyck-Wörter (Catalan)", "Motzkin-Wörter")] == [21.8, 167.5, 68.6]
    assert all(m["Ziehungen"] == 400 for m in res["measured"])


def test_readme_experiment_4_boltzmann():
    dist = ev.boltzmann_distribution()
    assert [round(d["chi"], 1) for d in dist] == [10.9, 19.0] and [round(d["z"], 2) for d in dist] == [-0.41, 1.18]
    assert [(round(d["rho"], 6), round(d["tau"], 6)) for d in dist] == [(0.25, 2.0), (round(1 / 3, 6), 3.0)]
    w = ev.window_rows()
    assert [float(f"{r['P(Fenster)']:.3g}") for r in w] == [5.90e-3, 2.87e-3, 1.80e-3] and [round(r["Versuche erwartet"]) for r in w] == [170, 349, 555]
    assert [round(r["Versuche gemessen"]) for r in w] == [157, 331, 558] and [r["Treffer"] for r in w] == [200, 120, 60]
    assert [round(r["Schritte je Treffer"]) for r in w] == [3406, 14991, 40446] and [r["Rekursions-Sampler"] for r in w] == [200, 800, 2000]
    xs = ev.x_rows()
    assert [float(f"{r['Versuche']:.2g}") for r in xs] == [2.4e11, 3.8e6, 22000.0, 1100.0, 420.0, 180.0, 170.0]
    assert [round(r["Versuche"]) for r in xs[2:]] == [21709, 1100, 418, 182, 170]
    assert [round(r["Mittel der Größe"], 2) for r in xs[:6]] == [0.62, 1.08, 1.74, 3.04, 4.5, 13.07] and xs[-1]["Mittel der Größe"] == math.inf


def test_readme_experiment_5_conditions_and_grid():
    cond = ev.condition_rows()
    assert [r["Objekte"] for r in cond["rows"]] == [1024, 2816, 4096, 3472, 1852, 571, 91, 4]
    assert [round(r["Rejection (Versuche)"], 2) for r in cond["rows"]] == [13.6, 4.95, 3.4, 4.01, 7.52, 24.39, 153.03, 3481.5]
    assert [(f["n"], f["k"], float(f"{f['Anteil']:.3g}"), round(f["Versuche"])) for f in cond["far"]] == [(100, 38, 2.88e-5, 34694), (400, 118, 2.09e-5, 47890)]
    grid = ev.grid_experiment()
    assert (grid["paths"], grid["best"], grid["optimal"], grid["semiring_count"]) == (924, 14, 10, 10) and round(grid["z"], 2) == -0.75 and round(grid["tv"], 3) == 0.15 and grid["max_factor"] == 2.0
    assert [(f["alle Wege"], f["kleinste Kosten"], f["optimale Wege"]) for f in grid["sizes"]] == [(705432, 26, 26), (35345263800, 41, 126), (30067266499541040, 65, 139320)]
    assert C.EXP_SEED + 7 == 20261109


def test_readme_play_equations():
    for c, n, rho, tau, expected in (((0, 1, 0), 100, 0.25, 2.0, 170), ((1, 1, 1), 100, 0.154701, 2.366025, 139), ((2, 0, 3), 150, 0.183013, 3.154701, 119)):
        res = ev.play_equation(*c, n)
        assert (round(res["rho"], 6), round(res["tau"], 6)) == (rho, tau) and round(res["tries_expected"]) == expected, c


def test_preset_help_claims():
    h = C.PRESET_HELP
    assert "13.926" in h["Standardfall: Schichtfolgen, n = 10"]
    naive = ev.analyse(SETTINGS(**C.PRESETS["Naiver Gang ist verzerrt, n = 8"]))
    assert round(naive.tv, 3) == 0.336 and round(naive.max_factor, 1) == 9.9 and "0,336" in h["Naiver Gang ist verzerrt, n = 8"] and "9,9-mal" in h["Naiver Gang ist verzerrt, n = 8"]
    ctx40, ctx100 = S.build_context("Schichtfolgen", 40), S.build_context("Schichtfolgen", 100)
    assert round(float(S.expected_tries(ctx40, "Rejection"))) == 577 and f"{float(S.expected_tries(ctx100, 'Rejection')):.1e}" == "1.1e+07" and "577" in h["Rejection wird teuer: n = 40"] and "10 Millionen" in h["Rejection wird teuer: n = 40"]
    k7 = S.build_context("Schichtfolgen mit k Nächten", 10, 7)
    assert k7.total == 4 and float(S.expected_tries(k7, "Rejection")) == 3481.5 and "3.481,5" in h["Genau k Nächte: k = 7, n = 10"]
    boltz = ev.analyse(SETTINGS(**C.PRESETS["Catalan-Bäume per Boltzmann, n = 100"]))
    assert boltz.window == (90, 110) and round(boltz.tries_expected) == 170 and "170" in h["Catalan-Bäume per Boltzmann, n = 100"] and boltz.steps_mean > 10 * 200
    assert S.build_context("Dyck-Wörter (Catalan)", 6).total == 132 and round(5000 / 132) == 38
    assert S.build_context("Motzkin-Wörter", 8).total == 323 and S.build_context("Mengenpartitionen", 7).total == 877


def test_readme_states_the_test_count_and_ends_with_the_footer():
    assert "Stück 10 von 16" in README and "Gleichverteilt ziehen" in README and "TESTCOUNT" not in README
    assert README.rstrip().endswith("[Abzählen: von der Rekursion zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-abzaehlen.html).")
