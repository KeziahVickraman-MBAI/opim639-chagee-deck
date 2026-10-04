# brief.md — OPIM639 Group Deck: Chagee

Read this together with CLAUDE.md. This file is the source of truth for content. If something is not here and not in assumptions.json, ask before inventing it.

---

## 1. Project in one paragraph

SMU MBAI course OPIM639 (Innovations & Operations of Intelligent Online Marketplaces). The group project is a strategic business plan with execution steps for an existing company: (a) the company, its core processes, and the problem AI can enhance, with impact and significance; (b) how we solve it; (c) the size of the benefit. Assessment is a 10-minute presentation including Q&A, plus a report of at most 6 pages. Slides are submitted as a soft copy on eLearn and a printed hard copy is handed to the instructor, so every slide must also work as a static page.

Company: Chagee (NASDAQ: CHA), the premium tea chain. Spell it "Chagee" everywhere.

Group members: TBC (confirm with the team before finalising the title slide).

## 2. The one claim

**In a new market, a mixed people-and-machine counter beats a fully automated one until demand becomes predictable.**

Why it might hold: a machine runs at a fixed speed and cannot be reassigned, so a surge piles up behind its slowest station. People can shift between stations, the way a bucket brigade rebalances itself (Week 5 logic). If demand turns out low, a machine-heavy line also sits idle after the cost is paid.

**This is a hypothesis, not a result.** The crossover must be computed by the simulator. If the simulator does not show it, change the headline, not the numbers, and tell me.

## 3. Why this slice (the argument for slide 1)

- Chagee's upstream is rigid by design: single-origin Yunnan tea, own plantations, centrally managed distribution, a narrow menu, and standardised SOPs. Sourcing is not where the flexibility is.
- Chagee is scaling fast into markets it has not operated in. With sourcing fixed, new-market uncertainty lands on two things: how much a new store opens with, and how fast its counter can serve.
- Today the opening forecast is judgment-led by a local General Manager, and service is moving toward automation.
- This is our inference from public facts, not a Chagee statement. Phrase it as "our reading".

Why we skip Weeks 1-2 and 8: Chagee runs one closed channel (app to store), with no third-party sellers, no sell-vs-FBA choice and no online-vs-offline channel conflict. The franchise GMV revenue share is the one place Week 2 touches. Footnote it as out of scope.

## 4. Audience (decision-makers inside Chagee)

| Who | Decision | What we give them |
|---|---|---|
| International / market-entry leads and GMs | Where and when to open; new-market forecast | Demand range before launch |
| Supply chain / planning | Opening stock, shipments with Yunnan lead times | Forecast-to-stock bridge |
| Store format / equipment / R&D | Automation tier per store | Line simulation by setup |
| Membership / CRM | Triggers, personalisation | Pre- and post-launch signal use |
| Franchisees (secondary) | Capex and labour | Right-sized setup |

## 5. Novelty: how to word it

Not novel (say so openly): AI forecasting and siting (Starbucks), beverage automation (Gong cha Super Wu), store digital twins (exist, built from existing stores), Chagee's own semi-automation.

Our contribution: (1) a pre-opening twin, meaning a simulation of a store that does not exist yet, fed by a demand forecast; (2) the hybrid-line hypothesis above; (3) using app-only member data to separate opening hype from repeat demand.

Wording rule: "to our knowledge, based on public sources". Never write "not available in the market" or "first".

## 6. Deck structure

Title slide (untimed) plus 5 content slides. About 7 minutes of talk and 3 for Q&A. Every slide has a claim headline, an interactive explainer panel (label it "INTERACTIVE EXPLAINER" as in the references), a short conclusion, reasoning cards where useful, speaker notes, and the footer "explainer figures are illustrative assumptions".

### Slide 1: Why this slice (~1.5 min)
- Headline: *Chagee's supply chain is fixed, so new-market risk lands on how much a store opens with and how fast its counter serves.*
- Content: scale facts (section 9), rigid upstream, GM-led forecasting, why not marketplace.
- Explainer: **"Where does uncertainty land?"** A toggle between "rigid sourcing" and "localised sourcing". Show which end absorbs the variance (stock quantity vs counter speed). Rigid is the default.

