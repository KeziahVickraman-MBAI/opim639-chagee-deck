r"""
build_opim639_deck.py  -  OPIM639 Week 5 (Group 3) as an interactive slide deck.

    python build_opim639_deck.py          # writes opim639_explainer.html
    python build_opim639_deck.py --open   # ...and opens it

Three 16:9 slides (1280 x 720, scaled to fit the window, F for full screen):

  1  Title slide
  2  Option 1 (buffer)    normal brigade vs. buffer before the busy section;
                          sliders for buffer size, busy-section speed, hiccups
  3  Option 2 (circling)  normal brigade vs. circling (no overtaking /
                          overtaking); a speed slider per worker

Every number in the explainer panels comes from running the simulation, so
moving a slider rebuilds the result. Formulas are rendered with MathJax.

Edit CONTENT (text) or SIM (default parameters) below; the JS engine is in
TEMPLATE.
"""

from __future__ import annotations

import html
import json
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "opim639_explainer.html"
esc = html.escape

TITLE = dict(
    course="OPIM639",
    subtitle="Week 5 Discussion Assignment",
    group="Group 3",
    members=["Ayumi Liow", "Jin Ong", "Keziah", "Revan"],
)

# ---------------------------------------------------------------------------
# Simulation defaults (units: 1 line length; speed 1 = one full line per hour)
# ---------------------------------------------------------------------------
SIM = {
    "option1": {
        "speeds": [1.0, 1.5, 2.0],     # slowest to fastest, upstream to downstream
        "walk": 6.0,                   # walk-back speed, lines per hour
        "busyFrom": 0.62, "busyTo": 0.90,
        "busyFactor": 0.35,            # share of normal pick speed inside the busy section
                                       # (the busy section also holds one picker at a time)
        "bufferAt": 0.62,
        "bufferCap": 4,
        "hiccup": 0.0,                 # random stalls per worker per hour
    },
    "option2": {
        "speeds": [1.0, 2.0, 3.0],
        "walk": 40.0,                  # near-instant walk back, as the lecture assumes
        "crowd": 0.6,                  # speed factor when carts share the aisle (overtaking)
    },
}

# ---------------------------------------------------------------------------
# Slide content (from OPIM639_Group_3_Week_5_Discussion_Assignment_1.pptx)
# ---------------------------------------------------------------------------
ICONS = {
    "layers": '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 12.5l9 5 9-5"/><path d="M3 17l9 5 9-5"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.3"/>',
    "bars": '<path d="M6 20v-8"/><path d="M12 20V5"/><path d="M18 20v-5"/>',
    "grid": '<rect x="4" y="4" width="6.5" height="6.5" rx="1"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1"/>'
            '<rect x="4" y="13.5" width="6.5" height="6.5" rx="1"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/>'
             '<path d="M16 4.5a3.5 3.5 0 010 7"/><path d="M18 14c2.2.6 3.5 2.8 3.5 6"/>',
    "cycle": '<path d="M20 11a8 8 0 00-14.3-4.9L4 8"/><path d="M4 4v4h4"/>'
             '<path d="M4 13a8 8 0 0014.3 4.9L20 16"/><path d="M20 20v-4h-4"/>',
    "map": '<path d="M9 4L3 6.5V20l6-2.5 6 2.5 6-2.5V4l-6 2.5L9 4z"/><path d="M9 4v13.5"/><path d="M15 6.5V20"/>',
    "alert": '<path d="M12 3.5L2.5 20h19L12 3.5z"/><path d="M12 10v4.5"/><path d="M12 17.3v.4"/>',
}

