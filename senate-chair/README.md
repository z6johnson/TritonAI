# Senate Chair Skill

This folder packages the **Senate Chair** local operations skill for
TritonAI Harness: guided setup, Senate Chair Outlook linking, shared Google
Drive linking, mail/Drive/folder/pasted intake, case management, a local
Kanban board, and a daily briefing.

## Designed for non-technical users

The Chair never installs dependencies, writes Python, or runs CLI commands.
Everything is driven by natural-language prompts:

```text
Use $senate-chair to initialize my data root and process new materials.
```

On first use the assistant runs `bin/senate-chair doctor`, which verifies the
runtime and links. If Python is missing, the assistant installs it
automatically (`uv python install 3.12` or `brew install python@3.12`); all
skill functionality is packaged behind the single `senate-chair` command.

## Setup experience

Setup asks three questions and verifies the links:

1. **Email account** — recommend the **Senate Chair Outlook account**. Also
   offer the personal university Outlook account, Gmail, or intake-folder-only.
   The assistant shows the connected account address and asks for one
   confirmation before linking.
2. **Document repository** — the Chair names the shared Google Drive (or
   pastes a link); the assistant searches Drive, shows matches, and links the
   confirmed folder.
3. **Data root** — defaults to `~/SenateChair`.

The skill stores only labels, display addresses, and the Drive folder
name/ID — never credentials or OAuth tokens.

## Local actions

- **Process:** `Use $senate-chair to process my new materials.`
- **Board:** `Use $senate-chair to view my board.`
- **Briefing:** `Use $senate-chair to run my daily briefing.`
- **Link Drive:** `Use $senate-chair to link my shared Google Drive repository.`
- **Status:** `Use $senate-chair to show my setup status.`

The assistant-side command surface is documented in
`references/harness-actions.md` and `references/case-format.md`.

## Assistant commands

All functionality is packaged as one command, run through `bin/senate-chair`
(or `senate-chair` after `install-command`): `doctor`, `setup`, `new-item`,
`process` (legacy JSON), `link-drive`, `triage`, `board`, `brief`, `list`,
`mark`, `serve`, `status`, and `install-command`. Item intake uses the
single-command `new-item` flow — no JSON files or copy/paste.

## Distribution

Package this folder:

```bash
cd senate-chair && zip -r ../senate-chair.zip . -x "*.DS_Store" "*/__pycache__/*" "*.pyc"
```

Install it by unzipping it into `$CODEX_HOME/skills/senate-chair/`, or share
the repository folder path through the Harness skill installer.
