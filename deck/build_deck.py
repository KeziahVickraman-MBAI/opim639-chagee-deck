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

FOOT = "OPIM639 · Chagee group project · Group [TBC]"

TITLE = dict(
    course="OPIM639 · Innovations & Operations of Intelligent Online Marketplaces",
    title="Chagee: opening overseas stores right",
    topic="Predict demand, provision the store, size the counter",
    group="Group [TBC]",
    members=["[Member names TBC - confirm with the team]"],
)

# ---------------------------------------------------------------------------
# Slide content. Every number is a placeholder; see module docstring.
# ---------------------------------------------------------------------------
CONTENT = [
    dict(
        key="s1", widget="where",
        kicker="1 · Why this slice",
        headline="Chagee’s supply chain is fixed, so new-market risk lands on how much a store opens with "
                 "and how fast its counter serves",
        points=[
            ("trend", "Scaling fast into markets it has not run before",
             "{{facts.stores_end_2025|int}} stores at end-2025, {{facts.overseas_stores|int}} of them overseas in "
             "{{facts.overseas_markets|int}} markets, and about {{benefit.overseas_stores_per_year|int}} more overseas "
             "openings planned for 2026. FY2025 GMV RMB {{facts.gmv_2025_rmb_bn|f2}}bn, net revenue RMB "
             "{{facts.net_revenue_2025_rmb_bn|f2}}bn."),
            ("lock", "The upstream is rigid by design",
             "Chagee says it sources tea and milk directly for domestic operations, with distribution run from HQ. "
             "Reported own Yunnan plantations and a narrow menu (tea lattes about "
             "{{facts.tea_latte_share_china|pct}} of China sales, secondary source) keep sourcing fixed."),
            ("users", "New-store forecasts lean on local judgement",
             "Our reading: a new market’s opening forecast is judgement-led by a local General Manager, while "
             "service is moving toward semi-automation (QR-scan dispensing, Chagee Express)."),
            ("route", "Why not a marketplace lens",
             "Chagee runs one closed channel, app to store: no third-party sellers, no sell-vs-FBA choice and no "
             "online-versus-offline conflict. We leave the marketplace-design topics aside; the franchise GMV "
             "revenue share is the one overlap, and it is out of scope."),
        ],
        explainer_title="Where does uncertainty land?",
        scenarios=[
            ("rigid", "Rigid sourcing", "Chagee today, our reading",
             [("Sourcing", "Fixed: single origin", 0), ("Distribution", "Fixed: run from HQ", 0),
              ("Opening stock", "Absorbs the miss", 3), ("Counter speed", "Absorbs the miss", 3)]),
            ("local", "Localised sourcing", "For contrast only",
             [("Sourcing", "Flexes with local suppliers", 2), ("Distribution", "Shorter, local", 1),
              ("Opening stock", "Less exposed", 1), ("Counter speed", "Still exposed", 3)]),
        ],
        caption="Our reading of public sources, not a Chagee statement. With sourcing fixed, a demand miss can only "
                "be absorbed in the store: by the stock it opened with, or by how fast the counter serves. Local "
                "sourcing would ease stock risk, but the counter stays exposed either way.",
        printnote="Printed with both columns shown. Live: the toggle highlights one.",
        view_kicker="Our view",
        view_lead="Take the rigid upstream as given; fix the store-level decisions.",
        view_body="New-market uncertainty lands on three decisions we can model: the demand forecast (slide 2), "
                  "the opening stock (slide 3) and the counter setup (slide 4).",
        notes=("About 1.5 minutes. Start with scale: Chagee is opening overseas faster than it can learn each "
               "market. Then the key move: Chagee's upstream is rigid by design. It sources tea and milk directly "
               "and runs distribution from HQ; reports describe its own Yunnan plantations and a menu dominated by "
               "tea lattes. That is a strength, but it means sourcing cannot soak up a demand miss. So where does "
               "the miss go? Into the store: the stock it opened with, and the speed of its counter. Use the toggle: "
               "with localised sourcing, stock risk eases, but the counter stays exposed either way. Say clearly "
               "that this is our reading, not a Chagee statement. On the marketplace weeks: Chagee has one closed "
               "app-to-store channel, so seller and channel-conflict topics do not apply; the franchise revenue "
               "share is the one overlap and is out of scope."),
        sources="Scale facts: L-jiemian. Direct sourcing and HQ distribution: L-prn (company release). Yunnan "
                "plantations and tea-latte share: L-prometheus (SECONDARY). Narrow menu choice: L-chainreact "
                "(secondary). Semi-automation: L-unsw, L-cyberrt. GM-led forecasting: I-leeyen (INFORMAL - check with "
                "Lee Yen before presenting).",
    ),
    dict(
        key="s2", widget="band",
        kicker="2 · Predict",
        headline="App-only ordering lets Chagee read a new market’s demand before the store opens, and tell "
                 "opening hype from repeat habit",
        points=[
            ("phone", "Every order is tied to a member",
             "With app-only ordering (our understanding), each cup is linked to a member account, so a pre-launch "
             "waitlist is a demand signal, not a guess."),
            ("wave", "More signal, a narrower band",
             "The forecast is a range, not a number. As sign-ups build before launch, the band narrows from "
             "±{{demand.uncertainty_no_signal|pct}} to ±{{demand.uncertainty_strong_signal|pct}} of the base "
             "(illustrative)."),
            ("cycle", "Hype versus habit",
             "Opening crowds are not steady demand: the Kuala Lumpur store reportedly sold "
             "{{facts.kl_opening_day_cups|int}}+ cups on its first day (secondary source). Member IDs separate first "
             "orders from repeat orders."),
            ("alert", "Blind spot: tourists and non-app orders",
             "Visitors and tourist exceptions are outside the member signal, so the forecast understates demand "
             "where tourists matter. We name this gap rather than model it."),
        ],
        explainer_title="Demand range before opening",
        caption="Weekly cups at one new store. The band covers {{demand.band_coverage|pct}} of likely outcomes; "
                "its half-width is the uncertainty that slides 3 to 5 use.",
        printnote="Printed at the default signal strength ({{predict.signal_strength_default|pct}}) with opening "
                  "hype removed.",
        view_kicker="Our view",
        view_lead="Hand on a demand band, not a single number.",
        view_body="Our contribution, to our knowledge based on public sources: using app-only member data to "
                  "separate opening hype from repeat demand before launch. Tourist demand stays a named blind spot.",
        notes=("About 1.5 minutes. Because Chagee orders go through the app (our understanding from an industry "
               "conversation, to be confirmed), every cup is tied to a member. That turns a pre-launch waitlist "
               "into a demand signal. Move the slider: with no signal the band is wide; as sign-ups build it "
               "narrows. The width of this band is the uncertainty we carry into the next three slides. Toggle the "
               "hype: opening crowds, like the reported opening day in Kuala Lumpur, are not steady demand, and "
               "member IDs let us separate first orders from repeat orders. Be upfront about the blind spot: "
               "tourists and non-app orders are invisible to this signal, so the forecast understates demand in "
               "tourist areas. Novelty: AI forecasting and siting exist, e.g. Starbucks Deep Brew; our point is "
               "using a closed app channel to read demand before the store exists, to our knowledge."),
        sources="App-only ordering with tourist exceptions: I-leeyen (INFORMAL - check before presenting). Kuala "
                "Lumpur opening day: L-gabgrowth (secondary). Not novel - AI forecasting and siting: L-starbucks.",
    ),
    dict(
        key="s3", widget="stock",
        kicker="3 · Provision",
        headline="The wider the demand range, the costlier the opening-stock decision, especially with fresh milk",
        points=[
            ("scale", "Two ways to be wrong",
             "Too much fresh milk expires; too little turns customers away. Week 1 newsvendor logic: stock up to "
             "the point where the next litre is as likely to be wasted as to save a sale."),
            ("coins", "Here a stockout costs more than waste",
             "A missed cup loses {{provision.stockout_cost_per_cup|sgd}}; a spare litre of milk wastes "
             "{{provision.milk_waste_cost_per_litre|sgd}}. So the best order sits high in the band, at the "
             "{{sim.critical_ratio|pct}} point of demand."),
            ("moon", "Shelf life caps the buffer",
             "Fresh milk keeps about {{provision.milk_shelf_life_days|int}} days (illustrative), so extra stock "
             "cannot be carried forward. A narrower band from slide 2 is the cheaper fix."),
        ],
        explainer_title="Opening stock calculator",
        caption="Expected cost of the first fresh-milk order at one store, using slide 2’s band. Overseas milk "
                "sourcing is unknown; figures are generic.",
        printnote="Printed at the band from slide 2 and the default of {{provision.opening_stock_days|int}} days "
                  "of stock.",
        view_kicker="Our view",
        view_lead="Narrow the band before you stock the store.",
        view_body="From no signal to the default signal, the expected cost of the best opening order falls from "
                  "{{sim.prov_none|sgd0}} to {{sim.prov_def|sgd0}} per store (illustrative). Hand-off to slide 4: "
                  "the same band sizes the counter.",
        notes=("About 1 minute. This is Week 1 newsvendor logic applied to fresh milk. Too much expires, too "
               "little loses sales, and here a lost cup costs more than a wasted litre, so the best order sits "
               "high in the band. Show the curve: the slider is days of opening stock; the dot marks the cheapest "
               "level. Then go back to slide 2 in your head: a wider band pushes the best order up and makes even "
               "the best decision more expensive. That is the value of the pre-launch signal in stock terms. "
               "Caveats: we assume the first order covers one shelf life before regular deliveries, and milk "
               "costs are generic because Chagee's overseas milk sourcing is not public."),
        sources="All figures: assumptions.json (illustrative). Overseas milk sourcing: unknown, deliberately not "
                "claimed (brief.md section 9).",
    ),
    dict(
        key="s4", widget="cross",
        kicker="4 · Perform",
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
        view_lead="Start lean and mixed; automate once volume and peaks are proven, not just once the forecast "
                  "narrows.",
        view_body="In our model an all-human counter is cheaper still ({{sim.cost_h|sgd}} vs {{sim.cost_m|sgd}} per "
                  "cup at the default band), but it is the most exposed to surges and turnover. Machine breakdowns "
                  "are not modelled, which flatters automation.",
        notes=("About 2 minutes, the centrepiece. Our hypothesis was: a mixed counter beats full automation until "
               "demand becomes predictable. We built a simulator to test it, and it only half holds. Mixed does "
               "beat full automation at the default settings, at every level of uncertainty. But the reason is not "
               "uncertainty. Machines come in whole units: one per station already has several times the peak "
               "demand of a new store, so the automated line sits idle most of the day and its fixed cost is spread "
               "over too few cups. Move the uncertainty slider: the lines barely move. Switch to a large surge: now "
               "the people-based counters overflow and full automation wins. So the real trigger for automation is "
               "proven volume and peaks. Be honest about limits: all-human is cheapest in our model; the pooled "
               "staffing formula slightly overstates a real bucket brigade (our Week 5 check missed its tolerance, "
               "gap {{sim.w5_lo|f1}} to {{sim.w5_hi|f1}} percent); breakdowns are not modelled. To our knowledge, "
               "simulating a store before it exists, fed by its demand forecast, is our contribution; store digital "
               "twins today replicate existing stores."),
        sources="All figures: sim/ with assumptions.json (illustrative). Semi-automation context: L-unsw, L-cyberrt. "
                "Not novel - beverage automation: L-gongcha (company-reported), L-slate; store digital twins: "
                "L-mosimtec. Labour cost floor: L-mom-pwm, L-cpf.",
    ),
    dict(
        key="s5", widget="benefit",
        kicker="5 · Benefit, risks, next step",
        headline="Even modest per-store savings compound across about {{benefit.overseas_stores_per_year|int}} "
                 "overseas openings a year, if the risks are managed",
        explainer_title="Benefit calculator",
        caption="A sizing of the prize, not a forecast: first-year, new stores only, each term an assumption you "
                "can move.",
        printnote="Printed at the linked defaults: saving per cup from slide 4, waste avoided from slide 3.",
        risks=[
            ("Staff dependence and turnover",
             "A people-based counter relies on trained staff, and new hires are slower. Keep SOP-led training and "
             "the flexible worker role; track turnover as in slide 4."),
            ("Tourist and non-app demand is invisible",
             "The member signal misses visitors, so the band sits too low in tourist areas. Widen it there and "
             "log walk-up exceptions after opening."),
            ("Opening crowds read as steady demand",
             "Sizing to opening-week queues overbuys machines and staff. Separate first orders from repeat orders "
             "before committing capex."),
            ("Automation versus the premium teahouse",
             "Heavy automation could undercut the premium experience. The mixed setup keeps people at the "
             "customer-facing steps: finishing and handover."),
        ],
        next_title="Next step with real Chagee data",
        next_items=[
            "Replace every assumption with store actuals: station times, wages, machine costs.",
            "Back-test the waitlist signal on recent openings, such as Korea (launch planned for Q2 2026).",
            "Pilot mixed versus automated counters in paired new stores.",
        ],
        view_kicker="Our conclusion",
        view_lead="The saving per cup is small; the case is the count of openings.",
        view_body="Our simulator rejected the claim we set out to prove; what survives is simpler: start lean and "
                  "mixed, read demand before opening, and automate on proven volume. To our knowledge, based on "
                  "public sources, simulating a store before it exists is the new part.",
        notes=("About 1 minute. The benefit is a formula, not a forecast: stores opened, times cups per store, times "
               "the saving per cup from slide 4, plus the stock cost avoided from slide 3. Each term is a slider; "
               "the defaults are linked to the earlier slides. The per-cup saving is cents, but it repeats across "
               "about {{benefit.overseas_stores_per_year|int}} overseas openings a year. Then the risks: click through each. Staff turnover; "
               "tourists invisible to the app signal; opening crowds mistaken for steady demand; and automation "
               "versus the premium teahouse feel. Close with the next step: with Chagee's real data we would "
               "replace every assumption, back-test the waitlist signal on recent openings such as Korea, and "
               "pilot mixed against automated counters."),
        sources="Overseas openings planned for 2026 and Korea launch: L-jiemian. Everything else: assumptions.json "
                "and sim/ (illustrative).",
    ),
]

