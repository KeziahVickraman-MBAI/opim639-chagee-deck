r"""
build_deck.py  -  OPIM639 group deck on Chagee's overseas expansion.

    python deck/build_deck.py          # writes deck/chagee_deck.html
    python deck/build_deck.py --open   # ...and opens it

Title slide + 5 content slides (1280 x 720, scaled to fit; F full screen, N notes, E edit).
Structure, toolbar, notes, edit mode and Download follow reference/week6.

Numbers
  * Every number in the slide text is a placeholder: {{section.key|fmt}} reads
    assumptions.json, {{sim.name|fmt}} reads the simulator output. The build fails
    if any text field contains a raw digit outside a short allow-list (years,
    "Week n", course code, ledger IDs).
  * Simulator output comes from `node sim/precompute.js`, re-run automatically when
    assumptions.json or sim/ is newer than deck/build/data.json.
  * Slides 2, 3 and 5 compute live in the browser with sim/sim.js (inlined);
    slide 4 reads the precomputed sweeps.

Printing: every slide prints as its own 1280 x 720 page at the settings on screen.
deck/export_pdf.sh writes the PDFs (with and without speaker-notes pages).
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "chagee_deck.html"
DATA = HERE / "build" / "data.json"
A = json.loads((ROOT / "assumptions.json").read_text(encoding="utf-8"))
esc = html.escape


TITLE = dict(
    course="OPIM639 · Innovations & Operations of Intelligent Online Marketplaces",
    title="Chagee: opening overseas stores right",
    topic="Predict demand, provision the store, size the counter",
    group="Group 3",
    members=["Keziah, Jin, Ayumi, Revan"],
)
FOOT = f"OPIM639 · Chagee group project · {TITLE['group']}"     # from the title, so the two never disagree

# ---------------------------------------------------------------------------
# Slide content. Every number is a placeholder; see module docstring.
# ---------------------------------------------------------------------------
CONTENT = [
    dict(
        key="c1", widget="aimap",
        kicker="Context and problem", chapter="context",
        headline="Chagee plans about {{benefit.overseas_stores_per_year|int}} overseas openings a year, and each "
                 "one commits its stock and its counter before its demand is known",
        points=[
            ("trend", "A premium tea chain scaling abroad",
             "{{facts.stores_end_2025|int}} stores at end-2025, {{facts.overseas_stores|int}} of them overseas in "
             "{{facts.overseas_markets|int}} markets. FY2025 GMV RMB {{facts.gmv_2025_rmb_bn|f2}}bn, net revenue "
             "RMB {{facts.net_revenue_2025_rmb_bn|f2}}bn. Orders run through Chagee's own app (our understanding)."),
            ("cycle", "Three core processes decide a new store",
             "Forecasting its demand, provisioning its opening stock, and setting up its counter. Sourcing is "
             "fixed: Chagee says it sources tea and milk directly, with distribution run from HQ."),
            ("alert", "The problem",
             "Stock and counter capacity are committed before a new market's demand is known, so a miss shows "
             "up as wasted milk, missed cups, queues or machines that sit idle (our reading)."),
            ("coins", "Why it matters",
             "The same decision repeats about {{benefit.overseas_stores_per_year|int}} times a year. Opening "
             "crowds can mislead: the Kuala Lumpur store reportedly sold {{facts.kl_opening_day_cups|int}}+ cups "
             "on its first day (secondary source)."),
        ],
        explainer_title="Where AI enters a new store's opening",
        caption="Click a step. Today's practice is our reading of public sources and one industry conversation, "
                "not a Chagee statement.",
        steps=[
            ("members", "Members",
             "Members order through the app (our understanding).",
             "Read sign-ups and pre-orders as early demand evidence.",
             "Membership / CRM", "slide {{ref.s2|int}}"),
            ("forecast", "Forecast",
             "Judgement-led by a local General Manager (our reading).",
             "A proposed demand range from member signals, with hype and habit separated by existing-market proxies.",
             "Market-entry leads and GMs", "slide {{ref.s2|int}}"),
            ("stock", "Opening stock",
             "Central, standardised supply of tea and milk.",
             "Size the first fresh-milk order to that range with newsvendor logic.",
             "Supply chain / planning", "slide {{ref.s3|int}}"),
            ("counter", "Counter",
             "Moving toward semi-automation: QR-scan dispensing, Chagee Express.",
             "Simulate the counter before the store exists, and set triggers for adding machines.",
             "Store format / equipment; franchisees", "slides {{ref.mech|int}} to {{ref.cost|int}}"),
            ("after", "After opening",
             "Not covered by public sources.",
             "Compare actual demand with the range to narrow the next market's forecast.",
             "Market-entry leads", "slide {{ref.playbook|int}}"),
        ],
        printnote="Printed with all five steps shown. Live: click a step to see one at a time.",
        view_kicker="The problem we solve",
        view_lead="Every overseas opening commits stock and counter capacity before its demand is known.",
        view_body="We do not train an AI model here. We show where AI fits, and test the opening decisions with "
                  "a simulation built on labelled assumptions.",
        notes=("About 50 seconds. Chagee is a premium tea chain growing fast abroad, with about "
               "{{benefit.overseas_stores_per_year|int}} overseas openings planned. Its sourcing is fixed by design, so each new store's risk sits in three "
               "processes: the demand forecast, the opening stock and the counter. The problem is timing: stock and "
               "counter capacity are committed before anyone knows the new market's demand. Click through the "
               "chain: AI reads the app's member signals before launch, sizes the first milk order to a demand "
               "range, and simulates the counter before it is built. Be clear that we have not trained a model; "
               "we show where AI fits and test the decisions with a simulation."),
        sources="Scale facts and planned openings: L-jiemian. Direct sourcing, HQ distribution: L-prn (company "
                "release). Semi-automation: L-unsw, L-cyberrt. Kuala Lumpur opening day: L-gabgrowth (secondary). "
                "App ordering and GM-led forecasting: I-leeyen (INFORMAL - check with Lee Yen before presenting).",
    ),
    dict(
        key="sc", widget="scope",
        kicker="Scope: what we left out and why", chapter="scope",
        headline="A closed app-to-store channel puts our problem in Topics 3 to 5, not the marketplace topics",
        explainer_title="Eight course topics: click one to see why it is in or out",
        topics=[
            (1, "Introduction to Online Retailing", "out", "",
             "One closed channel, app to store: no online-versus-store trade-off to weigh (our reading).",
             "Advantages and disadvantages of online retailing; Wharton case on online book retailing."),
            (2, "Online Marketplaces", "out", "",
             "No third-party sellers, so no sell-versus-fulfilment-service choice (our reading).",
             "Business models: sell on Amazon; fulfillment by Amazon."),
            (3, "Analytics and AI for Online Retailing", "in", "Predict · slide {{ref.s2|int}}",
             "Predicting a new market's demand from app-member signals.",
             "Predicting demand and optimizing price using data; the importance of data in the AI era. "
             "Price optimisation stays out: we have no demand-elasticity assumption."),
            (4, "Supply Chain Management using AI and Robotics", "in", "Provision · Perform",
             "Supply-chain planning sizes the stock; equipment selection sizes the counter.",
             "AI decision making for aggregate supply-chain planning; how to select robotics equipment and AI "
             "technology for effective fulfilment. Used on slide {{ref.s3|int}} (stock) and slides {{ref.mech|int}} to {{ref.cost|int}} (counter)."),
            (5, "Order Fulfillment for Online Retailing", "in", "Perform · Provision",
             "Picking with humans and robots: the bucket brigade behind our counter model.",
             "How to prepare inventory for effective fulfilment; how to perform efficient order-picking using "
             "humans and robots. Used on slides {{ref.mech|int}} to {{ref.cost|int}} (counter) and slide {{ref.s3|int}} (stock)."),
            (6, "Last-mile Delivery for Online Retailing", "unused", "",
             "Outside our question, which stops at the counter.",
             "Planning last-mile delivery using AI; uberization and autonomous vehicles."),
            (7, "Service-oriented platforms", "unused", "",
             "Outside our question.",
             "Differentiating factors, network effects, inventions, mistakes and failures of service-oriented "
             "platforms."),
            (8, "Omni-channel Retailing", "out", "",
             "One channel, so no channel conflict; the franchise revenue share is out of scope.",
             "Omni-channel retailing and distribution; its opportunities and challenges."),
        ],
        where_title="Where does uncertainty land?",
        scenarios=[
            ("rigid", "Rigid sourcing", "Chagee today, our reading",
             [("Sourcing", "Fixed: single origin", 0), ("Distribution", "Fixed: run from HQ", 0),
              ("Opening stock", "Absorbs the miss", 3), ("Counter speed", "Absorbs the miss", 3)]),
            ("local", "Localised sourcing", "For contrast only",
             [("Sourcing", "Flexes with local suppliers", 2), ("Distribution", "Shorter, local", 1),
              ("Opening stock", "Less exposed", 1), ("Counter speed", "Still exposed", 3)]),
        ],
        where_caption="Why this slice: with sourcing fixed, a demand miss lands in the store, on its opening stock "
                      "or its counter speed (our reading, not a Chagee statement).",
        printnote="Printed: every tile shows its status and reason; both sourcing columns are shown.",
        view_kicker="Our scope",
        view_lead="Three topics, three decisions.",
        view_body="Topic 3 feeds Predict; Topics 4 and 5 feed Provision and Perform. Sourcing is fixed by design, "
                  "so we take it as given, and the franchise revenue share stays out of scope.",
        notes=("About 40 seconds. The course has eight topics. Chagee runs one closed channel, from its app to its "
               "own stores, so the marketplace topics do not arise: there are no third-party sellers, no "
               "fulfilment-service choice and no channel conflict. Topics 6 and 7 are simply outside our question, "
               "which stops at the counter. Topics 3, 4 and 5 are where a new store's risk sits: predicting demand, "
               "planning the opening stock, and choosing people or robots at the counter. Use the toggle: because "
               "Chagee's sourcing is fixed, a demand miss can only be absorbed in the store. That is why we chose "
               "this slice."),
        sources="Topic names and content: OPIM639 course outline (AY2026-27), weekly lesson plans. Closed channel, "
                "no third-party sellers: brief.md section 3, our reading; app ordering rests on I-leeyen (INFORMAL). "
                "Direct sourcing and HQ distribution: L-prn. Franchise revenue share: out of scope, no figure "
                "claimed.",
    ),
    dict(
        key="s2", widget="band",
        kicker="Predict", chapter="predict",
        headline="App-only ordering could let Chagee read a new market’s demand before opening; we propose the "
                 "method and test how much it matters",
        points=[
            ("phone", "Every order is tied to a member",
             "With app-only ordering (our understanding), each cup is linked to a member account, so a pre-launch "
             "waitlist could be read as a demand signal."),
            ("wave", "A narrower band is our assumption",
             "The slider narrows the band from ±{{demand.uncertainty_no_signal|pct}} to "
             "±{{demand.uncertainty_strong_signal|pct}} along a straight line we assumed. We have not shown that "
             "member data does this: read it as a sensitivity."),
            ("cycle", "Hype versus habit needs a proxy",
             "A new store has no repeat history. Proxies: repeat rates in Chagee's existing overseas markets, "
             "nearby stores, and waitlist members who already order elsewhere. Kuala Lumpur reportedly sold "
             "{{facts.kl_opening_day_cups|int}}+ cups on day one (secondary)."),
            ("alert", "Blind spot: tourists and non-app orders",
             "Visitors and tourist exceptions sit outside the member signal, so the forecast understates demand "
             "where tourists matter. We name this gap rather than model it."),
        ],
        explainer_title="Demand range before opening: a sensitivity",
        caption="Weekly cups at one new store. The band covers {{demand.band_coverage|pct}} of likely outcomes; how "
                "fast it narrows with signal is our assumption.",
        printnote="Printed at the default assumed signal strength ({{predict.signal_strength_default|pct}}) with "
                  "opening hype removed.",
        view_kicker="Proposed method",
        view_lead="A method to test, not a result.",
        view_body="Back-test it: forecast past openings from their pre-launch sign-ups, and check the band holds "
                  "about {{demand.band_coverage|pct}} of actual demand. To our knowledge, reading app-only member "
                  "data this way before launch is new.",
        notes=("About 40 seconds; under time pressure, say only the Decision strip part. Chagee orders go "
               "through the app (our understanding, to be confirmed), so a pre-launch waitlist could be read as a "
               "demand signal. Be clear what the slider is: we assumed that more signal narrows the band, along a "
               "straight line between two end points; we have not shown member data does that. Separating opening "
               "hype from repeat habit also needs a proxy, because a new store has no repeat history: repeat rates "
               "in Chagee's existing overseas markets, nearby stores, or waitlist members who already order "
               "elsewhere. So this is a method to back-test on past openings. Decision strip: does the band change "
               "the counter? Barely: mixed overtakes all-human only beyond about "
               "±{{sim.be_u_all_human_mixed|pct}}. The band matters most for stock, the next slide."),
        decision=dict(
            question="Does the forecast band change which counter a new store opens with?",
            who="Market-entry leads and GMs; Membership / CRM runs the signal",
            trigger=("u", "all_human", "mixed", "band half-width"),
            also=("u", "mixed", "all_machine", "Mixed vs full automation"),
            action="Use the band for stock, not the counter: on the band alone mixed wins only past the "
                   "trigger, and full automation never does. The counter turns on volume and input costs.",
        ),
        sources="App-only ordering with tourist exceptions: I-leeyen (INFORMAL - check before presenting). Kuala "
                "Lumpur opening day: L-gabgrowth (secondary). Existing overseas markets: L-jiemian ({{facts.overseas_markets|int}} markets). "
                "Not novel - AI forecasting and siting: L-starbucks. Band narrowing with signal: assumption "
                "(predict.signal_strength_default, demand.uncertainty_no_signal / _strong_signal). Trigger: sim/ "
                "breakEven over the band half-width, default volume, moderate surge.",
    ),
    dict(
        key="mech", widget="brigade",
        kicker="Perform", chapter="perform",
        headline="In a surge, people pass work along like a bucket brigade; machines cannot, so the slowest "
                 "station sets the pace",
        points=[
            ("users", "People pass the work along",
             "Each worker carries a drink downstream and hands it over. In a surge the handover point moves, so "
             "the load evens out: the Week 5 bucket-brigade result."),
            ("box", "Machines stay at their station",
             "A fixed station cannot hand work back or take on more. The queue builds at the slowest one, "
             "wherever it sits on the line."),
            ("coins", "Sized for the peak, machines sit idle",
             "Switch to as sized in our cost model: the robots stop queuing, but they are busy only part of the "
             "time. Idle capacity is what a store pays for."),
        ],
        explainer_title="Inside the store: a bucket brigade at the counter",
        caption="Mechanism illustration on the Week 5 bucket-brigade engine, in its units. Times and costs come "
                "from the next two slides, not from this animation.",
        printnote="Printed at the end of the surge window; the table compares both sizing settings over the full "
                  "run.",
        view_kicker="Our view",
        view_lead="People flex; machines come in whole units.",
        view_body="So the counter choice turns on volume. The next two slides measure it: time to serve, then cost.",
        notes=("About 35 seconds. Press play. Top lane: people work as a bucket brigade. When the surge hits, the "
               "faster worker takes over more of each drink, the handover point moves and the load evens out. "
               "Bottom lane: robots are fixed at their station, so the queue builds at the slowest one and nobody "
               "can take its work. Flip to "
               "as sized in our cost model: the robots stop queuing, but they sit idle much of the run, and idle "
               "machines are what you pay for. This is a mechanism, in the Week 5 units; the next slide puts it "
               "in a real store layout in seconds."),
        sources="Bucket-brigade engine: course Week 5 explainer (reference, read-only), wrapped by "
                "sim/mechanism.js. As-sized ratios read from sim/ peakUtilisation and plan. Illustration settings: "
                "assumptions.json illustration (mixed_sizing needs approval).",
    ),
    dict(
        key="store", widget="storefront",
        kicker="Perform", chapter="perform",
        headline="In the peak hour, robots hand over a cup in about {{sim.st_med_all_machine|sec}}; a counter "
                 "like today's takes about {{sim.st_med_mixed|min1}}",
        explainer_title="Store replica: two counters in the peak hour, side by side",
        caption="Illustrative layout after a Chagee tea bar: order right, brewing behind the counter, pick-up left. "
                "Choose each counter; people move as the Week 5 bucket brigade; staff and arrivals from the cost "
                "model.",
        printnote="Printed at minute {{sim.store_print_minute|int}} of the peak hour, moderate surge: people slowest "
                  "first (top) against fastest first (bottom).",
        serve_summary="Time to serve, cost model (median · slowest tenth · lost):",
        serve_title="Time to serve: today versus simulated",
        serve_caption="From order to hand-over, waiting included. Cost model, peak hour, "
                      "{{validation.crossover_stability.seeds|int}} simulated days per bar.",
        serve_printnote="Printed at the moderate surge.",
        view_kicker="Our view",
        view_lead="Robots buy speed in the peak; whether it pays is the next slide.",
        notes=("About 45 seconds. Two counters laid out like a Chagee tea bar, seeing the same customers: order on "
               "the right, brewing behind the counter, pick-up on the left. It plays on its own. Top: people as the "
               "Week 5 bucket brigade, slowest first. Each worker carries a cup towards pick-up; the last hands it "
               "over, walks back and takes over from the colleague behind, so the line balances itself. Bottom: the "
               "same people, fastest first. The fast worker keeps catching the slow one and is held back, the red "
               "ring, and fewer cups get out. Switch the bottom to All-robot: nobody moves, the cups move from "
               "machine to machine. The times come from the cost model, in the line underneath: today's counter "
               "hands over a cup in about {{sim.st_med_mixed|min1}} at the median, an all-robot counter in about "
               "{{sim.st_med_all_machine|sec}}; open it for the chart. None of these is measured. The next slide "
               "puts a price on each counter."),
        sources="Semi-automation (machine dispenses the formulation): L-unsw; Chagee Express semi-automated "
                "machine: L-cyberrt. Layout: illustrative, after a Chagee tea-bar storefront (order right, pick-up "
                "left). Animation: sim/store.js (Week 5 brigade rules, illustration.walk_back_speed). Times and lost "
                "orders: sim.js serveTimes, a read-out of the cost model's peak hour. "
                "No measured serve time exists in our sources; the informal sub-one-minute target (I-leeyen) is "
                "not used.",
    ),
    dict(
        key="cost", widget="volcost",
        kicker="Perform", chapter="perform",
        headline="All-human and mixed are {{sim.vc_hm|sgd}} a cup apart at our forecast; mixed wins once volume, "
                 "wage or machine cost crosses a trigger",
        explainer_title="Cost per cup, by counter",
        caption="Cost model: labour, machines and lost sales per cup served; default band, moderate surge.",
        printnote="Printed at the default forecast.",
        tradeoff_title="When does mixed beat all-human?",
        tradeoff=["wage", "cupsPerDay", "machineMonth", "u", "coordHuman", "coordMixed", "newShare", "machineMult"],
        confidence=("How sure are we? A close call. The gap is {{sim.vc_hm|sgd}} a cup. Our staffing shortcut misses its "
                    "Week 5 check ({{sim.w5_lo|f1}}% and {{sim.w5_hi|f1}}% against "
                    "±{{validation.week5_comparison.tolerance_pct|int}}%), and with walking modelled people reach only "
                    "{{sim.cap_h|pct}} of the assumed capacity ({{sim.cap_m|pct}} at today's counter). Test the "
                    "ranking with real staffing data before relying on it."),
        decision=dict(
            question="Which counter does a new store open with, and when are machines added?",
            who="Store format / equipment, with franchisees (capex and labour)",
            trigger=("cupsPerDay", "all_human", "mixed", "steady cups per day"),
            also=("cupsPerDay", "mixed", "all_machine", "Full automation"),
            action="No default: all-human while a store sits below every trigger, mixed once any is crossed, full "
                   "automation only past about {{sim.be_cupsPerDay_mixed_all_machine|int}} cups a day.",
        ),
        notes=("About 45 seconds; under time pressure, read only the trade-off table. Speed has a price. The chart is "
               "the cost model: labour, machines and lost sales per cup against steady cups per day. At our "
               "forecast of about {{sim.cpd0|int}} cups a day all-human is cheaper, but only by {{sim.vc_hm|sgd}} a "
               "cup, so we do not recommend a default. The table says when mixed wins instead, nearest first: "
               "machine cost below about {{sim.be_machineMonth_all_human_mixed|sgd0}} a month, all-human staff "
               "coordinating a little worse than we assume (below {{sim.be_coordHuman_all_human_mixed|f2}}), or a "
               "wage above about {{sim.be_wage_all_human_mixed|sgd}} an hour; each is only a few per cent away. "
               "Volume needs about {{sim.be_cupsPerDay_all_human_mixed|int}} cups a day. Full automation needs about {{sim.be_cupsPerDay_mixed_all_machine|int}}. And be clear "
               "how sure we are: it is a close call on a simplified staffing model."),
        sources="Wage S$ per hour worked, fully loaded: L-mom-pwm, L-mom-ows, L-cpf, L-sdl, L-mom-leave, L-mom-ph. "
                "Costs and break-evens: sim/ cost model and breakEven over cups per day (data.json volumeCurve, "
                "breakEven), default band, moderate surge. All inputs: assumptions.json (illustrative).",
    ),
    dict(
        key="s3", widget="stock",
        kicker="Provision", chapter="provision",
        headline="The wider the demand range, the costlier the opening-stock decision, especially with fresh milk",
        points=[
            ("scale", "Two ways to be wrong",
             "Too much fresh milk expires; too little turns customers away. Newsvendor logic: order until one "
             "more litre's expected waste cost equals the expected lost-sale cost it avoids."),
            ("coins", "Here a stockout costs more than waste",
             "A missed cup loses {{provision.stockout_cost_per_cup|sgd}}; a spare litre of milk wastes "
             "{{provision.milk_waste_cost_per_litre|sgd}}. So the best order sits high in the band, at the "
             "{{sim.critical_ratio|pct}} point of demand."),
            ("moon", "Shelf life caps the buffer",
             "Fresh milk keeps about {{provision.milk_shelf_life_days|int}} days (illustrative), so extra stock "
             "cannot be carried forward. A narrower band from slide {{ref.s2|int}} is the cheaper fix."),
        ],
        explainer_title="Opening stock calculator",
        caption="Expected cost of the first fresh-milk order at one store, using slide {{ref.s2|int}}’s band. Overseas milk "
                "sourcing is unknown; figures are generic.",
        printnote="Printed at the band from slide {{ref.s2|int}} and the default of {{provision.opening_stock_days|int}} days "
                  "of stock.",
        view_kicker="Our view",
        view_lead="Narrow the band before you stock the store.",
        view_body="From no signal to the default signal, the expected cost of the best opening order falls from "
                  "{{sim.prov_none|sgd0}} to {{sim.prov_def|sgd0}} per store (illustrative). The band matters for "
                  "stock; for the counter, volume and input costs decide (slide {{ref.cost|int}}).",
        decision=dict(
            question="How much fresh milk does a new store open with: above or at the base forecast?",
            who="Supply chain / planning, from the market-entry team's demand band",
            trigger=("milk",),
            also=None,
            action="Order above the base forecast, at the cost-minimising level the calculator marks. Narrow the "
                   "band first: it lowers the cost of even the best order.",
        ),
        notes=("About 30 seconds; under time pressure, read only the Decision strip. Fresh milk is a newsvendor "
               "problem: order until one more litre's expected waste cost equals the expected lost-sale cost it "
               "avoids. A lost cup costs far more than a wasted litre, so the best order sits above the base "
               "forecast, and that holds unless waste costs over {{sim.milk_trigger|sgd}} a litre. A wider band "
               "raises the cost of even the best order: that is the pre-launch signal's value in stock terms. "
               "Caveat: milk costs are generic; Chagee's overseas sourcing is not public."),
        sources="All figures: assumptions.json (illustrative). Milk trigger: sim/ milkTrigger, stockout cost per "
                "cup / milk per cup, against the approved milk waste range. Overseas milk sourcing: unknown, "
                "deliberately not claimed (brief.md section 9).",
    ),
    dict(
        key="a1", widget="a1", kicker="Appendix A1 · assumptions", chapter="appendix",
        headline="Every assumption, with its unit, range and source",
        sections=["facts", "predict", "predict_toggles", "store", "demand", "surge"],
        notes="Handout only. Generated from assumptions.json at build time, so it always matches the deck.",
        sources="assumptions.json.",
    ),
    dict(
        key="a1b", widget="a1", kicker="Appendix A1 · assumptions (continued)", chapter="appendix",
        headline="Every assumption, with its unit, range and source (continued)",
        sections=["stations", "people", "costs", "service", "provision", "benefit"],
        notes="Handout only. Generated from assumptions.json at build time, so it always matches the deck.",
        sources="assumptions.json.",
    ),
    dict(
        key="a1c", widget="a1", kicker="Appendix A1 · assumptions (continued)", chapter="appendix",
        headline="Every assumption, with its unit, range and source (continued)",
        sections=["simulation", "triggers", "illustration", "validation"],
        notes="Handout only. Generated from assumptions.json at build time, so it always matches the deck.",
        sources="assumptions.json.",
    ),
    dict(
        key="a2", widget="a2", kicker="Appendix A2 · model and validation", chapter="appendix",
        headline="The model is stable across seeds but misses its Week 5 check, and a handful of inputs decide "
                 "all-human versus mixed",
        notes="Handout only. Week 5 comparison and seed stability from sim/ tests and precompute; the sensitivity "
              "chart varies one ranged assumption at a time across its approved range.",
        sources="sim/precompute.js: the Week 5 comparison, seed stability, the sensitivity sweep and replica capacity (data.json).",
    ),
    dict(
        key="a3", widget="a3", kicker="Appendix A3 · sources and claims not made", chapter="appendix",
        headline="The source behind every Chagee fact, and the claims we deliberately did not make",
        not_claimed=[
            "That Chagee is first at anything, or that anything is not available in the market.",
            "Any revenue-mix share for franchise supply: sources conflict.",
            "Overseas milk sourcing details: unknown, so milk costs are generic.",
            "A Supply Chain Security Act local-sourcing rule: low-quality source.",
            "Any Chagee internal cost, forecast method or automation plan not in the ledger.",
            "Measured serve times: every time on the store-replica slide is modelled; the observed row is empty.",
            "That member data narrows the forecast band: the narrowing is our assumption, tested as a sensitivity.",
            "That all-human or mixed is proven cheaper: the gap is small and rests on a simplified staffing model.",
            "A saving against today's practice: the benefit is a modelled avoided cost against a standard counter.",
            "Anything about menu prices: that would need a demand-elasticity assumption we do not have.",
            "The informal sub-one-minute fulfilment target from the industry call: not used.",
        ],
        notes="Handout only. Ledger from assumptions.json _sources; the list of claims not made follows brief.md "
              "section 9 plus the limits found while building the deck.",
        sources="assumptions.json _sources; brief.md section 9.",
    ),
    dict(
        key="s4", widget="cross",
        kicker="Appendix A2 · the uncertainty sweep", chapter="appendix",
        headline="At a new store’s volume, a mixed people-and-machine counter beats full automation, because "
                 "machines sit idle, not because demand is uncertain",
        sub="We tested the hypothesis that mixed wins only until demand becomes predictable. Our simulator "
            "rejected the uncertainty part.",
        points=[
            ("box", "Machines come in whole units, so they sit idle",
             "Even one machine per station serves about {{sim.machine_cap_hr|int}} cups an hour against a forecast "
             "peak of about {{sim.peak_hr|int}}. The fully automated line is busy only {{sim.busy_lo|pct}} to "
             "{{sim.busy_hi|pct}} of open hours."),
            ("users", "People flex; machines cannot be returned",
             "Rosters follow the hour and the real demand, and staff rebalance across stations like a bucket "
             "brigade. A mixed counter buys {{sim.mixed_units|int}} machines instead of "
             "{{sim.machine_units|int}}, with similar staff hours."),
            ("trend", "Where machines still win",
             "Big surges: at a {{surge.surge_multiplier.large|x}} peak, people-based counters lose about "
             "{{sim.large_lost|pct}} of orders and full automation is cheaper. Also steady high volume, "
             "consistency and labour scarcity."),
        ],
        explainer_title="Cost per cup by counter setup",
        printnote="Printed at the default band (±{{sim.u0|pct1}}) and {{surge.surge_default|txt}} surge.",
        shift_title="What could shift the balance",
        view_kicker="Our view",
        view_lead="Uncertainty did not decide the counter; volume, wage and machine cost do.",
        view_body="All-human ({{sim.cost_h|sgd}}) and mixed ({{sim.cost_m|sgd}} per cup at the default band) are a close "
                  "call settled by the triggers on slide {{ref.cost|int}}. Machine breakdowns are not modelled, which "
                  "flatters automation.",
        notes=("Handout only (appendix). Our starting hypothesis was that a mixed counter beats full automation "
               "until demand becomes predictable. The simulator only half supports it. Mixed does beat full "
               "automation at the default settings, at every level of uncertainty, but the reason is not "
               "uncertainty: machines come in whole units, so the automated line sits idle and its fixed cost is "
               "spread over too few cups. The uncertainty slider barely moves the lines; a large surge does, and "
               "there full automation wins. All-human versus mixed is a close call decided by volume, wage and "
               "machine cost (slide {{ref.cost|int}}). Limits: the pooled staffing formula overstates a real bucket "
               "brigade (our Week 5 check missed its tolerance, gap {{sim.w5_lo|f1}} to {{sim.w5_hi|f1}} percent), and "
               "breakdowns are not modelled."),
        sources="All figures: sim/ with assumptions.json (illustrative). Semi-automation context: L-unsw, L-cyberrt. "
                "Not novel - beverage automation: L-gongcha (company-reported), L-slate; store digital twins: "
                "L-mosimtec. Labour cost floor: L-mom-pwm, L-cpf.",
    ),
    dict(
        key="playbook", widget="playbook",
        kicker="Decide", chapter="decide",
        headline="The playbook: no default counter; a few measurable triggers decide each opening",
        groups=[
            ("Counter: when mixed beats all-human", "Store format / equipment, with franchisees",
             ("all_human", "mixed"), ["wage", "machineMonth", "coordHuman", "coordMixed", "cupsPerDay", "u",
                                       "newShare", "machineMult"]),
            ("Counter: when full automation beats mixed", "Store format / equipment, with franchisees",
             ("mixed", "all_machine"), ["cupsPerDay", "wage", "machineMonth", "u", "machineMult"]),
        ],
        stock_group=("Stock: when to order at or below the base forecast", "Supply chain / planning"),
        table_note="Break-evens from sim/, each with every other input at our defaults; nearest first. The "
                   "all-human vs mixed gap is {{sim.vc_hm|sgd}} a cup and rests on a simplified staffing model "
                   "(slide {{ref.cost|int}}).",
        explainer_title="Your market",
        caption="Set your inputs. Verdict and margin: the full cost model ({{simulation.monte_carlo_draws|int}} "
                "simulated stores; under {{validation.breakeven.tol_cost_sgd_per_cup|sgd}} a cup is a tie). Nearest "
                "trigger: a live search with {{simulation.live_draws|int}}.",
        printnote="Printed at our default inputs.",
        view_kicker="Our view",
        view_lead="Measure the triggers, then choose the counter.",
        view_body="Before each opening: price the machine, set the wage, and back-test the volume forecast. The "
                  "nearest trigger tells you what to check first.",
        notes=("About 50 seconds. This is the call to action. There is no default counter; the table collects "
               "every trigger from the simulator, nearest first. For mixed over all-human, three sit within a few "
               "per cent of our defaults: machine cost, how well staff coordinate, and the wage. Volume needs "
               "about {{sim.be_cupsPerDay_all_human_mixed|int}} cups a day. Full automation needs about "
               "{{sim.be_cupsPerDay_mixed_all_machine|int}} cups a day, and nothing else in range gets it there. "
               "Stock: order above the base forecast unless milk waste costs over {{sim.milk_trigger|sgd}} a litre, "
               "which is far outside our range. On the right, put in a market: say a higher wage, or a cheaper "
               "machine. The panel recomputes the verdict, how much it wins by, and which trigger is closest to "
               "flipping it. If the margin is under a cent a cup, call it a tie and decide on other grounds."),
        sources="Wage: L-mom-pwm, L-mom-ows, L-cpf, L-sdl, L-mom-leave, L-mom-ph. Triggers: sim/ breakEven "
                "(data.json breakEven, leverNow) and milkTrigger. Your market: sim/ "
                "runPoint with simulation.live_draws, nearest flip found by bisection at the user's inputs. All "
                "inputs: assumptions.json (illustrative).",
    ),
    dict(
        key="s5", widget="benefit",
        kicker="Benefit, risks, next step", chapter="decide",
        headline="Every opening passes four gates; choosing its counter by trigger, not one standard, is worth about "
                 "{{sim.bn_total|sgdm}} a year",
        explainer_title="Opening pipeline: what choosing by trigger is worth",
        comparator="Compared with: Chagee's semi-automated counter (our mixed setup) at every new store. A modelled "
                   "avoided cost, not a demonstrated saving.",
        caption="Bar = openings at that volume × the standard's yearly cost above the cheapest counter (our defaults).",
        printnote="Printed at our defaults: openings spread evenly over our volume range.",
        gates_title="How each opening is decided",
        gates=[
            ("Before committing the site", "Predict", "Market-entry leads, Membership / CRM",
             "Open the waitlist and read the demand band; back-test it on past openings.", "{{ref.s2|int}}"),
            ("Before the first order", "Provision", "Supply chain / planning",
             "Order milk at the best order, above the base forecast; that holds unless waste costs over "
             "{{sim.milk_trigger|sgd}} a litre.", "{{ref.s3|int}}"),
            ("Before fit-out", "Counter", "Store format / equipment, franchisee",
             "Put the store's volume, wage and machine price into the playbook: all-human below every trigger, "
             "mixed once any is crossed.", "{{ref.playbook|int}}"),
            ("After opening", "Review", "Operations, market-entry leads",
             "Measure steady volume once the opening hype fades; add the machine stations past about "
             "{{sim.be_cupsPerDay_all_human_mixed|int}} cups a day, full automation only past about "
             "{{sim.be_cupsPerDay_mixed_all_machine|int}}.", "{{ref.cost|int}}"),
        ],
        risks=[
            ("Staff dependence and turnover",
             "Keep SOP training and flexible roles."),
            ("Tourist and non-app demand is invisible",
             "Widen the band in tourist areas; log walk-ups."),
            ("Opening crowds read as steady demand",
             "Decide the counter on steady volume, after the hype."),
            ("Automation versus the premium teahouse",
             "Keep people at finishing and hand-over."),
        ],
        next_title="Next step with real Chagee data",
        next_items=[
            "Replace every assumption with store actuals: station times, staffing, wages, machine costs.",
            "Back-test the waitlist signal on recent openings, such as Korea (launch planned for Q2 2026).",
            "Pilot all-human against mixed counters in paired new stores, timing real orders.",
        ],
        view_kicker="Our conclusion",
        view_lead="Decide each opening at its gates, not by one standard.",
        view_body="Uncertainty did not decide the counter, so our starting claim fell. Next, with Chagee's data: "
                  "replace the assumptions, back-test the waitlist on recent openings such as Korea (Q2 2026), and "
                  "pilot all-human against mixed in paired stores.",
        notes=("About 1 minute. This is how an opening is actually decided: four gates. Before committing the site, "
               "read the waitlist band. Before the first order, stock milk above the base forecast. Before fit-out, "
               "put the store's volume, wage and machine price into the playbook and pick the counter. After "
               "opening, measure steady volume and add machine stations at about "
               "{{sim.be_cupsPerDay_all_human_mixed|int}} cups a day. On the left, what that is worth against one "
               "standard counter everywhere, Chagee's semi-automated one: move the openings and the expected volume "
               "range and the bars follow. Below the trigger the standard costs about {{sim.bn_store|sgd0}} a store a "
               "year more than the cheapest counter; above it, nothing. Across about "
               "{{benefit.overseas_stores_per_year|int}} openings that is about {{sim.bn_counter|sgdm}}, plus "
               "{{sim.bn_stock|sgdm}} of stock if the signal works as assumed. A modelled avoided cost, not a "
               "demonstrated saving. The risks are on the slide with one mitigation each. Close on the next step: "
               "real data, a back-test on recent openings such as Korea, and a paired pilot."),
        sources="Overseas openings planned for 2026 and Korea launch: L-jiemian. Semi-automated counter as Chagee's "
                "standard: L-unsw, L-cyberrt (our reading). Per-store cost: data.json volumeCurve and the cups-per-day "
                "break-even, x open days. Share below the trigger: openings assumed evenly spread over the approved "
                "cups range (illustrative). Stock term: provision best-order cost, no signal minus default band. "
                "Everything else: assumptions.json and sim/ (illustrative).",
    ),
]

# ---------------------------------------------------------------------------
# Claims register (deck/claims.md), generated at build time. Facts and ledger sources are matched to slides
# automatically; the rows below are the claims that need a status of their own.
# ---------------------------------------------------------------------------
CHECK_CLAIMS = [
    ("Members order through the app; app-only ordering, with tourist exceptions", ["c1", "s2"], "I-leeyen",
     "CHECK: informal call; the Predict slide depends on it"),
    ("New-market forecasting is judgement-led by a local General Manager", ["c1"], "I-leeyen",
     "CHECK: informal call"),
    ("One closed app-to-store channel; no third-party sellers", ["sc"], "brief.md section 3, I-leeyen",
     "CHECK: our reading"),
    ("Chagee's counter today is semi-automated, modelled as our mixed setup", ["store", "s5"], "L-unsw, L-cyberrt",
     "CHECK: our reading of public sources"),
]
MODEL_CLAIMS = [
    ("Labour cost {{costs.labour_cost_per_hour|sgd}} per hour worked, fully loaded", ["cost", "playbook"],
     "L-mom-pwm, L-cpf, L-sdl, L-mom-leave, L-mom-ph"),
    ("Cost per cup at our forecast: all-human {{sim.vc_h|sgd}}, mixed {{sim.vc_m|sgd}}; gap {{sim.vc_hm|sgd}}",
     ["cost", "playbook"], "sim/ volumeCurve"),
    ("Mixed overtakes all-human above about {{sim.be_cupsPerDay_all_human_mixed|int}} cups a day, a wage of "
     "{{sim.be_wage_all_human_mixed|sgd}}, or below a machine cost of {{sim.be_machineMonth_all_human_mixed|sgd0}} "
     "a month", ["cost", "playbook"], "sim/ breakEven"),
    ("Full automation overtakes mixed only above about {{sim.be_cupsPerDay_mixed_all_machine|int}} cups a day "
     "(a step)", ["cost", "playbook"], "sim/ breakEven"),
    ("Peak-hour time to serve: today's counter about {{sim.st_med_mixed|min1}}, all-robot about "
     "{{sim.st_med_all_machine|sec}} (median)", ["store"], "sim/ serveTimes (cost model)"),
    ("Best opening milk order holds above base unless waste costs over {{sim.milk_trigger|sgd}} a litre",
     ["s3", "playbook"], "sim/ milkTrigger"),
    ("Best opening order costs {{sim.prov_none|sgd0}} with no signal against {{sim.prov_def|sgd0}} at the "
     "default band", ["s3"], "sim/ provision"),
    ("Choosing by trigger instead of one standard: about {{sim.bn_total|sgdm}} a year", ["s5"],
     "sim/ volumeCurve, breakEven; openings spread evenly (illustrative)"),
    ("Week 5 check: pooled formula {{sim.w5_lo|f1}}% and {{sim.w5_hi|f1}}% above the Week 5 engine; the test fails",
     ["cost"], "sim/ tests"),
    ("Band narrows from ±{{demand.uncertainty_no_signal|pct}} to ±{{demand.uncertainty_strong_signal|pct}} with "
     "signal", ["s2"], "assumption, shown as a sensitivity"),
]
QA = [
    ("Why not a marketplace?", "Chagee runs one closed app-to-store channel, so the marketplace-design topics do not "
     "apply (our reading, partly from an informal call)."),
    ("So which counter should a new store open with?", "No default. All-human is cheaper at our forecast by "
     "{{sim.vc_hm|sgd}} a cup; mixed wins once machine cost, wage, staff coordination or volume crosses a trigger "
     "(slide {{ref.playbook|int}}). The gap is small and the staffing model is simplified, so pilot before relying "
     "on it."),
    ("Did uncertainty matter?", "Not for the counter: mixed beats full automation at every band width in all seeds, "
     "and the all-human versus mixed choice turns on volume and input costs. The band matters for stock."),
    ("Are the serve times real?", "No. They are a read-out of the cost model's peak hour; no measured serve time "
     "exists in our sources. Timing real orders would replace them."),
    ("How certain is the novelty claim?", "Hedged: to our knowledge, based on public sources. Forecasting, "
     "automation and digital twins exist; simulating a store before it exists is the part we add."),
    ("How would you use real data?", "Replace station times, staffing, wages, machine costs and demand with Chagee "
     "actuals and re-run sim/; the deck, the playbook and this register rebuild from the same data."),
]

# ---------------------------------------------------------------------------
# Chapters (brief-v2 section 3): rail order, one-line purpose, on-stage time.
# Times are a talk plan, not model inputs, so they live here rather than in assumptions.json.
# ---------------------------------------------------------------------------
CHAPTERS = [
    ("context", "Context", "Chagee, the processes AI can improve, and the problem", 50),
    ("scope", "Scope", "Which course topics we use, which we leave out, and why", 40),
    ("predict", "Predict", "Read a new market's demand before the store opens", 40),
    ("provision", "Provision", "How much fresh milk to open with", 30),
    ("perform", "Perform", "How a counter absorbs a surge, and which counter to open with", 140),
    ("decide", "Decide", "The playbook of triggers, and the size of the benefit", 110),
]
CONTENTS_SECONDS = 10          # the Contents slide itself
QA_SECONDS = 180               # brief.md: about 3 minutes of Q&A

# Slides not yet rebuilt for brief-v2 show as clearly marked placeholders.
PLACEHOLDERS = {
    "context": dict(key="p1", chapter="context", kicker="Context and problem", step="step 2",
                    plan="Chagee scale facts, the core processes AI can enhance (demand forecasting, opening "
                         "inventory, counter service), the problem statement and its significance."),
}
DECK = ["c1", "sc", "s2", "s3", "mech", "store", "cost", "playbook", "s5", "a1", "a1b", "a1c", "a2", "s4", "a3"]

# ---------------------------------------------------------------------------
# Placeholders and the no-raw-numbers check
# ---------------------------------------------------------------------------
PH = re.compile(r"\{\{([\w.]+)\|(\w+)\}\}")
ALLOW = re.compile(r"\bAY20\d\d-\d\d\b|\bTopics? \d+(?:(?:, | and | to )\d+)*|\bstep \d+|\bA[1-3]\b|^\d · |^About \d+(?:\.\d+)? (?:minutes?|seconds)|\bsection \d+|\b(?:FY)?20\d\d\b|\bWeeks? \d+(?:[–-]\d+)?(?: and \d+)?|OPIM639|\bQ[1-4]\b|\b[LI]-[\w-]+")
FMT = {
    "int": lambda v: f"{v:,.0f}",
    "pct": lambda v: f"{v * 100:.0f}%",
    "pct1": lambda v: f"{v * 100:.1f}%",
    "sgd": lambda v: f"S${v:,.2f}",
    "sgd0": lambda v: f"S${v:,.0f}",
    "f1": lambda v: f"{v:.1f}",
    "f2": lambda v: f"{v:.2f}",
    "x": lambda v: f"{v:g}×",
    "txt": lambda v: str(v),
    "sec": lambda v: f"{v:.0f} seconds",
    "sgdm": lambda v: f"S${v / 1e6:.1f}m",
    "min1": lambda v: f"{v / 60:.1f} minutes",
}


def ensure_data() -> dict:
    deps = [ROOT / "assumptions.json", *(ROOT / "sim").glob("*.js")]
    if not DATA.exists() or max(p.stat().st_mtime for p in deps) > DATA.stat().st_mtime:
        print("running sim/precompute.js (about 90 s) ...")
        subprocess.run(["node", str(ROOT / "sim" / "precompute.js"), str(DATA)], check=True)
    return json.loads(DATA.read_text(encoding="utf-8"))


def sim_values(d: dict) -> dict:
    g = A["surge"]["surge_default"]["value"]
    rows, u0 = d["sweeps"][g]["rows"], d["defaults"]["u"]

    def at(rs, u, f, key="u"):
        for a, b in zip(rs, rs[1:]):
            if a[key] <= u <= b[key]:
                t = (u - a[key]) / (b[key] - a[key])
                return f(a) + t * (f(b) - f(a))
        return f(rs[-1])

    vc = d["volumeCurve"]
    cpd0 = A["store"]["cups_per_store_per_year"]["value"] / A["store"]["open_days_per_year"]["value"]

    util = d["util"][g]
    pv = A["provision"]
    under = pv["stockout_cost_per_cup"]["value"] / pv["milk_litres_per_cup"]["value"]
    be = {f"be_{r['lever']}_{r['a']}_{r['b']}": r["x"] for r in d["breakEven"] if r["kind"] == "value"}
    return {
        **be,
        "cpd0": cpd0,
        **{f"st_med_{k}": v["median"] for k, v in d["store"][g].items()},
        **{f"st_p90_{k}": v["p90"] for k, v in d["store"][g].items()},
        "store_print_minute": d["storePrintMinute"],
        "cap_h": d["storeCap"]["all_human"]["replica"] / d["storeCap"]["all_human"]["nominal"],
        "cap_m": d["storeCap"]["mixed"]["replica"] / d["storeCap"]["mixed"]["nominal"],
        "vc_h": at(vc, cpd0, lambda r: r["all_human"]["cost"], "cupsPerDay"),
        "vc_m": at(vc, cpd0, lambda r: r["mixed"]["cost"], "cupsPerDay"),
        "vc_hm": at(vc, cpd0, lambda r: r["mixed"]["cost"] - r["all_human"]["cost"], "cupsPerDay"),
        "vc_busy": at(vc, cpd0, lambda r: r["all_machine"]["busy"], "cupsPerDay"),
        "vc_gap": at(vc, cpd0, lambda r: r["all_machine"]["cost"] - min(r["all_human"]["cost"], r["mixed"]["cost"]), "cupsPerDay"),
        "u0": u0,
        "busy_lo": min(r["all_machine"]["busy"] for r in rows),
        "busy_hi": max(r["all_machine"]["busy"] for r in rows),
        "machine_cap_hr": util["all_machine"]["capacityPerMin"] * 60,
        "peak_hr": d["util"]["none"]["all_machine"]["arrivalPerMin"] * 60,
        "mixed_units": util["mixed"]["machineUnits"],
        "machine_units": util["all_machine"]["machineUnits"],
        "large_lost": at(d["sweeps"]["large"]["rows"], u0, lambda r: r["mixed"]["lostShare"]),
        "cost_h": at(rows, u0, lambda r: r["all_human"]["cost"]),
        "cost_m": at(rows, u0, lambda r: r["mixed"]["cost"]),
        "milk_trigger": d["milkTrigger"]["value"],
        **benefit_values(d),
        "critical_ratio": under / (under + pv["milk_waste_cost_per_litre"]["value"]),
        "prov_none": d["provision"]["none"]["optTotal"],
        "prov_def": d["provision"]["def"]["optTotal"],
        "w5_lo": min(w["gapPct"] for w in d["week5"]),
        "w5_hi": max(w["gapPct"] for w in d["week5"]),
    }


def benefit_values(d: dict) -> dict:
    """Standard counter (mixed) at every store vs choosing by trigger: per-store cost by volume, from sim/."""
    days = A["store"]["open_days_per_year"]["value"]
    be = next(r for r in d["breakEven"] if (r["lever"], r["a"], r["b"]) == ("cupsPerDay", "all_human", "mixed"))["x"]
    vc = d["volumeCurve"]
    best = lambda r: min(r[k]["cost"] for k in ("all_human", "mixed", "all_machine"))
    below = [(r["mixed"]["cost"] - best(r)) * r["cupsPerDay"] * days for r in vc if r["cupsPerDay"] < be]
    full = [(r["all_machine"]["cost"] - best(r)) * r["cupsPerDay"] * days for r in vc]
    lo, hi = vc[0]["cupsPerDay"], vc[-1]["cupsPerDay"]
    share = (be - lo) / (hi - lo)
    stores = A["benefit"]["overseas_stores_per_year"]["value"]
    per = sum(below) / len(below)
    # openings spread evenly over [lo, hi]; each curve point stands for the volumes within half a step of it
    step = vc[1]["cupsPerDay"] - vc[0]["cupsPerDay"]
    frac = [(min(hi, r["cupsPerDay"] + step / 2) - max(lo, r["cupsPerDay"] - step / 2)) / (hi - lo) for r in vc]
    counter = stores * sum(f * (r["mixed"]["cost"] - best(r)) * r["cupsPerDay"] * days for f, r in zip(frac, vc))
    stock = stores * (d["provision"]["none"]["optTotal"] - d["provision"]["def"]["optTotal"])
    return {"bn_store": per, "bn_share": share, "bn_counter": counter, "bn_stock": stock,
            "bn_total": counter + stock, "bn_full_lo": min(full), "bn_full_hi": max(full)}


def lookup(path: str, simv: dict):
    parts = path.split(".")
    if parts[0] == "ref":                         # on-stage slide number of a deck entry (rail numbering)
        if parts[1] not in REFNUM:
            raise SystemExit(f"slide reference to {parts[1]!r}: not an on-stage slide")
        return REFNUM[parts[1]]
    if parts[0] == "sim":
        return simv[parts[1]]
    node = A[parts[0]][parts[1]]["value"]
    for p in parts[2:]:
        node = node[p]
    return node


def check_and_fill(content, simv: dict, where: str = "CONTENT"):
    """Fail on raw digits in text; replace placeholders. Recurses through lists, tuples and dicts."""
    if isinstance(content, str):
        bare = ALLOW.sub("", PH.sub("", content))
        if re.search(r"\d", bare):
            raise SystemExit(f"raw number in {where}: {content[:90]!r} - use a {{{{placeholder}}}}")
        return PH.sub(lambda m: FMT[m.group(2)](lookup(m.group(1), simv)), content)
    if isinstance(content, dict):
        return {k: (v if k in ("key", "widget") else check_and_fill(v, simv, f"{where}.{k}")) for k, v in content.items()}
    if isinstance(content, (list, tuple)):
        return type(content)(v if isinstance(v, (int, float)) else check_and_fill(v, simv, where) for v in content)
    return content


# ---------------------------------------------------------------------------
ICONS = {
    "trend": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7.5a4 4 0 018 0V11"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/>'
             '<path d="M16 4.5a3.5 3.5 0 010 7"/><path d="M18 14c2.2.6 3.5 2.8 3.5 6"/>',
    "route": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/>'
             '<path d="M8.5 18H15a3 3 0 000-6H9a3 3 0 010-6h6.5"/>',
    "phone": '<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/>',
    "wave": '<path d="M3 17l4-6 4 3 5-8 5 6"/><path d="M3 21h18"/>',
    "cycle": '<path d="M20 11a8 8 0 00-14.3-4.9L4 8"/><path d="M4 4v4h4"/>'
             '<path d="M4 13a8 8 0 0014.3 4.9L20 16"/><path d="M20 20v-4h-4"/>',
    "alert": '<path d="M12 3.5L2.5 20h19L12 3.5z"/><path d="M12 10v4.5"/><path d="M12 17.3v.4"/>',
    "scale": '<path d="M12 3v18"/><path d="M7 21h10"/><path d="M4 7h16"/><path d="M4 7l-2.5 6h5L4 7z"/>'
             '<path d="M20 7l-2.5 6h5L20 7z"/>',
    "coins": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/>'
             '<path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
    "moon": '<path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/>',
    "box": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M4 7.5l8 4.5 8-4.5"/><path d="M12 12v9"/>',
}

TEMPLATE_PATH = HERE / "template.html"
DATA_CACHE: dict = {}
ENGINE_PATH = HERE / "deck.js"


def icon(name: str) -> str:
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def ed(key: str, text: str, tag: str = "span", cls: str = "") -> str:
    """An element whose text can be changed in the browser's edit mode."""
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-k="{key}">{esc(text)}</{tag}>'


