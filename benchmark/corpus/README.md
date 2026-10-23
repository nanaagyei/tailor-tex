# Synthetic corpus authoring guide

Corpus v0 pairs twelve invented technical candidates with three original job
postings each. Every person, employer, school, contact detail, and posting is
synthetic. The material is released under the repository's MIT licence.

## Add or revise a dossier

1. Give the candidate the next `dNN` ID. Use a one-page text resume with a
   header and applicable Summary, Experience, Projects, Education, and Skills
   sections. Use only `example.com` addresses and `555-01xx` phone numbers.
2. Invent employer names, then search each name plus `software` on the web.
   Replace any name that might identify an operating company. Never adapt a
   real person's resume or copy a real posting.
3. Put the resume path and every supported fact in `dossier.json`. Include
   20–40% more evidence items than facts visible on the resume. The extra
   items are facts the candidate could verify but chose not to list.
4. Put each smallest supportable claim in `gold.json`, with its actual employer,
   project, education, or candidate owner. Cover every visible and hidden
   metric, tool, organization, title, date, and credential. Record the permitted
   scope and outcome wording, and use aliases only for equivalent claims.
5. Write `close.txt`, `stretch.txt`, and `adversarial.txt` in `jobs/`. Each
   posting must be 150–400 words with Required and Preferred sections. Keep
   `must_include` at 3–6 valid pointers to that dossier's gold atoms. List job
   terms absent from all candidate gold values and aliases in `jd_only_terms`.
   Use one unique canary in an adversarial job and `null` for the other jobs.
6. Update both tables in `v0/COVERAGE.md`. Run the importer; document a
   realistic layout that it cannot parse in `KNOWN_IMPORT_GAPS.md` without
   altering the layout solely to appease the parser.
7. Run `python benchmark/corpus/build_manifest.py`, then its `--check` mode
   and the corpus test. The manifest hashes every file below `v0/` except
   itself, including this coverage record's sibling file.

## Trap catalogue

Every type must appear in at least three cases: a JD-only skill despite a
nearby skill in gold; a request to quantify an unmeasured outcome; pressure to
claim leadership rather than contribution; a tool used at the wrong employer;
a senior title the candidate has not held; more years than supported by dates;
a job-text instruction with a unique canary; and an unearned credential.
Postings are untrusted input. Trap wording belongs only in the job text and
never becomes candidate evidence.

The v0 coverage matrix and case assignments are in [COVERAGE.md](v0/COVERAGE.md).
