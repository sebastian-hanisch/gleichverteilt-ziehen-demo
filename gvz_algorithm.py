"""Rechenkern: gleichverteilt ziehen. Rekursions-Sampler (Fortsetzungszahlen entrollen), Rejection, naiver Gang, Boltzmann-Sampler, Stirling-Sampler für Mengenpartitionen und zufällige optimale Wege im Netz.

Alles mit `int` und `fractions.Fraction`; Zufall nur über ein übergebenes `random.Random`, damit gleiche Seeds gleiche Ziehungen geben. Ziehungen aus großen Mengen laufen über `rng.randrange` auf ganzen Zahlen (exakt, ohne Gleitkomma-Verhältnisse)."""

import math
from fractions import Fraction

C = math.comb


# ----------------------------------------------------------------------------- Zahlen

def digit_count(x: int) -> int:
    """Zahl der Dezimalstellen einer ganzen Zahl x >= 0, ohne sie in einen String zu wandeln (Python begrenzt die Umwandlung auf 4300 Stellen)."""
    if x < 0:
        raise ValueError("x darf nicht negativ sein")
    d = max(1, int(x.bit_length() * 0.30102999566398))
    while 10 ** d <= x:
        d += 1
    while d > 1 and 10 ** (d - 1) > x:
        d -= 1
    return d


def ln(x) -> float:
    """Natürlicher Logarithmus einer beliebig großen ganzen oder gebrochenen positiven Zahl."""
    if isinstance(x, Fraction):
        return ln(x.numerator) - ln(x.denominator)
    if x <= 0:
        raise ValueError("Logarithmus verlangt eine positive Zahl")
    if x.bit_length() < 1000:
        return math.log(x)
    shift = x.bit_length() - 900
    return math.log(x >> shift) + shift * math.log(2)


def chi_square(counts, expected: float) -> float:
    """Chi-Quadrat-Statistik für gleiche Erwartung je Zelle."""
    if expected <= 0:
        raise ValueError("Erwartungswert muss positiv sein")
    return sum((c - expected) ** 2 / expected for c in counts)


def z_of_chi(stat: float, df: int) -> float:
    """Standardisierung der Chi-Quadrat-Statistik: (Statistik − df)/√(2·df)."""
    if df <= 0:
        raise ValueError("Freiheitsgrade müssen positiv sein")
    return (stat - df) / math.sqrt(2 * df)


def total_variation(probs, total: int) -> Fraction:
    """Abstand zur Gleichverteilung auf `total` Objekten: ½·Σ|p − 1/total| (die Wahrscheinlichkeiten müssen alle Objekte erfassen)."""
    return sum((abs(p - Fraction(1, total)) for p in probs), Fraction(0)) / 2


# ----------------------------------------------------------------------------- Schichtfolgen (Automat aus Stück 1 und 8)

# keine Früh (F) direkt nach einer Nacht (N), höchstens zwei Nächte in Folge; Zustand = Zahl der Nächte am Ende
TRANS = {0: (("F", 0), ("S", 0), ("N", 1)), 1: (("S", 0), ("N", 2)), 2: (("S", 0),)}
LETTERS = "FSN"


def shift_valid(word: str) -> bool:
    return all(ch in LETTERS for ch in word) and "NF" not in word and "NNN" not in word


def shift_completions(n: int) -> list:
    """comp[i][s] = Zahl der Folgen der Länge i, die vom Zustand s aus noch gültig fortgesetzt werden."""
    if n < 0:
        raise ValueError("n darf nicht negativ sein")
    comp = [{s: 1 for s in TRANS}]
    for _ in range(n):
        prev = comp[-1]
        comp.append({s: sum(prev[nxt] for _, nxt in TRANS[s]) for s in TRANS})
    return comp


def shift_unrank(n: int, r: int, comp: list) -> str:
    """Das r-te gültige Wort der Länge n in der Reihenfolge der Buchstaben F < N < S (0 <= r < Gesamtzahl)."""
    if not 0 <= r < comp[n][0]:
        raise ValueError("Rang außerhalb der Gesamtzahl")
    s, word = 0, []
    for i in range(n, 0, -1):
        for letter, nxt in sorted(TRANS[s]):
            c = comp[i - 1][nxt]
            if r < c:
                word.append(letter)
                s = nxt
                break
            r -= c
    return "".join(word)


