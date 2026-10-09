// Tests for store.js (store replica). Run: node --test sim/*.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const Sim = require("./sim.js");
const St = require("./store.js");
const RAW = require("../assumptions.json");
const P = Sim.params(RAW);
const walkBack = RAW.illustration.walk_back_speed.value;
const run = (Q, s, o = {}) => St.run(Sim, Q, s, { walkBack, ...o });
const make = (Q, s, o = {}) => St.create(Sim, Q, s, { walkBack, ...o });
const saturated = (Q, s, wb = walkBack) => {
  const S = St.create(Sim, Q, s, { warm: false, walkBack: wb });
  S.lam = Sim.nominalCap(Sim.plan(Q, s), S.staff) * 3 / 60;
  while (S.t < 4 * 3600) S.step(0.5);
  return { S, thr: S.handed / (S.t / 60), cap: Sim.nominalCap(Sim.plan(Q, s), S.staff) };
};

test("replica: every setup sees the same arrival stream (common random numbers)", () => {
  const a = Sim.SETUPS.map(s => run(P, s).arrived);
  assert.ok(a.every(x => x === a[0]), String(a));
});

test("replica: arrivals match the cost model's peak-hour rate", () => {
  const u = Sim.peakUtilisation(P, P.surgeDefault).all_human.arrivalPerMin * 60;
  const runs = [1, 2, 3, 4, 5, 6, 7, 8].map(k => run(P, "all_machine", { seed: P.seed + k }).arrived);
  const mean = runs.reduce((a, b) => a + b, 0) / runs.length;
  assert.ok(Math.abs(mean - u) / u < 0.1, `${mean} vs ${u}`);
});

test("replica: robots (no walking) reach the cost model's capacity", () => {
  const { thr, cap } = saturated({ ...P, targetWait: 1e9 }, "all_machine");
  assert.ok(Math.abs(thr - cap) / cap < 0.03, `${thr} vs ${cap}`);
});

test("replica: with instant walking, people reach the cost model's capacity; the gap is walking", () => {
  const Q = { ...P, targetWait: 1e9 };
  for (const s of ["all_human", "mixed"]) {
    const instant = saturated(Q, s, 1e6), week5 = saturated(Q, s);
    assert.ok(instant.thr >= instant.cap * 0.97, `${s} instant ${instant.thr} vs ${instant.cap}`);
    assert.ok(week5.thr < instant.thr, `${s}: walking should cost capacity`);
  }
});

test("replica: the brigade keeps Week 5's order, slowest at the order point (nobody passes)", () => {
  const S = make({ ...P, targetWait: 1e9 }, "all_human", { surge: "large" });
  for (let t = 0; t < 1800; t += 0.5) {
    S.step(0.5);
    const w = S.workers.filter(o => o.mode === "work").sort((a, b) => a.i - b.i);
    for (let k = 1; k < w.length; k++) assert.ok(w[k].x >= w[k - 1].x - 1e-9, `t=${S.t}: worker ${w[k].i} behind ${w[k - 1].i}`);
  }
  assert.ok(S.handovers.length > 0);
});

test("replica: staff on shift is the cost model's peak-hour roster", () => {
  for (const s of ["all_human", "mixed"]) {
    const S = make(P, s, { warm: false });
    assert.equal(S.staff, Sim.plan(P, s).rosterPlan[St.peakHour(P)]);
  }
});

test("replica: no robot cup is served faster than the machine seconds allow", () => {
  const r = run(P, "all_machine");
  const min = P.stations.reduce((a, s) => a + P.machineSec[s] * P.machineMult, 0);
  assert.ok(r.times.every(t => t >= min - 0.5), `${Math.min(...r.times)} < ${min}`);
});

test("replica: the balking rule is the cost model's (target wait)", () => {
  const strict = run({ ...P, targetWait: 0.01 }, "all_human", { surge: "large" });
  const loose = run({ ...P, targetWait: 1e9 }, "all_human", { surge: "large" });
  assert.ok(strict.lost > 0 && loose.lost === 0);
  assert.equal(strict.arrived, loose.arrived);
});

test("replica: cups are conserved (ordered = served in time + lost)", () => {
  for (const s of Sim.SETUPS) {
    const r = run(P, s);
    assert.equal(r.times.length + r.lost, r.arrived, s);
  }
});

test("replica: Week 5's lesson - fastest-first serves fewer cups and blocks more than slowest-first", () => {
  const Q = { ...P, targetWait: 1e9 };
  const sat = order => {
    const S = St.create(Sim, Q, "all_human", { warm: false, walkBack, order });
    S.lam = Sim.nominalCap(Sim.plan(Q, "all_human"), S.staff) * 1.5 / 60;
    while (S.t < 4 * 3600) S.step(0.5);
    return { thr: S.handed / S.t, blocked: S.workers.reduce((a, w) => a + w.blockedTime, 0) };
  };
  const slow = sat("slow_first"), fast = sat("fast_first");
  assert.ok(fast.thr < slow.thr, `${fast.thr} vs ${slow.thr}`);
  assert.ok(fast.blocked > slow.blocked, `${fast.blocked} vs ${slow.blocked}`);
});
