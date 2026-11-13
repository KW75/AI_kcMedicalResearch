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
        """Session 39 (item 11c): second figure, studies grouped by control
        type (subgroups.subgroup_summary entries of kind 'subgroup').
        forest_plot.png (generate above) is unchanged. Studies are matched to
        groups by name. Returns the path, or None when there are no
        subgroups."""
        groups = [e for e in (subgroups or []) if e.get("kind") == "subgroup"]
        if not groups:
            return None
        df = ma_result["study_effects"]
        by_study = {str(r["study"]): r for _, r in df.iterrows()}
        is_log = effect_measure in ("OR", "RR")
        C_STUDY = "#1a4a8a"; C_SUB = "#e67e22"; C_POOL = "#c0392b"; C_TEXT = "#212529"
        w_max = float(df["weight_pct"].max()) if len(df) else 0.0
        max_w = w_max if w_max > 0 else 1.0
        n_lines = sum(len(g["studies"]) + 2 for g in groups) + 2
        fig, ax = plt.subplots(figsize=(11, max(4, n_lines * 0.45 + 2)))
        ax.axvline(x=1.0 if is_log else 0.0, color="#6c757d",
                   linewidth=1.0, linestyle="--", zorder=1)
        dy = 0.3; y = 0.0
        ticks, labels, headers = [], [], []
        for g in groups:
            headers.append(len(labels))
            ticks.append(y); labels.append(f"{g['label']} (k={g['k']})"); y -= 1
            for s in g["studies"]:
                r = by_study.get(str(s))
                if r is not None:
                    ms = 40 + 120 * (float(r["weight_pct"]) / max_w)
                    ax.plot([r["ci_lower"], r["ci_upper"]], [y, y],
                            color=C_STUDY, linewidth=1.2, zorder=2)
                    ax.scatter(r["effect_estimate"], y, s=ms, color=C_STUDY,
                               zorder=3, clip_on=False)
                ticks.append(y); labels.append(f"   {s}"); y -= 1
            res = g.get("result")
            if res:
                px, cl, ch = res["pooled_effect"], res["ci_lower"], res["ci_upper"]
                ax.add_patch(plt.Polygon([[cl, y], [px, y + dy], [ch, y], [px, y - dy]],
                                         closed=True, fc=C_SUB, ec=C_SUB, zorder=4))
                labels.append(f"   Subgroup {px:.2f} [{cl:.2f}, {ch:.2f}]")
            else:
                labels.append(f"   {g.get('note') or 'Not pooled.'}")
            ticks.append(y); y -= 1.5
        px, cl, ch = ma_result["pooled_effect"], ma_result["ci_lower"], ma_result["ci_upper"]
        ax.add_patch(plt.Polygon([[cl, y], [px, y + dy], [ch, y], [px, y - dy]],
                                 closed=True, fc=C_POOL, ec=C_POOL, zorder=4))
        headers.append(len(labels))
        ticks.append(y)
        labels.append(f"Overall {px:.2f} [{cl:.2f}, {ch:.2f}] (k={ma_result['k']})")
        ax.set_yticks(ticks)
        ax.set_yticklabels(labels, fontsize=8.5, color=C_TEXT)
        for i in headers:
            ax.get_yticklabels()[i].set_fontweight("bold")
        ax.set_ylim(y - 1, 1)
        if is_log: ax.set_xscale("log")
        ax.set_xlabel(effect_measure, fontsize=10, color=C_TEXT)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_title(f"Forest Plot by control type -- {effect_measure} "
                     f"(Random-Effects, exploratory)",
                     fontsize=11, fontweight="bold", color=C_TEXT, pad=10)
        ax.text(0.5, -0.08,
                "Exploratory: groups with fewer than 3 studies are unreliable. "
                "Squares sized by weight in the overall analysis.",
                transform=ax.transAxes, ha="center", fontsize=7.5,
                color="#555555", style="italic")
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        plt.tight_layout()
        out = Path(output_path); out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(out), dpi=180, bbox_inches="tight", facecolor="white")
        plt.close(fig); return str(out)
