# Real ROI Skill Implementation Plan

Date: September 16, 2026

## Recommendation

Build a local-first, pseudonymous Real ROI check-in skill for the TritonAI Harness. Each participant runs the skill on their own machine, confirms every record locally, and submits only the confirmed analytical fields to a restricted Google Form. Use n8n to send the weekly reminder, not to collect or store check-in answers.

This design keeps conversation content and raw thread metadata local, gives participants control over what leaves their machine, and produces a small central dataset that can support the pilot ROI calculation without creating an individual productivity record.

## Decisions Already Made

- Use pseudonymous participant IDs, not email addresses, in the analytical dataset.
- Collect data locally on each participant's machine.
- Submit only confirmed, pseudonymous weekly records centrally.
- Use a Google Form for pilot submission, with responses stored in a protected Google Sheet.
- Put the response Sheet and identity mapping in separate, restricted locations.
- Use n8n for the weekly reminder.
- Do not use n8n execution history as the primary data store.
- Do not read or submit message content, attachments, file paths, or raw session IDs.
- Use manual thread recognition in version 1 because the Harness does not currently expose a metadata-only thread title.

## Scope

### In Scope

- One pilot unit.
- One tool: the TritonAI Harness.
- A six-week observation window.
- Local metadata extraction from the participant's own Harness session logs.
- A weekly check-in for up to three selected threads.
- A closing interview.
- Institutional cost intake for `L`.
- Unit-lead valuation for `C`.
- A one-page Real ROI report.

### Out of Scope

- Individual performance measurement.
- Workload comparisons between participants.
- Procurement approval or renewal gates.
- Automatic reading of message content.
- Automatic scheduling of an unattended check-in that saves data without participant confirmation.
- Institution-wide rollout before the pilot review.

## Operating Principles

1. **Measure the tool, not the person.** Records are pseudonymous, combined for reporting, and never used in performance reviews.
2. **Confirm before submission.** Nothing leaves the participant's machine until they review a complete record and confirm it.
3. **Separate identity from analysis.** The central analytical dataset contains a participant code, not a name or email.
4. **Keep raw work local.** Message content, thread titles, raw session IDs, attachments, and file paths stay on the participant's machine.
5. **Label every number.** Each value is marked as derived, reported, estimated, or missing.
6. **Count each hour once.** Hours saved are either counted as time returned or as new capacity, never both.
7. **Report uncertainty.** The ROI report shows coverage, missingness, and the quality of evidence behind each term.

## Architecture

```text
Participant's machine
  Harness session logs
    -> metadata-only parser
    -> thread selection
    -> interactive weekly check-in
    -> local confirmation
    -> local pseudonymous record
    -> participant submits confirmed fields

Central pilot storage
  Google Form
    -> protected Google Sheet in a UCSD Shared Drive
    -> aggregate ROI calculation
    -> one-page report

Scheduling
  n8n Schedule Trigger
    -> weekly reminder to pilot alias or Teams channel
```

### Local Layer

The local skill:

- reads only timestamp and session-header events from the participant's own session logs
- derives rough working time by thread and day
- selects the longest thread and up to two other threads
- asks the weekly questions
- shows the complete record for confirmation
- stores the confirmed record locally
- prepares a submission summary for the Google Form

The local layer does not:

- deserialize or output message content
- read attachments or file paths
- send anything without confirmation
- store credentials in plain-text configuration files

### Submission Layer

Use a manually created Google Form for the pilot.

Form settings:

- restrict access to UCSD accounts
- do not collect email addresses
- do not ask for names
- require the participant code
- use numeric validation for all hour and minute fields
- make free-text fields optional where possible
- include a clear statement that submitted answers will be stored in the pilot response Sheet

The form should contain structured fields rather than one free-form JSON field. Structured fields reduce parsing errors and make access review easier.

### Central Layer

The Google Form response Sheet should live in a UCSD-owned Shared Drive, not a personal My Drive.

Recommended folders:

```text
Real ROI Pilot/
  responses/
    Real ROI Weekly Check-In (Responses)
  analysis/
    costs.csv
    capacity-valuation.csv
    aggregate calculations
    final report
  governance/
    consent log
    retention schedule
    access review

Restricted record-holder folder/
  identity-map.csv
```

Access:

- `responses/`: pilot analysis team only
- `analysis/`: pilot analysis team only
- `governance/`: pilot sponsor and record holder as appropriate
- `identity-map.csv`: record holder only

