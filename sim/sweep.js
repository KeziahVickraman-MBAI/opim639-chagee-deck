// Runs the agreed analyses and writes JSON to sim/out/.
//   node sim/sweep.js util         peak-hour utilisation at the base forecast (user check 4)
//   node sim/sweep.js main         uncertainty sweep for none / moderate / large surge + crossover
//   node sim/sweep.js stability    crossover across seeds (validation.crossover_stability)
//   node sim/sweep.js sensitivity  one-at-a-time low/high on every ranged parameter
// No value is changed in response to results; all settings come from assumptions.json.

const fs = require("node:fs");
const path = require("node:path");
const S = require("./sim.js");

const RAW = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "assumptions.json"), "utf8"));
const P0 = S.params(RAW);
const OUT = path.join(__dirname, "out");
fs.mkdirSync(OUT, { recursive: true });
const save = (name, obj) => fs.writeFileSync(path.join(OUT, name), JSON.stringify(obj, null, 1));
const SURGES = Object.keys(P0.surgeMult);
const DEFAULT_SURGE = RAW.surge.surge_default.value;
const f = (x, d = 2) => (x == null ? "-" : x.toFixed(d));
const pct = x => (x == null ? "-" : (100 * x).toFixed(1) + "%");
const xo = c => (c.kind === "crossover" ? `u = ${pct(c.u)}` : c.kind);

function util() {
  const res = {};
  console.log("PEAK-HOUR UTILISATION at base forecast (arrivals x surge / nominal capacity), plus simulated loss in surge hours");
  console.log("setup        surge     util    arr/min  cap/min  staff  m.units  lost in surge hours");
  for (const g of SURGES) {
    const u = S.peakUtilisation(P0, g), sim = S.runPoint(P0, 0, g, P0.seed, P0.draws);
    res[g] = {};
    for (const s of S.SETUPS) {
      res[g][s] = { ...u[s], peakLostShare: sim[s].peakLostShare };
      console.log(`${s.padEnd(12)} ${g.padEnd(9)} ${pct(u[s].utilisation).padStart(6)}  ${f(u[s].arrivalPerMin).padStart(7)}  ${f(u[s].capacityPerMin).padStart(7)}  ${String(u[s].staff).padStart(5)}  ${String(u[s].machineUnits).padStart(7)}  ${pct(sim[s].peakLostShare).padStart(8)}`);
    }
  }
  save("utilisation.json", res);
}

function main() {
  const res = {};
  for (const g of SURGES) {
    const rows = S.sweep(P0, g);
    const c = S.crossover(rows);
    res[g] = { rows, crossover: c };
    console.log(`\nSURGE = ${g}   crossover (mixed vs all-machine): ${xo(c)}`);
    console.log("   u    | cost/cup  human  mixed  machine | mixed: mach  lab  lost | machine: mach  lab  lost | lost%: hum  mix  mach | machine busy: mix  mach");
    for (const r of rows) {
      const H = r.all_human, M = r.mixed, A = r.all_machine;
      console.log(`${pct(r.u).padStart(6)}  |        ${f(H.costPerCup)}   ${f(M.costPerCup)}   ${f(A.costPerCup)}  |       ${f(M.perCup.machine)} ${f(M.perCup.labour)} ${f(M.perCup.lost)} |         ${f(A.perCup.machine)} ${f(A.perCup.labour)} ${f(A.perCup.lost)} |      ${pct(H.lostShare)} ${pct(M.lostShare)} ${pct(A.lostShare)} |        ${pct(M.machineBusy)} ${pct(A.machineBusy)}`);
    }
  }
  save("sweep.json", res);
}

