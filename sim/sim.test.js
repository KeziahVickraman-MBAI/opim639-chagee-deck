// Tests for sim.js. Run: node --test sim/
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
