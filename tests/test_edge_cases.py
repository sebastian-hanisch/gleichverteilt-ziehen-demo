"""Randfälle: Grenzen der Regler, unbekannte Eingaben, Verfahren ohne Familie, Abbrüche, riesige Zahlen, Formatierung."""

import pytest

import gvz_algorithm as A
import gvz_constants as C
import gvz_evaluation as ev
import gvz_scenario as S

SETTINGS = ev.Settings


def test_effective_n_clamps_to_range_and_family_cap():
    assert S.effective_n("Schichtfolgen", 0) == C.N_MIN
    assert S.effective_n("Schichtfolgen", 5000) == C.N_MAX
    assert S.effective_n("Mengenpartitionen", 150) == 100 and S.effective_n("Mengenpartitionen", 50) == 50
    with pytest.raises(ValueError):
        S.effective_n("Unbekannt", 10)


def test_unknown_family_or_method_is_rejected():
    with pytest.raises(ValueError):
        S.effective_method("Unbekannt", "Rejection")
    with pytest.raises(ValueError):
        S.effective_method("Schichtfolgen", "Unbekannt")
    with pytest.raises(ValueError):
        S.build_context("Unbekannt", 5)


def test_unavailable_method_falls_back_with_a_note():
    a = ev.analyse(SETTINGS("Mengenpartitionen", "Rejection", 6, 0, 0, 50, 1))
    assert a.method_eff == "Rekursions-Sampler" and a.notes == ["Das Verfahren „Rejection“ gibt es für diese Familie nicht: gezogen wird mit dem Rekursions-Sampler."]
    b = ev.analyse(SETTINGS("Schichtfolgen", "Boltzmann mit Größenfenster", 6, 0, 0, 50, 1))
    assert b.method_eff == "Rekursions-Sampler" and len(b.notes) == 1


def test_k_is_limited_to_the_largest_possible_number_of_nights():
    a = ev.analyse(SETTINGS("Schichtfolgen mit k Nächten", "Rekursions-Sampler", 5, 120, 0, 20, 1))
    assert a.k_eff == len(A.night_counts(5)) - 1 and a.total > 0 and a.problems == []
    assert any("höchstens" in note for note in a.notes)
    assert S.effective_k("Schichtfolgen", 5, 99) == 99          # andere Familien lassen k unberührt


def test_smallest_size_for_every_family_and_method():
    for fam in C.FAMILIES:
        for method in C.AVAILABLE[fam]:
            a = ev.analyse(SETTINGS(fam, method, 0, 0, 0, 20, 1))
            assert a.n_eff == C.N_MIN and a.problems == [] and a.draws_done == 20, (fam, method)
            assert any("gerechnet wird mit n = 3" in n for n in a.notes)


def test_largest_size_with_huge_numbers_does_not_need_string_conversion():
    a = ev.analyse(SETTINGS("Dyck-Wörter (Catalan)", "Rekursions-Sampler", 200, 0, 10, 5, 1))
    assert a.digits > 100 and a.enumerated is False and a.exact_uniform is None and "Stellen" in ev.big_text(a.total)
    b = ev.analyse(SETTINGS("Mengenpartitionen", "Rekursions-Sampler", 100, 0, 10, 5, 1))
    assert b.digits > 100 and b.draws_done == 5
    assert ev.big_text(10 ** 5000).endswith("(5001 Stellen)") and A.digit_count(10 ** 5000) == 5001


def test_rejection_that_cannot_succeed_stops_at_the_step_limit_and_says_so():
    a = ev.analyse(SETTINGS("Schichtfolgen", "Rejection", 100, 0, 0, 5, 1))
    kind, text = ev.verdict_answers(a)
    assert a.draws_done == 0 and a.stopped == "Schrittgrenze" and kind == "warning" and "kein Objekt gezogen" in text and "lohnt sich dieses Verfahren nicht" in text


def test_budget_stops_a_long_series_with_a_note_in_the_verdict():
    a = ev.analyse(SETTINGS("Dyck-Wörter (Catalan)", "Boltzmann mit Größenfenster", 100, 0, 0, 20000, 1), max_steps=200_000)
    assert 0 < a.draws_done < a.draws_wanted and a.stopped == "Schrittgrenze"
    assert "abgebrochen" in ev.verdict_answers(a)[1]


