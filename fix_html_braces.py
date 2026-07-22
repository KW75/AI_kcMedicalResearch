from pathlib import Path

p = Path("D:/ai-automation-tool/sr/src/reporting/html_report.py")
src = p.read_text(encoding="utf-8")

# Find the HTML_TEMPLATE string boundaries
start = src.index('HTML_TEMPLATE = """')
end   = src.index('"""', start + len('HTML_TEMPLATE = """')) + 3

template_block = src[start:end]

# Split into the opening marker, CSS/HTML content, and closing marker
inner_start = start + len('HTML_TEMPLATE = """')
inner_end   = src.index('"""', inner_start)
inner       = src[inner_start:inner_end]

# Double all braces that are NOT already doubled and NOT Python format placeholders
# Strategy: double ALL braces first, then un-double the known format placeholders
import re
# Step 1: double all { and }
escaped = inner.replace("{", "{{").replace("}", "}}")

# Step 2: restore the known .format() placeholders (single braces)
placeholders = [
    "title", "authors_html", "generated_date", "model_name", "effect_measure",
    "n_uploaded", "n_included", "n_excluded", "n_uncertain", "k_studies",
    "pooled_display", "pico_html", "criteria_html", "screening_rows",
    "extraction_rows", "rob_rows", "ci_lower_display", "ci_upper_display",
    "z_display", "p_display", "i2_display", "tau2_display", "q_display",
    "q_p_display", "forest_plot_html",
]
for ph in placeholders:
    escaped = escaped.replace("{{" + ph + "}}", "{" + ph + "}")

new_src = src[:inner_start] + escaped + src[inner_end:]
p.write_text(new_src, encoding="utf-8")
print("Done. All CSS braces escaped.")