def render_title() -> str:
    t = TITLE
    names = "".join(ed(f"t.m{i}", m, "li") for i, m in enumerate(t["members"]))
    art = """<svg class="art" viewBox="0 0 430 720" fill="none" aria-hidden="true">
      <path d="M70 660 C 70 520, 340 560, 300 410 S 110 260, 230 150" stroke="#e8a33d" stroke-width="3" stroke-dasharray="2 12" stroke-linecap="round"/>
      <circle cx="70" cy="660" r="9" fill="#e8a33d"/>
      <g transform="translate(180 60)" stroke="#cbd2e0" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">
        <path d="M10 30h80l-10 92a10 10 0 01-10 9H30a10 10 0 01-10-9z"/><path d="M4 30h92"/><path d="M50 30V4"/>
        <circle cx="38" cy="108" r="4" fill="#cbd2e0"/><circle cx="54" cy="114" r="4" fill="#cbd2e0"/><circle cx="64" cy="104" r="4" fill="#cbd2e0"/>
      </g>
      <g transform="translate(250 380)" stroke="#fff" stroke-width="2.5" stroke-linejoin="round">
        <rect x="0" y="0" width="90" height="56" rx="6"/><path d="M0 18h90"/><path d="M14 56v18M76 56v18"/>
        <rect x="58" y="-30" width="22" height="30" rx="3" fill="#e8a33d" stroke="#e8a33d"/>
      </g>
    </svg>"""
    return f"""
<section class="slide title" aria-label="Title">
  <div class="ttext">
    {ed("t.course", t['course'], "p", "course")}
    {ed("t.title", t['title'], "h1")}
    {ed("t.topic", t['topic'], "p", "topic")}
    <div class="rule"></div>
    {ed("t.group", t['group'], "p", "group")}
    <ul class="names">{names}</ul>
  </div>
  {art}
</section>"""


