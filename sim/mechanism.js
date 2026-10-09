/* mechanism.js - slide 5 illustration: how a counter absorbs a surge.
 *
 * Pure functions, no UI. Runs in Node (require) and the browser (window.ChageeMechanism).
 * Mechanism only: the cost model (sim.js) uses pooled speeds, not these lines.
 *
 *   peopleLine(Brigade, cfg)  the Week 5 bucket-brigade engine, passed in read-only,
 *                             wrapped with an arrival stream: the line works while an
 *                             order is waiting and pauses when none is.
 *   machineLine(cfg)          fixed-rate stations in series with small buffers; an order
 *                             cannot be handed back or taken over, so the slowest station
 *                             sets the pace wherever it sits.
 *   mixedLine(Brigade, cfg)   robots and people together: the machine steps as one fixed-rate
 *                             block, feeding a people brigade that pools the hand steps.
 *   arrivals(RAW, speeds, g)  orders per hour over a run: base load plus a surge window,
 *                             all from assumptions.json "illustration" and "surge".
 *   handShare(RAW)            share of a cup's work left to people in the mixed counter
 *                             (human seconds on non-machine stations / all human seconds).
 *   lanes(Brigade, RAW, o)    the three lanes for one surge and sizing, ready to step.
 * Units are Week 5's: speed 1 = one full line (one order) per hour.
 */
(function (root) {
  "use strict";

  function arrivals(RAW, speeds, surge) {
    const I = RAW.illustration, [s0, s1] = I.surge_window_hours.value;
    const base = I.base_load_share.value * speeds.reduce((a, b) => a + b, 0);
    const mult = RAW.surge.surge_multiplier.value[surge];
    return t => (t >= s0 && t < s1 ? base * mult : base);
  }

  function feed(S, lambda, dt) {                 // deterministic arrivals: whole orders only
    S.acc += lambda(S.t) * dt;
    const k = Math.floor(S.acc);
    S.acc -= k; S.arrived += k;
    return k;
  }

  function peopleLine(Brigade, { speeds, walk, lambda }) {
    const inner = Brigade({ speeds, walk, hiccup: 0, bufferCap: 0, seed: 7 });
    const W = inner.W, n = speeds.length;
    const S = { t: 0, done: 0, arrived: 0, backlog: 0, acc: 0, W, handovers: [],
                stats: speeds.map(() => ({ work: 0, blocked: 0, walk: 0, idle: 0 })) };
    S.step = dt => {
      S.backlog += feed(S, lambda, dt);
      S.t += dt;
      if (S.backlog < 1) { S.stats.forEach(st => (st.idle += dt)); return; }   // nothing to make: the line waits
      const prev = W.map(w => w.mode), before = inner.done;
      inner.step(dt);
      const c = inner.done - before;
      S.done += c; S.backlog = Math.max(0, S.backlog - c);
      for (let i = 1; i < n; i++)
        if (prev[i] === "back" && W[i].mode === "work" && prev[i - 1] === "work" && W[i - 1].mode === "back")
          S.handovers.push({ t: S.t, pair: i, x: W[i].x });
      W.forEach((w, i) => { const st = S.stats[i];
        if (w.mode === "back") st.walk += dt; else if (w.blocked) st.blocked += dt; else st.work += dt; });
    };
    S.inLine = () => W.filter(w => w.mode === "work").length;
    S.queue = () => Math.max(0, S.backlog - S.inLine());
    S.utilisation = () => S.stats.map(st => (S.t ? st.work / S.t : 0));
    S.handoverPoints = since => [...Array(n - 1)].map((_, k) => {     // mean handover position per pair
      const h = S.handovers.filter(o => o.pair === k + 1 && o.t >= since);
      return h.length ? h.reduce((a, o) => a + o.x, 0) / h.length : null;
    });
    return S;
  }

  function machineLine({ rates, buffer, lambda }) {
    const n = rates.length;
    const st = rates.map(r => ({ r, has: false, p: 0, busy: 0, blocked: 0, starved: 0 }));
    const buf = Array(n - 1).fill(0);
    const S = { t: 0, done: 0, arrived: 0, inQueue: 0, acc: 0, st, buf };
    S.step = dt => {
      S.inQueue += feed(S, lambda, dt);
      S.t += dt;
      for (let i = n - 1; i >= 0; i--) {             // downstream first, so space frees before upstream passes on
        const s = st[i];
        if (s.has) {
          if (s.p < 1) { s.p += s.r * dt; s.busy += dt; } else s.blocked += dt;
          if (s.p >= 1) {
            if (i === n - 1) { S.done++; s.has = false; }
            else if (buf[i] < buffer) { buf[i]++; s.has = false; }
          }
        }
        if (!s.has) {
          const ready = i === 0 ? S.inQueue > 0 : buf[i - 1] > 0;
          if (ready) { if (i === 0) S.inQueue--; else buf[i - 1]--; s.has = true; s.p = 0; } else s.starved += dt;
        }
      }
    };
    S.queue = () => S.inQueue + buf.reduce((a, b) => a + b, 0);
    S.utilisation = () => st.map(s => (S.t ? s.busy / S.t : 0));
    S.bottleneck = () => { const u = S.utilisation(); return u.indexOf(Math.max(...u)); };
    return S;
  }

  function mixedLine(Brigade, { speeds, walk, share, blockRate, lambda }) {
    const M = machineLine({ rates: [blockRate], buffer: 0, lambda });
    // people do only `share` of each cup, so in Week 5 units (one line = one cup's hand steps) they move 1/share faster
    const H = peopleLine(Brigade, { speeds: speeds.map(v => v / share), walk: walk / share, lambda: () => 0 });
    const S = { t: 0, M, H, share };
    S.step = dt => {
      const before = M.done;
      M.step(dt);
      H.backlog += M.done - before;               // cups leave the machine block and wait for hands
      H.step(dt); S.t += dt;
    };
    Object.defineProperty(S, "done", { get: () => H.done });
    S.queue = () => M.queue() + H.queue();
    S.utilisation = () => [...M.utilisation(), ...H.utilisation()];
    S.bottleneck = () => (M.queue() >= H.queue() ? "machine" : "people");
    return S;
  }

  function handShare(RAW) {
    const st = RAW.stations, h = st.human_seconds_per_cup.value, m = new Set(st.mixed_machine_stations.value);
    const all = st.list.value.reduce((a, k) => a + h[k], 0);
    return st.list.value.filter(k => !m.has(k)).reduce((a, k) => a + h[k], 0) / all;
  }

  // ratios: { machine, mixed } as-sized multipliers read from sim/ (see illustration.machine_sizing, .mixed_sizing)
  function lanes(Brigade, RAW, { surge, sizing, ratios }) {
    const I = RAW.illustration, speeds = I.worker_speeds.value, walk = I.walk_back_speed.value;
    const lambda = arrivals(RAW, speeds, surge), share = handShare(RAW), k = sizing === "as_sized";
    const crew = speeds.reduce((a, b) => a + b, 0);
    return {
      people: peopleLine(Brigade, { speeds, walk, lambda }),
      mixed: mixedLine(Brigade, { speeds, walk, share, blockRate: (crew / share) * (k ? ratios.mixed : 1), lambda }),
      machine: machineLine({ rates: speeds.map(v => 3 * v * (k ? ratios.machine : 1)),
                             buffer: I.machine_buffer_capacity.value, lambda }),
    };
  }

  const api = { arrivals, peopleLine, machineLine, mixedLine, handShare, lanes };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ChageeMechanism = api;
})(typeof window !== "undefined" ? window : globalThis);
