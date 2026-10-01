# On-Prem Model Policy

This skill handles Senate Chair correspondence, cases, and scheduling, so it
runs only on models hosted on UCSD-controlled infrastructure. Do not use it
with commercial cloud models.

## Policy

This skill does **not** maintain a list of approved model names or versions.
The approved set changes as TritonAI deploys new on-prem models, and it differs
between harness environments. Never treat a model name written anywhere in
this skill as authoritative.

## Verification

1. Before any task, read the session's selected model from the current runtime
   information.
2. Confirm that the selected model is a UCSD-hosted on-prem model according to
   the current harness environment's approved-model configuration. That list
   is maintained by the TritonAI team outside this skill.
3. If the selected model is confirmed on-prem, proceed.
4. If the selected model is not on-prem, or you cannot verify its hosting,
   stop. Do not read mail, Drive files, calendar, or case content. Tell the
   Chair: "This skill is limited to UCSD on-prem models. Switch to the
   environment's approved on-prem model and try again."

## Data boundary

- Mail, Drive documents, calendar, case, and answer-bank content stays within
  the approved on-prem model session.
- Do not send Chair content to any other model, service, or endpoint.
