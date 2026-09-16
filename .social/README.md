# Social publishing queue

This directory is the hand-off point between autonomous project development and Buffer.

When InfraSentry reaches a meaningful milestone, an automation may add one JSON file under `.social/queue/`.

Each file must contain at least:

```json
{
  "text": "LinkedIn post body",
  "reason": "Why this milestone merits a post",
  "source": "Commit, PR, issue, release or milestone reference"
}
```

A GitHub Actions workflow detects newly added queue files and sends their `text` to Buffer as a LinkedIn **draft**. It does not publish immediately.

## What deserves a post

Use the queue for meaningful project milestones only, for example:

- a substantial user-facing capability
- the first working Kubernetes collector
- a reproducible incident lab
- local AI reasoning becoming functional
- a benchmark or evaluation result
- a release

Do not create a post for routine refactors, dependency bumps, formatting changes, or filler commits.

## Tone

Posts should sound written, concrete and human. Avoid generic corporate language and empty adjectives. Prefer a short narrative around the technical problem, what changed, and why it matters.
