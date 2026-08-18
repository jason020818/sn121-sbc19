---
name: morning-read
description: Compose a concise seller daily briefing from the supplied calendar, open deals, and notes using a single-pass decision procedure and strict evidence grounding.
---

# Daily pipeline briefing

Return the finished briefing only. Use supplied facts only. Omit anything you cannot support.

Never invent entities, contacts, roles, dates, amounts, deadlines, channels, commercial
terms, or customer intent. Never calculate a pipeline sum; only repeat a total explicitly
labeled by the handoff.

## Build the silent deal ledger

For each open deal, record only:

- corrected current facts;
- next meaningful event or information gap;
- owner of that next step, if supplied;
- timing/contact constraints;
- whether today's calendar already covers the interaction;
- one primary disposition: `ACTION`, `MEETING`, `MONITOR`, or `RECORD`.

No deal may have two dispositions.

Use the following decision sequence.

### 1. Calendar coverage

If a scheduled customer meeting today performs the useful interaction, assign `MEETING`.
Do not also create outbound work for that objective.

### 2. Decision-blocking record problem

If a contradiction or missing field prevents a reliable operating decision, assign `RECORD`.
A human correction is authoritative for the field it clearly corrects. System/automated
activity does not reset stakeholder recency.

### 3. Seller-owned move

Assign `ACTION` when the seller can materially change the state today by completing an
owed deliverable, answering a request, scheduling a needed interaction, identifying a
missing owner, correcting an operational blocker, or obtaining time-sensitive information.

### 4. Externally owned state

Otherwise assign `MONITOR`.

A customer-owned legal/procurement/board/signature/evaluation process remains MONITOR while
it has a credible current path. A single timing/status ask becomes ACTION only when all are
true: timing now matters, no usable checkpoint exists or the checkpoint passed, and the ask
would materially reduce today's uncertainty.

Amount, age, stage, quota pressure, and close proximity are ranking context, never sufficient
action triggers by themselves.

An explicit wait/do-not-contact/channel constraint always wins.

## Action selection

Lock the ACTION set before writing. Rank only those actions by:
1. consequence of waiting today;
2. explicit timing;
3. seller control over the blocker;
4. information gained.

Print exactly the locked actions: top three under `Priority Actions`, overflow under
`Other Actions Today`. Never manufacture a third item.

For every action, use a concrete verb and a grounded ask/deliverable. Do not choose a
recipient or channel unless supplied.

## Meetings and records

Meeting Prep contains source-supported objective, central decision/blocker, supplied
attendees, and one useful preparation question when warranted. Advice must not be presented
as customer fact.

Needs Record Update contains only record-only deals. Embed record issues inside ACTION or
MEETING items instead of duplicating the deal.

## Output shape

Use only non-empty sections:

# Daily Briefing - <date if established>
## Pipeline Health
## Priority Actions
## Meeting Prep
## Other Actions Today
## Monitor
## Needs Record Update

Do not sum money. Keep ordinary Monitor items grouped. Target 200-275 words; hard maximum
325 words.

Final check: every deal appears in at most one operational section; printed action count
matches the locked set; all names/amounts/dates/channels are grounded; meeting work is not
duplicated; explicit communication holds are respected.
