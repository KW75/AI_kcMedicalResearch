readme_rct_search_pipeline.txt
==============================
RCT Search pipeline (launcher menu 5, --mode rct_search): how it works
and what makes its results valid. Session 48, updated 2026-11-19 after
the menu 5 fixes (PRs #48-#55). Checked against
SOURCE_CODE/pipelines/rct_search/rct_search.py; section 7 lists what
was checked and fixed.

Short version: an AI writes the search strategy, two databases are
searched (at most 100 records each), and an AI scores each record for
relevance. This is a quick scoping search, NOT a systematic search.
The scores are AI opinions, not screening decisions.


1. What the pipeline does
-------------------------
  1-3. Three AI stages - Formulator, Searcher, Validator - build a
       PICO search strategy. Each stage gets the answer of the stage
       before it. The Formulator's PICO is saved as pico_<time>.json
       (not in a dry run, and not if the Formulator is skipped).
  4.   PubMed and Europe PMC are searched, the results are merged,
       duplicates are removed, and an AI ranks the records.

Search terms are always sent to PubMed and Europe PMC over the
internet, even when the AI runs locally (Ollama).


2. The Validator stage
----------------------
The strategy is accepted only if the Validator gives one clear verdict:
the first line after its last "Overall decision:" (or the whole answer
if there is none) says "APPROVED FOR DOWNLOAD" without "REQUIRES
REFINEMENT" or "NOT APPROVED". Otherwise (also after an AI error or
when the Validator is skipped) the screen shows:
  "Search strategy REQUIRES REFINEMENT - see Validator output."
Treat that message as a warning about the strategy: read the
Validator output in reports/rct_search/ before you use any results.
The approval itself is an AI judgement, not a check by a librarian.


3. The searches
---------------
PubMed query: the cleaned PICO terms joined with AND (or the topic
alone if no terms were found), plus this RCT filter:
  AND (randomized controlled trial[pt] OR clinical trial[pt]
       OR random*[tiab] OR RCT[tiab])
The full PubMed query is printed on screen and saved in this run's
pico_<time>.json file (pubmed_query_cleaned), if one was saved.

Limits:
- At most 100 records from PubMed and 100 from Europe PMC. Anything
  beyond the first 100 is never seen, and no message says so.
- Only these two databases. Not searched: CENTRAL (Cochrane), Embase,
  CINAHL, PsycINFO, Web of Science, trial registries
  (ClinicalTrials.gov, WHO ICTRP), grey literature.
- The filter also lets through non-randomised "clinical trial"
  records and any record with "random" in the title or abstract.
- No full texts are fetched.


4. Merging and duplicates
-------------------------
PubMed records come first. A Europe PMC record is dropped as a
duplicate if its PMID was already seen, or if its title matches an
earlier title after normalising.

The screen shows the counts:
  "Found N PubMed + M Europe PMC = K unique articles"
Write these numbers down - they are the counts for a flow diagram.

Europe PMC records without a PMID use the DOI (with "/" replaced by
"_") or a generated code in the PMID column. So not every value in
that column is a real PMID; use the Link column for those records.


5. AI ranking
-------------
The merged list is shuffled (except in a dry run) so that position
does not bias the AI, and sent with each abstract and the
Formulator's PICO. The AI returns one line per record:
  ARTICLE_RANK | SCORE | PMID | SOURCE | TITLE | URL
SCORE runs from 1 to 10 (10 = most relevant to the PICO); larger
numbers are scaled down to 1-10. The program reads the lines back
with a text pattern and matches them to the fetched records by PMID:
title, link and source always come from the database record, each
record is kept once, and lines with a PMID that was not fetched are
dropped. Records the AI did not score are listed last with score
"-". The screen line "Ranking check: N of K records scored by the
AI; ... invented, ... repeated, ... left out" gives the counts.
With local AI (Ollama) the records are ranked in batches that fit
the model's window (section 7); cloud AI gets one prompt.

What the score is NOT:
- not an inclusion or exclusion decision;
- not a check that the study is really randomised;
- not a risk-of-bias or quality rating.
Two runs, or two models, can rank the same records differently.


6. Output
---------
output/rct_search/
  rct_search_<time>.md     ranked table (Rank, Score, Source, Title,
                           PMID, Link); unscored records last ("-")
  rct_search_<time>.docx   the same table, with links (a .csv with the
                           same columns only if python-docx is missing)
  pico_<time>.json         the Formulator's PICO, the PubMed query and
                           the ranked list - this run's file only
reports/rct_search/
  rct_search_<time>.md / .docx   full report with every stage's
                                 output (Formulator, Searcher,
                                 Validator, ranking)