def render_points(s: dict) -> str:
    k = s["key"]
    return "".join(
        f'<div class="point"><span class="ico">{icon(ic)}</span><div>'
        f'{ed(f"{k}.p{i}.t", t, "h3")}{ed(f"{k}.p{i}.b", b, "p")}</div></div>'
        for i, (ic, t, b) in enumerate(s.get("points", [])))


def render_view(s: dict) -> str:
    k = s["key"]
    body = ed(f"{k}.vb", s["view_body"], "p", "vb") if s.get("view_body") else ""
    return (f'<div class="view">{ed(f"{k}.vk", s["view_kicker"], "p", "vk")}'
            f'{ed(f"{k}.vl", s["view_lead"], "p", "vl")}{body}</div>')


def render_where(s: dict) -> str:
    k, cols = s["key"], []
    for j, (sid, name, sub, steps) in enumerate(s["scenarios"]):
        rows = "".join(
            f'<div class="step"><span class="sname">{esc(st)}</span>'
            f'<span class="dots" aria-label="exposure {lvl} of 3">{"".join("<i class=on></i>" if d < lvl else "<i></i>" for d in range(3))}</span>'
            f'<span class="sdesc">{esc(desc)}</span></div>'
            for st, desc, lvl in steps)
        cols.append(f'<div class="scen {"on" if j == 0 else ""}" data-sc="{sid}"><h5>{ed(f"{k}.sc{j}", name)}'
                    f' <small>{esc(sub)}</small></h5>{rows}</div>')
    buttons = "".join(f'<button data-sc="{sid}" class="{"on" if j == 0 else ""}">{esc(name)}</button>'
                      for j, (sid, name, _, _) in enumerate(s["scenarios"]))
    legend = ('<div class="dlegend"><span><span class="dots"><i class=on></i><i></i><i></i></span> low</span>'
              '<span><span class="dots"><i class=on></i><i class=on></i><i class=on></i></span> high exposure to a demand miss</span></div>')
    return (f'<div class="variants">{buttons}</div><div class="scens">{"".join(cols)}</div>{legend}')


