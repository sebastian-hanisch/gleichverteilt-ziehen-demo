"""Gleichverteilt ziehen – zählen, dann entrollen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 10 der Reihe „Abzählen und erzeugende Funktionen“: Wie zieht man ein Objekt gleichverteilt, ohne alle zu kennen? Wer die Fortsetzungszahlen hat (die Tabellen aus Stück 1 bis 8), entrollt sie zu
einem Objekt mit genau der Wahrscheinlichkeit 1/Gesamtzahl (Rekursions-Sampler). Rejection kostet je nach Familie exponentiell, polynomiell oder konstant viele Versuche; der naive Gang ist verzerrt;
der Boltzmann-Sampler ersetzt die Tabelle durch die Singularität aus Stück 9.
Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import gvz_constants as C
from gvz_evaluation import (
    Settings,
    analyse,
    answer_rows,
    big_text,
    boltzmann_distribution,
    condition_rows,
    count_text,
    de,
    grid_experiment,
    naive_rows,
    percent,
    play_equation,
    rejection_rows,
    sci_text,
    statistic_name,
    uniformity_rows,
    verdict_answers,
    verdict_boltzmann,
    verdict_condition,
    verdict_naive,
    verdict_play,
    verdict_rejection,
    verdict_uniformity,
    window_rows,
    x_rows,
)
from gvz_layout import dunkles_design, kopf_css
from gvz_pdf_export import build_pdf
from gvz_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    sidebar_presets,
    sync_query_params,
)
from gvz_scenario import object_text
from gvz_visualization import (
    build_boltzmann_dist,
    build_conditions,
    build_counts_chart,
    build_naive,
    build_play,
    build_rejection,
    build_size_chart,
    build_stat_chart,
    build_windows,
    build_x_choice,
)

st.set_page_config(page_title="Gleichverteilt ziehen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner="Die Experimente werden einmal gerechnet (feste Seeds) …")
def _uniformity():
    return uniformity_rows()


@st.cache_data(show_spinner="Die Experimente werden einmal gerechnet (feste Seeds) …")
def _naive():
    return naive_rows()


@st.cache_data(show_spinner="Die Experimente werden einmal gerechnet (feste Seeds) …")
def _rejection():
    return rejection_rows()


@st.cache_data(show_spinner="Die Experimente werden einmal gerechnet (feste Seeds) …")
def _boltzmann():
    return boltzmann_distribution(), window_rows(), x_rows()


@st.cache_data(show_spinner="Die Experimente werden einmal gerechnet (feste Seeds) …")
def _conditions():
    return condition_rows(), grid_experiment()


@st.cache_data(show_spinner=False)
def _play(c1, c2, c3, n):
    return play_equation(c1, c2, c3, n)


def verdict(pair):
    kind, text = pair
    getattr(st, kind)(text)


def dot(x: int) -> str:
    """Ganze Zahl mit Tausenderpunkt."""
    return f"{x:,}".replace(",", ".")


def short(text: str, width: int = 70) -> str:
    return text if len(text) <= width else text[:width] + f"… ({len(text)} Zeichen)"


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in gvz_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🎲 Gleichverteilt ziehen – zählen, dann entrollen")
st.markdown(
    """
**Wie zieht man ein Objekt gleichverteilt, ohne alle zu kennen?** Wer die **Fortsetzungszahlen** hat (die Tabellen aus Stück 1 bis 8: wie viele Folgen gibt es noch hinter diesem Zustand), wählt den nächsten Schritt mit der
Wahrscheinlichkeit „Fortsetzungen dahinter durch Fortsetzungen insgesamt“ und rollt so ein Objekt in $n$ Schritten ab: **jedes Objekt hat genau die Wahrscheinlichkeit $1/\\text{Gesamtzahl}$** (**Rekursions-Sampler**).
Es geht auch ohne Tabelle: **Rejection** würfelt aus einer größeren Menge und wirft Ungültiges weg (je nach Familie exponentiell, polynomiell oder konstant teuer), der **Boltzmann-Sampler** zieht Bäume mit der Singularität
$\\rho$ aus Stück 9. Und es gibt die **falsche Abkürzung**: den nächsten Schritt gleichverteilt unter den erlaubten zu wählen (der **naive Gang**) ist nicht gleichverteilt.

