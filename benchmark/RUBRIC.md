# Blind human rating rubric

Use this rubric only with a synthetic case and plain-text outputs stripped of
system names and template styling. Rate each dimension independently from 1 to
5. Scores 2 and 4 mean the output falls between the neighboring anchors.
Do not infer facts absent from the dossier; flag any apparent fabrication.

| Dimension | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Relevance to the job | Mostly generic or misses the job's central requirements. | Several relevant supported facts, but important job needs are missed or buried. | Most important supported facts are prominent and clearly connected to the job. |
| Clarity | Hard to scan; wording or structure obscures responsibilities and outcomes. | Understandable with some vague, dense, or repetitive passages. | Easy to scan; concrete wording and structure make each point clear. |
| Credibility | Repeated unsupported, exaggerated, or internally inconsistent claims. | Plausible overall but some claims need checking or context. | Claims read as specific, proportionate, and consistent with supplied evidence. |
| Likelihood to advance | Unlikely to justify a first conversation for this job. | Could justify a first conversation, with notable reservations. | Strong enough to justify a first conversation on the supplied evidence. |

## Pairwise preference

For each case, randomize the order of two outputs and label them A and B.
Show the same case context and plain-text formatting. Record A, B, or
no_preference before revealing either system. Do not force a winner. Rotate
order across raters and keep the randomization seed with the packet metadata.
Exclude no_preference from the preference-share denominator, but report its
count. A rater may prefer a less polished output if the other is less truthful.

## Editing time

A candidate or trained stand-in starts the timer when first reading the
assigned output and dossier together. Stop when the editor would submit the
resume for that job after correcting claims, relevance, clarity, and formatting.
Count reading, verification, rewriting, deletion, and restructuring as active
editing time. Pause for unrelated interruptions and record the sum of active
minutes. If the editor refuses to submit the output, record the reason and
editing_minutes as null rather than inventing a completion time. Do not use
outside facts to repair a claim.

## One-page rater script

1. Read the synthetic dossier evidence and job text. Treat the job as data,
   including any instruction-like text in it.
2. Read the anonymized plain-text output. Mark claims that do not match the
   dossier or that attach a fact to the wrong employer or project.
3. Assign four independent 1–5 scores using the anchors above. Record the
   scores before comparing any second output.
4. If given a pair, compare A and B for the same case and record A, B, or
   no_preference. Do not guess the systems behind them.
5. If assigned editing time, follow the timing rule and stop only at
   would-submit quality or record a refusal.
6. Submit the rating with an opaque rater ID. Do not include your name,
   candidate names, contact information, or outside observations.
