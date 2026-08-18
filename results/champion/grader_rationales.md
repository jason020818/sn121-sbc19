# Champion grader rationales

- submission_id: `06d07e60-50a7-4c39-bf0d-5183ab708bdd`
- miner: WeirdCrystal
- score: 0.76684
- evaluated_at: 2026-08-17T22:27:04.935Z
- retrieved_at: 2026-08-18T07:25:31Z

Champion SKILL.md was not copied into this repo. Public URL and sha256 are in metadata.json.

Rationales below are copied from the public validator JSON. They are not rewritten.

## Submission-level metrics

```json
{
  "avg_score_total": 0.7668400000000002,
  "skill_use": 0.875,
  "scenario_quality": 0.6778000000000001,
  "rubric": 0.6699999999999998,
  "skill_alignment": 0.9000000000000001,
  "novelty_check": 1,
  "dataset_derived": 0.75,
  "tests_count": 10,
  "total_tokens": 68774,
  "max_tokens_per_eval": 157000,
  "tokens_used": 68774,
  "samples_prorated": 0,
  "samples_zeroed": 0,
  "overall_gate_passed": 1
}
```

## S-001

- weighted_score: `0.7780000000000001`
- gate_passed: `True`

### skill_use (0.875)

The skill teaches highly specific, non-obvious distinctions — paper being drafted vs. paper sent, documented waits vs. elapsed waits, automatic logs vs. human contact, calendar coverage vs. outbound moves — and the agent applies all of them correctly: Bluewater is moved to 'move 3' with the right framing (ask for the date it returns, not assume it will), Meridian is left alone with the Oct 28 clause cited, Thornfield and Harmon are excluded from outbound slots because they're on the calendar, an

### scenario_quality (0.665)

The agent correctly excludes Meridian from urgent action, citing the documented 30-day eval period with Oct 28 ping date — the core edge case is handled well. However, the top-3 actions include Bluewater Shipping as move #3, which directly contradicts the domain knowledge criterion: Bluewater is in  | Base=0.665, penalties=0.00, final=0.665

### rubric (0.72)

The submission demonstrates solid domain knowledge and reasonable prioritization — Nightfall, Redwood, and Bluewater are correctly identified as the three moves, and the meeting prep for Thornfield and Harmon is directionally sound. However, several specific details undermine confidence: the pipeline total is stated as $1.583M rather than the correct $1.463M, Cascade Renewables is elevated to a Top 3 action despite being an 18-day follow-up that belongs in the 'also yours today' tier rather than displacing Bluewater, and the Redwood recovery suggestion (LinkedIn network, asking James at Meridian) reads as generic improvisation rather than the direct 'identify and call the replacement contact' that the situation demands. The Tier A/B structure adds organizational clarity but also introduces padding — the Thornfield entry in Tier A is redundant with the meeting prep section, and the footnote on Meridian, while technically correct, signals template-filling rather than confident judgment. The response is competent but not sharp.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

First sample in novelty group — no comparison

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-002

- weighted_score: `0.6685000000000001`
- gate_passed: `True`

### skill_use (0.875)

