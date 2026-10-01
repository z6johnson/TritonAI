# Shared Google Drive Repository

The Chair's main document repository is a shared Google Drive. Link it once
during setup so intake can include repository documents alongside mail, the
local intake folder, and pasted text.

## Linking during setup (ease of use)

1. Ask the Chair one question: "Which shared Google Drive is the main Senate
   Chair document repository?" The Chair may answer with a name, a folder
   name, or a link.
2. Use the `google-drive` skill to search Drive for matching folders and show
   the top matches.
3. Ask the Chair to confirm the correct one with a single click or yes.
4. Record the confirmed folder with setup:

```bash
bin/senate-chair setup --root <root> --account outlook-chair \
  --drive-name "<confirmed folder name>" --drive-id "<folder id>"
```

Or link it on an already-initialized root:

```bash
bin/senate-chair link-drive --name "<confirmed folder name>" --drive-id "<folder id>"
```

Setup stores only the folder name and ID. Google credentials and OAuth tokens
stay in the Harness integration; the skill never stores them.

## Using the repository

- During intake, list new or updated documents in the linked folder since the
  `Last drive run` date in `config.md`.
- Read documents with the `google-drive` skill; summarize into the local data
  root and link each item back to its source document. Use
  `new-item --source-type file --ref "<Drive file name or ID>"`.
- After processing Drive documents, record the run:

```bash
bin/senate-chair mark --drive-run YYYY-MM-DD
```

## Boundaries

- The linked repository is the only Drive location this skill reads.
- Case data, summaries, and briefings stay in the local data root.
- Never upload case content or generated files to Drive unless the Chair
  explicitly asks, and confirm the destination folder first.
