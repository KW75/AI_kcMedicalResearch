import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

class ForestPlotGenerator:
    def generate(self, ma_result, effect_measure="OR",
                 output_path="outputs/figures/forest_plot.png", title="") -> str:
        df      = ma_result["study_effects"].copy()
        k       = ma_result["k"]
        is_log  = effect_measure in ("OR","RR")
        C_STUDY = "#1a4a8a"; C_POOL="#c0392b"; C_LINE="#dee2e6"; C_TEXT="#212529"

        fig, ax = plt.subplots(figsize=(11, max(4, k*0.55+3)))
        for i in range(k):
            ax.axhline(y=i, color=C_LINE, linewidth=0.5, zorder=0)
        ax.axvline(x=1.0 if is_log else 0.0, color="#6c757d",
                   linewidth=1.0, linestyle="--", zorder=1)

        weights   = df["weight_pct"].values
        max_w     = weights.max() if weights.max()>0 else 1.0
        estimates = df["effect_estimate"].values
        ci_lowers = df["ci_lower"].values
        ci_uppers = df["ci_upper"].values
        studies   = df["study"].values

        for i in range(k):
            ms = 40+120*(weights[i]/max_w)
            ax.plot([ci_lowers[i],ci_uppers[i]],[i,i],color=C_STUDY,linewidth=1.2,zorder=2)
            ax.scatter(estimates[i],i,s=ms,color=C_STUDY,zorder=3,clip_on=False)

        dy=0.35; px=ma_result["pooled_effect"]
        cl=ma_result["ci_lower"]; ch=ma_result["ci_upper"]; py=-1.3
        ax.add_patch(plt.Polygon([[cl,py],[px,py+dy],[ch,py],[px,py-dy]],
                                  closed=True,fc=C_POOL,ec=C_POOL,zorder=4))

        ax.set_yticks(range(k)); ax.set_yticklabels(studies,fontsize=9,color=C_TEXT)
        ax.set_ylim(-2.2,k-0.3)
        if is_log: ax.set_xscale("log")
        ax.set_xlabel(effect_measure,fontsize=10,color=C_TEXT)
        ax.tick_params(axis="x",labelsize=8)
        ax.set_title(title or f"Forest Plot -- {effect_measure} (Random-Effects)",
                     fontsize=11,fontweight="bold",color=C_TEXT,pad=10)
        footer=(f"Pooled {effect_measure}={px:.3f} [{cl:.3f},{ch:.3f}]  "
                f"I\u00b2={ma_result['I2']:.1f}%  \u03c4\u00b2={ma_result['tau2']:.4f}  "
                f"Q={ma_result['Q']:.2f}(p={ma_result['Q_p']:.3f})  k={k}")
        ax.text(0.5,-0.12,footer,transform=ax.transAxes,ha="center",
                fontsize=7.5,color="#555555",style="italic")
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        plt.tight_layout()
        out=Path(output_path); out.parent.mkdir(parents=True,exist_ok=True)
        fig.savefig(str(out),dpi=180,bbox_inches="tight",facecolor="white")
        plt.close(fig); return str(out)

    def generate_subgroups(self, ma_result, subgroups, effect_measure="OR",
                           output_path="outputs/figures/forest_plot_subgroups.png"):
        """Session 40: second figure, two panels (see build_panels below).
        Top: all pooled studies and the overall estimate. Bottom: the same
        studies in the same order, with waiting-list trials taken off; a
        study whose only control is a wait-list stays as a grey row with no
        effect (its control is never set to 0). forest_plot.png (generate
        above) is unchanged. Returns the path, or None when there is no
        excluding-waiting-list entry."""
        panels = build_panels(ma_result, subgroups)
        if len(panels) < 2:
            return None
        is_log = effect_measure in ("OR", "RR")
        C_STUDY = "#1a4a8a"; C_OFF = "#8a9199"; C_SUB = "#e67e22"
        C_POOL = "#c0392b"; C_TEXT = "#212529"
        weights = [float(r["weight_pct"]) for r in panels[0]["rows"]]
        max_w = max(weights) if weights and max(weights) > 0 else 1.0
        n_lines = sum(len(p["rows"]) + 2 for p in panels) + 2
        fig, ax = plt.subplots(figsize=(11, max(4, n_lines * 0.45 + 2)))
        ax.axvline(x=1.0 if is_log else 0.0, color="#6c757d",
                   linewidth=1.0, linestyle="--", zorder=1)
        dy = 0.3; y = 0.0
        ticks, labels, headers, greyed = [], [], [], []
        for i, p in enumerate(panels):
            headers.append(len(labels))
            ticks.append(y); labels.append(f"{p['label']} (k={p['k']})"); y -= 1
            for r in p["rows"]:
                if r["included"] and r["effect_estimate"] is not None:
                    ms = 40 + 120 * (float(r["weight_pct"]) / max_w)
                    ax.plot([r["ci_lower"], r["ci_upper"]], [y, y],
                            color=C_STUDY, linewidth=1.2, zorder=2)
                    ax.scatter(r["effect_estimate"], y, s=ms, color=C_STUDY,
                               zorder=3, clip_on=False)
                    labels.append(f"   {r['study']}")
                else:
                    greyed.append(len(labels))
                    labels.append(f"   {r['study']} - {r['note']}")
                ticks.append(y); y -= 1
            res = p.get("result")
            if res:
                px, cl, ch = res["pooled_effect"], res["ci_lower"], res["ci_upper"]
                colour = C_POOL if i == 0 else C_SUB
                ax.add_patch(plt.Polygon([[cl, y], [px, y + dy], [ch, y], [px, y - dy]],
                                         closed=True, fc=colour, ec=colour, zorder=4))
                name = "Overall" if i == 0 else "Pooled"
                labels.append(f"   {name} {px:.2f} [{cl:.2f}, {ch:.2f}]")
            else:
                labels.append(f"   {p.get('note') or 'Not pooled.'}")
            ticks.append(y); y -= 1.5
        ax.set_yticks(ticks)
        ax.set_yticklabels(labels, fontsize=8.5, color=C_TEXT)
        tl = ax.get_yticklabels()
        for i in headers:
            tl[i].set_fontweight("bold")
        for i in greyed:
            tl[i].set_color(C_OFF)
        ax.set_ylim(y + 0.5, 1)
        if is_log: ax.set_xscale("log")
        ax.set_xlabel(effect_measure, fontsize=10, color=C_TEXT)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_title(f"Forest Plot -- all pooled studies and excluding "
                     f"waiting-list trials -- {effect_measure} (Random-Effects)",
                     fontsize=11, fontweight="bold", color=C_TEXT, pad=10)
        ax.text(0.5, -0.08,
                "Sensitivity analysis. A trial whose only control is a wait-list "
                "has no other comparator, so it is listed but not in the lower "
                "estimate. Squares sized by weight in the overall analysis.",
                transform=ax.transAxes, ha="center", fontsize=7.5,
                color="#555555", style="italic")
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        plt.tight_layout()
        out = Path(output_path); out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(out), dpi=180, bbox_inches="tight", facecolor="white")
        plt.close(fig); return str(out)