Link sharing should be disabled except for explicitly authorized people or groups.

### Scheduling Layer

Use one n8n workflow:

```text
Schedule Trigger
  -> Send weekly reminder
```

The reminder should go to a pilot email alias or Teams channel rather than storing individual email addresses in the workflow. It should include:

- the check-in window
- the local invocation prompt
- the Google Form link
- the participant-code reminder
- the privacy statement
- the closing time for the week

n8n should not receive check-in answers. If a future version sends data through n8n, configure execution-data retention first and test that answers do not persist in workflow logs.

## Skill Package

Create the skill as:

```text
measure-real-roi/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── protocol.md
│   ├── governance.md
│   └── calculation.md
├── scripts/
│   ├── real_roi.py
│   ├── extract_thread_metadata.py
│   └── validate_store.py
└── assets/
    ├── consent-template.md
    ├── closing-interview.md
    ├── cost-intake.csv
    └── capacity-valuation.csv
```

### `SKILL.md`

Keep the main skill concise. It should:

- trigger on Real ROI, ROI check-in, weekly check-in, and pilot reporting requests
- route setup questions to `references/governance.md`
- route weekly collection to `references/protocol.md`
- route calculations to `references/calculation.md`
- require local confirmation before submission
- prohibit reading message content
- prohibit saving raw thread titles or raw session IDs in submitted records

### `references/protocol.md`

Contains:

- participant setup
- thread selection rules
- time-estimation rules
- weekly questions
- confirmation table format
- submission instructions
- skipped-week handling
- closing-interview steps

### `references/governance.md`

Contains:

- voluntary participation rules
- consent requirements
- pseudonym policy
- data minimization rules
- access-control expectations
- retention and deletion
- small-group suppression
- withdrawal and correction

### `references/calculation.md`

Contains:

- definitions of `T`, `C`, `L`, `H`, and `O`
- the standard-rate conversion
- period alignment
- missing-data rules
- double-counting rules
- ROI formula
- sensitivity checks
- report format

## Local Data Model

Store local records under:

```text
~/.tritonai-harness/real-roi/<pilot-id>/
```

Recommended files:

```text
config.json
local-records.jsonl
pending-checkin.json
submission-log.jsonl
```

Set the folder permissions to the local user only.

### `config.json`

Fields:

- `pilot_id`
- `participant_code`
- `tool_name`
- `pilot_start_date`
- `pilot_end_date`
- `gap_cutoff_minutes`
- `work_types`
- `standard_hourly_rate`
- `retention_date`
- `form_url`
- `record_holder_role`
- `schema_version`

Do not store the mapping from participant code to person in this file.

### Thread Metadata

For each thread, store locally:

- local `thread_ref`
- date
- first activity time
- last activity time
- turn count
- derived minutes
- selection reason
- provenance: `derived`

Generate `thread_ref` locally using a random ID or an HMAC of the raw session ID with a locally stored secret. Do not submit the raw session ID.

### Weekly Check-In Record

For each selected thread:

- `participant_code`
- `week_number`
- `thread_ref`
- `work_type`
- `derived_minutes`
- `confirmed_minutes`
- `baseline_method`
- `baseline_minutes`
- `checking_fixing_minutes`
- `wrong_output_mattered`
- `cleanup_minutes`
- `confidence`

Once per week:

- `new_capacity_description`
- `new_capacity_would_not_have_happened`
- `new_capacity_used_saved_time`
- `new_capacity_hours`
- `learning_hours`
- `coordination_hours`
- `model_changed`
- `model_change_redo_hours`
- `skipped_week`
- `participant_confirmed`
- `confirmed_at`

The submitted record should exclude:

- thread title
- raw session ID
- message content
- attachment names
- file paths
- machine hostname
- local username
- email address

## Metadata Extraction

### Safe Parser Rules

The parser should:

1. Read only JSONL lines whose top-level type is `session_meta` or `event_msg`.
2. From `session_meta`, read only session ID and creation timestamp.
3. From `event_msg`, read only event type, timestamp, and turn ID.
4. Use `task_started` and `task_complete` events to derive turn boundaries.
5. Skip `response_item` records, which contain conversation content.
6. Fail closed if the expected schema is missing.
7. Emit only allowlisted metadata fields.

Use a streaming parser or an equivalent implementation that does not copy `response_item` payloads into parser output, logs, temporary files, or error messages.

The parser should be tested against synthetic session files before it is used on real logs.

### Time Estimation

For each thread and calendar day:

