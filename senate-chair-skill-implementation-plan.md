# Senate Chair Skill Implementation Plan

Date: September 29, 2026

## Recommendation

Build `senate-chair` as a full operations skill for the TritonAI Harness: a local-first intake, case-management, visual-board, and daily-briefing system for the Senate Chair, with reply drafting and scheduling built in as case actions.

Materials — emails from the Chair's own mailbox, memos and reports dropped into an intake folder, or pasted text — are processed instantly into concise summaries with topic labels and extracted deadlines. Each item is linked to a case: new issues open new cases, updates append to existing ones. Leadership sees a Kanban-style board instead of an inbox, and every morning the skill produces a short synthesized briefing of the most urgent deadlines and bottlenecks.

All state stays in a Chair-owned local data root. Mail and calendar access runs through the Chair's own connected account only, never a shared mailbox. Processing runs only on approved UCSD on-prem models. Email is draft-only; the Chair always makes the final send decision.

## Decisions Already Made

- Five components: intake, AI processing, case management, visual dashboard, daily briefing. Reply drafting and scheduling are case actions inside this system, not the whole product.
- Intake accepts three source types: the Chair's own mailbox, new files in a local `intake/` folder, and pasted text.
- AI processing instantly produces a concise summary, one topic label from a fixed taxonomy, extracted deadlines with source wording, a priority, and a proposed case link.
- Cases are the unit of work. New issue: new case. Update to a known issue: item appended to the existing case. Low-confidence links are flagged for review, not blocked.
- Board statuses: Received (entered, not yet triaged), Active (owned, in progress), Pending (awaiting another unit), Resolved.
- The dashboard is a self-contained local HTML file generated from the case store; no external services or project-management SaaS.
- The daily briefing runs on demand and via a scheduled morning Harness run; it synthesizes urgent deadlines and bottlenecks.
- Mail and calendar access uses the Chair's own connected account only; never a shared, delegated, or departmental mailbox.
- Email is draft-only: the skill may search and read the Chair's mail and save unsent drafts, but never sends.
- Calendar reads are unrestricted; creating or changing an event requires explicit Chair confirmation.
- The skill runs only on approved UCSD on-prem models; the approved list lives in `references/model-policy.md`, and non-approved models are refused before any Chair content is read.
- The answers drafted and approved in the planning conversation are the seed content for the answer bank; copy them in verbatim.
- The skill does not improvise policy. Only the approved answer bank is authoritative; novel topics are flagged and routed.
- Sensitive topics (grievances, personnel disputes, legal, misconduct) are routed, not answered; their cases are marked confidential.
- The skill is self-contained: bundled Python scripts handle state integrity; no MCP dependencies beyond the Chair's environment's built-in mail and calendar integrations.

## Scope

### In Scope

- Intake from the Chair's own mailbox, a local `intake/` folder, and pasted text.
- Instant per-item processing: summary, topic label, deadline extraction, priority, case-link proposal.
- Case creation, linking, status and owner tracking, deadline tracking, and per-case logs.
- Kanban-style board generation: Received, Active (with owner), Pending (with waiting time), Resolved.
- Daily briefing: urgent deadlines, bottlenecks, new items, suggested first actions.
- Drafting replies to recurring faculty questions from the approved answer bank.
- Searching and reading the Chair's own connected mailbox; saving unsent reply drafts.
- Reading, creating, and editing events on the Chair's own calendar with confirmation.
- Triage flags and routing suggestions for out-of-scope topics.
- Proposing new answer-bank entries after the Chair resolves a new question.

### Out of Scope

- Shared, delegated, or departmental mailboxes and calendars.
- Sending email, invites, or messages on the Chair's behalf.
- Running on commercial cloud or other non-approved models.
- External project-management or ticketing services; all state is local.
- Personnel cases, grievances, investigations, or legal matters; these are routed and marked confidential.
- Automatically editing the answer bank without Chair approval.
- Live lookups of Senate policy; the bank is the source of truth for v1.

## Architecture

All state lives in a Chair-owned data root (default `~/SenateChair/`), created by the skill on first run:

```text
<root>/
├── intake/                  # Chair drops memos, reports, PDFs here
├── cases/
│   └── SC-2026-001/
│       ├── case.md          # metadata, deadlines, log, item index
│       └── items/
│           └── 2026-09-29-001.md
├── board/
│   └── index.html           # generated Kanban dashboard
├── briefings/
│   └── 2026-09-29.md
└── config.md                # root settings, taxonomy overrides, last-mail-run timestamp
```

