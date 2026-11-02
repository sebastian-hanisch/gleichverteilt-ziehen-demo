"""PDF-Export der aktuellen Ziehung mit den Prüfungen und den ersten Objekten (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

from gvz_evaluation import Analysis, answer_rows, verdict_answers
from gvz_scenario import object_text

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "€": "EUR", "„": '"', "“": '"', "ⁿ": "^n", "²": "^2", "ₖ": "k", "∞": "unendlich",
            "⁻": "-", "⁰": "0", "¹": "1", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "ₙ": "n", "χ": "chi", "ρ": "rho", "τ": "tau", "√": "Wurzel", "≈": "~"}


def _s(text) -> str:
    out = str(text)
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Gleichverteilt ziehen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    s = a.settings
    extra = f", genau {a.k_eff} Nächte" if s.family == "Schichtfolgen mit k Nächten" else ""
    pdf.multi_cell(0, 5, _s(f"{s.family}{extra}, n = {a.n_eff}, Verfahren: {a.method_eff}, {a.draws_done} Ziehungen, Seed {s.seed}. Alles gerechnet, keine Messdaten."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.multi_cell(0, 5, _s(verdict_answers(a)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    widths = (60, 50, 80)
    heads = ("Frage", "Ergebnis", "Prüfung")
    for h, w in zip(heads, widths):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for row in answer_rows(a):
        for key, w in zip(heads, widths):
            pdf.cell(w, 5.5, _s(row[key])[:48], border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Die ersten gezogenen Objekte"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 8)
    for obj in a.shown:
        pdf.multi_cell(0, 4, _s(object_text(s.family, obj))[:190], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: gleichverteilt-ziehen-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
