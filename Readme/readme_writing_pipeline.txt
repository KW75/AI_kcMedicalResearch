readme_writing_pipeline.txt - Writing mode (launcher menu 2): how drafts
are produced, and what limits their validity
======================================================================

This file explains the logic of the writing pipeline in general terms.
It is not a user guide: menu steps and options are in
Readme/flashcard-help.html.

1. What the pipeline does
-------------------------
Writing mode turns typed instructions, and optionally files placed in
input/writing/, into a draft document plus a short review of that
draft. There are four tracks:

  Topic     editorial / opinion piece           default  800 words
  Article   medical research (journal) article  default 3500 words
  Report    structured abstract / report        default  500 words
  Synopsis  ONE synopsis of ALL input files     default 1500 words

The default word limit can be changed when the run starts.

2. One AI call per document
---------------------------
Topic, Article and Report work in one pass. For each file in
input/writing/ the AI receives, in a single call: the writing
guidelines for the track, the typed instructions, and the text of that
one file. It returns the revised document and a review of it in the
same answer. Each file is handled on its own; the AI does not see the
other files.

If input/writing/ is empty, or files are switched off for the run, one
document is written from the instructions alone. Input files are never
moved or deleted.

Synopsis is different: one AI call receives all readable files
together and writes one synopsis across them, plus a review.

The AI sees nothing else: no web search, no reference database and no
other project files. Anything in the draft that is not in the
instructions or the input text came from the model itself.

3. Output
---------
Results go to output/writing/: the document as .md and .docx, and the
review as a separate _REVIEW.md file. File names carry the track, the
input file name and a time stamp, so earlier runs are not overwritten.
The one-pass tracks write nothing to reports/writing/.

4. How well the input is read
-----------------------------
The draft can only be as accurate as the text the AI received.

  .txt .md .html .tex .rst  read as plain text.
  .docx  paragraphs and tables, in document order; each table row
         becomes one line ("cell | cell | cell").
  .pdf   the text layer only. Tables arrive as plain text and their
         columns can mix. A scanned PDF has no text layer. A PDF with
         a broken font can lose symbols such as +/-, <, = and minus
         without any warning.
  .doc   refused (open it in Word and save it as .docx).

Tables pasted into Word as pictures are not read.
For scans, broken-font papers or number-critical PDF tables, run OCR
(menu 8) first, check the record against the original, and put the
record into input/writing/. See Readme/readme_ocr_pipeline.txt.

5. Size limits
--------------
Synopsis on a local AI (Ollama) adds up the size of all readable
files. Above 80,000 characters it stops before sending anything,
writes nothing, and says so on screen. Unreadable files are skipped.
A cloud provider has no such check.

Topic, Article and Report have NO size check at present. On a local
AI the whole prompt must fit the model's context window
(OLLAMA_CONTEXT, 32,768 tokens by default) together with room for the
answer. A very long input file (roughly above 80,000 characters) may
not fit. Ollama then drops the start of the prompt without an error,
and the guidelines come first. The draft can look normal while
ignoring them. Until a check is added, use a cloud provider or a
shorter file for long inputs.

The separate --report option reads input through the general reader,
which cuts a PDF at 30,000 characters. The cut is marked in the text
and shown as a WARNING, so it is visible.

6. What the review is - and is not
----------------------------------
The review is written by the same model, in the same call, that wrote
the draft. It is a self-check, not an independent review. It can point
out problems of style, structure and gaps against the guidelines, but
it cannot be relied on to notice its own invented or wrong facts,
numbers or references. A clean review is not evidence that the draft
is correct.

7. Known limits
---------------
- Invented content: the model can add facts, numbers, study details
  and references that are not in the input. Article and Report drafts
  are the most exposed.
- References are not checked against any database.
- The word limit is an instruction to the AI; check the actual length.
- Revision can change meaning. When a file is revised, compare it with
  the original, especially numbers, units, direction of effects and
  hedged claims.
- Synopsis covers only the files given. It is not a systematic search
  and does not notice missing papers.
- A cloud provider sends the instructions and file text off the
  machine. A local model keeps them on the machine but is usually
  smaller and makes more mistakes.

8. Rules for valid use
----------------------
1. Treat every output as a draft written by an AI.
2. Check every number, name, date and claim against the source.
3. Check that every reference exists and says what the draft says.
4. For PDFs, check that tables and symbols came through (section 4).
5. On local AI, keep one-pass input files short (section 5).
6. The named human author is responsible for the final text.

Legacy note: an older three-step chain (writer, editor, QA) is still
in the code but is not used by the writing menu.
