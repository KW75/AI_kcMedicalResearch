==============================================================================
 AI_kcMedicalResearch - SaMD mode (clinical decision support)
 How it works, and why it was built this way
==============================================================================

This file explains the logic of SaMD mode: what happens to a patient's
documents from the moment they are chosen to the final report, which method
is used at each step, and why. It is not a user guide. To start a run: launcher
menu 9, or main.py --mode samd. The code is in SOURCE_CODE/pipelines/samd/
(cli.py = steps 1-4; report.py = lab table, answer checks, report files).
The product decision and the intended use are in docs/project/PRD.md
(SaMD Mode) and docs/project/decision-log.md (2026-11-20).

Contents
  1. What this mode is, and what it is not
  2. Design principles
  3. The pipeline, step by step
       3.1 Step 1: choose the files, add the doctor's notes
       3.2 Choosing the AI: local first
       3.3 Step 2: reading the sources
       3.4 Step 3: one reasoning call over the whole case
       3.5 Step 4: the lab results table, computed by the program
       3.6 How a result row is read and named
       3.7 Statuses
       3.8 Automatic checks on the AI answer
       3.9 Reports and audit trail
  4. Decisions: the user's, and the assistant's defaults
  5. Honest limitations
  Appendix A. Worked example: a urinalysis section



------------------------------------------------------------------------------
1. What this mode is, and what it is not
------------------------------------------------------------------------------

SaMD mode takes a patient's documents - photos of lab reports, lab report
PDFs, Word or text files, clinical photos - together with the doctor's own
notes, and returns an AI reasoning answer and a table of the lab results.

It is decision support for a clinician. It is not a cleared or certified
medical device, it does not diagnose, and its answer is not a medical
decision. The intended-use statement (INTENDED_USE in cli.py) is written at
the top of reasoning.md.

The main danger is the same as in the SR pipeline: a language model can
misread a number, or call an abnormal result normal, and the wrong sentence
reads as confidently as a right one. The mode is built around that danger.



------------------------------------------------------------------------------
2. Design principles
------------------------------------------------------------------------------

  - The program, not the AI, decides whether a lab result is in range. The
    status comes from the reference range printed on the lab report.
  - The AI answer is compared with that table and with the sources. A
    mismatch is shown as a warning; the program does not rewrite the answer.
  - Local first. Patient documents go to a local Ollama model by default; a
    cloud provider is used only after the cloud warning and an explicit yes.
  - No half answers. A failed or empty AI reply stops the job.
  - Every step leaves a file in reports/samd/<run_id>/, so a reviewer can see
    what the AI was given and what it said.
  - Few false alarms. Each warning rule is tested on made-up sentences and
    re-checked on a real run; a warning that fires on correct answers would
    teach the reader to ignore warnings.
  - The clinician decides. The checks catch some errors; they do not make the
    answer safe.



------------------------------------------------------------------------------
3. The pipeline, step by step
------------------------------------------------------------------------------

3.1 Step 1: choose the files, add the doctor's notes

list_inputs() lists the files in input/samd/ that the mode can read: images
(.jpg .jpeg .png .tif .tiff .bmp .gif .webp), .pdf, .docx and .txt.
choose_files(): Enter = all files; "1,3" = those files, in list order.
read_clinician_text() takes the doctor's lines until an empty line.
save_step1() writes clinician_input.txt, inputs.json and run.log in
reports/samd/<run_id>/ (run id YYYYMMDD_HHMMSS, the same shape as SR runs).

input/, reports/ and output/ are in .gitignore, so patient files and results
are never committed to the repository.


3.2 Choosing the AI: local first

choose_call() picks the AI call for the case. With Ollama, a pulled model
that can read images is needed; if none is pulled, a cloud provider is
offered and the user is asked once. With --provider qwen or openai, main.py
has already shown the cloud warning (where the data will go) and asked
first. Providers that cannot read images are refused for this mode.

Why: photos of patient documents are the most sensitive data the app
handles. Nothing switches from local to cloud without the user saying so.


3.3 Step 2: reading the sources

read_sources() reads every chosen file first, through the OCR reader. Text
layers (text PDFs, .docx, .txt) need no AI. If one file cannot be read, the
job stops. The case text is limited to what fits the model's context.

