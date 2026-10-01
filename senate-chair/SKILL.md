---
name: senate-chair
description: Set up and run Senate Chair operations. Link the Senate Chair Outlook account and the shared Google Drive document repository, initialize a local data root, intake materials from mail, Drive, an intake folder, or pasted text; summarize and label them; extract deadlines; manage cases on a Kanban board; generate a daily deadline-and-bottleneck briefing; draft replies from an approved answer bank; and manage the Chair's calendar. Use when the Senate Chair or delegate asks to initialize the system, process new materials, view the board, run the briefing, triage or find a case, draft a reply, or handle scheduling.
---

# Senate Chair

A local-first operations system for the Senate Chair: intake, case
management, a visual board, and a daily briefing, with reply drafting and
scheduling as case actions. The skill acts only on the Chair's linked
accounts and only on approved on-prem models.

## Model Policy

1. Read `references/model-policy.md` first. Verify that the session's
   selected model is an approved UCSD on-prem model according to the current
   harness environment before touching any Chair content. The skill never
   hard-codes model names or versions; if verification fails or is unclear,
   stop and say so.

## Quick Start

Use `references/harness-actions.md` for the installed action prompts. The
Chair only sends natural-language prompts; the assistant runs every command.

1. **Check deployment.** Run `bin/senate-chair doctor`. If Python is
   missing, install it automatically (`uv python install 3.12`, or `brew
   install python@3.12` on macOS) and re-run. Never ask the Chair to install
   dependencies or run CLI commands.
2. **Initialize.** If `doctor` reports no initialized root, ask for three
   things: the email account (recommend the **Senate Chair Outlook account**;
   also offer personal university Outlook, Gmail, or intake-folder-only),
   the shared Google Drive document repository (search Drive and let the
   Chair confirm the folder), and the root location (default
   `~/SenateChair`). Verify the connected Outlook account per
   `references/account-access.md`, then run
   `bin/senate-chair setup --root <root> --account <scope> [--account-address <address>] [--drive-name <name>] [--drive-id <id>]`.
   Optionally run `bin/senate-chair install-command`.
3. **Process.** Continue directly into intake. Use the linked Senate Chair
   mailbox, the linked Drive repository, `<root>/intake/`, and pasted text.
4. **Board.** Run `bin/senate-chair board`, then open
   `<root>/board/index.html` locally. For drag-and-drop edits, run `serve`
   bound to `127.0.0.1`.
5. **Briefing.** Run `bin/senate-chair brief`, synthesize the JSON into 200
   words or fewer, save it to `<root>/briefings/YYYY-MM-DD.md`, and show it.

The remembered root is `~/.senate-chair/root`. Commands accept `--root` or
`SENATE_CHAIR_ROOT` when a different root is needed.

## Workflow

1. **Intake.** Read `references/workflow.md`. Collect new materials from the
   linked mailbox (per `references/account-access.md`), new or updated
   documents in the linked shared Drive (per
   `references/document-repository.md`), new files in `<root>/intake/`, and
   pasted text. Each material becomes one item. After each batch, record it:
   `bin/senate-chair mark --mail-run YYYY-MM-DD` for mail and
   `bin/senate-chair mark --drive-run YYYY-MM-DD` for Drive.
2. **Process.** For each item, produce a summary of 120 words or fewer, one
   topic label from `references/taxonomy.md`, every deadline normalized to
   YYYY-MM-DD with its verbatim source sentence, a priority, a suggested
   owner, and a proposed case link. Persist it with one
   `bin/senate-chair new-item ...` command (see `references/workflow.md`);
   do not hand-write JSON payload files.
3. **Cases.** New issues open new cases in `Received`; updates append to
   existing cases. Apply the Chair's triage decisions with
   `bin/senate-chair triage --case <id> ...` per `references/case-format.md`.
4. **Board.** The command regenerates the dashboard after every change.
   Apply the current UCSD Decorator 5 shell using the `ucsd-branding` skill,
   then give the Chair the path to `<root>/board/index.html`. To regenerate
   manually: `bin/senate-chair board`. To use the interactive board, run
   `bin/senate-chair serve --host 127.0.0.1 --port 8765`.
5. **Briefing.** Run `bin/senate-chair brief`, synthesize the returned JSON
   into a briefing of 200 words or fewer, save it to
   `<root>/briefings/YYYY-MM-DD.md`, and show it.
6. **Actions.** Draft replies from `references/answer-bank.md` in the
   Chair's voice using `references/voice.md` and
   `assets/reply-template.md`; save unsent drafts only, and log the draft in
   the case. Handle scheduling per `references/account-access.md`; the Chair
   confirms every event change.

## Hard Rules

- On-prem models only: never process Chair mail, Drive, calendar, case, or
  answer-bank content on a model that is not a UCSD-hosted on-prem model.
  Never hard-code or assume a model name or version; verify against the
  current harness environment.
- Senate business runs on the Senate Chair Outlook account. The Chair's
  personal university account is not used for Senate business. Never touch
  any other shared, delegated, or departmental mailbox or calendar.
- The linked shared Google Drive is the main document repository. Read only
  that folder; store only its name and ID during setup, never credentials or
  OAuth tokens.
- Store only account labels, display addresses, and repository names/IDs
  during setup; never store credentials or OAuth tokens.
- Never send email or invitations. Unsent drafts and Chair-confirmed
  calendar changes only.
- All case data stays under the Chair's data root. Never upload Chair
  content to Drive or any external service unless the Chair explicitly asks
  and confirms the destination.
- Keep the board local. Serve it only on `127.0.0.1`; never expose it on a
  network interface. The data root uses owner-only directory and file
  permissions.
- Do not fabricate deadlines, owners, or case links. Every extracted
  deadline cites its verbatim source sentence.
- Flag medium- and low-confidence case links for review instead of blocking
  intake.
- Only `references/answer-bank.md` is authoritative for Senate answers. Do
  not invent policy, timelines, or procedures. An empty or incomplete bank
  means "no match," not permission to improvise.
- If an answer-bank entry's last-reviewed date is more than 12 months old,
  flag it "verify before use" and show the date.
- For any topic in `references/routing.md`, create the case, mark it
  confidential and routed, and draft at most a brief acknowledgment.
- Keep message content out of any file outside the data root unless the
  Chair explicitly asks to save a new answer-bank entry.
- Use placeholders such as `[Faculty member]` for names in drafts unless the
  message itself establishes the name the Chair uses.
