"""Turn LaTeX that AI models write into plain Unicode text.

Moved from pipelines/ocr/output.py (Session 48) so Search can use it
without importing the OCR package (output.py needs python-docx).
"""
import re


# LaTeX that models still write in AI summaries, turned into plain symbols.
# Used only on AI-written summary text, never on OCR page text (verbatim).
# Unknown commands are left as they are, so nothing is guessed.
_LATEX_SYMBOLS = {
    "pm": "±", "mp": "∓", "times": "×", "div": "÷", "cdot": "·",
    "geq": "≥", "ge": "≥", "geqslant": "≥", "leq": "≤", "le": "≤",
    "leqslant": "≤", "neq": "≠", "ne": "≠", "approx": "≈", "sim": "~",
    "rightarrow": "→", "to": "→", "leftarrow": "←", "Rightarrow": "⇒",
    "leftrightarrow": "↔", "uparrow": "↑", "downarrow": "↓",
    "infty": "∞", "degree": "°",
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ",
    "kappa": "κ", "lambda": "λ", "mu": "μ", "sigma": "σ", "chi": "χ",
}
_LATEX_CMD = re.compile(r"\\([A-Za-z]+)(?![A-Za-z])")
_LATEX_DEGREE = re.compile(r"\^\s*\{?\s*\\circ\s*\}?")
_LATEX_ESCAPE = re.compile(r"\\([%&#])")
_LATEX_MATH = re.compile(r"\$([^$\n]+?)\$")
# \text{mean} etc.: keep the words, drop the wrapper (only inside $...$)
_LATEX_TEXT = re.compile(
    r"\\(?:text|textrm|textit|textbf|mathrm|mathit|mathbf|operatorname)"
    r"\s*\{([^{}]*)\}")


def _latex_symbols(text):
    text = _LATEX_DEGREE.sub("°", text)
    text = _LATEX_ESCAPE.sub(r"\1", text)
    return _LATEX_CMD.sub(
        lambda m: _LATEX_SYMBOLS.get(m.group(1), m.group(0)), text)


def strip_latex(text):
    """Known LaTeX commands -> Unicode; $...$ removed only around LaTeX.

    "$\\pm$" -> "±", "37$^\\circ$C" -> "37°C", "50\\%" -> "50%".
    Money ("$5 and $10"), [?] marks and unknown commands stay as they are.
    None stays None.
    """
    if not text:
        return text

    def _math(m):
        inner = m.group(1)
        if "\\" not in inner:
            stat = inner.strip()
            if re.fullmatch(r"[A-Za-z]\s*[=<>≤≥]\s*[−-]?\d[\d.,]*", stat):
                return stat  # "$P = 0.8$" -> "P = 0.8"; money starts with a digit
            return m.group(0)  # not LaTeX, e.g. "$5 and $"
        plain = _latex_symbols(_LATEX_TEXT.sub(r"\1", inner))
        plain = re.sub(r" {2,}", " ", plain)  # "\text{SD } -0.3" -> "SD -0.3"
        return plain.strip() if "\\" not in plain else m.group(0)

    return _latex_symbols(_LATEX_MATH.sub(_math, text))