Flow:

```text
Chair mailbox (own account) ─┐
intake/ folder ──────────────┼──> AI processing: summary, topic, deadlines, priority
pasted text ─────────────────┘         │
                                       ▼
                             case linking: new case or existing case
                                       │
                                       ▼
                       case store ──> Kanban board (local HTML)
                                       │
                                       ▼
                          daily briefing (deadlines + bottlenecks)
```

Division of labor:

- **Model (judgment):** reads materials, writes summaries, labels topics, extracts deadlines, proposes case links and owners, drafts replies, synthesizes briefings.
- **Scripts (state integrity):** validate and persist items and cases, enforce IDs, topics, statuses, and deadline formats, regenerate the board, and assemble briefing data. Scripts never touch the network and never send anything.

### 1. Intake

- **Mail:** search the Chair's own mailbox for messages received after the last processed timestamp stored in `config.md`. Read headers and bodies only; never send, forward, or delete. If no mail integration is connected, skip and say so.
- **Files:** process anything new in `<root>/intake/` (memos, reports, PDFs, documents). After processing, leave originals in place; the item file records the source path.
- **Pasted:** the Chair pastes material directly into the conversation.
- Every material becomes exactly one item file with a stable ID, source reference (message ID, file path, or `pasted`), and received date.

### 2. AI Processing (instant, per item)

Produce and persist:

- A concise summary (120 words or fewer).
- Exactly one topic label from `references/taxonomy.md`.
- Every deadline mentioned, normalized to `YYYY-MM-DD`, each with the verbatim source sentence it came from.
- A priority from the taxonomy.
- A proposed case link: new case, or existing case ID with a confidence level (high / medium / low) and a one-line reason.
- A suggested owner and next action, proposed only — the Chair confirms triage.

### 3. Case Management

- A case is one issue. `case.md` holds status, topic, owner, opened date, last update, next action, deadlines, review flags, a log, and the item index.
- New issue: the script creates a new case in `Received` with everything from processing filled in and the suggested owner noted. The Chair confirms owner and next action to move it to `Active`.
- Update to a known issue: the item is appended to the existing case; deadlines, last-update, and status are refreshed, and a log entry is added.
- Linking logic: match on same topic plus overlapping entities (unit, committee, person, project, budget line) plus an open case. High confidence links automatically; medium and low links attach with a `review` flag and surface on the board.
- Sensitive topics from `references/routing.md` still get a case, marked `confidential` and `routed`, with no substantive answer drafted.

### 4. Visual Dashboard

- `python3 scripts/senate_chair.py board --root <root>` regenerates `board/index.html` from the case files after every change and on demand.
- Kanban columns: **Received** (not yet triaged), **Active** (with owner), **Pending** (with days waiting), **Resolved**.
- Each card shows: case ID, title, topic chip, owner, next deadline (red at 3 days or fewer, amber at 7 or fewer), days since last update, and any review flag.
- The HTML is self-contained (inline CSS, no scripts loaded from the network), so the Chair can open it in any browser or share the file as a snapshot.

### 5. Daily Briefing

- `python3 scripts/senate_chair.py brief --root <root>` returns structured data: deadlines in the next 7 days, Pending cases ranked by days waiting, Active cases with no update in 5+ days, and items received since the last briefing.
- The model synthesizes that into a short briefing (200 words or fewer): the most urgent deadlines, the biggest bottlenecks, and two or three suggested first actions.
- Saved to `<root>/briefings/YYYY-MM-DD.md` and shown in the conversation.
- Runs on demand ("run my daily briefing") and via a scheduled Harness run each morning at the Chair's preferred time.

### Case Actions (retained functionality)

- **Draft reply:** match the item to an approved answer, draft in the Chair's voice, optionally save as an unsent draft in the Chair's own mailbox, and link the draft to the case log.
- **Schedule:** read the Chair's calendar for availability; propose event details; create or change events only after the Chair confirms.
- **Route:** apply `references/routing.md` for topics the skill must not answer substantively.

## Skill Package

```text
senate-chair/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── workflow.md
│   ├── account-access.md
│   ├── model-policy.md
│   ├── taxonomy.md
│   ├── case-format.md
│   ├── answer-bank.md
│   ├── routing.md
│   └── voice.md
├── scripts/
│   └── senate_chair.py
└── assets/
    ├── reply-template.md
    └── dashboard-template.html
```

Scripts are now included because state integrity is fragile and consistency matters: IDs, schemas, status transitions, and board generation belong in code. Judgment stays in the model.

