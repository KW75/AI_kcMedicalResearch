readme_search_pipeline.txt
==========================
Search pipeline (launcher menu 4, --mode search): how it works and what
makes its results valid. Session 48, 2026-11-18, updated 2026-11-19
after PRs #39 to #43. Checked against SOURCE_CODE/pipelines/search/
search.py and handle_search_mode in SOURCE_CODE/main.py. Points not
checked are listed in section 7.

Short version: one database is searched (Europe PMC for Topic, PubMed
for Article), only the first 5 to 15 records are used, and an AI writes
a summary of them. This is a quick look at a topic, NOT a literature
search. Menu 5 (RCT Search) searches more widely; see
readme_rct_search_pipeline.txt.


1. What the pipeline does
-------------------------
Menu 4 asks for a sub-mode:
  1. Topic Search    Europe PMC -> AI synopsis with references
  2. Article Search  PubMed, one article type -> AI summary and
                     comparison
A blank or invalid choice gives Topic Search.

Then you type the query; a blank line starts the search. Every line
you type is joined with spaces into ONE search query. Do not type
instructions such as "summarise in 200 words" - they are sent to the
database as search words. (Topic Search also removes leading digits
and dots from the query.)

The query is matched against all fields, including journal names: in
a live check, "asthma" also found angioedema and osteoarthritis
papers from the "Iranian journal of allergy, asthma, and immunology".
In Article Search, asthma[tiab] limits it to title and abstract (and
may miss records that use other words). Field tags for Europe PMC
(Topic) were not checked.


2. Topic Search
---------------
- Europe PMC is searched with your query. The first 10 records are
  used; 5 if the model name starts with llama3.2, llama3.1 or
  qwen2.5-coder.
- For each record the AI gets the title, the link and a snippet: the
  first 300 characters of the abstract (the title if there is no
  abstract). It never sees the full abstract or the full text.
- The AI writes Overview, Key Findings and Clinical Relevance.
- The program then deletes the AI's References section and puts in
  the real list of records it found. So the reference list is always
  correct, but the text above it is not checked: a "finding" may rest
  on 300 characters, or on nothing.


3. Article Search
-----------------
You pick an article type; it becomes a PubMed filter:
  1 Systematic Review  systematic[sb]
  2 Meta-analysis      meta-analysis[pt]
  3 RCT                randomized controlled trial[pt]
  4 Guideline          guideline[pt]
  5 Protocol           protocol [pt] tag or protocol phrase in title, below
  6 Review Article     review[pt]
  7 Clinical Trial     clinical trial[pt]
  8 Custom             your word, searched in title/abstract [tiab]
An invalid choice gives Review Article.

Choice 5 finds records that PubMed tags "clinical trial protocol", or
whose title contains "study protocol", "trial protocol", "review
protocol", "protocol for a" or "protocol design" (since Session 48;
it used to be "research support[pt]", which marks funded research).
Plain "protocol" in the title is not used: in a PubMed check for
asthma, 6 of the first 10 such records were clinical protocols (for
example "BLUE-protocol"), not study protocols; with the phrases, all
of the first 10 were. It still misses untagged protocols whose title
uses other wording.

- PubMed is searched; the first 15 records are used (small models are
  NOT reduced here).
- Their abstracts are fetched and given to the AI, which writes a
  summary and comparison.
- Abstracts are matched to records by PMID, from PubMed's XML reply
  (since Session 48; before, by position, which could put an
  abstract under the wrong record). A record without an abstract
  gets "[Abstract not available]". The abstract is only the
  abstract text (structured parts keep labels such as "BACKGROUND:");
  title, authors and journal are listed separately. If the fetch
  fails, "PubMed abstract fetch error: ... - summary uses titles
  only." is printed and the run continues.
- Unlike Topic Search, the AI's text - including any reference list -
  is saved as written. Links, PMIDs and DOIs in it are not replaced by
  the real ones; check each one.
- PUBMED_API_KEY from .env is used if set.


4. When something goes wrong
----------------------------
- No records: the run stops ("No results found" / "No articles
  found"). No AI call, no file.
- Network error: an error line is printed, then the same stop.
- Europe PMC answers with an HTTP error (for example 429, 500 or 503):
  the line "Europe PMC error: HTTP <code> - no records read. Try
  again later." is printed, then the same stop (since Session 48;
  before, only "No results found" was shown). PubMed HTTP errors
  (Article Search) already print an error line.
- The AI call fails, times out or returns nothing: no file and no
  report are written. The screen shows "AI call failed - no file
  written." with the error, and not "Complete." (Since Session 48.
  Limit: an error returned without the "[ERROR]" prefix is not
  caught and would still be saved.)
  Open the output before using it.


5. Output
---------
output/search/
  TOPIC_<query>_<time>.md / .docx
  ARTICLE_<type>_<query>_<time>.md / .docx
reports/search/
  TOPIC_SEARCH_topic_<query>_<time>.md
      log with the number of records found
  ARTICLE_SEARCH_article_<type>_<query>_<time>.md
      log with article type and number of records
The query part of a name is cut short and odd characters become "_".
Without python-docx installed, the .docx is skipped with a warning.
The last screen line names both files (the .docx only if written).
The AI's text may contain LaTeX such as $\text{FeNO}$; Search turns known
commands into plain symbols before saving (strip_latex, shared with OCR).
Money such as $5 and unknown commands stay as they are.


6. Privacy and size
-------------------
- Your query is always sent to Europe PMC (Topic) or PubMed (Article)
  over the internet, even with local AI. Keep patient details out.
- With a cloud AI, the records and your query also go to that
  provider.
- The [LOCAL AI] notice and the cloud confirmation prompt name
  PubMed and Europe PMC. (Until Session 48 they also named
  DuckDuckGo, which menu 4 no longer contacts.)
- There is no local size check. Prompts are small (at most 10
  snippets, or 15 abstracts), but this was not measured (section 7).


7. Not checked for this readme
------------------------------
- The full Article prompt.
- Which records come first: the program uses each service's default
  order; whether a sort is set for PubMed was not checked.
- How the search guidelines folder is found and read.
- Whether the AI disclosure line is added to every output.
- The size of an Article prompt against Ollama's window.


8. Rules for valid use
----------------------
1. Use menu 4 for orientation only, never as a literature search.
2. Type only search words.
3. After "No results" with no error line above it, try the query on
   europepmc.org or pubmed.ncbi.nlm.nih.gov before concluding there
   is nothing. If an error line is shown, the service failed: run
   again later.
4. If the screen says "AI call failed", no file was written; run
   again. Any output that starts with "[ERROR]" is not a result.
5. Check every statement against the article itself; Topic text rests
   on 300-character snippets. The AI can miscount or misstate: in a
   live check it said "eight RCTs" for 15 records, and "in the lungs"
   where its own article summary said systemically.
6. In Article output, check every link, PMID and DOI.
7. For type 5 (Protocol), check that each record is a study
   protocol.
8. The person who uses the summary is responsible for it.
