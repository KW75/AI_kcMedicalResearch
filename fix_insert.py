from pathlib import Path

func_text = '''

def run_sr_launcher() -> None:
    """Print SR pipeline launch instructions."""
    sr_dir = Path(__file__).resolve().parent.parent / "sr"
    print("\\n" + "="*58)
    print("  SR Automation Pipeline")
    print("  PRISMA 2020  |  Cochrane Handbook v6.5")
    print("="*58)
    print(f"\\n  Location : {sr_dir}")
    print("\\n  Before running:")
    print("    1. Edit  sr\\\\config\\\\prisma_criteria.yaml  (PICO + criteria)")
    print("    2. Place PDF articles in  sr\\\\data\\\\uploads\\\\")
    print("    3. Set ANTHROPIC_API_KEY in your environment")
    print("\\n  Run the pipeline:")
    print("    cd D:\\\\ai-automation-tool")
    print("    python sr\\\\main.py --pdf-dir sr\\\\data\\\\uploads")
    print("    python sr\\\\main.py --pdf-dir sr\\\\data\\\\uploads --effect-measure SMD")
    print("\\n  Outputs land in:")
    print("    sr\\\\data\\\\screened\\\\screening_log.csv")
    print("    sr\\\\data\\\\extracted\\\\extracted_data.csv")
    print("    sr\\\\data\\\\extracted\\\\rob2_assessment.csv")
    print("    sr\\\\data\\\\results\\\\meta_analysis_results.csv")
    print("    sr\\\\outputs\\\\figures\\\\forest_plot.png")
    print("    sr\\\\outputs\\\\reports\\\\systematic_review.html  (full record)")
    print("    sr\\\\outputs\\\\reports\\\\systematic_review.docx  (summary)")
    print("\\n  Full guide: docs\\\\flashcard-help.html")
    print("="*58 + "\\n")

'''

src = Path("D:/ai-automation-tool/src/main.py").read_text(encoding="utf-8")
marker = "def run_search_mode("
idx = src.index(marker)
new_src = src[:idx] + func_text + src[idx:]
Path("D:/ai-automation-tool/src/main.py").write_text(new_src, encoding="utf-8")
print("Done. run_sr_launcher inserted.")