describe_sources() keeps text layers as they are and makes one AI call per
image page. A lab report is transcribed; a clinical photo is described
without a diagnosis. parse_image_reply() reads the reply's TYPE line and
labels the page 'transcription', 'photo description' or 'image (type not
stated)'. Each page is saved as step2_<nn>_<file>.txt, so the reading of
every page can be compared with the original image.


3.4 Step 3: one reasoning call over the whole case

build_case() joins the sources and the doctor's notes into case.md. One
reasoning call over the whole case gives reasoning.md. missing_headings()
checks that the answer has the headings the prompt asked for (HEADINGS in
cli.py); missing ones are reported.


3.5 Step 4: the lab results table, computed by the program

write_report_step() runs step 4. parse_results() reads result rows from
every transcription and text layer; photo descriptions are skipped. The
table never comes from the AI answer, so a misjudged status in the answer
cannot reach the table.


3.6 How a result row is read and named

Each line is tried in this order:

  1. parse_line(): name, value, unit and printed reference range.
  2. _parse_other(): rows the main pattern skips - text results (NEGATIVE,
     POSITIVE, TRACE, NIL, NOT SEEN, 1+ to 4+), count ranges (1-3 cell/HPF),
     numbers without a unit but with a printed range (pH 5.5 5.0 - 8.0) and
     'up to N' references. An up/down arrow is the lab's own H/L flag.
  3. _parse_descriptive(): urinalysis Colour / Clarity / Appearance rows,
     with a fixed list of upper-case words (YELLOW, STRAW, RED, TURBID ...).

Three extra rules fix rows a line-by-line reader would get wrong:

  - A value printed without a name ("6.9 U <9.0"): _parse_nameless() and
    _name_above() take the name from the nearest line above that has English
    letters, at most 2 lines up. A blank line, a table header, a report note
    or another result gives no name.
  - A result printed without a range but with a band table under it (HbA1c
    6.1 % with diabetes / prediabetes bands): _add_bands() uses the printed
    bands of its own column as the reference and marks the value in every
    band it falls in. Bands can overlap, so the program does not pick one.
  - Urine rows: _mark_urine() adds " - Urine" after the English name of a row
    whose unit is per field (/HPF, /LPF), or of any row inside the
    URINALYSIS section. The section starts at an upper-case "URINALYSIS" line
    and ends at "Released By", a page break or after 60 lines. The Chinese part of the
    name is kept; names that already say Urine are left alone.
    Why: one lab file can print "WBC" for blood (4.9 x10e9/L) and for urine
    (NIL cell/HPF). Without the mark, the table and the answer check could
    confuse the two.


3.7 Statuses

  HIGH / LOW   status(): the value is above / below a printed range "a - b"
               (both ends count as in range).
  ABNORMAL     a urine Colour or Clarity of RED, BROWN and TURBID.
  unclear      a "<x" or ">x" value that may lie on either side of the
               range, or a text value with no rule (see below).
  see bands    HbA1c-style band tables (3.6).
  normal       inside the printed range; or NEGATIVE / NIL / NOT SEEN.
  no range     nothing printed to compare with (including other colour
               words such as YELLOW).

_text_status() handles text values: NEGATIVE, NIL and NOT SEEN are normal
against any printed reference; TRACE is normal against 'up to trace' and
HIGH against 'negative'; 1+ to 4+ and POSITIVE are HIGH against either.

The table lists HIGH, LOW and ABNORMAL rows first, in bold, then unclear and
see bands, then normal, then no range (STATUS_ORDER in report.py), so the
results that need attention are at the top.


3.8 Automatic checks on the AI answer

