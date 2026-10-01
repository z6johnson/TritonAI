# Senate Chair Workflow

## Intake

1. Mail: search the linked mailbox for messages received after the `Last mail run` timestamp in `config.md`. Update the timestamp with `mark --root <root> --mail-run YYYY-MM-DD` only after all new messages are processed.
2. Drive: list new or updated documents in the linked shared Google Drive repository (per `references/document-repository.md`) since the `Last drive run` timestamp. Update the timestamp with `mark --root <root> --drive-run YYYY-MM-DD` only after all new documents are processed.
3. Files: list unprocessed files in `<root>/intake/` and process each. Leave originals in place.
4. Pasted: treat pasted text as one item with source `pasted`.

The selected account and document repository are recorded in `config.md` during setup. Use only those links; when the account is set to intake-folder-only, skip mail and calendar access entirely.

## Processing (every item)

1. Summarize in 120 words or fewer.
2. Assign exactly one topic label from `taxonomy.md` (or a config.md extra topic).
3. Extract every deadline as YYYY-MM-DD with the verbatim source sentence.
4. Assign a priority: Urgent (deadline within 3 days or Chair-directed), High, Normal, Low.
5. Propose an owner and next action. Proposals only; the Chair confirms triage.
6. Propose a case link:
   - Same topic plus overlapping entities (unit, committee, person, project, budget line) plus an open case: link to that case.
   - High confidence: link automatically. Medium or low: the script attaches a review flag.
   - No open case matches: propose a new case with a one-line title.

## Persisting an item

Preferred: one `new-item` command per item, with no JSON file:

```bash
bin/senate-chair new-item --root <root> --source-type <email|file|pasted> \
  [--ref "<message-id, subject+date, or file path>"] [--received YYYY-MM-DD] \
  --summary "<120 words or fewer>" --topic "<taxonomy label>" \
  --priority <Urgent|High|Normal|Low> \
  [--deadline "YYYY-MM-DD|verbatim source sentence"] \
  --case-action <new|existing> [--case-id SC-YYYY-NNN | --case-title "<one-line title>"] \
  --confidence <high|medium|low> --reason "<why this link or new case>" \
  [--suggested-owner "<unit or person>"] [--suggested-next-action "<one line>"] \
  [--confidential]
```

Repeat `--deadline` for multiple deadlines. Legacy alternative: write the
JSON schema below to `<root>/tmp/payload.json` and run `process --root <root>
--payload <root>/tmp/payload.json`:

```json
{
  "source": {"type": "email", "ref": "<message-id or subject+date>"},
  "received": "YYYY-MM-DD",
  "summary": "120 words or fewer",
  "topic": "Taxonomy label",
  "priority": "Normal",
  "deadlines": [{"date": "YYYY-MM-DD", "source": "verbatim sentence from the material"}],
  "case": {
    "action": "new",
    "id": "SC-2026-001",
    "title": "One-line title for a new case",
    "confidence": "high",
    "reason": "why this link or new case",
    "suggested_owner": "unit or person",
    "suggested_next_action": "one line"
  },
  "confidential": false
}
```

Rules: `source.type` is `email`, `file`, or `pasted` (a `ref` is required for email and file). For Drive documents, use `file` with the Drive file name or ID as the reference. For an existing case, set `action` to `existing` and include `id`; omit `title`. For a new case, set `action` to `new` and include `title`. Set `confidential` to true for any routing-guide topic.

## Triage

- Received: case exists, no confirmed owner or next action.
- Active: Chair confirmed owner and next action.
- Pending: waiting on another unit; `triage --status Pending` requires `--pending-unit`.
- Resolved: Chair confirms closure; record the resolution with `--next-action`.

## Board and briefing

- The board regenerates after every `new-item`, `process`, `triage`, and interactive board edit. To rebuild manually, run `board --root <root>`.
- When creating or updating the board, use the `ucsd-branding` skill to apply the current UCSD Decorator 5 shell.
- The interactive board supports inline case edits and drag-and-drop stage changes. Start it locally with `bin/senate-chair serve --root <root> --host 127.0.0.1 --port 8765`.
- Briefing data comes from `brief --root <root>`: deadlines within 7 days (including overdue), Pending cases by days waiting, Active cases untouched for 5+ days, and items received since the last briefing. Synthesize it into 200 words or fewer with two or three suggested first actions.