CONTENT = [
    dict(
        num=1,
        nav="Option 1 · Buffer",
        quote="Allow a blocked worker to drop his incomplete job in a buffer before the busy section and walk back",
        headline="A buffer gives some short-term or visual relief, but weakens what makes bucket brigades work",
        verdict="Small or temporary benefit at best. The bottleneck is still there",
        verdict_kind="amber",
        widget="buffer",
        explainer_title="Impact of Option 1 to the Line",
        caption=("Workers on either side meet less often. Handovers happen at the buffer instead of wherever "
                 "the work is, so the automatic balancing has less room to work."),
        conclusion=("A buffer can reduce short term blocking, but it does not remove the downstream bottleneck, "
                    "it increases work in progress, and it weakens the pull and self balancing mechanism. If "
                    "blocking keeps happening, we would first look at the worker order and how popular items are "
                    "spread along the line before adding a buffer."),
        points=[
            ("layers", "It gives up the pull system advantage, increasing WIP inventory",
             "Bucket brigades keep unfinished work under control because nothing moves without a handover. A "
             "buffer lets half done orders queue on the floor. That means slower order response, extra lifting "
             "and setting down, more floor space, and one more thing to manage."),
            ("target", "It covers up the problem instead of fixing it",
             "The lecture taught us that slowest to fastest sequencing lets the line balance itself, but it "
             "assumes even work along the line, steady speeds, instant walk back and no overtaking. In practice, "
             "blocking can come from uneven work, varying speeds, a cluster of popular items or the wrong worker "
             "order. A buffer covers the symptom to make the situation look better, without showing which cause "
             "to fix."),
            ("bars", "Output is still capped by the busy section",
             "Workers at the front can pick faster, but orders only leave the line as fast as the worker at the "
             "busy section can clear them. The buffer fills up, and then blocking comes back. The only real gain "
             "is smoothing out random hiccups like a slow pick or a stuck tote, and that is a small and temporary "
             "effect."),
            ("grid", "It weakens the self balancing mechanism",
             "A buffer separates the work before it from the work after it, so workers no longer meet and hand "
             "over as dynamically. With fewer live handovers, the automatic balancing that the bucket brigade is "
             "known for has less chance to act, and the line can drift out of balance from one order to the next."),
        ],
    ),
    dict(
        num=2,
        nav="Option 2 · Circling",
        quote="Allow the workers to circle through the order-picking line",
        headline=("If workers circle without taking over one another\u2019s jobs, the workload can no longer "
                  "rebalance itself and system becomes less efficient"),
        verdict="Likely worse. Faster workers can get trapped behind slower ones",
        verdict_kind="red",
        widget="circle",
        explainer_title="Same 3 workers, two ways to run the line",
        caption="Output can fall by half with the same three people on the line.",
        conclusion=("Likely worse if circling removes the backward handovers, because those handovers redistribute "
                    "work and let the line balance itself. If workers keep their own orders on a loop with no "
                    "overtaking, faster workers can get trapped behind slower ones and output falls."),
        points=[
            ("users", "There is a jam where faster workers get trapped",
             "Slowest to fastest works on a straight line with a start and an end. On a loop with no overtaking, "
             "a faster worker can end up behind the slowest and cannot get past. Team output then falls toward "
             "the slowest speed times the number of workers. With speeds 1, 2 and 3, that is 3 orders an hour "
             "instead of 6."),
            ("cycle", "Without handovers, the line loses its self-balancing",
             "A brigade balances because each handover point drifts toward the worker who can do more. If "
             "circling means each worker keeps their own order all the way round, work is no longer shared out, "
             "and the line has a harder time adjusting to a slow day, a new hire or a section full of popular "
             "items."),
            ("map", "More walking per order, for every worker",
             "Walking is the most time-consuming part of picking. In a brigade each worker covers a short "
             "stretch repeatedly and gets to know it well. In a loop, every worker walks the whole line for every "
             "order and needs to know where every item is. Efficiency is lost."),
            ("alert", "Letting workers overtake does not save it",
             "If faster workers can overtake, the aisles get crowded with carts, and we end up with a group of "
             "people each picking whole orders on their own. There is no sharing of work and no control over "
             "half done orders."),
        ],
    ),
]


