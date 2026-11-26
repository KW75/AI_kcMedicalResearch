OCR PIPELINE - HOW A READING IS MADE TRUSTWORTHY
================================================
Overview for readers. How to run the pipeline: Readme/flashcard-help.html.


1. What the OCR pipeline is for

The OCR pipeline turns documents into plain text that can be searched,
quoted and reused: PDFs, page images (photos, scans, screenshots), .txt
and .docx files. Each file becomes a text record. With one file the job
also writes a short SUMMARY. With several files you choose:
  - Papers: each file is its own paper, with its own record and SUMMARY.
  - Synopsis: one record per file plus one SYNOPSIS summarising all
    papers in the input folder.

The aim is a faithful copy of what is printed, not an interpretation. The
main risk with AI reading is a confident error: a number, sign or word
that looks right but is not on the page. The pipeline is built so that,
where it cannot be sure, it leaves a visible gap rather than a guess.


2. The guiding rule: use the AI as little as possible

The AI reads a page only where ordinary text extraction cannot. Each page
takes the safest route that works:

  Route A - clean text layer. Most PDFs made on a computer carry their
  text. It is copied directly. No AI is involved, so nothing can be
  invented.

  Route B - broken font. Some PDFs (often journal articles) store symbols
  such as +/-, <, >, = or the minus sign in fonts that do not convert to
  text. Letters and digits come through; each lost symbol is marked [?].
  The AI sees the page image and is asked to fill only the [?] marks.

  Route C - no text layer. Scans, photos and screenshots have no text to
  copy. The AI reads the whole page from the image.

.txt and .docx files are taken as text (Route A). Old .doc files are
refused; save them as .docx first.


3. Checks on Route B (broken-font PDFs)

Route B has the strongest protection, because the text layer is a fixed
reference that the AI's answer can be compared with.

3.1 Fill the gaps, nothing else
  Only lines that contain [?] go to the AI, a few at a time, together
  with the page image. Every other line is kept exactly as extracted.

3.2 Letters and digits must not change
  The AI's answer is compared with the original line. If a letter or
  digit differs, or the answer belongs to another line, the fill is
  refused and the [?] stays. A dash in a [?] position is read as a
  minus sign.

3.3 Fills must fit the hidden font codes
  Each lost symbol carries a hidden font code. A fill that does not fit
  those codes (for example one code turned into two different symbols)
  is refused.

3.4 Document-wide vote
  After all pages are read, fills are counted per font code across the
  whole document. When at least two fills agree, and they make up at
  least 80% of the fills for that code, that symbol is used for every [?]
  with that code. A symbol seen only once stays where it was read but is
  not copied elsewhere. Fills that disagree with the agreed symbol go
  back to [?].

3.5 What these checks cannot catch
  They prove that no letter or digit was changed. They cannot prove that
  a filled symbol is the right one. In an earlier test a small model
  filled "+/-" as "=" ("mean = SD") again and again, and the vote
  accepted it: a consistent error looks like agreement. Agreement is not
  proof. This is the main reason the default model was changed
  (section 5).


4. Route C (scans, photos, screenshots)

There is no text layer to compare with, so the checks in section 3 do not
apply. The result is only as good as the AI's reading. Known habits of
the current model:
  - It may guess text that is covered, cut off or blurred instead of
    marking it [?]. In a test, a label partly hidden by a hand was read
    two different ways on two pages of the same run.
  - It can drop small print, such as a note printed under a number.
  - A summary may place table values under the wrong column even when
    the full text has them right.
Treat Route C text as a draft to be checked, especially numbers, signs,
table headers and anything near a fold, finger, stamp or blur.

Route C is also the only route that reads a table's layout. Routes A and
B keep the PDF's text layer, where table columns are flattened into plain
text, and the writing and appraisal pipelines read PDFs the same way. For
a table whose numbers matter, take a screenshot of it, run it through
menu 8, use the record next to the paper and check its numbers against
the PDF.


5. Which AI model reads the pages

The pipeline runs locally (Ollama) by default, so documents stay on this
computer. The default vision model is qwen3-vl:30b-a3b-instruct, the same
model the SR pipeline uses. It is large (about 20 GB) and slow on a
computer without a suitable graphics card.

Why this model: in a side-by-side test (Session 48) on a broken-font
journal article and three images (two tables and a ranked list):
  - gemma4:e4b left most [?] marks unfilled (the fills it made were
    right), lost table headers so numbers were no longer tied to their
    column, and misread values (58.2 and 58 for 58.6 and 58.4).
  - qwen3-vl filled every [?] in the article correctly (+/-, minus
    signs, a table header) and read every hand-checked value right.

If qwen3-vl is not installed, the pipeline warns and uses a smaller
vision model (normally gemma4:e4b). Its results need more checking.

Cloud models (Qwen, OpenAI) can be used instead, but only after a warning
that page images and document text will leave this computer, and only
with your consent.


6. Reading the output

  - [?] means "this symbol could not be filled safely". It is an honest
    gap, not a fault. Look it up on the original page.
  - A WARNING line means a fill was refused or a check failed; the [?]
    was kept.
  - Each record names the model that read the pages.
  - The full text is the result. The summary or synopsis is an AI-written
    overview for orientation only: never take numbers from it.
  - Route A text has no invented content. Route B text is safe for
    letters and digits; check filled symbols where they matter (+/-, <,
    >, minus). Route C text must be checked against the original wherever
    a value matters.


7. Responsibility

The OCR pipeline reduces reading errors; it does not remove them. Before
a value from an OCR record is used in a review, a report or a
calculation, check it against the original page. This matters most for
numbers, signs, units and table layout.


8. Finance (option 3, several files)

With several files, option 3 reads invoices and receipts into one finance
table: date, particulars (the invoice header), category, currency, amount,
exchange rate, amount in the local currency, a subtotal per category and
the total. It is written as <header>_FINANCE.csv, .html, .docx and .pdf in
output/ocr/. The OCR text of each invoice and the AI's reply are kept in
reports/ocr/<header>/ for checking.

  - Each file is read as in Synopsis (routes A-C). The AI then returns the
    fields of each invoice as JSON; it does no arithmetic.
  - Exchange rates come only from input/ocr/finance_rates.csv, which you
    fill in: "local,HKD" names the currency of the totals, and a line such
    as "USD,7.80" means 1 USD = 7.80 HKD. If the file is missing, a
    template is written. Rates are never guessed and never looked up
    online.
  - The program converts and adds up with exact decimals, rounded half up
    to 2 places.
  - A row is shown but marked "not in total" when the amount is not found
    in the invoice text, there is no amount or currency, or the currency
    has no rate. Fix the rate file or check the invoice, then run again.
  - Categories: Travel, Accommodation, Meals, Conference/registration,
    Equipment, Software/subscriptions, Publication fees, Other. A category
    outside this list becomes Other, with a note.
  - The CSV has plain numbers (no thousands separators) and is UTF-8
    without a BOM; if Excel shows Chinese text wrongly, open it with
    Data > From Text/CSV and choose UTF-8.
  - Check every row against its invoice before using the totals: the AI
    can pick the wrong printed amount (for example a subtotal before tax),
    and that passes the "amount found in the text" check.