def render_aimap(s: dict) -> str:
    k, steps = s["key"], s["steps"]
    chips = "".join(
        f'<button class="mstep {"on" if i == 0 else ""}" data-st="{sid}"><span class="mn">{i + 1}</span>{esc(name)}</button>'
        + ('<span class="marrow" aria-hidden="true">→</span>' if i < len(steps) - 1 else "")
        for i, (sid, name, *_rest) in enumerate(steps))
    cards = "".join(
        f'<div class="mcard {"on" if i == 0 else ""}" data-st="{sid}"><h5>{i + 1} · {esc(name)}</h5>'
        f'<div class="mrow"><span>Today</span><p>{esc(today)}</p></div>'
        f'<div class="mrow ai"><span>What AI adds</span><p>{esc(ai)}</p></div>'
        f'<div class="mrow"><span>Who decides</span><p>{esc(who)}</p></div>'
        f'<div class="mrow"><span>In this deck</span><p>{esc(where)}</p></div></div>'
        for i, (sid, name, today, ai, who, where) in enumerate(steps))
    table = "".join(
        f'<tr><th>{i + 1} · {esc(name)}</th><td>{esc(today)}</td><td>{esc(ai)}</td><td>{esc(who)}<br><i>{esc(where)}</i></td></tr>'
        for i, (sid, name, today, ai, who, where) in enumerate(steps))
    return (f'<div class="mchain">{chips}</div><div class="mcards screenonly">{cards}</div>'
            f'<table class="mtable printonly"><thead><tr><th>Step</th><th>Today (our reading)</th><th>What AI adds</th>'
            f'<th>Who decides · where</th></tr></thead><tbody>{table}</tbody></table>')


