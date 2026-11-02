"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def hand_shift_3():
    """Schichtfolgen n = 3 (keine Früh direkt nach Nacht, höchstens zwei Nächte): 20 Wörter. Fortsetzungszahlen für Länge 0, 1, 2 von den Zuständen 0, 1, 2: (1, 1, 1), (3, 2, 1), (8, 4, 3).
    Mit F < N < S: Plätze 0 bis 7 beginnen mit F, 8 bis 11 mit N (NNS, NSF, NSN, NSS), 12 bis 19 mit S. Wahrscheinlichkeit von NSF beim Sampler: 4/20·3/4·1/3 = 1/20, beim naiven Gang 1/3·1/2·1/3 = 1/18."""
    return {"total": 20, "comp": [(1, 1, 1), (3, 2, 1), (8, 4, 3)], "first": "FFF", "tenth": "NSF", "last": "SSS", "n_words": ["NNS", "NSF", "NSN", "NSS"], "p_sampler": Fraction(1, 20), "p_naive": Fraction(1, 18)}


@pytest.fixture
def hand_dyck_3():
    """Dyck n = 3: Ballot-Zeilen aus Höhe 0 für 0, 2, 4, 6 Schritte: 1, 1, 2, 5; in der Ordnung „(“ < „)“: ((())), (()()), (())(), ()(()), ()()()."""
    return {"ballot": [1, 1, 2, 5], "words": ["((()))", "(()())", "(())()", "()(())", "()()()"]}


@pytest.fixture
def hand_partitions_3():
    """Mengenpartitionen n = 3: Bell 5; Stirling S(3,1) = 1, S(3,2) = 3, S(3,3) = 1; Restricted-Growth-Strings 000, 001, 010, 011, 012."""
    return {"bell": 5, "stirling": [0, 1, 3, 1], "rgs": [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 2)]}


@pytest.fixture
def hand_boltzmann_catalan():
    """Catalan, x = ρ = 1/4: y = 2; Blatt 1/2, Knoten 1/2; P(N = 0) = 1/2, P(N = 1) = 1/8 (ein Knoten, zwei Blätter), P(N = 2) = 2/32 = 1/16."""
    return {"rho": 0.25, "tau": 2.0, "p": [0.5, 0.125, 0.0625]}
