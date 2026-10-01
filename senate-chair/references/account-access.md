# Chair Account Access

The Chair has two university accounts: a personal university Outlook account
and the Senate Chair Outlook account. Senate Chair operations use the
**Senate Chair account** for all Senate business.

## Account scope

- **Default and recommended:** Senate Chair Outlook account for mail and
  calendar.
- **Not for Senate business:** the Chair's personal university Outlook
  account. Never read it for intake or scheduling through this skill.
- **Still prohibited:** any other shared, delegated, or departmental mailbox
  or calendar.

## Setup linking (ease of use)

During setup, ask one question with the recommended choice first:

> Which email account should Senate Chair operations use?
> 1. Senate Chair Outlook account (recommended)
> 2. Personal university Outlook account
> 3. Gmail
> 4. Intake folder and pasted text only

Then verify the link before recording it:

1. Check which Outlook account the Harness integration is connected to and
   show the Chair its address.
2. If it is the Senate Chair account, ask the Chair to confirm with one yes.
3. If it is the personal account, guide the Chair to connect the Senate Chair
   account in Harness account settings, then confirm the new address. Do not
   proceed on the personal account for Senate business.

Record the scope with `--account outlook-chair` (or `outlook-personal`,
`gmail`, `none`) and the display address with `--account-address`. Setup
stores only the label and display address — never credentials or OAuth
tokens.

## Mail

- Use only the account scope recorded in `config.md` as `Linked account`.
- If setup selected intake-folder-only, do not read mail or calendar.
- Search and read the linked mailbox for intake and for messages the Chair
  refers to.
- Draft replies in the conversation first; save to the mailbox only as an
  unsent draft when the Chair asks.
- Never send, reply, reply-all, forward, or delete.
- Treat message content as confidential; do not quote it into any file
  outside the data root.

## Calendar

- Read the linked calendar to answer availability and schedule questions.
- Before creating or changing an event, show the Chair the full details:
  title, date, time, attendees, and location.
- Create or change the event only after the Chair confirms. Note that
  invitations go to attendees when the event is saved.
- Never modify another person's calendar.

## Fallback

If no integration is connected, work from the intake folder, the linked
Google Drive repository, and pasted text, and tell the Chair which capability
is unavailable.
