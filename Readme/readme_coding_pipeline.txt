readme_coding_pipeline.txt
==========================
Coding pipeline (launcher menu 1, --mode coding): how it works and what
makes its output valid. Session 48, 2026-11-18. Checked against
SOURCE_CODE/pipelines/coding/coding.py and handle_coding_mode in
SOURCE_CODE/main.py.

Short version: every result is written by an AI and checked by an AI.
No code is ever run. "PASSED" means an AI said so, not that the code
works.


1. What the pipeline does
-------------------------
Menu 1 asks for a sub-mode:

  1. Builder   build -> review -> test loop, writes code to output/coding/
  2. Reviewer  one AI review per file in input/coding/, report only
  3. Tester    one AI "test" per file in input/coding/, report only

Then you type instructions, one per line; a blank line ends input.
Every line you type becomes a direct instruction (highest priority):
the program adds "> " to any line that lacks it. If you type nothing,
the AI works from the docs/coding/ guidelines alone.

Every AI call gets the same system prompt, plus all *.md files in
docs/coding/ (joined in name order) as guidelines.


2. Builder: the loop
--------------------
Each file in input/coding/ is one subproject, handled in name order.
With no input files, Builder writes one new program ("new_app") from
your instructions.

For each subproject there is first a review loop (Builder writes,
Reviewer reads, its feedback goes back to Builder), then a test loop
(the same with Tester). The rounds are limited by MAX_ITERATIONS = 3.

If both Reviewer and Tester passed, the code is saved as _FINAL. If
not, the last version is saved anyway as _MAXITER_WARNING. That file
did NOT pass review or test; treat it as a failed attempt.

Long answers: if the code looks cut off, Builder asks the AI to go on,
up to 5 times. The cut-off check is a guess based on how the text
ends, so an incomplete file can still be saved.


3. Reviewer and Tester on their own
-----------------------------------
Sub-modes 2 and 3 make one AI call per file in input/coding/. They do
not change the code. They write one report per file and a session
summary. With no input files they stop: "nothing to review/test".


4. What PASS means
------------------
A step passes only if the AI answer STARTS with REVIEW_PASS or
TEST_PASS. Anything else counts as FAIL, including:
  - an answer that puts any text before the keyword;
  - "[ERROR] ..." when the AI call failed or hit the time limit
    (--time-limit 15/30/60/none).

The Tester never runs the code. There is no test run, no compiler and
no sandbox anywhere in this pipeline. TEST_PASS is an AI's opinion
after reading the code. The same model can write a bug and then pass
it.


5. Input and output
-------------------
Read from input/coding/ (top folder only; subfolders are skipped):
  .py .js .ts .html .css .java .c .cpp .cs .rb .go .rs .txt .md .php
  .swift .kt .r .sh .sql .svg
Other files (.ipynb, .json, .yaml, .docx, .pdf ...) are ignored with
no message. Files are read as UTF-8; bytes that are not valid UTF-8
are dropped with no message. Spaces in file names become "_".

Written:
  output/coding/   BUILDER_<name>_<time>_FINAL<ext>
                   BUILDER_<name>_<time>_MAXITER_WARNING<ext>
  reports/coding/  a report per round, a summary per file, and
                   BUILDER/REVIEWER/TESTER_SESSION_<time>_SUMMARY.md
The input file's extension is kept. For new code it is guessed from
the content. Files in input/coding/ are never changed.


6. Size limits
--------------
Each call sends the guidelines, your instructions and the whole file,
and Builder must send the whole file back.

On local AI (Ollama) the window is OLLAMA_CONTEXT, 32,768 tokens by
default, and holds both the prompt and the answer (up to 8,192 tokens).
If a prompt is longer, Ollama drops the START of it with no message -
that is the guidelines and your instructions.

So on local AI, an input file over 40,000 characters is skipped with a
message ("too large for local AI (limit 40,000). Skipped."); the other
files still run. Why 40,000, not 80,000 as in appraisal and writing:
code is about 3 characters per token, and from round 2 a Builder prompt
carries the whole file plus the last Reviewer/Tester answer (up to
8,192 tokens). Cloud providers are not limited by this check.

Not covered by the check:
- Builder's code can grow over the rounds; only the input size is
  checked.
- A file over about 24,000 characters cannot come back in one answer.
  Builder then asks the AI to go on (section 2), and each of those
  calls sees only the last 800 characters, so the joins can be wrong.
  Check them.
- Builder from scratch (no input file) is not checked.


7. Known limits
---------------
- Builder rewrites the whole file. The AI can drop or change parts you
  did not ask about. Only a diff against the input shows this.
- Each file is handled alone. The AI does not see the other files, so
  names and imports across files are not checked.
- The end line "Done. Check output/coding/ and reports/coding/" is
  shown even when nothing was written.
- With a cloud provider, your code and guidelines are sent to it.
- --dry-run gives placeholder answers, not real ones.
- generate_code_revision in main.py (reports/code_revision_*) is a
  separate older path, not one of the menu 1 sub-modes; not covered.


8. Rules for valid use
----------------------
1. Treat every output file as untested code written by an AI.
2. Read the diff between input and output before using it.
3. Run the code and your own tests yourself, in a copy or a virtual
   environment - never first on live or patient data.
4. Never use a _MAXITER_WARNING file as if it had passed.
5. REVIEW_PASS and TEST_PASS are AI opinions, not proof.
6. On local AI, files over 40,000 characters are skipped (section 6).
7. Keep patient data, passwords and API keys out of input/coding/ and
   docs/coding/, above all with a cloud provider.
8. The person who uses the code is responsible for it.