check_answer() reads the answer sentence by sentence and warns in three
cases:

  1. An in-range result called abnormal. A normal row's number is cited as a
     value in a sentence that has an abnormal word and no "normal" /
     "within". _value_cited() does not count the end of a range ("3-6"), a
     time span ("6 months") or part of a longer number ("6.5").
  2. An out-of-range result (HIGH, LOW, ABNORMAL) called normal. The sentence
     names the row and says "normal" or "within". _row_named(): a number value
     cited as a value; for a text value (RED, 1+, TRACE) the first word of the
     test name and the value; for a urine row also the test word next to
     "urine" / "urinary" ("urine protein", "protein in the urine").
     Not warned when the sentence also has an abnormal word (elevated,
     raised, high, increased, low, decreased, reduced, abnormal, borderline,
     anaemia) or says "not normal" / "no longer normal".
     _claim_part() first removes exception clauses. A clause starts at
     apart from, aside from, other than, besides, save for, with the
     exception of, or except (for), and runs to the next comma or semicolon,
     else to the end of the sentence. So "normal apart from protein 1+" is not
     warned, but a normal claim outside the clause still is. The warning
     quotes the whole sentence.
  3. Numbers not in the sources. A number with a unit or % in the answer that
     appears nowhere in case.md (sources and doctor's notes). Time spans are
     skipped.

The warnings are printed in the report. They point the clinician at a
sentence to check; they do not prove the sentence wrong.


3.9 Reports and audit trail

reports/samd/<run_id>/ (the audit trail):
  clinician_input.txt, inputs.json, run.log   step 1
  step2_<nn>_<file>.txt                         step 2, one per page or file
  case.md, reasoning.md                         step 3
  results.json                                  step 4, the computed rows

output/samd/<run_id>/ (the report, written by write_report()):
  report.md
  report.html   md_to_html(): one self-contained page, all text escaped;
                opened in the browser by open_browser() (a local file, no
                server)
  report.docx   write_docx(); if the .docx fails, the other two are kept



------------------------------------------------------------------------------
4. Decisions: the user's, and the assistant's defaults
------------------------------------------------------------------------------

User decisions:
  - SaMD mode takes launcher menu 9 (decision-log, 2026-11-20).
  - Urine colour / clarity RED, BROWN and TURBID are ABNORMAL (Session 49).
    Every other colour word is 'no range'.

By design:
  - AI interpretation errors that the number checks cannot catch are left to
    the clinician.

Assistant defaults, not yet confirmed by the user:
  - Colour and Clarity rows in the URINALYSIS section are named "- Urine".
  - A value row without a name looks at most 2 lines up for one.
  - The URINALYSIS section ends after 60 lines when no "Released By" line
    is found.
  - The exception-clause words in 3.8, and a clause ending at the next comma
    or semicolon.



------------------------------------------------------------------------------
5. Honest limitations
------------------------------------------------------------------------------

  - The checks cover numbers and named lab rows only. An answer that reasons
    wrongly from correct numbers, misses a diagnosis or misreads a photo
    passes every check.
  - The checks are English word rules. An answer worded another way
    ("protein is fine") or written in another language is not checked.
  - The table is only as good as the step 2 transcription. If the model
    misreads a value on an image, the program computes a status for the
    wrong value. Compare the step2_*.txt files with the original images.
  - The row rules were built on one laboratory's report layout (three lab
    files with the same layout). Other layouts may give missing rows or wrong
    names. A row the parser does not read is simply absent from the table.
  - The program supplies no reference ranges of its own. No printed range
    means 'no range'.
  - For band tables (HbA1c) the program shows the bands; it does not choose.
  - Clinical photos are described by the AI; no rule checks the description.
  - Real-run evidence so far: run 20261120_170939 (three files: a clinical
    photo, a lab report PDF and a photographed lab report) gave 73 rows and
    0 answer warnings. The rules are tested in tests/test_*samd*.py.



------------------------------------------------------------------------------
Appendix A. Worked example: a urinalysis section
------------------------------------------------------------------------------

A made-up urinalysis section as it appears in a transcription (the lines
marked ">" are read by tests/test_s50_samd_readme.py, so this example stays
true to the code):

    > URINALYSIS 尿液常規檢驗
    > Colour 順色 RED -
    > Blood - Urine 潛血 2+ Up to trace
    > Protein - Urine 蛋白質 1+ ↑ Up to trace
    > Urine Released By: LAB STAFF on 14/NOV/2022 13:07

The program's table:

    Colour - Urine 順色      RED   ABNORMAL   colour word rule; named
                                              "- Urine" inside the section
    Blood - Urine 潛血       2+    HIGH       2+ against 'up to trace'
    Protein - Urine 蛋白質   1+    HIGH       1+ against 'up to trace'

