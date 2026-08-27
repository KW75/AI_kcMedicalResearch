# Database Search Guide

This document is injected into the Searcher AI role only. It defines the
databases to search, Boolean logic conventions, and syntax rules for each
platform.

---

## Standard SR databases — search all of the following

| Database | Platform | Coverage |
|---|---|---|
| PubMed / MEDLINE | pubmed.ncbi.nlm.nih.gov | Biomedical and life sciences |
| Cochrane Central Register of Controlled Trials (CENTRAL) | cochranelibrary.com | RCTs and controlled trials |
| EMBASE | embase.com | Pharmacological and biomedical |
| CINAHL | ebsco.com | Nursing and allied health |
| PsycINFO | apa.org/psycinfo | Psychology and mental health |
| Scopus | scopus.com | Multidisciplinary |
| Web of Science | webofscience.com | Multidisciplinary |

---

## Search strategy construction rules

### Boolean operators
- Use AND to combine PICO elements
- Use OR to combine synonyms within each PICO element
- Use NOT sparingly and only when clearly necessary

### MeSH terms
- Always include MeSH / controlled vocabulary terms for each concept
- Pair each MeSH term with free-text synonyms to maximise recall

### Truncation and wildcards
- PubMed / EMBASE: use * for truncation (e.g. random* retrieves randomised,
  randomized, randomisation, randomization)
- CINAHL / PsycINFO (EBSCOhost): use * for truncation
- Scopus / Web of Science: use * for truncation

### RCT filter
- Apply the Cochrane RCT sensitivity-maximising filter for each database
- For PubMed: add the Cochrane Highly Sensitive Search Strategy for RCTs

### Standard filters to apply
- Study design: RCTs only
- Language: English (adjust per project requirements)
- Date range: set per project requirements — default is no restriction

---

## Search strategy output format

Present the search strategy for each database as a numbered block showing
the exact search string as it should be entered into that platform.