def render_explainer(s: dict) -> str:
    k = s["key"]
    head = (f'<div class="exhead"><span class="tag">● INTERACTIVE EXPLAINER</span>'
            f'{ed(f"{k}.ex", s["explainer_title"], "span", "ex-title")}</div>')
    cap = ed(f"{k}.cap", s["caption"], "p", "caption") if s.get("caption") else ""
    if s.get("comparator"):
        cap = ed(f"{k}.cmp", s["comparator"], "p", "comparator") + cap
    pn = f'<p class="printonly pnote">{esc(s["printnote"])}</p>'
    if s["widget"] == "where":
        inner = render_where(s)
    elif s["widget"] == "aimap":
        inner = render_aimap(s)
    elif s["widget"] == "cross":
        inner = (f'<div class="body"></div><div class="shift"><h4>{ed(f"{k}.shift", s["shift_title"])}</h4>'
                 f'<div class="shiftrows"></div></div>')
    else:
        inner = '<div class="body"></div>'
    return f'<div class="explainer" data-widget="{s["widget"]}">{head}{cap}{inner}{pn}</div>'


def render_risks(s: dict) -> str:
    k = s["key"]
    rows = "".join(
        f'<div class="risk {"on" if i == 0 else ""}"><button class="rt" aria-expanded="{"true" if i == 0 else "false"}">'
        f'<span class="rn">{i + 1}</span>{ed(f"{k}.r{i}.t", t)}</button>{ed(f"{k}.r{i}.b", b, "p", "rb")}</div>'
        for i, (t, b) in enumerate(s["risks"]))
    nxt = "".join(ed(f"{k}.n{i}", x, "li") for i, x in enumerate(s["next_items"]))
    return (f'<div class="risks"><h4>RISKS <span class="screenonly">· click each</span></h4>{rows}</div>'
            f'<div class="next"><h4>{ed(f"{k}.nt", s["next_title"])}</h4><ul>{nxt}</ul></div>')


def mmss(sec: int) -> str:
    return f"{sec // 60}:{sec % 60:02d}"


def render_rail(chapter: str, n: int, total: int, label: str = "") -> str:
    """Progress rail: current chapter filled, earlier ones ticked, a slide counter; chapters are links."""
    ids = [c[0] for c in CHAPTERS]
    cur = ids.index(chapter) if chapter in ids else len(ids)
    chips = "".join(
        f'<button class="rc {"cur" if i == cur else "done" if i < cur else ""}" data-goto="{cid}"'
        f'{" aria-current=step" if i == cur else ""}><span class="rd">{"✓" if i < cur else i + 1}</span>{esc(name)}</button>'
        for i, (cid, name, _, _) in enumerate(CHAPTERS))
    count = f"Slide {n} of {total}" if chapter != "appendix" else f"{esc(label) or 'Appendix'} · handout only"
    return f'<nav class="rail" aria-label="Progress">{chips}<span class="rcount">{count}</span></nav>'


