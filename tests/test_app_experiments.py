"""Oberfläche: jede Familie, jedes Preset, Permalink mit Müll, die Spielwiese und das PDF laufen ohne Ausnahme und zeigen die erwarteten Texte."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import gvz_constants as C
import gvz_evaluation as ev
import gvz_visualization as V

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _run(query=None, **state):
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for key, value in (query or {}).items():
        at.query_params[key] = value
    at.run()
    for key, value in state.items():
        at.session_state[key] = value
    if state:
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [e.value for e in at.success] + [e.value for e in at.warning] + [e.value for e in at.info] + [e.value for e in at.error]


def test_standard_case_shows_all_five_experiments_and_the_answer():
    at = _run()
    heads = [s.value for s in at.subheader]
    assert [h for h in heads if h.startswith("🔬 Experiment")] == ["🔬 Experiment 1: Dieselbe Aufgabe auf allen Wegen", "🔬 Experiment 2: Der naive Gang ist verzerrt", "🔬 Experiment 3: Rejection kostet je Familie etwas anderes",
                                                                   "🔬 Experiment 4: Boltzmann-Sampler und das Größenfenster", "🔬 Experiment 5: Ziehen mit Bedingung und die zufällige optimale Lösung"]
    assert any(t.startswith("Rekursions-Sampler, Schichtfolgen, n = 10: 13.926 Objekte") for t in _texts(at)) and not at.error


def test_metrics_of_the_standard_case():
    at = _run()
    values = {m.label: m.value for m in at.metric}
    assert values == {"Zahl der Objekte": "13.926", "Versuche je Objekt": "1", "Rechenschritte je Objekt": "10", "Wahrscheinlichkeit je Objekt": "exakt gleich"}


def test_every_preset_runs_and_shows_its_family():
    for name, preset in C.PRESETS.items():
        at = _run(family_select=preset["family"], method_select=preset["method"], n_slider=preset["n"], k_slider=preset["k"], window_slider=preset["window"], draws_slider=preset["draws"], seed_slider=preset["seed"])
        assert at.selectbox(key="family_select").value == preset["family"], name
        assert not at.error, name


def test_naive_walk_shows_the_distance_metric():
    at = _run(method_select="Naiver Gang", n_slider=8)
    values = {m.label: m.value for m in at.metric}
    assert values["Abstand zur Gleichverteilung"] == "0,336"


def test_unavailable_method_shows_a_note():
    at = _run(family_select="Mengenpartitionen", method_select="Boltzmann mit Größenfenster", n_slider=6)
    assert any("gibt es für diese Familie nicht" in t for t in _texts(at))


def test_permalink_garbage_falls_back_to_defaults():
    at = _run(query={"family": "Unsinn", "method": "Zauber", "n": "abc", "k": "99999", "draws": "-5"})
    assert at.selectbox(key="family_select").value == C.DEFAULT_FAMILY and at.selectbox(key="method_select").value == C.DEFAULT_METHOD
    assert at.slider(key="n_slider").value == C.DEFAULT_N and at.slider(key="k_slider").value == C.K_MAX and at.slider(key="draws_slider").value == C.DRAWS_MIN


def test_play_ground_all_kinds():
    for (c1, c2, c3), word in (((0, 1, 0), "F = 1 + z·F²"), ((1, 0, 0), "linear"), ((0, 0, 1), "Periode 2"), ((0, 0, 0), "leere Struktur"), ((3, 3, 3), "ρ =")):
        at = _run(play_c1=c1, play_c2=c2, play_c3=c3)
        assert any(word in t for t in _texts(at)), (c1, c2, c3)


def test_pdf_button_makes_a_download():
    at = _run()
    at.button(key="pdf_make").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert len(at.get("download_button")) == 1


def test_charts_have_unique_keys():
    at = _run(n_slider=6, draws_slider=3000)
    keys = [c.key for c in at.get("plotly_chart")]
    assert len(keys) == len(set(keys)) and {"main_chart", "stat_chart", "naive_chart", "rejection_chart", "boltz_chart", "window_chart", "x_chart", "cond_chart", "play_chart"} <= set(keys)


def test_pdf_builds_for_every_family_and_method():
    from gvz_pdf_export import build_pdf
    for fam in C.FAMILIES:
        for method in C.AVAILABLE[fam]:
            a = ev.analyse(ev.Settings(fam, method, 6, 2, 10, 30, 1))
            assert build_pdf(a)[:4] == b"%PDF", (fam, method)


def test_chart_builders_return_locked_axes():
    a = ev.analyse(ev.Settings("Schichtfolgen", "Rekursions-Sampler", 6, 0, 0, 500, 1))
    for fig in (V.build_counts_chart(a.extras["counts"], 1.0), V.build_stat_chart(a.extras["stat"], "Zahl der Nachtschichten")):
        assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
