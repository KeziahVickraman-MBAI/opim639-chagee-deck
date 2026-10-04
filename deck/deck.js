/* ================= deck explainers =================
 * Every number comes from RAW (assumptions.json), DATA (sim/precompute.js output)
 * or a live call into Sim (sim/sim.js). Slide 2's band is shared state: moving its
 * slider updates slides 3, 4 (marker) and 5.
 */
const $=(r,s)=>r.querySelector(s), $$=(r,s)=>[...r.querySelectorAll(s)];
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const money=v=>(v<0?"−":"")+"S$"+Math.abs(v).toFixed(2);
const money0=v=>(v<0?"−":"")+"S$"+Math.round(Math.abs(v)).toLocaleString("en-SG");
const moneyM=v=>(v<0?"−":"")+"S$"+(Math.abs(v)/1e6).toFixed(1)+"m";
const int=v=>Math.round(v).toLocaleString("en-SG");
const pct=v=>Math.round(v*100)+"%", pct1=v=>(v*100).toFixed(1)+"%";
const SETUPS=Sim.SETUPS, LABEL={all_human:"All-human",mixed:"Mixed",all_machine:"All-machine"}, SHORT={all_human:"Human",mixed:"Mixed",all_machine:"Machine"};
const COL={all_human:css("--c-human"),mixed:css("--c-mixed"),all_machine:css("--c-machine")};
const SURGE0=RAW.surge.surge_default.value, SURGES=Object.keys(RAW.surge.surge_multiplier.value);
const SURGE_LABEL=g=>`${g[0].toUpperCase()+g.slice(1)} ×${RAW.surge.surge_multiplier.value[g]}`;

/* ---------- shared state ---------- */
const STATE={signal:RAW.predict.signal_strength_default.value, removeHype:RAW.predict_toggles.remove_hype_default.value, band:null};
const LISTEN=[];
const onBand=fn=>LISTEN.push(fn);
function emit(){ STATE.band=Sim.band(P,STATE.signal,STATE.removeHype); LISTEN.forEach(f=>f(STATE.band)); }

/* ---------- small SVG helpers ---------- */
function niceStep(range,n){ const raw=range/n, mag=Math.pow(10,Math.floor(Math.log10(raw))), f=raw/mag;
  return mag*(f<1.5?1:f<3?2:f<7?5:10); }
const ticks=(max,n)=>{ const s=niceStep(max,n), out=[]; for(let v=0;v<=max+1e-9;v+=s) out.push(+v.toFixed(10)); return out; };
const txt=(x,y,s,a="")=>`<text x="${x}" y="${y}" ${a}>${s}</text>`;
function nudge(items,minGap,lo,hi){            // keep direct labels apart vertically
  items.sort((a,b)=>a.y-b.y);
  for(let i=1;i<items.length;i++) if(items[i].y-items[i-1].y<minGap) items[i].y=items[i-1].y+minGap;
  const over=items.length?items[items.length-1].y-hi:0; if(over>0) items.forEach(it=>it.y-=over);
  items.forEach(it=>it.y=Math.max(lo,it.y)); return items;
}

/* ================= slide 1: where does uncertainty land ================= */
function whereWidget(root){
  $$(root,".variants button").forEach(b=>b.onclick=()=>{
    $$(root,".variants button").forEach(x=>x.classList.toggle("on",x===b));
    $$(root,".scen").forEach(s=>s.classList.toggle("on",s.dataset.sc===b.dataset.sc));
  });
}

