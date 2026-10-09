// Tests for mechanism.js (slide 5 illustration). Run: node --test sim/*.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const M = require("./mechanism.js");
const { loadWeek5Brigade } = require("./week5.js");
const RAW = require("../assumptions.json");
const I = RAW.illustration;
const { Brigade, measure } = loadWeek5Brigade();
const speeds = I.worker_speeds.value, walk = I.walk_back_speed.value;

const run = (S, hours, dt = 0.002) => { for (let t = 0; t < hours; t += dt) S.step(dt); return S; };

test("people line: with no arrivals the Week 5 engine is never stepped", () => {
  const S = run(M.peopleLine(Brigade, { speeds, walk, lambda: () => 0 }), 2);
  assert.equal(S.done, 0);
  assert.ok(S.stats.every(w => w.work === 0));
});

test("people line: always-full queue reproduces the Week 5 engine's own throughput (engine untouched)", () => {
  const S = run(M.peopleLine(Brigade, { speeds, walk, lambda: () => 1e6 }), 250);
  const w5 = measure(Brigade, { speeds, walk, hiccup: 0, bufferCap: 0, seed: 7 }).thr;
  assert.ok(Math.abs(S.done / 250 - w5) / w5 < 0.02, `${S.done / 250} vs ${w5}`);
});

test("machine line: saturated output is the slowest station's rate, wherever it sits", () => {
  for (const rates of [[3, 4.5, 6], [4.5, 3, 6], [6, 4.5, 3]]) {
    const S = run(M.machineLine({ rates, buffer: I.machine_buffer_capacity.value, lambda: () => 1e6 }), 100);
    assert.ok(Math.abs(S.done / 100 - 3) / 3 < 0.03, `${rates}: ${S.done / 100}`);
    assert.equal(S.bottleneck(), rates.indexOf(3));
  }
});

test("machine line never beats its slowest station", () => {
  const S = run(M.machineLine({ rates: [5, 2, 7], buffer: 2, lambda: () => 1e6 }), 50);
  assert.ok(S.done / 50 <= 2 + 1e-6);
});

test("under the same surge, people share the load more evenly than fixed machines", () => {
  const lam = M.arrivals(RAW, speeds, "large");
  const P = run(M.peopleLine(Brigade, { speeds, walk, lambda: lam }), I.run_hours.value);
  const Mm = run(M.machineLine({ rates: speeds.map(v => 3 * v), buffer: I.machine_buffer_capacity.value, lambda: lam }), I.run_hours.value);
  const spread = a => Math.max(...a) - Math.min(...a);
  assert.ok(spread(P.utilisation()) < spread(Mm.utilisation()), `${P.utilisation()} vs ${Mm.utilisation()}`);
});

test("illustration arrivals: base is base_load_share of the crew's capacity, surge only inside the window", () => {
  const lam = M.arrivals(RAW, speeds, "large"), [s0, s1] = I.surge_window_hours.value;
  const base = I.base_load_share.value * speeds.reduce((a, b) => a + b, 0);
  assert.equal(lam(s0 - 0.01), base);
  assert.equal(lam((s0 + s1) / 2), base * RAW.surge.surge_multiplier.value.large);
  assert.equal(lam(s1 + 0.01), base);
});

test("same inputs give the same run", () => {
  const lam = M.arrivals(RAW, speeds, "moderate");
  const a = run(M.peopleLine(Brigade, { speeds, walk, lambda: lam }), 1), b = run(M.peopleLine(Brigade, { speeds, walk, lambda: lam }), 1);
  assert.equal(a.done, b.done); assert.deepEqual(a.utilisation(), b.utilisation());
});

// ---------- mixed lane (robots and people together) ----------
const S = require("./sim.js");
const P = S.params(RAW);
const ratios = () => {
  const pu = S.peakUtilisation(P, RAW.surge.surge_default.value);
  return { machine: pu.all_machine.capacityPerMin / pu.mixed.capacityPerMin,
           mixed: S.plan(P, "mixed").machineCap / pu.mixed.capacityPerMin };
};

test("hand share is derived from the station seconds, not typed", () => {
  const st = RAW.stations, h = st.human_seconds_per_cup.value;
  const mach = st.mixed_machine_stations.value.reduce((a, k) => a + h[k], 0);
  const all = Object.values(h).reduce((a, b) => a + b, 0);
  assert.equal(M.handShare(RAW), 1 - mach / all);
});

test("mixed lane: saturated output is capped by the slower of the machine block and the people part", () => {
  const share = M.handShare(RAW), crew = speeds.reduce((a, b) => a + b, 0);
  const people = measure(Brigade, { speeds: speeds.map(v => v / share), walk: walk / share, hiccup: 0, bufferCap: 0, seed: 7 }).thr;
  for (const blockRate of [1, 2 * crew / share]) {
    const L = run(M.mixedLine(Brigade, { speeds, walk, share, blockRate, lambda: () => 1e6 }), 100);
    const want = Math.min(blockRate, people);
    assert.ok(Math.abs(L.done / 100 - want) / want < 0.03, `block ${blockRate}: ${L.done / 100} vs ${want}`);
  }
});

test("mixed lane conserves cups: everything served came through the machine block", () => {
  const L = run(M.mixedLine(Brigade, { speeds, walk, share: 0.5, blockRate: 5, lambda: () => 4 }), 4);
  assert.ok(L.done <= L.M.done);
  assert.ok(L.M.done - L.done <= L.H.backlog + speeds.length);
});

test("lanes: as sized, machines are idle more of the time than when matched (the cost of buying for the peak)", () => {
  const r = ratios(), g = RAW.surge.surge_default.value, hrs = I.run_hours.value;
  const busy = sizing => { const L = M.lanes(Brigade, RAW, { surge: g, sizing, ratios: r });
    run(L.machine, hrs); run(L.mixed, hrs);
    return { machine: Math.max(...L.machine.utilisation()), block: L.mixed.M.utilisation()[0] }; };
  const m = busy("matched"), a = busy("as_sized");
  assert.ok(r.machine > 1 && r.mixed > 1);
  assert.ok(a.machine < m.machine && a.block < m.block, JSON.stringify({ m, a }));
});

test("lanes: under a moderate surge matched machines queue at their slowest station; people do not build that queue", () => {
  const L = M.lanes(Brigade, RAW, { surge: "moderate", sizing: "matched", ratios: ratios() });
  const [s0, s1] = I.surge_window_hours.value;
  let peakP = 0, peakM = 0;
  for (let t = 0; t < s1; t += 0.002) { L.people.step(0.002); L.machine.step(0.002); peakP = Math.max(peakP, L.people.queue()); peakM = Math.max(peakM, L.machine.queue()); }
  assert.ok(peakM > peakP, `machine ${peakM} vs people ${peakP}`);
  assert.equal(L.machine.bottleneck(), speeds.indexOf(Math.min(...speeds)));
});
