"""Unabhängige Orakel: jede Zahl und jede Wahrscheinlichkeit über einen zweiten Weg, der den Rechenkern nicht benutzt."""

import itertools
import math
import random
from fractions import Fraction

import pytest

import gvz_algorithm as A


class ScriptedRng:
    """Zufallsquelle, die nur `randrange` kennt und die vorgegebene Zahl liefert: damit wird jeder Rang einzeln durchgespielt."""

    def __init__(self, value):
        self.value = value

    def randrange(self, n):
        assert 0 <= self.value < n
        return self.value


def brute_shift_words(n):
    return sorted(w for w in map("".join, itertools.product("FSN", repeat=n)) if "NF" not in w and "NNN" not in w)


def test_shift_counts_and_words_against_brute_force():
    for n in range(0, 9):
        assert sorted(A.shift_words(n)) == brute_shift_words(n)
        assert A.shift_completions(n)[n][0] == len(brute_shift_words(n))


def test_shift_unrank_is_a_bijection_onto_the_valid_words():
    order = str.maketrans("FNS", "ABC")
    for n in range(1, 8):
        comp = A.shift_completions(n)
        words = [A.shift_unrank(n, r, comp) for r in range(comp[n][0])]
        assert sorted(words) == brute_shift_words(n) and words == sorted(words, key=lambda w: w.translate(order))
        assert [A.shift_rank(w, comp) for w in words] == list(range(comp[n][0]))
        # der Sampler mit festem Rang liefert genau das r-te Wort: damit hat jedes Wort genau die Wahrscheinlichkeit 1/Gesamtzahl
        assert [A.shift_sample(n, comp, ScriptedRng(r)) for r in range(comp[n][0])] == words


def naive_walk_probabilities(n):
    """Wahrscheinlichkeiten des naiven Gangs durch Verzweigung des Automaten (eigene Tabelle, nicht die des Kerns)."""
    options = {"s0": [("F", "s0"), ("S", "s0"), ("N", "s1")], "s1": [("S", "s0"), ("N", "s2")], "s2": [("S", "s0")]}
    paths = {("", "s0"): Fraction(1)}
    for _ in range(n):
        nxt = {}
        for (word, state), p in paths.items():
            for letter, to in options[state]:
                nxt[(word + letter, to)] = p / len(options[state])
        paths = nxt
    return {word: p for (word, _), p in paths.items()}


def test_naive_walk_probabilities_against_independent_branching():
    for n in (3, 5, 8):
        ref = naive_walk_probabilities(n)
        assert sum(ref.values()) == 1
        assert all(A.shift_naive_probability(w) == p for w, p in ref.items())
    ref10 = naive_walk_probabilities(10)
    assert float(A.total_variation(list(ref10.values()), 13926)) == pytest.approx(0.3628, abs=5e-5)


def test_night_distribution_and_words_against_brute_force():
    for n in range(1, 9):
        brute = {}
        for w in brute_shift_words(n):
            brute[w.count("N")] = brute.get(w.count("N"), 0) + 1
        assert A.night_counts(n) == [brute.get(k, 0) for k in range(max(brute) + 1)]
        tab = A.night_table(n)
        for k in brute:
            ws = [w for w in brute_shift_words(n) if w.count("N") == k]
            assert sorted(A.night_words(n, k, tab)) == ws
            assert sorted(A.night_sample(n, k, tab, ScriptedRng(r)) for r in range(len(ws))) == ws
            assert all(A.night_recursion_probability(w, tab) == Fraction(1, len(ws)) for w in ws)


def test_dyck_against_brute_force_and_bijection():
    for n in range(1, 8):
        brute = sorted(w for w in map("".join, itertools.product("()", repeat=2 * n)) if A.dyck_valid(w))
        assert len(brute) == math.comb(2 * n, n) // (n + 1) and sorted(A.dyck_words(n)) == brute
        b = A.ballot_table(n)
        assert sorted(A.dyck_sample(n, b, ScriptedRng(r)) for r in range(b[2 * n][0])) == brute
        assert all(A.dyck_recursion_probability(w, b) == Fraction(1, len(brute)) for w in brute)