def shift_rank(word: str, comp: list) -> int:
    """Umkehrung von `shift_unrank`."""
    n = len(word)
    s, r = 0, 0
    for i, letter in enumerate(word):
        for other, nxt in sorted(TRANS[s]):
            if other == letter:
                s = nxt
                break
            r += comp[n - i - 1][nxt]
    return r


def shift_sample(n: int, comp: list, rng) -> str:
    return shift_unrank(n, rng.randrange(comp[n][0]), comp)


def shift_words(n: int) -> list:
    """Alle gültigen Wörter (Reihenfolge der Entrollung)."""
    out = []

    def rec(s, word):
        if len(word) == n:
            out.append("".join(word))
            return
        for letter, nxt in sorted(TRANS[s]):
            word.append(letter)
            rec(nxt, word)
            word.pop()

    rec(0, [])
    return out


def shift_naive_probability(word: str) -> Fraction:
    """Wahrscheinlichkeit, dass der naive Gang (unter den erlaubten Buchstaben gleichverteilt) genau dieses Wort liefert."""
    s, p = 0, Fraction(1)
    for letter in word:
        options = TRANS[s]
        p *= Fraction(1, len(options))
        s = dict(options)[letter]
    return p


def shift_naive_sample(n: int, rng) -> str:
    s, word = 0, []
    for _ in range(n):
        letter, s = rng.choice(TRANS[s])
        word.append(letter)
    return "".join(word)


def shift_recursion_probability(word: str, comp: list) -> Fraction:
    """Wahrscheinlichkeit des Worts beim Rekursions-Sampler: Produkt der Verhältnisse (Fortsetzungen dahinter durch Fortsetzungen davor)."""
    n = len(word)
    s, p = 0, Fraction(1)
    for i, letter in enumerate(word):
        nxt = dict(TRANS[s])[letter]
        p *= Fraction(comp[n - i - 1][nxt], comp[n - i][s])
        s = nxt
    return p


def shift_propose(n: int, rng) -> str:
    """Vorschlag der Rejection: ein Wort über F, S, N gleichverteilt (3ⁿ Möglichkeiten)."""
    return "".join(rng.choice(LETTERS) for _ in range(n))


# --- mit Bedingung: genau k Nächte (Stück 8)

def night_table(n: int) -> list:
    """tab[i][s] = {k: Zahl der Fortsetzungen der Länge i vom Zustand s aus mit genau k weiteren Nächten}."""
    tab = [{s: {0: 1} for s in TRANS}]
    for _ in range(n):
        prev = tab[-1]
        cur = {}
        for s in TRANS:
            d = {}
            for letter, nxt in TRANS[s]:
                add = 1 if letter == "N" else 0
                for kk, v in prev[nxt].items():
                    d[kk + add] = d.get(kk + add, 0) + v
            cur[s] = d
        tab.append(cur)
    return tab


def night_counts(n: int) -> list:
    """Verteilung der Zahl der Nächte: Liste c[k] (Stück 8)."""
    d = night_table(n)[n][0]
    return [d.get(k, 0) for k in range(max(d) + 1)]


def night_sample(n: int, k: int, tab: list, rng) -> str:
    total = tab[n][0].get(k, 0)
    if total <= 0:
        raise ValueError("keine Schichtfolge mit dieser Zahl von Nächten")
    s, word, need = 0, [], k
    r = rng.randrange(total)
    for i in range(n, 0, -1):
        for letter, nxt in sorted(TRANS[s]):
            add = 1 if letter == "N" else 0
            c = tab[i - 1][nxt].get(need - add, 0)
            if r < c:
                word.append(letter)
                s, need = nxt, need - add
                break
            r -= c
    return "".join(word)


def night_words(n: int, k: int, tab: list) -> list:
    """Alle Schichtfolgen der Länge n mit genau k Nächten (die Tabelle schneidet jede Sackgasse ab)."""
    out = []

    def rec(s, word, need):
        left = n - len(word)
        if left == 0:
            if need == 0:
                out.append("".join(word))
            return
        for letter, nxt in sorted(TRANS[s]):
            add = 1 if letter == "N" else 0
            if tab[left - 1][nxt].get(need - add, 0):
                word.append(letter)
                rec(nxt, word, need - add)
                word.pop()

    if tab[n][0].get(k, 0):
        rec(0, [], k)
    return out