1. Collect `task_started` and `task_complete` timestamps.
2. Merge activity periods separated by gaps no longer than the configured cutoff, initially ten minutes.
3. Split overlapping periods between threads.
4. Sum the resulting minutes.
5. Label the result as `derived`.

The participant can confirm or correct the derived value. A corrected value is labeled `reported`.

Run a sensitivity check using five-minute and fifteen-minute cutoffs. Do not treat the ten-minute result as more precise than it is.

### Thread Selection

Each week:

1. Exclude threads outside the pilot window.
2. Exclude threads already selected in earlier weeks unless no new threads are available.
3. Select the thread with the longest derived minutes.
4. Select up to two additional threads using a deterministic random seed based on participant code and week number.
5. If fewer than three threads exist, select all.

The check-in should display:

- date
- start time
- end time
- turn count
- derived minutes

It should not display a thread title in version 1. If the participant cannot recognize a thread from metadata, they may skip it and select another manually from the Harness history.

## Weekly Protocol

### Setup

Before the pilot:

1. Confirm pilot approval.
2. Confirm the record holder.
3. Assign participant codes.
4. Obtain written consent.
5. Agree on work types.
6. Confirm the ten-minute gap cutoff.
7. Confirm the standard hourly rate.
8. Confirm P2 storage approval.
9. Create the Google Form and response Sheet.
10. Configure n8n reminder scheduling.
11. Install and configure the skill on each participant's machine.

### Weekly Check-In

For each selected thread, ask:

1. What kind of work was this?
2. The records show about this many minutes. Does that match your sense of the work? If not, about how long did it take?
3. Without the Harness, how would you have done this work, and about how long would it have taken?
4. After finishing in the Harness, about how long did you spend checking or fixing the result elsewhere?
5. Did anything it produced turn out wrong in a way that mattered? If yes, what happened, and about how long did cleanup take?

Once per week, ask:

6. Did you or your team do anything this week with the Harness that you would not have done before?
7. If yes, did that work use time the Harness had saved you?
8. About how many hours went to learning the tool?
9. About how many hours went to meetings or messages about the tool?

Only when the model changed:

10. Did you have to redo or adjust anything because of the model change? About how long did that take?

At the end:

- show every field in a table
- let the participant correct any value
- accept "I don't know" and store it as missing
- require explicit confirmation
- save locally
- show the fields that will be submitted
- provide the Google Form link

### Skipped Weeks

Record a skipped week as skipped. Do not fill values. Do not infer a skipped week from adjacent weeks.

The record holder may follow up on a pattern across the group, but should not chase individuals or compare completion rates by person.

## Institutional Cost And Capacity Data

### `L`: Line Item

Collect from procurement, IT, and budget records:

- contract or license cost for the pilot period
- infrastructure cost allocation
- hosting and energy allocation, if applicable
- staff time already included in the line item
- seats purchased, if applicable
- seats active, if applicable

All costs must align to the same six-week period.

### `C`: New Capacity

The unit lead reviews new work reported during the pilot and answers:

1. What new work happened?
2. Would it have happened without the Harness?
3. Would it survive if the Harness went away?
4. Who would have had to do it?
5. What is the valuation evidence?

Acceptable valuation evidence:

- quote
- prior contract
- published rate
- documented staffing estimate

If no defensible price exists, set `C` to zero and record the work in the judgment section.

### `H`: Human Cost

Convert these hours at the standard rate:

- learning the tool
- checking and fixing output
- redoing work after a model change

Routine checking and fixing belongs in `H`.

### `O`: Organizational Cost

Include:

- unused seats or underused infrastructure, in dollars
- coordination and meeting hours, converted at the standard rate
- cleanup after materially wrong output, converted at the standard rate

Downstream or organization-wide cleanup belongs in `O`. Do not count the same cleanup minutes in both `H` and `O`.

## Calculation

Let:

- `R` = institution-wide standard hourly rate
- `T_hours` = net time returned, in hours
- `C_dollars` = valued new capacity, in dollars
- `L_dollars` = line-item cost for the pilot period
- `H_hours` = learning, checking, fixing, and model-change redo hours
- `O_dollars` = unused seat or infrastructure cost
- `O_hours` = coordination and cleanup hours

Then:

```text
Real ROI = (T_hours × R + C_dollars)
           ÷
           (L_dollars + H_hours × R + O_dollars + O_hours × R)
```

A result of `1.0` is break even.

### Time Returned

For each selected thread:

```text
time_saved = baseline_minutes - confirmed_harness_minutes
```

Negative values are allowed.

For unselected threads, estimate missing values from selected threads of the same work type. Use the mean time saved per selected thread of that type. If no selected thread exists for that type, mark the value missing rather than inventing it.

Report selected, inferred, and missing coverage separately.

### Counting Rules

- If new capacity used time the Harness saved, count those hours under `C`, not `T`.
- If a baseline comes from records, label it `measured`.
- If a baseline comes from participant memory, label it `estimated`.
- If a value is unknown, leave it missing.
- Do not replace missing values with zero unless the participant explicitly said zero.
- If the denominator is zero, report the ratio as undefined.

### Report Outputs

Produce:

- `real-roi-report.md`: one-page decision report
- `roi-summary.csv`: term-level totals and coverage
- `assumptions.md`: judgment calls and missing data

The report should include:

1. the Real ROI ratio
2. `T`, `C`, `L`, `H`, and `O`
3. evidence quality by term
4. coverage and missingness
5. sensitivity results
6. non-monetized benefits left out of the ratio
7. the renewal judgment and who made it
8. what the unit would decide differently

## Privacy And Security Controls

### Local Controls

- Restrict the Real ROI folder to the local user.
- Store any local HMAC secret in the Harness secret store or macOS Keychain.
- Do not write credentials to `config.json`.
- Delete pending records after submission or rejection.
- Delete local individual records on the agreed retention date.

### Central Controls

- Store responses in a UCSD Shared Drive.
- Disable public link sharing.
- Restrict the response Sheet to the pilot analysis team.
- Store the identity map in a separate restricted location.
- Do not use email as the participant identifier.
- Suppress small-group breakdowns.
- Review access before the pilot, midway through, and at closeout.
- Delete individual records on the agreed retention date.

### Google Sheets Caveat

Google Sheets version history can retain deleted values. The consent form should say:

- individual records will be deleted on the retention date
- version history may persist under the administrator-controlled retention policy
- only aggregate totals will be kept after the retention date

For a durable institutional system, replace the Sheet with a campus-managed database that supports controlled deletion and audit logs.

## n8n Workflow Design

### Nodes

```text
Schedule Trigger
  -> Set Reminder Content
  -> Send Email or Teams Message
```

### Configuration

- Run once per week.
- Send to a pilot alias or Teams channel.
- Include the local check-in prompt and Google Form link.
- Do not include participant codes in the message body.
- Do not collect responses in n8n.
- Disable unnecessary execution-data retention.
- Test that the workflow does not write participant data to logs.

### Future Enhancement

If direct Google Sheets integration is added later:

1. Add an approved Google credential.
2. Use a service account or restricted OAuth account.
3. Write only allowlisted fields.
4. Validate the record schema before writing.
5. Disable or prune execution data.
6. Test access and retention before production use.

## Testing Plan

### Unit Tests

Test:

- metadata parser allowlist
- timestamp parsing and timezone conversion
- gap merging
- overlap splitting
- thread selection
- deterministic random selection
- negative time savings
- missing-value handling
- ROI calculation
- denominator of zero

### Privacy Tests

Create synthetic session files containing:

- message content
- attachment names
- file paths
- credentials
- thread titles

Verify the parser and submission packet exclude all of them.

### End-to-End Test

Use one volunteer and synthetic or real metadata:

1. Run the weekly check-in.
2. Confirm the record.
3. Submit through the Google Form.
4. Verify the response Sheet.
5. Verify the local submission log.
6. Verify no raw content appears centrally.
7. Calculate a test ROI.

### Access Test

Confirm:

- participants cannot read one another's responses
- the analysis team cannot read the identity map
- the record holder cannot see unnecessary report drafts, if separation is required
- link sharing is disabled
- the retention date is documented

## Milestones

### Days 1-5: Governance And Approvals

- Confirm pilot scope.
- Confirm record holder.
- Confirm standard hourly rate.
- Confirm P2 storage approval.
- Confirm retention period.
- Approve consent language.
- Agree on work types.
- Agree on the ten-minute gap cutoff.
- Confirm the pilot alias or Teams channel.

Exit criteria:

- written pilot approval
- signed consent process ready
- storage and identity-map locations approved

### Days 6-10: Metadata Spike

- Build the metadata-only parser.
- Test it against synthetic logs.
- Confirm turn-boundary extraction.
- Confirm derived-minute calculation.
- Confirm no content is emitted.

Exit criteria:

- parser passes privacy tests
- derived minutes reconcile on synthetic cases

### Days 11-15: Skill Scaffold

- Initialize `measure-real-roi`.
- Write `SKILL.md`.
- Add protocol, governance, and calculation references.
- Add consent and interview templates.
- Add cost and capacity intake templates.

Exit criteria:

- skill validation passes
- a fresh agent can follow the setup and weekly workflow

### Days 16-20: Local Check-In MVP

- Implement thread selection.
- Implement the weekly questions.
- Implement local confirmation and storage.
- Implement submission summary.
- Implement record validation.

Exit criteria:

- participant can complete a check-in locally
- confirmed record matches the displayed table
- no unconfirmed data can be submitted

### Days 21-25: Form, Sheet, And n8n

- Create the Google Form.
- Create the protected response Sheet in Shared Drive.
- Configure validation and access.
- Build the n8n weekly reminder.
- Test the reminder.

Exit criteria:

- form writes correctly to the response Sheet
- reminder arrives on schedule
- n8n logs contain no check-in answers

### Days 26-30: Volunteer Dry Run

- One volunteer completes a real week.
- Measure check-in duration.
- Fix confusing questions and metadata errors.
- Confirm privacy controls.

Exit criteria:

- check-in takes ten minutes or less
- participant understands what is saved and submitted
- no content leakage

### Days 31-72: Six-Week Pilot

- Run weekly check-ins.
- Send weekly reminders.
- Track skipped weeks.
- Collect institutional costs.
- Collect new-capacity descriptions.
- Conduct closing interviews.

Exit criteria:

- sufficient confirmed records to calculate a pilot ratio
- skipped weeks and missing values documented

### Days 73-80: Calculation And Review

- Aggregate responses.
- Apply cost and capacity data.
- Calculate `T`, `C`, `L`, `H`, and `O`.
- Run sensitivity checks.
- Draft the one-page report.
- Review with the unit and OSI.

Exit criteria:

- report explains the ratio and its limitations
- decision owner records the renewal judgment

### Days 81-90: Decision And Cleanup

- Decide whether to extend the method.
- Delete individual records on the approved schedule.
- Keep only aggregate totals.
- Document changes needed for institution-wide use.

Exit criteria:
- pilot decision recorded
- retention actions completed
- next-step recommendation written

## Acceptance Criteria

The pilot implementation is successful if:

1. A participant can complete the weekly check-in in ten minutes or less.
2. Every submitted record was explicitly confirmed by the participant.
3. No message content, thread title, raw session ID, file path, or attachment name is submitted.
4. The central dataset contains no names or email addresses.
5. The identity map is stored separately from the analytical data.
6. The calculation reconciles every input to the report.
7. Missing data is reported rather than silently replaced.
8. The final report states the ratio, evidence quality, and judgment calls.
9. The unit can decide whether to continue, change, or stop the measurement.

## Risks And Mitigations

| Risk | Mitigation |
|---|---|
| Participants cannot recognize threads without titles | Show date, time, turn count, and minutes; allow manual selection from Harness history |
| Derived minutes overcount multitasking or idle time | Require participant confirmation and run cutoff sensitivity checks |
| Counterfactual baseline estimates are weak | Label baseline method and confidence; avoid presenting the ratio as audited financial ROI |
| Small group makes people identifiable | Use aggregate reporting and suppress small breakdowns |
| Google Sheet version history retains deleted values | Disclose retention policy; use a database for durable rollout |
| n8n logs retain answers | Keep answers out of n8n in version 1; test retention before any direct integration |
| Cost and human hours are double-counted | Define term boundaries and reconcile all inputs before calculating |
| Process change is confused with AI impact | Record workflow changes in the judgment section |

## Open Decisions

1. Who is the record holder?
2. What is the standard hourly rate?
3. What is the retention period for individual records?
4. Which UCSD Shared Drive will hold the response Sheet?
5. Who owns the Google Form and response Sheet?
6. What pilot alias or Teams channel receives reminders?
7. What work-type list does the pilot group agree to?
8. What valuation method does the unit lead accept for `C`?
9. What six-week `L` allocation does budget or IT approve?
10. Who signs the final pilot decision memo?

## Immediate Next Steps

1. Confirm the record holder and retention period.
2. Confirm the Shared Drive location and form owner.
3. Confirm the standard hourly rate.
4. Draft the consent form.
5. Run the metadata parser spike.
6. Build the local skill MVP.
7. Create the Google Form and n8n reminder.
