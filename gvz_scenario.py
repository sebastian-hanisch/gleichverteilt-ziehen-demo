"""Szenario: aus der gewählten Familie die Tabellen bauen, Objekte aufzählen und je Verfahren ziehen (mit Versuchen und Rechenschritten)."""

from dataclasses import dataclass
from fractions import Fraction

import gvz_algorithm as A
import gvz_constants as C


def effective_n(family: str, n: int) -> int:
    if family not in C.FAMILIES:
        raise ValueError(f"unbekannte Familie {family!r}")
    return max(C.N_MIN, min(n, C.N_CAP[family], C.N_MAX))


def effective_k(family: str, n: int, k: int) -> int:
    """Zahl der Nächte begrenzt auf 0 bis zum Größten, das es bei dieser Länge gibt (nur die Familie mit Bedingung)."""
    if family != "Schichtfolgen mit k Nächten":
        return k
    return max(0, min(k, len(A.night_counts(n)) - 1))


def effective_method(family: str, method: str) -> str:
    if family not in C.FAMILIES or method not in C.METHODS:
        raise ValueError("unbekannte Familie oder unbekanntes Verfahren")
    return method if method in C.AVAILABLE[family] else C.DEFAULT_METHOD


@dataclass
class Context:
    """Tabellen und Zählungen einer Familie bei fester Größe (einmal je Auswertung gebaut)."""
    family: str
    n: int
    k: int
    total: int                 # Zahl der Objekte
    universe: int | None       # Zahl der Vorschläge der Rejection (None: kein Rejection-Verfahren)
    table: object = None
    comp: object = None


def build_context(family: str, n: int, k: int = 0) -> Context:
    if family not in C.FAMILIES:
        raise ValueError(f"unbekannte Familie {family!r}")
    if family == "Schichtfolgen":
        comp = A.shift_completions(n)
        return Context(family, n, k, comp[n][0], 3 ** n, comp=comp)
    if family == "Schichtfolgen mit k Nächten":
        tab = A.night_table(n)
        comp = A.shift_completions(n)
        total = tab[n][0].get(k, 0)
        return Context(family, n, k, total, comp[n][0], table=tab, comp=comp)
    if family == "Dyck-Wörter (Catalan)":
        table = A.ballot_table(n)
        return Context(family, n, k, table[2 * n][0], 4 ** n, table=table)
    if family == "Motzkin-Wörter":
        table = A.motzkin_table(n)
        return Context(family, n, k, table[n][0], 3 ** n, table=table)
    table = A.stirling2_table(n)
    return Context(family, n, k, sum(table[n]), None, table=table)


def objects(ctx: Context) -> list | None:
    """Alle Objekte, wenn es höchstens ENUM_MAX sind, sonst None."""
    if ctx.total > C.ENUM_MAX:
        return None
    if ctx.family == "Schichtfolgen":
        return A.shift_words(ctx.n)
    if ctx.family == "Schichtfolgen mit k Nächten":
        return A.night_words(ctx.n, ctx.k, ctx.table)
    if ctx.family == "Dyck-Wörter (Catalan)":
        return A.dyck_words(ctx.n)
    if ctx.family == "Motzkin-Wörter":
        return A.motzkin_words(ctx.n)
    return A.partitions_all(ctx.n)


def object_text(family: str, obj) -> str:
    return A.partition_text(obj) if family == "Mengenpartitionen" else str(obj)


def recursion_probability(ctx: Context, obj) -> Fraction:
    """Wahrscheinlichkeit des Objekts beim Rekursions-Sampler (Produkt der Verhältnisse)."""
    if ctx.family == "Schichtfolgen":
        return A.shift_recursion_probability(obj, ctx.comp)
    if ctx.family == "Schichtfolgen mit k Nächten":
        return A.night_recursion_probability(obj, ctx.table)
    if ctx.family == "Dyck-Wörter (Catalan)":
        return A.dyck_recursion_probability(obj, ctx.table)
    if ctx.family == "Motzkin-Wörter":
        return A.motzkin_recursion_probability(obj, ctx.table)
    return A.partition_recursion_probability(obj, ctx.table)


