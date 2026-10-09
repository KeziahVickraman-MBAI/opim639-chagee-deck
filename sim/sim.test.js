// Tests for sim.js. Run: node --test sim/*.test.js
// Written before sim.js; tolerances and pass rules come from assumptions.json "validation".

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");
const S = require("./sim.js");
const { loadWeek5Brigade } = require("./week5.js");

const RAW = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "assumptions.json"), "utf8"));
const P = S.params(RAW);
const SETUPS = ["all_human", "mixed", "all_machine"];

// ---------------------------------------------------------------- 1. Week 5 cross-check
test("pooled brigade rate is within the fixed tolerance of the Week 5 engine (walk = 40)", () => {
  const V = RAW.validation.week5_comparison.value;
  const { Brigade, measure } = loadWeek5Brigade();
  for (const speeds of V.speed_sets) {
    const w5 = measure(Brigade, { speeds, walk: V.settings.walk, hiccup: 0, bufferCap: 0, seed: 7 }).thr;
    const pooled = S.brigadeRate(speeds, 1.0);
    const gapPct = 100 * Math.abs(pooled - w5) / w5;
    console.log(`  week5 speeds ${speeds.join(",")}: engine ${w5.toFixed(3)}, pooled ${pooled.toFixed(3)}, gap ${gapPct.toFixed(2)}%`);
    assert.ok(gapPct <= V.tolerance_pct, `gap ${gapPct.toFixed(2)}% > ${V.tolerance_pct}%`);
  }
});

test("Week 5 at walk = 6 is reported as a calibration point (information only)", () => {
  const { Brigade, measure } = loadWeek5Brigade();
  for (const speeds of RAW.validation.week5_comparison.value.speed_sets) {
    const w5 = measure(Brigade, { speeds, walk: 6, hiccup: 0, bufferCap: 0, seed: 7 }).thr;
    console.log(`  INFO walk=6 speeds ${speeds.join(",")}: engine/pooled = ${(w5 / S.brigadeRate(speeds, 1)).toFixed(3)}`);
  }
});

test("pooled rate ignores how speed is spread across workers (the rebalancing assumption)", () => {
  assert.equal(S.brigadeRate([1, 1, 1], 1), S.brigadeRate([0.6, 1.0, 1.4], 1));
  assert.equal(S.brigadeRate([1, 1], 0.9), 1.8);
});

// ---------------------------------------------------------------- 2. machine bottleneck
test("all-machine never serves more per minute than its slowest station allows", () => {
  const plan = S.plan(P, "all_machine");
  const cap = plan.machineCap;                             // cups per minute
  const r = S.simulateDay(P, "all_machine", { m: 3, surge: "large", seed: 1, trace: true });
  const maxServed = Math.max(...r.trace.served);
  assert.ok(maxServed <= cap + 1e-9, `served ${maxServed} > cap ${cap}`);
});

// ---------------------------------------------------------------- 3. no losses below capacity
test("deterministic demand below capacity loses no orders, in every setup", () => {
  for (const s of SETUPS) {
    const r = S.simulateDay(P, s, { m: 1, surge: "none", seed: 1, deterministic: true });
    assert.equal(r.lost, 0, `${s} lost ${r.lost}`);
    assert.ok(Math.abs(r.served - S.dailyBase(P)) < 1e-6, `${s} served ${r.served}`);
  }
});

// ---------------------------------------------------------------- 4. surge monotonicity
test("a bigger surge never loses fewer orders (same seeds)", () => {
  for (const s of SETUPS) {
    const lost = ["none", "moderate", "large"].map(g => S.runPoint(P, 0.3, g, 11, 100)[s].lost);
    assert.ok(lost[0] <= lost[1] && lost[1] <= lost[2], `${s}: ${lost.join(" > ")}`);
  }
});

// ---------------------------------------------------------------- 5. zero uncertainty
test("at u = 0 every draw is the base forecast", () => {
  const r = S.drawMultipliers(0, 50, 639, P);
  assert.ok(r.every(m => m === 1));
});

test("u = 0, no surge: each setup serves its planned volume (losses only from random noise, < 0.5%)", () => {
  const pt = S.runPoint(P, 0, "none", 639, 100);
  for (const s of SETUPS) {
    const share = pt[s].lost / pt[s].arrivals;
    assert.ok(share < 0.005, `${s} lost ${(100 * share).toFixed(2)}%`);
  }
});

