---
name: morning-read
description: Draft a seller's daily sales briefing from a calendar, an open-deal ledger, and attached notes. Return only the finished briefing. Inventing a name, date, amount, contact, or fact is worse than leaving it out. Rank work by whether a seller action today changes the outcome, not by how busy the list looks.
---

# Daily pipeline briefing

Write the page a seller reads before outbound. The job is triage, not CRM recap.
Treat the handoff as the entire world: if a name, title, date, amount, contact, or
fact is not in the handoff, do not invent it. Return only the finished briefing. No
preamble, no ranking narration, no restated source table.

## Ground truth

- Prose notes, footnotes, and typed corrections override contradictory CRM fields.
- A system timestamp is not a human conversation. Count quiet from the last human
  exchange, not from auto-logs, sequence steps, or receipt stamps.
- Requested quiet periods must be respected until they expire against the handoff's
  as-of date. A seller being out does not stop the buyer's clock.
- A live legal, procurement, security, or signature process is not stale just because
  it is old. Monitor it unless the seller still owes something.
- A booked meeting for today covers that deal. Fold any pre-meeting send into Meeting
  Prep. Do not also give the same deal an outbound action seat.
- Seller-owed artifacts or answers are actionable unless the same deal is already
  covered by today's meeting.
- Rumor can raise attention around an existing fact pattern, but it cannot become a
  fact on the page.
- Never use generic verbs like "follow up", "touch base", or "check in."

## Internal decision procedure

1. Establish the handoff's as-of date/time from explicit briefing context. If no usable
   briefing date exists, omit the date from the heading.
2. Reconcile prose corrections against structured fields and keep the corrected value.
3. Enumerate all open deals exactly once.
4. Detect broken records: contradictory dates, retracted activity, missing owner on a
   next step, unreadable amount, or fields that prevent triage.
5. Separate deals already covered by today's calendar into Meeting Prep, including any
   pre-meeting artifact the seller still owes for that conversation.
6. Classify every remaining deal into exactly one bucket:
   - `ACTION`: seller action today can change outcome or unblock meaningfully.
   - `MONITOR`: named hold, live external process, or valid waiting state.
   - `RECORD-REPAIR`: the only useful act is internal CRM repair, with no outreach.
7. For each `ACTION`, assign one primary reason:
   - `P1` seller-caused blocker or seller-owed artifact
   - `P2` unresolved blocker on an explicit close date that is today, within 5 working
     days, or inside a month/quarter/period the handoff actually names
   - `P3` expired requested pause or decision date now due/past due
   - `P4` unexplained human silence with no active process
   - `P5` missing data that can be obtained only by asking someone
   If a deal could fit more than one class, keep the lowest number. Do not invent a
   period boundary. If no close date or named period exists, do not use `P2`.
8. Rank actions first by priority class, then by: close proximity -> deterioration if
   delayed today -> exposure -> information gain.
9. Generate one concrete act, one recipient, one ask, and one why-today fact per line.
10. Silently audit the final briefing before printing it.

## Action rules

An `ACTION` must be real work for the seller today. Looks-busy is not enough.

- If the seller owes a document, link, answer, or approval, send or supply it.
- If a deal is near close and still blocked, target the blocker directly.
- If a requested pause has expired or a decision date is now due, re-engage against
  that clock.
- If missing data requires asking a person, that outreach is `ACTION` (`P5`), not
  `RECORD-REPAIR`. If the seller can fix the row without contacting anyone, it is
  `RECORD-REPAIR` only.
- If a deal has both a known owed artifact and a broken field, classify as `ACTION`
  and put the record issue in the same sentence. Do not list the deal twice.
- If legal or procurement owns the ball, monitor the live process. Ask that desk for
  a return date only when the file is idle with no date and the seller needs that
  answer today.

Channel must match the blockage:

- Write when the artifact or precise question is the point.
- Call when the deal is materially exposed, human-silent, close, and nothing forbids
  a call.
- Do not call when the handoff says not to.

## Record and amount rules

Internal-only broken rows go to `Needs Record Update`, not into fake certainty. State
what is wrong, which date/value you used if one source overrode another, and what
would repair it. Do not also dump ACTION or Meeting Prep deals into this section.

Aggregate amount only if every relevant open deal has a readable amount in the same
currency and the total can be derived directly. Never perform FX conversion without a
supplied rate. Otherwise report counts and named exposure only.

Working days mean Monday-Friday unless holidays are explicitly provided.

Meeting Prep is an objective, an ask, and a fallback: who is in the room, what they
control, and the two things to hold. Internal 1:1s and reviews stay here and are
marked internal.

## Page shape

Keep these section names and meanings when a section is present. Omit any empty
section, including `Top 3 Actions` when there is no outbound action. Do not print
boilerplate empty-state lines. If `Top 3 Actions` already contains every actionable
deal, omit `Tier A - Other Deals Needing Action Today`.

Default order: Pipeline Health, Top 3 Actions, Meeting Prep, Tier A, Tier B, Needs
Record Update. If a customer meeting starts within the hour, put Meeting Prep before
Top 3. If the requester asks for a reasonable variant, change only order, density, or
date format. Do not drop triage content to satisfy a forecast or other format.

```
# Daily Briefing - <Weekday, Month D>
[omit the date from this heading if no usable briefing date exists]
[italic line only if a customer meeting starts inside the hour]

## Pipeline Health
  Count open deals, count actions due today, and name the dominant exposure.
  Include a total only when every included open deal has a readable amount in the
  same currency.

## Top 3 Actions
  At most three outbound seats. No calendar-covered deal. One sentence each.
  Fewer than three is correct when fewer than three are warranted.

## Meeting Prep
  Booked conversations in time order. Internal marked. Pre-meeting sends named here.

## Tier A - Other Deals Needing Action Today
  Remaining actionable deals beyond Top 3 only.

## Tier B - Monitor
  Named holds, live external processes, and valid waiting states.

## Needs Record Update
  Internal CRM repairs only. Each row: what is wrong, which value you used,
  what would repair it.
```

Typical length is 180-380 words. Hard max 450. Never add filler to hit a target.

## Silent pre-output audit

- Every open deal is accounted for exactly once, in one section only.
- No meeting deal is duplicated as outbound; pre-meeting sends stay in Meeting Prep.
- No invented people, dates, amounts, contacts, or facts.
- All dates and amounts are grounded in the handoff or validly derived from it.
- No mixed-currency total.
- Requested holds are respected.
- Live external processes are not mislabeled as stale silence.
- Each action states one act, one recipient, one ask, and why it matters today.
- No generic follow-up language.
- No empty sections.