/* ================= slide 2: demand band ================= */
function bandWidget(root){
  const body=$(root,".body");
  body.innerHTML=`<div class="exgrid"><div>
      <svg class="chart" viewBox="0 0 470 206" role="img" aria-label="Weekly demand bands"></svg>
      <div class="controls"><label for="sig">Pre-launch signal</label><div class="rng"><input id="sig" type="range" min="0" max="1" step="any"><span class="val sigv"></span></div></div>
      <div class="variants" style="margin-top:5px"><button data-h="1">Opening hype removed</button><button data-h="0">Hype included</button></div>
    </div><div class="out"></div></div>`;
  const svg=$(body,"svg"), out=$(body,".out"), sig=$(body,"#sig");
  sig.value=STATE.signal;
  sig.oninput=e=>{STATE.signal=+e.target.value; emit();};
  $$(body,"[data-h]").forEach(b=>b.onclick=()=>{STATE.removeHype=b.dataset.h==="1"; emit();});
  const xmax=7*Sim.dailyBase(P)*P.hype*(1+P.uNone);
  onBand(b=>{
    $$(body,"[data-h]").forEach(x=>x.classList.toggle("on",(x.dataset.h==="1")===b.removeHype));
    $(body,".sigv").textContent=`${pct(STATE.signal)} → ±${pct1(b.u)}`;
    const steady=Sim.band(P,STATE.signal,true), hype=Sim.band(P,STATE.signal,false);
    const L=12,R=458,X=v=>L+(R-L)*v/xmax, amber=css("--amber"), grey="#c5cad3";
    let s=ticks(xmax,5).map(v=>`<line x1="${X(v)}" x2="${X(v)}" y1="18" y2="176" stroke="#e5e7eb"/>`+
      txt(X(v),192,int(v),'font-size="10" fill="#6b7280" text-anchor="middle"')).join("");
    [[steady,"Steady demand (repeat habit)",40,b.removeHype],[hype,"Opening weeks, with hype",116,!b.removeHype]].forEach(([bd,lab,y,act])=>{
      s+=txt(L,y-6,lab+(act?" · handed on":""),`font-size="11.5" font-weight="700" fill="${act?"#23272f":"#6b7280"}"`);
      s+=`<rect x="${X(bd.low)}" y="${y}" width="${X(bd.high)-X(bd.low)}" height="22" rx="4" fill="${act?amber:grey}" opacity="${act?0.9:0.7}"/>`;
      s+=`<line x1="${X(bd.base)}" x2="${X(bd.base)}" y1="${y-3}" y2="${y+25}" stroke="#23272f" stroke-width="2"/>`;
      s+=txt(X(bd.low),y+36,int(bd.low),'font-size="10.5" fill="#374151" text-anchor="middle"');
      s+=txt(X(bd.high),y+36,int(bd.high),'font-size="10.5" fill="#374151" text-anchor="middle"');
      s+=txt(X(bd.base)+4,y+16,int(bd.base),'font-size="10.5" font-weight="700" fill="#23272f"');
    });
    s+=txt(R,204,"cups per week","font-size=\"10\" fill=\"#6b7280\" text-anchor=\"end\"");
    svg.innerHTML=s;
    out.innerHTML=`<h4>BAND HANDED ON</h4>
      <div class="big">±${pct1(b.u)} <small>of base</small></div>
      <div class="stat"><span>Low</span><b>${int(b.low)}</b></div>
      <div class="stat"><span>Base</span><b>${int(b.base)}</b></div>
      <div class="stat"><span>High</span><b>${int(b.high)}</b></div>
      <div class="stat"><span>Width</span><b>${int(b.width)}</b></div>
      <p class="note">Cups per week. ${b.removeHype?"Opening hype removed: steady demand.":"Hype included: opening-week demand."}</p>
      <div class="handoff"><b>Not in the signal:</b> tourists and non-app orders, so true demand is likely higher.</div>`;
  });
}