ENGINE = r"""
/* ================= simulation engines ================= */
function rng(seed){ return ()=>{ seed=seed+0x6D2B79F5|0; let t=Math.imul(seed^seed>>>15,1|seed);
  t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; }; }

/* Straight bucket brigade. Worker 0 is upstream (nearest Start). */
function Brigade(c){
  const n=c.speeds.length, R=rng(c.seed||7), GAP=0.03, cap=c.bufferCap||0;
  const W=c.speeds.map((v,i)=>({v,x:i/n*0.9,mode:"work",stall:0,blocked:false,work:0}));
  const S={W,buffer:[],t:0,done:0,handovers:0,pickups:0,drops:0,blockedTime:0,wipArea:0,log:[]};
  const busyMult=x=>(c.busyFactor!=null && x>=c.busyFrom && x<c.busyTo)?c.busyFactor:1;
  S.reset=()=>{S.t=0;S.done=0;S.handovers=0;S.pickups=0;S.drops=0;S.blockedTime=0;S.wipArea=0;S.log=[];W.forEach(w=>w.work=0);};
  S.step=dt=>{
    S.t+=dt;
    for(let i=n-1;i>=0;i--){
      const w=W[i]; w.blocked=false;
      if(w.mode==="work"){
        if(w.stall>0){w.stall-=dt;continue;}
        if(c.hiccup && R()<c.hiccup*dt){w.stall=0.08;continue;}
        let nx=w.x+w.v*busyMult(w.x)*dt;
        const a=W[i+1];
        if(a && a.mode==="work" && a.x>=w.x && nx>a.x-GAP){ nx=Math.max(w.x,a.x-GAP); }
        // busy section holds one picker at a time: wait at its entrance while someone is picking inside
        // (with a buffer, orders already waiting in it go first, so nobody walks past a full buffer)
        if(c.busyFactor!=null && w.x<c.busyFrom && nx>=c.busyFrom &&
           ((cap>0 && i<n-1 && S.buffer.length>0) ||
            W.some((o,j)=>j!==i && o.mode==="work" && o.x>=c.busyFrom && o.x<c.busyTo))){ nx=Math.max(w.x,c.busyFrom-1e-4); }
        if(nx<=w.x+1e-9) w.blocked=true;
        if(w.blocked){
          S.blockedTime+=dt;
          if(cap>0 && i<n-1 && S.buffer.length<cap && w.x>=c.bufferAt-0.12 && w.x<=c.bufferAt+1e-6){
            S.buffer.push(w.x); S.drops++; w.mode="back";
          }
          continue;
        }
        w.work+=nx-w.x; w.x=nx;
        if(w.x>=1){ w.x=1; S.done++; S.log.push(S.t); w.mode="back"; }
      }else{
        const nx=w.x-c.walk*dt;
        if(cap>0 && i===n-1 && S.buffer.length && nx<=c.bufferAt){ w.x=S.buffer.shift(); w.mode="work"; S.pickups++; continue; }
        if(i>0){ const u=W[i-1]; if(u.mode==="work" && nx<=u.x){ w.x=u.x; w.mode="work"; w.stall=0; u.mode="back"; S.handovers++; continue; } }
        if(nx<=0){ w.x=0; w.mode="work"; continue; }
        w.x=nx;
      }
    }
    let wip=S.buffer.length; for(const w of W) if(w.mode==="work") wip++;
    S.wipArea+=wip*dt;
  };
  S.wip=()=>S.buffer.length+W.filter(w=>w.mode==="work").length;
  return S;
}

/* Workers circling a loop, each carrying their own order the whole way round. */
function Loop(c){
  const n=c.speeds.length, GAP=0.06;
  const W=c.speeds.map((v,i)=>({v,p:(n-1-i)/n,work:0,slowed:false}));
  const S={W,t:0,done:0,handovers:0,log:[],wipArea:0};
  S.reset=()=>{S.t=0;S.done=0;S.log=[];S.wipArea=0;W.forEach(w=>w.work=0);};
  S.step=dt=>{
    S.t+=dt;
    const old=W.map(w=>w.p);
    W.forEach((w,i)=>{
      let np;
      if(c.overtake){
        const crowded=W.some((o,j)=>{ if(j===i)return false; let d=Math.abs(((old[j]-old[i])%1+1.5)%1-0.5); return d<GAP; });
        w.slowed=crowded; np=old[i]+w.v*dt*(crowded?c.crowd:1);
      }else{
        let ahead=Infinity;                           // nearest worker in front, unwrapped
        W.forEach((o,j)=>{ if(j===i)return; let q=old[j]; while(q<=old[i])q+=1; ahead=Math.min(ahead,q); });
        np=Math.min(old[i]+w.v*dt, ahead-GAP); np=Math.max(np,old[i]);
        w.slowed=np<old[i]+w.v*dt-1e-9;
      }
      w.work+=np-old[i];
      if(Math.floor(np)>Math.floor(old[i])){ S.done++; S.log.push(S.t); }
      w.p=np;
    });
    S.wipArea+=n*dt;
  };
  S.wip=()=>n;
  return S;
}

/* Run a model headless and report steady-state numbers. */
function measure(make, cfg, warm=25, hours=250, dt=0.002){
  const S=make(cfg);
  for(let t=0;t<warm;t+=dt) S.step(dt);
  S.reset();
  let blockedSum=0, bufSum=0, steps=0;
  for(let t=0;t<hours;t+=dt){ S.step(dt); steps++; if(S.buffer) bufSum+=S.buffer.length; }
  const thr=S.done/hours, wip=S.wipArea/hours;
  return { thr, wip, flow: thr>0? wip/thr : Infinity, hand:S.handovers/hours,
           blocked: S.blockedTime!=null ? S.blockedTime/(hours*cfg.speeds.length) : 0,
           buf: steps? bufSum/steps:0, share: S.W.map(w=>S.done? w.work/S.done : 0) };
}

/* ================= drawing helpers ================= */
const COL=["#2563eb","#b93a3a","#23272f"];
function setupCanvas(cv,h){
  const dpr=(window.devicePixelRatio||1)*Math.max(1,SCALE), w=cv.clientWidth||460;
  cv.width=w*dpr; cv.height=h*dpr; cv.style.height=h+"px";
  const g=cv.getContext("2d"); g.setTransform(dpr,0,0,dpr,0,0); return {g,w,h};
}
function workerDot(g,x,y,i,label,{blocked=false,back=false,carrying=true}={}){
  g.globalAlpha=back?0.45:1;
  if(carrying && !back){ g.fillStyle="#e8a33d"; g.fillRect(x-6,y-24,12,9); }
  g.beginPath(); g.arc(x,y,10,0,Math.PI*2); g.fillStyle=COL[i%3]; g.fill();
  if(blocked){ g.lineWidth=3; g.strokeStyle="#b93a3a"; g.beginPath(); g.arc(x,y,14,0,Math.PI*2); g.stroke(); }
  g.fillStyle="#fff"; g.font="bold 11px Calibri,Carlito,sans-serif"; g.textAlign="center"; g.textBaseline="middle"; g.fillText(label,x,y+0.5);
  g.globalAlpha=1;
}
function lineAxis(g,x0,x1,y){
  g.strokeStyle="#23272f"; g.lineWidth=2; g.beginPath(); g.moveTo(x0,y); g.lineTo(x1,y); g.stroke();
  g.beginPath(); g.moveTo(x1+8,y); g.lineTo(x1,y-5); g.lineTo(x1,y+5); g.fill();
  g.fillStyle="#6b7280"; g.font="13px Calibri,Carlito,sans-serif"; g.textBaseline="middle";
  g.textAlign="right"; g.fillText("Start",x0-8,y); g.textAlign="left"; g.fillText("End",x1+14,y);
}
const fmt=(v,d=2)=>Number.isFinite(v)?v.toFixed(d):"–";
function delta(v,base,goodWhenUp,d=2){
  const df=v-base; if(Math.abs(df)<Math.pow(10,-d)/2) return `<span class="d same">same</span>`;
  const good= goodWhenUp? df>0 : df<0;
  return `<span class="d ${good?"down":"up"}">${df>0?"+":""}${df.toFixed(d)}</span>`;
}

/* ================= Option 1 widget ================= */
function bufferWidget(root){
  const D=SIM.option1;
  const st={variant:"buffer",cap:D.bufferCap,busy:D.busyFactor,hic:D.hiccup,playing:!matchMedia("(prefers-reduced-motion: reduce)").matches};
  root.querySelector(".body").innerHTML=`
    <div class="ex-grid">
      <div><canvas height="210"></canvas>
        <div class="controls">
          <div class="variants"><button data-v="normal">Normal bucket brigade</button><button data-v="buffer">Option 1: buffer</button></div>
          <label for="o1cap" class="capl">Buffer size</label><div class="rng capr"><input id="o1cap" type="range" min="1" max="10" step="1" value="${st.cap}"><span class="val cap"></span></div>
          <label for="o1busy">Busy section speed</label><div class="rng"><input id="o1busy" type="range" min="0.15" max="1" step="0.05" value="${st.busy}"><span class="val busy"></span></div>
          <label for="o1hic">Random hiccups</label><div class="rng"><input id="o1hic" type="range" min="0" max="3" step="0.25" value="${st.hic}"><span class="val hic"></span></div>
          <div class="playbar"><button class="play"></button><button class="restart">Restart</button><span>1 s ≈ 15 min of picking</span></div>
        </div>
      </div>
      <div class="panel"></div>
    </div>`;
  const cv=root.querySelector("canvas"), panel=root.querySelector(".panel");
  let S, res, base;
  const cfg=v=>({...D, busyFactor:st.busy, hiccup:st.hic, bufferCap: v==="buffer"? st.cap:0, seed:11});
  function rebuild(){
    root.querySelectorAll(".variants button").forEach(b=>b.classList.toggle("on",b.dataset.v===st.variant));
    root.querySelector(".cap").textContent=st.variant==="buffer"? `${st.cap} orders`:"none";
    root.querySelector(".capl").classList.toggle("off",st.variant!=="buffer");
    root.querySelector(".capr").classList.toggle("off",st.variant!=="buffer");
    root.querySelector("#o1cap").disabled=st.variant!=="buffer";
    root.querySelector(".busy").textContent=Math.round(st.busy*100)+"%";
    root.querySelector(".hic").textContent=st.hic? st.hic+"/hr":"none";
    base=measure(Brigade,cfg("normal")); res=st.variant==="buffer"? measure(Brigade,cfg("buffer")) : base;
    S=Brigade(cfg(st.variant));
    const isB=st.variant==="buffer";
    panel.innerHTML=`
      <h4>STEADY STATE · 250 SIMULATED HOURS</h4>
      <div class="big">${fmt(res.thr)} <span style="font-size:14px;font-weight:400">orders/hr</span></div>
      <div class="stat"><span>vs. normal brigade</span>${isB?delta(res.thr,base.thr,true):'<span class="d same">baseline</span>'}</div>
      <hr>
      <div class="stat"><span>Orders in progress (WIP)</span><span><b>${fmt(res.wip,1)}</b> ${isB?delta(res.wip,base.wip,false,1):""}</span></div>
      <div class="stat"><span>…of which in the buffer</span><b>${fmt(res.buf,1)}</b></div>
      <div class="stat"><span>Live handovers per hour</span><span><b>${fmt(res.hand,1)}</b> ${isB?delta(res.hand,base.hand,true,1):""}</span></div>
      <div class="stat"><span>Time spent blocked</span><span><b>${Math.round(res.blocked*100)}%</b></span></div>
      <hr>
      <h4>LITTLE'S LAW</h4>
      <p>\\[ \\text{flow time} = \\frac{\\text{WIP}}{\\text{output}} = \\frac{${fmt(res.wip,1)}}{${fmt(res.thr)}} \\]</p>
      <div class="stat"><span>= time an order spends on the line</span><b>${Math.round(res.flow*60)} min</b></div>
      <p class="note">${isB
        ? (res.thr-base.thr>0.05 ? "Output rises a little, mostly from absorbing hiccups, while WIP and flow time go up."
           : res.thr-base.thr<-0.05 ? "Output falls: handovers now happen at the buffer, so the fastest worker clears the busy section alone and the line stops balancing itself. Half done orders pile up."
           : "The busy section still sets the pace: output barely moves, but more orders sit half done.")
        : "Handovers happen wherever the workers meet, so the busy section is shared out."}</p>`;
    root.querySelector(".status").textContent=`${isB?"buffer of "+st.cap:"no buffer"} · ${fmt(res.thr)} orders/hr · WIP ${fmt(res.wip,1)}`;
    typeset(panel);
  }
  function draw(){
    const {g,w,h}=setupCanvas(cv,210), x0=46, x1=w-40, y=140, X=p=>x0+p*(x1-x0);
    g.clearRect(0,0,w,h);
    g.fillStyle="#fbe9d0"; g.fillRect(X(D.busyFrom),y-112,X(D.busyTo)-X(D.busyFrom),140);
    g.fillStyle="#9a6b1e"; g.font="13px Calibri,Carlito,sans-serif"; g.textAlign="center"; g.textBaseline="middle";
    g.fillText("Busy section",(X(D.busyFrom)+X(D.busyTo))/2,y-98);
    g.font="12px Calibri,Carlito,sans-serif";
    const zc=(X(D.busyFrom)+X(D.busyTo))/2; g.fillText("1 picker at a time",zc,y-83); g.fillText(`${Math.round(st.busy*100)}% speed`,zc,y-69);
    lineAxis(g,x0,x1,y);
    if(st.variant==="buffer"){
      const sw=12, bx=X(D.bufferAt)-8, top=y-48;
      for(let k=0;k<st.cap;k++){
        const sx=bx-(k+1)*sw;
        g.strokeStyle="#e8a33d"; g.setLineDash([3,2]); g.strokeRect(sx,top,sw-3,20); g.setLineDash([]);
        if(k<S.buffer.length){ g.fillStyle="#e8a33d"; g.fillRect(sx+2,top+2,sw-7,16); }
      }
      g.fillStyle="#9a6b1e"; g.textAlign="right"; g.font="12px Calibri,Carlito,sans-serif";
      g.fillText(`Buffer ${S.buffer.length}/${st.cap}`,bx,top-10);
    }
    S.W.forEach((wk,i)=>workerDot(g,X(wk.x),y,i,String(wk.v),{blocked:wk.blocked,back:wk.mode==="back"}));
    g.fillStyle="#23272f"; g.font="bold 12px Calibri,Carlito,sans-serif"; g.textAlign="left"; g.textBaseline="middle";
    g.fillText(`${S.done} orders out · ${fmt(S.t,1)} h`,10,14);
    g.textAlign="left"; g.fillStyle="#6b7280"; g.font="12px Calibri,Carlito,sans-serif";
    g.fillText("Numbers = worker speed. Tote = order in hand; faded = walking back; red ring = blocked.",10,h-10);
  }
  let last=null;
  function frame(ts){
    if(last!=null && st.playing && slides[cur].contains(root)){ const dt=Math.min(0.05,(ts-last)/1000)*0.25; for(let k=0;k<10;k++) S.step(dt/10); }
    last=ts; draw(); requestAnimationFrame(frame);
  }
  const playBtn=root.querySelector(".play"); const setPlay=()=>playBtn.textContent=st.playing?"Pause":"Play";
  playBtn.onclick=()=>{st.playing=!st.playing;setPlay();};
  root.querySelector(".restart").onclick=()=>{S=Brigade(cfg(st.variant));};
  root.querySelectorAll(".variants button").forEach(b=>b.onclick=()=>{st.variant=b.dataset.v;rebuild();});
  root.querySelector("#o1cap").oninput=e=>{st.cap=+e.target.value;rebuild();};
  root.querySelector("#o1busy").oninput=e=>{st.busy=+e.target.value;rebuild();};
  root.querySelector("#o1hic").oninput=e=>{st.hic=+e.target.value;rebuild();};
  setPlay(); rebuild(); requestAnimationFrame(frame);
}

/* ================= Option 2 widget ================= */
function circleWidget(root){
  const D=SIM.option2;
  const st={variant:"loop",v:[...D.speeds],crowd:D.crowd,playing:!matchMedia("(prefers-reduced-motion: reduce)").matches};
  root.querySelector(".body").innerHTML=`
    <div class="ex-grid">
      <div><canvas height="200"></canvas>
        <div class="controls">
          <div class="variants"><button data-v="line">Normal brigade</button><button data-v="loop">Circling, no overtaking</button><button data-v="overtake">Circling, overtaking</button></div>
          ${[0,1,2].map(i=>`<label for="o2v${i}">Worker ${i+1} speed</label><div class="rng"><input id="o2v${i}" type="range" min="0.5" max="4" step="0.5" value="${st.v[i]}"><span class="val v${i}"></span></div>`).join("")}
          <label for="o2crowd" class="crl">Aisle crowding</label><div class="rng crr"><input id="o2crowd" type="range" min="0.3" max="1" step="0.05" value="${D.crowd}"><span class="val crowd"></span></div>
          <div class="playbar"><button class="play"></button><button class="restart">Restart</button><span>Speed = orders/hr picking the whole line alone</span></div>
        </div>
      </div>
      <div class="panel"></div>
    </div>`;
  const cv=root.querySelector("canvas"), panel=root.querySelector(".panel");
  let S, res, base;
  const make=v=> v==="line"? Brigade : Loop;
  const cfg=v=>({speeds:[...st.v], walk:D.walk, crowd:st.crowd, overtake:v==="overtake", seed:5});
  function rebuild(){
    root.querySelectorAll(".variants button").forEach(b=>b.classList.toggle("on",b.dataset.v===st.variant));
    st.v.forEach((v,i)=>root.querySelector(".v"+i).textContent=v+"/hr");
    const ov=st.variant==="overtake";
    root.querySelector(".crowd").textContent=`${Math.round(st.crowd*100)}% speed`;
    root.querySelector(".crl").classList.toggle("off",!ov); root.querySelector(".crr").classList.toggle("off",!ov);
    root.querySelector("#o2crowd").disabled=!ov;
    base=measure(Brigade,cfg("line")); res=st.variant==="line"? base : measure(make(st.variant),cfg(st.variant));
    S=make(st.variant)(cfg(st.variant));
    const [a,b,c]=st.v, sum=a+b+c, mn=Math.min(a,b,c);
    const formula={
      line:`\\[ v_1+v_2+v_3 = ${a}+${b}+${c} = ${fmt(sum,1)} \\]`,
      loop:`\\[ 3\\times\\min(v_1,v_2,v_3) = 3\\times${mn} = ${fmt(3*mn,1)} \\]`,
      overtake:`\\[ \\approx (v_1+v_2+v_3)\\times\\text{crowding} \\le ${fmt(sum,1)} \\]`}[st.variant];
    const pct=Math.round(100*res.thr/base.thr);
    const sorted=a<=b && b<=c;
    panel.innerHTML=`
      <h4>WHAT THE LECTURE PREDICTS</h4>
      <p>${formula}</p>
      <h4>WHAT THE SIMULATION GETS</h4>
      <div class="big">${fmt(res.thr,1)} <span style="font-size:14px;font-weight:400">orders/hr</span></div>
      <div class="stat"><span>vs. normal brigade (${fmt(base.thr,1)})</span><b>${pct}%</b></div>
      <hr>
      <div class="stat"><span>Live handovers per hour</span><b>${fmt(res.hand,1)}</b></div>
      <h4 style="margin-top:6px">SHARE OF EACH ORDER PICKED</h4>
      ${res.share.map((s,i)=>`<div class="stat"><span style="color:${COL[i]}">Worker ${i+1}</span><b>${st.variant==="line"?Math.round(s*100)+"%":"100% of own"}</b></div>`).join("")}
      <p class="note">${st.variant==="line"
        ? (sorted ? "Handover points drift toward the faster workers, so each covers a short stretch."
                  : "Workers are not slowest to fastest, so a faster worker gets blocked and output drops.")
        : st.variant==="loop" ? "Faster workers end up stuck behind the slowest one, and every worker walks the whole line."
        : "Output can recover, but everyone picks whole orders alone: no sharing of work, and passing in the aisle slows both carts."}</p>`;
    root.querySelector(".status").textContent=`${{line:"straight line",loop:"loop, no overtaking",overtake:"loop, overtaking"}[st.variant]} · ${fmt(res.thr,1)} orders/hr`;
    root.querySelector(".caption").textContent= st.variant==="line"
      ? "Spread out, hand over, walk back: team output is the sum of the speeds."
      : `Output is ${pct}% of the normal brigade with the same three people on the line.`;
    typeset(panel);
  }
  function draw(){
    const {g,w,h}=setupCanvas(cv,200); g.clearRect(0,0,w,h);
    if(st.variant==="line"){
      const x0=46,x1=w-40,y=106,X=p=>x0+p*(x1-x0);
      lineAxis(g,x0,x1,y);
      S.W.forEach((wk,i)=>workerDot(g,X(wk.x),y,i,String(st.v[i]),{blocked:wk.blocked,back:wk.mode==="back"}));
    }else{
      const cx=w/2, cy=h/2+4, rx=Math.min(w*0.40,300), ry=70;
      g.strokeStyle="#23272f"; g.lineWidth=2; g.beginPath(); g.ellipse(cx,cy,rx,ry,0,0,Math.PI*2); g.stroke();
      g.fillStyle="#6b7280"; g.font="13px Calibri,Carlito,sans-serif"; g.textAlign="center";
      g.fillText("Start / End",cx,cy-ry-12);
      g.beginPath(); g.moveTo(cx,cy-ry-5); g.lineTo(cx,cy-ry+5); g.stroke();
      const pt=p=>{const a=-Math.PI/2+2*Math.PI*(p%1); return [cx+rx*Math.cos(a), cy+ry*Math.sin(a)];};
      const order=S.W.map((w,i)=>i).sort((i,j)=>S.W[i].v-S.W[j].v).reverse();
      order.forEach(i=>{const [x,y]=pt(S.W[i].p); workerDot(g,x,y,i,String(st.v[i]),{blocked:S.W[i].slowed && st.variant==="loop"});});
      g.fillStyle="#6b7280"; g.font="12px Calibri,Carlito,sans-serif"; g.textAlign="left";
      g.fillText(st.variant==="loop"?"Red ring = stuck behind a slower worker.":"Each worker carries their own order all the way round.",10,h-10);
    }
    g.fillStyle="#23272f"; g.font="bold 12px Calibri,Carlito,sans-serif"; g.textAlign="left"; g.textBaseline="middle";
    g.fillText(`${S.done} orders out · ${fmt(S.t,1)} h`,10,14);
  }
  let last=null;
  function frame(ts){
    if(last!=null && st.playing && slides[cur].contains(root)){ const dt=Math.min(0.05,(ts-last)/1000)*0.25; for(let k=0;k<10;k++) S.step(dt/10); }
    last=ts; draw(); requestAnimationFrame(frame);
  }
  const playBtn=root.querySelector(".play"); const setPlay=()=>playBtn.textContent=st.playing?"Pause":"Play";
  playBtn.onclick=()=>{st.playing=!st.playing;setPlay();};
  root.querySelector(".restart").onclick=()=>{S=make(st.variant)(cfg(st.variant));};
  root.querySelectorAll(".variants button").forEach(b=>b.onclick=()=>{st.variant=b.dataset.v;rebuild();});
  root.querySelector("#o2crowd").oninput=e=>{st.crowd=+e.target.value;rebuild();};
  [0,1,2].forEach(i=>root.querySelector("#o2v"+i).oninput=e=>{st.v[i]=+e.target.value;rebuild();});
  setPlay(); rebuild(); requestAnimationFrame(frame);
}

"""

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OPIM639 · Week 5 Discussion Assignment · Group 3</title>
<script>
window.MathJax = { tex: { inlineMath: [["\\(", "\\)"]], displayMath: [["\\[", "\\]"]] }, svg: { fontCache: "global" } };
</script>
<script async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.js"></script>
<style>
:root{
  --navy:#1f2a44; --smu:#102b72; --gold:#987c4d; --cyan:#00b0f0;
  --amber:#e8a33d; --amber-soft:#fbe9d0; --amber-ink:#9a6b1e; --ink:#23272f; --body:#374151;
  --muted:#6b7280; --line:#e5e7eb; --soft:#f3f4f6; --red:#b93a3a; --blue:#2563eb; --green:#2f855a;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#15171c;overflow:hidden;
  font:15px/1.4 Calibri,Carlito,"Segoe UI",system-ui,sans-serif;color:var(--body)}