def render_contents(first: dict) -> str:
    rows = "".join(
        f'<button class="chap" data-goto="{cid}"><span class="cn">{i + 1}</span><span class="ct">{esc(name)}'
        f'<small>{esc(purpose)}</small></span><span class="cs">slide{"s" if len(first[cid]) > 1 else ""} '
        f'{(" and ".join(str(x) for x in first[cid])) if len(first[cid]) < 3 else f"{first[cid][0]} to {first[cid][-1]}"}</span><span class="cm">{mmss(sec)}</span></button>'
        for i, (cid, name, purpose, sec) in enumerate(CHAPTERS))
    stage = sum(c[3] for c in CHAPTERS) + CONTENTS_SECONDS
    return f"""
<section class="slide contents" aria-label="Contents" data-kicker="Contents">
  <p class="kicker">Contents</p>
  <h2>Six chapters: from Chagee's problem to a playbook of triggers</h2>
  <div class="chaps">{rows}</div>
  <p class="ctotal">About {mmss(stage)} on stage, then {mmss(QA_SECONDS)} for Q&amp;A. Click a chapter to jump to it.
     Appendix slides are in the handout only.</p>
  <div class="foot"><span>{esc(FOOT)} · <span class="assume">explainer figures are illustrative assumptions</span></span><span>2</span></div>
</section>"""


def render_placeholder(page: int, n: int, total: int, s: dict) -> str:
    k = s["key"]
    return f"""
<section class="slide content placeholder {k}" aria-label="Slide {page}" data-chapter="{s['chapter']}" data-kicker="{esc(s['kicker'])}">
  {render_rail(s['chapter'], n, total)}
  <h2>{esc(s['kicker'])}</h2>
  <div class="phbox"><p class="phk">DRAFT PLACEHOLDER · BUILT IN {esc(s['step']).upper()}</p><p>{esc(s['plan'])}</p></div>
  <div class="foot"><span>{esc(FOOT)} · <span class="assume">explainer figures are illustrative assumptions</span></span><span>{page}</span></div>
  <div class="notes"><p class="nk">SPEAKER NOTES</p><p data-k="{k}.notes">Placeholder: this slide is built in {esc(s['step'])}.</p><p class="src"><b>Sources:</b> none yet.</p></div>
</section>"""


def render_scope(s: dict) -> str:
    k = s["key"]
    badge = {"in": "IN", "out": "OUT", "unused": "NOT USED"}
    tiles = "".join(
        f'<button class="topic {st}{" on" if n == 3 else ""}" data-t="{n}"><span class="tn">Topic {n}</span>'
        f'<span class="tname">{esc(name)}</span><span class="tbadge">{badge[st]}</span>{f'<span class="tch">→ {esc(ch)}</span>' if ch else ""}'
        f'<span class="treason">{esc(why)}</span></button>'
        for n, name, st, ch, why, course in s["topics"])
    details = "".join(
        f'<div class="tdetail{" on" if n == 3 else ""}" data-t="{n}"><h5>Topic {n} · {esc(name)} '
        f'<span class="tbadge {st}">{badge[st]}{" · " + esc(ch) if ch else ""}</span></h5>'
        f'<p><b>Course content:</b> {esc(course)}</p><p><b>Why {"we use it" if st == "in" else "it is out"}:</b> {esc(why)}</p></div>'
        for n, name, st, ch, why, course in s["topics"])
    scope_ex = (f'<div class="explainer" data-widget="scope"><div class="exhead"><span class="tag">● INTERACTIVE EXPLAINER</span>'
                f'{ed(f"{k}.ex", s["explainer_title"], "span", "ex-title")}</div><div class="topics">{tiles}</div>'
                f'<div class="tdetails screenonly">{details}</div></div>')
    where = dict(key=f"{k}w", widget="where", explainer_title=s["where_title"], caption=s["where_caption"],
                 scenarios=s["scenarios"], printnote=s["printnote"])
    return (f'{scope_ex}<div class="grid gsc"><div class="left">{render_explainer(where)}</div>'
            f'<div class="right">{render_view(s)}</div></div>')


LEVER_FMT = {"u": lambda x: f"±{round(x * 100, 1):g}%", "wage": lambda x: f"S${x:,.2f}/h",
             "machineMonth": lambda x: f"S${x:,.0f}/month", "cupsPerDay": lambda x: f"{x:,.0f} cups/day",
             "newShare": lambda x: f"{x * 100:.0f}% new staff", "machineMult": lambda x: f"{x:.2f}×",
             "coordHuman": lambda x: f"{x:.2f}", "coordMixed": lambda x: f"{x:.2f}"}
SETUP_NAME = {"all_human": "all-human", "mixed": "mixed", "all_machine": "all-machine"}


def trigger_text(lever: str, a: str, b: str) -> tuple:
    """(value, short reading, raw result) for one sim/ break-even. Never typed in: read from data.json."""
    r = next(x for x in DATA_CACHE["breakEven"] if (x["lever"], x["a"], x["b"]) == (lever, a, b))
    f = LEVER_FMT[lever]
    rng = f"swept {f(r['range'][0])} to {f(r['range'][1])}"
    if r["kind"] == "none_in_range":
        return ("none in range", f"No break-even in range ({rng}): {SETUP_NAME[r[r['cheaper']]]} is cheaper "
                                 f"throughout, so this choice holds everywhere.", r)
    lo = r[r["below"]]
    hi = b if lo == a else a
    step = " Step: staff and machines come in whole units." if r["step"] else ""
    if lever == "cupsPerDay":
        step += " Trigger range, not a new-store forecast."
    return (f(r["x"]) + (" · step" if r["step"] else ""),
            f"Below it {SETUP_NAME[lo]} is cheaper, above it {SETUP_NAME[hi]} ({rng}).{step}", r)


TRADE_LABEL = {"wage": "Wage per hour", "cupsPerDay": "Steady volume", "machineMonth": "Machine cost",
               "u": "Forecast band", "coordHuman": "All-human coordination", "coordMixed": "Mixed coordination",
               "newShare": "New-hire share", "machineMult": "Machine time"}


def cost_split() -> dict:
    """Cost per cup by setup at the default band and surge, split into labour, machines and lost sales (sim/ sweep)."""
    d, g = DATA_CACHE, A["surge"]["surge_default"]["value"]
    rows, u = d["sweeps"][g]["rows"], d["defaults"]["u"]
    for r0, r1 in zip(rows, rows[1:]):
        if r0["u"] <= u <= r1["u"]:
            t = (u - r0["u"]) / (r1["u"] - r0["u"])
            return {k: {f: r0[k][f] + t * (r1[k][f] - r0[k][f]) for f in ("cost", "machine", "labour", "lost")}
                    for k in ("all_human", "mixed", "all_machine")}
    return {k: rows[-1][k] for k in ("all_human", "mixed", "all_machine")}


def price_tip(lever: str, kind: str, a: str = "all_human", b: str = "mixed") -> str:
    """Hover text explaining how a price in the trigger tables is derived. Empty for non-price levers."""
    if lever not in ("wage", "machineMonth"):
        return ""
    c, d = cost_split(), DATA_CACHE
    cpd = A["store"]["cups_per_store_per_year"]["value"] / A["store"]["open_days_per_year"]["value"]
    days, util = A["store"]["open_days_per_year"]["value"], d["util"][A["surge"]["surge_default"]["value"]]
    split = lambda k: (f"{SETUP_NAME[k]}: labour S${c[k]['labour']:.3f} + machines S${c[k]['machine']:.3f} + lost sales "
                       f"S${c[k]['lost']:.3f} = S${c[k]['cost']:.3f} a cup")
    V = A["validation"]["breakeven"]["value"]
    how = (f"Found by sim/ breakEven: {V['grid_points']} points scanned across the approved range, then bisection to "
           f"{V['tol_x_share_of_range'] * 100:g}% of the range; every other input at our defaults.")
    if lever == "wage" and kind == "now":
        return "How S$15.06 is built (assumptions.json):\n" + A["costs"]["labour_cost_per_hour"]["rationale"].split(". ", 1)[1]
    if lever == "machineMonth" and kind == "now":
        m = A["costs"]["machine_cost_per_unit_per_month"]
        return (f"Approved as USD {m['value_usd']:,.0f} a month per machine unit, converted at "
                f"{A['_meta']['fx_sgd_per_usd']['value']} SGD per USD (L-xrates) = S${m['value']:,.2f}. "
                + m["rationale"].split(" Converted")[0])
    if kind == "none":
        r = next(x for x in d["breakEven"] if (x["lever"], x["a"], x["b"]) == (lever, a, b))
        f = LEVER_FMT[lever]
        return (f"No break-even: across {f(r['range'][0])} to {f(r['range'][1])}, {SETUP_NAME[r[r['cheaper']]]} stays "
                f"cheaper.\nAt our defaults:\n{split(a)}\n{split(b)}\n{how}")
    if lever == "wage":
        return (f"The wage at which {SETUP_NAME[a]} and {SETUP_NAME[b]} cost the same per cup.\nAt our defaults:\n"
                f"{split(a)}\n{split(b)}\nA higher wage raises labour per cup in proportion, and the counter with more "
                f"staff hours per cup rises faster (peak staff: all-human {util['all_human']['staff']}, mixed "
                f"{util['mixed']['staff']} plus {util['mixed']['machineUnits']} machines).\n{how}")
    units = util[b]["machineUnits"]
    per100 = units * 100 * 12 / days / cpd
    return (f"The machine price at which {SETUP_NAME[a]} and {SETUP_NAME[b]} cost the same per cup.\nAt our defaults:\n"
            f"{split(a)}\n{split(b)}\n{SETUP_NAME[b].capitalize()} carries {units} machine units: each S$100 a month per "
            f"unit adds {units} × S$100 × 12 ÷ {days} days ÷ {cpd:.0f} cups a day = about S${per100:.3f} a cup.\n{how}")


def trigger_rows(a: str, b: str, levers: list, now: dict) -> list:
    """(sort key, row html) per lever: when setup b beats setup a, from sim/ breakEven at our defaults."""
    rows = []
    for lever in levers:
        r = next(x for x in DATA_CACHE["breakEven"] if (x["lever"], x["a"], x["b"]) == (lever, a, b))
        f = LEVER_FMT[lever]
        tx = price_tip(lever, "none" if r["kind"] == "none_in_range" else "x", a, b)
        tn = price_tip(lever, "now", a, b)
        tip = lambda t: f' class="ptip" data-tip="{esc(t)}" tabindex="0"' if t else ""
        if r["kind"] == "none_in_range":
            rows.append((9e9, f'<tr class="none"><th>{TRADE_LABEL[lever]}</th><td colspan="3"{tip(tx)}>none in '
                              f'{f(r["range"][0])} to {f(r["range"][1])}: {SETUP_NAME[r[r["cheaper"]]]} cheaper '
                              f'throughout</td></tr>'))
            continue
        b_above = r[r["below"]] == a
        dist = (r["x"] - now[lever]) / now[lever]
        rows.append((abs(dist), f'<tr><th>{TRADE_LABEL[lever]}</th><td{tip(tx)}>{"above" if b_above else "below"} '
                                f'<b>{f(r["x"])}</b>{" · step" if r["step"] else ""}</td><td{tip(tn)}>{f(now[lever])}</td>'
                                f'<td>{dist * 100:+.0f}%</td></tr>'))
    rows.sort(key=lambda t: t[0])
    return rows


