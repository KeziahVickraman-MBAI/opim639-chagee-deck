# brief-v2.md: revisions after reviewing chagee_deck.pdf (v1)

Read after brief.md. Where this file and brief.md disagree, this file wins. Do not change sim/ results or assumptions.json values to suit any slide. Propose the plan first and wait for approval, then build one slide per prompt.

## 1. What was wrong with v1

1. The bucket brigade is a single sentence on slide 4. It is the mechanism behind the whole argument, so it must be shown and not described.
2. There is no problem-statement slide. The project brief asks for the company, the core processes AI can enhance, and the problem and its significance. v1 jumps straight into "why this slice".
3. The explainers show results but do not help a decision-maker act. There is no trigger, threshold or action. Example: "if machine cost, wages or milk price rise to X, do Y".
4. There is no contents slide and no progress indicator.
5. The scope is not visible. Topics 1, 2 and 8 are excluded, but the deck never shows that.
6. Honesty problems to fix:
   - The slide 4 headline says mixed beats full automation. The simulator also shows all-human is cheapest (S$0.61 vs S$0.64). Full automation at about 555 cups a day is a reference bound, not something Chagee does. Chagee already semi-automates.
   - The S$10m benefit is built on the mixed-vs-full-automation gap, which is not Chagee's real counterfactual.
   - The finding that machines sit idle (about 21% busy) comes from one assumed machine speed (about 15 s at the slowest station, about 4 cups/min). Show that dependency and where it flips.
   - Slide 3 cites "Week 1 newsvendor logic" while we exclude Week 1. Cite the concept ("newsvendor logic") and confirm against reference/ and the course outline which topic it belongs to.

## 2. The message the deck now carries

Chagee's sourcing is fixed, so new-store risk is in how much a store opens with and how it staffs its counter. A new store's demand is unknown, so machine capacity bought up front sits idle. People flex like a bucket brigade, and machines cannot be returned. Therefore: open lean, read the demand, and add machines on a trigger. The deck gives those triggers.

State openly that the hypothesis "mixed beats full automation until demand becomes predictable" was tested and the uncertainty part was rejected. The surviving finding is about volume and idle capacity. Do not present anything as proven.

## 3. Navigation (applies to every slide)

- A Contents slide after the title: six chapters with a one-line purpose and an on-stage time. Clicking a chapter jumps to it.
- A persistent progress rail on every content slide: Context, Scope, Predict, Provision, Perform, Decide. It highlights the current chapter, marks earlier ones as visited, and shows a slide counter. Arrow keys and clicks work.
- Print state: the rail prints as a header strip with the current chapter in bold.

## 4. Slide list

On stage: about 7 minutes, with 3 for Q&A. Appendix slides sit in the eLearn soft copy and the hard copy only.

Title, then Contents.

1. **Context and problem** (Context). Chagee scale facts from the ledger; the core processes involved (demand forecasting, opening inventory, counter service); the problem statement; significance (about 200 overseas openings planned). Read the rubric in OPIM639-Project.pdf and make the slide answer part (a) of the brief.
2. **Scope: what we left out and why** (Scope). A strip of the eight course topics, with Topics 1, 2 and 8 struck through and a one-line reason each (single closed app-to-store channel; no third-party sellers, no sell-vs-FBA choice, no channel conflict). Topics 3, 4 and 5 are highlighted and mapped to Predict, Provision and Perform. Take the topic names from the course outline in the uploads, not from memory.
   - Explainer: click a topic to see in or out and why.
   - Merge in v1's "Where does uncertainty land?" toggle (rigid vs localised sourcing), which is the "why this slice" argument.
3. **Predict**. Keep v1's explainer. Add a Decision strip.
4. **Provision**. Keep v1's explainer. Add a Decision strip.
5. **How a counter absorbs a surge** (Perform, part 1). A bucket-brigade explainer, shown not described.
   - Left: three workers on a line with handover points. Right: the same line as fixed-speed machines.
   - Controls: surge size, a play button, and a toggle for the slowest worker or station.
   - Show queue length, each station's utilisation and where the bottleneck sits. In the people line the handover point shifts and the load evens out. In the machine line the queue builds at the slowest station and cannot be reassigned.
   - Reuse the Week 5 bucket-brigade engine, read-only, for this mechanism. Label the slide: "Mechanism illustration. Cost figures come from the next slide's model."
   - Say plainly on the slide that the cost model uses pooled speeds, not this animation.
6. **Perform: which counter, and when to add machines** (Perform, part 2). The simulator result.
   - Add a second chart: cost per cup against cups per day for all-human, mixed and all-machine, with the break-even volume marked, or "none in range".
   - Keep the uncertainty chart, but state that uncertainty did not decide the result.
   - Show the dependency on machine speed and machine cost, with where the result flips.
   - Add a Decision strip.
7. **Decide: the playbook** (Decide). This is the call to action.
   - Left: a table of triggers (see section 5).
   - Right: a "Your market" panel. Inputs: wage per hour, machine monthly cost, milk cost, expected cups per day, forecast band. Output: a verdict (all-human, mixed, or add machines), the margin by which it wins, and which trigger is closest to flipping.
   - All thresholds come from sim/ break-even solves. If a threshold is outside any plausible range, write "no break-even in range: this choice holds everywhere".
8. **Benefit, risks, next step** (Decide). Rebuild the benefit calculator around "cost of choosing the wrong counter" per store, times openings. Name the counterfactual on the slide. Keep the four risks and the next step with real Chagee data.

Appendix: A1 assumptions table (from assumptions.json); A2 model and validation (Week 5 comparison, seed stability, sensitivity tornado); A3 source ledger and "claims we did not make".

## 5. Decision strip (on slides 3, 4 and 6)

A slim panel under the explainer with four fields: **Decision** (the question), **Who decides** (from the audience table in brief.md), **Trigger** (a number), **Action**. Triggers are computed live from sim/ and assumptions.json, never typed in. Slide 7 collects them all.

Example triggers to compute, if the model supports them:
- Wage per hour at which mixed overtakes all-human, or all-human overtakes mixed.
- Machine monthly cost at which all-machine matches mixed.
- Cups per day at which all-machine matches mixed (the volume trigger for adding machines).
- Forecast band width above which the opening order should be staged in two shipments.
- Staff turnover share above which the people-based counter loses its edge.

"Price" in the decision panel means input costs (wage, machine, milk). Menu price would need a demand-elasticity assumption we do not have, so flag it as out of scope and do not model it.

## 6. Build and checking rules

- Add a breakEven(param) function to sim/, with tests: it returns a value inside the swept range, or "none in range", and re-running the setup at the returned value shows the two setups equal within tolerance.
- Every trigger on slides 3 to 7 reads from sim/. No hand-typed thresholds.
- One slide per prompt. After each, report what you built, what you assumed and what you flagged. Check the print state of each slide page by page.
- Keep the footer "explainer figures are illustrative assumptions". Chagee facts carry a source in the speaker notes.
- Rehearse: eight content slides in about seven minutes is tight. Write the speaker notes for the on-stage path first and mark which slides can be skipped under time pressure (3 and 4 can be summarised in one sentence each).
