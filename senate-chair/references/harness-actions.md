# Harness Actions

These prompts are the entire user-facing surface. The Chair never runs CLI
commands; the assistant executes the packaged `senate-chair` commands
behind these prompts. The default skill chip uses the first prompt.

All assistant-side commands go through the wrapper at `bin/senate-chair`
(or `senate-chair` after `install-command`), never through raw Python
invocations.

## Initialize and process

```text
Use $senate-chair to initialize my data root and process new materials.
```

1. Verify the model policy first.
2. Run the deployment check:

```bash
bin/senate-chair doctor
```

   If it reports that Python is missing, install it automatically (`uv
   python install 3.12`, or `brew install python@3.12` on macOS), then
   re-run `doctor`. The Chair should never be asked to install anything.

3. If the data root is uninitialized, ask only:
   - the email account: `Senate Chair Outlook account (recommended)`,
     `Personal university Outlook account`, `Gmail`, or `Intake folder and
     pasted text only`
   - the shared Google Drive repository: search Drive for the Chair's
     answer, show matches, and let the Chair confirm one
   - the data root, defaulting to `~/SenateChair`
4. Verify the connected Outlook account matches the Chair's choice per
   `references/account-access.md`.
5. Run one command with the confirmed choices:

```bash
bin/senate-chair setup --root <root> --account <outlook-chair|outlook-personal|gmail|none> \
  [--account-address <address>] [--drive-name <name>] [--drive-id <id>]
```

6. Optionally install the short command for later turns:

```bash
bin/senate-chair install-command
```

7. Continue directly into the normal intake workflow.

## Process

```text
Use $senate-chair to process my new materials.
```

Collect new mail from the linked account, new documents from the linked
Drive repository, new files in `<root>/intake/`, and pasted text. For each
item, run one command (no JSON files, no copy/paste):

```bash
bin/senate-chair new-item --source-type <email|file|pasted> [--ref <reference>] \
  --summary "<120 words or fewer>" --topic "<taxonomy label>" --priority <priority> \
  [--deadline "YYYY-MM-DD|verbatim source sentence"] \
  --case-action <new|existing> [--case-id <id> | --case-title "<title>"] \
  --confidence <high|medium|low> --reason "<why>" \
  [--suggested-owner <owner>] [--suggested-next-action <action>] [--confidential]
```

After the mail batch, record it with `mark --mail-run YYYY-MM-DD`; after the
Drive batch, record it with `mark --drive-run YYYY-MM-DD`.

## View board

```text
Use $senate-chair to view my board.
```

```bash
bin/senate-chair board
```

Then open `<root>/board/index.html` locally. In TritonAI Harness, use the
collaborative preview browser when available; on macOS, `open <root>/board/index.html`
also works. For drag-and-drop editing, use `serve` and keep the server bound
to `127.0.0.1`.

## Daily briefing

```text
Use $senate-chair to run my daily briefing.
```

```bash
bin/senate-chair brief
```

Synthesize the returned JSON into 200 words or fewer, include two or three
suggested first actions, save it to `<root>/briefings/YYYY-MM-DD.md`, and
show it.

## Link the document repository

```text
Use $senate-chair to link my shared Google Drive repository.
```

Search Drive for the Chair's named folder, confirm the match, then:

```bash
bin/senate-chair link-drive --name "<folder name>" --drive-id "<folder id>"
```

## Status and health

```text
Use $senate-chair to show my setup status.
```

```bash
bin/senate-chair status
bin/senate-chair doctor
```

The remembered root is stored in `~/.senate-chair/root`. That pointer
contains only the local path, never Chair content. Override it for one
command with `--root` or for a session with `SENATE_CHAIR_ROOT`.