// ---------------------------------------------------------------- demand floor
test("demand draws are floored at zero, never negative", () => {
  const r = S.drawMultipliers(0.6, 5000, 1, P);
  assert.ok(Math.min(...r) >= 0);
  assert.ok(r.some(m => m === 0), "expected some floored draws at u = 0.6");
});

test("uncertainty u is the 80% band half-width: about 10% of draws above 1 + u", () => {
  const r = S.drawMultipliers(0.3, 20000, 3, P);
  const above = r.filter(m => m > 1.3).length / r.length;
  assert.ok(Math.abs(above - 0.10) < 0.01, `share above high = ${above}`);
});

// ---------------------------------------------------------------- 6. reproducibility
test("same seed gives identical results", () => {
  const a = S.runPoint(P, 0.4, "moderate", 42, 50), b = S.runPoint(P, 0.4, "moderate", 42, 50);
  assert.deepEqual(a, b);
});

// ---------------------------------------------------------------- slide 2: demand band
test("signal strength maps linearly between the approved band end points", () => {
  assert.ok(Math.abs(S.band(P, 0, true).u - RAW.demand.uncertainty_no_signal.value) < 1e-12);
  assert.ok(Math.abs(S.band(P, 1, true).u - RAW.demand.uncertainty_strong_signal.value) < 1e-12);
  const b = S.band(P, 0.5, true);
  assert.ok(Math.abs(b.high - b.low - 2 * b.u * b.base) < 1e-9);
  assert.ok(Math.abs(b.base - 7 * S.dailyBase(P)) < 1e-9, "weekly base");
});

test("keeping opening hype in scales the band by the hype multiplier", () => {
  const off = S.band(P, 0.5, true), on = S.band(P, 0.5, false);
  assert.ok(Math.abs(on.base / off.base - RAW.demand.opening_hype_multiplier.value) < 1e-9);
});

// ---------------------------------------------------------------- slide 3: opening stock
test("with no uncertainty the cost-minimising stock is one shelf life and costs nothing", () => {
  const r = S.provision(P, 0, 3, S.dailyBase(P));
  assert.ok(Math.abs(r.optDays - RAW.provision.milk_shelf_life_days.value) < 1e-9);
  assert.ok(r.optTotal < 1e-9);
});

test("a wider band never makes the best opening-stock decision cheaper", () => {
  const c = [0, 0.15, 0.3, 0.5].map(u => S.provision(P, u, 3, S.dailyBase(P)).optTotal);
  for (let i = 1; i < c.length; i++) assert.ok(c[i] >= c[i - 1] - 1e-9, c.join(" > "));
});

test("expected cost at the optimum is no higher than at any slider position", () => {
  for (const d of [1, 3, 7, 10, 14]) {
    const r = S.provision(P, 0.3, d, S.dailyBase(P));
    assert.ok(r.optTotal <= r.total + 1e-6, `days ${d}: ${r.optTotal} > ${r.total}`);
  }
});

// ---------------------------------------------------------------- crossover rule
test("crossover follows the pre-registered definition", () => {
  const u = [0, 0.1, 0.2, 0.3];
  const mk = d => d.map((x, i) => ({ u: u[i], mixed: { costPerCup: 1 + x }, all_machine: { costPerCup: 1 } }));
  assert.equal(S.crossover(mk([0.2, 0.1, -0.1, -0.2])).kind, "crossover");
  assert.ok(Math.abs(S.crossover(mk([0.2, 0.1, -0.1, -0.2])).u - 0.15) < 1e-9);
  assert.equal(S.crossover(mk([-0.1, -0.1, -0.1, -0.1])).kind, "mixed_cheaper_everywhere");
  assert.equal(S.crossover(mk([0.1, 0.1, 0.1, 0.1])).kind, "machine_cheaper_everywhere");
  assert.equal(S.crossover(mk([-0.1, 0.1, 0.2, 0.3])).kind, "reverse");          // mixed wins only at low u
  assert.equal(S.crossover(mk([0.1, -0.1, 0.1, -0.1])).kind, "crossover");        // last sign change counts
});

// ---------------------------------------------------------------- breakEven (brief-v2 section 6)
const BE = RAW.validation.breakeven.value;

test("breakEven core: a smooth crossing is found inside the range and the gap is ~0 there", () => {
  const r = S.breakEvenFn(x => x - 3.3, [0, 10], BE);
  assert.equal(r.kind, "value");
  assert.ok(r.x >= 0 && r.x <= 10);
  assert.ok(Math.abs(r.x - 3.3) <= BE.tol_x_share_of_range * 10);
  assert.equal(r.step, false);
});