def naive_probability(ctx: Context, obj) -> Fraction | None:
    if ctx.family == "Schichtfolgen":
        return A.shift_naive_probability(obj)
    if ctx.family == "Dyck-Wörter (Catalan)":
        return A.dyck_naive_probability(obj)
    if ctx.family == "Motzkin-Wörter":
        return A.motzkin_naive_probability(obj)
    if ctx.family == "Mengenpartitionen":
        return A.partition_naive_probability(obj)
    return None


def expected_tries(ctx: Context, method: str, window: tuple | None = None):
    """Erwartete Versuche je Objekt: Rejection = Vorschläge durch Zahl der Objekte; Boltzmann = 1/P(Fenster); sonst 1."""
    if method == "Rejection":
        if ctx.universe is None or ctx.total == 0:
            return None
        return Fraction(ctx.universe, ctx.total)
    if method == "Boltzmann mit Größenfenster":
        lo, hi = window
        counts = [A.catalan(i) for i in range(hi + 1)]
        p = A.tree_count_terms(counts, 0.25, 2.0, lo, hi)
        return 1 / p if p > 0 else None
    return Fraction(1)


def size_window(n: int, percent: int) -> tuple:
    """Fenster der Größe (Zahl der Knoten) für den Boltzmann-Sampler: genau n bei 0 Prozent, sonst ±Prozent."""
    if percent <= 0:
        return n, n
    delta = -(-n * percent // 100)       # aufgerundet, ganzzahlig (ohne Gleitkomma-Rundung)
    return max(0, n - delta), n + delta


def draw_once(ctx: Context, method: str, rng, window: tuple | None = None, step_limit: int | None = None) -> tuple:
    """Eine Ziehung: (Objekt oder None, Versuche, Schritte). None, wenn die Versuchsgrenze oder (bei gesetztem `step_limit`) die Schrittgrenze erreicht wurde."""
    family, n = ctx.family, ctx.n
    if method == "Rekursions-Sampler":
        if family == "Schichtfolgen":
            return A.shift_sample(n, ctx.comp, rng), 1, n
        if family == "Schichtfolgen mit k Nächten":
            return A.night_sample(n, ctx.k, ctx.table, rng), 1, n
        if family == "Dyck-Wörter (Catalan)":
            return A.dyck_sample(n, ctx.table, rng), 1, 2 * n
        if family == "Motzkin-Wörter":
            return A.motzkin_sample(n, ctx.table, rng), 1, n
        return A.partition_sample(n, ctx.table, rng), 1, n
    if method == "Naiver Gang":
        if family == "Schichtfolgen":
            return A.shift_naive_sample(n, rng), 1, n
        if family == "Dyck-Wörter (Catalan)":
            return A.dyck_naive_sample(n, rng), 1, 2 * n
        if family == "Motzkin-Wörter":
            return A.motzkin_naive_sample(n, rng), 1, n
        return A.partition_naive_sample(n, rng), 1, n
    if method == "Rejection":
        steps = 0
        for tries in range(1, C.MAX_TRIES_PER_OBJECT + 1):
            if family == "Schichtfolgen":
                obj = A.shift_propose(n, rng)
                steps += n
                ok = A.shift_valid(obj)
            elif family == "Schichtfolgen mit k Nächten":
                obj = A.shift_sample(n, ctx.comp, rng)
                steps += n
                ok = obj.count("N") == ctx.k
            elif family == "Dyck-Wörter (Catalan)":
                obj = A.dyck_propose(n, rng)
                steps += 2 * n
                ok = A.dyck_valid(obj)
            else:
                obj = A.motzkin_propose(n, rng)
                steps += n
                ok = A.motzkin_valid(obj)
            if ok:
                return obj, tries, steps
            if step_limit is not None and steps >= step_limit:
                return None, tries, steps
        return None, C.MAX_TRIES_PER_OBJECT, steps
    # Boltzmann (nur Catalan): Bäume ziehen, bis die Größe im Fenster liegt
    lo, hi = window
    steps = 0
    for tries in range(1, C.MAX_TRIES_PER_OBJECT + 1):
        word, s = A.boltzmann_dyck(rng, hi)
        steps += s
        if word is not None and lo <= len(word) // 2 <= hi:
            return word, tries, steps
        if step_limit is not None and steps >= step_limit:
            return None, tries, steps
    return None, C.MAX_TRIES_PER_OBJECT, steps
