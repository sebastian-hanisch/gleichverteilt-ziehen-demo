"""Einheiten des Rechenkerns, jede an einer von Hand gerechneten Mini-Instanz."""

import math
import random
from fractions import Fraction

import pytest

import gvz_algorithm as A


def test_digit_count_and_ln():
    assert [A.digit_count(x) for x in (0, 1, 9, 10, 99, 100, 10 ** 50 - 1, 10 ** 50)] == [1, 1, 1, 2, 2, 3, 50, 51]
    with pytest.raises(ValueError):
        A.digit_count(-1)
    assert A.ln(10 ** 5000) == pytest.approx(5000 * math.log(10), rel=1e-12)
    assert A.ln(Fraction(1, 2)) == pytest.approx(-math.log(2))
    with pytest.raises(ValueError):
        A.ln(0)


def test_chi_square_and_z_hand():
    # Zellen 8, 12 bei Erwartung 10: (4 + 4)/10 = 0,8; z = (0,8 − 1)/√2
    assert A.chi_square([8, 12], 10) == pytest.approx(0.8)
    assert A.z_of_chi(0.8, 1) == pytest.approx(-0.2 / math.sqrt(2))
    with pytest.raises(ValueError):
        A.chi_square([1], 0)
    with pytest.raises(ValueError):
        A.z_of_chi(1, 0)


def test_total_variation_hand():
    # Wahrscheinlichkeiten 1/2, 1/4, 1/4 gegen 1/3: ½·(1/6 + 1/12 + 1/12) = 1/6
    assert A.total_variation([Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)], 3) == Fraction(1, 6)
    assert A.total_variation([Fraction(1, 4)] * 4, 4) == 0


def test_shift_hand(hand_shift_3):
    comp = A.shift_completions(3)
    assert [tuple(comp[i][s] for s in (0, 1, 2)) for i in range(3)] == hand_shift_3["comp"]
    assert comp[3][0] == hand_shift_3["total"]
    words = [A.shift_unrank(3, r, comp) for r in range(20)]
    assert words[0] == hand_shift_3["first"] and words[9] == hand_shift_3["tenth"] and words[19] == hand_shift_3["last"]
    assert words[8:12] == hand_shift_3["n_words"]
    assert A.shift_rank("NSF", comp) == 9
    assert A.shift_recursion_probability("NSF", comp) == hand_shift_3["p_sampler"]
    assert A.shift_naive_probability("NSF") == hand_shift_3["p_naive"]


def test_shift_validity_rules():
    assert A.shift_valid("FSNNS") and not A.shift_valid("NF") and not A.shift_valid("SNNNS") and not A.shift_valid("FXS")
    assert A.shift_words(3) == sorted(A.shift_words(3)) and len(A.shift_words(3)) == 20
    with pytest.raises(ValueError):
        A.shift_unrank(3, 20, A.shift_completions(3))
    with pytest.raises(ValueError):
        A.shift_completions(-1)


def test_night_tables_hand():
    # n = 3: ohne Nacht 8 (F, S frei), eine Nacht 8, zwei Nächte 4 (Stück 8)
    assert A.night_counts(3) == [8, 8, 4]
    assert A.night_counts(10) == [1024, 2816, 4096, 3472, 1852, 571, 91, 4]
    tab = A.night_table(3)
    assert A.night_words(3, 2, tab) == ["FNN", "NNS", "NSN", "SNN"]
    with pytest.raises(ValueError):
        A.night_sample(3, 3, tab, random.Random(1))


def test_dyck_hand(hand_dyck_3):
    b = A.ballot_table(3)
    assert [b[i][0] for i in (0, 2, 4, 6)] == hand_dyck_3["ballot"]
    assert A.dyck_words(3) == hand_dyck_3["words"]
    assert A.catalan(3) == 5 and A.dyck_valid("(()())") and not A.dyck_valid("())(") and not A.dyck_valid("(()")
    assert A.dyck_recursion_probability("(()())", b) == Fraction(1, 5)
    # naiver Gang für ((())): immer genau eine Möglichkeit bei Höhe 0, dann (, (, ), ), ) mit je 1/2 bis die Öffnungen verbraucht sind
    assert A.dyck_naive_probability("()()()") == Fraction(1, 2) * Fraction(1, 2)