At the end you are asked whether to copy this run's pico_<time>.json
to input/sr/ for the SR pipeline (not asked if no file was saved).
--dry-run sends no searches, calls no AI, saves no pico_<time>.json
and lists one fake test record; its screen line reads "Dry run: no
searches sent, 1 fake test record." It prints no "Searching PubMed /
Europe PMC" lines, and its ranking line reads "Dry run: fake ranking,
no AI call." instead of "Ranking check: ...".


7. Checked in the code (Session 48)
-----------------------------------
Checked in SOURCE_CODE/pipelines/rct_search/rct_search.py (Session 48,
first at e72820d). Every gap found was fixed in PRs #48-#55; function
names are given instead of line numbers, which change.
- Validator gate: fixed (Session 48). Stage 4 (search and ranking)
  still always runs; "REQUIRES REFINEMENT" is only printed and written
  in the report. Approval needs one clear verdict in the Validator's
  own answer (_validator_verdict): the line after the last "Overall
  decision:" must say APPROVED FOR DOWNLOAD without REQUIRES REFINEMENT
  or NOT APPROVED. The echoed prompt template, an AI error or a skipped
  Validator all count as REQUIRES REFINEMENT.
- Ranking prompt: fixed (Session 48). The "PICO Question" it sends is
  the Formulator's answer; before, it was the last stage output (the
  Validator's answer). If the Formulator fails or is skipped, the topic
  and any typed P/I/C/O are sent instead.
- Abstracts: sent. Each record goes to the AI with source, PMID, title,
  URL and abstract, or "No abstract available." Europe PMC asks for
  full records (resultType=core, fetch_europepmc_articles).
- Failed searches: fixed for PubMed (Session 48). Europe PMC and PubMed
  both print a line and give 0 records: "[Europe PMC] Search failed:
  ...", "[PubMed] Search failed: ...", "[PubMed] Fetch failed: ..." or
  "[PubMed] XML could not be read: ...". All requests have a 30 s time
  limit. If a source shows 0 with an error line, rerun before trusting it.
- Ranking lines: fixed (Session 48). Only records that were fetched are
  kept, once each; title, URL and source come from the fetched record,
  not from the AI line. Every record the AI did not score (left out, or
  all of them after an AI error or an answer that cannot be read) is
  listed at the end with score "-"; no position-based scores. One screen
  line "Ranking check: N of K records scored by the AI; ... invented,
  ... repeated, ... left out" gives the counts.
- AI call: fixed (Session 48). call_ai no longer returns a made-up
  "[MOCK] ..." answer when main cannot be imported or the AI call
  raises ImportError or AttributeError. It raises RuntimeError: the
  stage then shows "[ERROR in <role>: ...]", and a ranking error
  lists every record unscored ("-").
- Saved PICO: fixed (Session 48). Up to 5 saved pico_*.json files are
  offered, from input/rct_search/ if it has any, else output/rct_search/.
  The chosen file fills P, I, C, O and the topic; it is not changed.
  Each run (not a dry run) saves a new pico_<time>.json in
  output/rct_search/ after the Formulator. The ranking is added only to
  that file, and only that file is offered for copying to input/sr/.
  If no file was saved (formulator-prompt.md missing, or a dry run),
  the screen says so and no older run's file is changed or offered.
- Local AI size: fixed (Session 48). For provider ollama the records are
  ranked in batches: each prompt fits OLLAMA_CONTEXT (3 characters per
  token, OLLAMA_NUM_PREDICT tokens kept for the answer, default 8192) and
  holds at most 109 records (scaled with OLLAMA_NUM_PREDICT),
  so every rating line fits the answer limit. Abstracts are not cut.
  More than one batch prints "Local AI: N records ranked in K batches".
  A failed batch prints a line and leaves only its records unscored
  ("-"). Cloud providers get one prompt, as before.


8. Rules for valid use
----------------------
1. Use menu 5 for scoping, not as the search for a systematic review.
2. Rerun the printed PubMed query yourself on pubmed.ncbi.nlm.nih.gov
   and note the date and the total number of hits.
3. The table always has K rows (section 4). Read the "Ranking check"
   line: records the AI did not score are listed last with "-";
   screen them like the rest.
4. Screen ALL records yourself. Never drop a record because of a low
   AI score.
5. Do not use the results if the Validator said REQUIRES REFINEMENT
   until you have reviewed and fixed the strategy.
6. Open the link for every study you keep. Title and link come from
   the database record, but a record without a PMID shows a DOI or a
   generated code in the PMID column (section 4).
7. Search the other databases and registries (section 3) yourself.
8. The reviewer who reports the search is responsible for it.