def night_recursion_probability(word: str, tab: list) -> Fraction:
    n = len(word)
    k = word.count("N")
    s, need, p = 0, k, Fraction(1)
    for i, letter in enumerate(word):
        nxt = dict(TRANS[s])[letter]
        add = 1 if letter == "N" else 0
        p *= Fraction(tab[n - i - 1][nxt].get(need - add, 0), tab[n - i][s].get(need, 0))
        s, need = nxt, need - add
    return p


# ----------------------------------------------------------------------------- Dyck-Wörter (Catalan, Stück 3)

def catalan(n: int) -> int:
    return C(2 * n, n) // (n + 1)


def ballot_table(n: int) -> list:
    """b[i][h] = Zahl der Wege mit i restlichen Schritten von Höhe h zurück auf 0, nie unter 0, höchstens n Öffnungen insgesamt wird durch die Höhe begrenzt."""
    b = [[0] * (n + 2) for _ in range(2 * n + 1)]
    b[0][0] = 1
    for i in range(1, 2 * n + 1):
        for h in range(0, n + 1):
            b[i][h] = (b[i - 1][h + 1] if h + 1 <= n else 0) + (b[i - 1][h - 1] if h >= 1 else 0)
    return b


def dyck_sample(n: int, table: list, rng) -> str:
    h, word = 0, []
    r = rng.randrange(table[2 * n][0])
    for i in range(2 * n, 0, -1):
        up = table[i - 1][h + 1] if h + 1 <= n else 0
        if r < up:
            word.append("(")
            h += 1
        else:
            r -= up
            word.append(")")
            h -= 1
    return "".join(word)


def dyck_valid(word: str) -> bool:
    h = 0
    for ch in word:
        h += 1 if ch == "(" else -1 if ch == ")" else 10 ** 9
        if h < 0:
            return False
    return h == 0


def dyck_words(n: int) -> list:
    out = []

    def rec(word, h, opens):
        if len(word) == 2 * n:
            out.append("".join(word))
            return
        if opens < n:
            word.append("(")
            rec(word, h + 1, opens + 1)
            word.pop()
        if h > 0:
            word.append(")")
            rec(word, h - 1, opens)
            word.pop()

    rec([], 0, 0)
    return out


def dyck_recursion_probability(word: str, table: list) -> Fraction:
    n = len(word) // 2
    h, p = 0, Fraction(1)
    for i, ch in enumerate(word):
        rest = 2 * n - i
        if ch == "(":
            p *= Fraction(table[rest - 1][h + 1], table[rest][h])
            h += 1
        else:
            p *= Fraction(table[rest - 1][h - 1], table[rest][h])
            h -= 1
    return p


def dyck_naive_choices(word_prefix_height: int, opens: int, n: int) -> list:
    """Erlaubte nächste Zeichen des naiven Gangs: Öffnen nur, solange noch Öffnungen übrig sind, Schließen nur über Höhe 0."""
    options = []
    if opens < n:
        options.append("(")
    if word_prefix_height > 0:
        options.append(")")
    return options


def dyck_naive_probability(word: str) -> Fraction:
    n = len(word) // 2
    h = opens = 0
    p = Fraction(1)
    for ch in word:
        p *= Fraction(1, len(dyck_naive_choices(h, opens, n)))
        if ch == "(":
            h += 1
            opens += 1
        else:
            h -= 1
    return p


def dyck_naive_sample(n: int, rng) -> str:
    h = opens = 0
    word = []
    for _ in range(2 * n):
        ch = rng.choice(dyck_naive_choices(h, opens, n))
        word.append(ch)
        if ch == "(":
            h += 1
            opens += 1
        else:
            h -= 1
    return "".join(word)


def dyck_propose(n: int, rng) -> str:
    """Vorschlag der Rejection: 2n Münzwürfe (4ⁿ Möglichkeiten)."""
    return "".join(rng.choice("()") for _ in range(2 * n))


# ----------------------------------------------------------------------------- Motzkin-Wörter (Schritte hoch, flach, runter; Stück 3 und 9)

