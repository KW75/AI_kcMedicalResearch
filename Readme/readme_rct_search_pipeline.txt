readme_rct_search_pipeline.txt
==============================
RCT Search pipeline (launcher menu 5, --mode rct_search): how it works
and what makes its results valid. Session 48, 2026-11-18. Checked
against SOURCE_CODE/pipelines/rct_search/rct_search.py. Points not
checked are listed in section 7.

Short version: an AI writes the search strategy, two databases are
searched (at most 100 records each), and an AI scores each record for
relevance. This is a quick scoping search, NOT a systematic search.
The scores are AI opinions, not screening decisions.


1. What the pipeline does
-------------------------
  1-3. Three AI stages - Formulator, Searcher, Validator - build a
       PICO search strategy. Each stage gets the answer of the stage
       before it. The strategy is saved as pico_<time>.json.
  4.   PubMed and Europe PMC are searched, the results are merged,
       duplicates are removed, and an AI ranks the records.

Search terms are always sent to PubMed and Europe PMC over the
internet, even when the AI runs locally (Ollama).


2. The Validator stage
----------------------
If the Validator's answer contains "APPROVED FOR DOWNLOAD", the
strategy is accepted. If not, the screen shows:
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
The full PubMed query is printed on screen and saved in the
pico_<time>.json file (pubmed_query_cleaned).

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
The AI gets the merged list and returns one line per record:
  ARTICLE_RANK | SCORE | PMID | SOURCE | TITLE | URL
SCORE runs from 1 to 10 (10 = most relevant to the PICO). The program
reads these lines back with a text pattern.

What the score is NOT:
- not an inclusion or exclusion decision;
- not a check that the study is really randomised;
- not a risk-of-bias or quality rating.
Two runs, or two models, can rank the same records differently.


6. Output
---------
output/rct_search/
  rct_search_<time>.md     ranked table (Rank, Score, Source, Title,
                           PMID, Link)
  rct_search_<time>.docx   the same table, with links
  rct_search_<time>.csv    the same columns, for a spreadsheet
  pico_<time>.json         strategy, PubMed query
reports/rct_search/
  rct_search_<time>.md / .docx   full report with every stage's
                                 output (Formulator, Searcher,
                                 Validator, ranking)
--dry-run sends no searches and lists one fake test record.


7. Not checked for this readme
------------------------------
These points were not checked in the code. Check them on your own run
before you rely on the results:
- Whether stage 4 still runs after "REQUIRES REFINEMENT" (section 2).
- Whether a failed Europe PMC search shows an error, or just gives
  0 records. If one source shows 0, rerun before trusting that.
- Whether the ranking prompt includes abstracts or only titles.
- What happens to a record the AI leaves out of its ranking lines.
  Compare the number of rows with K from section 4.
- How an existing pico_*.json (input/rct_search/ or
  output/rct_search/) is reused.
- There is no size check for local AI. A long ranking prompt (up to
  200 records) has not been measured against Ollama's window.


8. Rules for valid use
----------------------
1. Use menu 5 for scoping, not as the search for a systematic review.
2. Rerun the printed PubMed query yourself on pubmed.ncbi.nlm.nih.gov
   and note the date and the total number of hits.
3. Check that the row count equals K (section 4); if not, find the
   missing records in the report.
4. Screen ALL records yourself. Never drop a record because of a low
   AI score.
5. Do not use the results if the Validator said REQUIRES REFINEMENT
   until you have reviewed and fixed the strategy.
6. Open the link for every study you keep; the AI can copy a title or
   PMID wrongly.
7. Search the other databases and registries (section 3) yourself.
8. The reviewer who reports the search is responsible for it.