## File Contents

### 1. `SKILL.md` (paste-ready draft)

```markdown
---
name: senate-chair
description: Run Senate Chair operations. Intake materials from the Chair's own email, an intake folder, or pasted text; instantly summarize and label them; extract deadlines; manage cases on a Kanban board; generate a daily deadline-and-bottleneck briefing; draft replies from an approved answer bank; and manage the Chair's own calendar. Use when the Senate Chair or their delegate asks to process new materials, triage or find a case, view the board, run the daily briefing, draft a reply, or handle Chair scheduling.
---

# Senate Chair

A local-first operations system for the Senate Chair: intake, case management, a visual board, and a daily briefing, with reply drafting and scheduling as case actions. The skill acts only on the Chair's personal connected account and only on approved on-prem models.

## Model Policy

1. Read `references/model-policy.md` first. Verify the session's selected model is on the approved on-prem list before touching any Chair content. If it is not, stop and name the approved models.

## Setup

1. If the data root does not exist, create it: `python3 scripts/senate_chair.py init --root <root>`.
2. Use the same root for every command. Store preferences and the last-mail-run timestamp in `<root>/config.md`.

## Workflow

1. **Intake.** Read `references/workflow.md`. Collect new materials from the Chair's own mailbox (per `references/account-access.md`), new files in `<root>/intake/`, and pasted text. Each material becomes one item.
2. **Process.** For each item, produce a summary of 120 words or fewer, one topic label from `references/taxonomy.md`, every deadline normalized to YYYY-MM-DD with its verbatim source sentence, a priority, a suggested owner, and a proposed case link. Persist with `scripts/senate_chair.py`.
3. **Cases.** New issues open new cases in `Received`; updates append to existing cases. Confirm the Chair's owner and next-action decisions, then update status per `references/case-format.md`.
4. **Board.** Regenerate the dashboard after every case change: `python3 scripts/senate_chair.py board --root <root>`. Give the Chair the path to `<root>/board/index.html`.
5. **Briefing.** Run `python3 scripts/senate_chair.py brief --root <root>`, synthesize the returned data into a briefing of 200 words or fewer, save it to `<root>/briefings/YYYY-MM-DD.md`, and show it.
6. **Actions.** Draft replies from `references/answer-bank.md` in the Chair's voice using `references/voice.md` and `assets/reply-template.md`; save unsent drafts only. Handle scheduling per `references/account-access.md`; the Chair confirms every event change.

## Hard Rules

- On-prem models only: never process Chair mail, calendar, case, or answer-bank content on a model outside the approved list in `references/model-policy.md`.
- Own account only: never a shared, delegated, or departmental mailbox or calendar.
- Never send email or invitations. Unsent drafts and Chair-confirmed calendar changes only.
- All case data stays under the Chair's data root. Never upload Chair content to any external service.
- Do not fabricate deadlines, owners, or case links. Every extracted deadline cites its verbatim source sentence.
- Flag medium- and low-confidence case links for review instead of blocking intake.
- Only `references/answer-bank.md` is authoritative for Senate answers. Do not invent policy, timelines, or procedures.
- If an answer-bank entry's last-reviewed date is more than 12 months old, flag it "verify before use" and show the date.
- For any topic in `references/routing.md`, create the case, mark it confidential and routed, and draft at most a brief acknowledgment.
- Keep message content out of any file outside the data root unless the Chair explicitly asks to save a new answer-bank entry.
- Use placeholders such as `[Faculty member]` for names in drafts unless the message itself establishes the name the Chair uses.
```

### 2. `agents/openai.yaml`

```yaml
interface:
  display_name: "Senate Chair Assistant"
  short_description: "Intake, cases, board, and daily briefing"
  default_prompt: "Use $senate-chair to process my new materials and show my board."
policy:
  allow_implicit_invocation: false
```

`allow_implicit_invocation: false` makes the skill explicit-invocation only (`$senate-chair`), which reduces the chance it runs by accident on a non-approved model.

### 3. `references/workflow.md`

The end-to-end procedure:

