# Claims register: Chagee deck

Every factual claim in the deck and where it comes from. Ledger IDs are defined in `assumptions.json` under `_sources`. Every model figure (costs, bands, savings) comes from `assumptions.json` and `sim/`; all of them are illustrative, and the deck footer says so.

Status key: **OK** = public source in the ledger · **SECONDARY** = secondary source, flagged in the speaker notes · **CHECK** = informal or our own reading; confirm before presenting · **MODEL** = simulator or assumption output

## Chagee facts

| # | Claim (as worded in the deck) | Slide | Source | Status |
|---|---|---|---|---|
| 1 | 7,453 stores at end-2025 | 1 | L-jiemian | OK |
| 2 | 345 overseas stores in 7 markets | 1 | L-jiemian | OK |
| 3 | About 200 overseas openings planned for 2026 | 1, 5 | L-jiemian | OK |
| 4 | FY2025 GMV RMB 31.58bn, net revenue RMB 12.91bn | 1 | L-jiemian | OK |
| 5 | Sources tea and milk directly for domestic operations; distribution run from HQ | 1 | L-prn (company release) | OK |
| 6 | Own Yunnan plantations ("reported") | 1 | L-prometheus | SECONDARY |
| 7 | Tea lattes about 91% of China sales | 1 | L-prometheus | SECONDARY (said on slide) |
| 8 | Narrow menu kept partly for supply-chain simplicity | 1 (notes) | L-chainreact | SECONDARY |
| 9 | Semi-automation: QR-scan dispensing; Chagee Express | 1 | L-unsw, L-cyberrt | OK |
| 10 | New-market opening forecast is judgement-led by a local GM ("our reading") | 1 | I-leeyen | **CHECK**: informal call; confirm with Lee Yen before citing |
| 11 | One closed channel, app to store; no third-party sellers | 1 | brief.md section 3 (our reading) | **CHECK**: partly rests on I-leeyen |
| 12 | App-only ordering ties every order to a member (headline of slide 2) | 2 | I-leeyen | **CHECK**: the slide 2 headline depends on this |
| 13 | Tourist exceptions to app-only ordering | 2 | I-leeyen | **CHECK** |
| 14 | Kuala Lumpur store reportedly sold 1,000+ cups on its first day | 2 | L-gabgrowth | SECONDARY (said on slide) |
| 15 | Korea launch planned for Q2 2026 | 5 | L-jiemian | OK. As of Oct 2026, whether it launched has not been checked. |

## What isn't new, and the hedged contribution

| # | Claim | Slide | Source | Status |
|---|---|---|---|---|
| 16 | AI forecasting and siting exist (Starbucks Deep Brew) | 2 (notes) | L-starbucks | OK |
| 17 | Beverage automation exists (Gong cha Super Wu; robot shaker) | 4 (notes) | L-gongcha (company-reported), L-slate | OK |
| 18 | Store digital twins replicate *existing* stores | 4 (notes) | L-mosimtec | OK |
| 19 | "To our knowledge, based on public sources": pre-opening store simulation; app-member data to separate hype from habit | 2, 4, 5 | brief.md section 5 | Hedged as required; never says "first" |

## Model figures (illustrative)

| # | Claim | Slide | Source | Status |
|---|---|---|---|---|
| 20 | Labour cost S$14.09/hr (minimum-wage floor plus employer CPF) | 4 (notes) | L-mom-pwm, L-cpf | OK as a floor; **placeholder** for a market rate |
| 21 | Band narrows from ±50% to ±15% with signal | 2 | assumptions.json | MODEL |
| 22 | Best opening order costs S$1,064 with no signal vs S$694 at the default band | 3 | sim/ provision() | MODEL |
| 23 | Mixed beats full automation at every uncertainty level (none and moderate surge); machines win under a large surge | 4 | sim/ sweep | MODEL, stable across 20 of 20 seeds |
| 24 | Automated line busy 21–22% of open hours; one machine per station ≈ 240 cups/hr vs a peak of ≈ 61 | 4 | sim/ | MODEL |
| 25 | All-human cheaper still (S$0.61 vs S$0.64 per cup) | 4 | sim/ | MODEL |
| 26 | Week 5 check: pooled formula is 4.65% / 6.76% above the Week 5 engine (tolerance 3%) | 4 (notes) | sim/ tests | MODEL. **The test fails**, and the notes say so. |
| 27 | ≈ S$10.0m a year across new overseas stores | 5 | formula on slide | MODEL, presented as sizing, not a forecast |

## Deliberately not claimed

These follow brief.md section 9: no revenue-mix percentage for franchise supply, no overseas milk sourcing details, no "Supply Chain Security Act", no Chagee internal costs or plans, and nothing called "first" or "not available in the market".

---

## Likely Q&A: short answers

1. **Why not a marketplace?** Chagee runs one closed app-to-store channel. There are no third-party sellers and no channel conflict, so the marketplace-design topics don't apply. The franchise revenue share is the one overlap, and it's out of scope.
2. **How certain is the novelty claim?** It's hedged: "to our knowledge, based on public sources". Forecasting, automation and digital twins all exist. What we add is simulating a store *before* it exists, fed by its own forecast.
3. **Why synthetic data?** Chagee's internal data isn't public. Every number is a labelled assumption with a range, and the sensitivity sweep shows which ones matter.
4. **Tourists and non-app customers?** They're a named blind spot. The forecast understates demand in tourist areas, so widen the band there.
5. **Would a human-heavy line hurt the premium experience?** That's a risk on slide 5. The mixed setup keeps people at finishing and handover, the steps customers see.
6. **What if machines win everywhere?** They don't in our model. The result is more specific: mixed beats full automation because machines sit idle at new-store volume, and uncertainty barely matters. Machines win only under large surges. So the answer is "automate on proven volume and peaks".
7. **How would you size the benefit with real data?** Replace station times, wages, machine costs and demand with Chagee actuals, then re-run `sim/` and the deck rebuilds itself.
