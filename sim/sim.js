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
      uNone: v("demand", "uncertainty_no_signal"),
      uStrong: v("demand", "uncertainty_strong_signal"),
      hype: v("demand", "opening_hype_multiplier"),
      milkPerCup: v("provision", "milk_litres_per_cup"),
      wasteCost: v("provision", "milk_waste_cost_per_litre"),
      shelfLife: v("provision", "milk_shelf_life_days"),
      stockoutCost: v("provision", "stockout_cost_per_cup"),
      breakeven: raw.validation.breakeven.value,
      signalDefault: raw.predict.signal_strength_default.value,
      surgeDefault: raw.surge.surge_default.value,
      ranges: {                                  // lever ranges for breakEven(), all from assumptions.json
        u: [raw.demand.uncertainty_sweep.value.from, raw.demand.uncertainty_sweep.value.to],
        wage: raw.costs.labour_cost_per_hour.range,
        machineMonth: raw.costs.machine_cost_per_unit_per_month.range,
        newShare: raw.people.new_staff_share.range,
        machineMult: raw.stations.machine_seconds_per_cup.range,
        cupsPerDay: raw.store.cups_per_store_per_year.range.map(c => c / v("store", "open_days_per_year")),
        cupsPerDayTrigger: raw.triggers.volume_trigger_range_cups_per_day.value,
        milkWaste: raw.provision.milk_waste_cost_per_litre.range,
        coordHuman: raw.people.coordination_loss_human.range,
        coordMixed: raw.people.coordination_loss_mixed.range,
      },
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
    const tr = trace ? { served: [], cap: [], wait: [], accepted: [], lost: [], hour: [] } : null;
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
      const B0 = B;                                          // work already ahead of this minute's orders
      if (deterministic) {
        a = lam;
        if (B / capNom > P.targetWait) l = a; else B += a;
      } else {
        a = poisson(lam, RA());
        for (let k = 0; k < a; k++) { if (B / capNom > P.targetWait) l++; else B += 1; }
      }
      arrivals += a; lost += l;
      if (sh.has(h)) { peakArr += a; peakLost += l; }
      if (tr) { tr.wait.push(B0 / capReal); tr.accepted.push(a - l); tr.lost.push(l); tr.hour.push(h); }   // minutes of work ahead of this minute's orders
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

  /* ---------------- time to serve (read-out of simulateDay; changes no cost result) ----------------
   * For the peak hour (the busiest hourly_demand_share hour) of a base-demand day (m = 1):
   *   time to serve = wait (work already ahead, plus earlier orders that minute, / capacity) + make time,
   *   make time = sum over stations of machine seconds, or human seconds / (coordination x experience).
   * Weighted by the orders accepted each minute; seeds = validation.crossover_stability.seeds. */
  function makeSeconds(P, setup) {
    const m = setup === "all_machine" ? P.stations : setup === "mixed" ? P.mixedMachine : [];
    const exp = expFactor(P);
    return P.stations.reduce((a, s) => a + (m.includes(s) ? P.machineSec[s] * P.machineMult
                                                          : P.humanSec[s] * P.humanMult / (P.coord[setup] * exp)), 0);
  }
  function serveTimes(P, setup, { surge = P.surgeDefault, seeds = 20, seed = P.seed } = {}) {
    const ph = P.share.indexOf(Math.max(...P.share)), make = makeSeconds(P, setup), times = [];
    let arr = 0, lost = 0, served = 0;
    for (let k = 0; k < seeds; k++) {
      const tr = simulateDay(P, setup, { m: 1, surge, seed: hash(seed + k, 9), trace: true }).trace;
      tr.hour.forEach((h, t) => {
        if (h !== ph) return;
        for (let j = 0; j < tr.accepted[t]; j++) times.push((tr.wait[t] + j / tr.cap[t]) * 60 + make);   // j-th order of the minute waits behind j more
        served += tr.served[t]; arr += tr.accepted[t] + tr.lost[t]; lost += tr.lost[t];
      });
    }
    times.sort((a, b) => a - b);
    const q = p => times[Math.min(times.length - 1, Math.floor(p * times.length))];
    return { setup, surge, make, median: q(0.5), p90: q(0.9), servedPerHour: served / seeds, ordersPerHour: arr / seeds,
             lostShare: arr ? lost / arr : 0 };
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

  /* ---------------- slide 2: demand band (weekly cups) ---------------- */
  // signal 0..1 moves u on a straight line from the no-signal to the strong-signal half-width.
  function band(P, signal, removeHype) {
    const u = P.uNone - signal * (P.uNone - P.uStrong);
    const base = 7 * dailyBase(P) * (removeHype ? 1 : P.hype);
    return { u, base, low: base * (1 - u), high: base * (1 + u), width: 2 * u * base, removeHype };
  }

  /* ---------------- slide 3: opening stock (newsvendor on fresh milk) ---------------- */
  // The opening order covers one shelf life; unsold milk expires, unmet cups are stockouts.
  function provision(P, u, days, daily) {
    const ms = drawMultipliers(u, P.draws, P.seed, P);
    const dem = ms.map(m => P.shelfLife * daily * m * P.milkPerCup);                // litres demanded
    const cost = q => {
      let w = 0, s = 0;
      for (const d of dem) { w += Math.max(0, q - d) * P.wasteCost; s += Math.max(0, d - q) / P.milkPerCup * P.stockoutCost; }
      return { waste: w / dem.length, stockout: s / dem.length };
    };
    const under = P.stockoutCost / P.milkPerCup, over = P.wasteCost;                // cost per litre short / spare
    const ratio = under / (under + over);
    const sorted = [...dem].sort((a, b) => a - b);
    const qOpt = sorted[Math.min(sorted.length - 1, Math.ceil(ratio * sorted.length) - 1)];
    const at = cost(days * daily * P.milkPerCup), opt = cost(qOpt);
    return { days, waste: at.waste, stockout: at.stockout, total: at.waste + at.stockout,
             optDays: qOpt / (daily * P.milkPerCup), optWaste: opt.waste, optStockout: opt.stockout,
             optTotal: opt.waste + opt.stockout, criticalRatio: ratio, curve: d => cost(d * daily * P.milkPerCup) };
  }

  /* Linear interpolation of a sweep at any u (slides 4 and 5 read precomputed sweeps). */
  function atU(rows, u, pick) {
    if (u <= rows[0].u) return pick(rows[0]);
    for (let i = 1; i < rows.length; i++) if (u <= rows[i].u) {
      const t = (u - rows[i - 1].u) / (rows[i].u - rows[i - 1].u);
      return pick(rows[i - 1]) + t * (pick(rows[i]) - pick(rows[i - 1]));
    }
    return pick(rows[rows.length - 1]);
  }

  /* ---------------- break-even triggers (brief-v2 section 6) ---------------- */
  // Levers: how each moves the model. "u" is the uncertainty passed to runPoint; the rest set P.
  const LEVERS = {                               // now: the current (default) value, for "how far from the trigger"
    u:            { range: "u",            set: (P, x) => P,                          now: P => defaultU(P) },
    wage:         { range: "wage",         set: (P, x) => ({ ...P, wage: x }),         now: P => P.wage },
    machineMonth: { range: "machineMonth", set: (P, x) => ({ ...P, machineMonth: x }), now: P => P.machineMonth },
    newShare:     { range: "newShare",     set: (P, x) => ({ ...P, newShare: x }),     now: P => P.newShare },
    machineMult:  { range: "machineMult",  set: (P, x) => ({ ...P, machineMult: x }),  now: P => P.machineMult },
    cupsPerDay:   { range: "cupsPerDayTrigger", set: (P, x) => ({ ...P, cupsYear: x * P.days }), now: P => P.cupsYear / P.days },
    coordHuman:   { range: "coordHuman",   set: (P, x) => ({ ...P, coord: { ...P.coord, all_human: x } }), now: P => P.coord.all_human },
    coordMixed:   { range: "coordMixed",   set: (P, x) => ({ ...P, coord: { ...P.coord, mixed: x } }),     now: P => P.coord.mixed },
  };

  // Core: scan a gap function on an even grid, refine every sign change by bisection.
  // gap(x) = cost(a) - cost(b): negative means a is cheaper.
  function breakEvenFn(gap, [lo, hi], tol) {
    const n = tol.grid_points, xs = [...Array(n)].map((_, i) => lo + (hi - lo) * i / (n - 1)), gs = xs.map(gap);
    const width = tol.tol_x_share_of_range * (hi - lo), crossings = [];
    gs.forEach((g, i) => { if (g === 0) crossings.push({ x: xs[i], bracket: [xs[i], xs[i]], gap: 0, step: false, below: null }); });
    for (let i = 0; i < n - 1; i++) {
      if (gs[i] === 0 || gs[i + 1] === 0 || Math.sign(gs[i]) === Math.sign(gs[i + 1])) continue;
      let x0 = xs[i], x1 = xs[i + 1];
      while (x1 - x0 > width) { const m = (x0 + x1) / 2; if (Math.sign(gap(m)) === Math.sign(gs[i])) x0 = m; else x1 = m; }
      const x = (x0 + x1) / 2, g = gap(x);
      crossings.push({ x, bracket: [x0, x1], gap: g, step: Math.abs(g) > tol.tol_cost_sgd_per_cup, below: gs[i] < 0 ? "a" : "b" });
    }
    crossings.sort((p, q) => p.x - q.x);
    if (!crossings.length) return { kind: "none_in_range", range: [lo, hi], cheaper: gs.every(g => g < 0) ? "a" : "b", grid: xs.map((x, i) => [x, gs[i]]) };
    const c = crossings[0];
    return { kind: "value", range: [lo, hi], x: c.x, bracket: c.bracket, step: c.step, gap: c.gap, below: c.below, crossings, grid: xs.map((x, i) => [x, gs[i]]) };
  }

  const defaultU = P => P.uNone - P.signalDefault * (P.uNone - P.uStrong);   // slide 2's default band

  function leverGap(P, lever, a, b, { u = defaultU(P), surge = P.surgeDefault, seed = P.seed, draws = P.draws } = {}) {
    const L = LEVERS[lever];
    return x => {
      const Q = L.set(P, x), r = runPoint(Q, lever === "u" ? x : u, surge, seed, draws);
      return r[a].costPerCup - r[b].costPerCup;
    };
  }

  // Which value of `lever` makes setups a and b cost the same per cup (others at P's values).
  function breakEven(P, lever, a, b, opts = {}) {
    const range = opts.range || P.ranges[LEVERS[lever].range];
    return { lever, a, b, ...breakEvenFn(leverGap(P, lever, a, b, opts), range, P.breakeven) };
  }

  // Slide 4: the milk waste cost at which the best opening order falls to the base forecast.
  // provision() orders at the critical ratio under/(under+over); with a band centred on the base,
  // the order equals the base when the ratio is 1/2, i.e. waste cost per litre = stockout cost per cup / litres per cup.
  function milkTrigger(P) {
    const value = P.stockoutCost / P.milkPerCup, [lo, hi] = P.ranges.milkWaste;
    return { kind: value >= lo && value <= hi ? "value" : "none_in_range", value, range: [lo, hi],
             stockoutCost: P.stockoutCost, milkPerCup: P.milkPerCup };
  }

  const api = { defaultU, LEVERS, breakEvenFn, leverGap, breakEven, milkTrigger, band, provision, atU, SETUPS, params, rng, hash, normInv, poisson, dailyBase, drawMultipliers, surgeHourSet,
                brigadeRate, workerSpeeds, plan, nominalCap, simulateDay, runPoint, uGrid, sweep, crossover,
                peakUtilisation, makeSeconds, serveTimes };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ChageeSim = api;
})(typeof window !== "undefined" ? window : globalThis);