```markdown
# Senate Chair Workflow

## Intake

1. Mail: search the Chair's own mailbox for messages received after the last-mail-run timestamp in `config.md`. Update the timestamp only after all new messages are processed.
2. Files: list unprocessed files in `<root>/intake/` and process each. Leave originals in place.
3. Pasted: treat pasted text as one item with source `pasted`.

## Processing (every item)

1. Summarize in 120 words or fewer.
2. Assign exactly one topic label from `taxonomy.md`.
3. Extract every deadline as YYYY-MM-DD with the verbatim source sentence.
4. Assign a priority: Urgent (deadline within 3 days or Chair-directed), High, Normal, Low.
5. Propose an owner and next action. Proposals only; the Chair confirms triage.
6. Propose a case link:
   - Same topic plus overlapping entities (unit, committee, person, project, budget line) plus an open case: link to that case.
   - High confidence: link automatically. Medium or low: link with a review flag.
   - No open case matches: propose a new case with a one-line title.

## Triage

- Received: case exists, no confirmed owner or next action.
- Active: Chair confirmed owner and next action.
- Pending: waiting on another unit; record which unit and the date requested.
- Resolved: Chair confirms closure; record the resolution in the log.

## Board and briefing

- Regenerate the board after every item or case change.
- Briefing data: deadlines within 7 days, Pending cases by days waiting, Active cases untouched for 5+ days, new items since the last briefing.
```

### 4. `references/taxonomy.md`

```markdown
# Topic Taxonomy

Use exactly one topic per item. The Chair may extend this list in `config.md`.

## Topics

Budget; Faculty Affairs; Academic Personnel; Governance and Bylaws; Curriculum; Student Matters; Research Administration; Facilities and Space; Communications and Media; Government and External Relations; Events and Ceremonies; Awards and Recognition; Other.

## Statuses

Received; Active; Pending; Resolved.

## Priorities

- Urgent: deadline within 3 days or explicitly flagged by the Chair.
- High: significant stake or hard deadline within 2 weeks.
- Normal: standard business.
- Low: informational or no action required.
```

### 5. `references/case-format.md`

```markdown
# Case and Item Formats

## case.md

# SC-2026-001: <one-line title>
- Status: Received | Active | Pending | Resolved
- Topic: <taxonomy label>
- Owner: <name or unit, or "unassigned">
- Opened: YYYY-MM-DD
- Last update: YYYY-MM-DD
- Next action: <one line, or "awaiting triage">
- Review flag: <blank | new case unreviewed | auto-link low confidence | confidential>

## Deadlines
| Deadline | Source sentence | Item | Done |
|---|---|---|---|

## Log
- YYYY-MM-DD: <what changed>

## Items
- 2026-09-29-001: <one-line summary>

## Item file

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

### 6. `references/account-access.md`

```markdown
# Chair Account Access

The skill may use the mail and calendar integration connected to the Chair's own UCSD account. It must never touch a shared, delegated, or departmental mailbox or calendar.

## Platforms

- If the Chair uses Gmail: use the Gmail and Google Calendar skills.
- If the Chair uses Outlook: use the Outlook mail and Outlook calendar skills.
- Use whichever integration is actually connected; do not assume a platform.

## Mail

- Search and read the Chair's own mailbox for intake and for messages the Chair refers to.
- Draft replies in the conversation first; save to the mailbox only as an unsent draft when the Chair asks.
- Never send, reply, reply-all, forward, or delete.
- Treat message content as confidential; do not quote it into any file outside the data root.

## Calendar

- Read the Chair's calendar to answer availability and schedule questions.
- Before creating or changing an event, show the Chair the full details: title, date, time, attendees, and location.
- Create or change the event only after the Chair confirms. Note that invitations go to attendees when the event is saved.
- Never modify another person's calendar.

## Fallback

If no integration is connected, work from the intake folder and pasted text, and tell the Chair which capability is unavailable.
```

### 7. `references/model-policy.md`

```markdown
# On-Prem Model Policy

This skill handles Senate Chair correspondence, cases, and scheduling, so it runs only on models hosted on UCSD-controlled infrastructure. Do not use it with commercial cloud models.

## Approved models

- [TritonAI team fills in the approved on-prem model slugs, e.g. `api-glm-5.3`]

If this list is empty or unclear, treat the skill as unavailable and ask the Chair to confirm the approved models with the TritonAI team.

## Enforcement

1. Before any task, check the session's selected model against this list.
2. If the selected model matches, proceed.
3. If it does not match, stop. Do not read mail, files, calendar, or case content. Tell the Chair: "This skill is limited to UCSD on-prem models. Switch to an approved model and try again."
4. If the selected model cannot be verified, say so and stop.

## Data boundary

- Mail, calendar, case, and answer-bank content stays within the approved on-prem model session.
- Do not send Chair content to any other model, service, or endpoint.
```

### 8. `references/answer-bank.md`

One entry per approved answer, in this format:

```markdown
# Senate Chair Answer Bank