/* ================= slide 3: opening stock ================= */
function stockWidget(root){
  const body=$(root,".body"), [lo,hi]=RAW.provision.opening_stock_days.range;
  let days=RAW.provision.opening_stock_days.value;
  body.innerHTML=`<div class="exgrid"><div>
      <svg class="chart" viewBox="0 0 470 236" role="img" aria-label="Expected cost by days of opening stock"></svg>
      <div class="dlegend" style="margin:4px 0 0"><span><span class="sw" style="background:#23272f"></span>Total expected cost</span>
        <span><span class="sw" style="background:${css("--c-human")}"></span>Milk wasted</span><span><span class="sw" style="background:${css("--red")}"></span>Cups missed</span></div>
      <div class="controls"><label for="days">Days of opening stock</label><div class="rng"><input id="days" type="range" min="${lo}" max="${hi}" step="1" value="${days}"><span class="val dv"></span></div></div>
    </div><div class="out"></div></div>`;
  const svg=$(body,"svg"), out=$(body,".out");
  $(body,"#days").oninput=e=>{days=+e.target.value; draw(STATE.band);};
  function draw(b){
    const daily=b.base/7, r=Sim.provision(P,b.u,days,daily), strong=Sim.provision(P,P.uStrong,days,daily);
    $(body,".dv").textContent=`${days} days`;
    const n=40, pts=[...Array(n+1)].map((_,i)=>{const d=lo+(hi-lo)*i/n, c=r.curve(d); return {d,w:c.waste,s:c.stockout,t:c.waste+c.stockout};});
    const ymax=Math.max(...pts.map(p=>p.t))*1.05, L=46,R=458,T=12,B=210;
    const X=d=>L+(R-L)*(d-lo)/(hi-lo), Y=v=>B-(B-T)*v/ymax;
    const path=k=>pts.map((p,i)=>(i?"L":"M")+X(p.d).toFixed(1)+" "+Y(p[k]).toFixed(1)).join("");
    let s=ticks(ymax,4).map(v=>`<line x1="${L}" x2="${R}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e5e7eb"/>`+txt(L-5,Y(v)+3,money0(v),'font-size="10" fill="#6b7280" text-anchor="end"')).join("");
    for(let d=lo; d<=hi; d+=Math.max(1,Math.round((hi-lo)/6))) s+=txt(X(d),B+14,d,'font-size="10" fill="#6b7280" text-anchor="middle"');
    s+=txt(R,B+25,"days of base demand","font-size=\"10\" fill=\"#6b7280\" text-anchor=\"end\"");
    s+=`<path d="${path("w")}" fill="none" stroke="${css("--c-human")}" stroke-width="2" stroke-dasharray="5 3"/>`;
    s+=`<path d="${path("s")}" fill="none" stroke="${css("--red")}" stroke-width="2" stroke-dasharray="5 3"/>`;
    s+=`<path d="${path("t")}" fill="none" stroke="#23272f" stroke-width="2.5"/>`;
    s+=`<line x1="${X(days)}" x2="${X(days)}" y1="${T}" y2="${B}" stroke="${css("--amber")}" stroke-width="2"/>`;
    s+=`<circle cx="${X(days)}" cy="${Y(r.total)}" r="5" fill="${css("--amber")}" stroke="#fff" stroke-width="2"/>`;
    if(r.optDays>=lo && r.optDays<=hi){
      s+=`<circle cx="${X(r.optDays)}" cy="${Y(r.optTotal)}" r="6" fill="#fff" stroke="${css("--green")}" stroke-width="3"/>`;
      s+=txt(X(r.optDays),Y(r.optTotal)-11,"lowest cost",`font-size="10.5" font-weight="700" fill="${css("--green")}" text-anchor="middle"`);
    }
    svg.innerHTML=s;
    const rows=DATA.sweeps[SURGE0].rows, cost=k=>Sim.atU(rows,b.u,r=>r[k].cost);
    const best=SETUPS.reduce((a,k)=>cost(k)<cost(a)?k:a), gap=cost("all_machine")-cost("mixed");
    out.innerHTML=`<h4>AT ${days} DAYS OF STOCK</h4>
      <div class="big">${money0(r.total)} <small>expected</small></div>
      <div class="stat"><span>Milk wasted</span><b>${money0(r.waste)}</b></div>
      <div class="stat"><span>Cups missed</span><b>${money0(r.stockout)}</b></div>
      <hr><h4>BEST ORDER AT THIS BAND (±${pct1(b.u)})</h4>
      <div class="stat best"><span>${r.optDays.toFixed(1)} days</span><b>${money0(r.optTotal)}</b></div>
      <div class="stat"><span>Same order, strong signal</span><b>${money0(strong.optTotal)}</b></div>
      <div class="handoff"><b>Hand-off:</b> open with ${int(r.optDays*daily*P.milkPerCup)} L of milk. Counter (slide 4): cheapest is ${LABEL[best]}; mixed beats full automation by ${money(gap)}/cup.</div>`;
  }
  onBand(draw);
}