#viewport{position:fixed;inset:0;display:grid;place-items:center}
#stage{position:absolute;left:0;top:0;width:1280px;height:720px;transform-origin:0 0;background:#fff;overflow:hidden;
  box-shadow:0 10px 40px rgba(0,0,0,.45)}
.slide{position:absolute;inset:0;display:none}
.slide.on{display:block}

/* ---------- title slide ---------- */
.title{background:var(--navy);color:#fff}
.title .ttext{position:absolute;left:96px;top:50%;transform:translateY(-50%)}
.title .course{margin:0;font-size:24px;font-weight:700;letter-spacing:.14em;color:var(--amber)}
.title h1{margin:6px 0 0;font-size:56px;line-height:1.1;font-weight:700}
.title .rule{width:96px;height:4px;background:var(--amber);margin:34px 0 30px}
.title .group{margin:0 0 8px;font-size:22px;font-weight:700;color:#cbd2e0}
.title .names{list-style:none;margin:0;padding:0;font-size:26px;line-height:1.45}

/* ---------- content slides ---------- */
.content{padding:20px 40px 0}
.topline{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;min-height:36px}
.option{margin:4px 0 0;font-size:15px;color:var(--ink);display:flex;gap:10px;align-items:baseline}
.option i{color:var(--body)}
.numc{flex:none;display:inline-grid;place-items:center;width:26px;height:26px;border:2px solid var(--navy);border-radius:50%;
  font-weight:700;color:var(--navy);font-style:normal;font-size:14px}
.verdict{flex:none;max-width:300px;padding:5px 14px;border-radius:9px;color:#fff;font-weight:700;font-size:14px;line-height:1.25;text-align:center}
.verdict.amber{background:var(--amber)}.verdict.red{background:var(--red)}
h2{font-size:25px;line-height:1.14;color:var(--ink);margin:6px 0 12px;max-width:1040px}
.grid{display:grid;grid-template-columns:712px 1fr;gap:26px;align-items:start}
.explainer{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);padding:9px 14px 8px;position:relative}
.exhead{display:flex;gap:10px;align-items:center;margin-bottom:6px}
.tag{background:var(--navy);color:#fff;font-size:10.5px;font-weight:700;border-radius:999px;padding:2px 10px}
.ex-title{font-weight:700;letter-spacing:.05em;color:var(--muted);font-size:12px}
.explainer .status{display:none}
.caption{margin:5px 0 0;font-size:12.5px;color:var(--body)}
.ex-grid{display:grid;grid-template-columns:1fr 212px;gap:14px}
canvas{width:100%;display:block;background:var(--soft);border-radius:6px}
.controls{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;align-items:center;margin-top:6px;font-size:12.5px}
.variants{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:5px;margin-bottom:2px}
.variants button,.playbar button{font:inherit;font-size:12.5px;padding:2px 9px;border:1px solid var(--navy);background:#fff;color:var(--navy);border-radius:5px;cursor:pointer}
.variants button.on{background:var(--navy);color:#fff}
.controls label{color:var(--ink);font-weight:600;white-space:nowrap}
.controls .rng{display:flex;gap:8px;align-items:center}
.controls input[type=range]{flex:1;accent-color:var(--amber);height:16px;margin:0}
.controls .val{font:11.5px var(--mono);min-width:60px;text-align:right}
.controls .off{opacity:.4}
.playbar{grid-column:1/-1;display:flex;gap:5px;align-items:center;font-size:11.5px;color:var(--muted);margin-top:2px}
button:focus-visible,input:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
.panel{border-left:1px solid var(--line);padding-left:12px;font-size:12.5px;line-height:1.3}
.panel h4{margin:0 0 3px;font-size:10.5px;letter-spacing:.05em;color:var(--muted)}
.panel p{margin:2px 0}
.big{font:700 21px var(--mono);color:var(--ink)}
.big span{font-family:Calibri,Carlito,sans-serif}
.stat{display:flex;justify-content:space-between;align-items:baseline;margin:2px 0;gap:6px}
.stat b{font:600 13px var(--mono);color:var(--ink);white-space:nowrap}
.stat .d{font:11px var(--mono)}.up{color:var(--red)}.down{color:var(--green)}.same{color:var(--muted)}
.panel .note{font-size:11.5px;color:var(--muted);margin:5px 0 0;line-height:1.3}
.panel hr{border:0;border-top:1px solid var(--line);margin:6px 0}
.conclusion{margin-top:10px;background:var(--navy);color:#fff;border-radius:9px;padding:10px 16px 11px;font-size:13.5px;line-height:1.38}
.conclusion .kicker{margin:0 0 3px;color:var(--amber);font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:12px}
.conclusion p{margin:0}
.points{display:flex;flex-direction:column;gap:13px}
.point{display:flex;gap:11px}
.point .ico{flex:none;width:34px;height:34px;border-radius:50%;background:var(--navy);color:#fff;display:grid;place-items:center}
.point .ico svg{width:18px;height:18px}
.point h3{margin:0 0 2px;font-size:14.5px;line-height:1.2;color:var(--ink)}
.point p{margin:0;font-size:12.5px;line-height:1.36}
.foot{position:absolute;left:40px;right:40px;bottom:9px;display:flex;justify-content:space-between;font-size:11px;color:var(--muted)}

/* ---------- presenter toolbar (outside the slide) ---------- */
#toolbar{position:fixed;left:50%;bottom:14px;transform:translateX(-50%);display:flex;gap:6px;align-items:center;
  background:rgba(20,22,28,.82);color:#fff;border-radius:999px;padding:5px 8px;font-size:13px;transition:opacity .3s;z-index:5}
#toolbar button{all:unset;cursor:pointer;padding:4px 10px;border-radius:999px}
#toolbar button:hover,#toolbar button:focus-visible{background:rgba(255,255,255,.18)}
#toolbar .count{min-width:44px;text-align:center;font-variant-numeric:tabular-nums}
body.idle #toolbar{opacity:0}
@media (prefers-reduced-motion:reduce){#toolbar{transition:none}}
</style>
</head>
<body>
<div id="viewport"><div id="stage">__SLIDES__</div></div>
<div id="toolbar" role="toolbar" aria-label="Slide controls">
  <button id="prev" aria-label="Previous slide">◀</button><span class="count" id="count"></span>
  <button id="next" aria-label="Next slide">▶</button><button id="fs" aria-label="Full screen">⛶ Full screen</button>
</div>
<script>
const SIM = __SIM__;
const slides=[...document.querySelectorAll(".slide")];
const stage=document.getElementById("stage");
let cur=0, SCALE=1;
const typeset=el=>{ if(window.MathJax&&MathJax.typesetPromise) MathJax.typesetPromise([el]).catch(()=>{}); };

function fit(){
  // scale the fixed 1280x720 slide to the largest size that fits, and centre it
  const W=document.documentElement.clientWidth||innerWidth, H=document.documentElement.clientHeight||innerHeight;
  SCALE=Math.min(W/1280, H/720);
  stage.style.transformOrigin="0 0";
  stage.style.transform=`scale(${SCALE})`;
  stage.style.left=((W-1280*SCALE)/2)+"px";
  stage.style.top=((H-720*SCALE)/2)+"px";
}
addEventListener("resize",fit); document.addEventListener("fullscreenchange",()=>setTimeout(fit,50));
if(window.ResizeObserver) new ResizeObserver(fit).observe(document.documentElement);
fit();

function go(i){
  cur=Math.max(0,Math.min(slides.length-1,i));
  slides.forEach((s,k)=>s.classList.toggle("on",k===cur));
  document.getElementById("count").textContent=`${cur+1} / ${slides.length}`;
  try{ history.replaceState(null,"","#"+(cur+1)); }catch(e){}   // sandboxed previews (about:srcdoc) block this
  typeset(slides[cur]);
}
document.getElementById("next").onclick=()=>go(cur+1);
document.getElementById("prev").onclick=()=>go(cur-1);
const toggleFS=()=>{ try{ const p=document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen?.(); p&&p.catch&&p.catch(()=>{}); }catch(e){} };
document.getElementById("fs").onclick=toggleFS;
if(!document.fullscreenEnabled) document.getElementById("fs").style.display="none";   // not allowed in embedded previews
document.addEventListener("keydown",e=>{
  if(e.target.tagName==="INPUT" && ["ArrowLeft","ArrowRight"].includes(e.key)) return;
  if(["ArrowRight","PageDown"," "].includes(e.key) && e.target.tagName!=="BUTTON"){e.preventDefault();go(cur+1);}
  else if(["ArrowLeft","PageUp"].includes(e.key)){e.preventDefault();go(cur-1);}
  else if(e.key==="Home")go(0); else if(e.key==="End")go(slides.length-1);
  else if((e.key==="f"||e.key==="F") && document.fullscreenEnabled)toggleFS();
});
let idle; const wake=()=>{document.body.classList.remove("idle");clearTimeout(idle);idle=setTimeout(()=>document.body.classList.add("idle"),2500);};
addEventListener("mousemove",wake); addEventListener("keydown",wake); wake();

__ENGINE__
const WIDGETS={buffer:bufferWidget,circle:circleWidget};
document.querySelectorAll("[data-widget]").forEach(el=>WIDGETS[el.dataset.widget](el));
let start=0; try{ start=(parseInt(location.hash.slice(1))||1)-1; }catch(e){}
go(Math.max(0,start));
</script>
</body>
</html>
"""

def icon(name: str) -> str:
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def render_title() -> str:
    t = TITLE
    names = "".join(f"<li>{esc(m)}</li>" for m in t["members"])
    return f"""
<section class="slide title" aria-label="Title">
  <div class="ttext">
    <p class="course">{esc(t['course'])}</p>
    <h1>{esc(t['subtitle'])}</h1>
    <div class="rule"></div>
    <p class="group">{esc(t['group'])}</p>
    <ul class="names">{names}</ul>
  </div>
</section>"""


def render_slide(page: int, s: dict) -> str:
    points = "".join(
        f'<div class="point"><span class="ico">{icon(ic)}</span><div><h3>{esc(t)}</h3><p>{esc(b)}</p></div></div>'
        for ic, t, b in s["points"])
    return f"""
<section class="slide content" aria-label="Option {s['num']}">
  <div class="topline">
    <p class="option"><span class="numc">{s['num']}</span><span><b>Option {s['num']}:</b> <i>\u201c{esc(s['quote'])}\u201d</i></span></p>
    <span class="verdict {s['verdict_kind']}">{esc(s['verdict'])}</span>
  </div>
  <h2>{esc(s['headline'])}</h2>
  <div class="grid">
    <div class="left">
      <div class="explainer" data-widget="{s['widget']}">
        <div class="exhead"><span class="tag">\u25cf INTERACTIVE EXPLAINER</span><span class="ex-title">{esc(s["explainer_title"])}</span><span class="status"></span></div>
        <div class="body"></div>
        <p class="caption">{esc(s['caption'])}</p>
      </div>
      <div class="conclusion"><p class="kicker">Our conclusion</p><p>{esc(s['conclusion'])}</p></div>
    </div>
    <div class="points">{points}</div>
  </div>
  <div class="foot"><span>OPIM639 · Week 5 Discussion Assignment · Group 3</span><span>{page}</span></div>
</section>"""


def build() -> Path:
    slides = render_title() + "".join(render_slide(i + 2, s) for i, s in enumerate(CONTENT))
    page = (TEMPLATE
            .replace("__SLIDES__", slides)
            .replace("__SIM__", json.dumps(SIM))
            .replace("__ENGINE__", ENGINE))
    OUT.write_text(page, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({len(CONTENT) + 1} slides)")
    if "--open" in sys.argv:
        webbrowser.open(p.resolve().as_uri())
