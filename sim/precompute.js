// Precomputes everything the deck needs from the simulator and writes one JSON file.
//   node sim/precompute.js <out.json>
// Slide 4's sweeps are too slow to run live in the browser, so they are computed here
// (same code, same seeds) and embedded; slides 2, 3 and 5 compute live from sim.js.

const fs = require("node:fs");
const path = require("node:path");
const S = require("./sim.js");
const { loadWeek5Brigade } = require("./week5.js");

const RAW = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "assumptions.json"), "utf8"));
const P0 = S.params(RAW);
const out = process.argv[2];
if (!out) { console.error("usage: node sim/precompute.js <out.json>"); process.exit(1); }

const trim = rows => rows.map(r => {
  const o = { u: r.u };
  for (const s of S.SETUPS) {
    const x = r[s];
    o[s] = { cost: x.costPerCup, machine: x.perCup.machine, labour: x.perCup.labour, lost: x.perCup.lost,
             lostShare: x.lostShare, busy: x.machineBusy };
  }
  return o;
});
const run = (P, g) => { const rows = S.sweep(P, g); return { rows: trim(rows), crossover: (({ kind, u }) => ({ kind, u }))(S.crossover(rows)) }; };

const t0 = Date.now();
const data = { generated: new Date().toISOString(), sweeps: {}, util: {}, shift: {} };

for (const g of Object.keys(P0.surgeMult)) {
  data.sweeps[g] = run(P0, g);
  const u = S.peakUtilisation(P0, g), sim = S.runPoint(P0, 0, g, P0.seed, P0.draws);
  data.util[g] = Object.fromEntries(S.SETUPS.map(s => [s, { ...u[s], peakLostShare: sim[s].peakLostShare }]));
}

// "What could shift the balance": the approved low/high ends, moderate surge.
const SHIFT = {
  machine_cost: ["costs", "machine_cost_per_unit_per_month", (P, x) => (P.machineMonth = x)],
  staff_turnover: ["people", "new_staff_share", (P, x) => (P.newShare = x)],
};
const surge0 = RAW.surge.surge_default.value;
for (const [k, [sec, key, set]] of Object.entries(SHIFT)) {
  const [lo, hi] = RAW[sec][key].range;
  const withValue = x => { const P = { ...P0 }; set(P, x); return P; };
  data.shift[k] = { param: `${sec}.${key}`, surge: surge0, low: lo, high: hi,
    lowRun: run(withValue(lo), surge0), highRun: run(withValue(hi), surge0) };
}

// Multi-seed stability (validation.crossover_stability), default surge.
const V = RAW.validation.crossover_stability.value, kinds = {}, us = [];
for (let k = 0; k < V.seeds; k++) {
  const c = S.crossover(S.sweep(P0, surge0, P0.seed + k));
  kinds[c.kind] = (kinds[c.kind] || 0) + 1; if (c.kind === "crossover") us.push(c.u);
}
const spread = us.length ? Math.max(...us) - Math.min(...us) : null;
data.stability = { surge: surge0, seeds: V.seeds, kinds, spread,
  pass: us.length >= V.min_seeds_with_crossover && spread != null && 100 * spread <= V.max_spread_pct_points };

// Week 5 cross-check, as run by the tests.
const W = RAW.validation.week5_comparison.value, { Brigade, measure } = loadWeek5Brigade();
data.week5 = W.speed_sets.map(speeds => {
  const eng = measure(Brigade, { speeds, walk: W.settings.walk, hiccup: 0, bufferCap: 0, seed: 7 }).thr;
  const eng6 = measure(Brigade, { speeds, walk: 6, hiccup: 0, bufferCap: 0, seed: 7 }).thr;
  const pooled = S.brigadeRate(speeds, 1);
  return { speeds, engine: eng, pooled, gapPct: 100 * Math.abs(pooled - eng) / eng, ratioWalk6: eng6 / pooled };
});
data.week5Pass = data.week5.every(w => w.gapPct <= W.tolerance_pct);

// Slide 2 default band and slide 3 headline figures (same functions the slides run live).
const sig = RAW.predict.signal_strength_default.value, noHype = RAW.predict_toggles.remove_hype_default.value;
const b0 = S.band(P0, sig, noHype), daily = b0.base / 7, days0 = RAW.provision.opening_stock_days.value;
const prov = u => S.provision(P0, u, days0, daily);
data.defaults = { signal: sig, removeHype: noHype, u: b0.u, band: b0 };
data.provision = { none: prov(P0.uNone), def: prov(b0.u), strong: prov(P0.uStrong) };
for (const k in data.provision) delete data.provision[k].curve;

fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(data));
console.log(`precompute: wrote ${out} in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