### Slide 2: Predict (~1.5 min)
- Headline: *App-only ordering lets Chagee read a new market's demand before the store opens, and tell opening hype from repeat habit.*
- Content: every order tied to a member, so a pre-launch waitlist is a demand signal. State the tourist blind spot on the slide.
- Explainer: **demand range that narrows as signal grows.** Slider: pre-launch signal strength. Optional toggle: remove opening-week hype. Output: a low/base/high weekly demand band and its width.
- Handoff out: the demand range object (low/base/high plus width).

### Slide 3: Provision (~1 min)
- Headline: *The wider the demand range, the costlier the opening-stock decision, especially with fresh milk.*
- Content: newsvendor logic from Week 1, with waste on one side and stockouts on the other.
- Explainer: **opening stock calculator.** Input: the range from slide 2. Slider: days of opening stock. Output: expected waste cost vs stockout cost, and the cost-minimising stock level.
- Handoff out: recommended opening stock and the chosen counter setup.

### Slide 4: Perform (~2 min, the centrepiece)
- Headline: *In a new market, a mixed people-and-machine counter beats full automation until demand becomes predictable.* (Subject to the simulator result.)
- Layout: Week 6 pattern with reasoning cards:
  - Why machines struggle with surges (fixed speed, no reassigning)
  - Why people rebalance (bucket-brigade self-balancing)
  - Where machines still win (steady demand, consistency, labour scarcity)
- Explainer: **crossover chart.** X-axis: demand uncertainty. Y-axis: cost per cup (machine cost per cup, labour, lost orders from long waits). Three lines: all-human, mixed, all-machine. Slider: uncertainty. Toggle: surge size. Mark the crossover point if one exists.
- Closing panel (as in Week 6): "What could shift the balance": machine cost per cup, how quickly the forecast narrows, staff turnover.

