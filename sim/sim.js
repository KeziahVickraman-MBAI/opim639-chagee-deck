/* sim.js - pooled-speed counter simulator for the Chagee deck.
 *
 * Pure functions, no UI. Runs in Node (require) and in the browser (window.ChageeSim).
 * Every number comes from assumptions.json via params(); nothing is hard-coded here
 * except unit conversions (60 s/min, 12 months/year).
 *
 * Model (approved):
 *   1. A store's true demand = forecast base x m, with m = max(floor, 1 + u z / z80),
 *      so u is the half-width of the 80% band as a share of base (slide 2's output).
 *   2. Each setup is sized before opening with the same rule: forecast peak x safety margin.
 *      Machines round up to whole units per station and are never adjusted.
 *      Staff rosters (per open hour) are planned on the forecast, then move a share
 *      `staffing_flexibility` of the way to what the true demand needs.
 *   3. One trading day, minute by minute. Poisson arrivals (surge on the busiest hours).
 *      Capacity: all-human = pooled bucket-brigade rate; all-machine = slowest station;
 *      mixed = min(machine stations, pooled human rate on the other stations).
 *      An arriving order balks (is lost) if the expected wait, backlog / nominal capacity,
 *      exceeds the target wait.
 *   4. Cost per cup = (machine + labour + lost-order cost) / cups served, summed over
 *      stores before dividing (ratio of sums).
 */
