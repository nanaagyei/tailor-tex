# Known corpus import gaps

The v0 importer smoke test checks each resume's experience and education
counts and rejects "could not parse" warnings. One realistic layout currently
produces an extra, invalid education entry:

| Dossier | Layout | Observed import | Expected import |
| --- | --- | --- | --- |
| d12 | Institution, degree, and date range on three separate lines | Two entries: the degree without dates, then an `Unknown` institution and degree with dates | One entry with institution, degree, and dates |

The resume keeps the three-line education layout so the parser limitation is
visible to the future harness. The test asserts the observed count and this
documented exception; it does not treat the extra entry as candidate gold.