### Slide 5: Benefit, risks, next step (~1 min)
- Headline: *Even modest per-store savings compound across about 200 overseas openings a year, if the risks are managed.*
- Explainer: **benefit calculator.** Sliders: number of stores, cups per store per year, saving per cup (default from the simulator), waste avoided. Output: annual saving, shown as a formula with each assumption named. Never present it as a precise forecast.
- Risks (Ayumi's point), with a toggle to show each: staff dependence and turnover; tourist and non-app demand invisible; opening-week crowds mistaken for steady demand; heavy automation undercutting the premium teahouse experience.
- Next step: what we would do with real Chagee data.

## 7. Simulator spec (sim/)

Pure functions, no UI, tested before any slide uses them.

- Six stations: ticket, cup/ice, tea and milk dispense, topping/finish, shake/seal, handover.
- Three setups: all-human (bucket brigade, workers of different speeds, handover points rebalance), mixed (machines on fixed-time stations, people on variable ones, one flexible worker), all-machine (fixed speeds, no reassigning).
- Inputs: orders per hour (a draw from the Predict range), demand uncertainty, surge size, setup, target wait time.
- Outputs: cost per cup (machine cost per cup served, labour, lost-order cost for orders exceeding the wait target), percentage of orders over the wait target, throughput.
- Method: Monte Carlo over demand draws, with queueing or discrete-event logic. Propose the simplest model that captures rebalancing vs fixed speeds, explain it in plain words, and wait for my approval.
- Sweep uncertainty to produce the crossover chart. Report whatever it shows.

## 8. assumptions.json

All numbers live here, each with a unit, a short rationale and a label: `source: "assumption"` or a source ID from section 9. Create the file with the parameter names below, **propose values with rationale, and wait for my approval.** Do not silently pick numbers.

Parameters: station service times by setup; human speed variation; machine cost per month; labour cost per hour; target wait time (slider, not a fixed claim); cost of a lost order; waste cost per unit of fresh milk; stockout cost; demand range defaults; number of overseas stores (use the 2026 plan figure); cups per store per year.

## 9. Source ledger

### Public, usable (cite the source; most are secondary)
- Chagee had 7,453 stores at end-2025, about 200 overseas stores planned for 2026, 345 overseas stores, 7 overseas markets, Korea launching Q2 2026. Full-year 2025 GMV RMB 31.58bn, net revenue RMB 12.91bn. Source: Jiemian (en.jiemian.com), earnings call coverage.
- Chagee says it sources all tea and milk directly for domestic operations, with distribution managed through HQ. Source: PR Newswire, 21 May 2024 (company release).
- Own Yunnan plantations and cold chain to 6,000+ stores; tea lattes about 91% of China sales. Source: Prometheus Capital Substack (secondary; flag it).
- Founder avoided fruit tea partly for supply chain complexity. Source: Chainreact Substack (secondary).
- Chagee's pure milk-tea menu is seen as simpler to export; Mixue has 7 SEA warehouses and 3 planned local factories. Source: Studio Triunity, citing the Mixue prospectus.
- Chagee semi-automation: baristas scan a QR code and the machine dispenses the formulation; Teaspresso machines. Source: UNSW BusinessThink, Oct 2024.
- Chagee Express (Malaysia): semi-automated machine, three drink categories for speed. Source: Cyber-RT / Citizens Journal, Oct 2022.
- Gong cha Super Wu (company-reported): up to 65% higher peak-hour productivity, about one minute off prep, stores with as few as two staff, 40-store pilot in 13 countries; kiosks about 70% of US transactions, 80% loyalty opt-in. Source: FastCasual and franchise.org, Jan-Feb 2026.
- Starbucks Deep Brew: forecasting, scheduling, replenishment, order sequencing; location analytics for new stores. Sources: Constellation Research, Harvard D3.
- Store digital twins replicate existing layouts. Source: MOSIMTEC, Winter Simulation Conference 2025.
- Bubble tea shaker robot needed about one worker vs four to six; two earlier all-robot shops closed within about a year. Source: Slate, Aug 2021.
- First overseas store (Kuala Lumpur) reportedly sold 1,000+ cups on opening day. Source: GabGrowth (secondary).

### From the call with Lee Yen (informal; do not cite without checking with her)
- Standardised sourcing from Yunnan; local sourcing only when regulation forces it (e.g. matcha).
- New-market forecasting is GM-led, with the GM hired up to a year ahead (Korea example).
- Four membership tiers, most members at L1; app-only ordering with tourist exceptions; target of sub-one-minute fulfilment.
- China saturation (about 7,000 stores) and competitor top-up-credit promotions; Chagee avoids cheap promotions to protect its premium image.
- The auto-generated meeting summary spells the brand "Chaji". Ignore that.

### Do NOT claim
- Anything is "not available in the market", or Chagee is "first" at anything.
- Any revenue-mix percentage for franchise supply. Sources conflict (60% to about 88%). Verify in the filings first.
- Overseas milk sourcing details (unknown).
- A "Supply Chain Security Act" local-sourcing rule (low-quality source).
- Any number for Chagee internals (costs, forecast methods, automation plans) that is not in the ledger.

## 10. Build rules

- Mirror reference/week5 and reference/week6 for structure, components, speaker notes and export. Never edit reference/.
- Every explainer reads from sim/ or assumptions.json. No hardcoded numbers in slide code.
- Every interactive slide needs a print or static state that shows the key result without interaction.
- Footer on every slide: "explainer figures are illustrative assumptions". Chagee facts carry a source in the speaker notes.
- One slide per prompt. After each, tell me what you built, what you assumed, and what you flagged.
- If a claim cannot be supported by this file, flag it instead of writing it.

## 11. Likely Q&A (prepare short answers)

1. Why not a marketplace? (one closed channel, section 3)
2. How certain is the novelty claim? (hedged, section 5)
3. Why synthetic data? (Chagee internal data is not public; assumptions are labelled)
4. What about tourists and non-app customers? (named blind spot; forecast understates demand)
5. Would a human-heavy line hurt the premium experience? (risk on slide 5; staff training and the teahouse positioning)
6. What if the simulator shows machines win everywhere? (then the hybrid claim is rejected, and the answer is when to automate)
7. How would you size the benefit with real data? (replace the assumptions with Chagee actuals)

## 12. Definition of done

- Five content slides plus a title slide, matching the template's look.
- Every explainer works live and reads correctly when printed.
- Every number traces to assumptions.json or the ledger.
- The headline claim matches what the simulator shows.
- PDF exported and checked page by page.
- A list of every factual claim in the deck with its source marked.