def test_motzkin_against_brute_force_and_trinomial_sum():
    for n in range(1, 9):
        brute = sorted(w for w in map("".join, itertools.product("UFD", repeat=n)) if A.motzkin_valid(w))
        assert len(brute) == sum(math.comb(n, 2 * k) * (math.comb(2 * k, k) // (k + 1)) for k in range(n // 2 + 1)) == A.motzkin_number(n)
        assert sorted(A.motzkin_words(n)) == brute
        t = A.motzkin_table(n)
        assert sorted(A.motzkin_sample(n, t, ScriptedRng(r)) for r in range(t[n][0])) == brute
        assert all(A.motzkin_recursion_probability(w, t) == Fraction(1, len(brute)) for w in brute)


def brute_set_partitions(n):
    """Alle Mengenpartitionen über beliebige Markierungen, kanonisiert zum Restricted-Growth-String."""
    seen = set()
    for labels in itertools.product(range(n), repeat=n):
        mapping, canon = {}, []
        for v in labels:
            mapping.setdefault(v, len(mapping))
            canon.append(mapping[v])
        seen.add(tuple(canon))
    return sorted(seen)


def test_partitions_against_brute_force_and_stirling_formula():
    for n in range(1, 7):
        brute = brute_set_partitions(n)
        assert sorted(A.partitions_all(n)) == brute and len(brute) == A.bell_number(n)
        s = A.stirling2_table(n)
        for k in range(1, n + 1):
            direct = sum((-1) ** j * math.comb(k, j) * (k - j) ** n for j in range(k + 1)) // math.factorial(k)
            assert s[n][k] == direct == len([p for p in brute if max(p) + 1 == k])
        assert all(A.partition_recursion_probability(p, s) == Fraction(1, len(brute)) for p in brute)
        assert sum(A.partition_naive_probability(p) for p in brute) == 1


def test_partition_sampler_chi_square_band():
    n = 5
    s = A.stirling2_table(n)
    rng = random.Random(11)
    draws = 40_000
    cnt = {}
    for _ in range(draws):
        p = A.partition_sample(n, s, rng)
        cnt[p] = cnt.get(p, 0) + 1
    allp = A.partitions_all(n)
    z = A.z_of_chi(A.chi_square([cnt.get(p, 0) for p in allp], draws / len(allp)), len(allp) - 1)
    assert abs(z) < 4 and set(cnt) == set(allp)


def test_derangements_against_brute_force():
    for n in range(0, 8):
        brute = sum(1 for p in itertools.permutations(range(n)) if all(p[i] != i for i in range(n)))
        assert A.derangements(n) == brute
    assert A.derangement_expected_tries(10) == Fraction(math.factorial(10), 1334961)


def test_grid_semiring_against_enumeration():
    for seed in range(5):
        rng = random.Random(seed)
        right, down = A.grid_costs(5, 5, rng)
        dist, cnt = A.grid_semiring(5, 5, right, down)
        paths = A.grid_all_paths(5, 5)
        costs = [A.grid_path_cost(p, right, down) for p in paths]
        assert len(paths) == math.comb(8, 4) and dist[(0, 0)] == min(costs) and cnt[(0, 0)] == costs.count(min(costs))
        opt = [p for p, c in zip(paths, costs) if c == min(costs)]
        probs = [A.grid_naive_probability(p, 5, 5, right, down, dist) for p in opt]
        assert sum(probs) == 1


def test_boltzmann_size_distribution_against_independent_branching_recursion():
    """P(N = n) aus der Verzweigung selbst (Blatt 1/2, Knoten 1/2 mit zwei Kindern), nicht aus der Catalan-Formel."""
    p = [Fraction(1, 2)]
    for n in range(1, 25):
        p.append(Fraction(1, 2) * sum(p[i] * p[n - 1 - i] for i in range(n)))
    counts = A.spec_coefficients(A.spec_terms(0, 1, 0), 24)
    assert all(float(p[n]) == pytest.approx(counts[n] * 0.25 ** n / 2) for n in range(25))
    # Motzkin: Blatt 1/3, z·F mit 1/3, z²·F² mit 1/3
    q = [Fraction(1, 3)]
    for n in range(1, 25):
        q.append(Fraction(1, 3) * q[n - 1] + (Fraction(1, 3) * sum(q[i] * q[n - 2 - i] for i in range(n - 1)) if n >= 2 else 0))
    mc = A.spec_coefficients(A.spec_terms(1, 0, 1), 24)
    assert all(float(q[n]) == pytest.approx(mc[n] * (1 / 3) ** n / 3, rel=1e-9) for n in range(25))


def test_boltzmann_sampler_chi_square_band_on_fixed_seed():
    terms = A.spec_terms(0, 1, 0)
    rng = random.Random(8)
    draws = 60_000
    cells = [0] * 10
    for _ in range(draws):
        size, _ = A.boltzmann_size(terms, 0.25, 2.0, rng, 3000)
        cells[9 if size is None or size >= 9 else size] += 1
    counts = A.spec_coefficients(terms, 8)
    theo = [counts[i] * 0.25 ** i / 2 for i in range(9)]
    theo.append(1 - sum(theo))
    chi = sum((c - t * draws) ** 2 / (t * draws) for c, t in zip(cells, theo))
    assert abs(A.z_of_chi(chi, 9)) < 4


def test_boltzmann_dyck_trees_of_one_size_are_uniform():
    rng = random.Random(21)
    cnt = {}
    done = 0
    while done < 6000:
        word, _ = A.boltzmann_dyck(rng, 4)
        if word is not None and len(word) == 8:
            cnt[word] = cnt.get(word, 0) + 1
            done += 1
    words = A.dyck_words(4)
    assert set(cnt) == set(words)
    assert abs(A.z_of_chi(A.chi_square([cnt[w] for w in words], done / len(words)), len(words) - 1)) < 4
