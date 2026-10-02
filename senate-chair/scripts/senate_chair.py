#!/usr/bin/env python3
"""Senate Chair local case management commands.

Offline, standard library only. The AI layer produces structured payloads;
this tool validates them and maintains the case store, board, and briefing
data. It never makes a network request and never sends anything.

Users never invoke this module directly. The `bin/senate-chair` wrapper
resolves a suitable Python interpreter and forwards every subcommand.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

STATUSES = ["Received", "Active", "Pending", "Resolved"]
PRIORITIES = ["Urgent", "High", "Normal", "Low"]
CONFIDENCE_LEVELS = ["high", "medium", "low"]
SOURCE_TYPES = ["email", "file", "pasted"]
ACCOUNT_TYPES = ["outlook-chair", "outlook-personal", "gmail", "none"]
ACCOUNT_CHOICES = ACCOUNT_TYPES + ["outlook"]
ACCOUNT_LABELS = {
    "outlook-chair": "Outlook — Senate Chair account",
    "outlook-personal": "Outlook — personal university account",
    "gmail": "Gmail",
    "none": "Intake folder and pasted text",
}
BUILT_IN_TOPICS = [
    "Budget",
    "Faculty Affairs",
    "Academic Personnel",
    "Governance and Bylaws",
    "Curriculum",
    "Student Matters",
    "Research Administration",
    "Facilities and Space",
    "Communications and Media",
    "Government and External Relations",
    "Events and Ceremonies",
    "Awards and Recognition",
    "Other",
]
META_KEYS = [
    "Status",
    "Topic",
    "Owner",
    "Suggested owner",
    "Opened",
    "Last update",
    "Next action",
    "Review flag",
    "Pending unit",
    "Pending since",
    "Confidential",
]
CASE_HEADING_RE = re.compile(r"^(SC-\d{4}-\d{3}):\s*(.*)$")
ITEM_ENTRY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{3}):\s*(.*)$")
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CASE_ID_RE = re.compile(r"^SC-\d{4}-\d{3}$")


def secure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def secure_write_text(path: Path, text: str) -> None:
    secure_directory(path.parent)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)


def secure_data_root(root: Path) -> None:
    secure_directory(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        parent = Path(dirpath)
        for dirname in dirnames:
            directory = parent / dirname
            if not directory.is_symlink():
                directory.chmod(0o700)
        for filename in filenames:
            file_path = parent / filename
            if not file_path.is_symlink() and file_path.is_file():
                file_path.chmod(0o600)


def root_pointer_path() -> Path:
    return Path.home() / ".senate-chair" / "root"


def read_root_pointer() -> Path | None:
    pointer = root_pointer_path()
    if not pointer.is_file():
        return None
    value = pointer.read_text(encoding="utf-8").strip()
    return Path(value).expanduser().resolve() if value else None


def write_root_pointer(root: Path) -> None:
    pointer = root_pointer_path()
    pointer.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    pointer.parent.chmod(0o700)
    pointer.write_text(f"{root}\n", encoding="utf-8")
    pointer.chmod(0o600)


def resolve_root(value: str | None = None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    environment_root = os.environ.get("SENATE_CHAIR_ROOT")
    if environment_root:
        return Path(environment_root).expanduser().resolve()
    pointer_root = read_root_pointer()
    if pointer_root:
        return pointer_root
    return Path.home() / "SenateChair"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def emit(payload: dict | list) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def parse_iso_date(value, label: str = "date") -> date:
    text = str(value).strip()
    if not DATE_ONLY_RE.match(text):
        fail(f"Invalid {label}: {value!r} (expected YYYY-MM-DD)")
    try:
        return date.fromisoformat(text)
    except ValueError:
        fail(f"Invalid {label}: {value!r}")


def require_root(root: Path) -> None:
    config = root / "config.md"
    if not config.is_file():
        fail(f"Data root is not initialized: {config} is missing. Run the init command first.")
    secure_data_root(root)


def load_config(root: Path) -> dict:
    text = (root / "config.md").read_text(encoding="utf-8")
    topics = list(BUILT_IN_TOPICS)
    last_mail_run = "none"
    last_briefing = "none"
    last_drive_run = "none"
    linked_account = "not configured"
    account_address = ""
    document_repository = ""
    document_repository_id = ""
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if section == "Extra topics" and line.startswith("- "):
            topic = line[2:].strip()
            if topic and topic not in topics:
                topics.append(topic)
        elif line.startswith("- Last mail run:"):
            last_mail_run = line.split(":", 1)[1].strip()
        elif line.startswith("- Last briefing:"):
            last_briefing = line.split(":", 1)[1].strip()
        elif line.startswith("- Last drive run:"):
            last_drive_run = line.split(":", 1)[1].strip()
        elif line.startswith("- Linked account:"):
            linked_account = line.split(":", 1)[1].strip()
        elif line.startswith("- Account address:"):
            account_address = line.split(":", 1)[1].strip()
        elif line.startswith("- Document repository:"):
            document_repository = line.split(":", 1)[1].strip()
        elif line.startswith("- Document repository ID:"):
            document_repository_id = line.split(":", 1)[1].strip()
    return {
        "topics": topics,
        "last_mail_run": last_mail_run,
        "last_briefing": last_briefing,
        "last_drive_run": last_drive_run,
        "linked_account": linked_account,
        "account_address": account_address,
        "document_repository": document_repository,
        "document_repository_id": document_repository_id,
    }


def update_config(root: Path, key: str, value: str) -> None:
    path = root / "config.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    needle = f"- {key}:"
    output = []
    found = False
    for line in lines:
        if line.startswith(needle):
            output.append(f"- {key}: {value}")
            found = True
        else:
            output.append(line)
    if not found:
        output.append("")
        output.append(f"- {key}: {value}")
    secure_write_text(path, "\n".join(output) + "\n")


def escape_cell(text: str) -> str:
    return text.replace("|", "\\|")


def unescape_cell(text: str) -> str:
    return text.replace("\\|", "|")


def parse_case_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    meta = {key: "" for key in META_KEYS}
    meta["Owner"] = "unassigned"
    deadlines: list[dict] = []
    log: list[str] = []
    items: list[str] = []
    case_id = ""
    title = ""
    section = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("# ") and not case_id:
            match = CASE_HEADING_RE.match(line[2:].strip())
            if match:
                case_id, title = match.group(1), match.group(2).strip()
            continue
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if line.startswith("- ") and section is None:
            body = line[2:]
            for key in META_KEYS:
                if body.startswith(f"{key}:"):
                    meta[key] = body[len(key) + 1 :].strip()
                    break
            continue
        if section == "Deadlines" and line.startswith("|"):
            cells = [unescape_cell(cell.strip()) for cell in line.strip().strip("|").split("|")]
            if len(cells) != 4:
                continue
            if cells[0] in ("Deadline", "") or set(cells[0]) <= {"-"}:
                continue
            deadlines.append(
                {"date": cells[0], "source": cells[1], "item": cells[2], "done": cells[3]}
            )
        elif section == "Log" and line.startswith("- "):
            log.append(line[2:].strip())
        elif section == "Items" and line.startswith("- "):
            items.append(line[2:].strip())
    if not case_id:
        return None
    case = {"id": case_id, "title": title, "path": str(path)}
    case.update(meta)
    case["deadlines"] = deadlines
    case["log"] = log
    case["items"] = items
    return case


def write_case_file(root: Path, case: dict) -> Path:
    case_dir = root / "cases" / case["id"]
    secure_directory(case_dir)
    secure_directory(case_dir / "items")
    path = case_dir / "case.md"
    lines = [f"# {case['id']}: {case['title']}", ""]
    for key in META_KEYS:
        value = case.get(key, "")
        if value != "":
            lines.append(f"- {key}: {value}")
    lines += ["", "## Deadlines"]
    if case["deadlines"]:
        lines.append("| Deadline | Source sentence | Item | Done |")
        lines.append("|---|---|---|---|")
        for entry in case["deadlines"]:
            lines.append(
                "| {date} | {source} | {item} | {done} |".format(
                    date=escape_cell(entry["date"]),
                    source=escape_cell(entry["source"]),
                    item=escape_cell(entry["item"]),
                    done=escape_cell(entry["done"]),
                )
            )
    else:
        lines.append("None yet.")
    lines += ["", "## Log"]
    if case["log"]:
        lines.extend(f"- {entry}" for entry in case["log"])
    else:
        lines.append("- None yet.")
    lines += ["", "## Items"]
    if case["items"]:
        lines.extend(f"- {entry}" for entry in case["items"])
    else:
        lines.append("- None yet.")
    secure_write_text(path, "\n".join(lines) + "\n")
    return path


def load_all_cases(root: Path) -> list[dict]:
    cases: list[dict] = []
    cases_dir = root / "cases"
    if not cases_dir.is_dir():
        return cases
    for child in sorted(cases_dir.iterdir()):
        case_path = child / "case.md"
        if case_path.is_file():
            case = parse_case_file(case_path)
            if case is not None:
                cases.append(case)
    return cases


def find_case(root: Path, case_id: str) -> dict:
    if not CASE_ID_RE.fullmatch(case_id):
        fail(f"Invalid case ID: {case_id!r} (expected SC-YYYY-NNN)")
    path = root / "cases" / case_id / "case.md"
    if not path.is_file():
        fail(f"Case not found: {case_id}")
    case = parse_case_file(path)
    if case is None:
        fail(f"Case file is unreadable: {path}")
    return case


def next_case_id(root: Path, today: date) -> str:
    year = today.year
    max_seq = 0
    cases_dir = root / "cases"
    if cases_dir.is_dir():
        for child in cases_dir.iterdir():
            match = re.match(r"^SC-(\d{4})-(\d{3})$", child.name)
            if match and int(match.group(1)) == year:
                max_seq = max(max_seq, int(match.group(2)))
    return f"SC-{year}-{max_seq + 1:03d}"


def next_item_id(root: Path, received: date) -> str:
    day = received.isoformat()
    pattern = re.compile(re.escape(day) + r"-(\d{3})\.md$")
    max_seq = 0
    items_dir = root / "cases"
    if items_dir.is_dir():
        for path in items_dir.glob("*/items/*.md"):
            match = pattern.search(path.name)
            if match:
                max_seq = max(max_seq, int(match.group(1)))
    return f"{day}-{max_seq + 1:03d}"


def headline_from_summary(summary: str) -> str:
    first_sentence = re.split(r"(?<=[.!?])\s+", summary.strip(), maxsplit=1)[0]
    if len(first_sentence) > 100:
        first_sentence = first_sentence[:97].rstrip() + "..."
    return first_sentence


def next_deadline(case: dict) -> dict | None:
    open_deadlines = [entry for entry in case["deadlines"] if entry["done"].lower() != "yes"]
    if not open_deadlines:
        return None
    return min(open_deadlines, key=lambda entry: entry["date"])


def create_data_root(
    root: Path,
    account: str,
    account_address: str,
    document_repository: str = "",
    document_repository_id: str = "",
) -> None:
    config = root / "config.md"
    if config.exists():
        fail(f"{config} already exists; refusing to overwrite an initialized data root.")
    if root.exists() and not root.is_dir():
        fail(f"Root path is not a directory: {root}")
    secure_directory(root)
    for folder in ("intake", "cases", "board", "briefings", "tmp"):
        secure_directory(root / folder)
    secure_write_text(
        config,
        "\n".join(
            [
                "# Senate Chair Data Root",
                "",
                f"- Data root: {root}",
                f"- Linked account: {ACCOUNT_LABELS[account]}",
                f"- Account address: {account_address}",
                f"- Document repository: {document_repository}",
                f"- Document repository ID: {document_repository_id}",
                "- Last mail run: none",
                "- Last drive run: none",
                "- Last briefing: none",
                "",
                "## Extra topics",
                "",
                "Add one topic per line, formatted as `- Topic`.",
                "",
                "## Owners and units",
                "",
                "Add one owner or unit per line, formatted as `- Name`.",
                "",
            ]
        )
        + "\n",
    )


def cmd_init(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    create_data_root(root, "none", "")
    emit({"root": str(root), "initialized": True})


def cmd_setup(args: argparse.Namespace) -> None:
    root_value = args.root
    if not root_value and sys.stdin.isatty():
        default_root = resolve_root()
        root_value = input(f"Data root [{default_root}]: ").strip() or str(default_root)
    root = Path(root_value or resolve_root()).expanduser().resolve()

    account = args.account
    if not account and sys.stdin.isatty():
        print("Linked email account:")
        print("  1. Outlook — Senate Chair account (recommended)")
        print("  2. Outlook — personal university account")
        print("  3. Gmail")
        print("  4. Intake folder and pasted text only")
        choice = input("Choose 1-4 [1]: ").strip() or "1"
        account = {
            "1": "outlook-chair",
            "2": "outlook-personal",
            "3": "gmail",
            "4": "none",
        }.get(choice)
        if account is None:
            fail("Choose 1, 2, 3, or 4.")
    if account not in ACCOUNT_CHOICES:
        fail(
            "Provide --account outlook-chair, outlook-personal, gmail, or none."
        )
    legacy_account = account == "outlook"
    if legacy_account:
        account = "outlook-chair"

    account_address = args.account_address
    if account_address is None and account != "none" and sys.stdin.isatty():
        account_address = input("Account address (optional, press Enter to skip): ").strip()
    account_address = (account_address or "").strip() if account != "none" else ""

    document_repository = (args.drive_name or "").strip()
    document_repository_id = (args.drive_id or "").strip()
    if sys.stdin.isatty() and not document_repository:
        document_repository = input(
            "Shared Google Drive repository name (optional, press Enter to skip): "
        ).strip()
        if document_repository:
            document_repository_id = input(
                "Drive folder ID (optional, press Enter to skip): "
            ).strip()

    create_data_root(
        root,
        account,
        account_address,
        document_repository,
        document_repository_id,
    )
    if not args.no_remember:
        write_root_pointer(root)
    board_path = generate_board(root)
    emit(
        {
            "root": str(root),
            "initialized": True,
            "linked_account": ACCOUNT_LABELS[account],
            "account_address": account_address,
            "legacy_outlook_alias": legacy_account,
            "document_repository": document_repository,
            "document_repository_id": document_repository_id,
            "board_path": str(board_path),
            "remembered_root": not args.no_remember,
            "harness_actions": {
                "process": "Use $senate-chair to process my new materials.",
                "board": "Use $senate-chair to view my board.",
                "briefing": "Use $senate-chair to run my daily briefing.",
            },
        }
    )


def read_payload(path: str) -> dict:
    payload_path = Path(path).expanduser()
    if not payload_path.is_file():
        fail(f"Payload file not found: {payload_path}")
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Payload is not valid JSON: {exc}")
    if not isinstance(payload, dict):
        fail("Payload must be a JSON object.")
    return payload


def apply_payload(root: Path, payload: dict) -> None:
    config = load_config(root)
    for key in ("source", "received", "summary", "topic", "priority", "deadlines", "case"):
        if key not in payload:
            fail(f"Payload missing required key: {key}")

    source = payload["source"]
    if not isinstance(source, dict) or source.get("type") not in SOURCE_TYPES:
        fail("source.type must be one of: email, file, pasted")
    source_ref = str(source.get("ref", "")).strip()
    if source["type"] != "pasted" and not source_ref:
        fail("source.ref is required for email and file items")
    if source["type"] == "pasted":
        source_display = "pasted"
    else:
        source_display = f"{source['type']} <{source_ref}>"

    received = parse_iso_date(payload["received"], "received date")
    summary = str(payload["summary"]).strip()
    if not summary:
        fail("summary must not be empty")
    word_count = len(summary.split())
    if word_count > 120:
        fail(f"summary is {word_count} words; the limit is 120")

    topic = str(payload["topic"]).strip()
    if topic not in config["topics"]:
        fail(f"Unknown topic: {topic!r}. Use a label from taxonomy.md or config.md Extra topics.")

    priority = str(payload["priority"]).strip()
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority!r} (expected one of {', '.join(PRIORITIES)})")

    raw_deadlines = payload["deadlines"]
    if not isinstance(raw_deadlines, list):
        fail("deadlines must be a list")
    deadlines = []
    for entry in raw_deadlines:
        if not isinstance(entry, dict) or "date" not in entry or "source" not in entry:
            fail("Each deadline needs a date and a source sentence.")
        deadline_date = parse_iso_date(entry["date"], "deadline date")
        deadline_source = str(entry["source"]).strip()
        if not deadline_source:
            fail("A deadline source sentence must not be empty.")
        deadlines.append({"date": deadline_date.isoformat(), "source": deadline_source})

    case_spec = payload["case"]
    if not isinstance(case_spec, dict):
        fail("case must be a JSON object")
    confidence = str(case_spec.get("confidence", "")).strip()
    if confidence not in CONFIDENCE_LEVELS:
        fail("case.confidence must be high, medium, or low")
    reason = str(case_spec.get("reason", "")).strip()
    if not reason:
        fail("case.reason is required")
    suggested_owner = str(case_spec.get("suggested_owner", "")).strip()
    suggested_next = str(case_spec.get("suggested_next_action", "")).strip()
    confidential = bool(payload.get("confidential", False))

    today = date.today()
    item_id = next_item_id(root, received)
    action = case_spec.get("action")
    if action == "new":
        title = str(case_spec.get("title", "")).strip()
        if not title:
            fail("case.title is required for a new case")
        if len(title) > 120:
            fail("case.title must be 120 characters or fewer")
        case_id = next_case_id(root, today)
        case = {key: "" for key in META_KEYS}
        case.update(
            {
                "id": case_id,
                "title": title,
                "Status": "Received",
                "Topic": topic,
                "Owner": "unassigned",
                "Suggested owner": suggested_owner,
                "Opened": today.isoformat(),
                "Last update": today.isoformat(),
                "Next action": "awaiting triage",
                "Review flag": "new case unreviewed",
                "Confidential": "yes" if confidential else "no",
                "deadlines": [],
                "log": [],
                "items": [],
            }
        )
        new_case = True
    elif action == "existing":
        case_id = str(case_spec.get("id", "")).strip()
        case = find_case(root, case_id)
        new_case = False
    else:
        fail("case.action must be 'new' or 'existing'")

    for deadline in deadlines:
        duplicate = any(
            entry["date"] == deadline["date"] and entry["source"] == deadline["source"]
            for entry in case["deadlines"]
        )
        if not duplicate:
            case["deadlines"].append({**deadline, "item": item_id, "done": "no"})

    case["Last update"] = today.isoformat()
    if confidential:
        case["Confidential"] = "yes"
    if not new_case and confidence in ("medium", "low") and not case["Review flag"]:
        case["Review flag"] = f"auto-link {confidence} confidence"

    action_word = "Opened with" if new_case else "Added"
    case["log"].append(f"{today.isoformat()}: {action_word} item {item_id} ({confidence} confidence).")
    case["items"].append(f"{item_id}: {headline_from_summary(summary)}")

    item_path = root / "cases" / case["id"] / "items" / f"{item_id}.md"
    item_lines = [
        f"# Item {item_id}",
        f"- Source: {source_display}",
        f"- Received: {received.isoformat()}",
        f"- Case: {case['id']}",
        f"- Topic: {topic}",
        f"- Priority: {priority}",
        f"- Link confidence: {confidence} — {reason}",
        "",
        "## Summary",
        summary,
        "",
        "## Deadlines",
    ]
    if deadlines:
        item_lines.extend(f"- {entry['date']}: {entry['source']}" for entry in deadlines)
    else:
        item_lines.append("None.")
    secure_write_text(item_path, "\n".join(item_lines) + "\n")
    write_case_file(root, case)
    board_path = generate_board(root)
    emit(
        {
            "case_id": case["id"],
            "item_id": item_id,
            "item_path": str(item_path),
            "new_case": new_case,
            "status": case["Status"],
            "review_flag": case["Review flag"],
            "board_path": str(board_path),
        }
    )


def cmd_process(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    payload = read_payload(args.payload)
    apply_payload(root, payload)


def parse_deadline_flag(value: str) -> dict:
    if "|" not in value:
        fail("Each --deadline must be formatted 'YYYY-MM-DD|verbatim source sentence'.")
    raw_date, source = value.split("|", 1)
    deadline_date = parse_iso_date(raw_date, "deadline date")
    deadline_source = source.strip()
    if not deadline_source:
        fail("A deadline source sentence must not be empty.")
    return {"date": deadline_date.isoformat(), "source": deadline_source}


def cmd_new_item(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    source_ref = (args.ref or "").strip()
    if args.source_type != "pasted" and not source_ref:
        fail("--ref is required for email and file items")
    if args.source_type == "pasted":
        source_ref = ""
    deadlines = [parse_deadline_flag(entry) for entry in (args.deadline or [])]
    payload = {
        "source": {"type": args.source_type, "ref": source_ref},
        "received": args.received or date.today().isoformat(),
        "summary": args.summary,
        "topic": args.topic,
        "priority": args.priority,
        "deadlines": deadlines,
        "case": {
            "action": args.case_action,
            "id": args.case_id or "",
            "title": args.case_title or "",
            "confidence": args.confidence,
            "reason": args.reason,
            "suggested_owner": args.suggested_owner or "",
            "suggested_next_action": args.suggested_next_action or "",
        },
        "confidential": args.confidential,
    }
    apply_payload(root, payload)


def cmd_link_drive(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    name = (args.name or "").strip()
    if not name:
        fail("Provide --name for the shared Google Drive repository.")
    update_config(root, "Document repository", name)
    update_config(root, "Document repository ID", (args.drive_id or "").strip())
    emit(
        {
            "root": str(root),
            "document_repository": name,
            "document_repository_id": (args.drive_id or "").strip(),
        }
    )


def cmd_link_account(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    account = args.account
    legacy_account = account == "outlook"
    if legacy_account:
        account = "outlook-chair"
    if account not in ACCOUNT_TYPES:
        fail(
            "Provide --account outlook-chair, outlook-personal, gmail, or none."
        )
    account_address = (args.account_address or "").strip() if account != "none" else ""
    update_config(root, "Linked account", ACCOUNT_LABELS[account])
    update_config(root, "Account address", account_address)
    emit(
        {
            "root": str(root),
            "linked_account": ACCOUNT_LABELS[account],
            "account_address": account_address,
            "legacy_outlook_alias": legacy_account,
        }
    )


def cmd_triage(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    case = find_case(root, args.case)
    today = date.today().isoformat()

    has_change = any(
        (
            args.status,
            args.owner is not None,
            args.next_action is not None,
            args.clear_review,
        )
    )
    if not has_change:
        fail("Nothing to update; provide --status, --owner, --next-action, or --clear-review.")
    if args.pending_unit and args.status != "Pending":
        fail("--pending-unit is only valid together with --status Pending.")

    changes: list[str] = []
    if args.status:
        if args.status not in STATUSES:
            fail(f"Invalid status: {args.status!r} (expected one of {', '.join(STATUSES)})")
        case["Status"] = args.status
        changes.append(f"status -> {args.status}")
        if args.status == "Pending":
            if args.pending_unit:
                case["Pending unit"] = args.pending_unit
                case["Pending since"] = today
            elif not case.get("Pending unit"):
                fail("Pending requires --pending-unit.")
        else:
            case["Pending unit"] = ""
            case["Pending since"] = ""
    if args.owner is not None:
        case["Owner"] = args.owner.strip() or "unassigned"
        changes.append(f"owner -> {case['Owner']}")
    if args.next_action is not None:
        case["Next action"] = args.next_action.strip()
        changes.append(f"next action -> {case['Next action']}")
    if args.clear_review:
        case["Review flag"] = ""
        changes.append("review flag cleared")

    case["Last update"] = today
    case["log"].append(f"{today}: Triage — {'; '.join(changes)}.")
    write_case_file(root, case)
    board_path = generate_board(root)
    emit(
        {
            "case_id": case["id"],
            "status": case["Status"],
            "owner": case["Owner"],
            "next_action": case["Next action"],
            "review_flag": case["Review flag"],
            "board_path": str(board_path),
        }
    )


def deadline_label(deadline: dict, today: date) -> tuple[str, str]:
    deadline_date = date.fromisoformat(deadline["date"])
    days = (deadline_date - today).days
    if days < 0:
        label = f"{deadline['date']} (overdue {-days}d)"
    elif days == 0:
        label = f"{deadline['date']} (today)"
    else:
        label = f"{deadline['date']} (in {days}d)"
    css = "deadline-urgent" if days <= 3 else "deadline-soon" if days <= 7 else "deadline-normal"
    return label, css


def render_card(case: dict, today: date) -> str:
    deadline = next_deadline(case)
    if deadline:
        deadline_text, deadline_css = deadline_label(deadline, today)
    else:
        deadline_text, deadline_css = "None", "dl-normal"
    last_update = case.get("Last update", "")
    if last_update:
        update_days = (today - date.fromisoformat(last_update)).days
        updated_text = "today" if update_days <= 0 else f"{update_days}d ago"
    else:
        updated_text = "unknown"

    badges = []
    if case.get("Review flag"):
        badges.append(f'<span class="badge review">Review: {html.escape(case["Review flag"])}</span>')
    if case.get("Confidential") == "yes":
        badges.append('<span class="badge confidential">Confidential</span>')
    pending_rows = ""
    if case["Status"] == "Pending" and case.get("Pending unit"):
        since = case.get("Pending since", "")
        if since:
            waiting = (today - date.fromisoformat(since)).days
            waiting_text = f"{waiting}d" if waiting >= 0 else "unknown"
        else:
            waiting_text = "unknown"
        badges.append(
            f'<span class="badge pending">Waiting on {html.escape(case["Pending unit"])} · {waiting_text}</span>'
        )

    return (
        '<article class="panel panel-default case-card">'
        '<div class="panel-heading">'
        f'<h3 class="panel-title">{html.escape(case["id"])}</h3>'
        "</div>"
        '<div class="panel-body">'
        f'<p class="case-topic"><span class="label label-default">{html.escape(case.get("Topic", "Other"))}</span></p>'
        f'<h4 class="case-title">{html.escape(case["title"])}</h4>'
        '<dl class="case-meta">'
        f'<dt>Owner</dt><dd>{html.escape(case.get("Owner", "unassigned"))}</dd>'
        f'<dt>Next deadline</dt><dd class="{deadline_css}">{html.escape(deadline_text)}</dd>'
        f'<dt>Updated</dt><dd>{html.escape(updated_text)}</dd>'
        "</dl>"
        + (f'<div class="case-badges">{"".join(badges)}</div>' if badges else "")
        + "</div>"
        + "</article>"
    )


def render_static_column(status: str, cases: list[dict], today: date) -> str:
    cards = "".join(render_card(case, today) for case in cases)
    empty = '<p class="empty-column">Nothing here.</p>' if not cases else ""
    return (
        f'<section class="col-xs-12 col-sm-6 col-md-3 board-column" data-status="{html.escape(status)}">'
        f'<h2>{html.escape(status)} <span class="badge count">{len(cases)}</span></h2>'
        f'<div class="column-cards">{cards}{empty}</div>'
        "</section>"
    )


def render_static_board(cases: list[dict], today: date) -> str:
    columns = {status: [] for status in STATUSES}
    for case in cases:
        status = case.get("Status", "")
        if status not in columns:
            fail(f"Case {case['id']} has an invalid status: {status!r}")
        columns[status].append(case)
    return "".join(
        render_static_column(status, column_cases, today)
        for status, column_cases in columns.items()
    )


def generate_board(root: Path) -> Path:
    cases = load_all_cases(root)
    today = date.today()
    board_dir = root / "board"
    secure_directory(board_dir)
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    asset_targets = {"dashboard.css": "dashboard.css", "dashboard-app.js": "app.js"}
    for source_name, target_name in asset_targets.items():
        source = assets_dir / source_name
        if not source.is_file():
            fail(f"Dashboard asset missing: {source}")
        secure_write_text(board_dir / target_name, source.read_text(encoding="utf-8"))
    template_path = assets_dir / "dashboard-template.html"
    if not template_path.is_file():
        fail(f"Dashboard asset missing: {template_path}")
    template = template_path.read_text(encoding="utf-8")
    if "<!--BOARD_CARDS-->" not in template:
        fail("Dashboard template is missing the board placeholder.")
    board_html = template.replace("<!--BOARD_CARDS-->", render_static_board(cases, today))
    board_path = board_dir / "index.html"
    secure_write_text(board_path, board_html)
    return board_path


def cmd_board(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    board_path = generate_board(root)
    cases = load_all_cases(root)
    counts = {status: 0 for status in STATUSES}
    for case in cases:
        if case.get("Status") in counts:
            counts[case["Status"]] += 1
    emit({"board_path": str(board_path), "counts": counts})


def cmd_brief(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    config = load_config(root)
    today = parse_iso_date(args.date, "briefing date") if args.date else date.today()
    horizon = today + timedelta(days=7)

    deadlines = []
    pending = []
    stalled = []
    new_items = []

    cutoff = today
    if config["last_briefing"] not in ("", "none"):
        cutoff = parse_iso_date(config["last_briefing"], "last briefing date")

    for case in load_all_cases(root):
        for entry in case["deadlines"]:
            if entry["done"].lower() == "yes":
                continue
            entry_date = date.fromisoformat(entry["date"])
            if entry_date <= horizon:
                deadlines.append(
                    {
                        "case_id": case["id"],
                        "title": case["title"],
                        "date": entry["date"],
                        "days": (entry_date - today).days,
                        "source": entry["source"],
                    }
                )
        if case.get("Status") == "Pending":
            since = case.get("Pending since", "")
            days_waiting = (today - date.fromisoformat(since)).days if since else None
            pending.append(
                {
                    "case_id": case["id"],
                    "title": case["title"],
                    "unit": case.get("Pending unit", ""),
                    "days_waiting": days_waiting,
                }
            )
        if case.get("Status") == "Active" and case.get("Last update"):
            days_idle = (today - date.fromisoformat(case["Last update"])).days
            if days_idle >= 5:
                stalled.append(
                    {
                        "case_id": case["id"],
                        "title": case["title"],
                        "owner": case.get("Owner", "unassigned"),
                        "days_since_update": days_idle,
                    }
                )
        for entry in case["items"]:
            match = ITEM_ENTRY_RE.match(entry)
            if not match:
                continue
            received = date.fromisoformat(match.group(1))
            if cutoff < received <= today:
                new_items.append(
                    {
                        "case_id": case["id"],
                        "item_id": f"{match.group(1)}-{match.group(2)}",
                        "summary": match.group(3),
                    }
                )

    deadlines.sort(key=lambda entry: (entry["date"], entry["case_id"]))
    pending.sort(key=lambda entry: (-(entry["days_waiting"] or -1), entry["case_id"]))
    stalled.sort(key=lambda entry: (-entry["days_since_update"], entry["case_id"]))
    update_config(root, "Last briefing", today.isoformat())
    emit(
        {
            "briefing_date": today.isoformat(),
            "deadlines": deadlines,
            "pending": pending,
            "stalled": stalled,
            "new_items": new_items,
        }
    )


def cmd_list(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    cases = load_all_cases(root)
    if args.status:
        if args.status not in STATUSES:
            fail(f"Invalid status filter: {args.status!r}")
        cases = [case for case in cases if case.get("Status") == args.status]
    if args.topic:
        cases = [case for case in cases if case.get("Topic", "") == args.topic]
    rows = []
    for case in sorted(cases, key=lambda case: case["id"]):
        deadline = next_deadline(case)
        rows.append(
            {
                "id": case["id"],
                "title": case["title"],
                "status": case.get("Status", ""),
                "topic": case.get("Topic", ""),
                "owner": case.get("Owner", "unassigned"),
                "next_deadline": deadline["date"] if deadline else None,
                "review_flag": case.get("Review flag", ""),
            }
        )
    emit(rows)


def cmd_mark(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    result = {}
    if args.mail_run:
        mail_run = parse_iso_date(args.mail_run, "mail run date")
        update_config(root, "Last mail run", mail_run.isoformat())
        result["last_mail_run"] = mail_run.isoformat()
    if args.drive_run:
        drive_run = parse_iso_date(args.drive_run, "drive run date")
        update_config(root, "Last drive run", drive_run.isoformat())
        result["last_drive_run"] = drive_run.isoformat()
    if not result:
        fail("Provide --mail-run or --drive-run YYYY-MM-DD.")
    emit(result)


def cmd_serve(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    from senate_chair_server import serve

    serve(root, args.host, args.port)


def cmd_status(args: argparse.Namespace) -> None:
    root = resolve_root(args.root)
    require_root(root)
    config = load_config(root)
    board_path = root / "board" / "index.html"
    emit(
        {
            "root": str(root),
            "linked_account": config["linked_account"],
            "account_address": config["account_address"],
            "document_repository": config["document_repository"],
            "document_repository_id": config["document_repository_id"],
            "last_mail_run": config["last_mail_run"],
            "last_drive_run": config["last_drive_run"],
            "last_briefing": config["last_briefing"],
            "board_path": str(board_path),
            "board_exists": board_path.is_file(),
        }
    )


def skill_directory() -> Path:
    return Path(__file__).resolve().parent.parent


def wrapper_path() -> Path:
    return skill_directory() / "bin" / "senate-chair"


def command_install_path() -> Path:
    return Path.home() / ".local" / "bin" / "senate-chair"


def path_contains(directory: Path) -> bool:
    return str(directory) in os.environ.get("PATH", "").split(os.pathsep)


def cmd_doctor(args: argparse.Namespace) -> None:
    checks = {}
    next_actions = []

    version = sys.version_info
    checks["python"] = {
        "ok": version >= (3, 9),
        "version": f"{version.major}.{version.minor}.{version.micro}",
    }

    required_files = [
        "SKILL.md",
        "assets/dashboard.css",
        "assets/dashboard-app.js",
        "assets/dashboard-template.html",
        "scripts/senate_chair_server.py",
    ]
    missing_files = [
        relative
        for relative in required_files
        if not (skill_directory() / relative).is_file()
    ]
    checks["skill_files"] = {"ok": not missing_files, "missing": missing_files}
    if missing_files:
        next_actions.append("Reinstall the senate-chair skill; required files are missing.")

    root = resolve_root(args.root)
    initialized = (root / "config.md").is_file()
    checks["data_root"] = {"ok": initialized, "root": str(root)}
    if not initialized:
        next_actions.append(
            "Run setup to initialize the data root, link the Senate Chair Outlook "
            "account, and link the shared Google Drive repository."
        )
        emit({"ok": False, "checks": checks, "next_actions": next_actions})
        return

    require_root(root)
    config = load_config(root)
    account_ok = config["linked_account"] != "not configured"
    checks["linked_account"] = {
        "ok": account_ok,
        "label": config["linked_account"],
        "address": config["account_address"],
    }
    if not account_ok:
        next_actions.append("Link the Senate Chair Outlook account during setup.")
    elif config["linked_account"] == "Intake folder and pasted text":
        next_actions.append(
            "Mail and calendar are disabled; run setup again to link the Senate "
            "Chair Outlook account when ready."
        )

    drive_ok = bool(config["document_repository"])
    checks["document_repository"] = {
        "ok": drive_ok,
        "name": config["document_repository"],
        "id": config["document_repository_id"],
    }
    if not drive_ok:
        next_actions.append(
            "Link the shared Google Drive document repository with link-drive."
        )

    board_path = root / "board" / "index.html"
    checks["board"] = {"ok": board_path.is_file(), "path": str(board_path)}

    installed_command = command_install_path()
    checks["command"] = {
        "wrapper": str(wrapper_path()),
        "installed": installed_command.is_file() or installed_command.is_symlink(),
        "install_path": str(installed_command),
    }

    ok = all(
        (
            checks["python"]["ok"],
            checks["skill_files"]["ok"],
            checks["data_root"]["ok"],
            account_ok,
            drive_ok,
        )
    )
    emit({"ok": ok, "checks": checks, "next_actions": next_actions})


def cmd_install_command(args: argparse.Namespace) -> None:
    source = wrapper_path()
    if not source.is_file():
        fail(f"Command wrapper missing: {source}")
    target = command_install_path()
    target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        target.unlink()
    target.symlink_to(source)
    emit(
        {
            "installed": True,
            "command": str(target),
            "on_path": path_contains(target.parent),
            "note": (
                "The command is ready."
                if path_contains(target.parent)
                else "Add ~/.local/bin to PATH or invoke the wrapper by full path."
            ),
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create the data root")
    init_parser.add_argument("--root", default="~/SenateChair")
    init_parser.set_defaults(func=cmd_init)

    setup_parser = subparsers.add_parser(
        "setup",
        help="initialize the data root, select the account link, and generate the board",
    )
    setup_parser.add_argument("--root")
    setup_parser.add_argument("--account", choices=ACCOUNT_CHOICES)
    setup_parser.add_argument("--account-address")
    setup_parser.add_argument("--drive-name", help="shared Google Drive repository name")
    setup_parser.add_argument("--drive-id", help="shared Google Drive folder ID")
    setup_parser.add_argument(
        "--no-remember",
        action="store_true",
        help="do not save this root as the default for later commands",
    )
    setup_parser.set_defaults(func=cmd_setup)

    process_parser = subparsers.add_parser("process", help="persist one processed item")
    process_parser.add_argument("--root")
    process_parser.add_argument("--payload", required=True)
    process_parser.set_defaults(func=cmd_process)

    new_item_parser = subparsers.add_parser(
        "new-item",
        help="process one item without writing a JSON payload file",
    )
    new_item_parser.add_argument("--root")
    new_item_parser.add_argument(
        "--source-type", required=True, choices=SOURCE_TYPES, dest="source_type"
    )
    new_item_parser.add_argument("--ref", help="message ID, subject+date, or file path")
    new_item_parser.add_argument("--received", help="YYYY-MM-DD (default: today)")
    new_item_parser.add_argument("--summary", required=True)
    new_item_parser.add_argument("--topic", required=True)
    new_item_parser.add_argument("--priority", choices=PRIORITIES, default="Normal")
    new_item_parser.add_argument(
        "--deadline",
        action="append",
        help="YYYY-MM-DD|verbatim source sentence; repeat for multiple deadlines",
    )
    new_item_parser.add_argument("--case-action", required=True, choices=["new", "existing"], dest="case_action")
    new_item_parser.add_argument("--case-id", help="existing case ID, e.g. SC-2026-001")
    new_item_parser.add_argument("--case-title", help="one-line title for a new case")
    new_item_parser.add_argument("--confidence", required=True, choices=CONFIDENCE_LEVELS)
    new_item_parser.add_argument("--reason", required=True, help="why this case link or new case")
    new_item_parser.add_argument("--suggested-owner", dest="suggested_owner")
    new_item_parser.add_argument("--suggested-next-action", dest="suggested_next_action")
    new_item_parser.add_argument("--confidential", action="store_true")
    new_item_parser.set_defaults(func=cmd_new_item)

    link_drive_parser = subparsers.add_parser(
        "link-drive",
        help="link or update the shared Google Drive document repository",
    )
    link_drive_parser.add_argument("--root")
    link_drive_parser.add_argument("--name", required=True)
    link_drive_parser.add_argument("--drive-id", dest="drive_id")
    link_drive_parser.set_defaults(func=cmd_link_drive)

    link_account_parser = subparsers.add_parser(
        "link-account",
        help="link or update the email account scope on an initialized root",
    )
    link_account_parser.add_argument("--root")
    link_account_parser.add_argument("--account", required=True, choices=ACCOUNT_CHOICES)
    link_account_parser.add_argument("--account-address", dest="account_address")
    link_account_parser.set_defaults(func=cmd_link_account)

    triage_parser = subparsers.add_parser("triage", help="apply Chair-confirmed case decisions")
    triage_parser.add_argument("--root")
    triage_parser.add_argument("--case", required=True)
    triage_parser.add_argument("--status", choices=STATUSES)
    triage_parser.add_argument("--owner")
    triage_parser.add_argument("--next-action")
    triage_parser.add_argument("--pending-unit")
    triage_parser.add_argument("--clear-review", action="store_true")
    triage_parser.set_defaults(func=cmd_triage)

    board_parser = subparsers.add_parser("board", help="regenerate the Kanban dashboard")
    board_parser.add_argument("--root")
    board_parser.set_defaults(func=cmd_board)

    brief_parser = subparsers.add_parser("brief", help="print the daily briefing data skeleton")
    brief_parser.add_argument("--root")
    brief_parser.add_argument("--date")
    brief_parser.set_defaults(func=cmd_brief)

    list_parser = subparsers.add_parser("list", help="list cases")
    list_parser.add_argument("--root")
    list_parser.add_argument("--status", choices=STATUSES)
    list_parser.add_argument("--topic")
    list_parser.set_defaults(func=cmd_list)

    mark_parser = subparsers.add_parser("mark", help="record the last processed mail date")
    mark_parser.add_argument("--root")
    mark_parser.add_argument("--mail-run")
    mark_parser.add_argument("--drive-run", dest="drive_run")
    mark_parser.set_defaults(func=cmd_mark)

    serve_parser = subparsers.add_parser("serve", help="serve the interactive local board")
    serve_parser.add_argument("--root")
    serve_parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1",))
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.set_defaults(func=cmd_serve)

    status_parser = subparsers.add_parser("status", help="show the configured data root and account")
    status_parser.add_argument("--root")
    status_parser.set_defaults(func=cmd_status)

    doctor_parser = subparsers.add_parser(
        "doctor", help="verify dependencies, setup, and links"
    )
    doctor_parser.add_argument("--root")
    doctor_parser.set_defaults(func=cmd_doctor)

    install_command_parser = subparsers.add_parser(
        "install-command", help="install the senate-chair command into ~/.local/bin"
    )
    install_command_parser.set_defaults(func=cmd_install_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