Entries are the Chair's approved answers. Do not edit an answer without Chair approval.

## <Topic title>
- ID: SC-001
- Triggers: <phrases faculty actually use when asking this>
- Status: approved
- Last reviewed: YYYY-MM-DD
- Answer:

<approved answer, verbatim>

- Routing: <office or person to cc or defer to, if any>
- Cautions: <situations where this answer does not apply>
```

Build rules:

- Transfer each approved answer from the planning conversation into its own entry, verbatim.
- Give each a stable ID (`SC-001`, `SC-002`, ...) and a short topic title.
- List 2-4 trigger phrasings per entry, drawn from how faculty actually ask.
- Set `Last reviewed` to the date the Chair approved the answer.
- Fill `Routing` and `Cautions` only where they genuinely apply.

### 9. `references/routing.md`

```markdown
# Routing Guide

These topics still get a case, marked confidential and routed. Do not draft a substantive answer. Recommend the route and, if asked, draft only a brief acknowledgment.

| Topic | Route to | Notes |
|---|---|---|
| Grievances and personnel disputes | [confirm with Chair] | Never characterize a case |
| Harassment or discrimination reports | [confirm with Chair] | Preserve confidentiality |
| Legal threats or claims | [confirm with Chair] | Route through administration |
| Media inquiries | [confirm with Chair] | Use campus communications |
| Public records requests | [confirm with Chair] | Do not respond substantively |
| Safety emergencies | [confirm with Chair] | Act immediately per campus protocol |
```

### 10. `references/voice.md`

```markdown
# Senate Chair Voice

- Answer the question in the first sentence or two, then add context.
- Be concise, collegial, and plain-spoken; no filler or jargon.
- Write in first person as the Chair.
- Close with the next step, not a slogan.
- Preferred greeting: [fill in]
- Sign-off: [fill in]
- Phrases to favor: [fill in]
- Phrases to avoid: [fill in]
- Tone for declines or reroutes: warm but unambiguous, and name the right next door.
```

### 11. `assets/reply-template.md`

```markdown
Subject: Re: <original subject, if replying by email>

<One-line acknowledgment of the question.>

<The answer, adapted from the approved entry.>

<Next step or routing sentence, if needed.>

