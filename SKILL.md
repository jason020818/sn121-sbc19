---
name: morning-read
description: Turn a seller's calendar, open-deal ledger, and attached notes into a concise daily pipeline briefing. Use only supplied facts, surface the few seller moves that can change outcomes today, and keep waiting states and record problems visible without inventing detail.
---

# Daily pipeline briefing

Write the page a seller reads before starting the day. This is triage, not a CRM recap.
Return the finished briefing first.

The handoff is the evidence boundary. Never invent a person, role, date, amount, contact
path, stage, deadline, commercial term, reason, or instruction. Omission is better than
plausible detail.

## Build a clean working view

Before writing, silently reconcile the handoff.

- Prefer an explicit human correction when it clearly corrects a structured field.
- Treat recency as stakeholder interaction, not merely system or workflow activity.
- Use a date, elapsed-time statement, count, or amount only when it is directly supported
  or safely derived from unambiguous source values.
- Do not calculate or print an aggregate pipeline value unless the handoff itself provides
  that total explicitly. Deal count is enough.
- If a field conflict prevents a reliable conclusion, keep the uncertainty visible rather
  than resolving it by guess.

For each open deal, silently identify:

1. the next meaningful event, decision, deliverable, or information gap;
2. who owns that next step, if the handoff says;
3. any explicit timing or communication constraint;
4. whether seller action today can materially change the state;
5. whether today's calendar already supplies the needed interaction.

## Assign each deal once

Before composing prose, assign every open deal to exactly one working bucket:

- `ACTION` — seller work today can materially change the outcome or remove a real blocker;
- `MEETING` — today's scheduled interaction is the useful work for that deal;
- `MONITOR` — a credible next event, owner, or waiting state exists and no seller move is
  worth a seat today;
- `RECORD` — internal data repair is the only useful next step.

This assignment is exclusive. Once a deal is assigned, do not print that deal name in a
second operational section. If a record issue belongs to an ACTION or MEETING deal,
mention it inside that line instead of repeating the deal elsewhere.

## Lock the action count before writing

Count genuine `ACTION` deals before producing the briefing. Call this number `N`.

- Print exactly `N` action items, subject to a maximum of three in `Priority Actions`.
- If `N` is 0, omit the action section.
- If `N` is 1 or 2, print 1 or 2. Never fill unused seats.
- If `N` is greater than 3, put the best three in `Priority Actions` and the remainder
  in `Other Actions Today`.

A deal is not actionable merely because it is large, old, late-stage, or quiet. Give
strongest consideration to consequence if today passes, explicit timing, whether the
seller owns a blocker, and whether one seller move can actually change the state.

If another party owns the next step and the handoff shows a credible process or expected
event, respect that state. If timing has become material but no usable return date exists,
one precise request for timing may be appropriate.

An explicit do-not-contact or channel instruction overrides all default outreach logic.

## Ground every action

Each action line should contain:

- one deal;
- one concrete seller act;
- one recipient only if that person or role is explicitly supplied;
- one ask or deliverable;
- one grounded reason it matters today.

If no recipient or role is supplied, do not invent one and do not choose a channel.
State what owner or information must be identified.

Prefer verbs that perform the work: send, answer, schedule, confirm, request, identify,
prepare. Avoid generic language such as "follow up", "touch base", or "check in".

Do not invent exact response deadlines, signature dates, escalation dates, pricing
structures, concessions, fallback offers, product claims, or stakeholder duties.

## Meeting Prep

A scheduled customer interaction replaces a separate outbound action for the same
objective.

For each meeting, use only source-supported material:

- objective;
- central question, decision, or blocker;
- named attendees and roles from the handoff;
- next step or fallback only when the handoff supports it.

Do not manufacture negotiation positions, pricing options, product details, or internal
approval strategy. Mark internal meetings as internal.

## Monitor and record sections

`Monitor` is for defensible waiting states. Name only the important holds or constraints;
group the ordinary remainder compactly. Do not turn Monitor into a second CRM export.

`Needs Record Update` is for internal-only repairs. State the unreliable field and what
would resolve it. Do not repeat deals already printed under actions or meetings.

Internally account for every open deal, but the finished page does not need to restate
every row individually when a grouped monitor line is sufficient.

## Page shape

Use only sections that contain useful content. Omit empty sections and empty-state
boilerplate. If a customer meeting starts within the hour, put Meeting Prep before
Priority Actions.

```text
# Daily Briefing - <Weekday, Month D>
[omit date if the handoff does not establish one]
[optional one-line urgency note for an imminent customer meeting]

## Pipeline Health
Open-deal count, number of genuine seller moves today, and the dominant named exposure,
constraint, or risk. Do not compute a pipeline sum unless the handoff gives one.

## Priority Actions
Exactly min(N, 3) genuine seller moves.

## Meeting Prep
Today's scheduled conversations in time order. Internal meetings marked internal.

## Other Actions Today
Only when N > 3.

## Monitor
Important named holds or waiting states, then one compact grouped remainder when useful.

## Needs Record Update
Internal-only repairs for deals not already handled elsewhere.
```

Target 220-300 words. Hard ceiling 360 words. Prefer omission over padding.

## Extra requests

If the user also asks for a forecast, model, or adjacent analysis, finish the briefing
first. Then provide only conclusions that can be computed directly from the supplied
handoff. If assumptions are required, state the missing assumptions briefly instead of
inventing them.

## Final audit

Before printing, silently verify:

- `ACTION` count in the output equals the locked count `N`;
- no deal name appears in more than one operational section;
- every printed person, role, date, amount, contact path, deadline, and commercial detail
  is grounded in the handoff;
- no aggregate pipeline sum was calculated unless the handoff supplied the total;
- no scheduled meeting deal is duplicated as outbound work;
- explicit waiting and communication constraints are respected;
- no unsupported recipient, channel, deadline, concession, fallback, or product detail
  was created;
- the answer is within 360 words;
- no empty section remains.
