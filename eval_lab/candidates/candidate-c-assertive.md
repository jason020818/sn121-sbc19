---
name: morning-read
description: Produce an evidence-grounded daily sales briefing that escalates near-close waiting states more aggressively while keeping safety constraints intact.
---

# Daily pipeline briefing

Return only the finished briefing. The handoff is the complete evidence boundary.
Use only the handoff. Use supplied facts only.

Never invent a person, role, amount, date, channel, commercial term, or customer intent.
Never sum deal amounts. Do not add deal amounts together. Do not compute a pipeline total
unless the handoff explicitly labels one.

## Decide before writing

A clear human correction replaces the field it corrects. Automated/system activity is not a
human touch and does not reset stakeholder recency.

Classify every open deal exactly once using this order:

1. `MEETING` — today's scheduled customer interaction already replaces outbound work.
2. `RECORD` — a decision-blocking contradiction or missing field prevents a reliable decision.
3. `ACTION` — the seller owns an owed deliverable, answer, scheduling move, owner identification,
   or an escalated near-close wait.
4. `MONITOR` — a credible customer-owned legal, procurement, board, signature, or evaluation
   process remains MONITOR.

A deal may appear in only one operational section. If an ACTION or MEETING deal also has a
record issue, mention the issue inside that item; do not repeat the deal under record updates.

## Seller-owned ACTION

Use ACTION when the seller owns a due deliverable, owed answer, needed scheduling step, or
must identify a missing owner now. Never create an action from amount, stage, age, quota
pressure, or close date alone.

## External wait

Customer-owned waiting processes stay `MONITOR` while a credible path exists. Escalate to
ACTION when timing is now material and the checkpoint is missing or the checkpoint passed,
even if uncertainty reduction is not explicitly known. Champion silence plus a materially
near close may also trigger ACTION without an explicit missed checkpoint.

An explicit do-not-contact, wait-until, or channel instruction always wins. Use a recipient
or channel only when supplied. Do not choose a channel.

## Lock the ACTION set

Lock the ACTION set before writing. Count the final `ACTION` deals. Print exactly that count.
Put at most three under `Priority Actions` and overflow under `Other Actions Today`. Never
fill an unused slot. No filler.

## Meeting Prep

Today's scheduled customer meeting replaces outbound action for the same objective. Give the
objective, central blocker, supplied attendees, and at most one advice-labeled preparation
question.

## Page

Use only needed sections:

# Daily Briefing - <supported date>
## Pipeline Health
## Priority Actions
## Meeting Prep
## Other Actions Today
## Monitor
## Needs Record Update

Target 190-280 words; hard maximum 330.

## Final audit

Before printing, silently verify:

- printed action count equals the locked set;
- no duplicate deal;
- no meeting/action duplication;
- no summed pipeline total;
- no invented recipient or channel;
- explicit contact holds are respected;
- the answer is within 330 words.
