"""Eigenschaftstests (Schicht 2): Aussagen, die für ganze Klassen von Eingaben gelten, nicht nur für Einzelwerte."""

import math
import random
from fractions import Fraction

import pytest

import gvz_algorithm as A
import gvz_constants as C
import gvz_evaluation as ev
import gvz_scenario as S

SETTINGS = ev.Settings


def test_every_available_combination_draws_only_valid_objects():
    for fam in C.FAMILIES:
        for method in C.AVAILABLE[fam]:
            for n in (3, 6, 9):
                a = ev.analyse(SETTINGS(fam, method, n, 2, 0, 300, 7))
                assert a.problems == [] and a.draws_done == 300 and a.method_eff == method, (fam, method, n)


def test_same_seed_same_draws_other_seed_other_draws():
    for fam in C.FAMILIES:
        a = ev.analyse(SETTINGS(fam, "Rekursions-Sampler", 12, 3, 10, 50, 5))
        b = ev.analyse(SETTINGS(fam, "Rekursions-Sampler", 12, 3, 10, 50, 5))
        c = ev.analyse(SETTINGS(fam, "Rekursions-Sampler", 12, 3, 10, 50, 6))
        assert a.shown == b.shown and a.shown != c.shown, fam


def test_recursion_sampler_is_exactly_uniform_for_every_family_and_size():
    for fam in C.FAMILIES:
        for n in range(3, 10):
            a = ev.analyse(SETTINGS(fam, "Rekursions-Sampler", n, 2, 10, 20, 1))
            if a.enumerated:
                assert a.exact_uniform is True and a.problems == [], (fam, n)


def test_naive_walk_is_never_uniform_and_distance_grows_with_n():
    for fam, ns in (("Schichtfolgen", range(3, 11)), ("Dyck-Wörter (Catalan)", range(3, 9)), ("Mengenpartitionen", range(3, 8)), ("Motzkin-Wörter", range(4, 10))):
        tvs = []
        for n in ns:
            a = ev.analyse(SETTINGS(fam, "Naiver Gang", n, 2, 10, 10, 1))
            assert a.tv is not None and a.tv > 0 and a.max_factor > 1, (fam, n)
            tvs.append(a.tv)
        assert all(tvs[i] < tvs[i + 1] for i in range(len(tvs) - 1)), fam


def test_rejection_expected_tries_are_proposals_over_objects_and_grow_with_n():
    for fam in ("Schichtfolgen", "Dyck-Wörter (Catalan)", "Motzkin-Wörter"):
        last = 0
        for n in (5, 10, 20, 40):
            ctx = S.build_context(fam, n)
            e = S.expected_tries(ctx, "Rejection")
            assert e == Fraction(ctx.universe, ctx.total) and e > last, (fam, n)
            last = e
    assert S.expected_tries(S.build_context("Mengenpartitionen", 5), "Rejection") is None


def test_rejection_growth_per_step_tends_to_three_over_the_dominant_eigenvalue():
    comp = A.shift_completions(201)
    growth = Fraction(3 * comp[200][0], comp[201][0])
    assert float(growth) == pytest.approx(3 / 2.546818, rel=1e-5)


def test_drawn_statistic_matches_the_exact_distribution_for_uniform_methods():
    for fam in ("Schichtfolgen", "Dyck-Wörter (Catalan)", "Motzkin-Wörter", "Mengenpartitionen"):
        a = ev.analyse(SETTINGS(fam, "Rekursions-Sampler", 14 if fam != "Mengenpartitionen" else 10, 0, 0, 8000, 3))
        rows = a.extras["stat"]
        assert sum(r["theoretisch"] for r in rows) == pytest.approx(1)
        assert max(abs(r["gezogen"] - r["theoretisch"]) for r in rows) < 0.03, fam
    naive = ev.analyse(SETTINGS("Dyck-Wörter (Catalan)", "Naiver Gang", 14, 0, 0, 8000, 3))
    assert max(abs(r["gezogen"] - r["theoretisch"]) for r in naive.extras["stat"]) > 0.05


def test_conditioned_sampler_only_gives_words_with_exactly_k_nights():
    for n, k in ((6, 0), (6, 3), (10, 7), (30, 12)):
        a = ev.analyse(SETTINGS("Schichtfolgen mit k Nächten", "Rekursions-Sampler", n, k, 0, 200, 4))
        ctx = S.build_context("Schichtfolgen mit k Nächten", n, k)
        assert a.total == ctx.total > 0 and a.problems == []


def test_boltzmann_sizes_lie_in_the_window_and_window_probability_grows_with_x():
    a = ev.analyse(SETTINGS("Dyck-Wörter (Catalan)", "Boltzmann mit Größenfenster", 60, 0, 10, 40, 2))
    assert a.window == (54, 66) and all(54 <= s <= 66 for s in a.sizes) and sum(a.sizes.values()) == a.draws_done
    xs = ev.x_rows()
    ps = [r["P(Fenster)"] for r in xs]
    assert all(ps[i] < ps[i + 1] for i in range(len(ps) - 1)) and xs[-1]["Mittel der Größe"] == math.inf


def test_size_window_integer_arithmetic():
    assert S.size_window(100, 10) == (90, 110) and S.size_window(1000, 10) == (900, 1100) and S.size_window(3, 10) == (2, 4)
    assert S.size_window(50, 0) == (50, 50) and S.size_window(5, 20) == (4, 6)


def test_steps_count_at_least_the_tries():
    for fam in ("Schichtfolgen", "Dyck-Wörter (Catalan)", "Motzkin-Wörter"):
        a = ev.analyse(SETTINGS(fam, "Rejection", 8, 0, 0, 100, 9))
        assert a.steps_mean >= a.tries_mean >= 1


def test_chi_square_only_when_enough_draws_per_object():
    few = ev.analyse(SETTINGS("Schichtfolgen", "Rekursions-Sampler", 10, 0, 0, 2000, 1))
    many = ev.analyse(SETTINGS("Schichtfolgen", "Rekursions-Sampler", 6, 0, 0, 2000, 1))
    assert few.chi is None and few.needed_draws == 5 * 13926 and many.chi is not None and abs(many.z) < 4


def test_random_conditioned_sampler_over_many_seeds_stays_in_the_support():
    tab = A.night_table(12)
    for seed in range(30):
        rng = random.Random(seed)
        k = rng.randrange(0, len(A.night_counts(12)))
        assert A.night_sample(12, k, tab, rng).count("N") == k
