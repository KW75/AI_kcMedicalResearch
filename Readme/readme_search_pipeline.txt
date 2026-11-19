readme_search_pipeline.txt
==========================
Search pipeline (launcher menu 4, --mode search): how it works and what
makes its results valid. Session 48, 2026-11-18. Checked against
SOURCE_CODE/pipelines/search/search.py and handle_search_mode in
SOURCE_CODE/main.py. Points not checked are listed in section 7.

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
  5 Protocol           research support[pt]   <- WRONG, see below
  6 Review Article     review[pt]
  7 Clinical Trial     clinical trial[pt]
  8 Custom             your word, searched in title/abstract [tiab]
An invalid choice gives Review Article.

Choice 5 does not find protocols: "research support[pt]" marks funded
research. Do not use it (open item).

- PubMed is searched; the first 15 records are used (small models are
  NOT reduced here).
- Their abstracts are fetched and given to the AI, which writes a
  summary and comparison.
- Abstracts are matched to records by their position in PubMed's
  reply. If that reply splits differently, an abstract can end up
  under the wrong record. If the fetch fails, no message is shown.
- Unlike Topic Search, the AI's text - including any reference list -
  is saved as written. Links, PMIDs and DOIs in it are not replaced by
  the real ones; check each one.
- PUBMED_API_KEY from .env is used if set.


4. When something goes wrong
----------------------------
- No records: the run stops ("No results found" / "No articles
  found"). No AI call, no file.
- Network error: an error line is printed, then the same stop.
- Europe PMC answers with an HTTP error (for example 500 or 503): NO
  error line, only "No results found". So "no results" can mean the
  server failed. Try again before concluding there is nothing.
- The AI call fails or times out: the text "[ERROR] ..." is saved as
  the synopsis or summary, and the screen still says "Complete."
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


6. Privacy and size
-------------------
- Your query is always sent to Europe PMC (Topic) or PubMed (Article)
  over the internet, even with local AI. Keep patient details out.
- With a cloud AI, the records and your query also go to that
  provider.
- The cloud confirmation prompt still lists DuckDuckGo, but menu 4 no
  longer contacts it (Topic Search moved to Europe PMC).
- There is no local size check. Prompts are small (at most 10
  snippets, or 15 abstracts), but this was not measured (section 7).


7. Not checked for this readme
------------------------------
- The full Article prompt, and what the AI gets if the abstract fetch
  failed.
- Which records come first: the program uses each service's default
  order; whether a sort is set for PubMed was not checked.
- How the search guidelines folder is found and read.
- Whether the AI disclosure line is added to every output.
- The size of an Article prompt against Ollama's window.


8. Rules for valid use
----------------------
1. Use menu 4 for orientation only, never as a literature search.
2. Type only search words.
3. After "No results", run again and try the query on europepmc.org
   or pubmed.ncbi.nlm.nih.gov before concluding there is nothing.
4. Open the output: if it starts with "[ERROR]", it is not a result.
5. Check every statement against the article itself; Topic text rests
   on 300-character snippets.
6. In Article output, check every link, PMID and DOI.
7. Do not use article type 5 (Protocol).
8. The person who uses the summary is responsible for it.