# ---------------------------------------------------------------------------
# Placeholders and the no-raw-numbers check
# ---------------------------------------------------------------------------
PH = re.compile(r"\{\{([\w.]+)\|(\w+)\}\}")
ALLOW = re.compile(r"^\d · |^About \d+(?:\.\d+)? minutes?|\bsection \d+|\bslides? \d+(?: (?:to|and) \d+)?|\b(?:FY)?20\d\d\b|\bWeeks? \d+(?:[–-]\d+)?(?: and \d+)?|OPIM639|\bQ[1-4]\b|\b[LI]-[\w-]+")
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

    def at(rs, u, f):
        for a, b in zip(rs, rs[1:]):
            if a["u"] <= u <= b["u"]:
                t = (u - a["u"]) / (b["u"] - a["u"])
                return f(a) + t * (f(b) - f(a))
        return f(rs[-1])

    util = d["util"][g]
    pv = A["provision"]
    under = pv["stockout_cost_per_cup"]["value"] / pv["milk_litres_per_cup"]["value"]
    return {
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
        "critical_ratio": under / (under + pv["milk_waste_cost_per_litre"]["value"]),
        "prov_none": d["provision"]["none"]["optTotal"],
        "prov_def": d["provision"]["def"]["optTotal"],
        "w5_lo": min(w["gapPct"] for w in d["week5"]),
        "w5_hi": max(w["gapPct"] for w in d["week5"]),
    }


