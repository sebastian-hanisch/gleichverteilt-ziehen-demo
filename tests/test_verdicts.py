"""Urteilstexte (Schicht 3): die Texte, die die App zeigt, mit genauem Wortlaut für die Standardfälle, damit jede Zahl darin geprüft ist."""

import gvz_constants as C
import gvz_evaluation as ev

S = ev.Settings


def answer(name):
    return ev.verdict_answers(ev.analyse(S(**C.PRESETS[name])))


def test_answer_standard_case_exact():
    kind, text = answer("Standardfall: Schichtfolgen, n = 10")
    assert kind == "success"
    assert text == "Rekursions-Sampler, Schichtfolgen, n = 10: 13.926 Objekte, jedes mit der Wahrscheinlichkeit 1/13.926 (für alle 13.926 Objekte als Bruch nachgerechnet). 2000 Ziehungen, 10 Schritte je Objekt."


def test_answer_naive_walk_exact():
    kind, text = answer("Naiver Gang ist verzerrt, n = 8")
    assert kind == "warning"
    assert text == "Naiver Gang, Schichtfolgen, n = 8: nicht gleichverteilt. Abstand zur Gleichverteilung 0,336, das wahrscheinlichste Objekt kommt 9,9-mal so oft vor wie bei Gleichverteilung. 5000 Ziehungen."


def test_answer_rejection_exact():
    kind, text = answer("Rejection wird teuer: n = 40")
    assert kind == "success"
    assert text == ("Rejection, Schichtfolgen, n = 40: im Mittel 489 Versuche je Objekt, erwartet 577; 19.560 Rechenschritte je Objekt. 5 Ziehungen. "
                    "Gleichverteilt, weil jedes gültige Objekt gleich oft vorgeschlagen wird.")


def test_answer_conditioned_and_boltzmann():
    kind, text = answer("Genau k Nächte: k = 7, n = 10")
    assert kind == "success" and "4 Objekte, jedes mit der Wahrscheinlichkeit 1/4" in text and "Chi-Quadrat 7,3 bei 3 Freiheitsgraden (z = 1,77)" in text
    kind, text = answer("Catalan-Bäume per Boltzmann, n = 100")
    assert kind == "success" and text.startswith("Boltzmann-Sampler, Catalan-Bäume, Größe 90 bis 110: im Mittel 121 Bäume je Treffer, erwartet 170;") and "gegen 200 beim Rekursions-Sampler. 50 Ziehungen." in text


def test_answer_other_families_exact_counts():
    for name, total, z in (("Dyck-Wörter exakt, n = 6", "132", "0,04"), ("Motzkin-Wörter, n = 8", "323", "−0,19"), ("Mengenpartitionen, n = 7", "877", "−1,70")):
        kind, text = answer(name)
        assert kind == "success" and f"{total} Objekte, jedes mit der Wahrscheinlichkeit 1/{total}" in text and f"(z = {z})" in text, name


def test_answer_error_when_the_ways_disagree():
    a = ev.analyse(S(**C.PRESETS["Standardfall: Schichtfolgen, n = 10"]))
    a.problems.append("zwei Wege weichen ab")
    assert ev.verdict_answers(a) == ("error", "Die Rechenwege widersprechen sich: zwei Wege weichen ab")


def test_answer_rows_of_the_standard_case():
    rows = ev.answer_rows(ev.analyse(S(**C.PRESETS["Standardfall: Schichtfolgen, n = 10"])))
    by = {r["Frage"]: r for r in rows}
    assert by["Zahl der Objekte"]["Ergebnis"] == "13.926" and by["Wahrscheinlichkeit je Objekt"]["Ergebnis"] == "1/13.926"
    assert "mindestens 69.630" in by["Chi-Quadrat der Ziehungen"]["Prüfung"] and by["Versuche je Objekt"]["Ergebnis"] == "1"


def test_uniformity_verdict_exact():
    kind, text = ev.verdict_uniformity(ev.uniformity_rows())
    assert kind == "success"
    assert text == ("8 Kombinationen aus Familie und exaktem Verfahren ohne Verzerrung: z-Werte zwischen −1,53 und 1,14 (gleichverteilt: etwa −3 bis 3); "
                    "der naive Gang liegt bei z = 447, 1056, 428, 738 und im Abstand 0,18 bis 0,31 zur Gleichverteilung.")