def render_playbook(s: dict) -> str:
    now, k = DATA_CACHE["leverNow"], s["key"]
    head = '<thead><tr><th>Trigger</th><th>flips when</th><th>ours</th><th>gap</th></tr></thead>'
    parts = []
    for title, who, (a, b), levers in s["groups"]:
        rows = "".join(h for _, h in trigger_rows(a, b, levers, now)).replace("<tr>", '<tr class="near">', 1)
        parts.append(f'<tr class="grp"><th colspan="4">{esc(title)} <span>· {esc(who)}</span></th></tr>{rows}')
    m = DATA_CACHE["milkTrigger"]
    title, who = s["stock_group"]
    mt = (f"Waste cost per litre at which the best opening order falls to the base forecast: a lost cup costs "
          f"S${m['stockoutCost']:.2f} (provision.stockout_cost_per_cup: {A['provision']['stockout_cost_per_cup']['rationale']}) "
          f"and uses {m['milkPerCup']:g} L of milk (provision.milk_litres_per_cup), so a litre short loses "
          f"S${m['stockoutCost']:.2f} ÷ {m['milkPerCup']:g} = S${m['value']:.2f}. Our waste cost is "
          f"S${A['provision']['milk_waste_cost_per_litre']['value']:.2f} a litre "
          f"({A['provision']['milk_waste_cost_per_litre']['rationale']}).")
    milk = (f'<tr><th>Milk waste per litre</th><td colspan="3" class="ptip" data-tip="{esc(mt)}" tabindex="0">'
            + (f'none in S${m["range"][0]:.2f} to S${m["range"][1]:.2f}/L: order above base throughout '
               f'(flips at S${m["value"]:.2f}/L = S${m["stockoutCost"]:.2f} per lost cup ÷ {m["milkPerCup"]:g} L)'
               if m["kind"] == "none_in_range" else f'above <b>S${m["value"]:.2f}/L</b>') + '</td></tr>')
    parts.append(f'<tr class="grp"><th colspan="4">{esc(title)} <span>· {esc(who)}</span></th></tr>{milk}')
    table = (f'<div class="pbtable"><table>{head}<tbody>{"".join(parts)}</tbody></table>'
             f'{ed(f"{k}.tn", s["table_note"], "p", "tnote")}</div>')
    return (f'<div class="grid gpb"><div class="left">{table}</div>'
            f'<div class="right">{render_explainer(s)}{render_view(s)}</div></div>')


def render_tradeoff(s: dict) -> str:
    """Mixed versus all-human, one row per lever: the break-even from sim/, where we are, and how far."""
    rows = trigger_rows("all_human", "mixed", s["tradeoff"], DATA_CACHE["leverNow"])
    body = "".join(h for _, h in rows).replace("<tr>", '<tr class="near">', 1)
    return (f'<div class="tradeoff"><h4>{esc(s["tradeoff_title"])}</h4><table><thead><tr><th>Mixed wins when…</th>'
            f'<th>is</th><th>ours</th><th>gap</th></tr></thead><tbody>{body}</tbody></table>'
            f'<p class="tnote">Break-evens from sim/; nearest trigger first.</p></div>')


def milk_trigger_text() -> tuple:
    """The milk waste cost per litre at which the best opening order falls to the base forecast (sim/ milkTrigger)."""
    m = DATA_CACHE["milkTrigger"]
    conv = f"= S${m['stockoutCost']:.2f} per lost cup ÷ {m['milkPerCup']:g} L per cup"
    if m["kind"] == "none_in_range":
        return (f"S${m['value']:.2f}/L", f"{conv}. Above the whole S${m['range'][0]:.2f} to S${m['range'][1]:.2f}/L "
                                        f"range, so ordering above base holds everywhere.", {"lever": "milk", "x": m["value"]})
    return (f"S${m['value']:.2f}/L", f"{conv}. Above it, order at or below base.", {"lever": "milk", "x": m["value"]})


def render_decision(s: dict) -> str:
    k, d = s["key"], s["decision"]
    if d["trigger"][0] == "milk":
        val, read, r = milk_trigger_text()
        label = "waste cost per litre at which the best order falls to the base forecast"
    else:
        val, read, r = trigger_text(*d["trigger"][:3])
        label = d["trigger"][3]
    if not d.get("also"):
        also = ""
    elif isinstance(d["also"], str):
        also = esc(d["also"])
    else:
        aval, aread, r2 = trigger_text(*d["also"][:3])
        also = f'<b>{esc(d["also"][3])}:</b> {esc(aval + "." if r2["kind"] == "value" else aread)}'
    live = f' data-lever="{r["lever"]}" data-x="{r.get("x", "")}"'
    return (f'<div class="dstrip"{live}><span class="dtag">DECISION STRIP</span>'
            f'<div class="df"><span class="dl">Decision</span>{ed(f"{k}.dq", d["question"], "p")}</div>'
            f'<div class="df"><span class="dl">Who decides</span>{ed(f"{k}.dw", d["who"], "p")}</div>'
            f'<div class="df dt"><span class="dl">Trigger · computed by sim/</span><p><b class="dv">{esc(val)}</b> '
            f'<span class="dlab">{esc(label)}.</span> {esc(read)}</p>'
            + (f'<p class="dalso">{also}</p>' if also else "") + '</div>'
            f'<div class="df"><span class="dl">Action</span>{ed(f"{k}.da", d["action"], "p")}<p class="dnow"></p></div></div>')


def fmt_value(v) -> str:
    """Compact, readable value for the assumptions table."""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (int, float)):
        return f"{v:,.4g}" if abs(v) < 1e5 else f"{v:,.0f}"
    if isinstance(v, list):
        return ", ".join(fmt_value(x) for x in v)
    t = " · ".join(f"{k.replace('_', ' ')} {fmt_value(x)}" for k, x in v.items()) if isinstance(v, dict) else str(v)
    return t if len(t) <= 110 else t[:108] + "…"


def render_a1(s: dict) -> str:
    rows = []
    for sec in s["sections"]:
        rows.append(f'<tr class="grp"><th colspan="5">{esc(sec.replace("_", " "))}</th></tr>')
        for key, a in A[sec].items():
            if not isinstance(a, dict) or "value" not in a:
                continue
            rng = "–" if a.get("range") is None else (fmt_value(a["range"][0]) + " to " + fmt_value(a["range"][1])
                                                      if isinstance(a["range"], list) and len(a["range"]) == 2 else fmt_value(a["range"]))
            src = a.get("source", "")
            rows.append(f'<tr><th>{esc(key.replace("_", " "))}</th><td>{esc(fmt_value(a["value"]))}</td>'
                        f'<td>{esc(str(a.get("unit", "")))}</td><td>{esc(rng)}</td><td>{esc(src)}</td></tr>')
    return (f'<div class="apx a1t"><table><colgroup><col style="width:190px"><col style="width:380px">'
            f'<col style="width:270px"><col style="width:110px"><col></colgroup><thead><tr><th>Assumption</th><th>Value</th><th>Unit</th><th>Range</th>'
            f'<th>Source</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
            f'<p class="tnote">Source "assumption" = our illustrative choice; ledger IDs are listed in A3. Ranges drive '
            f'the sliders and the sensitivity chart in A2.</p></div>')


def render_a2(s: dict) -> str:
    d = DATA_CACHE
    W = A["validation"]["week5_comparison"]["value"]
    w5 = "".join(f'<tr><td>{esc(", ".join(f"{x:g}" for x in w["speeds"]))}</td><td>{w["engine"]:.3f}</td>'
                 f'<td>{w["pooled"]:.3f}</td><td class="{"bad" if w["gapPct"] > W["tolerance_pct"] else "ok"}">'
                 f'{w["gapPct"]:.2f}%</td></tr>' for w in d["week5"])
    st = d["stability"]
    KIND = {"mixed_cheaper_everywhere": "mixed cheaper than full automation at every band width",
            "machine_cheaper_everywhere": "full automation cheaper than mixed at every band width",
            "crossover": "with a crossover", "reverse": "with a reverse crossover"}
    kinds = ", ".join(f"{v} of {st['seeds']} seeds: {KIND.get(k, k.replace('_', ' '))}" for k, v in st["kinds"].items())
    cap = d["storeCap"]
    caprows = "".join(f'<tr><td>{SETUP_NAME[k]}</td><td>{v["replica"]:.2f}</td><td>{v["nominal"]:.2f}</td>'
                      f'<td>{v["replica"] / v["nominal"] * 100:.0f}%</td></tr>' for k, v in cap.items())
    left = (f'<div class="apx"><h4>Week 5 check: pooled staffing formula vs the Week 5 engine</h4>'
            f'<table><thead><tr><th>Worker speeds</th><th>Engine, lines/h</th><th>Pooled</th><th>Gap</th></tr></thead>'
            f'<tbody>{w5}</tbody></table><p class="tnote"><b class="bad">{"Passes" if d["week5Pass"] else "Fails"}</b> '
            f'the pre-registered ±{W["tolerance_pct"]:g}% tolerance: the pooled formula overstates a real bucket brigade. '
            f'The coordination factor (0.9) absorbs part of this.</p>'
            f'<h4>Seed stability</h4><p class="tnote">Uncertainty sweep at the {esc(st["surge"])} surge: {esc(kinds)}. '
            + (f'The result agrees in every seed. The pre-registered rule asks for a crossover point in most seeds; '
               f'with none in any seed, the deck shows no crossover point, as the rule requires.</p>'
               if not st["pass"] and st["kinds"].get("crossover", 0) == 0 else
               f'{"Passes" if st["pass"] else "Does not pass"} the stability rule.</p>') +
            f'<h4>Store replica (walking modelled) vs cost-model capacity, cups per minute</h4>'
            f'<table><thead><tr><th>Counter</th><th>Replica</th><th>Cost model</th><th>Share</th></tr></thead>'
            f'<tbody>{caprows}</tbody></table><p class="tnote">The replica animates movement only; times and costs '
            f'on the slides come from the cost model.</p></div>')
    T = d["tornado"]
    rows = [r for r in T["rows"] if abs(r["gapHi"] - r["gapLo"]) > 1e-3]
    flat = [r for r in T["rows"] if abs(r["gapHi"] - r["gapLo"]) <= 1e-3]
    lo = min(min(r["gapLo"], r["gapHi"]) for r in rows + [{"gapLo": T["base"], "gapHi": T["base"]}])
    hi = max(max(r["gapLo"], r["gapHi"]) for r in rows + [{"gapLo": T["base"], "gapHi": T["base"]}])
    lo, hi = min(lo, 0) * 1.1, hi * 1.1
    Wd, L, R, rh, top = 560, 190, 470, 19, 22
    X = lambda v: L + (R - L) * (v - lo) / (hi - lo)
    svg = [f'<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{top - 6}" y2="{top + rh * len(rows)}" stroke="#23272f"/>',
           f'<line x1="{X(T["base"]):.1f}" x2="{X(T["base"]):.1f}" y1="{top - 6}" y2="{top + rh * len(rows)}" '
           f'stroke="#9aa3af" stroke-dasharray="3 3"/>',
           f'<text x="{X(0) - 4:.1f}" y="{top - 9}" font-size="9.5" fill="#2563eb" text-anchor="end">← mixed cheaper</text>',
           f'<text x="{X(0) + 4:.1f}" y="{top - 9}" font-size="9.5" fill="#2a9d8f">all-human cheaper →</text>']
    for i, r in enumerate(rows):
        y = top + i * rh
        a, b = sorted((r["gapLo"], r["gapHi"]))
        flips = a < 0 < b or (a < 0 and b < 0)
        svg.append(f'<text x="{L - 6}" y="{y + 12}" font-size="10" fill="#23272f" text-anchor="end">'
                   f'{esc(r["key"].split(".")[1].replace("_", " "))}</text>')
        svg.append(f'<rect x="{X(a):.1f}" y="{y + 3}" width="{max(1, X(b) - X(a)):.1f}" height="{rh - 6}" rx="2" '
                   f'fill="{"#d4892a" if flips else "#c5cad3"}"/>')
        svg.append(f'<text x="{X(b) + 4:.1f}" y="{y + 12}" font-size="9" fill="#6b7280">'
                   f'{fmt_value(r["range"][0])}–{fmt_value(r["range"][1])}</text>')
    axis = "".join(f'<text x="{X(v):.1f}" y="{top + rh * len(rows) + 12}" font-size="9" fill="#6b7280" '
                   f'text-anchor="middle">{"−" if v < 0 else ""}S${abs(v):.2f}</text>'
                   for v in (lo / 1.1, 0, hi / 1.1))
    h = top + rh * len(rows) + 18
    right = (f'<div class="apx"><h4>Sensitivity: mixed minus all-human cost per cup, one assumption at a time</h4>'
             f'<svg viewBox="0 0 {Wd} {h}" class="tornado" role="img" aria-label="Sensitivity of the counter gap">'
             f'{"".join(svg)}{axis}</svg><p class="tnote">Dashed: our default gap (S${T["base"]:.3f} a cup, all-human '
             f'cheaper). Amber bars cross zero inside their approved range, so they can flip the choice; labels '
             f'show the range tested. No visible effect: '
             f'{esc(", ".join(r["key"].split(".")[1].replace("_", " ") for r in flat))}.</p></div>')
    return f'<div class="grid ga2"><div class="left">{left}</div><div class="right">{right}</div></div>'