test("breakEven core: a jump is returned as a 'step' with a narrow bracket and a sign change", () => {
  const g = x => (x < 2.5 ? -0.2 : 0.2);
  const r = S.breakEvenFn(g, [0, 10], BE);
  assert.equal(r.kind, "value");
  assert.equal(r.step, true);
  assert.ok(r.bracket[1] - r.bracket[0] <= BE.tol_x_share_of_range * 10 + 1e-12);
  assert.ok(Math.sign(g(r.bracket[0])) !== Math.sign(g(r.bracket[1])));
});

test("breakEven core: no sign change gives none_in_range and names the cheaper side", () => {
  assert.deepEqual(
    (({ kind, cheaper }) => ({ kind, cheaper }))(S.breakEvenFn(x => -1 - x, [0, 10], BE)),
    { kind: "none_in_range", cheaper: "a" });
  assert.equal(S.breakEvenFn(x => 1 + x, [0, 10], BE).cheaper, "b");
});

test("breakEven core: every crossing is listed, the first is primary", () => {
  const r = S.breakEvenFn(x => Math.sin(x), [0.5, 7], BE);
  assert.equal(r.crossings.length, 2);
  assert.ok(Math.abs(r.x - Math.PI) < 0.05);
});

test("breakEven on the simulator: wage, all-human vs mixed, passes the pre-registered rule", () => {
  const P = { ...S.params(RAW), draws: 100 };
  const r = S.breakEven(P, "wage", "all_human", "mixed");
  const [lo, hi] = P.ranges.wage;
  if (r.kind === "none_in_range") return;
  assert.ok(r.x >= lo && r.x <= hi);
  const g = S.leverGap(P, "wage", "all_human", "mixed");
  const equal = Math.abs(g(r.x)) <= BE.tol_cost_sgd_per_cup;
  const stepOk = r.bracket[1] - r.bracket[0] <= BE.tol_x_share_of_range * (hi - lo) + 1e-9 &&
                 Math.sign(g(r.bracket[0])) !== Math.sign(g(r.bracket[1]));
  assert.ok(equal || stepOk, `gap ${g(r.x)} at ${r.x}`);
  assert.equal(r.step, !equal);
});

test("every lever's range comes from assumptions.json", () => {
  const P = S.params(RAW);
  assert.deepEqual(P.ranges.wage, RAW.costs.labour_cost_per_hour.range);
  assert.deepEqual(P.ranges.cupsPerDayTrigger, RAW.triggers.volume_trigger_range_cups_per_day.value);
  assert.deepEqual(P.ranges.cupsPerDay, RAW.store.cups_per_store_per_year.range.map(c => c / RAW.store.open_days_per_year.value));
});

// ---------------------------------------------------------------- slide 4 trigger: milk cost
test("milk trigger: at the returned waste cost per litre the best order equals the base forecast", () => {
  const P = S.params(RAW), daily = S.dailyBase(P), t = S.milkTrigger(P, 0.325, daily);
  assert.ok(Math.abs(t.value - P.stockoutCost / P.milkPerCup) < 1e-9, "unit conversion");
  const r = S.provision({ ...P, wasteCost: t.value }, 0.325, 3, daily);
  assert.ok(Math.abs(r.optDays - P.shelfLife) / P.shelfLife < 0.01, `optDays ${r.optDays}`);
  const inRange = t.value >= P.ranges.milkWaste[0] && t.value <= P.ranges.milkWaste[1];
  assert.equal(t.kind, inRange ? "value" : "none_in_range");
});

// ---------- time to serve (read-out; must not change any cost result) ----------
test("serveTimes: tracing a day changes none of its results", () => {
  const P = S.params(RAW);
  for (const s of S.SETUPS) {
    const a = S.simulateDay(P, s, { surge: "moderate", seed: 3 }), b = S.simulateDay(P, s, { surge: "moderate", seed: 3, trace: true });
    assert.deepEqual({ ...a, trace: null }, { ...b, trace: null });
  }
});

test("serveTimes: no cup is faster than its make time, and the robot counter loses no orders in the peak", () => {
  const P = S.params(RAW);
  for (const s of S.SETUPS) {
    const r = S.serveTimes(P, s, { surge: "moderate", seeds: 5 });
    assert.ok(r.median >= r.make - 1e-9 && r.p90 >= r.median, s);
  }
  assert.equal(S.serveTimes(P, "all_machine", { surge: "moderate", seeds: 5 }).lostShare, 0);
});
