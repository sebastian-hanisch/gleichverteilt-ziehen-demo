"""Auswertung: die eingestellte Ziehung, fünf Experimente, die Spielwiese und die Urteilstexte. Alle Zufallszahlen aus festen Seeds."""

import functools
import math
import random
from dataclasses import dataclass, field
from fractions import Fraction

import gvz_algorithm as A
import gvz_constants as C
from gvz_scenario import (
    Context,
    build_context,
    draw_once,
    effective_k,
    effective_method,
    effective_n,
    expected_tries,
    naive_probability,
    object_text,
    objects,
    recursion_probability,
    size_window,
)

_SUPER = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


@dataclass(frozen=True)
class Settings:
    family: str
    method: str
    n: int
    k: int
    window: int
    draws: int
    seed: int


@dataclass
class Analysis:
    settings: Settings
    n_eff: int
    k_eff: int
    method_eff: str
    total: int
    digits: int
    window: tuple | None
    draws_wanted: int
    draws_done: int
    stopped: str                   # "" | "Versuchsgrenze" | "Schrittgrenze"
    shown: list
    tries_mean: float | None
    tries_expected: float | None
    steps_mean: float | None
    enumerated: bool
    exact_uniform: bool | None     # Rekursions-Sampler: jedes Objekt exakt 1/Gesamtzahl
    tv: float | None               # Abstand zur Gleichverteilung des naiven Gangs (exakt gerechnet)
    max_factor: float | None       # wahrscheinlichstes Objekt so oft wie gerecht
    chi: float | None
    df: int | None
    z: float | None
    coverage: float | None
    needed_draws: int | None
    sizes: dict
    problems: list
    notes: list
    extras: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- Formatierung

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def big_text(x: int) -> str:
    """Ganze Zahl lesbar: bis 12 Stellen mit Tausenderpunkt, darüber Mantisse mal Zehnerpotenz mit Stellenzahl (ohne Stringumwandlung der ganzen Zahl)."""
    if x < 10 ** 12:
        return f"{x:,}".replace(",", ".")
    d = A.digit_count(x)
    s = str(x // 10 ** (d - 3))
    return f"{s[0]},{s[1:3]}·10{str(d - 1).translate(_SUPER)} ({d} Stellen)"


def sci_text(x: float, digits: int = 2) -> str:
    """Gleitkommazahl als Mantisse mal Zehnerpotenz oder ohne Potenz, wenn sie klein genug ist."""
    if x == 0:
        return "0"
    if 0.01 <= abs(x) < 10000:
        return de(x, digits)
    mant, exp = f"{x:.{digits - 1}e}".split("e")
    return f"{mant.replace('.', ',').replace('-', '−')}·10{str(int(exp)).translate(_SUPER)}"


def count_text(x: float) -> str:
    """Zahl der Versuche: ab 1000 mit Tausenderpunkt, bei großen Werten als Zehnerpotenz."""
    if x < 100000 and abs(x - round(x)) < 1e-9:
        return f"{round(x):,}".replace(",", ".")
    if x < 10:
        return de(x, 2)
    if x < 100000:
        return f"{x:,.0f}".replace(",", ".")
    return sci_text(x, 3)


def percent(x: float, digits: int = 3) -> str:
    return de(100 * x, digits) + " %"


# ----------------------------------------------------------------------------- Gültigkeit

def is_valid(ctx: Context, obj) -> bool:
    if ctx.family == "Schichtfolgen":
        return len(obj) == ctx.n and A.shift_valid(obj)
    if ctx.family == "Schichtfolgen mit k Nächten":
        return len(obj) == ctx.n and A.shift_valid(obj) and obj.count("N") == ctx.k
    if ctx.family == "Dyck-Wörter (Catalan)":
        return A.dyck_valid(obj)
    if ctx.family == "Motzkin-Wörter":
        return len(obj) == ctx.n and A.motzkin_valid(obj)
    first_seen = -1
    for v in obj:
        if v > first_seen + 1 or v < 0:
            return False
        first_seen = max(first_seen, v)
    return len(obj) == ctx.n


# ----------------------------------------------------------------------------- die eingestellte Ziehung

def analyse(s: Settings, max_steps: int = C.MAX_STEPS) -> Analysis:
    n = effective_n(s.family, s.n)
    k = effective_k(s.family, n, s.k)
    method = effective_method(s.family, s.method)
    notes, problems = [], []
    if n != s.n:
        notes.append(f"Für diese Familie rechnet die App höchstens bis n = {C.N_CAP[s.family]} und mindestens ab n = {C.N_MIN}: gerechnet wird mit n = {n}.")
    if k != s.k and s.family == "Schichtfolgen mit k Nächten":
        notes.append(f"Bei n = {n} gibt es höchstens {k} Nächte in einer gültigen Schichtfolge: gerechnet wird mit k = {k}.")
    if method != s.method:
        notes.append(f"Das Verfahren „{s.method}“ gibt es für diese Familie nicht: gezogen wird mit dem {method}.")
    ctx = build_context(s.family, n, k)
    if ctx.total <= 0:
        problems.append("Es gibt kein Objekt mit diesen Angaben")
    window = size_window(n, s.window) if method == "Boltzmann mit Größenfenster" else None
    draws_wanted = max(C.DRAWS_MIN, min(s.draws, C.DRAWS_MAX))
    rng = random.Random(s.seed)
    counts, sizes, shown = {}, {}, []
    done = tries_sum = steps_sum = 0
    stopped = ""
    failed = None
    for _ in range(draws_wanted if ctx.total > 0 else 0):
        obj, tries, steps = draw_once(ctx, method, rng, window, step_limit=max(1, max_steps - steps_sum))
        if obj is None:
            stopped = "Versuchsgrenze" if tries >= C.MAX_TRIES_PER_OBJECT else "Schrittgrenze"
            steps_sum += steps
            failed = (tries, steps)
            break
        done += 1
        tries_sum += tries
        steps_sum += steps
        counts[obj] = counts.get(obj, 0) + 1
        if len(shown) < C.SHOW_OBJECTS:
            shown.append(obj)
        if window is not None:
            size = len(obj) // 2
            sizes[size] = sizes.get(size, 0) + 1
        if steps_sum > max_steps and done < draws_wanted:
            stopped = "Schrittgrenze"
            break
    for obj in counts:
        if not is_valid(ctx, obj):
            problems.append(f"Ungültiges Objekt gezogen: {object_text(s.family, obj)}")
            break
    exp = expected_tries(ctx, method, window) if ctx.total > 0 else None
    tries_expected = None if exp is None else float(exp)
    all_objs = objects(ctx) if ctx.total > 0 and (window is None or window[0] == window[1]) else None
    exact_uniform = tv = max_factor = chi = z = coverage = needed = None
    df = None
    if all_objs is not None and ctx.total > 0:
        if len(all_objs) != ctx.total:
            problems.append("Aufzählen und Zählen stimmen nicht überein")
        obj_set = set(all_objs)
        if any(o not in obj_set for o in counts):
            problems.append("Ein gezogenes Objekt fehlt in der Aufzählung")
        if method == "Rekursions-Sampler":
            probs = [recursion_probability(ctx, o) for o in all_objs]
            exact_uniform = all(p == Fraction(1, ctx.total) for p in probs) and sum(probs) == 1
            if not exact_uniform:
                problems.append("Die Wahrscheinlichkeiten des Rekursions-Samplers sind nicht gleich")
        if method == "Naiver Gang":
            probs = [naive_probability(ctx, o) for o in all_objs]
            if sum(probs) != 1:
                problems.append("Die Wahrscheinlichkeiten des naiven Gangs summieren sich nicht zu 1")
            tv = float(A.total_variation(probs, ctx.total))
            max_factor = float(max(probs) * ctx.total)
        coverage = len(counts) / ctx.total if ctx.total else None
        needed = C.MIN_EXPECTED * ctx.total
        if ctx.total > 1 and done > 0 and done / ctx.total >= C.MIN_EXPECTED:
            chi = A.chi_square([counts.get(o, 0) for o in all_objs], done / ctx.total)
            df = ctx.total - 1
            z = A.z_of_chi(chi, df)
    extras = {"failed": failed}
    if all_objs is not None and 0 < ctx.total <= 3000:
        extras["counts"] = [counts.get(o, 0) for o in all_objs]
    if (window is None or window[0] == window[1]) and counts and ctx.total > 0:
        extras["stat"] = statistic_rows(ctx, counts)
    return Analysis(s, n, k, method, ctx.total, A.digit_count(ctx.total) if ctx.total > 0 else 0, window, draws_wanted, done, stopped, shown,
                    tries_sum / done if done else None, tries_expected, steps_sum / done if done else None, all_objs is not None, exact_uniform, tv, max_factor, chi, df, z, coverage,
                    needed, sizes, problems, notes, extras)


def statistic_name(family: str) -> str | None:
    return {"Schichtfolgen": "Zahl der Nachtschichten", "Dyck-Wörter (Catalan)": "Zahl der Gipfel „()“", "Motzkin-Wörter": "Zahl der flachen Schritte",
            "Mengenpartitionen": "Zahl der Blöcke"}.get(family)


def statistic_value(family: str, obj) -> int:
    if family == "Schichtfolgen":
        return obj.count("N")
    if family == "Dyck-Wörter (Catalan)":
        return obj.count("()")
    if family == "Motzkin-Wörter":
        return obj.count("F")
    return max(obj) + 1


def statistic_theory(ctx: Context) -> dict:
    """Exakter Anteil je Wert der Kenngröße (aus den gezählten Verteilungen: Stück 8, Narayana, Trinomial, Stirling)."""
    n, total = ctx.n, ctx.total
    if ctx.family == "Schichtfolgen":
        return {k: Fraction(c, total) for k, c in enumerate(A.night_counts(n))}
    if ctx.family == "Dyck-Wörter (Catalan)":
        return {k: Fraction(math.comb(n, k) * math.comb(n, k - 1), n * total) for k in range(1, n + 1)}
    if ctx.family == "Motzkin-Wörter":
        return {j: Fraction(math.comb(n, j) * A.catalan((n - j) // 2), total) for j in range(0, n + 1) if (n - j) % 2 == 0}
    return {k: Fraction(ctx.table[n][k], total) for k in range(1, n + 1)}


def statistic_rows(ctx: Context, counts: dict) -> list[dict] | None:
    """Anteil der Ziehungen je Wert der Kenngröße neben dem exakten Anteil; für die Familie mit Bedingung entfällt sie."""
    if statistic_name(ctx.family) is None:
        return None
    theory = statistic_theory(ctx)
    done = sum(counts.values())
    got = {}
    for obj, c in counts.items():
        v = statistic_value(ctx.family, obj)
        got[v] = got.get(v, 0) + c
    return [{"Wert": v, "gezogen": got.get(v, 0) / done, "theoretisch": float(theory[v])} for v in sorted(theory)]


def answer_rows(a: Analysis) -> list[dict]:
    """Tabelle der Prüfungen: Frage, Ergebnis, Bewertung."""
    rows = [{"Frage": "Zahl der Objekte", "Ergebnis": big_text(a.total), "Prüfung": "gezählt (Tabelle)"}]
    if a.exact_uniform is not None:
        rows.append({"Frage": "Wahrscheinlichkeit je Objekt", "Ergebnis": f"1/{big_text(a.total)}" if a.exact_uniform else "ungleich", "Prüfung": f"für alle {big_text(a.total)} Objekte als Bruch nachgerechnet" if a.exact_uniform else "weicht ab"})
    if a.tv is not None:
        rows.append({"Frage": "Abstand zur Gleichverteilung (Totalvariation)", "Ergebnis": de(a.tv, 4), "Prüfung": f"wahrscheinlichstes Objekt {de(a.max_factor, 2)}-mal so oft wie gerecht"})
    if a.chi is not None:
        rows.append({"Frage": "Chi-Quadrat der Ziehungen", "Ergebnis": f"{de(a.chi, 1)} bei {a.df} Freiheitsgraden", "Prüfung": f"z = {de(a.z, 2)} (gleichverteilt: etwa zwischen −3 und 3)"})
    elif a.enumerated and a.needed_draws is not None and a.draws_done:
        rows.append({"Frage": "Chi-Quadrat der Ziehungen", "Ergebnis": "–", "Prüfung": f"zu wenige Ziehungen: nötig sind mindestens {big_text(a.needed_draws)}"})
    if a.coverage is not None:
        rows.append({"Frage": "Anteil der Objekte, die gezogen wurden", "Ergebnis": percent(a.coverage, 2), "Prüfung": f"{a.draws_done} Ziehungen"})
    if a.tries_mean is not None:
        rows.append({"Frage": "Versuche je Objekt", "Ergebnis": count_text(a.tries_mean), "Prüfung": "" if a.tries_expected is None else f"erwartet {count_text(a.tries_expected)}"})
    if a.steps_mean is not None:
        rows.append({"Frage": "Rechenschritte je Objekt", "Ergebnis": count_text(a.steps_mean), "Prüfung": ""})
    return rows


def verdict_answers(a: Analysis):
    if a.problems:
        return "error", "Die Rechenwege widersprechen sich: " + "; ".join(a.problems)
    s = a.settings
    method, fam = a.method_eff, s.family
    if a.draws_done == 0:
        tries, steps = a.extras["failed"] if a.extras.get("failed") else (0, 0)
        return "warning", (f"{method}: nach {count_text(tries)} Versuchen und {count_text(steps)} Rechenschritten kein Objekt gezogen ({a.stopped}). Erwartet sind {count_text(a.tries_expected) if a.tries_expected else '?'} Versuche je Objekt; "
                           f"bei {fam}, n = {a.n_eff} lohnt sich dieses Verfahren nicht.")
    cut = ""
    if a.stopped:
        cut = f" (nach {a.draws_done} von {a.draws_wanted} Ziehungen abgebrochen: {a.stopped}; Obergrenze {count_text(C.MAX_STEPS)} Rechenschritte)"
    total = big_text(a.total)
    zt = "" if a.z is None else f" Chi-Quadrat {de(a.chi, 1)} bei {a.df} Freiheitsgraden (z = {de(a.z, 2)})."
    if method == "Rekursions-Sampler":
        head = f"Rekursions-Sampler, {fam}, n = {a.n_eff}: {total} Objekte, jedes mit der Wahrscheinlichkeit 1/{total}"
        head += f" (für alle {total} Objekte als Bruch nachgerechnet)." if a.exact_uniform else " (Gesamtzahl zu groß zum Aufzählen; die Wahrscheinlichkeit folgt aus dem Produkt der Verhältnisse)."
        text = head + f" {a.draws_done} Ziehungen{cut}, {count_text(a.steps_mean)} Schritte je Objekt." + zt
        return ("warning" if a.z is not None and abs(a.z) > 4 else "success"), text
    if method == "Rejection":
        base = f"Rejection, {fam}, n = {a.n_eff}: im Mittel {count_text(a.tries_mean)} Versuche je Objekt, erwartet {count_text(a.tries_expected)}; {count_text(a.steps_mean)} Rechenschritte je Objekt."
        return ("warning" if a.z is not None and abs(a.z) > 4 else "success"), base + f" {a.draws_done} Ziehungen{cut}." + zt + " Gleichverteilt, weil jedes gültige Objekt gleich oft vorgeschlagen wird."
    if method == "Boltzmann mit Größenfenster":
        lo, hi = a.window
        win = f"genau n = {a.n_eff}" if lo == hi else f"Größe {lo} bis {hi}"
        return "success", (f"Boltzmann-Sampler, Catalan-Bäume, {win}: im Mittel {count_text(a.tries_mean)} Bäume je Treffer, erwartet {count_text(a.tries_expected)}; {count_text(a.steps_mean)} Rechenschritte je Treffer "
                           f"gegen {2 * a.n_eff} beim Rekursions-Sampler. {a.draws_done} Ziehungen{cut}." + zt)
    text = f"Naiver Gang, {fam}, n = {a.n_eff}: nicht gleichverteilt."
    if a.tv is not None:
        text += f" Abstand zur Gleichverteilung {de(a.tv, 3)}, das wahrscheinlichste Objekt kommt {de(a.max_factor, 1)}-mal so oft vor wie bei Gleichverteilung."
    else:
        text += " Bei dieser Größe ist die Menge zu groß, um den Abstand auszurechnen."
    return "warning", text + zt + f" {a.draws_done} Ziehungen{cut}."


# Die Experimente sind deterministisch (feste Seeds) und werden je Prozess einmal gerechnet; die Rückgaben dürfen nicht verändert werden.

# ----------------------------------------------------------------------------- Experiment 1: dieselbe Aufgabe auf allen Wegen

@functools.cache
def uniformity_rows() -> list[dict]:
    rows = []
    cases = (("Schichtfolgen", C.EXP_SHIFT_N, ("Rekursions-Sampler", "Rejection", "Naiver Gang"), C.EXP_DRAWS),
             ("Dyck-Wörter (Catalan)", C.EXP_DYCK_N, ("Rekursions-Sampler", "Rejection", "Boltzmann mit Größenfenster", "Naiver Gang"), C.EXP_DRAWS),
             ("Motzkin-Wörter", 6, ("Rekursions-Sampler", "Rejection", "Naiver Gang"), C.EXP_DRAWS),
             ("Mengenpartitionen", 5, ("Rekursions-Sampler", "Naiver Gang"), C.EXP_DRAWS))
    for fam, n, methods, draws in cases:
        for method in methods:
            d = 4000 if method.startswith("Boltzmann") else draws
            a = analyse(Settings(fam, method, n, 0, 0, d, C.EXP_SEED), max_steps=8_000_000)
            rows.append({"Familie": fam, "n": n, "Verfahren": method, "Objekte": a.total, "Ziehungen": a.draws_done, "z": a.z, "TV": a.tv, "exakt": a.exact_uniform,
                         "Versuche": a.tries_mean, "Schritte": a.steps_mean, "Anteil gezogen": a.coverage})
    return rows


def verdict_uniformity(rows: list[dict]):
    exact = [r for r in rows if r["Verfahren"] != "Naiver Gang"]
    naive = [r for r in rows if r["Verfahren"] == "Naiver Gang"]
    ok = all(r["z"] is not None and abs(r["z"]) <= 4 for r in exact)
    zs = [r["z"] for r in exact]
    text = (f"{len(exact)} Kombinationen aus Familie und exaktem Verfahren ohne Verzerrung: z-Werte zwischen {de(min(zs), 2)} und {de(max(zs), 2)} (gleichverteilt: etwa −3 bis 3); "
            f"der naive Gang liegt bei z = " + ", ".join(de(r["z"], 0) for r in naive) + f" und im Abstand {de(min(r['TV'] for r in naive), 2)} bis {de(max(r['TV'] for r in naive), 2)} zur Gleichverteilung.")
    return ("success" if ok else "warning"), text


# ----------------------------------------------------------------------------- Experiment 2: der naive Gang ist verzerrt

@functools.cache
def naive_rows() -> list[dict]:
    rows = []
    for n in C.EXP_NAIVE_NS:
        words = A.shift_words(n)
        probs = [_float_naive_shift(w) for w in words]
        rows.append(_naive_row("Schichtfolgen", n, probs))
    for n in C.EXP_NAIVE_DYCK_NS:
        probs = [float(A.dyck_naive_probability(w)) for w in A.dyck_words(n)]
        rows.append(_naive_row("Dyck-Wörter (Catalan)", n, probs))
    for n in C.EXP_NAIVE_PART_NS:
        probs = [float(A.partition_naive_probability(p)) for p in A.partitions_all(n)]
        rows.append(_naive_row("Mengenpartitionen", n, probs))
    return rows


def _float_naive_shift(word: str) -> float:
    s, p = 0, 1.0
    for letter in word:
        options = A.TRANS[s]
        p /= len(options)
        s = dict(options)[letter]
    return p


def _naive_row(fam: str, n: int, probs: list) -> dict:
    t = len(probs)
    tv = sum(abs(p - 1 / t) for p in probs) / 2
    return {"Familie": fam, "n": n, "Objekte": t, "TV": tv, "häufigstes Objekt (mal gerecht)": max(probs) * t, "größte gegen kleinste": max(probs) / min(probs), "Summe": sum(probs)}


def verdict_naive(rows: list[dict]):
    shifts = [r for r in rows if r["Familie"] == "Schichtfolgen"]
    grows = all(shifts[i]["TV"] < shifts[i + 1]["TV"] for i in range(len(shifts) - 1))
    last = shifts[-1]
    return "warning", (f"Der naive Gang ist bei allen drei Familien verzerrt; bei den Schichtfolgen {'wächst' if grows else 'schwankt'} der Abstand zur Gleichverteilung von {de(shifts[0]['TV'], 3)} (n = {shifts[0]['n']}) auf {de(last['TV'], 3)} (n = {last['n']}), "
                       f"dort kommt das wahrscheinlichste Wort {de(last['häufigstes Objekt (mal gerecht)'], 1)}-mal so oft vor wie gerecht. Wer den nächsten Schritt gleichverteilt unter den erlaubten wählt, bevorzugt Objekte, die durch Engstellen laufen.")


# ----------------------------------------------------------------------------- Experiment 3: Rejection kostet je Familie

@functools.cache
def rejection_rows() -> dict:
    rows = []
    for n in C.EXP_REJECT_NS:
        sh = Fraction(3 ** n, A.shift_completions(n)[n][0])
        dy = Fraction(4 ** n, A.catalan(n))
        mo = Fraction(3 ** n, A.motzkin_number(n))
        de_ = A.derangement_expected_tries(n)
        rows.append({"n": n, "Schichtfolgen": float(sh), "Dyck-Wörter": float(dy), "Motzkin-Wörter": float(mo), "Derangements": float(de_), "Dyck / (√π·n^1,5)": float(dy) / (math.sqrt(math.pi) * n ** 1.5)})
    top = C.EXP_REJECT_NS[-1]
    comp = A.shift_completions(top + 1)
    growth = float(Fraction(3 * comp[top][0], comp[top + 1][0]))
    n = C.EXP_REJECT_MEASURE_N
    rng = random.Random(C.EXP_SEED + 3)
    measured = []
    for fam in ("Schichtfolgen", "Dyck-Wörter (Catalan)", "Motzkin-Wörter"):
        ctx = build_context(fam, n)
        tries = [draw_once(ctx, "Rejection", rng)[1] for _ in range(C.EXP_REJECT_DRAWS)]
        measured.append({"Familie": fam, "n": n, "gemessen": sum(tries) / len(tries), "erwartet": float(expected_tries(ctx, "Rejection")), "Ziehungen": len(tries)})
    tries = []
    for _ in range(C.EXP_REJECT_DRAWS):
        t = 0
        while True:
            t += 1
            if A.derangement_valid(A.derangement_propose(n, rng)):
                break
        tries.append(t)
    measured.append({"Familie": "Derangements", "n": n, "gemessen": sum(tries) / len(tries), "erwartet": float(A.derangement_expected_tries(n)), "Ziehungen": len(tries)})
    return {"rows": rows, "growth": growth, "measured": measured}


def verdict_rejection(res: dict):
    rows = {r["n"]: r for r in res["rows"]}
    n1, n2 = 30, 100
    return "warning", (f"Rejection kostet je nach Familie ganz Verschiedenes: Schichtfolgen {count_text(rows[n1]['Schichtfolgen'])} Versuche bei n = {n1} und {count_text(rows[n2]['Schichtfolgen'])} bei n = {n2} (Faktor {de(res['growth'], 3)} je Schritt, exponentiell), "
                       f"Dyck-Wörter {count_text(rows[n1]['Dyck-Wörter'])} und {count_text(rows[n2]['Dyck-Wörter'])} (etwa √π·n^(3/2), polynomiell), Derangements immer etwa e = {de(rows[n2]['Derangements'], 3)}. "
                       "Ob Rejection taugt, hängt von der Wachstumsrate der Objekte gegen die der Vorschläge ab (Stück 9).")


# ----------------------------------------------------------------------------- Experiment 4: Boltzmann und das Fenster

CATALAN_TERMS = A.spec_terms(0, 1, 0)
MOTZKIN_TERMS = A.spec_terms(1, 0, 1)


@functools.cache
def boltzmann_distribution() -> list[dict]:
    """Größenverteilung der Boltzmann-Bäume bei x = ρ gegen c_n·ρⁿ/τ (Zellen 0 bis 12 und Rest)."""
    out = []
    for name, terms in (("Catalan: F = 1 + z·F²", CATALAN_TERMS), ("Motzkin: F = 1 + z·F + z²·F²", MOTZKIN_TERMS)):
        rho, tau = A.solve_system(terms)
        counts = A.spec_coefficients(terms, 12)
        rng = random.Random(C.EXP_SEED + 4)
        cells = [0] * 14
        for _ in range(C.EXP_BOLTZ_DRAWS):
            size, _ = A.boltzmann_size(terms, rho, tau, rng, C.EXP_BOLTZ_CAP)
            cells[13 if size is None or size >= 13 else size] += 1
        theo = [counts[i] * rho ** i / tau for i in range(13)]
        theo.append(1 - sum(theo))
        chi = sum((c - t * C.EXP_BOLTZ_DRAWS) ** 2 / (t * C.EXP_BOLTZ_DRAWS) for c, t in zip(cells, theo))
        out.append({"Gleichung": name, "rho": rho, "tau": tau, "empirisch": [c / C.EXP_BOLTZ_DRAWS for c in cells], "theoretisch": theo, "chi": chi, "df": 13, "z": A.z_of_chi(chi, 13)})
    return out


@functools.cache
def window_rows() -> list[dict]:
    """Versuche und Schritte je Treffer im Größenfenster (Catalan, x = ρ) gegen die Vorhersage 1/P(Fenster) und den Rekursions-Sampler."""
    rows = []
    rng = random.Random(C.EXP_SEED + 5)
    top = int(max(C.EXP_WINDOW_NS) * (1 + C.EXP_WINDOW_EPS)) + 1
    counts = [A.catalan(i) for i in range(top + 1)]
    for n0, wanted in zip(C.EXP_WINDOW_NS, C.EXP_WINDOW_DRAWS):
        lo, hi = int(n0 * (1 - C.EXP_WINDOW_EPS)), int(n0 * (1 + C.EXP_WINDOW_EPS))
        p = A.tree_count_terms(counts, 0.25, 2.0, lo, hi)
        tries = steps = got = 0
        while got < wanted:
            tries += 1
            size, st = A.boltzmann_size(CATALAN_TERMS, 0.25, 2.0, rng, hi)
            steps += st
            if size is not None and lo <= size <= hi:
                got += 1
        rows.append({"n0": n0, "lo": lo, "hi": hi, "P(Fenster)": p, "Versuche erwartet": 1 / p, "Versuche gemessen": tries / wanted, "Schritte je Treffer": steps / wanted, "Rekursions-Sampler": 2 * n0, "Treffer": wanted})
    return rows


@functools.cache
def x_rows(n0: int = 100) -> list[dict]:
    """Annahmewahrscheinlichkeit des Fensters ±10 % bei x = t·ρ (Catalan): sie wächst mit x bis ρ."""
    counts = [A.catalan(i) for i in range(1101)]
    lo, hi = int(n0 * 0.9), int(n0 * 1.1)
    rows = []
    for t in C.EXP_X_TS:
        x = 0.25 * t
        y = 2.0 if t >= 1 else A.spec_value(CATALAN_TERMS, x, 2.0)
        p = A.tree_count_terms(counts, x, y, lo, hi)
        mean = math.inf if t >= 1 else sum(i * math.exp(A.ln(counts[i]) + i * math.log(x)) for i in range(1, 1101)) / y
        rows.append({"t": t, "y": y, "Mittel der Größe": mean, "P(Fenster)": p, "Versuche": 1 / p})
    return rows


def verdict_boltzmann(dist: list[dict], windows: list[dict], xs: list[dict]):
    zs = [d["z"] for d in dist]
    worst = max(abs(w["Versuche gemessen"] / w["Versuche erwartet"] - 1) for w in windows)
    last = windows[-1]
    best = min(xs, key=lambda r: r["Versuche"])
    kind = "success" if all(abs(z) <= 4 for z in zs) else "warning"
    return kind, (f"Die Größe der Boltzmann-Bäume folgt c_n·ρⁿ/τ (z = {', '.join(de(z, 2) for z in zs)}). Ein Fenster ±10 % um n kostet 1/P(Fenster) Versuche: bei n = {last['n0']} erwartet {count_text(last['Versuche erwartet'])}, gemessen {count_text(last['Versuche gemessen'])} "
                  f"(größte Abweichung über alle Größen {percent(worst, 0)}; bei {last['Treffer']} Treffern ist ein Standardfehler von etwa {percent(1 / math.sqrt(last['Treffer']), 0)} Zufall), {count_text(last['Schritte je Treffer'])} Rechenschritte je Treffer gegen {last['Rekursions-Sampler']} beim Rekursions-Sampler, aber ohne Tabelle. Am besten ist x = ρ (t = {de(best['t'], 3)}): "
                  "kleiner gewählte x machen das Fenster seltener, und der Mittelwert der Größe ist bei x = ρ unendlich.")


# ----------------------------------------------------------------------------- Experiment 5: Bedingung und zufällige optimale Lösung

@functools.cache
def condition_rows() -> dict:
    n = C.EXP_COND_N
    tab = A.night_table(n)
    dist = A.night_counts(n)
    total = sum(dist)
    rng = random.Random(C.EXP_SEED + 6)
    rows = []
    for k, c in enumerate(dist):
        row = {"k": k, "Objekte": c, "Anteil": c / total, "Rejection (Versuche)": total / c, "z": None}
        if c > 1 and C.EXP_COND_DRAWS / c >= C.MIN_EXPECTED:
            words = A.night_words(n, k, tab)
            cnt = {}
            for _ in range(C.EXP_COND_DRAWS):
                w = A.night_sample(n, k, tab, rng)
                cnt[w] = cnt.get(w, 0) + 1
            row["z"] = A.z_of_chi(A.chi_square([cnt.get(w, 0) for w in words], C.EXP_COND_DRAWS / c), c - 1)
        rows.append(row)
    far = []
    for m in (100, 400):
        d = A.night_counts(m)
        tot = sum(d)
        mean = sum(i * v for i, v in enumerate(d)) / tot
        var = sum(i * i * v for i, v in enumerate(d)) / tot - mean ** 2
        kk = int(round(mean + 4 * math.sqrt(var)))
        far.append({"n": m, "k": kk, "Anteil": d[kk] / tot, "Versuche": tot / d[kk], "Stellen": A.digit_count(tot)})
    return {"rows": rows, "far": far, "total": total}


@functools.cache
def grid_experiment() -> dict:
    rows = cols = C.EXP_GRID
    rng = random.Random(C.EXP_SEED + 7)
    right, down = A.grid_costs(rows, cols, rng)
    dist, cnt = A.grid_semiring(rows, cols, right, down)
    paths = A.grid_all_paths(rows, cols)
    costs = [A.grid_path_cost(p, right, down) for p in paths]
    best = min(costs)
    optimal = [p for p, c in zip(paths, costs) if c == best]
    counts = {}
    for _ in range(C.EXP_GRID_DRAWS):
        p = A.grid_sample_optimal(rows, cols, right, down, dist, cnt, rng)
        counts[p] = counts.get(p, 0) + 1
    chi = A.chi_square([counts.get(p, 0) for p in optimal], C.EXP_GRID_DRAWS / len(optimal)) if len(optimal) > 1 else 0.0
    z = A.z_of_chi(chi, len(optimal) - 1) if len(optimal) > 1 else None
    probs = [A.grid_naive_probability(p, rows, cols, right, down, dist) for p in optimal]
    tv = float(A.total_variation(probs, len(optimal)))
    sizes = []
    for size in C.EXP_GRID_SIZES:
        r2, c2 = A.grid_costs(size, size, rng)
        d2, n2 = A.grid_semiring(size, size, r2, c2)
        sizes.append({"Gitter": f"{size}×{size}", "alle Wege": math.comb(2 * size - 2, size - 1), "kleinste Kosten": d2[(0, 0)], "optimale Wege": n2[(0, 0)]})
    return {"grid": f"{rows}×{cols}", "paths": len(paths), "best": best, "semiring_best": dist[(0, 0)], "optimal": len(optimal), "semiring_count": cnt[(0, 0)], "z": z, "tv": tv,
            "max_factor": float(max(probs) / min(probs)), "sizes": sizes, "draws": C.EXP_GRID_DRAWS}


def verdict_condition(cond: dict, grid: dict):
    rows = {r["k"]: r for r in cond["rows"]}
    kmax = max(rows)
    zs = [r["z"] for r in cond["rows"] if r["z"] is not None]
    far = cond["far"][-1]
    ok = all(abs(z) <= 4 for z in zs) and (grid["z"] is None or abs(grid["z"]) <= 4)
    return ("success" if ok else "warning"), (f"Mit der Bedingung „genau k Nächte“ zieht die Tabelle gezielt: bei n = 10 haben nur {rows[kmax]['Objekte']} von {big_text(cond['total'])} Schichtfolgen {kmax} Nächte, Rejection aus der Gesamtmenge bräuchte {count_text(rows[kmax]['Rejection (Versuche)'])} Versuche; "
                                                f"bei n = {far['n']} mit k = {far['k']} (Mittel plus vier Standardabweichungen) {count_text(far['Versuche'])}. Im Netz {grid['grid']} gibt es {grid['optimal']} optimale von {big_text(grid['paths'])} Wegen "
                                                f"(Semiring und Aufzählen stimmen überein); der Sampler nach Zahl der optimalen Fortsetzungen ist gleichverteilt (z = {de(grid['z'], 2) if grid['z'] is not None else '–'}), der naive Gang unter den optimalen Kanten nicht (Abstand {de(grid['tv'], 3)}).")


# ----------------------------------------------------------------------------- Spielwiese: eigene Gleichung

@functools.cache
def play_equation(c1: int, c2: int, c3: int, n: int, seed: int = C.EXP_SEED) -> dict:
    c1, c2, c3 = (max(0, min(c, C.PLAY_C_MAX)) for c in (c1, c2, c3))
    n = max(C.PLAY_N_MIN, min(n, C.PLAY_N_MAX))
    terms = A.spec_terms(c1, c2, c3)
    res = {"terms": terms, "n": n, "equation": equation_text(c1, c2, c3)}
    if not terms:
        res["kind"] = "trivial"
        return res
    if A.is_periodic(terms):
        res["kind"] = "periodic"
        return res
    if not A.is_nonlinear(terms):
        res.update(kind="pole", mu=c1, rho=1 / c1)
        return res
    rho, tau = A.solve_system(terms)
    lo, hi = size_window(n, 10)
    counts = A.spec_coefficients(terms, max(hi, 40))
    p = A.tree_count_terms(counts, rho, tau, lo, hi)
    rng = random.Random(seed)
    tries = steps = got = 0
    sizes_hit = []
    while got < C.PLAY_DRAWS and steps < C.MAX_STEPS:
        tries += 1
        size, st = A.boltzmann_size(terms, rho, tau, rng, hi)
        steps += st
        if size is not None and lo <= size <= hi:
            got += 1
            sizes_hit.append(size)
    hist = {}
    for _ in range(C.PLAY_HIST_DRAWS):
        size, _ = A.boltzmann_size(terms, rho, tau, rng, C.PLAY_CAP)
        key = -1 if size is None else size
        hist[key] = hist.get(key, 0) + 1
    theo = {m: counts[m] * rho ** m / tau for m in range(0, 31)}
    res.update(kind="root", rho=rho, tau=tau, window=(lo, hi), p_window=p, tries_expected=1 / p if p > 0 else None, tries_measured=tries / got if got else None,
               steps_per_hit=steps / got if got else None, hits=got, sizes_hit=sizes_hit, hist=hist, theory=theo, leaf_prob=1 / tau, recursion_steps=2 * n)
    return res


def equation_text(c1: int, c2: int, c3: int) -> str:
    def coef(c):
        return "" if c == 1 else str(c)

    parts = ["1"]
    if c1:
        parts.append(f"{coef(c1)}z·F")
    if c2:
        parts.append(f"{coef(c2)}z·F²")
    if c3:
        parts.append(f"{coef(c3)}z²·F²")
    return "F = " + " + ".join(parts)


def verdict_play(res: dict):
    if res["kind"] == "trivial":
        return "info", "Alle Koeffizienten sind 0: F = 1, es gibt nur die leere Struktur; es gibt nichts zu ziehen."
    if res["kind"] == "periodic":
        return "warning", ("Die Gleichung hat nur Terme mit z²: es kommen nur gerade Größen vor (Periode 2, Stück 3), und es gibt mehrere Singularitäten auf dem Rand. Die App zieht nur bei aperiodischen Gleichungen "
                           "(mindestens ein Term mit z¹).")
    if res["kind"] == "pole":
        mu = res["mu"]
        denominator = "1 − z" if mu == 1 else f"1 − {mu}z"
        return "info", (f"Die Gleichung ist linear: F = 1/({denominator}), die Zahl der Objekte der Größe n ist {mu}ⁿ. Der Boltzmann-Sampler bei x = ρ = {de(res['rho'], 6)} liefe in den Pol "
                        "(die Größe wäre unendlich). Bitte c₂ oder c₃ wählen.")
    lo, hi = res["window"]
    if not res["hits"]:
        return "warning", f"{res['equation']}: bei x = ρ = {de(res['rho'], 6)} wurde in {count_text(C.MAX_STEPS)} Rechenschritten kein Baum im Fenster {lo} bis {hi} gezogen."
    return "success", (f"{res['equation']}: ρ = {de(res['rho'], 6)}, τ = {de(res['tau'], 6)}; Blatt mit Wahrscheinlichkeit 1/τ = {de(res['leaf_prob'], 4)}. Fenster {lo} bis {hi}: P(Fenster) = {sci_text(res['p_window'], 3)}, "
                       f"erwartet {count_text(res['tries_expected'])} Versuche je Treffer, gemessen {count_text(res['tries_measured'])} ({res['hits']} Treffer), {count_text(res['steps_per_hit'])} Rechenschritte je Treffer "
                       f"gegen {res['recursion_steps']} bei einer Tabelle (Größe n).")
