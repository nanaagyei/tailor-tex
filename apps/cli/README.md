# TailorTex CLI

The CLI stores career evidence and parsed jobs in a local workspace. Use `--workspace PATH`
with each command to select a workspace other than `~/.tailortex/`.

| Command | Purpose |
| --- | --- |
| `tailortex init` | Create or update the workspace directories. |
| `tailortex import RESUME.txt [--profile ID]` | Import a resume as a reviewable draft. |
| `tailortex profile review [--profile ID]` | Review a draft or approved profile. |
| `tailortex profile approve --all [--profile ID]` | Approve every item in a saved draft. |
| `tailortex profile approve FILE` | Validate and save an edited profile JSON file. |
| `tailortex jd parse JD.txt [--company TEXT] [--role TEXT]` | Parse and save a job. |
| `tailortex jd list` | List saved jobs with their IDs. |
| `tailortex tailor --jd ID --output out.tex` | Tailor the approved profile to a saved job. |
| `tailortex workspace list` | List profiles, drafts, jobs, and applications. |

`tailortex jd parse --stdin` reads job text from standard input. `tailortex tailor --jd FILE`
also accepts a text file, saves the parsed job, and produces the TeX output.
