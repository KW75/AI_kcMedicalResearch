# PICO Framework

This document defines the PICO structure used to formulate clinical research
questions for systematic review searches. It is injected into all three
rct_search roles as a shared reference.

---

## PICO Structure

| Element | Question to answer | Example |
|---|---|---|
| **P — Population** | Who are the patients or participants? | Adults over 65 with type 2 diabetes |
| **I — Intervention** | What is the intervention or exposure? | Metformin monotherapy |
| **C — Comparison** | What is the comparator? | Placebo or no treatment |
| **O — Outcome** | What outcomes are being measured? | HbA1c reduction at 12 months |

---

## Scope of this mode

This mode locates RCT articles suitable for download and subsequent
systematic review. It does not appraise article quality — that is a
separate step performed outside this tool.

The workflow is:

1. Formulator AI structures the research topic into a formal PICO question
2. Searcher AI builds a comprehensive search strategy across all SR databases
3. Validator AI checks alignment between the PICO and the search strategy
4. If gaps are found, return to step 1 to refine the PICO
5. When validated, the article list is ready for download

---

## Current research topic

[The Formulator AI will ask the user for the raw research topic at the
start of each session and construct the formal PICO question from it.]