(function (root) {
  "use strict";

  const SETUPS = ["all_human", "mixed", "all_machine"];

  /* ---------------- assumptions.json -> flat parameter object ---------------- */
  function params(raw) {
    const v = (sec, key) => raw[sec][key].value;
    return {
      hours: v("store", "open_hours_per_day"),
      days: v("store", "open_days_per_year"),
      cupsYear: v("store", "cups_per_store_per_year"),
      share: v("store", "hourly_demand_share"),
      coverage: v("demand", "band_coverage"),
      floor: v("demand", "demand_floor_share_of_base"),
      sweepU: v("demand", "uncertainty_sweep"),
      surgeMult: v("surge", "surge_multiplier"),
      surgeHours: v("surge", "surge_hours"),
      stations: v("stations", "list"),
      humanSec: v("stations", "human_seconds_per_cup"),
      machineSec: v("stations", "machine_seconds_per_cup"),
      humanMult: 1, machineMult: 1,              // sensitivity multipliers on station times
      mixedMachine: v("stations", "mixed_machine_stations"),
      humanCv: v("people", "human_speed_variation_cv"),
      spread: v("people", "worker_speed_spread"),
      coord: { all_human: v("people", "coordination_loss_human"), mixed: v("people", "coordination_loss_mixed") },
      newShare: v("people", "new_staff_share"),
      newSpeed: v("people", "new_staff_relative_speed"),
      minStaff: v("people", "min_staff_on_shift"),
      attendant: v("people", "all_machine_attendant_per_open_hour"),
      flex: v("people", "staffing_flexibility"),
      wage: v("costs", "labour_cost_per_hour"),
      machineMonth: v("costs", "machine_cost_per_unit_per_month"),
      lostCost: v("costs", "lost_order_cost"),
      margin: v("costs", "capacity_safety_margin"),
      targetWait: v("service", "target_wait_minutes"),
      draws: v("simulation", "monte_carlo_draws"),
      seed: v("simulation", "base_seed"),
    };
  }

  /* ---------------- random numbers ---------------- */
  function rng(seed) {                         // mulberry32, as in the Week 5 engine
    let s = seed | 0;
    return () => {
      s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hash(...xs) {                       // stable integer from several integers
    let h = 2166136261;
    for (const x of xs) { h ^= x | 0; h = Math.imul(h, 16777619); h ^= h >>> 13; }
    return h | 0;
  }
  function normal(R) {                         // Box-Muller
    let u = 0; while (u === 0) u = R();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * R());
  }
  function normInv(p) {                        // Acklam's approximation, |error| < 1.2e-9
    const a = [-39.6968302866538, 220.946098424521, -275.928510446969, 138.357751867269, -30.6647980661472, 2.50662827745924];
    const b = [-54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857];
    const c = [-0.00778489400243029, -0.322396458041136, -2.40075827716184, -2.54973253934373, 4.37466414146497, 2.93816398269878];
    const d = [0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742];
    const lo = 0.02425;
    if (p < lo) { const q = Math.sqrt(-2 * Math.log(p));
      return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
    if (p > 1 - lo) return -normInv(1 - p);
    const q = p - 0.5, r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  function poisson(lambda, u) {                // inverse CDF: same u -> monotone in lambda
    let p = Math.exp(-lambda), F = p, k = 0;
    while (u > F && k < 1000) { k++; p *= lambda / k; F += p; }
    return k;
  }

  /* ---------------- demand ---------------- */
  const dailyBase = P => P.cupsYear / P.days;

  function drawMultipliers(u, n, seed, P) {
    const zc = normInv(0.5 + P.coverage / 2), floor = P.floor;
    const R = rng(hash(seed, 1));
    const out = [];
    for (let i = 0; i < n; i++) { const z = normal(R); out.push(Math.max(floor, 1 + u * z / zc)); }
    return out;
  }

  function surgeHourSet(P) {
    return new Set(P.share.map((s, h) => [s, h]).sort((x, y) => y[0] - x[0] || x[1] - y[1])
      .slice(0, P.surgeHours).map(x => x[1]));
  }

  /* ---------------- capacity ---------------- */
  // Bucket brigade, pooled: team rate = sum of worker speeds x coordination loss (Week 5 result).
  const brigadeRate = (speeds, coord) => speeds.reduce((a, b) => a + b, 0) * coord;

  const workerSpeeds = (n, spread) =>
    n <= 1 ? (n === 1 ? [1] : []) : Array.from({ length: n }, (_, i) => 1 - spread + 2 * spread * i / (n - 1));

  const expFactor = P => 1 - P.newShare * (1 - P.newSpeed);

  function plan(P, setup) {
    const base = dailyBase(P), rate = P.share.map(s => base * s / 60);          // forecast cups/min by hour
    const R = Math.max(...rate) * P.margin;
    const mStations = setup === "all_machine" ? P.stations : setup === "mixed" ? P.mixedMachine : [];
    const hStations = setup === "all_machine" ? [] : P.stations.filter(s => !mStations.includes(s));
    let machineUnits = 0, machineCap = Infinity;
    for (const s of mStations) {
      const sec = P.machineSec[s] * P.machineMult;
      const units = Math.max(1, Math.ceil(R * sec / 60 - 1e-9));
      machineUnits += units; machineCap = Math.min(machineCap, units * 60 / sec);
    }
    const W = hStations.reduce((a, s) => a + P.humanSec[s] * P.humanMult, 0);   // human seconds per cup
    const perWorker = W > 0 ? (60 / W) * P.coord[setup] * expFactor(P) : 0;      // cups/min, average worker
    const minStaff = P.minStaff[setup];
    const need = m => rate.map(r => Math.max(minStaff, perWorker > 0 ? Math.ceil(r * m * P.margin / perWorker - 1e-9) : 0));
    const rosterPlan = setup === "all_machine" ? rate.map(() => 0) : need(1);
    const roster = m => setup === "all_machine" ? rosterPlan
      : need(m).map((n, h) => Math.max(minStaff, Math.round(rosterPlan[h] + P.flex * (n - rosterPlan[h]))));
    return { setup, machineUnits, machineCap, W, perWorker, rosterPlan, roster, rate };
  }

  function nominalCap(pl, n) {
    if (pl.setup === "all_machine") return pl.machineCap;
    const human = brigadeRate(Array(n).fill(1), 1) * pl.perWorker;
    return pl.setup === "mixed" ? Math.min(pl.machineCap, human) : human;
  }

  /* ---------------- one trading day ---------------- */
  function simulateDay(P, setup, { m = 1, surge = "none", seed = 1, deterministic = false, trace = false } = {}) {
    const pl = plan(P, setup), roster = pl.roster(m), sh = surgeHourSet(P), mult = P.surgeMult[surge];
    const base = dailyBase(P), RA = rng(hash(seed, 2));
    let B = 0, arrivals = 0, served = 0, lost = 0, peakArr = 0, peakLost = 0;
    const tr = trace ? { served: [], cap: [] } : null;
    for (let t = 0; t < P.hours * 60; t++) {
      const h = Math.floor(t / 60), n = roster[h];
      const lam = base * P.share[h] * m * (sh.has(h) ? mult : 1) / 60;
      const capNom = nominalCap(pl, n);
      let capReal = capNom;
      if (!deterministic && setup !== "all_machine") {
        const sp = workerSpeeds(n, P.spread);
        let sum = 0;
        for (let i = 0; i < n; i++) {                       // noise keyed by (seed, minute, worker): shared across setups
          const z = normal(rng(hash(seed, 3, t, i)));
          sum += sp[i] * Math.max(0, 1 + P.humanCv * z);
        }
        const human = brigadeRate([sum], 1) * pl.perWorker;
        capReal = setup === "mixed" ? Math.min(pl.machineCap, human) : human;
      }
      let a, l = 0;
      if (deterministic) {
        a = lam;
        if (B / capNom > P.targetWait) l = a; else B += a;
      } else {
        a = poisson(lam, RA());
        for (let k = 0; k < a; k++) { if (B / capNom > P.targetWait) l++; else B += 1; }
      }
      arrivals += a; lost += l;
      if (sh.has(h)) { peakArr += a; peakLost += l; }
      const s = Math.min(B, capReal); B -= s; served += s;
      if (tr) { tr.served.push(s); tr.cap.push(capReal); }
    }
    served += B;                                             // backlog at close is finished after hours
    const labourHours = setup === "all_machine" ? P.attendant * P.hours : roster.reduce((x, y) => x + y, 0);
    const cost = {
      machine: pl.machineUnits * P.machineMonth * 12 / P.days,
      labour: labourHours * P.wage,
      lost: lost * P.lostCost,
    };
    const machineBusy = pl.machineUnits ? served / (pl.machineCap * P.hours * 60) : null;
    return { setup, m, arrivals, served, lost, peakArr, peakLost, labourHours, machineUnits: pl.machineUnits,
             machineCap: pl.machineCap, machineBusy, cost, trace: tr };
  }

  /* ---------------- Monte Carlo over stores ---------------- */
  function runPoint(P, u, surge, seed, draws) {
    const ms = drawMultipliers(u, draws, seed, P);
    const out = { u, surge };
    for (const s of SETUPS) {
      const acc = { arrivals: 0, served: 0, lost: 0, peakArr: 0, peakLost: 0, labourHours: 0,
                    machine: 0, labour: 0, lostCost: 0, machineBusy: 0 };
      ms.forEach((m, i) => {
        const r = simulateDay(P, s, { m, surge, seed: hash(seed, 4, i) });
        acc.arrivals += r.arrivals; acc.served += r.served; acc.lost += r.lost;
        acc.peakArr += r.peakArr; acc.peakLost += r.peakLost; acc.labourHours += r.labourHours;
        acc.machine += r.cost.machine; acc.labour += r.cost.labour; acc.lostCost += r.cost.lost;
        acc.machineBusy += r.machineBusy || 0;
      });
      const total = acc.machine + acc.labour + acc.lostCost;
      out[s] = {
        arrivals: acc.arrivals, served: acc.served, lost: acc.lost,
        costPerCup: total / acc.served,
        perCup: { machine: acc.machine / acc.served, labour: acc.labour / acc.served, lost: acc.lostCost / acc.served },
        lostShare: acc.arrivals ? acc.lost / acc.arrivals : 0,
        peakLostShare: acc.peakArr ? acc.peakLost / acc.peakArr : 0,
        cupsPerDay: acc.served / draws,
        labourHoursPerDay: acc.labourHours / draws,
        machineBusy: s === "all_human" ? null : acc.machineBusy / draws,
      };
    }
    return out;
  }

  function uGrid(P) {
    const { from, to, step } = P.sweepU, g = [];
    for (let k = 0; from + k * step <= to + 1e-9; k++) g.push(+(from + k * step).toFixed(10));
    return g;
  }

  const sweep = (P, surge, seed = P.seed, draws = P.draws) => uGrid(P).map(u => runPoint(P, u, surge, seed, draws));

  /* Pre-registered rule (assumptions.json validation.crossover_definition). */
  function crossover(rows) {
    const d = rows.map(r => r.mixed.costPerCup - r.all_machine.costPerCup);
    let i = d.length;
    while (i > 0 && d[i - 1] <= 0) i--;
    if (i === d.length) return { kind: d.some(x => x <= 0) ? "reverse" : "machine_cheaper_everywhere", u: null, d };
    if (i === 0) return { kind: "mixed_cheaper_everywhere", u: null, d };
    const u0 = rows[i - 1].u, u1 = rows[i].u;
    return { kind: "crossover", u: u0 + (0 - d[i - 1]) / (d[i] - d[i - 1]) * (u1 - u0), d };
  }

  /* User check (4): peak-hour load vs nominal capacity at the base forecast. */
  function peakUtilisation(P, surge) {
    const sh = surgeHourSet(P), mult = P.surgeMult[surge], out = {};
    for (const s of SETUPS) {
      const pl = plan(P, s), roster = pl.roster(1);
      let worst = 0, at = null;
      for (const h of sh) {
        const u = pl.rate[h] * mult / nominalCap(pl, roster[h]);
        if (u > worst) { worst = u; at = h; }
      }
      out[s] = { utilisation: worst, hour: at, capacityPerMin: nominalCap(pl, roster[at]),
                 arrivalPerMin: pl.rate[at] * mult, staff: roster[at], machineUnits: pl.machineUnits };
    }
    return out;
  }

  const api = { SETUPS, params, rng, hash, normInv, poisson, dailyBase, drawMultipliers, surgeHourSet,
                brigadeRate, workerSpeeds, plan, nominalCap, simulateDay, runPoint, uGrid, sweep, crossover,
                peakUtilisation };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ChageeSim = api;
})(typeof window !== "undefined" ? window : globalThis);