<Sign-off from voice.md>
```

### 12. `assets/dashboard-template.html`

A self-contained Kanban shell the script fills with case cards:

- Inline CSS only; no external fonts, scripts, or network requests.
- Four columns: Received, Active, Pending, Resolved.
- Card fields: case ID, title, topic chip, owner, next deadline with color coding (red ≤3 days, amber ≤7 days), days since last update, review flag badge.
- Pending cards also show the unit being waited on and days waiting.
- A header with the generation timestamp and counts per column.

### 13. `scripts/senate_chair.py`

One offline CLI, standard library only. The model passes structured payloads; the script validates and writes. It must never make a network request.

Subcommands:

- `init --root <path>`: create the folder structure and `config.md`.
- `process --root <root> --payload <json>`: validate a processed item (summary, topic, priority, deadlines with source sentences, source reference, received date, case proposal) against the taxonomy; write the item file; create a new case or append to an existing one; update deadlines, last-update, and log; regenerate the board; print the case ID and any review flags. Reject unknown topics, malformed dates, deadlines without source sentences, and paths outside the root.
- `triage --root <root> --case <id> [--status <s>] [--owner <o>] [--next-action <text>] [--pending-unit <unit>]`: update a case with Chair-confirmed decisions and regenerate the board.
- `board --root <root>`: regenerate `board/index.html` from all case files using the dashboard template.
- `brief --root <root> [--date <YYYY-MM-DD>]`: print a JSON skeleton: deadlines within 7 days, Pending cases by days waiting, Active cases untouched 5+ days, and items received since the last briefing.
- `list --root <root> [--status <s>] [--topic <t>]`: list cases with ID, title, status, owner, and next deadline.

Build rules:

- Enforce sequential case IDs (`SC-2026-001`, `SC-2026-002`, ...) and item IDs (`YYYY-MM-DD-NNN`).
- Keep every write inside the data root.
- Fail loudly on invalid payloads; never guess or silently repair data.
- Test every subcommand against a fixture root before packaging.

## Content to Supply Before Packaging

1. The approved answers from the planning conversation: the seed entries for `answer-bank.md`.
2. The Chair's greeting, sign-off, and voice preferences for `voice.md`.
3. Confirmed routing contacts for `routing.md`.
4. The Chair's mail and calendar platform (Gmail or Outlook), so `account-access.md` names the right integrations.
5. The approved on-prem model list from the TritonAI team, for `model-policy.md`.
6. The Chair's preferred data root location and the list of owners/units that can hold cases.
7. The Chair's preferred briefing time for the scheduled morning run.
8. Optional: any additional recurring questions the Chair wants seeded into v1.

## Build Steps

1. Create the `senate-chair/` folder structure shown above.
2. Add `SKILL.md` and `agents/openai.yaml` from this plan.
3. Add all `references/` files and `assets/` files from this plan.
4. Implement `scripts/senate_chair.py` to the subcommand spec, then test each subcommand against a fixture root: `init`, `process` a new case, `process` an update to that case, `triage`, `board`, `brief`, and `list`.
5. Transfer the approved answers into the answer bank using the entry format.
6. Validate the skill:

   `python3 ~/.tritonai-harness/codex/skills/.system/skill-creator/scripts/quick_validate.py senate-chair/`

7. Run the acceptance tests below in fresh Harness threads.
8. Fix anything the tests surface, then package and share.

## Acceptance Tests

Run each in a fresh conversation with only the skill invoked:

1. **New material to new case.** Paste a memo with a deadline. Pass: item file created with summary, one topic label, and the deadline with its source sentence; a new case opens in `Received` with a suggested owner; the board regenerates.
2. **Update to existing case.** Paste a follow-up email on the same issue. Pass: the item appends to the existing case, deadlines refresh, no duplicate case is created, and the log records the update.
3. **Deadline extraction.** A memo saying "comments are due October 15" produces `2026-10-15` with that sentence quoted. Invented or unsourced deadlines fail the test.
4. **Triage.** Confirm an owner and next action. Pass: the case moves to `Active`, the board card shows the owner, and `Pending` records the unit and days waiting when used.
5. **Board.** With mixed fixtures, `board/index.html` shows the correct columns, owners, deadline colors, and review flags, with no network requests.
6. **Daily briefing.** With fixtures, the briefing lists deadlines within 7 days, aged `Pending` cases, and stalled `Active` cases, in 200 words or fewer, saved to `briefings/`.
7. **Matched reply.** Paste a faculty question matching a bank entry. Pass: draft uses the approved substance and voice, shows the entry ID, links to the case, and sends nothing.
8. **No match.** A plausible question with no bank entry. Pass: no improvised policy; closest entries and routing offered.
9. **Routed topic.** A message alleging a grievance. Pass: a confidential, routed case is created; no substantive answer; at most a brief acknowledgment.
10. **Mailbox intake.** Ask the skill to process new mail. Pass: it reads only the Chair's own mailbox after the stored timestamp, processes new messages, updates the timestamp, and sends nothing.
11. **Calendar.** Ask about availability, then request a meeting. Pass: correct read; the event is created only after the Chair confirms details and attendees.
12. **Shared mailbox refusal.** Ask the skill to check the shared Senate mailbox. Pass: it declines and explains it is limited to the Chair's own account.
13. **On-prem enforcement.** Start a session on a non-approved model and invoke the skill. Pass: it stops without reading anything, names the approved models, and tells the Chair to switch.
14. **Stale answer.** Set an entry's review date older than 12 months. Pass: the draft is flagged "verify before use" with the date shown.

## Packaging and Import

- Package: `zip -r senate-chair.zip senate-chair/`
- Share the zip with the Chair, or push the folder to a GitHub repo the Chair can reach.
- The Chair imports it into their Harness environment either by unzipping into their skills directory (`$CODEX_HOME/skills/senate-chair/`) or, if shared via GitHub, by asking their Harness to install it with the skill installer.
- After import, the Chair connects their own mail and calendar integration (Gmail or Outlook) and confirms the skill can read their inbox and calendar.
- Set the Chair's Harness default model to an approved on-prem model before first use.
- Create a scheduled Harness run at the Chair's preferred morning time with the prompt: "Use $senate-chair to run my daily briefing."
- Confirm the skill appears on the Chair's next turn, then run acceptance tests 1, 5, and 6 together.

## Maintenance

- The Chair owns the answers and the case store. Update answer-bank entries only with their approval, and reset `Last reviewed` on any change.
- Add an answer-bank entry whenever the Chair resolves a new recurring question.
- Review the topic taxonomy each term; add labels only through `config.md` so existing cases stay valid.
- Review the whole bank at least once per academic year and after any Senate policy or bylaw change.
- Keep versions in the sharing repo so the Chair can update by reinstalling.
