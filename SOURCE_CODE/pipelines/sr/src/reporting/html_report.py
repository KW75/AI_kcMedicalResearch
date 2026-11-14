import base64, datetime
from pathlib import Path
from .override_summary import override_changed_values, override_confirmed_only, study_label
from ..analysis.subgroups import subgroup_report_lines, SUBGROUP_INTRO


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>{title}</title>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:"Segoe UI",Arial,sans-serif;background:#f4f6f9;color:#1a1a2e;line-height:1.7}}
    .cover{{background:linear-gradient(135deg,#0f3460,#1a1a2e);color:#fff;padding:56px 64px 48px}}
    .cover h1{{font-size:2rem;font-weight:700;margin-bottom:12px;max-width:800px}}
    .cover .meta{{font-size:.85rem;opacity:.85;margin-top:16px}}
    .container{{max-width:1100px;margin:36px auto;padding:0 28px}}
    .section{{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.07);padding:32px 36px;margin-bottom:24px}}
    .sh{{display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:2px solid #f0f2f5}}
    .sh h2{{font-size:1.1rem;font-weight:700}}
    .sg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-bottom:24px}}
    .sc{{background:#f8fafc;border:1px solid #e5e9f0;border-radius:9px;padding:18px;text-align:center}}
    .sc .sv{{font-size:1.9rem;font-weight:800;color:#0f3460;line-height:1;margin-bottom:5px}}
    .sc .sl{{font-size:.72rem;color:#6b7280;text-transform:uppercase;letter-spacing:.7px}}
    .sc.h{{background:#0f3460;border-color:#0f3460}}.sc.h .sv{{color:#fff}}.sc.h .sl{{color:rgba(255,255,255,.7)}}
    .pg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
    .pi{{background:#f8fafc;border-left:4px solid #0f3460;border-radius:0 7px 7px 0;padding:12px 14px}}
    .pk{{font-size:.68rem;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;color:#0f3460;margin-bottom:3px}}
    .pv{{font-size:.83rem;color:#374151;line-height:1.4}}
    .tw{{overflow-x:auto;margin-top:6px}}
    table{{width:100%;border-collapse:collapse;font-size:.8rem}}
    thead tr{{background:#0f3460;color:#fff}}
    thead th{{padding:10px 12px;text-align:left;font-weight:600;white-space:nowrap}}
    tbody tr{{border-bottom:1px solid #f0f2f5}}
    tbody tr:hover{{background:#f8fafc}}
    tbody td{{padding:9px 12px;vertical-align:top;color:#374151}}
    /* Screening table column widths */
    .screening-filename {{ max-width: 160px; word-wrap: break-word; font-size: .76rem; }}
    .screening-rationale {{ max-width: 300px; word-wrap: break-word; font-size: .76rem; }}
    .screening-check {{ text-align: center; }}
    .bi{{display:inline-block;background:#d1fae5;color:#065f46;border-radius:5px;padding:2px 9px;font-size:.73rem;font-weight:700}}
    .bx{{display:inline-block;background:#fee2e2;color:#991b1b;border-radius:5px;padding:2px 9px;font-size:.73rem;font-weight:700}}
    .bu{{display:inline-block;background:#fef3c7;color:#92400e;border-radius:5px;padding:2px 9px;font-size:.73rem;font-weight:700}}
    .rl{{background:#d1fae5;color:#065f46;border-radius:4px;padding:2px 6px;font-size:.7rem;font-weight:700}}
    .rs{{background:#fef3c7;color:#92400e;border-radius:4px;padding:2px 6px;font-size:.7rem;font-weight:700}}
    .rh{{background:#fee2e2;color:#991b1b;border-radius:4px;padding:2px 6px;font-size:.7rem;font-weight:700}}
    .fw{{text-align:center;background:#f8fafc;border:1px solid #e5e9f0;border-radius:9px;padding:20px}}
    .fw img{{max-width:100%;height:auto;border-radius:5px}}
    .rb2{{background:linear-gradient(135deg,#0f3460,#1a4a8a);color:#fff;border-radius:9px;padding:22px 26px;margin-bottom:18px}}
    .rm{{font-size:1.4rem;font-weight:800;margin-bottom:5px}}
    .hg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-top:14px}}
    .hc{{background:#f8fafc;border:1px solid #e5e9f0;border-radius:7px;padding:12px;text-align:center}}
    .hv{{font-size:1.25rem;font-weight:700;color:#0f3460}}
    .hl{{font-size:.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:.6px}}
    .wb{{background:#fff7ed;border:1px solid #fed7aa;border-left:4px solid #f97316;border-radius:7px;padding:12px 16px;font-size:.81rem;color:#7c2d12;margin-bottom:18px}}
    .footer{{text-align:center;padding:28px;font-size:.76rem;color:#9ca3af}}
  </style>
</head>
<body>
<div class="cover">
  <h1>{title}</h1>
  {authors_html}
  <div class="meta">Generated: {generated_date} &middot; PRISMA 2020 &middot; Model: {model_name} &middot; Effect: {effect_measure}</div>
</div>
<div class="container">
  <div class="wb">&#9888; <strong>Research Accelerator.</strong> Verify all extracted values against source PDFs before submission.</div>
  <div class="section" id="ov">
    <div class="sh"><h2>Pipeline Overview</h2></div>
    <div class="sg">
      <div class="sc"><div class="sv">{n_uploaded}</div><div class="sl">PDFs Uploaded</div></div>
      <div class="sc"><div class="sv">{n_included}</div><div class="sl">Included</div></div>
      <div class="sc"><div class="sv">{n_excluded}</div><div class="sl">Excluded</div></div>
      <div class="sc"><div class="sv">{n_uncertain}</div><div class="sl">Uncertain</div></div>
      <div class="sc h"><div class="sv">{k_studies}</div><div class="sl">In Meta-Analysis</div></div>
      <div class="sc h"><div class="sv">{pooled_display}</div><div class="sl">Pooled {effect_measure}</div></div>
    </div>
  </div>
  <div class="section" id="pico">
    <div class="sh"><h2>PICO Framework</h2></div>
    <div class="pg">{pico_html}</div>{criteria_html}
  </div>
  <div class="section" id="sc2">
    <div class="sh"><h2>Screening Log</h2></div>
    <div class="tw"><table><thead><tr><th>#</th><th>Filename</th><th>Decision</th><th>Confidence</th><th>RCT</th><th>P</th><th>I</th><th>C</th><th>O</th><th>Rationale</th></tr></thead><tbody>{screening_rows}</tbody></table></div>
  </div>
  <div class="section" id="ex">
    <div class="sh"><h2>Data Extraction</h2></div>
    <div class="tw"><table><thead><tr><th>Study</th><th>Country</th><th>N Int.</th><th>N Con.</th><th>Intervention</th><th>Comparator</th><th>Outcome</th><th>Effect</th><th>95% CI</th><th>p</th><th>DOI</th></tr></thead><tbody>{extraction_rows}</tbody></table></div>
    {overrides_html}
  </div>
  <div class="section" id="rob">
    <div class="sh"><h2>Risk of Bias &mdash; Cochrane RoB 2.0</h2></div>
    <div class="tw"><table><thead><tr><th>Study</th><th>D1 Randomisation</th><th>D2 Deviations</th><th>D3 Missing Data</th><th>D4 Outcome</th><th>D5 Reported Result</th><th>Overall</th></tr></thead><tbody>{rob_rows}</tbody></table></div>
  </div>
  <div class="section" id="ma">
    <div class="sh"><h2>Meta-Analysis Results</h2></div>
    <div class="rb2">
      <div class="rm">Pooled {effect_measure} = {pooled_display} (95% CI: {ci_lower_display} &ndash; {ci_upper_display})</div>
      <div>k = {k_studies} studies &middot; z = {z_display} &middot; p = {p_display}</div>
    </div>
    <div class="hg">
      <div class="hc"><div class="hv">{i2_display}%</div><div class="hl">I&#178; Heterogeneity</div></div>
      <div class="hc"><div class="hv">{tau2_display}</div><div class="hl">&#964;&#178;</div></div>
      <div class="hc"><div class="hv">{q_display}</div><div class="hl">Cochran Q</div></div>
      <div class="hc"><div class="hv">{q_p_display}</div><div class="hl">Q p-value</div></div>
    </div>
    {not_pooled_html}
    {subgroups_html}
  </div>
  <div class="section" id="fp">
    <div class="sh"><h2>Forest Plot</h2></div>
    {forest_plot_html}
  </div>
</div>
<div class="footer">SR Automation Pipeline &middot; PRISMA 2020 &middot; {generated_date} &middot; All outputs require human verification.</div>
</body></html>"""

# Session 38 (7n e): wording for the not-pooled table in the report.
# Statistical reasons stay verbatim (exact for technical readers); only
# pipeline-internal text (file paths, flag names, code syntax) is reworded.
# The CSV and console keep the raw skip_reason.
_FIELD_WORDS = {
    "mean_intervention": "intervention mean",
    "sd_intervention": "intervention SD",
    "mean_control": "control mean",
    "sd_control": "control SD",
    "n_intervention": "intervention N",
    "n_control": "control N",
}


def _plain_one(part):
    part = part.strip()
    if part.startswith("outcome_match=False:"):
        return ("Outcome does not match the review outcome: "
                + part[len("outcome_match=False:"):].strip())
    if part.startswith("needs review"):
        head = "needs review: runs disagree ("
        flags = part[len(head):].split(")", 1)[0] if part.startswith(head) else ""
        fields, shift = [], False
        for tok in (t.strip() for t in flags.split("|")):
            if tok == "table_shift":
                shift = True
            elif tok.endswith(":no_majority"):
                f = tok.split(":", 1)[0]
                fields.append(_FIELD_WORDS.get(f, f.replace("_", " ")))
        bits = []
        if fields:
            bits.append("the AI read different values on repeated readings ("
                        + ", ".join(fields) + ")")
        if shift:
            bits.append("one of the repeated readings took a neighbouring table row")
        if not bits:
            bits.append("the AI read different values on repeated readings")
        text = "; ".join(bits)
        return text[0].upper() + text[1:] + ". Not confirmed by a reviewer."
    return part


def plain_skip_reason(reason):
    """Report wording for a skip_reason (see comment above)."""
    s = str(reason or "").strip()
    if not s:
        return "no reason recorded"
    if s.startswith("excluded by reviewer:"):
        return "Excluded by the reviewer: " + s[len("excluded by reviewer:"):].strip()
    return " Also: ".join(_plain_one(p) for p in s.split("; also: "))

def _override_changed_values(override_fields) -> bool:
    """Session 39 (item 4c): True if StudyOverrides.apply recorded a changed
    value ("field(old->new)" or "field(absent->v)")."""
    return "->" in str(override_fields or "")


def _override_confirmed_only(override_fields) -> bool:
    """True if the reviewer only confirmed values ("field(confirmed v)")."""
    s = str(override_fields or "")
    return "(confirmed " in s and "->" not in s

class HTMLReportGenerator:
    def generate(self, title, authors, pico, inclusion_criteria, exclusion_criteria,
                 ma_result, extraction_results, screening_results, rob_results,
                 forest_plot_path, effect_measure="OR", model_name="claude-opus-4-7",
                 output_path="outputs/reports/systematic_review.html", meta_audit=None, subgroups=None, subgroup_plot_path=None) -> str:
        out = Path(output_path); out.parent.mkdir(parents=True, exist_ok=True)
        html = HTML_TEMPLATE.format(
            title=self._e(title),
            authors_html=f'<p style="margin-top:10px;opacity:.9;">{self._e(authors)}</p>' if authors else "",
            generated_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            model_name=model_name, effect_measure=effect_measure,
            n_uploaded=len(screening_results),
            n_included=sum(1 for s in screening_results if s.get("decision")=="INCLUDE"),
            n_excluded=sum(1 for s in screening_results if s.get("decision")=="EXCLUDE"),
            n_uncertain=sum(1 for s in screening_results if s.get("decision")=="UNCERTAIN"),
            k_studies=ma_result.get("k","--"),
            pooled_display=f"{ma_result.get('pooled_effect',0):.3f}",
            pico_html=self._pico_html(pico),
            criteria_html=self._criteria_html(inclusion_criteria,exclusion_criteria),
            screening_rows=self._screening_rows(screening_results),
            extraction_rows=self._extraction_rows(extraction_results),
            overrides_html=self._overrides_html(extraction_results),
            not_pooled_html=self._not_pooled_html(meta_audit),
            subgroups_html=self._subgroups_html(subgroups, effect_measure, subgroup_plot_path),
            rob_rows=self._rob_rows(rob_results or []),
            ci_lower_display=f"{ma_result.get('ci_lower',0):.3f}",
            ci_upper_display=f"{ma_result.get('ci_upper',0):.3f}",
            z_display=f"{ma_result.get('z_score',0):.3f}",
            p_display=f"{ma_result.get('p_value',0):.4f}",
            i2_display=f"{ma_result.get('I2',0):.1f}",
            tau2_display=f"{ma_result.get('tau2',0):.4f}",
            q_display=f"{ma_result.get('Q',0):.2f}",
            q_p_display=f"{ma_result.get('Q_p',0):.3f}",
            forest_plot_html=self._forest_html(forest_plot_path),
        )
        out.write_text(html, encoding="utf-8"); return str(out.resolve())

    @staticmethod
    def _e(t): return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

    def _pico_html(self,pico):
        L={"population":"P  Population","intervention":"I  Intervention",
           "comparator":"C  Comparator","outcome":"O  Outcome","study_design":"S  Study Design"}
        return "\n".join(f'<div class="pi"><div class="pk">{L.get(k,k)}</div><div class="pv">{self._e(str(v))}</div></div>'
                         for k,v in pico.items())

    def _criteria_html(self,inc,exc):
        if not inc and not exc: return ""
        def ul(items): return "<ul style='list-style:none;padding:0;'>"+"".join(
            f"<li style='padding:4px 0;font-size:.81rem;'>&#10003; {self._e(str(i))}</li>" for i in items)+"</ul>"
        return (f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px;">'
                f'<div><h4 style="font-size:.77rem;color:#065f46;margin-bottom:6px;">Inclusion</h4>{ul(inc)}</div>'
                f'<div><h4 style="font-size:.77rem;color:#991b1b;margin-bottom:6px;">Exclusion</h4>{ul(exc)}</div></div>')

    def _screening_rows(self, results):
        """Generate screening rows with truncated filename and proper column widths."""
        rows = []
        for i, r in enumerate(results, 1):
            d = r.get("decision", "--")
            bc = {"INCLUDE": "bi", "EXCLUDE": "bx"}.get(d, "bu")
            pm = r.get("pico_match", {})
            
            def f(v):
                return "&#10003;" if v is True else ("&#10007;" if v is False else "--")
            
            # Truncate filename to 35 characters with tooltip
            filename = r.get('filename', '')
            if len(filename) > 35:
                filename_display = filename[:32] + "..."
            else:
                filename_display = filename
            
            rows.append(
                f"<tr><td>{i}</td>"
                f"<td class='screening-filename' title='{self._e(filename)}'>{self._e(filename_display)}</td>"
                f"<td><span class='{bc}'>{d}</span></td>"
                f"<td>{r.get('confidence', 0):.2f}</td>"
                f"<td class='screening-check'>{f(r.get('is_rct'))}</td>"
                f"<td class='screening-check'>{f(pm.get('population'))}</td>"
                f"<td class='screening-check'>{f(pm.get('intervention'))}</td>"
                f"<td class='screening-check'>{f(pm.get('comparator'))}</td>"
                f"<td class='screening-check'>{f(pm.get('outcome'))}</td>"
                f"<td class='screening-rationale'>{self._e(r.get('rationale', ''))}</td>"
                f"</tr>"
            )
        return "\n".join(rows)

    def _extraction_rows(self,results):
        rows=[]
        for r in results:
            m=r.get("study_metadata",{}); pt=r.get("participants",{})
            iv=r.get("intervention",{}); co=r.get("comparator",{}); po=r.get("primary_outcome",{})
            study=f"{m.get('first_author','?')} ({m.get('year','')})"
            doi=m.get("doi","")
            doi_h=(f'<a href="https://doi.org/{self._e(doi)}" target="_blank" style="color:#0f3460;">'
                   f'{self._e(doi)}</a>') if doi else "--"
            ci=(f"[{po.get('ci_lower_95','?')}, {po.get('ci_upper_95','?')}]"
                if po.get("ci_lower_95") else "--")
            rows.append(f"<tr><td><strong>{self._e(study)}</strong></td>"
                        f"<td>{self._e(str(m.get('country','--')))}</td>"
                        f"<td>{pt.get('n_intervention','--')}</td><td>{pt.get('n_control','--')}</td>"
                        f"<td style='font-size:.78rem;'>{self._e(str(iv.get('name','--')))}</td>"
                        f"<td style='font-size:.78rem;'>{self._e(str(co.get('name','--')))}</td>"
                        f"<td style='font-size:.78rem;'>{self._e(str(po.get('name','--')))}</td>"
                        f"<td>{po.get('effect_estimate','--')}</td><td>{self._e(ci)}</td>"
                        f"<td>{po.get('p_value','--')}</td><td>{doi_h}</td></tr>")
        return "\n".join(rows)

    def _overrides_html(self, results):
        """Session 37: list studies whose values were entered by a reviewer.
        Session 39 (item 4c): count only entries that changed a value; exclude-only
        entries (Ang) are in the not-pooled section; confirm-only entries are named
        separately."""
        rows = [r for r in (results or []) if isinstance(r, dict)]
        ov = [r for r in rows if override_changed_values(r.get("override_fields"))]
        conf = [r for r in rows if override_confirmed_only(r.get("override_fields"))]
        if not ov and not conf:
            return ""
        html = "<div class='wb' style='margin-top:14px;'><strong>Reviewer-entered data.</strong> "
        if ov:
            items = []
            for r in ov:
                note = f" {self._e(r['override_note'])}" if r.get("override_note") else ""
                fields = (f" <span style='color:#6b7280;'>Fields: {self._e(r['override_fields'])}</span>"
                          if r.get("override_fields") else "")
                items.append(f"<li><strong>{self._e(study_label(r))}</strong>:{note}{fields}</li>")
            html += (f"{len(ov)} of {len(results)} extracted studies use values entered by a reviewer "
                     "from the source PDF (input/sr/study_overrides.yaml), not values extracted by the model. "
                     "Report them as manually extracted.<ul style='margin:6px 0 0 18px;'>"
                     + "".join(items) + "</ul>")
        if conf:
            html += ("<p style='margin:6px 0 0 0;'>Checked by a reviewer against the PDF, values "
                     "unchanged (confirmed): " + self._e(", ".join(study_label(r) for r in conf)) + ".</p>")
        return html + "</div>"

    def _subgroups_html(self, subgroups, effect_measure, plot_path=None):
        # Session 39 (item 11): same rows as the Word report
        # (subgroups.subgroup_report_lines). No subgroups -> no section.
        lines = subgroup_report_lines(subgroups, effect_measure)
        if not lines:
            return ""
        body = "".join(
            f"<tr><td>{self._e(g)}</td><td>{self._e(s)}</td>"
            f"<td>{self._e(est) or '-'}</td><td>{self._e(n)}</td></tr>"
            for g, s, est, n in lines)
        img = ""
        if plot_path and Path(plot_path).exists():
            import base64
            b64 = base64.b64encode(Path(plot_path).read_bytes()).decode("ascii")
            img = (f'<p><img src="data:image/png;base64,{b64}" '
                   f'alt="Forest plot: all pooled studies and excluding waiting-list trials" style="max-width:100%;"></p>'
                   f"<p><em>Figure 2. Forest plot: all pooled studies and excluding "
                   f"waiting-list trials (sensitivity analysis).</em></p>")
        return (f"<h3>Subgroups by control type</h3>"
                f"<p>{self._e(SUBGROUP_INTRO)}</p>"
                f"<table><thead><tr><th>Group</th><th>Studies</th>"
                f"<th>Estimate</th><th>Note</th></tr></thead>"
                f"<tbody>{body}</tbody></table>" + img)


    def _not_pooled_html(self, meta_audit):
        """Session 38 (7k): every study left out of the pooled estimate, with its
        reason (PRISMA 2020 item 13a). Reviewer decision vs automatic skip."""
        rows = [r for r in (meta_audit or []) if isinstance(r, dict)]
        if not rows:
            return ""
        out = [r for r in rows if not r.get("included_in_meta")]
        head = ("<div class='wb' style='margin-top:14px;'><strong>Studies included in the review "
                f"but not in the meta-analysis.</strong> {len(rows) - len(out)} of {len(rows)} studies pooled.")
        if not out:
            return head + " None left out.</div>"
        items = []
        for r in out:
            reason = str(r.get("skip_reason") or "no reason recorded")
            who = "Reviewer" if reason.startswith("excluded by reviewer") else "Automatic"
            label = f"{r.get('first_author') or r.get('filename', '?')} ({r.get('year', '')})"
            items.append(f"<tr><td>{self._e(label)}</td><td>{self._e(plain_skip_reason(reason))}</td><td>{who}</td></tr>")
        return (head + "<table style='margin-top:6px;'><thead><tr><th>Study</th><th>Reason</th>"
                "<th>Decided by</th></tr></thead><tbody>" + "".join(items) + "</tbody></table></div>")

    def _rob_rows(self,results):
        if not results:
            return "<tr><td colspan='7' style='text-align:center;color:#9ca3af;padding:18px;'>RoB 2.0 not available</td></tr>"
        def c(j):
            j2=str(j).lower()
            if "low"  in j2: return f'<td><span class="rl">Low</span></td>'
            if "some" in j2: return f'<td><span class="rs">Some Concerns</span></td>'
            if "high" in j2: return f'<td><span class="rh">High</span></td>'
            if "not assessed" in j2: return '<td><span style="color:#6b7280;font-style:italic">Not assessed</span></td>'
            return "<td>--</td>"
        rows=[]
        for r in results:
            d=r.get("domains",{})
            rows.append(f"<tr><td><strong>{self._e(str(r.get('study',r.get('filename','?'))))}</strong></td>"
                        +c(d.get("randomisation","--"))+c(d.get("deviations","--"))
                        +c(d.get("missing_data","--"))+c(d.get("outcome_measurement","--"))
                        +c(d.get("reported_result","--"))+c(r.get("overall_judgment","--"))+"</tr>")
        return "\n".join(rows)

    def _forest_html(self,path):
        if not path or not Path(path).exists():
            return '<div class="fw" style="color:#9ca3af;padding:36px;">Forest plot not available.</div>'
        b64=base64.b64encode(Path(path).read_bytes()).decode("ascii")
        return (f'<div class="fw"><img src="data:image/png;base64,{b64}" alt="Forest Plot"/>'
                f'<div style="margin-top:10px;font-size:.76rem;color:#6b7280;font-style:italic;">'
                f'Figure 1. Squares = study estimates (sized by weight); lines = 95% CI; diamond = pooled estimate.</div></div>')