def build_panels(ma_result, subgroups):
    """Session 40: what the two-panel figure shows; draws nothing.

    subgroups: entries from analysis.subgroups.subgroup_summary.
    Returns [] when there are no entries, [top] when there is no
    excluding-waiting-list entry, else [top, bottom]. Each panel:
    label, k, rows, result (None = not pooled), note. Each row: study,
    effect_estimate, ci_lower, ci_upper, weight_pct, included, note.

    Top = every pooled study with the overall estimate. Bottom = the same
    studies in the same order; a study not in the excluding-waiting-list
    entry keeps its row with no effect (None, never 0) and a note saying
    why. Its pooled result is the sensitivity entry's result."""
    entries = list(subgroups or [])
    if not entries:
        return []
    ctype = {}
    for e in entries:
        if e.get("kind") == "subgroup":
            for s in e.get("studies", []):
                ctype[str(s)] = e.get("key")
    sens = next((e for e in entries if e.get("kind") == "sensitivity"), None)
    base = []
    for _, r in ma_result["study_effects"].iterrows():
        base.append({"study": str(r["study"]),
                     "effect_estimate": float(r["effect_estimate"]),
                     "ci_lower": float(r["ci_lower"]),
                     "ci_upper": float(r["ci_upper"]),
                     "weight_pct": float(r["weight_pct"]),
                     "included": True, "note": ""})
    top = {"label": "All pooled studies", "k": ma_result["k"], "rows": base,
           "result": {"pooled_effect": ma_result["pooled_effect"],
                      "ci_lower": ma_result["ci_lower"],
                      "ci_upper": ma_result["ci_upper"]},
           "note": ""}
    if sens is None:
        return [top]
    keep = {str(s) for s in sens.get("studies", [])}
    rows = []
    for r in base:
        b = dict(r)
        if r["study"] not in keep:
            b.update(effect_estimate=None, ci_lower=None, ci_upper=None,
                     included=False)
            if ctype.get(r["study"]) == "waiting_list":
                b["note"] = "wait-list control only - not in this estimate"
            else:
                b["note"] = "control type unknown - not in this estimate"
        rows.append(b)
    bottom = {"label": sens.get("label") or "Excluding waiting-list trials",
              "k": sens.get("k", len(keep)), "rows": rows,
              "result": sens.get("result"), "note": sens.get("note", "")}
    return [top, bottom]