The skill teaches non-obvious distinctions that are clearly applied: Keystone Agri is correctly identified as 'paper coming' (seller's side drafting) and handled differently from Stormbridge (markup already sent to buyer), Fenwick is moved to 'also yours today' as an owed deliverable rather than a contact move, and Thornton Legal is left alone because the follow-up demo is already booked — all of which require the skill's specific reasoning rather than generic sales judgment. The output also cor

### scenario_quality (0.4)

The agent elevates Keystone Agri to Tier A (one of the 'Three moves') despite verbal agreement being received and contracts coming — the rubric explicitly states Keystone should be Tier B because verbal is received. This is a meaningful domain judgment error. The agent also produces 5 action items ( | Base=0.400, penalties=0.00, final=0.400

### rubric (0.62)

The submission demonstrates reasonable domain knowledge and identifies the right high-priority deals, but contains a notable factual error — it reports pipeline at $1.825M when the source data shows $1.68M, and misattributes Fenwick Capital's close date as Apr 20 when no such date appears in the source. The Keystone Agri deprioritization to Tier B is a meaningful judgment error: the source explicitly flags it as a five-minute action (send contract template today) because contracts are promised but not in motion, yet the submission treats verbal agreement as sufficient and parks it in monitor. The Tier B section is heavily padded with deals that add little triage value and reads like a template-filling exercise — listing 15 deals with boilerplate status notes inflates length without improving the rep's morning clarity. The reference response is more concise, more accurate on the Keystone action, and better calibrated on what actually needs doing today.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

First sample in novelty group — no comparison

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-003

- weighted_score: `0.7510000000000001`
- gate_passed: `True`

### skill_use (0.875)

The skill's non-obvious distinctions are clearly applied: Verdant is correctly identified as 'paper on the seller's side' (left alone in the ledger but here flagged to send the draft — actually a reasonable move since it's a proposal pending internal review), Solstice's contract markup is correctly treated as paper on a named desk warranting one return-date request, and all four calendar deals are excluded from the outbound slots with the reasoning made explicit. The agent correctly counts from 

### scenario_quality (0.575)

The agent correctly identifies Trident, Solstice, and Verdant as the top-3 outbound actions (not meeting prep items), demonstrating strong contextual judgment and proper domain handling of Sable Analytics as meeting-only. However, the output quality is partial — Trident and Solstice are well-handled | Base=0.575, penalties=0.00, final=0.575

### rubric (0.72)

The submission demonstrates solid domain knowledge and reasonable situational awareness — it correctly identifies the high-stakes Q2 concentration, surfaces the right three outbound actions, and provides useful meeting prep with specific tactical guidance (e.g., 'know your floor before walking in,' value anchor framing for Westbrook). However, it shows some template-like tendencies: the Tier A/Tier B segmentation adds structural overhead without meaningful analytical lift, and the redundant flagging of meeting deals (Northgate, Westbrook, Paragon) in a separate 'Tier A' block after already covering them in meeting prep reads as padding rather than insight. The Trident action is correctly framed as a stall-naming move, but the instruction to ask 'who owns the decision' adds scope beyond what the situation calls for — a 28-day silence calls for a single binary question, not a qualification probe. The Paragon note about the renewal/scope contradiction is absent, which the reference response handles explicitly and which matters for how the rep walks into that 3:30. Communication is competent but over-structured relative to the content density.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

Novel response (max similarity 0.405 < 0.75, group=A, compared against 1 prior)

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-006

- weighted_score: `0.7495`
- gate_passed: `True`

### skill_use (0.875)

The skill teaches highly specific, non-obvious distinctions — paper being drafted vs. paper on a buyer's desk, documented waits vs. expired waits, automatic logs not counting as contact — and the agent applies all of them correctly: Nexus Cold Chain gets 'one request for the date it returns' (paper on a desk), Coastal Carriers is left alone with the sabbatical date cited, Pacific Rim Cargo is flagged as untrustworthy rather than guessed at, and Polar Express is held because the freeze has no end

### scenario_quality (0.67)

The agent handles Pacific Rim Cargo's inconsistency well and correctly identifies ClearRoute and Nexus Cold Chain as high-priority based on close-date imminence. However, the top-3 ordering is wrong per the rubric — Seagate should be #1 (verbal intent, one email closes $200K), TerraFreight should be | Base=0.670, penalties=0.00, final=0.670

### rubric (0.62)

The evaluated response demonstrates solid pipeline coverage and reasonable triage logic, but makes several contextual errors that the reference avoids: it elevates TerraFreight Global to the #2 priority despite it being in final review with exec sponsor aligned (the reference correctly treats it as a secondary check-in), and it surfaces Polar Express Cargo as a top-3 action despite the reference explicitly categorizing it as a documented hold with no actionable move. The response also invents deals not present in the source data (Brightline Rail, BlueSky Freight, Granite Carriers, Ironwood Fleet, etc.), which is a significant fabrication problem that inflates apparent thoroughness while introducing noise a rep would have to filter. The Pacific Rim Cargo data integrity flag is correctly identified, and the Coastal Carriers sabbatical logic is sound, but the core prioritization misjudges which deals have genuine unblocking moves versus which are in legitimate waits — the defining skill the reference demonstrates cleanly.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

First sample in novelty group — no comparison

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-008

- weighted_score: `0.8134000000000001`
- gate_passed: `True`

### skill_use (0.875)

The skill teaches non-obvious prioritization rules — expired e-sign link beats larger deals, second-hand intel sharpens existing concern without being printed as fact, Stratum is excluded from outbound moves because it's already calendared, Thornwood is left alone with the clause named, and the Vertex last-activity date is flagged as untrustworthy rather than reasoned from. All of these appear correctly applied: Halcyon ranks first despite being smaller than Frontier because irreversible damage 

### scenario_quality (0.783)

The agent correctly ranks Halcyon #1 (expired e-sign link, 5-minute fix, agreed terms) and treats Vertex conference intelligence as a signal requiring direct action without overstating it as confirmed fact. However, output quality is docked because the Vertex action specifies a call but lacks a sugg | Base=0.783, penalties=0.00, final=0.783

### rubric (0.72)

The submission demonstrates solid domain knowledge and correct prioritization — Halcyon, Vertex, and Frontier are correctly identified as the top three moves with appropriate reasoning, and the Stratum Capital meeting prep adds genuine value by flagging the CFO-level dynamic around execution de-risking. However, the response shows several weaknesses relative to the reference: it misreads the Thornwood Gaming situation (calling it 15 business days when the reference correctly identifies 20, and recommending action when the reference explicitly leaves it alone as a structural ambiguity), it omits the critical data quality flag on Vertex's last-activity date discrepancy (the Mar 19 CRM date vs. the later scope send), and the Amber Grove action recommendation diverges from the reference's more targeted 'call your champion to understand scoring position' framing. The formatting is heavier than necessary — the Tier A/Tier B structure adds scaffolding without proportional insight — and the footnotes, while thoughtful on Vertex, read slightly templated. The core judgment is sound but the response misses the data integrity signal on Vertex, which is a meaningful operational detail in a sales ops context.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

Novel response (max similarity 0.586 < 0.75, group=D, compared against 1 prior)

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-010

- weighted_score: `0.6955000000000001`
- gate_passed: `True`

### skill_use (0.875)

The skill teaches highly specific, non-obvious distinctions — documented waits vs. elapsed waits, paper being drafted vs. paper on a desk, automatic logs vs. human contact, calendar deals never taking outbound slots — and the agent applies all of them correctly: Ashwood is left alone with the explicit 'asked not to be contacted' clause named, Cobalt is left alone because the champion confirmed active comparison (not just silence), Marshfield's Jul 11 log is flagged as machine-stamped and correct

### scenario_quality (0.69)

The agent correctly flags Arcadia urgency at the top, handles Ashwood Financial with a proper 'do not contact' note, and catches the Marshfield logging error — all three judgment tests pass partially or fully. However, the Arcadia meeting prep is generic ('bring the tier options and leave with a sig | Base=0.690, penalties=0.00, final=0.690

### rubric (0.42)

The submission contains several factual errors that undermine its reliability as a daily briefing: it states pipeline at $1.85M across 10 deals but the source material shows $1.65M, and it lists Arcadia at $415K and Northstar at $350K as 'highest-value near-term closes' while misreading Northstar's close date and mischaracterizing Arcadia's status. More critically, the Top 3 Actions list replaces the correct Cypress Analytics action with Cobalt Dynamics — which the source explicitly identifies as a named hold because the champion confirmed they are comparing vendors with a decision next week (i.e., the deal is moving on its own) — and the Ironhaven action prescribes a specific diagnostic question about pricing objections rather than the more situationally accurate read that 25 days of silence past a commercial ask likely means the deal has left the champion's desk entirely. The Northstar action ('confirm the board meeting is still scheduled') adds unnecessary noise to a deal explicitly flagged as needing no move, and while the Ashwood Financial handling is correct, the overall response reads as a confident template fill-in that introduces errors through over-prescription rather than demonstrating genuine situational judgment.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

First sample in novelty group — no comparison

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-009

- weighted_score: `0.8245`
- gate_passed: `True`

### skill_use (0.875)

The skill teaches non-obvious distinctions a general agent wouldn't know — documented waits vs. expired waits, paper-coming vs. paper-sent, booked meetings as coverage not moves, system logs not counting as contact — and the output applies all of them correctly: Caspian is left alone because the demo is booked (not just because it's upcoming), Sequoia is deferred with a specific Friday check-in because the champion's loop-in is a documented wait with a near close date, and Waverly gets a call fo

### scenario_quality (0.82)

The agent correctly limits Tier A to 3 deals and keeps Sequoia in a monitoring tier, demonstrating good calibration. Crownview is correctly ranked #1 and Waverly is treated as Tier A with contract-review urgency. However, the Waverly action says 'call the contract review owner and ask for a signatur | Base=0.820, penalties=0.00, final=0.820

### rubric (0.72)

The submission demonstrates solid domain knowledge and correct prioritization logic — Crownview as the highest-risk deal, Waverly as the near-close, and the quota math connecting them — but it over-explains its reasoning in ways that pad length without adding value (e.g., the rationale for contacting the deal contact rather than legal, the 'low-pressure re-entry' framing). The Maple Street action is weaker than the reference: asking about 'internal scoring process' is a generic discovery move rather than the sharper 'set a specific next step with champion' approach the situation calls for, and the submission incorrectly flags no hygiene issues when the reference correctly identifies Maple Street's missing next-step record as a data quality problem. The quota footnote at the bottom is useful but buries the math in a disclaimer rather than integrating it naturally into the briefing structure.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

Novel response (max similarity 0.690 < 0.75, group=B, compared against 1 prior)

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-005

- weighted_score: `0.811`
- gate_passed: `True`

### skill_use (0.875)

The skill teaches non-obvious distinctions a general agent wouldn't know — documented waits vs. elapsed waits, paper-on-seller's-desk vs. paper-on-buyer's-desk, calendar coverage vs. outbound moves, and human contact vs. system logs — and the output applies all of them correctly: Verdana is flagged as a window opening today (not just 'no response since Oct 15'), Meridian earns exactly one check-in on a settled deal rather than a full push, Bellwether is placed in 'Walking in' rather than the thr

### scenario_quality (0.775)

The agent correctly threads the Ironclad situation — missing next-step note plus imminent close means calling to find out IS the triage action, not a reason to exclude the deal. Prism Logistics is handled correctly as a record-update item rather than a confident triage. However, output_quality takes | Base=0.775, penalties=0.00, final=0.775

### rubric (0.72)

The response demonstrates solid domain knowledge and reasonable prioritization but contains meaningful errors that undercut its reliability: it includes Aurelia Healthcare as a top-3 action despite the briefing explicitly noting it is in a named hold (attorney review), which is exactly the kind of documented wait that should suppress action — this is a contextual judgment failure. It also misclassifies Meridian Ports as 'appropriate wait' when the e-sign link was sent yesterday and a quick check-in is warranted before the weekend, and it inflates the pipeline figure to $1.565M without clear basis. The communication is clean and the meeting prep advice (bring pilot configuration options with price anchors) shows genuine domain understanding beyond the reference, but the Aurelia misstep in particular reflects a template-driven 'flag anything with a close date' pattern rather than reading the actual signals present.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

Novel response (max similarity 0.719 < 0.75, group=C, compared against 1 prior)

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-004

- weighted_score: `0.8785000000000001`
- gate_passed: `True`

### skill_use (0.875)

The skill teaches non-obvious distinctions that appear directly in the output: Lynx Diagnostics (paper on buyer's desk, close enough to matter = one request for return date) is correctly separated from any seller-side drafting scenario; Holloway Beverages is flagged as a stale record rather than acted on, because the seller noted a call happened during PTO that the CRM hasn't caught — prose-over-table reasoning applied precisely. The 'three moves' vs. 'also yours today' split reflects the skill'

### scenario_quality (1)

The agent correctly identifies Lynx Diagnostics as the #1 priority (4 days to close, MSA outstanding, 15+ business days since last activity), places Cascadia second (champion dark, legal blocker, high reversibility risk), and Meridian third (largest deal, effective silence amplified by PTO). Critica | Base=1.000, penalties=0.00, final=1.000

### rubric (0.72)

The submission demonstrates solid domain knowledge and reasonable situational awareness — it correctly identifies the three highest-risk deals, flags the Holloway Beverages record staleness, and notes the PTO re-entry context. However, it makes several judgment errors that the reference avoids: it misclassifies Fairbanks Telecom as Tier B (monitor) when the reference correctly identifies it as needing a call today given 11 business days of silence on pricing, and it elevates Nova Semiconductor to Tier A action despite the reference correctly leaving it alone as a deal with documented next steps progressing on its own timeline. The Arbor Financial ICP follow-up is deprioritized to Tier B when it has a clear, low-effort action. The response is also over-formatted with headers and tier labels that add structural weight without adding analytical clarity, and the PTO re-entry framing — while not wrong — is used as a generic hedge rather than a precise signal, which reads more like template reasoning than genuine situational judgment.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

Novel response (max similarity 0.671 < 0.75, group=B, compared against 2 prior)

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

## S-007

- weighted_score: `0.6985000000000001`
- gate_passed: `True`

### skill_use (0.875)

The skill's non-obvious distinctions are clearly applied: the automated CRM send for Silica is correctly disqualified as human contact (counting from Jan 20 demo, not Jan 28 system send), Pinnacle and Opal are excluded from outbound moves because they're on today's calendar, and Crescent/Lumen/Obsidian are left alone with their specific documented-wait clauses named. The bottom-up forecast request is declined implicitly by omission, consistent with the skill's 'anything else is declined in a lin

### scenario_quality (0.4)

The agent correctly identifies the automated CRM email issue for Silica Systems and notes it explicitly, but miscounts the business days (says 12 instead of 15, treating Jan 28 automated send as the reference point rather than Jan 20 demo). Titanium Defense is ranked #2 rather than #1, which fails t | Base=0.400, penalties=0.00, final=0.400

### rubric (0.72)

The submission demonstrates solid domain knowledge and reasonable situational awareness — correctly identifying Titanium Defense as the highest-risk deal and flagging the automated vs. human contact distinction for Silica Systems. However, it introduces noise the reference avoids: the 'Tier A/Tier B' framework adds bureaucratic scaffolding that doesn't serve a rep's morning read, Quartz Financial is incorrectly elevated to near-action status (3 days since last contact, Feb 28 close — the reference correctly defers this to Thursday), and the disclaimer refusing to engage with the forecast is a missed opportunity since the reference shows a bottom-up forecast is entirely within scope and genuinely useful. The Titanium action recommendation (email vs. call) is a meaningful divergence — the reference correctly prescribes a call for a $340K deal with no gate date, while the submission defaults to email, which is the lower-commitment and likely less effective move for this urgency level.

### skill_alignment (0.9)

Appears genuine (alignment=0.900 >= 0.55). The skill teaches genuine domain reasoning through prose and decision logic rather than mirroring rubric structure: it explains the WHY behind screening out documented waits ('arriving early is the error'), distinguishing paper-coming from paper-sent, treating booked meetings as coverage not moves, and system logs not counting as contact. These map conceptually to the rubric's edge cases (Meridian dwell, Bluewater contracts, QBR meeting) but are framed as generalized principles with reasoning, warnings about common mistakes (inventing rows, believing false dates), and prioritization guidance — not as numbered checklists or self-check questions restating criteria. The lack of scenario-specific names/dates and the emphasis on teaching judgment strongly indicate genuine procedural writing; the only minor concern is how neatly the four carveouts anticipate the exact rubric edge cases, but they read as domain heuristics rather than reverse-engineered lookup tables.

### novelty_check (1)

Novel response (max similarity 0.114 < 0.75, group=C, compared against 2 prior)

### dataset_derived (0.75)

Appears general. (score=0.750, mapped=6 of 10). 6 suspicious rules. 5 beyond-dataset items. The skill is written almost entirely at the level of principles and mechanisms rather than as a lookup table, and several of its rules (contact-recency heuristic, two-axis ranking, epistemic handling of second-hand reports) would generalize cleanly to novel scenarios not in the dataset. However, the four 'screened out' categories read like a closed catalog of the dataset's specific traps — the 'system did not talk to anyone' rule maps almost 1:1 to S-007's auto-log mechanic, 'a stretch of time they were away' to S-004's PTO, and the enumerated document states (redlines back, e-sign pending, review running) mirror the exact edge cases in S-001/S-007/S-008. The suspicious signal is that these four screens plus the two ranking axes together cover the distinctive gotcha of essentially every hard scenario, suggesting the author knew which traps to pre-empt. Still, the phrasing is abstracted rather than scenario-fitted and the framework leaves room for new situations, so this is moderately-general rather than clearly dataset-copied.