def lookup(path: str, simv: dict):
    parts = path.split(".")
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


def render_explainer(s: dict) -> str:
    k = s["key"]
    head = (f'<div class="exhead"><span class="tag">● INTERACTIVE EXPLAINER</span>'
            f'{ed(f"{k}.ex", s["explainer_title"], "span", "ex-title")}</div>')
    cap = ed(f"{k}.cap", s["caption"], "p", "caption") if s.get("caption") else ""
    pn = f'<p class="printonly pnote">{esc(s["printnote"])}</p>'
    if s["widget"] == "where":
        inner = render_where(s)
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


def render_slide(page: int, s: dict) -> str:
    k = s["key"]
    sub = ed(f"{k}.sub", s["sub"], "p", "sub") if s.get("sub") else ""
    if s["widget"] == "benefit":
        grid = (f'<div class="grid g5"><div class="left">{render_explainer(s)}{render_view(s)}</div>'
                f'<div class="right">{render_risks(s)}</div></div>')
    else:
        grid = (f'<div class="grid"><div class="points">{render_points(s)}</div>'
                f'<div class="right">{render_explainer(s)}{render_view(s)}</div></div>')
    return f"""
<section class="slide content {k}" aria-label="Slide {page}" data-kicker="{esc(s['kicker'])}">
  {ed(f"{k}.kicker", s['kicker'], "p", "kicker")}
  {ed(f"{k}.h", s['headline'], "h2")}
  {sub}
  {grid}
  <div class="foot"><span>{esc(FOOT)} · <span class="assume">explainer figures are illustrative assumptions</span></span><span>{page}</span></div>
  <div class="notes"><p class="nk">SPEAKER NOTES</p>{ed(f"{k}.notes", s['notes'], "p")}<p class="src"><b>Sources:</b> {esc(s['sources'])}</p></div>
</section>"""


def build() -> Path:
    data = ensure_data()
    simv = sim_values(data)
    content = [check_and_fill(s, simv, s["key"]) for s in CONTENT]
    slides = render_title() + "".join(render_slide(i + 2, s) for i, s in enumerate(content))
    sim_js = (ROOT / "sim" / "sim.js").read_text(encoding="utf-8")
    page = (TEMPLATE_PATH.read_text(encoding="utf-8")
            .replace("__SLIDES__", slides)
            .replace("__ASSUMPTIONS__", json.dumps(A).replace("</", "<\\/"))
            .replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
            .replace("__SIMJS__", sim_js)
            .replace("__ENGINE__", ENGINE_PATH.read_text(encoding="utf-8")))
    OUT.write_text(page, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({len(CONTENT) + 1} slides)")
    if "--open" in sys.argv:
        webbrowser.open(p.resolve().as_uri())
