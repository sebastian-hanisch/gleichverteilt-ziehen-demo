"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import gvz_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_stat_chart(rows: list[dict], name: str):
    """Anteil der Ziehungen je Wert einer Kenngröße gegen den exakten Anteil (Zahl der Nächte, Gipfel, flache Schritte, Blöcke)."""
    fig = go.Figure()
    xs = [r["Wert"] for r in rows]
    fig.add_trace(go.Bar(x=xs, y=[r["gezogen"] for r in rows], name="gezogen", marker_color=C.COLOR_MAIN))
    fig.add_trace(go.Scatter(x=xs, y=[r["theoretisch"] for r in rows], mode="lines+markers", name="exakt (gezählt)", line=dict(color=C.COLOR_WARN)))
    fig.update_xaxes(title_text=name)
    fig.update_yaxes(title_text="Anteil")
    return _base(fig)


def build_counts_chart(counts: list, expected: float):
    """Zahl der Ziehungen je Objekt (in der Reihenfolge der Aufzählung) mit der gerechten Erwartung."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(range(len(counts))), y=counts, name="Ziehungen je Objekt", marker_color=C.COLOR_MAIN))
    fig.add_hline(y=expected, line=dict(color=C.COLOR_WARN, dash="dash"))
    fig.update_xaxes(title_text="Objekt (Nummer in der Aufzählung)")
    fig.update_yaxes(title_text="Ziehungen")
    return _base(fig)


def build_size_chart(sizes: dict, n: int):
    """Größen der Boltzmann-Bäume im Fenster (Zahl je Größe)."""
    fig = go.Figure()
    xs = sorted(sizes)
    fig.add_trace(go.Bar(x=xs, y=[sizes[x] for x in xs], name="angenommene Bäume", marker_color=C.COLOR_MAIN))
    fig.update_xaxes(title_text=f"Größe (Zahl der Knoten), gesucht n = {n}")
    fig.update_yaxes(title_text="Zahl")
    return _base(fig)


def build_naive(rows: list[dict]):
    """Abstand des naiven Gangs zur Gleichverteilung gegen n, je Familie."""
    fig = go.Figure()
    for fam in dict.fromkeys(r["Familie"] for r in rows):
        sub = [r for r in rows if r["Familie"] == fam]
        fig.add_trace(go.Scatter(x=[r["n"] for r in sub], y=[r["TV"] for r in sub], mode="lines+markers", name=fam))
    fig.update_xaxes(title_text="n")
    fig.update_yaxes(title_text="Abstand zur Gleichverteilung", range=[0, 0.6])
    return _base(fig)


def build_rejection(res: dict):
    """Erwartete Versuche der Rejection je Familie gegen n (logarithmische Achsen)."""
    fig = go.Figure()
    for key in ("Schichtfolgen", "Dyck-Wörter", "Motzkin-Wörter", "Derangements"):
        fig.add_trace(go.Scatter(x=[r["n"] for r in res["rows"]], y=[r[key] for r in res["rows"]], mode="lines+markers", name=key))
    fig.update_xaxes(title_text="n", type="log")
    fig.update_yaxes(title_text="erwartete Versuche je Objekt", type="log")
    return _base(fig, 360)


def build_boltzmann_dist(dist: list[dict]):
    """Größenverteilung der Boltzmann-Bäume: gezogen gegen c_n·ρⁿ/τ (Zellen 0 bis 12 und Rest)."""
    fig = go.Figure()
    xs = [str(i) for i in range(13)] + ["≥ 13"]
    for d in dist:
        short = d["Gleichung"].split(":")[0]
        fig.add_trace(go.Bar(x=xs, y=d["empirisch"], name=f"{short}: gezogen"))
        fig.add_trace(go.Scatter(x=xs, y=d["theoretisch"], mode="lines+markers", name=f"{short}: c_n·ρⁿ/τ"))
    fig.update_xaxes(title_text="Größe des Baums (Zahl der z-Atome)")
    fig.update_yaxes(title_text="Anteil", type="log")
    return _base(fig, 360)


def build_windows(rows: list[dict]):
    """Versuche je Treffer im Größenfenster: erwartet gegen gemessen."""
    fig = go.Figure()
    xs = [f"n = {r['n0']}" for r in rows]
    fig.add_trace(go.Bar(x=xs, y=[r["Versuche erwartet"] for r in rows], name="erwartet 1/P(Fenster)", marker_color=C.COLOR_LINE))
    fig.add_trace(go.Bar(x=xs, y=[r["Versuche gemessen"] for r in rows], name="gemessen", marker_color=C.COLOR_MAIN))
    fig.update_yaxes(title_text="Versuche je Treffer")
    return _base(fig, 300)


def build_x_choice(rows: list[dict]):
    """Versuche je Treffer gegen t = x/ρ (logarithmische Achse)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["t"] for r in rows], y=[r["Versuche"] for r in rows], mode="lines+markers", name="erwartete Versuche", line=dict(color=C.COLOR_MAIN)))
    fig.update_xaxes(title_text="t = x/ρ")
    fig.update_yaxes(title_text="erwartete Versuche (Fenster ±10 % um n = 100)", type="log")
    return _base(fig, 300)


def build_conditions(rows: list[dict]):
    """Versuche der Rejection aus der Gesamtmenge je Zahl der Nächte k (logarithmische Achse)."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[r["k"] for r in rows], y=[r["Rejection (Versuche)"] for r in rows], name="Rejection aus der Gesamtmenge", marker_color=C.COLOR_LINE))
    fig.add_hline(y=1, line=dict(color=C.COLOR_WARN, dash="dash"))
    fig.update_xaxes(title_text="gesuchte Zahl der Nächte k", dtick=1)
    fig.update_yaxes(title_text="Versuche je Schichtfolge (die Tabelle braucht 1)", type="log")
    return _base(fig, 300)


def build_play(res: dict):
    """Größen der Boltzmann-Bäume der eigenen Gleichung: gezogen gegen c_m·ρᵐ/τ (logarithmische Achsen, Größen 0 bis 30)."""
    fig = go.Figure()
    total = sum(res["hist"].values())
    ms = [m for m in range(0, 31) if res["theory"].get(m, 0) > 0]
    fig.add_trace(go.Bar(x=ms, y=[res["hist"].get(m, 0) / total for m in ms], name="gezogen", marker_color=C.COLOR_MAIN))
    fig.add_trace(go.Scatter(x=ms, y=[res["theory"][m] for m in ms], mode="lines+markers", name="exakt c_m·ρᵐ/τ", line=dict(color=C.COLOR_WARN)))
    fig.update_xaxes(title_text="Größe des Baums")
    fig.update_yaxes(title_text="Anteil", type="log")
    return _base(fig, 320)