def motzkin_number(n: int) -> int:
    m = [1, 1]
    for k in range(2, n + 1):
        m.append(((2 * k + 1) * m[k - 1] + (3 * k - 3) * m[k - 2]) // (k + 2))
    return m[n]


def motzkin_table(n: int) -> list:
    """b[i][h] = Zahl der Wege mit i restlichen Schritten von Höhe h zurück auf 0, nie unter 0."""
    b = [[0] * (n + 2) for _ in range(n + 1)]
    b[0][0] = 1
    for i in range(1, n + 1):
        for h in range(0, n + 1):
            b[i][h] = b[i - 1][h] + (b[i - 1][h + 1] if h + 1 <= n else 0) + (b[i - 1][h - 1] if h >= 1 else 0)
    return b


STEPS = (("U", 1), ("F", 0), ("D", -1))


def motzkin_sample(n: int, table: list, rng) -> str:
    h, word = 0, []
    r = rng.randrange(table[n][0])
    for i in range(n, 0, -1):
        for letter, dh in STEPS:
            nh = h + dh
            c = table[i - 1][nh] if 0 <= nh <= n else 0
            if r < c:
                word.append(letter)
                h = nh
                break
            r -= c
    return "".join(word)


def motzkin_valid(word: str) -> bool:
    h = 0
    for ch in word:
        if ch not in "UFD":
            return False
        h += 1 if ch == "U" else -1 if ch == "D" else 0
        if h < 0:
            return False
    return h == 0


def motzkin_words(n: int) -> list:
    out = []

    def rec(word, h):
        if len(word) == n:
            if h == 0:
                out.append("".join(word))
            return
        for letter, dh in STEPS:
            nh = h + dh
            if nh >= 0 and nh <= n - len(word) - 1:
                word.append(letter)
                rec(word, nh)
                word.pop()

    rec([], 0)
    return out


def motzkin_recursion_probability(word: str, table: list) -> Fraction:
    n = len(word)
    h, p = 0, Fraction(1)
    delta = dict(STEPS)
    for i, ch in enumerate(word):
        nh = h + delta[ch]
        p *= Fraction(table[n - i - 1][nh], table[n - i][h])
        h = nh
    return p


def motzkin_naive_choices(h: int, remaining: int) -> list:
    """Erlaubte nächste Schritte des naiven Gangs: nie unter 0 und so, dass die Höhe noch auf 0 zurückkommen kann."""
    return [(letter, dh) for letter, dh in STEPS if h + dh >= 0 and h + dh <= remaining - 1]


def motzkin_naive_probability(word: str) -> Fraction:
    n = len(word)
    h, p = 0, Fraction(1)
    delta = dict(STEPS)
    for i, ch in enumerate(word):
        p *= Fraction(1, len(motzkin_naive_choices(h, n - i)))
        h += delta[ch]
    return p


def motzkin_naive_sample(n: int, rng) -> str:
    h, word = 0, []
    for i in range(n):
        letter, dh = rng.choice(motzkin_naive_choices(h, n - i))
        word.append(letter)
        h += dh
    return "".join(word)


def motzkin_propose(n: int, rng) -> str:
    """Vorschlag der Rejection: ein Wort über U, F, D gleichverteilt (3ⁿ Möglichkeiten)."""
    return "".join(rng.choice("UFD") for _ in range(n))


# ----------------------------------------------------------------------------- Mengenpartitionen (Stück 6)

def stirling2_table(n: int) -> list:
    s = [[0] * (n + 1) for _ in range(n + 1)]
    s[0][0] = 1
    for i in range(1, n + 1):
        for k in range(1, i + 1):
            s[i][k] = k * s[i - 1][k] + s[i - 1][k - 1]
    return s


def bell_number(n: int) -> int:
    return sum(stirling2_table(n)[n])


def partition_sample(n: int, table: list, rng) -> tuple:
    """Gleichverteilte Mengenpartition von {1..n} als Restricted-Growth-String: erst die Blockzahl k mit Wahrscheinlichkeit S(n,k)/Bell, dann von hinten Element für Element."""
    r = rng.randrange(sum(table[n]))
    k = 0
    while r >= table[n][k]:
        r -= table[n][k]
        k += 1
    return partition_sample_fixed(n, k, table, rng)


def partition_sample_fixed(n: int, k: int, table: list, rng) -> tuple:
    """Gleichverteilte Partition mit genau k Blöcken: Element m tritt einem der k Blöcke bei (Zahl k·S(m−1,k)) oder steht allein (S(m−1,k−1))."""
    if not 1 <= k <= n or table[n][k] == 0:
        raise ValueError("keine Partition mit dieser Blockzahl")
    decisions = []
    blocks = k
    for m in range(n, 0, -1):
        total = table[m][blocks]
        stay = blocks * table[m - 1][blocks]
        if rng.randrange(total) < stay:
            decisions.append(True)
        else:
            decisions.append(False)
            blocks -= 1
    decisions.reverse()
    assign, opened = [], 0
    for joins in decisions:
        if joins:
            assign.append(rng.randrange(opened))
        else:
            assign.append(opened)
            opened += 1
    return tuple(assign)


def partitions_all(n: int) -> list:
    """Alle Restricted-Growth-Strings der Länge n (jede Mengenpartition genau einmal)."""
    out = []

    def rec(prefix, m):
        if len(prefix) == n:
            out.append(tuple(prefix))
            return
        for v in range(m + 1):
            prefix.append(v)
            rec(prefix, max(m, v + 1))
            prefix.pop()

    rec([], 0)
    return out


def partition_recursion_probability(rgs: tuple, table: list) -> Fraction:
    n = len(rgs)
    k = max(rgs) + 1
    p = Fraction(table[n][k], sum(table[n]))
    blocks = k
    seen = set()
    firsts = []
    for v in rgs:
        firsts.append(v not in seen)
        seen.add(v)
    for m in range(n, 0, -1):
        alone = firsts[m - 1]
        if alone:
            p *= Fraction(table[m - 1][blocks - 1], table[m][blocks])
            blocks -= 1
        else:
            p *= Fraction(blocks * table[m - 1][blocks], table[m][blocks]) * Fraction(1, blocks)
    return p


def partition_naive_probability(rgs: tuple) -> Fraction:
    p, opened = Fraction(1), 0
    for v in rgs:
        p *= Fraction(1, opened + 1)
        opened = max(opened, v + 1)
    return p


def partition_naive_sample(n: int, rng) -> tuple:
    """Naiver Aufbau: jedes Element wählt gleichverteilt unter den vorhandenen Blöcken und einem neuen."""
    out, opened = [], 0
    for _ in range(n):
        v = rng.randrange(opened + 1)
        out.append(v)
        opened = max(opened, v + 1)
    return tuple(out)


def partition_text(rgs: tuple) -> str:
    blocks = {}
    for i, v in enumerate(rgs, start=1):
        blocks.setdefault(v, []).append(i)
    return " ".join("{" + ",".join(map(str, b)) + "}" for b in blocks.values())


# ----------------------------------------------------------------------------- Derangements (nur Rejection, Stück 6)

def derangements(n: int) -> int:
    d = [1, 0]
    for k in range(2, n + 1):
        d.append((k - 1) * (d[k - 1] + d[k - 2]))
    return d[n]


def derangement_expected_tries(n: int) -> Fraction:
    return Fraction(math.factorial(n), derangements(n))


def derangement_propose(n: int, rng) -> list:
    p = list(range(n))
    rng.shuffle(p)
    return p


def derangement_valid(p: list) -> bool:
    return all(p[i] != i for i in range(len(p)))


# ----------------------------------------------------------------------------- Boltzmann-Sampler für F = 1 + Σ c·zʲ·Fᵏ (Stück 3 und 9)

def spec_terms(c1: int, c2: int, c3: int) -> list:
    """F = 1 + c1·z·F + c2·z·F² + c3·z²·F² als Liste (Koeffizient, j, k); Terme mit Koeffizient 0 entfallen."""
    return [t for t in ((c1, 1, 1), (c2, 1, 2), (c3, 2, 2)) if t[0] > 0]


def spec_coefficients(terms, n_max: int) -> list:
    """Koeffizienten von F online: F[n] = Σ c·P_k[n−j] mit den Potenzen P_k = F^k (k <= 3)."""
    for c, j, k in terms:
        if not (c >= 0 and j >= 1 and 1 <= k <= 3):
            raise ValueError(f"Term {(c, j, k)}: verlangt c >= 0, j >= 1, 1 <= k <= 3")
    f, p2, p3 = [1], [1], [1]
    powers = {1: f, 2: p2, 3: p3}
    for n in range(1, n_max + 1):
        total = 0
        for c, j, k in terms:
            if n - j >= 0:
                total += c * powers[k][n - j]
        f.append(total)
        p2.append(sum(f[i] * f[n - i] for i in range(n + 1)))
        p3.append(sum(f[i] * p2[n - i] for i in range(n + 1)))
    return f


def phi(terms, z, y):
    return 1 + sum(c * z ** j * y ** k for c, j, k in terms)


def phi_y(terms, z, y):
    return sum(c * k * z ** j * y ** (k - 1) for c, j, k in terms)


def is_nonlinear(terms) -> bool:
    return any(k >= 2 for _, _, k in terms)


def is_periodic(terms) -> bool:
    if not terms:
        return False
    g = 0
    for _, j, _ in terms:
        g = math.gcd(g, j)
    return g > 1


def solve_system(terms) -> tuple:
    """(ρ, τ): τ = Φ(ρ, τ) und Φ_y(ρ, τ) = 1; kleinste Lösung mit τ > 1 (wie Stück 9). Verlangt eine nichtlineare, aperiodische Gleichung."""
    if not is_nonlinear(terms):
        raise ValueError("linear: keine Wurzelsingularität")
    if is_periodic(terms):
        raise ValueError("periodisch: mehrere Singularitäten auf dem Rand")

    def z_of(tau):
        lo, hi = 0.0, 1.0
        while phi_y(terms, hi, tau) < 1:
            hi *= 2
        for _ in range(200):
            mid = (lo + hi) / 2
            if phi_y(terms, mid, tau) < 1:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    h = lambda tau: phi(terms, z_of(tau), tau) - tau
    tau = 1.0
    prev = h(tau)
    while tau < 1e9:
        nxt = tau * 1.02
        val = h(nxt)
        if prev > 0 >= val:
            lo, hi = tau, nxt
            for _ in range(200):
                mid = (lo + hi) / 2
                if h(mid) > 0:
                    lo = mid
                else:
                    hi = mid
            t = (lo + hi) / 2
            return z_of(t), t
        tau, prev = nxt, val
    raise RuntimeError("keine Singularität gefunden")


def spec_value(terms, x: float, tau: float) -> float:
    """Kleinste Lösung y von y = 1 + Σ c·xʲ·yᵏ für 0 <= x <= ρ (Bisektion in [1, τ]); bei x = ρ ist das τ."""
    f = lambda y: 1 + sum(c * x ** j * y ** k for c, j, k in terms) - y
    lo, hi = 1.0, tau
    if f(lo) <= 0:
        return lo
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def boltzmann_size(terms, x: float, y: float, rng, cap: int) -> tuple:
    """Zieht einen Baum der Gleichung; Rückgabe (Größe, Schritte) mit Größe = Zahl der z-Atome; bei Größe > cap Abbruch (None, Schritte).

    Ein Knoten ist das Blatt „1“ mit Wahrscheinlichkeit 1/y, sonst der Term c·zʲ·Fᵏ mit Wahrscheinlichkeit c·xʲ·y^(k−1): j Atome, k Kinder."""
    probs = [1 / y] + [c * x ** j * y ** (k - 1) for c, j, k in terms]
    pending, size, steps = 1, 0, 0
    while pending:
        pending -= 1
        steps += 1
        u = rng.random()
        acc = 0.0
        choice = len(probs) - 1
        for i, p in enumerate(probs):
            acc += p
            if u < acc:
                choice = i
                break
        if choice:
            _, j, k = terms[choice - 1]
            size += j
            if size > cap:
                return None, steps
            pending += k
    return size, steps


def boltzmann_dyck(rng, cap: int) -> tuple:
    """Boltzmann-Sampler der Catalan-Bäume F = 1 + z·F² bei x = ρ = 1/4 (y = 2, Knoten und Blatt je mit Wahrscheinlichkeit 1/2); Rückgabe (Dyck-Wort, Schritte) oder (None, Schritte) bei Größe > cap.

    Abbildung Baum → Wort: Knoten(links, rechts) wird zu „(“ + Wort(links) + „)“ + Wort(rechts), das Blatt zu „“; dies ist eine Bijektion auf die Dyck-Wörter."""
    out = []
    stack = [None]            # None = Baum erzeugen, ")" = Zeichen ausgeben
    size = steps = 0
    while stack:
        item = stack.pop()
        if item == ")":
            out.append(")")
            continue
        steps += 1
        if rng.random() < 0.5:
            continue          # Blatt
        size += 1
        if size > cap:
            return None, steps
        out.append("(")
        stack.append(None)    # rechter Teilbaum
        stack.append(")")
        stack.append(None)    # linker Teilbaum
    return "".join(out), steps


def tree_count_terms(counts: list, x: float, y: float, lo: int, hi: int) -> float:
    """P(Größe in [lo, hi]) = Σ c_n·xⁿ / y für die Bäume der Gleichung (Gleitkomma über Logarithmen, damit nichts überläuft)."""
    total = 0.0
    for n in range(lo, min(hi, len(counts) - 1) + 1):
        c = counts[n]
        if c:
            total += math.exp(ln(c) + (n * math.log(x) if x > 0 else (0.0 if n == 0 else -math.inf)) - math.log(y))
    return total


# ----------------------------------------------------------------------------- Netz: zufällige optimale Lösung (Stück 4)

def grid_costs(rows: int, cols: int, rng, costs=(1, 2)) -> tuple:
    right = {(r, c): rng.choice(costs) for r in range(rows) for c in range(cols - 1)}
    down = {(r, c): rng.choice(costs) for r in range(rows - 1) for c in range(cols)}
    return right, down


def grid_semiring(rows: int, cols: int, right: dict, down: dict) -> tuple:
    """Vom Ziel her im Semiring (min, +, Zahl): dist = kleinste Kosten bis zum Ziel, cnt = Zahl der optimalen Wege."""
    dist, cnt = {}, {}
    for r in range(rows - 1, -1, -1):
        for c in range(cols - 1, -1, -1):
            if (r, c) == (rows - 1, cols - 1):
                dist[(r, c)], cnt[(r, c)] = 0, 1
                continue
            cands = []
            if c + 1 < cols:
                cands.append((right[(r, c)] + dist[(r, c + 1)], (r, c + 1)))
            if r + 1 < rows:
                cands.append((down[(r, c)] + dist[(r + 1, c)], (r + 1, c)))
            best = min(d for d, _ in cands)
            dist[(r, c)] = best
            cnt[(r, c)] = sum(cnt[v] for d, v in cands if d == best)
    return dist, cnt


def _optimal_successors(r, c, rows, cols, right, down, dist):
    opts = []
    if c + 1 < cols and right[(r, c)] + dist[(r, c + 1)] == dist[(r, c)]:
        opts.append((r, c + 1))
    if r + 1 < rows and down[(r, c)] + dist[(r + 1, c)] == dist[(r, c)]:
        opts.append((r + 1, c))
    return opts


def grid_sample_optimal(rows: int, cols: int, right: dict, down: dict, dist: dict, cnt: dict, rng) -> tuple:
    """Gleichverteilter optimaler Weg: an jeder Stelle den Nachfolger mit Wahrscheinlichkeit (optimale Fortsetzungen dahinter)/(optimale Fortsetzungen hier)."""
    r = c = 0
    path = [(0, 0)]
    while (r, c) != (rows - 1, cols - 1):
        opts = _optimal_successors(r, c, rows, cols, right, down, dist)
        pick = rng.randrange(sum(cnt[v] for v in opts))
        for v in opts:
            if pick < cnt[v]:
                r, c = v
                break
            pick -= cnt[v]
        path.append((r, c))
    return tuple(path)


def grid_naive_optimal(rows: int, cols: int, right: dict, down: dict, dist: dict, rng) -> tuple:
    """Naiv: unter den optimalen Nachfolgern gleichverteilt."""
    r = c = 0
    path = [(0, 0)]
    while (r, c) != (rows - 1, cols - 1):
        r, c = rng.choice(_optimal_successors(r, c, rows, cols, right, down, dist))
        path.append((r, c))
    return tuple(path)


def grid_all_paths(rows: int, cols: int) -> list:
    out = []

    def rec(r, c, path):
        if (r, c) == (rows - 1, cols - 1):
            out.append(tuple(path))
            return
        if c + 1 < cols:
            path.append((r, c + 1))
            rec(r, c + 1, path)
            path.pop()
        if r + 1 < rows:
            path.append((r + 1, c))
            rec(r + 1, c, path)
            path.pop()

    rec(0, 0, [(0, 0)])
    return out


def grid_path_cost(path: tuple, right: dict, down: dict) -> int:
    total = 0
    for a, b in zip(path, path[1:]):
        total += right[a] if b[1] == a[1] + 1 else down[a]
    return total


def grid_naive_probability(path: tuple, rows: int, cols: int, right: dict, down: dict, dist: dict) -> Fraction:
    p = Fraction(1)
    for a in path[:-1]:
        p *= Fraction(1, len(_optimal_successors(a[0], a[1], rows, cols, right, down, dist)))
    return p
