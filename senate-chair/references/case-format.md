# Case and Item Formats

The script owns these formats. Read them to understand the store; do not edit case or item files by hand — use the `process`, `triage`, and `mark` commands so IDs, logs, and the board stay consistent.

## case.md

```markdown
# SC-2026-001: <one-line title>
- Status: Received | Active | Pending | Resolved
- Topic: <taxonomy label>
- Owner: <name or unit, or "unassigned">
- Suggested owner: <proposal awaiting triage>
- Opened: YYYY-MM-DD
- Last update: YYYY-MM-DD
- Next action: <one line, or "awaiting triage">
- Review flag: <blank | new case unreviewed | auto-link medium confidence | auto-link low confidence>
- Pending unit: <unit being waited on>
- Pending since: YYYY-MM-DD
- Confidential: yes | no

## Deadlines
| Deadline | Source sentence | Item | Done |
|---|---|---|---|
| 2026-10-15 | "comments are due October 15" | 2026-09-29-001 | no |

## Log
- YYYY-MM-DD: <what changed>

## Items
- 2026-09-29-001: <one-line summary>
```

## Item file

```markdown
# Item 2026-09-29-001
- Source: email <message-id> | file <path> | pasted
- Received: YYYY-MM-DD
- Case: SC-2026-001
- Topic: <label>
- Priority: Urgent | High | Normal | Low
- Link confidence: high | medium | low — <one-line reason>

## Summary
<120 words or fewer>

## Deadlines
- YYYY-MM-DD: <verbatim source sentence>
```

## Commands

All commands run through `bin/senate-chair` (or `senate-chair` after
`install-command`). Users never invoke Python directly.

- `doctor [--root <path>]`: verify dependencies, skill files, root, account, and Drive links.
- `setup --root <path> --account <outlook-chair|outlook-personal|gmail|none> [--account-address <address>] [--drive-name <name>] [--drive-id <id>]`: initialize the data root, record links, and generate the board.
- `new-item --root <root> ...`: persist one processed item in a single command; see `workflow.md`.
- `process --root <root> --payload <json>`: legacy JSON-payload alternative to `new-item`.
- `link-drive --root <root> --name <name> [--drive-id <id>]`: link or update the shared Google Drive repository.
- `link-account --root <root> --account <outlook-chair|outlook-personal|gmail|none> [--account-address <address>]`: link or update the email account scope after verifying the connected account.
- `triage --root <root> --case <id> [--status <s>] [--owner <o>] [--next-action <text>] [--pending-unit <unit>] [--clear-review]`: apply Chair-confirmed decisions; regenerate the board.
- `board --root <root>`: regenerate `board/index.html`.
- `brief --root <root> [--date YYYY-MM-DD]`: print the briefing JSON skeleton and update the last-briefing marker.
- `list --root <root> [--status <s>] [--topic <t>]`: list cases.
- `mark --root <root> [--mail-run YYYY-MM-DD] [--drive-run YYYY-MM-DD]`: record the last processed mail and Drive dates.
- `serve --root <root> --host 127.0.0.1 --port 8765`: serve the interactive board locally; non-loopback hosts are rejected.
- `status --root <root>`: show the configured root, account, Drive repository, timestamps, and board path.
- `install-command`: install `senate-chair` into `~/.local/bin`.