def test_naive_verdict_exact():
    kind, text = ev.verdict_naive(ev.naive_rows())
    assert kind == "warning"
    assert text.startswith("Der naive Gang ist bei allen drei Familien verzerrt; bei den Schichtfolgen wächst der Abstand zur Gleichverteilung von 0,156 (n = 3) auf 0,391 (n = 12), dort kommt das wahrscheinlichste Wort 69,7-mal so oft vor wie gerecht.")


def test_rejection_verdict_exact():
    kind, text = ev.verdict_rejection(ev.rejection_rows())
    assert kind == "warning"
    assert text == ("Rejection kostet je nach Familie ganz Verschiedenes: Schichtfolgen 112 Versuche bei n = 30 und 1,07·10⁷ bei n = 100 (Faktor 1,178 je Schritt, exponentiell), "
                    "Dyck-Wörter 302 und 1.792 (etwa √π·n^(3/2), polynomiell), Derangements immer etwa e = 2,718. Ob Rejection taugt, hängt von der Wachstumsrate der Objekte gegen die der Vorschläge ab (Stück 9).")


def test_boltzmann_verdict_exact():
    kind, text = ev.verdict_boltzmann(ev.boltzmann_distribution(), ev.window_rows(), ev.x_rows())
    assert kind == "success"
    assert text == ("Die Größe der Boltzmann-Bäume folgt c_n·ρⁿ/τ (z = −0,41, 1,18). Ein Fenster ±10 % um n kostet 1/P(Fenster) Versuche: bei n = 1000 erwartet 555, gemessen 558 "
                    "(größte Abweichung über alle Größen 7 %; bei 60 Treffern ist ein Standardfehler von etwa 13 % Zufall), 40.446 Rechenschritte je Treffer gegen 2000 beim Rekursions-Sampler, aber ohne Tabelle. "
                    "Am besten ist x = ρ (t = 1,000): kleiner gewählte x machen das Fenster seltener, und der Mittelwert der Größe ist bei x = ρ unendlich.")


def test_condition_verdict_exact():
    kind, text = ev.verdict_condition(ev.condition_rows(), ev.grid_experiment())
    assert kind == "success"
    assert text == ("Mit der Bedingung „genau k Nächte“ zieht die Tabelle gezielt: bei n = 10 haben nur 4 von 13.926 Schichtfolgen 7 Nächte, Rejection aus der Gesamtmenge bräuchte 3.482 Versuche; "
                    "bei n = 400 mit k = 118 (Mittel plus vier Standardabweichungen) 47.890. Im Netz 7×7 gibt es 10 optimale von 924 Wegen (Semiring und Aufzählen stimmen überein); "
                    "der Sampler nach Zahl der optimalen Fortsetzungen ist gleichverteilt (z = −0,75), der naive Gang unter den optimalen Kanten nicht (Abstand 0,150).")


def test_play_verdicts_exact():
    kind, text = ev.verdict_play(ev.play_equation(0, 1, 0, 100))
    assert kind == "success"
    assert text == ("F = 1 + z·F²: ρ = 0,250000, τ = 2,000000; Blatt mit Wahrscheinlichkeit 1/τ = 0,5000. Fenster 90 bis 110: P(Fenster) = 5,90·10⁻³, erwartet 170 Versuche je Treffer, gemessen 174 (20 Treffer), "
                    "3.677 Rechenschritte je Treffer gegen 200 bei einer Tabelle (Größe n).")
    assert ev.verdict_play(ev.play_equation(0, 0, 0, 100))[0] == "info"
    kind, text = ev.verdict_play(ev.play_equation(0, 0, 1, 100))
    assert kind == "warning" and "Periode 2" in text and "mindestens ein Term mit z¹" in text
    kind, text = ev.verdict_play(ev.play_equation(1, 0, 0, 100))
    assert kind == "info" and text.startswith("Die Gleichung ist linear: F = 1/(1 − z), die Zahl der Objekte der Größe n ist 1ⁿ.") and text.endswith("Bitte c₂ oder c₃ wählen.")
    assert "F = 1/(1 − 3z)" in ev.verdict_play(ev.play_equation(3, 0, 0, 100))[1] and "3ⁿ" in ev.verdict_play(ev.play_equation(3, 0, 0, 100))[1]