function stability() {
  const V = RAW.validation.crossover_stability.value, out = [];
  for (let k = 0; k < V.seeds; k++) {
    const c = S.crossover(S.sweep(P0, DEFAULT_SURGE, P0.seed + k));
    out.push({ seed: P0.seed + k, kind: c.kind, u: c.u });
    console.log(`seed ${P0.seed + k}: ${xo(c)}`);
  }
  const us = out.filter(o => o.kind === "crossover").map(o => o.u);
  const spread = us.length ? Math.max(...us) - Math.min(...us) : null;
  const pass = us.length >= V.min_seeds_with_crossover && spread != null && 100 * spread <= V.max_spread_pct_points;
  const kinds = out.reduce((a, o) => ((a[o.kind] = (a[o.kind] || 0) + 1), a), {});
  console.log(`\nSTABILITY (${DEFAULT_SURGE} surge): ${JSON.stringify(kinds)}; crossover spread ${spread == null ? "-" : (100 * spread).toFixed(1) + " pts"}; ${pass ? "PASS" : "FAIL"}`);
  save("stability.json", { surge: DEFAULT_SURGE, criteria: V, seeds: out, spread, pass });
}

// Parameters with a non-null range that feed the slide 4 simulator, and how to set them.
const SENS = {
  "store.cups_per_store_per_year": (P, x) => (P.cupsYear = x),
  "stations.human_seconds_per_cup": (P, x) => (P.humanMult = x),
  "stations.machine_seconds_per_cup": (P, x) => (P.machineMult = x),
  "people.human_speed_variation_cv": (P, x) => (P.humanCv = x),
  "people.worker_speed_spread": (P, x) => (P.spread = x),
  "people.coordination_loss_human": (P, x) => (P.coord = { ...P.coord, all_human: x }),
  "people.coordination_loss_mixed": (P, x) => (P.coord = { ...P.coord, mixed: x }),
  "people.new_staff_share": (P, x) => (P.newShare = x),
  "people.new_staff_relative_speed": (P, x) => (P.newSpeed = x),
  "people.all_machine_attendant_per_open_hour": (P, x) => (P.attendant = x),
  "people.staffing_flexibility": (P, x) => (P.flex = x),
  "costs.labour_cost_per_hour": (P, x) => (P.wage = x),
  "costs.machine_cost_per_unit_per_month": (P, x) => (P.machineMonth = x),
  "costs.lost_order_cost": (P, x) => (P.lostCost = x),
  "costs.capacity_safety_margin": (P, x) => (P.margin = x),
  "service.target_wait_minutes": (P, x) => (P.targetWait = x),
};

function sensitivity() {
  const strong = RAW.demand.uncertainty_strong_signal.value, none = RAW.demand.uncertainty_no_signal.value;
  const gapAt = (rows, u) => { const r = rows.find(r => Math.abs(r.u - u) < 1e-9); return r.mixed.costPerCup - r.all_machine.costPerCup; };
  const base = S.sweep(P0, DEFAULT_SURGE);
  const out = [{ param: "(defaults)", value: null, crossover: S.crossover(base), gapStrong: gapAt(base, strong), gapNone: gapAt(base, none) }];
  console.log(`SENSITIVITY (${DEFAULT_SURGE} surge). gap = mixed - all-machine cost/cup (SGD); negative = mixed cheaper`);
  console.log(`parameter                                    value     crossover                     gap@u=${pct(strong)}  gap@u=${pct(none)}`);
  const line = o => console.log(`${o.param.padEnd(44)} ${String(o.value ?? "").padStart(8)}  ${xo(o.crossover).padEnd(28)}  ${f(o.gapStrong).padStart(9)}  ${f(o.gapNone).padStart(9)}`);
  line(out[0]);
  for (const [key, set] of Object.entries(SENS)) {
    const [sec, k] = key.split(".");
    for (const x of RAW[sec][k].range) {
      const P = { ...P0 }; set(P, x);
      const rows = S.sweep(P, DEFAULT_SURGE);
      const o = { param: key, value: x, crossover: S.crossover(rows), gapStrong: gapAt(rows, strong), gapNone: gapAt(rows, none) };
      out.push(o); line(o);
    }
  }
  save("sensitivity.json", out);
}

const mode = process.argv[2];
({ util, main, stability, sensitivity }[mode] || (() => { console.error("mode: util | main | stability | sensitivity"); process.exit(1); }))();