Three answer sentences and what check_answer() does:

    "Urine protein is normal."
        warned: Protein - Urine 1+ (HIGH) is called normal; the urine row is
        named by "urine protein" without its value.
    "Urinalysis normal apart from protein 1+."
        not warned: protein is inside the exception clause.
    "Apart from protein 1+, urine blood is normal."
        warned: the clause ends at the comma; "urine blood is normal" calls
        Blood - Urine 2+ (HIGH) normal.
Session 51 changes (2026-11-27)
-------------------------------------------------------------
Urinalysis section (PR #101): rows after URINALYSIS are named "- Urine" until
"Released By", a page-break line ("--- page N (") or 60 lines, whichever comes
first. Known limit: a report that ends with another phrase (for example
"Signed") can still name a blood row "- Urine" if its name is also a urine test
(Glucose, Protein, Blood, Bilirubin); see "Urine names" below.

Other labs' layouts (PR #102): a leading row number is dropped; one up/down
arrow on a line is the report's H/L flag; the order name - value - range - unit
is read ("Total Cholesterol 4.12 < 5.20 mmol/L"); a reading that took the
reference limit as the value is refused.

Answer check (PR #103): a number counts as cited only as a value with the
row's own unit (not inside a test name such as CA19-9, not the start of a
range); "from X to Y" trend values are not judged as in-range results;
"above/below/outside normal" is not counted as calling a result normal.

Labelled ranges (PR #104): bands printed with labels (Female / Male,
Non-smoker / Smoker, a "Recommended Range" with band lines below) are all
shown in the Reference range column, the value is marked "(value in band)",
and the status is "see bands". The program does not choose a band (the
patient's sex or smoking status is not known to it); the clinician does.
"Upto 2.5" and "under 4 ng/ml" are read as upper limits (<=2.5, <4).

Reference-note lines (PR #105): a line with no printed range (or a range as
its value), no H/L flag and a note word in its name (normal, optimal,
desirable, borderline, high, low, risk, factor, target, patient, adult, ref,
recommended, ideal, goal) is a reference note, not a result ("Normal : < 1.7
mmol/L", "Target in patients 0-1 risk factors : < 3.4 mmol/L"). "High/low
density" and "high/low sensitivity" do not count. Known limit: a real result
with a note word in its name, no printed range and no flag is left out.
Urine names (Session 51 cont. 9): inside a URINALYSIS section only rows whose
English name starts like a urine test (pH, Sp./Specific Gravity, Protein,
Glucose, Ketone, Bilirubin, Urobil..., Blood, Nitrit..., Leuc/Leuk..., RBC, WBC,
Epith..., Cast, Granular, Hyaline, Crystal, Bacteria, Yeast, Mucus/Mucous,
Colour/Color, Clarity, Appearance, Others) are named "- Urine"; a /HPF or /LPF
unit is named "- Urine" anywhere. A blood-only test (Sodium, Potassium) below a
urinalysis section with no "Released By" keeps its name. Known limit: names
shared with blood tests (Glucose, Protein, Blood, Bilirubin) cannot be told
apart by name.
Urine result - reference order (Session 51 cont. 10): some labs print a urine row as
name, result, reference, unit ("Blood 尿血 Trace * Negative", "Hyaline Cast Nil
Nil /HPF", "RBC 1 - 2 < 5 cells/ul"). Inside a URINALYSIS section, a line the
main parser cannot read, or reads without a reference, is read in this order.
A "*" after the result is the report's flag. TRACE, +, 1+ to 4+ and POSITIVE
against Negative or Nil are HIGH. Colour / Appearance pairs such as "Yellow
Yellow" are not read yet.
Abnormal results not mentioned (Session 51 cont. 12): after the answer, the program
lists abnormal results (HIGH, LOW, ABNORMAL, or "see bands" with the lab's own
flag) that the answer never names: "Abnormal results not mentioned in the
answer: Globulin, Platelet Count; urine: Blood, Protein". A result counts as
named when a distinctive English word of its test name appears in the answer;
for a urine result the word must be in a sentence that says urine or urinary.
Known limit: a word used in another sense ("C-reactive protein") counts as
named, so the warning reduces silent omissions but cannot rule them out.
CKD stage check (Session 51 cont. 13): when the answer names a CKD stage
("CKD stage 3", "stage 3 CKD", "CKD G3a"), the program compares it with the
eGFR (the table row; if there is none, an eGFR written in the answer) using the
KDIGO categories G1 >=90, G2 60-89, G3a 45-59, G3b 30-44, G4 15-29, G5 <15, and
warns when the stage fits none of the eGFR values. A stage after "not", "rule
out", "unlikely", "risk of" or "progress to" in the same sentence is skipped.
Known limit: only the stage is checked against the eGFR; whether CKD is the
right diagnosis (more than 3 months, markers such as proteinuria) is for the
clinician.

eGFR value-only row (Session 51 cont. 14)
  Some labs print eGFR as name and value only ("e-GFR ... 68"), with the
  unit and the reference in notes below the table. parse_line reads such a
  line only when no other reader finds a row, and only for eGFR. The value
  is kept as printed; unit and reference stay empty, so the status is
  'no range'. The CKD stage check (cont. 13) uses this row.

Answer checks: urine value and 'elevation' (Session 51 cont. 15)
  A urine result counts as named in the answer only when its value is in
  the same sentence as 'urine'/'urinary' and the test word ("urine protein
  1+", "trace blood in the urine", "RBC 10-17"). "Urine protein
  quantification" alone does not count. Blood rows are unchanged. The words
  that call a result abnormal now include 'elevation'. A sentence without a
  number ("elevated urea and creatinine") still gives no in-range warning.

'Urinalysis' as a urine word (Session 51 cont. 16)
  For the not-mentioned check, a sentence is about urine when it has
  'urine', 'urinary' or 'urinalysis'. The result value must still be in the
  sentence ("Urinalysis shows protein 1+"); "urinalysis" alone does not count.

Denied urine findings and negated words (Session 51 cont. 17)
  A sentence such as "No proteinuria" or "no haematuria confirmed" gives a
  warning when the matching urine result (Protein; Blood and RBC; WBC and
  Leuk. esterase; Glucose; Ketone) is HIGH. An abnormal word with "no",
  "not", "without", "absence of" or "negative for" up to 3 words before it
  ("no evidence of anaemia") no longer counts as calling a result abnormal.

Plural abbreviations, urine ratios and comma lists (Session 51 cont. 18)
The not-mentioned check reads 'RBCs' as RBC for urine rows only (urine 'RBCs/ul' does
not name the blood RBC row). A urine albumin- or protein-to-creatinine ratio does not
count as naming serum Albumin, Protein or Creatinine. The denied-urine check reads a
comma list after 'No' ('No proteinuria, haematuria, or ...'); the list stops at but,
however, although, though, yet, whereas or except.

In-range result called abnormal: judged per clause (Session 51 cont. 19)
A sentence is split at semicolons and at but, however, although, though and whereas.
A clause warns when it gives the in-range value, calls it abnormal and has no
'normal'/'within' word, so '... mild elevation in AFP (2.24 ng/ml), but all tumour
markers remain within ...' warns. The warning quotes the whole sentence. For a range
with only an upper limit ('<5.0') 'low' is not abnormal ('CRP is low at 0.8'); for
only a lower limit, 'high' is not. For a result of 10, the '10' in 'x 10^12/L' is
not read as that result.

Band names in the answer (Session 51 cont. 20)
For a result with labelled bands (Vitamin D: Lack of Vit-D, Insufficiency, Enough,
Toxicosis), the program warns when a sentence gives the value and calls it by a band
it is not in ('35.9 ng/ml ... insufficient' with 35.9 in Enough 30-100). Words:
deficient/deficiency, insufficient/insufficiency, sufficient/adequate/enough,
toxic/toxicity/toxicosis/excess. A word right after a range and 'as' ('10-30 as
insufficient') is a definition, and a negated word does not count. Bands for sex or
smoking (CPK, CEA) are not checked.

Units, denials and urine rows (Session 52)
Power-of-ten units are compared in one form, so 'x 10^12/L', 'x10e12/L' and
'x10(sup)12/L' are the same unit, and the 10 in them is never read as a result.
'Proteinuria is absent' or 'was not seen' counts as denying a positive urine result;
'no data on proteinuria' and 'does not exclude proteinuria' do not. 'C-reactive
protein' does not count as naming total protein. Urine Colour/Appearance rows with a
reference word ('Yellow Yellow': normal when they match) and Crystals rows are read,
and 'Ep. Cell' is named '- Urine'.