def test_motzkin_hand():
    assert [A.motzkin_number(n) for n in range(8)] == [1, 1, 2, 4, 9, 21, 51, 127]
    assert A.motzkin_words(3) == ["UFD", "UDF", "FUD", "FFF"]
    assert A.motzkin_valid("UFD") and not A.motzkin_valid("DU") and not A.motzkin_valid("U")
    t = A.motzkin_table(3)
    assert t[3][0] == 4 and A.motzkin_recursion_probability("UFD", t) == Fraction(1, 4)


def test_partitions_hand(hand_partitions_3):
    s = A.stirling2_table(3)
    assert s[3] == hand_partitions_3["stirling"] and A.bell_number(3) == hand_partitions_3["bell"]
    assert A.partitions_all(3) == hand_partitions_3["rgs"]
    for rgs in hand_partitions_3["rgs"]:
        assert A.partition_recursion_probability(rgs, s) == Fraction(1, 5)
    assert A.partition_naive_probability((0, 1, 0)) == Fraction(1, 6)       # 1 · 1/2 · 1/3
    assert A.partition_text((0, 1, 0)) == "{1,3} {2}"
    with pytest.raises(ValueError):
        A.partition_sample_fixed(3, 4, s, random.Random(1))


def test_derangements_hand():
    assert [A.derangements(n) for n in range(7)] == [1, 0, 1, 2, 9, 44, 265]
    assert A.derangement_expected_tries(3) == 3
    assert A.derangement_valid([1, 2, 0]) and not A.derangement_valid([0, 2, 1])


def test_spec_hand_and_boltzmann_probabilities(hand_boltzmann_catalan):
    terms = A.spec_terms(0, 1, 0)
    rho, tau = A.solve_system(terms)
    assert (rho, tau) == pytest.approx((0.25, 2.0), abs=1e-9)
    assert A.spec_value(terms, rho, tau) == pytest.approx(2.0, abs=1e-6)
    counts = A.spec_coefficients(terms, 2)
    assert [counts[n] * rho ** n / tau for n in range(3)] == pytest.approx(hand_boltzmann_catalan["p"])
    assert A.tree_count_terms(A.spec_coefficients(terms, 2), 0.25, 2.0, 0, 2) == pytest.approx(0.6875)


def test_spec_validation_and_degenerate_systems():
    with pytest.raises(ValueError):
        A.spec_coefficients([(1, 0, 2)], 5)
    with pytest.raises(ValueError):
        A.solve_system(A.spec_terms(1, 0, 0))
    with pytest.raises(ValueError):
        A.solve_system(A.spec_terms(0, 0, 1))
    assert A.spec_terms(0, 0, 0) == [] and A.is_periodic(A.spec_terms(0, 0, 1)) and not A.is_periodic([])


def test_boltzmann_dyck_word_is_valid_and_aborts():
    rng = random.Random(3)
    for _ in range(200):
        word, steps = A.boltzmann_dyck(rng, 50)
        assert steps >= 1
        if word is not None:
            assert A.dyck_valid(word) and len(word) // 2 <= 50
    aborted = [A.boltzmann_dyck(random.Random(i), 0)[0] for i in range(20)]
    assert all(w is None or w == "" for w in aborted)


def test_grid_hand():
    right = {(0, 0): 1, (1, 0): 1}
    down = {(0, 0): 1, (0, 1): 1}
    dist, cnt = A.grid_semiring(2, 2, right, down)
    # 2×2: zwei Wege der Kosten 2 (rechts-runter, runter-rechts)
    assert dist[(0, 0)] == 2 and cnt[(0, 0)] == 2
    assert A.grid_all_paths(2, 2) == [((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (1, 1))]
    assert A.grid_path_cost(((0, 0), (0, 1), (1, 1)), right, down) == 2
    assert A.grid_naive_probability(((0, 0), (0, 1), (1, 1)), 2, 2, right, down, dist) == Fraction(1, 2)