def render_a3(s: dict) -> str:
    def status(t):
        t = t.upper()
        return "informal" if "INFORMAL" in t or t.startswith("I-") else "secondary" if "SECONDARY" in t else "public"
    rows = "".join(f'<tr><th>{esc(k)}</th><td>{esc(v if len(v) <= 165 else v[:163] + "…")}</td>'
                   f'<td class="st {status(k + " " + v)}">{status(k + " " + v)}</td></tr>'
                   for k, v in A["_sources"].items())
    nc = "".join(f"<li>{esc(x)}</li>" for x in s["not_claimed"])
    return (f'<div class="grid ga3"><div class="left apx a3t"><table><thead><tr><th>ID</th><th>Source and what it '
            f'supports</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<div class="right apx"><h4>Claims we did not make</h4><ul class="nc">{nc}</ul></div></div>')


def render_slide(page: int, s: dict, n: int = 0, total: int = 0) -> str:
    k = s["key"]
    sub = ed(f"{k}.sub", s["sub"], "p", "sub") if s.get("sub") else ""
    if s["widget"] == "scope":
        grid = render_scope(s)
    elif s["widget"] == "storefront":
        serve = dict(key=f"{k}t", widget="serve", explainer_title=s["serve_title"], caption=s["serve_caption"],
                     printnote=s["serve_printnote"])
        summary = (f'<summary><span class="slab">{esc(s["serve_summary"])}</span><span class="ssum"></span>'
                   f'<span class="sopen screenonly">open the chart ▸</span><span class="sclose screenonly">close ▾</span></summary>')
        grid = (f'{render_explainer(s)}<div class="grid gstore"><div class="left"><details class="servebox">{summary}'
                f'<div class="servepop">{render_explainer(serve)}</div></details></div>'
                f'<div class="right">{render_view(s)}</div></div>')
    elif s["widget"] == "playbook":
        grid = render_playbook(s)
    elif s["widget"] in ("a1", "a2", "a3"):
        grid = {"a1": render_a1, "a2": render_a2, "a3": render_a3}[s["widget"]](s)
    elif s["widget"] == "volcost":
        conf = ed(f"{k}.conf", s["confidence"], "p", "conf")
        grid = (f'<div class="grid gcost"><div class="left">{render_explainer(s)}</div>'
                f'<div class="right">{render_tradeoff(s)}{conf}</div></div>')
    elif s["widget"] == "benefit":
        gates = "".join(
            f'<div class="gate"><span class="gn">{i + 1}</span><div><p class="gh"><b>{esc(when)}</b> · {esc(what)} '
            f'<span class="gref">slide {esc(ref)}</span></p>{ed(f"{k}.g{i}", body, "p", "gb")}'
            f'<p class="gw">{esc(who)}</p></div></div>'
            for i, (when, what, who, body, ref) in enumerate(s["gates"]))
        risks = "".join(f'<div class="rk"><b>{esc(t)}</b>{ed(f"{k}.r{i}.b", b, "span")}</div>'
                        for i, (t, b) in enumerate(s["risks"]))
        grid = (f'<div class="grid g5"><div class="left">{render_explainer(s)}'
                f'<div class="rkgrid"><h4>Risks and how we would manage them</h4>{risks}</div></div>'
                f'<div class="right"><div class="gates"><h4>{esc(s["gates_title"])}</h4>{gates}</div>'
                f'{render_view(s)}</div></div>')
    else:
        grid = (f'<div class="grid"><div class="points">{render_points(s)}</div>'
                f'<div class="right">{render_explainer(s)}{render_view(s)}</div></div>')
    return f"""
<section class="slide content {k}" aria-label="Slide {page}" data-chapter="{s['chapter']}" data-kicker="{esc(s['kicker'])}">
  {render_rail(s['chapter'], n, total, s.get('kicker', '') if s['chapter'] == 'appendix' else '')}
  {ed(f"{k}.h", s['headline'], "h2")}
  {sub}
  {grid}
  {render_decision(s) if s.get("decision") else ""}
  <div class="foot"><span>{esc(FOOT)} · <span class="assume">explainer figures are illustrative assumptions</span></span><span>{page}</span></div>
  <div class="notes"><p class="nk">SPEAKER NOTES</p>{ed(f"{k}.notes", s['notes'], "p")}<p class="src"><b>Sources:</b> {esc(s['sources'])}</p></div>
</section>"""


def week5_engine() -> str:
    """The Week 5 bucket-brigade engine's simulation part, read from the reference deck (never modified)."""
    src = (ROOT / "week5" / "build_opim639_deck.py").read_text(encoding="utf-8")
    eng = re.search(r'ENGINE = r"""([\s\S]*?)"""', src).group(1).split("/* ================= drawing helpers")[0]
    return f"const W5=(function(){{\n{eng}\nreturn {{Brigade, measure}};\n}})();"


REFNUM: dict = {}


def ledger_check() -> None:
    """Every ledger ID cited in the slides or in assumptions.json must exist in _sources."""
    cited = set(re.findall(r"\b[LI]-[a-z][\w-]*", json.dumps(CONTENT) + json.dumps({k: v for k, v in A.items() if k != "_sources"})))
    missing = sorted(c.rstrip("-") for c in cited if c.rstrip("-") not in A["_sources"])
    if missing:
        raise SystemExit(f"ledger: cited but not in assumptions.json _sources: {', '.join(missing)}")


def timing_check(filled: dict) -> None:
    """Sum each chapter's 'About N seconds/minutes' notes and fail if a chapter runs over its Contents time."""
    used = {c[0]: 0 for c in CHAPTERS}
    for key in DECK:
        it = filled.get(key)
        if not it or it["chapter"] == "appendix":
            continue
        m = re.match(r"About (\d+(?:\.\d+)?) (minutes?|seconds)", it["notes"])
        if not m:
            raise SystemExit(f"timing: notes for {key!r} do not start with 'About N seconds/minutes'")
        used[it["chapter"]] += float(m.group(1)) * (60 if m.group(2).startswith("minute") else 1)
    over = [f"{cid}: {used[cid]:.0f} s against {sec} s" for cid, _, _, sec in CHAPTERS if used[cid] > sec]
    if over:
        raise SystemExit("timing: chapters over their Contents time - " + "; ".join(over))
    print("timing: " + ", ".join(f"{cid} {used[cid]:.0f}/{sec} s" for cid, _, _, sec in CHAPTERS))


def slide_label(key: str, filled: dict) -> str:
    if key in REFNUM:
        return str(REFNUM[key])
    m = re.search(r"\bA[1-3]\b", filled[key]["kicker"])
    return m.group(0) if m else key


def write_claims(filled: dict, simv: dict) -> None:
    """deck/claims.md from the same data and placeholders as the slides."""
    text = {k: json.dumps(v, ensure_ascii=False) for k, v in CONTENT_RAW.items()}
    where = lambda needle: ", ".join(slide_label(k, filled) for k in DECK if k in text and needle in text[k]) or "-"
    fill = lambda t: check_and_fill(t, simv, "claims")
    status = lambda t: ("INFORMAL" if "INFORMAL" in t.upper() else "SECONDARY" if "SECONDARY" in t.upper() else "OK")
    out = ["# Claims register: Chagee deck", "",
           "Generated by deck/build_deck.py from assumptions.json, data.json and the slide text. Do not edit by hand.",
           "Slide numbers follow the progress rail (on-stage slides); A1-A3 are appendix pages. Status: OK = public "
           "ledger source; SECONDARY = secondary source, flagged where shown; INFORMAL / CHECK = confirm before "
           "presenting; MODEL = simulator or assumption (illustrative).", "",
           "## Chagee facts", "", "| Fact | Value | Source | Status | Slides |", "|---|---|---|---|---|"]
    for k, a in A["facts"].items():
        if isinstance(a, dict) and "value" in a:
            src = a["source"]
            out.append(f'| {k.replace("_", " ")} | {fmt_value(a["value"])} {a.get("unit", "")} | {src} | '
                       f'{status(src + " " + A["_sources"].get(src, ""))} | {where("{{facts." + k)} |')
    out += ["", "## Ledger sources and where they are cited", "", "| ID | Status | Cited on slides |", "|---|---|---|"]
    for k, v in A["_sources"].items():
        out.append(f"| {k} | {status(k + ' ' + v)} | {where(k)} |")
    out += ["", "## Claims that rest on our reading or an informal source", "",
            "| Claim | Slides | Source | Status |", "|---|---|---|---|"]
    for c, ks, src, st in CHECK_CLAIMS:
        out.append(f"| {c} | {', '.join(slide_label(x, filled) for x in ks)} | {src} | {st} |")
    out += ["", "## Model figures (illustrative)", "", "| Claim | Slides | Source | Status |", "|---|---|---|---|"]
    for c, ks, src in MODEL_CLAIMS:
        out.append(f"| {fill(c)} | {', '.join(slide_label(x, filled) for x in ks)} | {src} | MODEL |")
    out += ["", "## Deliberately not claimed", ""] + [f"- {x}" for x in filled["a3"]["not_claimed"]]
    out += ["", "## Likely Q&A: short answers", ""] + [f"{i + 1}. **{q}** {fill(a)}" for i, (q, a) in enumerate(QA)]
    (HERE / "claims.md").write_text("\n".join(out) + "\n", encoding="utf-8")


CONTENT_RAW: dict = {}


def build() -> Path:
    data = ensure_data()
    chap = {**{c["key"]: c["chapter"] for c in CONTENT}, **{k: v["chapter"] for k, v in PLACEHOLDERS.items()}}
    REFNUM.update({k: i + 1 for i, k in enumerate(d for d in DECK if chap[d] != "appendix")})
    DATA_CACHE.update(data)
    simv = sim_values(data)
    filled = {s["key"]: check_and_fill(s, simv, s["key"]) for s in CONTENT}
    CONTENT_RAW.update({s["key"]: s for s in CONTENT})
    ledger_check()
    timing_check(filled)
    write_claims(filled, simv)
    for ph in PLACEHOLDERS.values():
        check_and_fill(ph, simv, ph["key"])
    items = [filled[d] if d in filled else PLACEHOLDERS[d] for d in DECK]
    total = sum(1 for it in items if it["chapter"] != "appendix")
    first = {}                                    # chapter -> content-slide numbers, for the Contents slide
    for n, it in enumerate(items, start=1):
        first.setdefault(it["chapter"], []).append(n)
    parts, page = [render_title(), render_contents(first)], 3
    for n, it in enumerate(items, start=1):
        parts.append(render_placeholder(page, n, total, it) if it["key"] in [p["key"] for p in PLACEHOLDERS.values()]
                     else render_slide(page, it, n, total))
        page += 1
    slides = "".join(parts)
    sim_js = (ROOT / "sim" / "sim.js").read_text(encoding="utf-8")
    page = (TEMPLATE_PATH.read_text(encoding="utf-8")
            .replace("__SLIDES__", slides)
            .replace("__ASSUMPTIONS__", json.dumps(A).replace("</", "<\\/"))
            .replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
            .replace("__REFS__", json.dumps(REFNUM))
            .replace("__SIMJS__", sim_js)
            .replace("__W5__", week5_engine())
            .replace("__MECHJS__", (ROOT / "sim" / "mechanism.js").read_text(encoding="utf-8") + "\n"
                     + (ROOT / "sim" / "store.js").read_text(encoding="utf-8"))
            .replace("__ENGINE__", ENGINE_PATH.read_text(encoding="utf-8")))
    OUT.write_text(page, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({len(DECK) + 2} slides incl. title and contents)")
    if "--open" in sys.argv:
        webbrowser.open(p.resolve().as_uri())