/* ================= slide 4: crossover chart ================= */
function crossWidget(root){
  const body=$(root,".body"), shiftRows=$(root,".shiftrows");
  const st={surge:SURGE0, u:null, shift:null};
  const allRuns=[...Object.values(DATA.sweeps),...Object.values(DATA.shift).flatMap(s=>[s.lowRun,s.highRun])];
  const ymax=Math.max(...allRuns.flatMap(r=>r.rows.flatMap(x=>SETUPS.map(k=>x[k].cost))))*1.06;
  const grid=DATA.sweeps[SURGE0].rows.map(r=>r.u), umin=grid[0], umax=grid[grid.length-1];
  body.innerHTML=`<div class="exgrid"><div>
      <div class="variants">${SURGES.map(g=>`<button data-g="${g}">${SURGE_LABEL(g)} surge</button>`).join("")}</div>
      <div class="chartwrap"><svg class="chart" viewBox="0 0 470 178" role="img" aria-label="Cost per cup against demand uncertainty"></svg><div class="tip"></div></div>
      <p class="note xo" style="margin-top:3px"></p>
      <div class="controls"><label for="uu">Demand uncertainty</label><div class="rng"><input id="uu" type="range" min="${umin}" max="${umax}" step="any"><span class="val uv"></span></div></div>
    </div><div class="out"></div></div>`;
  const svg=$(body,"svg"), out=$(body,".out"), tip=$(body,".tip");
  const SHIFT=[
    ["machine_cost","Machine cost per month",x=>money0(x)],
    ["staff_turnover","Staff turnover (share new)",x=>pct(x)],
  ];
  shiftRows.innerHTML=SHIFT.map(([k,lab,f])=>{const s=DATA.shift[k];
    return `<div class="srow" data-shift="${k}"><span>${lab}</span><span class="seg">
      <button data-l="low">Low ${f(s.low)}</button><button data-l="def">Default</button><button data-l="high">High ${f(s.high)}</button></span><span class="sval"></span></div>`;}).join("")+
    `<div class="srow" data-shift="forecast"><span>Forecast narrows (slide 2 band)</span><span class="seg">
      <button data-u="${P.uNone}">No signal ±${pct(P.uNone)}</button><button data-u="def">Slide 2</button><button data-u="${P.uStrong}">Strong ±${pct(P.uStrong)}</button></span><span class="sval"></span></div>`;
  const run=()=>{ if(st.shift && st.surge===DATA.shift[st.shift.k].surge){ const s=DATA.shift[st.shift.k]; return s[st.shift.l+"Run"]; } return DATA.sweeps[st.surge]; };
  const KIND={
    mixed_cheaper_everywhere:"No crossover: mixed is cheaper than full automation at every uncertainty level shown.",
    machine_cheaper_everywhere:"No crossover: full automation is cheaper than mixed at every uncertainty level shown.",
    reverse:"Mixed is cheaper only when demand is predictable: the reverse of our hypothesis.",
  };
  const kindText=c=>c.kind==="crossover"?`Crossover at ±${pct1(c.u)}: mixed is cheaper above it.`:KIND[c.kind];
  const L=44,R=378,T=10,B=150, X=u=>L+(R-L)*(u-umin)/(umax-umin), Y=v=>B-(B-T)*v/ymax;
  function draw(){
    const rs=run(), rows=rs.rows, u=st.u;
    $$(body,"[data-g]").forEach(b=>b.classList.toggle("on",b.dataset.g===st.surge));
    $(body,"#uu").value=u; $(body,".uv").textContent=`±${pct1(u)}`;
    let s=`<rect x="${X(P.uStrong)}" y="${T}" width="${X(P.uNone)-X(P.uStrong)}" height="${B-T}" fill="${css("--amber-soft")}" opacity=".6"/>`+
      txt(X(P.uStrong)+4,B-5,"slide 2 range",`font-size="10" fill="${css("--amber-ink")}"`);
    s+=ticks(ymax,4).map(v=>`<line x1="${L}" x2="${R}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e5e7eb"/>`+txt(L-5,Y(v)+3,money(v),'font-size="10" fill="#6b7280" text-anchor="end"')).join("");
    s+=grid.filter((_,i)=>i%2===0).map(g=>txt(X(g),B+13,"±"+pct(g),'font-size="10" fill="#6b7280" text-anchor="middle"')).join("");
    s+=txt(R,B+25,"demand uncertainty (band half-width)","font-size=\"10\" fill=\"#6b7280\" text-anchor=\"end\"");
    const labs=[];
    SETUPS.forEach(k=>{
      s+=`<path d="${rows.map((r,i)=>(i?"L":"M")+X(r.u).toFixed(1)+" "+Y(r[k].cost).toFixed(1)).join("")}" fill="none" stroke="${COL[k]}" stroke-width="${k==="mixed"?2.6:2}"/>`;
      labs.push({k,y:Y(rows[rows.length-1][k].cost)+4});
    });
    nudge(labs,13,T+8,B).forEach(l=>{ s+=txt(R+6,l.y,`${LABEL[l.k]} ${money(rows[rows.length-1][l.k].cost)}`,`font-size="10.5" fill="#23272f"`);
      s+=`<line x1="${R+1}" x2="${R+5}" y1="${l.y-4}" y2="${l.y-4}" stroke="${COL[l.k]}" stroke-width="3"/>`; });
    s+=`<line x1="${X(u)}" x2="${X(u)}" y1="${T}" y2="${B}" stroke="#23272f" stroke-width="1.5" stroke-dasharray="4 3"/>`;
    SETUPS.forEach(k=>{ s+=`<circle cx="${X(u)}" cy="${Y(Sim.atU(rows,u,r=>r[k].cost))}" r="4.5" fill="${COL[k]}" stroke="#fff" stroke-width="2"/>`; });
    if(rs.crossover.kind==="crossover"){ const cu=rs.crossover.u, cy=Y(Sim.atU(rows,cu,r=>r.mixed.cost));
      s+=`<circle cx="${X(cu)}" cy="${cy}" r="7" fill="none" stroke="#23272f" stroke-width="2"/>`+txt(X(cu),cy-11,"crossover",'font-size="10.5" font-weight="700" fill="#23272f" text-anchor="middle"'); }
    s+=`<rect class="hit" x="${L}" y="${T}" width="${R-L}" height="${B-T}" fill="transparent"/>`;
    svg.innerHTML=s;
    $(body,".xo").textContent=kindText(rs.crossover)+(st.shift&&st.surge===DATA.shift[st.shift.k].surge?" (with the shifted assumption)":"");
    const c=Object.fromEntries(SETUPS.map(k=>[k,Sim.atU(rows,u,r=>r[k].cost)]));
    const best=SETUPS.reduce((a,k)=>c[k]<c[a]?k:a);
    const parts=k=>["machine","labour","lost"].map(p=>Sim.atU(rows,u,r=>r[k][p]));
    const pmax=Math.max(...SETUPS.map(k=>c[k]));
    const PC={machine:"#8b95a7",labour:"#4b5563",lost:css("--red")};
    out.innerHTML=`<h4>COST PER CUP AT ±${pct1(u)}</h4>
      ${SETUPS.map(k=>`<div class="stat ${k===best?"best":""}"><span><span class="sw" style="background:${COL[k]}"></span>${LABEL[k]}</span><b>${money(c[k])}</b></div>`).join("")}
      <div class="stat"><span>Mixed − machine</span><b>${money(c.mixed-c.all_machine)}</b></div>
      <hr><h4>WHAT THE COST IS MADE OF</h4>
      ${SETUPS.map(k=>{const [m,l,o]=parts(k);return `<div style="display:flex;align-items:center;gap:6px;margin:3px 0;font-size:11px"><span style="width:44px">${SHORT[k]}</span>
        <span style="display:flex;gap:2px;flex:1">${[["machine",m],["labour",l],["lost",o]].map(([p,v])=>v>0.004?`<span title="${p} ${money(v)}" style="height:10px;border-radius:2px;background:${PC[p]};width:${(100*v/pmax).toFixed(1)}%"></span>`:"").join("")}</span></div>`;}).join("")}
      <div class="dlegend" style="margin-top:2px;gap:8px"><span><span class="sw" style="background:${PC.machine}"></span>machines</span><span><span class="sw" style="background:${PC.labour}"></span>labour</span><span><span class="sw" style="background:${PC.lost}"></span>lost</span></div>
      <hr>
      <div class="stat"><span>Automated line busy</span><b>${pct(Sim.atU(rows,u,r=>r.all_machine.busy))}</b></div>
      <div class="stat"><span>Orders lost: mixed</span><b>${pct1(Sim.atU(rows,u,r=>r.mixed.lostShare))}</b></div>`;
    // shift rows
    $$(shiftRows,".srow").forEach(row=>{
      const k=row.dataset.shift;
      if(k==="forecast"){
        $$(row,"button").forEach(b=>b.classList.toggle("on",Math.abs((b.dataset.u==="def"?STATE.band.u:+b.dataset.u)-u)<1e-9));
        $(row,".sval").textContent=""; return;
      }
      const s=DATA.shift[k], enabled=st.surge===s.surge, lvl=st.shift&&st.shift.k===k?st.shift.l:"def";
      $$(row,"button").forEach(b=>{ b.disabled=!enabled; b.classList.toggle("on",enabled&&b.dataset.l===lvl); });
      const kind=lvl==="def"?DATA.sweeps[s.surge].crossover:s[lvl+"Run"].crossover;
      $(row,".sval").textContent=enabled?(kind.kind==="crossover"?`→ crossover at ±${pct1(kind.u)}`:`→ ${kind.kind.replace(/_/g," ")}`):`computed at ${s.surge} surge only`;
    });
  }
  svg.addEventListener("mousemove",e=>{
    const pt=svg.createSVGPoint(); pt.x=e.clientX; pt.y=e.clientY; const p=pt.matrixTransform(svg.getScreenCTM().inverse());
    if(p.x<L||p.x>R){ tip.style.display="none"; return; }
    const rows=run().rows, uu=umin+(umax-umin)*(p.x-L)/(R-L), r=rows.reduce((a,b)=>Math.abs(b.u-uu)<Math.abs(a.u-uu)?b:a);
    tip.innerHTML=`<div>±${pct(r.u)} uncertainty</div>`+SETUPS.map(k=>`<div><span class="sw" style="background:${COL[k]}"></span>${LABEL[k]} <b>${money(r[k].cost)}</b></div>`).join("");
    const sc=svg.getBoundingClientRect().width/470;
    tip.style.display="block"; tip.style.left=((X(r.u)+10)*sc/SCALE)+"px"; tip.style.top=(12*sc/SCALE)+"px";
  });
  svg.addEventListener("mouseleave",()=>tip.style.display="none");
  $$(body,"[data-g]").forEach(b=>b.onclick=()=>{st.surge=b.dataset.g; draw();});
  $(body,"#uu").oninput=e=>{st.u=+e.target.value; draw();};
  $$(shiftRows,"[data-shift] button").forEach(b=>b.onclick=()=>{
    const k=b.closest(".srow").dataset.shift;
    if(k==="forecast"){ st.u=b.dataset.u==="def"?STATE.band.u:+b.dataset.u; }
    else st.shift=b.dataset.l==="def"?null:{k,l:b.dataset.l};
    draw();
  });
  onBand(b=>{ st.u=b.u; draw(); });
}