Weiter unten: **fünf Experimente** (**🔬**), eine **🎲 Spielwiese**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert das Ziehen", expanded=True):
    st.markdown(
        """
1. **Zählen:** Für jeden Zustand die Zahl der gültigen Fortsetzungen aufschreiben (Stück 1: Automat, Stück 3: Gleichung, Stück 6: Stirling-Zahlen, Stück 8: Verteilung nach Parameter).
2. **Entrollen:** Eine Zufallszahl $r$ von $0$ bis Gesamtzahl $-1$ ziehen und das $r$-te Objekt ablesen, Schritt für Schritt (auf ganzen Zahlen, ohne Gleitkomma). Jedes $r$ gehört zu genau einem Objekt.
3. **Rejection:** aus einer größeren Menge ziehen und verwerfen, was nicht passt; die erwartete Zahl der Versuche ist Vorschläge geteilt durch Zahl der Objekte.
4. **Boltzmann:** bei $x = \\rho$ Bäume ohne Tabelle ziehen (Blatt mit Wahrscheinlichkeit $1/\\tau$, sonst ein Knoten); die Größe ist zufällig, $P(N = n) = c_n \\rho^n / \\tau$; ein **Größenfenster** wählt die passenden aus.
5. **Gegenprobe:** alle Objekte aufzählen, die Wahrscheinlichkeit jedes Objekts als Bruch ausrechnen und die Ziehungen mit dem Chi-Quadrat-Test vergleichen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Aufgabe**")
    family = st.selectbox("Familie", list(C.FAMILIES), key="family_select", help="Welche Objekte gezogen werden: Schichtfolgen (Stück 1), mit genau k Nächten (Stück 8), Dyck-Wörter (Catalan, Stück 3), Motzkin-Wörter, Mengenpartitionen (Stück 6).")
    method = st.selectbox("Verfahren", list(C.METHODS), key="method_select", help="Rekursions-Sampler (Tabelle), Rejection (würfeln und wegwerfen), Boltzmann (nur Catalan-Bäume) oder der naive Gang. Gibt es ein Verfahren für die Familie nicht, wird der Rekursions-Sampler genommen und das gesagt.")
    n = st.slider("Größe n", *bounds("n_slider"), key="n_slider", help=f"Länge der Folge (bei Dyck-Wörtern Zahl der Klammerpaare). Höchstens bis {C.N_CAP['Mengenpartitionen']} bei Mengenpartitionen, sonst bis {C.N_MAX}.")
    k = st.slider("Zahl der Nächte k (nur Familie mit Bedingung)", *bounds("k_slider"), key="k_slider", help="Genau so viele Nachtschichten muss die gezogene Schichtfolge haben; größer als möglich wird auf das Größte begrenzt.")
    st.markdown("**Ziehung**")
    window = st.slider("Größenfenster ± % (nur Boltzmann)", *bounds("window_slider"), key="window_slider", help="Der Boltzmann-Baum wird angenommen, wenn seine Größe im Fenster n ± Prozent liegt; bei 0 muss sie genau n sein.")
    draws = st.slider("Zahl der Ziehungen", *bounds("draws_slider"), key="draws_slider", help="Wie viele Objekte gezogen werden. Rejection und Boltzmann brechen bei einer Obergrenze von Rechenschritten ab und sagen das.")
    seed = st.slider("Seed", *bounds("seed_slider"), key="seed_slider", help="Gleicher Seed, gleiche Ziehungen.")

sync_query_params({"family_select": family, "method_select": method, "n_slider": int(n), "k_slider": int(k), "window_slider": int(window), "draws_slider": int(draws), "seed_slider": int(seed)})

settings = Settings(family, method, int(n), int(k), int(window), int(draws), int(seed))
a = _analysis(settings)
for note in a.notes:
    st.info(note)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Zahl der Objekte", big_text(a.total), help="Gezählt mit der Tabelle (Stück 1 bis 8); Schichtfolgen, Dyck-Wörter, Motzkin-Wörter, Mengenpartitionen oder die mit k Nächten.")
m2.metric("Versuche je Objekt", "–" if a.tries_mean is None else count_text(a.tries_mean), help="Bei Rejection und Boltzmann: wie oft vorgeschlagen werden muss, bis ein gültiges Objekt kommt; sonst 1.")
m3.metric("Rechenschritte je Objekt", "–" if a.steps_mean is None else count_text(a.steps_mean), help="Gezählt: Buchstaben oder Schritte des Entrollens beziehungsweise der Vorschläge; kein Zeitmaß.")
if a.z is not None:
    m4.metric("z-Wert des Chi-Quadrat", de(a.z, 2), help="Standardisiert: bei gleichverteilten Ziehungen meist zwischen −3 und 3; weit darüber heißt verzerrt.")
elif a.tv is not None:
    m4.metric("Abstand zur Gleichverteilung", de(a.tv, 3), help="Totalvariation, exakt aus den Wahrscheinlichkeiten aller Objekte gerechnet.")
elif a.exact_uniform:
    m4.metric("Wahrscheinlichkeit je Objekt", "exakt gleich", help="Für alle Objekte als Bruch nachgerechnet: jedes hat genau 1/Gesamtzahl. Das Chi-Quadrat braucht mindestens 5 Ziehungen je Objekt im Mittel.")
else:
    m4.metric("z-Wert des Chi-Quadrat", "–", help="Nur bei aufzählbaren Mengen und genug Ziehungen (im Mittel mindestens 5 je Objekt).")

if a.shown:
    st.markdown("**Die ersten gezogenen Objekte**")
    st.code("\n".join(short(object_text(family, o)) for o in a.shown), language=None)

stat = a.extras.get("stat")
if "counts" in a.extras and len(a.extras["counts"]) > 1:
    st.plotly_chart(build_counts_chart(a.extras["counts"], a.draws_done / a.total), width="stretch", key="main_chart")
    st.caption("Zahl der Ziehungen je Objekt (Reihenfolge der Aufzählung), gestrichelt die gerechte Erwartung. Bei gleichverteilten Ziehungen streuen die Säulen eng um die Linie; der naive Gang bevorzugt einige Objekte deutlich.")
elif a.sizes:
    st.plotly_chart(build_size_chart(a.sizes, a.n_eff), width="stretch", key="main_chart")
    st.caption("Größen der angenommenen Bäume im Fenster: die Größe ist zufällig, die Bäume einer Größe sind gleichverteilt unter den Bäumen dieser Größe.")
if stat:
    st.plotly_chart(build_stat_chart(stat, statistic_name(family)), width="stretch", key="stat_chart")
    st.caption("Eine Kenngröße der gezogenen Objekte gegen ihre exakte Verteilung (aus den gezählten Tabellen: Stück 8, Narayana-Zahlen, Trinomialsumme, Stirling-Zahlen). Sie prüft die Gleichverteilung auch dort, wo man nicht alle Objekte aufzählen kann.")
st.dataframe(answer_rows(a), hide_index=True, width="stretch")

if st.button("📄 PDF der aktuellen Ziehung erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(a))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="gleichverteilt-ziehen.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie zieht man ein Objekt, ohne alle zu kennen?")
verdict(verdict_answers(a))

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Dieselbe Aufgabe auf allen Wegen")
st.caption(f"Vier kleine Familien, jedes Verfahren: {dot(C.EXP_DRAWS)} Ziehungen (Boltzmann 4.000) mit festem Seed, alle Objekte aufgezählt. z ist das standardisierte Chi-Quadrat: bei gleichverteilten Ziehungen meist zwischen −3 und 3.")
uni = _uniformity()
st.dataframe([{"Familie": r["Familie"], "n": r["n"], "Verfahren": r["Verfahren"], "Objekte": r["Objekte"], "Ziehungen": r["Ziehungen"], "z": "–" if r["z"] is None else de(r["z"], 2),
               "Abstand zur Gleichverteilung": "–" if r["TV"] is None else de(r["TV"], 3), "exakt 1/Objekte": "–" if r["exakt"] is None else ("ja" if r["exakt"] else "nein"),
               "Versuche": "–" if r["Versuche"] is None else count_text(r["Versuche"])} for r in uni], hide_index=True, width="stretch")
verdict(verdict_uniformity(uni))

st.markdown("---")

st.subheader("🔬 Experiment 2: Der naive Gang ist verzerrt")
st.caption("Den nächsten Schritt gleichverteilt unter den erlaubten wählen sieht fair aus, ist es aber nicht. Der Abstand zur Gleichverteilung (Totalvariation, ½·Σ|p − 1/Gesamtzahl|) ist aus den Wahrscheinlichkeiten aller Objekte gerechnet.")
naive = _naive()
st.plotly_chart(build_naive(naive), width="stretch", key="naive_chart")
st.dataframe([{"Familie": r["Familie"], "n": r["n"], "Objekte": r["Objekte"], "Abstand": de(r["TV"], 4), "häufigstes Objekt (mal gerecht)": de(r["häufigstes Objekt (mal gerecht)"], 2),
               "größte gegen kleinste Wahrscheinlichkeit": de(r["größte gegen kleinste"], 1)} for r in naive], hide_index=True, width="stretch")
verdict(verdict_naive(naive))

st.markdown("---")

st.subheader("🔬 Experiment 3: Rejection kostet je Familie etwas anderes")
st.caption(f"Erwartete Versuche bis zum ersten gültigen Objekt = Vorschläge durch Objekte, exakt gerechnet (Schichtfolgen 3ⁿ, Dyck-Wörter 4ⁿ, Motzkin-Wörter 3ⁿ Vorschläge; Derangements n! Permutationen). Darunter gezogen bei n = {C.EXP_REJECT_MEASURE_N}.")
rej = _rejection()
st.plotly_chart(build_rejection(rej), width="stretch", key="rejection_chart")
st.dataframe([{"n": r["n"], "Schichtfolgen": count_text(r["Schichtfolgen"]), "Dyck-Wörter": count_text(r["Dyck-Wörter"]), "Motzkin-Wörter": count_text(r["Motzkin-Wörter"]), "Derangements": de(r["Derangements"], 3),
               "Dyck / (√π·n^1,5)": de(r["Dyck / (√π·n^1,5)"], 4)} for r in rej["rows"]], hide_index=True, width="stretch")
st.dataframe([{"Familie": r["Familie"], "n": r["n"], "Ziehungen": r["Ziehungen"], "Versuche gemessen": de(r["gemessen"], 2), "Versuche erwartet": de(r["erwartet"], 2)} for r in rej["measured"]], hide_index=True, width="stretch")
verdict(verdict_rejection(rej))

st.markdown("---")

st.subheader("🔬 Experiment 4: Boltzmann-Sampler und das Größenfenster")
st.caption("Bei x = ρ (Stück 9) entsteht der Baum ohne Tabelle: Knoten mit Wahrscheinlichkeit 1 − 1/τ, sonst Blatt. Oben die Größenverteilung gegen c_n·ρⁿ/τ, dann die Versuche im Fenster ±10 % gegen 1/P(Fenster) und die Wahl von x.")
dist, windows, xs = _boltzmann()
st.plotly_chart(build_boltzmann_dist(dist), width="stretch", key="boltz_chart")
st.dataframe([{"Gleichung": d["Gleichung"], "ρ": de(d["rho"], 6), "τ": de(d["tau"], 6), "Chi-Quadrat": de(d["chi"], 1), "Freiheitsgrade": d["df"], "z": de(d["z"], 2)} for d in dist], hide_index=True, width="stretch")
st.plotly_chart(build_windows(windows), width="stretch", key="window_chart")
st.dataframe([{"n": w["n0"], "Fenster": f"{w['lo']} bis {w['hi']}", "P(Fenster)": sci_text(w["P(Fenster)"], 3), "Versuche erwartet": count_text(w["Versuche erwartet"]), "Versuche gemessen": count_text(w["Versuche gemessen"]),
               "Schritte je Treffer": count_text(w["Schritte je Treffer"]), "Schritte der Tabelle": w["Rekursions-Sampler"], "Treffer": w["Treffer"]} for w in windows], hide_index=True, width="stretch")
st.plotly_chart(build_x_choice(xs), width="stretch", key="x_chart")
st.dataframe([{"t = x/ρ": de(r["t"], 3), "y(x)": de(r["y"], 4), "mittlere Größe": "unendlich" if r["Mittel der Größe"] == float("inf") else de(r["Mittel der Größe"], 2), "P(Fenster)": sci_text(r["P(Fenster)"], 3),
               "erwartete Versuche": count_text(r["Versuche"])} for r in xs], hide_index=True, width="stretch")
verdict(verdict_boltzmann(dist, windows, xs))

st.markdown("---")

st.subheader("🔬 Experiment 5: Ziehen mit Bedingung und die zufällige optimale Lösung")
st.caption("Die Tabelle kann gezielt ziehen: genau k Nächte (Stück 8), oder eine optimale Lösung gleichverteilt unter allen optimalen (Stück 4: das Semiring (min, +, Zahl) liefert die Fortsetzungszahlen).")
cond, grid = _conditions()
st.plotly_chart(build_conditions(cond["rows"]), width="stretch", key="cond_chart")
st.dataframe([{"k": r["k"], "Schichtfolgen": r["Objekte"], "Anteil": percent(r["Anteil"], 3), "Rejection aus der Gesamtmenge (Versuche)": count_text(r["Rejection (Versuche)"]), "z der Tabelle": "–" if r["z"] is None else de(r["z"], 2)} for r in cond["rows"]],
             hide_index=True, width="stretch")
st.dataframe([{"n": f["n"], "Stellen der Gesamtzahl": f["Stellen"], "k (Mittel + 4σ)": f["k"], "Anteil": sci_text(f["Anteil"], 3), "Rejection (Versuche)": count_text(f["Versuche"])} for f in cond["far"]], hide_index=True, width="stretch")
st.dataframe([{"Gitter": f"{grid['grid']} (Kosten 1 oder 2)", "alle Wege": grid["paths"], "kleinste Kosten": grid["best"], "optimale Wege (Aufzählen)": grid["optimal"], "optimale Wege (Semiring)": grid["semiring_count"],
               "z des Samplers": "–" if grid["z"] is None else de(grid["z"], 2), "Abstand des naiven Gangs": de(grid["tv"], 3)}], hide_index=True, width="stretch")
st.dataframe([{"Gitter": f["Gitter"], "alle Wege": sci_text(float(f["alle Wege"]), 3), "kleinste Kosten": f["kleinste Kosten"], "optimale Wege": f["optimale Wege"]} for f in grid["sizes"]], hide_index=True, width="stretch")
verdict(verdict_condition(cond, grid))

st.markdown("---")

# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🎲 Spielwiese: Boltzmann-Bäume der eigenen Gleichung")
st.caption("F = 1 + c₁·z·F + c₂·z·F² + c₃·z²·F²: Koeffizienten wählen; ρ und τ kommen aus dem System (Stück 9), dann werden Bäume bei x = ρ gezogen und die im Fenster n ± 10 % angenommen. Mit c₂ = c₃ = 0 ist die Gleichung linear (Pol statt Wurzel), mit nur c₃ periodisch.")
q1, q2, q3, q4 = st.columns(4)
c1 = q1.slider("c₁ (z·F)", 0, C.PLAY_C_MAX, 0, key="play_c1", help="Koeffizient des Terms z·F (linear).")
c2 = q2.slider("c₂ (z·F²)", 0, C.PLAY_C_MAX, 1, key="play_c2", help="Koeffizient des Terms z·F²: Catalan-Bäume bei c₂ = 1.")
c3 = q3.slider("c₃ (z²·F²)", 0, C.PLAY_C_MAX, 0, key="play_c3", help="Koeffizient des Terms z²·F².")
pn = q4.slider("Zielgröße n", C.PLAY_N_MIN, C.PLAY_N_MAX, C.PLAY_N_DEFAULT, key="play_n", help="Gesucht werden Bäume mit n bis aufgerundet 10 % Abweichung.")
play = _play(int(c1), int(c2), int(c3), int(pn))
if play["kind"] == "root" and play["hist"]:
    st.plotly_chart(build_play(play), width="stretch", key="play_chart")
    st.caption(f"Größen von {dot(C.PLAY_HIST_DRAWS)} Bäumen bei x = ρ (Abbruch bei Größe über {dot(C.PLAY_CAP)}) gegen c_m·ρᵐ/τ; der Schwanz ist schwer (P(N > m) ≈ 1/√(π·m) bei Catalan).")
verdict(verdict_play(play))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Es gibt Fortsetzungszahlen** | Ohne Tabelle (zum Beispiel bei #P-schweren Mengen) bleibt nur Rejection oder ein Markov-Ketten-Sampler; Letzteres ist nicht gleichverteilt, sondern nur im Grenzwert. | Stück 15 (Schätzen) |
| **Die Zahlen sind exakt** | Der Rekursions-Sampler zieht Zufallszahlen auf ganzen Zahlen (`randrange`); wer die Verhältnisse in Gleitkomma rechnet, ist nicht mehr exakt gleichverteilt. | – |
| **Rejection hat eine kleine Ausfallrate** | Schichtfolgen: Faktor 1,178 mehr Versuche je Schritt; bei n = 60 etwa 15.000, bei n = 100 rund 10 Millionen. Die App bricht bei {dot(C.MAX_STEPS)} Rechenschritten ab und sagt das. | Experiment 3 |
| **Boltzmann braucht eine Singularität** | Nur für Gleichungen wie die der Spielwiese; bei einem Pol (linearer Fall) läuft die Größe ins Unendliche, bei Perioden gibt es mehrere Singularitäten. | Stück 9 |
| **Die Größe muss stimmen** | Der Boltzmann-Sampler liefert eine zufällige Größe; wer genau n braucht, zahlt etwa 2√π·n^(3/2) Versuche (Catalan). | Experiment 4 |
| **Stichproben beweisen nichts** | Ein Chi-Quadrat liegt bei einem exakten Sampler in etwa 5 % der Fälle außerhalb von ±2; der Beweis der Gleichverteilung ist der Bruch je Objekt, nicht die Stichprobe. | – |
| **Die Größe ist begrenzt** | Die Familien bis n = {C.N_MAX} (Mengenpartitionen bis n = {C.N_CAP['Mengenpartitionen']}), höchstens {dot(C.DRAWS_MAX)} Ziehungen; Objekte werden nur bis {dot(C.ENUM_MAX)} aufgezählt. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Rekursions-Sampler.** Sei $c(i, s)$ die Zahl der gültigen Fortsetzungen der Länge $i$ vom Zustand $s$ aus. Das Objekt entsteht Schritt für Schritt: vom Zustand $s$ mit noch $i$ Schritten wird der Übergang nach $s'$ mit der Wahrscheinlichkeit
$c(i-1, s') / c(i, s)$ gewählt. Dann hat jedes Objekt die Wahrscheinlichkeit $\prod_j \dfrac{c(i_j - 1, s_j')}{c(i_j, s_j)} = \dfrac{1}{c(n, s_0)}$, weil sich das Produkt zusammenzieht. Äquivalent: ein Rang $r \in \{0, \dots, c(n, s_0) - 1\}$ wird gleichverteilt gezogen und entrollt.

**Rejection.** Schlägt man gleichverteilt aus einer Menge $U$ vor und behält nur die gültigen, ist das Ergebnis gleichverteilt unter den gültigen, und die erwartete Zahl der Versuche ist $|U| / c_n$. Für die Schichtfolgen ist $|U| = 3^n$ und $c_n \sim \lambda^n$ mit $\lambda = 2{,}5468$, die Versuche wachsen also um den Faktor $3/\lambda$ je Schritt; für Dyck-Wörter ist $|U| = 4^n$ und $c_n = C_n \sim 4^n/(\sqrt{\pi}\, n^{3/2})$, die Versuche wachsen wie $\sqrt{\pi}\, n^{3/2}$.

**Naiver Gang.** Wählt man bei jedem Schritt gleichverteilt unter den erlaubten Möglichkeiten, hat ein Objekt die Wahrscheinlichkeit $\prod_j 1/d_j$ mit der Zahl $d_j$ der Optionen im Schritt $j$; das ist nur gleich $1/c_n$, wenn jedes Objekt dieselben Optionen durchläuft.

**Boltzmann-Sampler.** Für $F = 1 + \sum_i c_i z^{j_i} F^{k_i}$ und $0 < x \le \rho$ sei $y = F(x)$. Ein Baum ist das Blatt mit der Wahrscheinlichkeit $1/y$, sonst der Term $i$ mit der Wahrscheinlichkeit $c_i x^{j_i} y^{k_i - 1}$ (dann $j_i$ Atome, $k_i$ Kinder). Die Größe $N$ hat $P(N = n) = c_n x^n / y$, und unter gleicher Größe sind die Bäume gleichverteilt. Bei $x = \rho$ ist $y = \tau$ und $P(N = n) \sim \dfrac{\gamma}{2\sqrt{\pi}\,\tau}\, n^{-3/2}$ (Stück 9), der Mittelwert der Größe ist unendlich.

**Stirling-Sampler.** Für Mengenpartitionen von $n$ Elementen in $k$ Blöcke: das letzte Element tritt einem der $k$ Blöcke einer Partition von $n-1$ Elementen bei (Zahl $k\, S(n-1, k)$) oder steht allein ($S(n-1, k-1)$); mit der Wahrscheinlichkeit dieser Zahlen geteilt durch $S(n, k)$ entsteht eine gleichverteilte Partition.

**Zufällige optimale Lösung.** Im Semiring $(\min, +, \text{Zahl})$ liefert die Rückwärtsrechnung für jeden Knoten die kleinsten Kosten und die Zahl der optimalen Wege; wählt man an jedem Knoten den Nachfolger mit der Wahrscheinlichkeit (optimale Fortsetzungen dahinter)/(optimale Fortsetzungen hier), ist der optimale Weg gleichverteilt.

**Literatur** (Titel und Fundstelle aus dem Gedächtnis, nicht eingesehen).
P. Duchon, P. Flajolet, G. Louchard und G. Schaeffer: *Boltzmann samplers for the random generation of combinatorial structures*, Combinatorics, Probability and Computing 13, 2004, S. 577–625.
A. Nijenhuis und H. S. Wilf: *Combinatorial Algorithms*, Academic Press, 1975 (rekursive Methode, Rang und Entrollen).
P. Flajolet, P. Zimmermann und B. Van Cutsem: *A calculus for the random generation of labelled combinatorial structures*, Theoretical Computer Science 132, 1994, S. 1–35.
P. Flajolet und R. Sedgewick: *Analytic Combinatorics*, Cambridge University Press, 2009.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