def test_draws_are_clamped():
    assert ev.analyse(SETTINGS("Schichtfolgen", "Rekursions-Sampler", 5, 0, 0, 0, 1)).draws_wanted == 1
    assert ev.analyse(SETTINGS("Schichtfolgen", "Rekursions-Sampler", 5, 0, 0, 10 ** 9, 1), max_steps=10).draws_wanted == C.DRAWS_MAX


def test_is_valid_detects_wrong_objects():
    ctx = S.build_context("Schichtfolgen", 3)
    assert ev.is_valid(ctx, "FSS") and not ev.is_valid(ctx, "NFS") and not ev.is_valid(ctx, "FS")
    ctx = S.build_context("Dyck-Wörter (Catalan)", 2)
    assert ev.is_valid(ctx, "(())") and not ev.is_valid(ctx, ")(")
    ctx = S.build_context("Schichtfolgen mit k Nächten", 3, 2)
    assert ev.is_valid(ctx, "NNS") and not ev.is_valid(ctx, "FSS")
    ctx = S.build_context("Mengenpartitionen", 3)
    assert ev.is_valid(ctx, (0, 1, 0)) and not ev.is_valid(ctx, (0, 2, 0)) and not ev.is_valid(ctx, (1, 0, 0))
    ctx = S.build_context("Motzkin-Wörter", 3)
    assert ev.is_valid(ctx, "UFD") and not ev.is_valid(ctx, "UUD")


def test_formatting_helpers():
    assert ev.de(-1.5, 1) == "−1,5" and ev.de(0, 2) == "0,00"
    assert ev.sci_text(0) == "0" and ev.sci_text(0.5) == "0,50" and ev.sci_text(1.23e-4, 3) == "1,23·10⁻⁴" and ev.sci_text(25000, 2) == "2,5·10⁴"
    assert ev.percent(0.01126, 3) == "1,126 %"
    assert ev.big_text(0) == "0" and ev.big_text(999999999999) == "999.999.999.999" and ev.big_text(10 ** 12) == "1,00·10¹² (13 Stellen)"
    assert ev.count_text(8.0) == "8" and ev.count_text(2.5) == "2,50" and ev.count_text(577.0) == "577" and ev.count_text(15260.4) == "15.260" and ev.count_text(1.0678e7) == "1,07·10⁷"


def test_play_equation_degenerate_kinds_and_clamping():
    assert ev.play_equation(0, 0, 0, 100)["kind"] == "trivial"
    assert ev.play_equation(0, 0, 1, 100)["kind"] == "periodic" and ev.play_equation(0, 0, 3, 100)["kind"] == "periodic"
    pole = ev.play_equation(2, 0, 0, 100)
    assert pole["kind"] == "pole" and pole["mu"] == 2
    clamped = ev.play_equation(99, -5, 0, 10 ** 6)
    assert clamped["n"] == C.PLAY_N_MAX and clamped["terms"] == [(C.PLAY_C_MAX, 1, 1)] and clamped["kind"] == "pole"
    assert ev.play_equation(0, 1, 0, 0)["n"] == C.PLAY_N_MIN


def test_play_equation_all_combinations_never_raise():
    for c1 in (0, 1, 3):
        for c2 in (0, 1, 3):
            for c3 in (0, 1, 3):
                res = ev.play_equation(c1, c2, c3, 30)
                kind, text = ev.verdict_play(res)
                assert kind in ("success", "warning", "info") and text, (c1, c2, c3)


def test_play_equation_text_formats_coefficients():
    assert ev.equation_text(0, 1, 0) == "F = 1 + z·F²" and ev.equation_text(2, 0, 3) == "F = 1 + 2z·F + 3z²·F²" and ev.equation_text(0, 0, 0) == "F = 1"
    assert "1/(1 − z)" in ev.verdict_play(ev.play_equation(1, 0, 0, 50))[1] and "1z" not in ev.verdict_play(ev.play_equation(1, 0, 0, 50))[1]


def test_boltzmann_leaves_nothing_behind_when_size_is_zero():
    """Der leere Baum (Größe 0) ist ein gültiges Objekt: das leere Wort."""
    ctx = S.build_context("Dyck-Wörter (Catalan)", 0)
    assert ctx.total == 1
    obj, tries, steps = S.draw_once(ctx, "Boltzmann mit Größenfenster", __import__("random").Random(1), (0, 0))
    assert obj == "" and tries >= 1 and steps >= 1