/* ================= slide 5: benefit calculator ================= */
function benefitWidget(root){
  const body=$(root,".body"), B=RAW.benefit, rows=DATA.sweeps[SURGE0].rows;
  const daily0=Sim.dailyBase(P), days0=RAW.provision.opening_stock_days.value;
  const maxSaving=Math.max(...rows.map(r=>r.all_machine.cost));
  const maxWaste=Sim.provision(P,P.uNone,days0,daily0).optTotal;
  const st={stores:B.overseas_stores_per_year.value, cups:RAW.store.cups_per_store_per_year.value, saving:0, waste:0, linked:true};
  const [s0,s1]=B.overseas_stores_per_year.range, [c0,c1]=RAW.store.cups_per_store_per_year.range;
  body.innerHTML=`<div class="controls" style="grid-template-columns:262px 1fr">
      <label for="bst">Overseas openings a year</label><div class="rng"><input id="bst" type="range" min="${s0}" max="${s1}" step="1"><span class="val v1"></span></div>
      <label for="bcu">Cups per store per year</label><div class="rng"><input id="bcu" type="range" min="${c0}" max="${c1}" step="any"><span class="val v2"></span></div>
      <label for="bsa">Saving per cup (slide 4)</label><div class="rng"><input id="bsa" type="range" min="0" max="${maxSaving}" step="any"><span class="val v3"></span></div>
      <label for="bwa">Stock cost avoided per opening (slide 3)</label><div class="rng"><input id="bwa" type="range" min="0" max="${maxWaste}" step="any"><span class="val v4"></span></div>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px"><span class="note link"></span><span class="variants" style="margin:0"><button class="relink">Re-link to slides 2–4</button></span></div>
    <div class="formula"></div>`;
  const ids={bst:"stores",bcu:"cups",bsa:"saving",bwa:"waste"};
  Object.entries(ids).forEach(([id,k])=>$(body,"#"+id).oninput=e=>{ st[k]=+e.target.value; if(k==="saving"||k==="waste") st.linked=false; draw(); });
  $(body,".relink").onclick=()=>{ st.linked=true; link(STATE.band); };
  function link(b){
    if(!st.linked) return draw();
    const daily=b.base/7;
    st.saving=Sim.atU(rows,b.u,r=>r.all_machine.cost-r.mixed.cost);
    st.waste=Sim.provision(P,P.uNone,days0,daily).optTotal-Sim.provision(P,b.u,days0,daily).optTotal;
    draw();
  }
  function draw(){
    Object.entries(ids).forEach(([id,k])=>$(body,"#"+id).value=st[k]);
    $(body,".v1").textContent=int(st.stores); $(body,".v2").textContent=int(st.cups);
    $(body,".v3").textContent=money(st.saving); $(body,".v4").textContent=money0(st.waste);
    const counter=st.stores*st.cups*st.saving, stock=st.stores*st.waste, total=counter+stock;
    $(body,".link").textContent=st.linked?`Linked: band ±${pct1(STATE.band.u)} from slide 2, ${SURGE0} surge.`:"Unlinked: you moved a linked slider.";
    $(body,".formula").innerHTML=`<div class="big" style="margin-bottom:3px">≈ ${moneyM(total)} <small>a year, illustrative</small></div>
      <span class="term"><b>${int(st.stores)}</b> openings</span> × ( <span class="term"><b>${int(st.cups)}</b> cups</span> × <span class="term"><b>${money(st.saving)}</b> saved per cup</span>
      + <span class="term"><b>${money0(st.waste)}</b> stock cost avoided</span> )
      <small style="margin-top:4px">≈ ${moneyM(counter)} from the counter + ${moneyM(stock)} from opening stock. Saving per cup = full-automation minus mixed cost per cup; stock cost avoided = best-order cost with no signal minus with the slide 2 band.</small>`;
  }
  onBand(link);
}

/* ================= slide 5: risk toggles ================= */
function riskToggles(){
  $$(document,".risk .rt").forEach(b=>b.onclick=()=>{
    const r=b.closest(".risk"), on=!r.classList.contains("on");
    r.classList.toggle("on",on); b.setAttribute("aria-expanded",on);
  });
}
