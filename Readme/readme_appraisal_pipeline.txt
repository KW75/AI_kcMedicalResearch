README - APPRAISAL PIPELINE (menu 3, --mode appraisal)
How a critical appraisal is produced, and what keeps it valid

This file explains how the appraisal pipeline works, in general terms.
How to run it step by step is in flashcard-help.html and README.md.


1. What the appraisal pipeline is for

It writes a structured critical appraisal of each research article you
place in input/appraisal/: how the study was designed and run, how far
its results can be trusted, and what they mean in practice. Each article
gets its own report. The report is a draft to support a human appraiser,
not a replacement for one.


2. How a run goes

  - Every readable file in input/appraisal/ is one article: PDF, Word
    (.docx), Markdown (.md) or plain text (.txt). Old Word .doc files are
    not read; save them as .docx first.
  - Before the run you may type direct instructions (for example "focus
    on blinding"). Every line you type is treated as highest priority
    and applies to every article in the run.
  - For each article the AI receives one request with three parts: the
    appraisal guidelines, your instructions and the whole article text.
    There is one AI call per article, so one article cannot influence
    the report on another.
  - The guidelines ask for a fixed 7-section report, a plain-language
    summary of at most 200 words and an AI disclosure statement at the
    end.
  - Each report is saved as .md and .docx. A short process log and a
    session summary are saved separately.


3. The guiding rule: the AI sees the whole article

An appraisal depends on details spread through a paper: randomisation
and blinding in the methods, dropouts in the results, funding and
conflicts of interest at the end. So the pipeline sends the complete
article text, not selected passages. It does not use search-based
retrieval (RAG), which returns only the passages closest to a question
and would miss most of these details.

This rule only works if the AI can hold the whole article at once, which
is why there is a size limit (section 5).


4. What the AI actually receives

The AI reads text, not pages. How good that text is depends on the file:
  - Word (.docx): paragraphs and tables, in document order. Each table
    row arrives as "cell | cell | cell".
  - PDF with a normal text layer: words and numbers are exact, but table
    columns are flattened into plain text and can mix. The AI may then
    attach a number to the wrong group.
  - PDF with a broken symbol font (some older journal PDFs): symbols such
    as plus-minus, less-than and minus can be lost from the text layer,
    so "p < 0.05" may arrive as "p 0.05".
  - Scanned PDF or image: there is no text layer, so there is nothing
    for the AI to appraise.
For the last three cases, use the OCR pipeline (menu 8) first: the
scanned file itself, the broken-font PDF, or a screenshot of the table
that matters. Put the OCR record in input/appraisal/ next to, or instead
of, the original, and check its key numbers against the paper.


5. Size and the local AI

By default the AI runs locally (Ollama). A local model can hold only a
fixed amount of text per request (its context window), and the request
and the answer share it. If a request is too long, Ollama does not
refuse it: it silently drops the beginning, which is where the appraisal
guidelines are. The report would look normal but ignore the rules.

To prevent this, a local run skips any article longer than 80,000
characters, with a message naming it, and still appraises the others.
The last line of the run says how many were skipped. For a skipped
article, use a cloud provider or shorten the file (for example, remove
the reference list or appendices). Cloud providers have much larger
windows and are not limited, but the article is then sent to that
provider.


6. What is not checked

Unlike the SR pipeline, the appraisal pipeline has no automatic checks
on the AI's answer. In particular:
  - Quotes and numbers in the report are not compared with the article.
    The AI can misquote, round, or attach a number to the wrong group.
  - Each article is appraised once. There are no repeated runs to show
    where the AI is unsure.
  - Judgements (risk of bias, certainty of evidence, applicability) are
    the AI's reading of the text. They can be too lenient or too harsh,
    and an item the paper does not report may be treated as done.
  - The AI knows only the article and its own training. It does not look
    up trial registrations, protocols, corrections or later papers.
  - Direct instructions are followed with high priority, so a leading
    instruction ("show this trial is robust") can bias the report.
  - A smaller local model follows the 7-section structure and the word
    limit less reliably than a large one.


7. How to keep an appraisal valid

  - Give the AI a text it can read well (section 4); give tables that
    matter as an OCR record.
  - Keep instructions neutral: say what to examine, not what to conclude.
  - Check every number and quote you intend to use against the article.
  - Check each risk-of-bias judgement against the methods yourself; read
    the reasons given, not only the labels.
  - Look up the trial registration and protocol to judge selective
    reporting.
  - If a report is missing sections or seems to ignore the guidelines,
    check the run messages for a skipped or very long article and rerun.


8. Reading the output

  output/appraisal/   APPRAISAL_<article>_<YYYYMMDD_HHMMSS>.md and .docx
                      - the report.
  reports/appraisal/  a process log per article and a session summary.
The guidelines ask the AI to end every report with a statement that it
was produced by AI. Check that it is there, and keep it when the text is
shared or reused.


9. Responsibility

The appraisal is produced by an AI model and can contain errors. The
person using it is responsible for checking it against the original
article before relying on it, citing it or making decisions with it.
