r"""
build_opim639_week6_deck.py  -  OPIM639 Week 6 (Group 3) as an interactive slide deck.

    python build_opim639_week6_deck.py          # writes opim639_week6_explainer.html
    python build_opim639_week6_deck.py --open   # ...and opens it

Three 16:9 slides (1280 x 720, scaled to fit the window, F for full screen):

  1  Title slide
  2  Riders keep the edge   explainer tabs: "Where the time goes" (drive vs doorstep,
                            by building type) and "A day of demand" (fixed robot fleet
                            vs riders who flex with the peaks)
  3  Robots win niches      explainer: "Cheapest capable mode" - the platform sends
                            each order type to a rider or a robot; the sliders are the
                            signposts that could shift the balance

Editing the words
  * Here: change CONTENT (text) or SIM (explainer numbers) below and re-run.
  * In the browser: press E (or the Edit button) and click any text to change it.
    Edits are saved in that browser. "Download" saves a copy of the deck with the
    edits built in. Re-running this script does NOT pick up browser edits, so copy
    anything you want to keep into CONTENT.
  * N shows the speaker notes (editable too).

All explainer numbers are illustrative assumptions, not market data. They live in SIM.
"""

from __future__ import annotations

import html
import json
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "opim639_week6_explainer.html"
esc = html.escape

TITLE = dict(
    course="OPIM639",
    subtitle="Week 6 Discussion Assignment",
    topic="Autonomous vehicles versus Uberization for last-mile delivery",
    group="Group 3",
    members=["Ayumi Liow", "Jin Ong", "Keziah", "Revan"],
)

# ---------------------------------------------------------------------------
# Explainer assumptions (illustrative, S$ and minutes)
# ---------------------------------------------------------------------------
SIM = {
    # Tab A: one order, door to door. Minutes a rider spends on each step.
    "doorstep": {
        "rideMin": 12,          # rider's ride from restaurant to the address
        "robotRideMin": 17,     # pavement / road robots travel slower
        "buildings": {
            "landed": {"label": "Landed house", "park": 0.5, "find": 0.5, "guard": 0, "lift": 0, "hand": 1,
                       "robotStops": "at the gate", "custWalk": 0.5},
            "hdb":    {"label": "HDB block", "park": 2, "find": 2, "guard": 0, "lift": 3, "hand": 1,
                       "robotStops": "at the void deck", "custWalk": 4},
            "condo":  {"label": "Condo with guard", "park": 3, "find": 2, "guard": 3, "lift": 3, "hand": 1,
                       "robotStops": "at the guardhouse", "custWalk": 6},
            "office": {"label": "Office tower", "park": 4, "find": 2, "guard": 2, "lift": 4, "hand": 1,
                       "robotStops": "at the lobby", "custWalk": 5},
        },
        "notHomeRider": 3,      # rider calls, reroutes or leaves it with the guard
        "notHomeRobotWait": 10, # robot waits, then goes back: a failed attempt
    },
    # Tab B: one zone, one day. Orders per hour, midnight to midnight.
    "demand": {
        "hourly": [5, 3, 2, 1, 1, 2, 8, 20, 30, 25, 30, 70, 120, 90, 40, 30, 35, 60, 110, 100, 60, 35, 20, 10],
        "days": {
            "normal": {"label": "Normal day", "peak": 1.0, "off": 1.0},
            "rain":   {"label": "Rainy day", "peak": 1.45, "off": 1.2},
            "sale":   {"label": "Sale day", "peak": 1.8, "off": 1.1},
        },
        "riderPay": 5.5,        # per drop
        "riderSurge": 2.0,      # extra incentive per drop in peak hours
        "surgeAbove": 60,       # orders/hr that counts as a peak hour
        "robotPerHour": 1.5,    # drops per robot per hour (slow, one order per trip)
        "robotDayCost": 120,     # purchase, charging, repair, insurance, monitoring, per robot per day
        "robotPerDrop": 0.5,
        "fleet": 40,
    },
    # Slide 3: which mode gets each type of order.
    # vol = share of orders; rules/build = how open the rules / how robot-ready the
    # buildings must be before a robot can do it; never = why a robot cannot.
    "dispatch": {
        "riderCost": 5.5, "robotCost": 6.5, "rules": 0.35, "build": 0.2,
        "future": {"riderCost": 7.0, "robotCost": 3.0, "rules": 0.8, "build": 0.7},
        "orders": [
            {"name": "Campus or business park run", "vol": 8,  "rules": 0.2, "build": 0.0, "rider": 1.0, "robot": 0.7},
            {"name": "Hub to locker parcels",        "vol": 7,  "rules": 0.3, "build": 0.0, "rider": 1.0, "robot": 0.6},
            {"name": "Night grocery top-up",         "vol": 6,  "rules": 0.4, "build": 0.3, "rider": 1.4, "robot": 1.0},
            {"name": "Pharmacy item, contactless",   "vol": 5,  "rules": 0.4, "build": 0.3, "rider": 1.0, "robot": 1.0},
            {"name": "Lunch rush meal, HDB block",   "vol": 30, "rules": 0.5, "build": 0.6, "rider": 1.2, "robot": 1.3},
            {"name": "Hot meal to a guarded condo",  "vol": 20, "rules": 0.5, "build": 0.8, "rider": 1.1, "robot": 1.2},
            {"name": "Bulky grocery order",          "vol": 12, "never": "too big for the box", "rider": 1.5},
            {"name": "Address changed mid route",    "vol": 12, "never": "needs a judgement call", "rider": 1.1},
        ],
    },
}

# ---------------------------------------------------------------------------
# Slide content (from OPIM639 Week 6 Discussion_Group 3.pptx)
# ---------------------------------------------------------------------------
ICONS = {
    "building": '<path d="M4 21V5l8-2v18"/><path d="M12 21V9l8 2v10"/><path d="M3 21h18"/>'
                '<path d="M7 8h2M7 12h2M7 16h2M15 13h2M15 17h2"/>',
    "wave": '<path d="M3 17l4-6 4 3 5-8 5 6"/><path d="M3 21h18"/>',
    "coins": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/>'
             '<path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
    "phone": '<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/>',
    "box": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M4 7.5l8 4.5 8-4.5"/><path d="M12 12v9"/>',
    "scale": '<path d="M12 3v18"/><path d="M7 21h10"/><path d="M4 7h16"/><path d="M4 7l-2.5 6h5L4 7z"/>'
             '<path d="M20 7l-2.5 6h5L20 7z"/>',
    "route": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/>'
             '<path d="M8.5 18H15a3 3 0 000-6H9a3 3 0 010-6h6.5"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/>'
             '<path d="M16 4.5a3.5 3.5 0 010 7"/><path d="M18 14c2.2.6 3.5 2.8 3.5 6"/>',
    "moon": '<path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7.5a4 4 0 018 0V11"/>',
    "trend": '<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
}

CONTENT = [
    dict(
        key="s2",
        widget="edge",
        kicker="Autonomous vehicles versus Uberization for last-mile delivery",
        headline="We believe that human riders are likely to keep the edge in last mile delivery",
        points=[
            ("building", "Robots struggle once they reach the building",
             "Parking, finding the right block and lift, getting past condo guards. Most robots stop at the kerb instead."),
            ("wave", "Rider supply stretches to meet demand peaks",
             "Incentives pull extra riders online for lunch rushes, rain and sales. Robots sized for peaks sit idle otherwise."),
            ("coins", "Platforms avoid the cost of owning fleets",
             "Platforms profit by matching, not owning. Robots add purchase, charging, repair, insurance and monitoring costs."),
            ("phone", "Riders solve problems on the spot",
             "Customer out, address changed, orders added mid route: riders call and reroute without a remote operator."),
            ("box", "One rider can carry almost any order",
             "Hot meals, bulky groceries, parcels and returns on one trip. Robots are capped by box size, weight and range."),
            ("scale", "Rules and public opinion slow robot rollout",
             "Robot rules differ by city, and platforms seen as job creators risk backlash for cutting gig income."),
        ],
        explainer_title="The logic behind our view",
        tabs=[
            ("time", "Where the time goes",
             "Robots mainly automate the drive, yet much of the delay happens at the doorstep. Parking, lifts and "
             "missed customers need judgement riders have and robots lack."),
            ("day", "A day of demand",
             "Riders also flex with demand at no fixed cost, so replacing them saves little today."),
        ],
        view_kicker="Our view",
        view_lead="Riders keep the edge because the hardest part of the last mile is at the doorstep, where "
                  "flexibility beats automation.",
        view_body="Robots cut driving cost, but until they reliably handle buildings, demand surges and surprises, "
                  "riders stay cheaper and more dependable for most orders.",
        notes=("Build the argument left to right. The lecture's list of last-mile challenges (parking, finding the "
               "lift, locating the unit, customer not around, failed attempts) is mostly about the handover, not the "
               "driving. Robots mainly automate the driving. Point 1: most sidewalk and road robots meet the customer "
               "at the kerb, which shifts the last few metres onto the customer. Point 2: meal demand is very peaky; "
               "gig supply responds to incentives, a fixed fleet does not. Point 3: this is the go light versus go "
               "heavy contrast; robots push a platform toward owning and servicing a fleet. Point 4: dynamic routing "
               "and rescheduling are where human judgement matters. Point 5: O2O platforms bundle many services, and "
               "a human courier is the most flexible unit. Point 6: platforms are major job creators, so replacing "
               "riders is a political question too. Conclusion: automation solves the easier part of the problem, so "
               "riders likely keep the edge for most orders for now."),
    ),
    dict(
        key="s3",
        widget="dispatch",
        kicker="Where robots win in our view",
        headline="Robots will likely win niches, not the whole market",
        sub="Autonomy is strongest where the environment is predictable and labour is scarce.",
        points=[
            ("route", "Robots do well on predictable, repeat routes",
             "Campuses, business parks and hub to locker runs, where stops and service times are easy to plan."),
            ("users", "Robots offset rider shortages and turnover",
             "In ageing, high wage markets, robots offer a steady service level that a churning workforce struggles to match."),
            ("moon", "Robots can run through the night",
             "Night and off peak runs with no shift limits, freeing riders for the complex, high value orders."),
            ("lock", "Robots offer secure, contactless handover",
             "Locked compartments and precise ETAs suit groceries, pharmacy items and small parcels."),
            ("trend", "Robot costs fall as volumes grow",
             "No wage per drop, so unit economics should improve as volumes grow and the technology matures."),
        ],
        explainer_title="Each order goes to the cheapest capable mode",
        caption="What could shift the balance",
        sliders=[
            ("robotCost", "Robot cost per drop falls below a rider’s"),
            ("rules", "Clear rules for pavement and road robots"),
            ("build", "Buildings add robot friendly lifts and lockers"),
            ("riderCost", "Rider cost per drop (wages, shortages)"),
        ],
        view_kicker="Our view",
        view_lead="Human riders will likely dominate for years, with robots growing as a complementary layer.",
        view_body="Uber Eats and Meituan already test robots and drones inside their rider networks. The long run "
                  "winner is probably the platform that sends each order to the cheapest capable mode.",
        notes=("Robots are not losing, they are specialising. They fit where routing is predictable and service times "
               "are stable, which is essentially the textbook routing problem with few surprises, and they pair "
               "naturally with pick-up stations and lockers. Labour turnover was listed in class as a threat to "
               "consistent service; robots address that directly. Verdict: rather than one mode winning, the platform "
               "becomes the dominant player. Today it runs a three sided market of customers, restaurants and riders; "
               "tomorrow it may add robots as a fourth supply type and assign each order to whichever mode is cheapest "
               "and able to do it. Close with the signposts: if costs, regulation and building infrastructure move "
               "quickly, the balance could tilt toward autonomy sooner."),
    ),
]


ENGINE = r"""
/* ================= helpers ================= */
const $=(r,s)=>r.querySelector(s), $$=(r,s)=>[...r.querySelectorAll(s)];
const money=v=>"S$"+v.toFixed(2);
const pct=v=>Math.round(v*100)+"%";
function setupCanvas(cv,h){
  const dpr=(window.devicePixelRatio||1)*Math.max(1,SCALE), w=cv.clientWidth||560;
  cv.width=w*dpr; cv.height=h*dpr; cv.style.height=h+"px";
  const g=cv.getContext("2d"); g.setTransform(dpr,0,0,dpr,0,0); return {g,w,h};
}

/* ================= slide 2: riders keep the edge ================= */
function edgeWidget(root){
  $$(root,".tabs [data-tab]").forEach(b=>b.onclick=()=>{
    $$(root,".tabs [data-tab]").forEach(x=>x.classList.toggle("on",x===b));
    $$(root,".tabpane").forEach(p=>p.classList.toggle("on",p.dataset.tab===b.dataset.tab));
  });
  timeTab($(root,'[data-tab="time"] .body'));
  dayTab($(root,'[data-tab="day"] .body'));
}

function timeTab(el){
  const D=SIM.doorstep, st={b:"condo",out:false};
  el.innerHTML=`
    <div class="variants">${Object.entries(D.buildings).map(([k,b])=>`<button data-b="${k}">${b.label}</button>`).join("")}
      <label class="check"><input type="checkbox"> Customer not at home</label></div>
    <div class="trip"></div>
    <div class="legend"><span><i class="sw drive"></i>Driving: what robots automate</span><span><i class="sw door"></i>Doorstep: needs judgement</span>
      <span><i class="sw cust"></i>Customer’s own time</span><span><i class="sw fail"></i>Failed attempt</span></div>
    <div class="readout"></div>`;
  $$(el,"[data-b]").forEach(b=>b.onclick=()=>{st.b=b.dataset.b;draw();});
  $(el,"input").onchange=e=>{st.out=e.target.checked;draw();};
  function bar(segs,max){
    return `<div class="bar">${segs.filter(s=>s[1]>0).map(([cls,m,lab])=>
      `<span class="seg ${cls}" style="width:${m/max*100}%" title="${lab}: ${m} min">${m/max*520>lab.length*6+10?lab:""}</span>`).join("")}</div>`;
  }
  function draw(){
    $$(el,"[data-b]").forEach(b=>b.classList.toggle("on",b.dataset.b===st.b));
    const b=D.buildings[st.b];
    const door=[["door",b.park,"Park"],["door",b.find,"Find block"],["door",b.guard,"Guard"],["door",b.lift,"Lift & unit"],["door",b.hand,"Hand over"]];
    if(st.out) door.push(["door",D.notHomeRider,"Call & reroute"]);
    const rider=[["drive",D.rideMin,"Ride"],...door];
    const robot=[["drive",D.robotRideMin,"Robot drive"],["cust",b.custWalk,"Customer walks"]];
    if(st.out) robot.splice(1,1,["fail",D.notHomeRobotWait,"Waits, then returns"]);
    const tot=a=>a.reduce((s,x)=>s+x[1],0), rT=tot(rider), oT=tot(robot), max=Math.max(rT,oT,30);
    const doorMin=rT-D.rideMin;
    el.querySelector(".trip").innerHTML=`
      <div class="row"><b>Rider</b>${bar(rider,max)}<span class="mins">${rT} min</span></div>
      <div class="row"><b>Robot</b>${bar(robot,max)}<span class="mins">${oT} min</span></div>`;
    el.querySelector(".readout").innerHTML=`
      <div class="kpi"><b>${pct(D.rideMin/rT)}</b><span>of the rider’s trip is driving, the only part a robot takes over</span></div>
      <div class="kpi"><b>${doorMin} min</b><span>at the doorstep, where riders use judgement</span></div>
      <div class="kpi ${st.out?"bad":""}"><b>${st.out?"Failed":b.custWalk+" min"}</b><span>${st.out
        ? "robot waits, then heads back. The rider called and rerouted instead"
        : "the customer walks to meet a robot that stops "+b.robotStops}</span></div>`;
  }
  draw();
}

function dayTab(el){
  const D=SIM.demand, st={day:"normal",fleet:D.fleet,cost:D.robotDayCost};
  el.innerHTML=`
    <div class="variants">${Object.entries(D.days).map(([k,d])=>`<button data-d="${k}">${d.label}</button>`).join("")}</div>
    <div class="daygrid">
      <canvas height="150"></canvas>
      <div class="dayout"></div>
    </div>
    <div class="controls">
      <label for="fleet">Robot fleet size</label><div class="rng"><input id="fleet" type="range" min="10" max="160" step="5" value="${st.fleet}"><span class="val fleetv"></span></div>
      <label for="rcost">Cost per robot per day</label><div class="rng"><input id="rcost" type="range" min="20" max="150" step="5" value="${st.cost}"><span class="val costv"></span></div>
    </div>`;
  const cv=$(el,"canvas");
  $$(el,"[data-d]").forEach(b=>b.onclick=()=>{st.day=b.dataset.d;draw();});
  $(el,"#fleet").oninput=e=>{st.fleet=+e.target.value;draw();};
  $(el,"#rcost").oninput=e=>{st.cost=+e.target.value;draw();};
  function calc(){
    const dy=D.days[st.day];
    const d=D.hourly.map(v=>Math.round(v*(v>=D.surgeAbove?dy.peak:dy.off)));
    const cap=st.fleet*D.robotPerHour, total=d.reduce((a,b)=>a+b,0);
    const riderHr=v=>v*(D.riderPay+(v>=D.surgeAbove?D.riderSurge:0));
    const riderCost=d.reduce((s,v)=>s+riderHr(v),0);
    const served=d.reduce((s,v)=>s+Math.min(v,cap),0), missed=total-served;
    const fleetCost=st.fleet*st.cost+D.robotPerDrop*served;
    const overflow=d.reduce((s,v)=>s+Math.max(0,v-cap)*(D.riderPay+D.riderSurge),0);
    return {d,cap,total,served,missed,util:served/(cap*24),
      rider:riderCost/total, robot:fleetCost/served, mix:(fleetCost+overflow)/total};
  }
  function draw(){
    $$(el,"[data-d]").forEach(b=>b.classList.toggle("on",b.dataset.d===st.day));
    $(el,".fleetv").textContent=st.fleet+" robots"; $(el,".costv").textContent="S$"+st.cost;
    const r=calc();
    const {g,w,h}=setupCanvas(cv,150), x0=28, x1=w-6, y0=h-18, top=12, bw=(x1-x0)/24;
    const vmax=Math.max(220,...r.d)*1.02, Y=v=>y0-(v/vmax)*(y0-top);
    g.clearRect(0,0,w,h);
    g.font="10px Calibri,Carlito,sans-serif"; g.fillStyle="#6b7280"; g.textAlign="right"; g.textBaseline="middle";
    [0,100,200].forEach(v=>{ g.fillText(v,x0-4,Y(v)); g.strokeStyle="#e5e7eb"; g.beginPath(); g.moveTo(x0,Y(v)); g.lineTo(x1,Y(v)); g.stroke(); });
    r.d.forEach((v,i)=>{
      const x=x0+i*bw+1.5, cw=bw-3, s=Math.min(v,r.cap);
      g.fillStyle="#1f2a44"; g.fillRect(x,Y(s),cw,y0-Y(s));
      if(v>r.cap){ g.fillStyle="#b93a3a"; g.fillRect(x,Y(v),cw,Y(s)-Y(v)); }
    });
    g.strokeStyle="#e8a33d"; g.lineWidth=2; g.setLineDash([5,3]); g.beginPath(); g.moveTo(x0,Y(r.cap)); g.lineTo(x1,Y(r.cap)); g.stroke(); g.setLineDash([]);
    g.fillStyle="#9a6b1e"; g.textAlign="left"; g.textBaseline="bottom"; g.font="bold 10.5px Calibri,Carlito,sans-serif";
    g.fillText("Robot fleet capacity",x0+4,Y(r.cap)-2);
    g.fillStyle="#6b7280"; g.font="10px Calibri,Carlito,sans-serif"; g.textAlign="center"; g.textBaseline="top";
    [0,6,12,18].forEach(hr=>g.fillText(hr===12?"noon":hr===0?"12am":hr<12?hr+"am":(hr-12)+"pm",x0+hr*bw+bw/2,y0+4));
    const best=Math.min(r.rider,r.mix);
    $(el,".dayout").innerHTML=`
      <h4>COST PER ORDER · ${r.total} ORDERS</h4>
      <div class="stat ${r.rider<=best?"best":""}"><span>Riders only</span><b>${money(r.rider)}</b></div>
      <div class="stat"><span>Robots only (orders served)</span><b>${money(r.robot)}</b></div>
      <div class="stat miss"><span>…but orders missed</span><b>${r.missed}</b></div>
      <div class="stat ${r.mix<best+1e-9&&r.mix<r.rider?"best":""}"><span>Robots + riders for overflow</span><b>${money(r.mix)}</b></div>
      <hr>
      <div class="stat"><span>Robot fleet busy</span><b>${pct(r.util)}</b></div>
      <p class="note">${r.missed>0 ? `<i class="sw fail"></i> Red = orders above what the fleet can carry. Riders absorb them anyway.`
        : `The fleet covers the peak but sits idle ${pct(1-r.util)} of the day.`}</p>`;
  }
  draw();
  addEventListener("resize",draw);
}

/* ================= slide 3: cheapest capable mode ================= */
function dispatchWidget(root){
  const D=SIM.dispatch, st={riderCost:D.riderCost,robotCost:D.robotCost,rules:D.rules,build:D.build};
  const RANGES={robotCost:[1,10,0.25],rules:[0,1,0.05],build:[0,1,0.05],riderCost:[3,10,0.25]};
  const body=$(root,".body");
  const sl=$$(root,".sliders [data-s]");
  sl.forEach(row=>{
    const k=row.dataset.s, [mn,mx,step]=RANGES[k];
    row.querySelector(".rng").innerHTML=`<input type="range" min="${mn}" max="${mx}" step="${step}" aria-label="${row.textContent.trim()}"><span class="val"></span>`;
    row.querySelector("input").oninput=e=>{st[k]=+e.target.value;draw();};
  });
  $$(root,".presets button").forEach(b=>b.onclick=()=>{
    Object.assign(st, b.dataset.p==="future"? D.future : {riderCost:D.riderCost,robotCost:D.robotCost,rules:D.rules,build:D.build});
    draw();
  });
  body.innerHTML=`<table class="dtab"><thead><tr><th>Order type</th><th>Share</th><th>Rider</th><th>Robot</th><th>Goes to</th></tr></thead><tbody></tbody></table>
    <div class="share"><div class="sbar"><span class="rob"></span></div><span class="stext"></span></div>`;
  function draw(){
    sl.forEach(row=>{
      const k=row.dataset.s, v=st[k];
      row.querySelector("input").value=v;
      row.querySelector(".val").textContent= k==="rules"||k==="build" ? pct(v) : money(v);
    });
    const isFuture=Object.keys(D.future).every(k=>Math.abs(st[k]-D.future[k])<1e-9);
    const isToday=["riderCost","robotCost","rules","build"].every(k=>Math.abs(st[k]-D[k])<1e-9);
    $$(root,".presets button").forEach(b=>b.classList.toggle("on",b.dataset.p==="future"?isFuture:isToday));
    let robotVol=0, totVol=0;
    body.querySelector("tbody").innerHTML=D.orders.map(o=>{
      const rc=st.riderCost*o.rider;
      let why=o.never||"", oc=null;
      if(!why){
        if(st.rules<o.rules) why="rules don’t allow it yet";
        else if(st.build<o.build) why="building not robot ready";
        else oc=st.robotCost*o.robot;
      }
      const robot=oc!=null && oc<rc;
      totVol+=o.vol; if(robot) robotVol+=o.vol;
      return `<tr class="${robot?"isrobot":""}"><td>${o.name}</td><td class="num">${o.vol}%</td><td class="num">${money(rc)}</td>
        <td class="num ${oc==null?"why":""}">${oc==null?why:money(oc)}</td>
        <td><span class="chip ${robot?"robot":"rider"}">${robot?"Robot":"Rider"}</span></td></tr>`;
    }).join("");
    const share=robotVol/totVol;
    body.querySelector(".rob").style.width=pct(share);
    body.querySelector(".stext").innerHTML=`<b>${pct(share)}</b> of orders go to robots, <b>${pct(1-share)}</b> stay with riders`;
  }
  draw();
}
"""

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OPIM639 · Week 6 Discussion Assignment · Group 3</title>
<script id="baked-edits" type="application/json">{}</script>
<style>
:root{
  --navy:#1f2a44; --amber:#e8a33d; --amber-soft:#fbe9d0; --amber-ink:#9a6b1e; --ink:#23272f; --body:#374151;
  --muted:#6b7280; --line:#e5e7eb; --soft:#f3f4f6; --red:#b93a3a; --blue:#2563eb; --green:#2f855a;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#15171c;overflow:hidden;
  font:15px/1.4 Calibri,Carlito,"Segoe UI",system-ui,sans-serif;color:var(--body)}
#viewport{position:fixed;inset:0}
#stage{position:absolute;left:0;top:0;width:1280px;height:720px;transform-origin:0 0;background:#fff;overflow:hidden;
  box-shadow:0 10px 40px rgba(0,0,0,.45)}
.slide{position:absolute;inset:0;display:none}
.slide.on{display:block}

/* ---------- title slide ---------- */
.title{background:var(--navy);color:#fff}
.title .ttext{position:absolute;left:96px;top:50%;transform:translateY(-50%);max-width:760px}
.title .course{margin:0;font-size:24px;font-weight:700;letter-spacing:.14em;color:var(--amber)}
.title h1{margin:6px 0 0;font-size:56px;line-height:1.1;font-weight:700}
.title .topic{margin:14px 0 0;font-size:22px;color:#cbd2e0}
.title .rule{width:96px;height:4px;background:var(--amber);margin:30px 0 26px}
.title .group{margin:0 0 8px;font-size:22px;font-weight:700;color:#cbd2e0}
.title .names{list-style:none;margin:0;padding:0;font-size:26px;line-height:1.45}
.title .art{position:absolute;right:0;top:0;bottom:0;width:430px;opacity:.95}

/* ---------- content slides ---------- */
.content{padding:18px 40px 0}
.kicker{margin:0;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--amber-ink)}
h2{font-size:27px;line-height:1.14;color:var(--ink);margin:4px 0 4px;max-width:1100px}
.sub{margin:0 0 4px;font-size:15px;color:var(--body)}
.grid{display:grid;grid-template-columns:500px 1fr;gap:28px;align-items:start;margin-top:14px}
.points{display:flex;flex-direction:column;gap:20px}
.point{display:flex;gap:12px}
.point .ico{flex:none;width:32px;height:32px;border-radius:50%;background:var(--navy);color:#fff;display:grid;place-items:center}
.point .ico svg{width:17px;height:17px}
.point h3{margin:0 0 3px;font-size:16px;line-height:1.2;color:var(--ink)}
.point p{margin:0;font-size:13.5px;line-height:1.38}
.s3 .points{gap:24px}

.explainer{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);padding:9px 14px 10px}
.exhead{display:flex;gap:10px;align-items:center;margin-bottom:7px}
.tag{flex:none;background:var(--navy);color:#fff;font-size:10.5px;font-weight:700;border-radius:999px;padding:2px 10px}
.ex-title{font-weight:700;letter-spacing:.05em;color:var(--muted);font-size:12px;text-transform:uppercase}
.tabs{display:flex;gap:0;border-bottom:1px solid var(--line);margin-bottom:6px}
.tabs [data-tab]{cursor:pointer;padding:4px 12px 5px;font-size:13px;font-weight:700;color:var(--muted);border-bottom:3px solid transparent;margin-bottom:-1px}
.tabs [data-tab].on{color:var(--navy);border-bottom-color:var(--amber)}
.tabpane{display:none}.tabpane.on{display:block}
.caption{margin:0 0 6px;font-size:12.5px;color:var(--body);line-height:1.33}
.variants{display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-bottom:6px}
.variants button,.presets button{font:inherit;font-size:12.5px;padding:2px 9px;border:1px solid var(--navy);background:#fff;color:var(--navy);border-radius:5px;cursor:pointer}
.variants button.on,.presets button.on{background:var(--navy);color:#fff}
.check{font-size:12.5px;color:var(--ink);display:flex;gap:4px;align-items:center;margin-left:6px;cursor:pointer}
.check input{accent-color:var(--red);margin:0}
button:focus-visible,input:focus-visible{outline:2px solid var(--blue);outline-offset:2px}

.trip .row{display:grid;grid-template-columns:44px 1fr 52px;gap:8px;align-items:center;margin:8px 0}
.trip .row b{font-size:13px;color:var(--ink)}
.trip .mins{font:600 12.5px var(--mono);color:var(--ink);text-align:right}
.bar{display:flex;height:32px;background:var(--soft);border-radius:4px;overflow:hidden}
.seg{display:flex;align-items:center;justify-content:center;font-size:11px;color:#fff;white-space:nowrap;overflow:hidden;border-right:1px solid #fff;transition:width .35s}
.seg.drive,.sw.drive{background:var(--blue)}
.seg.door,.sw.door{background:var(--amber);color:#3d2a08}
.seg.cust,.sw.cust{background:repeating-linear-gradient(45deg,#9ca3af 0 5px,#c5cad3 5px 10px);color:#1f2937}
.seg.fail,.sw.fail{background:var(--red)}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:11.5px;color:var(--muted);margin:4px 0 8px 52px}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}
.readout{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.kpi{background:var(--soft);border-radius:6px;padding:6px 9px}
.kpi b{display:block;font:700 19px var(--mono);color:var(--ink)}
.kpi span{font-size:11.5px;line-height:1.25;display:block}
.kpi.bad b{color:var(--red)}
@media (prefers-reduced-motion:reduce){.seg{transition:none}}

.daygrid{display:grid;grid-template-columns:1fr 200px;gap:12px}
canvas{width:100%;display:block;background:var(--soft);border-radius:6px}
.dayout{border-left:1px solid var(--line);padding-left:11px;font-size:12.5px;line-height:1.3}
.dayout h4,.sliders h4{margin:0 0 4px;font-size:10.5px;letter-spacing:.05em;color:var(--muted)}
.stat{display:flex;justify-content:space-between;align-items:baseline;margin:2px 0;gap:6px}
.stat b{font:600 13px var(--mono);color:var(--ink);white-space:nowrap}
.stat.best b,.stat.best span{color:var(--green);font-weight:700}
.stat.miss span,.stat.miss b{color:var(--red)}
.dayout hr{border:0;border-top:1px solid var(--line);margin:5px 0}
.note{font-size:11.5px;color:var(--muted);margin:4px 0 0;line-height:1.3}
.controls{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;align-items:center;margin-top:7px;font-size:12.5px}
.controls label{color:var(--ink);font-weight:600;white-space:nowrap}
.rng{display:flex;gap:8px;align-items:center}
.rng input[type=range]{flex:1;accent-color:var(--amber);height:16px;margin:0;min-width:0}
.rng .val{font:11.5px var(--mono);min-width:70px;text-align:right;color:var(--ink)}

.dtab{width:100%;border-collapse:collapse;font-size:12px}
.dtab th{text-align:left;font-size:10.5px;letter-spacing:.04em;color:var(--muted);font-weight:700;padding:0 6px 3px;border-bottom:1px solid var(--line)}
.dtab td{padding:1.5px 6px;border-bottom:1px solid var(--line);color:var(--ink)}
.dtab td.num,.dtab th:nth-child(n+2){text-align:right}
.dtab th:last-child,.dtab td:last-child{text-align:center}
.dtab td.num{font-family:var(--mono);font-size:11.5px}
.dtab td.why{font-family:inherit;color:var(--muted);font-style:italic;font-size:11.5px}
.dtab tr.isrobot td{background:#eef3ff}
.chip{display:inline-block;min-width:50px;padding:1px 8px;border-radius:999px;font-size:11px;font-weight:700}
.chip.rider{background:var(--amber-soft);color:var(--amber-ink)}
.chip.robot{background:var(--blue);color:#fff}
.share{display:flex;gap:10px;align-items:center;margin:7px 0 2px;font-size:12.5px}
.sbar{flex:0 0 160px;height:12px;border-radius:999px;background:var(--amber);overflow:hidden}
.sbar .rob{display:block;height:100%;background:var(--blue);transition:width .35s}
.sliders{margin-top:8px;border-top:1px solid var(--line);padding-top:7px}
.sliders .hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px}
.sliders .hd h4{margin:0}
.presets{display:flex;gap:5px;white-space:nowrap}
.srow{display:grid;grid-template-columns:300px 1fr;gap:10px;align-items:center;font-size:12.5px;margin:2px 0}
.srow label{color:var(--ink);font-weight:600}

.view{margin-top:10px;background:var(--navy);color:#fff;border-radius:9px;padding:10px 16px 11px;font-size:13px;line-height:1.38}
.view .vk{margin:0 0 3px;color:var(--amber);font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:12px}
.view .vl{margin:0 0 4px;font-size:15px;font-weight:700;line-height:1.3}
.view .vb{margin:0;color:#dfe4ee}
.foot{position:absolute;left:40px;right:40px;bottom:9px;display:flex;justify-content:space-between;font-size:11px;color:var(--muted)}
.assume{font-style:italic}

/* ---------- speaker notes ---------- */
.notes{display:none;position:absolute;left:0;right:0;bottom:0;max-height:46%;overflow:auto;background:rgba(20,22,28,.96);color:#e5e7eb;
  padding:14px 40px 34px;font-size:14px;line-height:1.5;z-index:3}
.notes .nk{margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.12em;color:var(--amber)}
.notes p{margin:0;white-space:pre-wrap}
body.shownotes .notes{display:block}

/* ---------- edit mode ---------- */
body.editing [data-k]{outline:1px dashed rgba(37,99,235,.55);outline-offset:2px;cursor:text;border-radius:2px}
body.editing [data-k]:hover{background:rgba(37,99,235,.06)}
body.editing [data-k]:focus{outline:2px solid var(--blue);background:rgba(37,99,235,.08)}
body.editing .title [data-k]:hover,body.editing .view [data-k]:hover,body.editing .notes [data-k]:hover{background:rgba(255,255,255,.08)}
[data-k].edited{box-shadow:inset 3px 0 0 -1px transparent}

/* ---------- presenter toolbar (outside the slide) ---------- */
#toolbar{position:fixed;left:50%;bottom:14px;transform:translateX(-50%);display:flex;gap:4px;align-items:center;
  background:rgba(20,22,28,.86);color:#fff;border-radius:999px;padding:5px 8px;font-size:13px;transition:opacity .3s;z-index:5;white-space:nowrap}
#toolbar button{all:unset;cursor:pointer;padding:4px 10px;border-radius:999px}
#toolbar button:hover,#toolbar button:focus-visible{background:rgba(255,255,255,.18)}
#toolbar button.on{background:var(--amber);color:#1f2a44;font-weight:700}
#toolbar .count{min-width:44px;text-align:center;font-variant-numeric:tabular-nums}
#toolbar .sep{width:1px;height:16px;background:rgba(255,255,255,.25);margin:0 4px}
#toolbar .editonly{display:none}
body.editing #toolbar .editonly{display:inline-block}
body.idle:not(.editing) #toolbar{opacity:0}
#toast{position:fixed;left:50%;top:14px;transform:translateX(-50%);background:var(--navy);color:#fff;padding:6px 14px;border-radius:8px;font-size:13px;
  opacity:0;transition:opacity .3s;pointer-events:none;z-index:6}
#toast.on{opacity:1}
@media (prefers-reduced-motion:reduce){#toolbar,#toast{transition:none}}
</style>
</head>
<body>
<div id="viewport"><div id="stage">__SLIDES__</div></div>
<div id="toolbar" role="toolbar" aria-label="Slide controls">
  <button id="prev" aria-label="Previous slide">◀</button><span class="count" id="count"></span>
  <button id="next" aria-label="Next slide">▶</button><span class="sep"></span>
  <button id="notesb" title="Speaker notes (N)">Notes</button>
  <button id="editb" title="Edit text (E)">✎ Edit</button>
  <button id="dl" class="editonly" title="Save a copy with your edits built in">⤓ Download</button>
  <button id="reset" class="editonly" title="Undo all edits made in this browser">Reset</button>
  <span class="sep"></span><button id="fs" aria-label="Full screen">⛶ Full screen</button>
</div>
<div id="toast" role="status"></div>
<script>
const PRISTINE = "<!doctype html>\n" + document.documentElement.outerHTML;
const SIM = __SIM__;
const slides=[...document.querySelectorAll(".slide")];
const stage=document.getElementById("stage");
let cur=0, SCALE=1;

function fit(){
  // scale the fixed 1280x720 slide to the largest size that fits, and centre it
  const W=document.documentElement.clientWidth||innerWidth, H=document.documentElement.clientHeight||innerHeight;
  SCALE=Math.min(W/1280, H/720);
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
  dispatchEvent(new Event("resize"));
}
document.getElementById("next").onclick=()=>go(cur+1);
document.getElementById("prev").onclick=()=>go(cur-1);
const toggleFS=()=>{ try{ const p=document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen?.(); p&&p.catch&&p.catch(()=>{}); }catch(e){} };
document.getElementById("fs").onclick=toggleFS;
if(!document.fullscreenEnabled) document.getElementById("fs").style.display="none";   // not allowed in embedded previews

/* ---------- editing: click any text in edit mode; saved per browser, Download bakes it in ---------- */
const STORE="opim639-week6-edits";
const toast=m=>{const t=document.getElementById("toast"); t.textContent=m; t.classList.add("on"); clearTimeout(toast.h); toast.h=setTimeout(()=>t.classList.remove("on"),2200);};
let edits={};
try{ edits=JSON.parse(document.getElementById("baked-edits").textContent||"{}"); }catch(e){}
try{ Object.assign(edits, JSON.parse(localStorage.getItem(STORE)||"{}")); }catch(e){}
function applyEdits(){ document.querySelectorAll("[data-k]").forEach(el=>{ if(edits[el.dataset.k]!=null) el.textContent=edits[el.dataset.k]; }); }
function saveEdits(){ try{ localStorage.setItem(STORE, JSON.stringify(edits)); }catch(e){} }
function setEditing(on){
  document.body.classList.toggle("editing",on);
  document.getElementById("editb").classList.toggle("on",on);
  document.querySelectorAll("[data-k]").forEach(el=>{ if(on) el.setAttribute("contenteditable","true"); else el.removeAttribute("contenteditable"); });
  if(!on && document.activeElement && document.activeElement.blur) document.activeElement.blur();
  toast(on?"Edit mode: click any text to change it":"Edits saved in this browser");
}
document.getElementById("editb").onclick=()=>setEditing(!document.body.classList.contains("editing"));
document.addEventListener("input",e=>{ const el=e.target.closest&&e.target.closest("[data-k]"); if(!el) return; edits[el.dataset.k]=el.innerText.replace(/\n+$/,""); saveEdits(); });
document.addEventListener("paste",e=>{ if(!e.target.closest||!e.target.closest("[data-k]")) return; e.preventDefault();
  document.execCommand("insertText",false,(e.clipboardData||window.clipboardData).getData("text/plain")); });
document.addEventListener("keydown",e=>{ const el=e.target.closest&&e.target.closest("[data-k]");
  if(el && e.key==="Enter" && !el.closest(".notes")){ e.preventDefault(); el.blur(); }
  if(el && e.key==="Escape") el.blur(); }, true);
document.getElementById("dl").onclick=()=>{
  const json=JSON.stringify(edits).replace(/</g,"\\u003c");
  const out=PRISTINE.replace(/(<script id="baked-edits" type="application\/json">)[\s\S]*?(<\/script>)/, (m,a,b)=>a+json+b);
  const a=document.createElement("a"); a.href=URL.createObjectURL(new Blob([out],{type:"text/html"}));
  a.download="opim639_week6_explainer_edited.html"; document.body.appendChild(a); a.click(); a.remove();
  toast("Downloaded a copy with your edits built in");
};
document.getElementById("reset").onclick=()=>{ if(!confirm("Undo every edit made in this browser?")) return;
  try{ localStorage.removeItem(STORE); }catch(e){} location.reload(); };
document.getElementById("notesb").onclick=()=>{ document.body.classList.toggle("shownotes"); document.getElementById("notesb").classList.toggle("on"); };

document.addEventListener("keydown",e=>{
  if(e.target.isContentEditable) return;
  if(e.target.tagName==="INPUT" && ["ArrowLeft","ArrowRight"].includes(e.key)) return;
  if(["ArrowRight","PageDown"," "].includes(e.key) && e.target.tagName!=="BUTTON"){e.preventDefault();go(cur+1);}
  else if(["ArrowLeft","PageUp"].includes(e.key)){e.preventDefault();go(cur-1);}
  else if(e.key==="Home")go(0); else if(e.key==="End")go(slides.length-1);
  else if((e.key==="f"||e.key==="F") && document.fullscreenEnabled)toggleFS();
  else if(e.key==="e"||e.key==="E") document.getElementById("editb").click();
  else if(e.key==="n"||e.key==="N") document.getElementById("notesb").click();
});
let idle; const wake=()=>{document.body.classList.remove("idle");clearTimeout(idle);idle=setTimeout(()=>document.body.classList.add("idle"),2500);};
addEventListener("mousemove",wake); addEventListener("keydown",wake); wake();

__ENGINE__
const WIDGETS={edge:edgeWidget,dispatch:dispatchWidget};
document.querySelectorAll("[data-widget]").forEach(el=>WIDGETS[el.dataset.widget](el));
applyEdits();
let start=0; try{ start=(parseInt(location.hash.slice(1))||1)-1; }catch(e){}
go(Math.max(0,start));
</script>
</body>
</html>
"""


def icon(name: str) -> str:
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def ed(key: str, text: str, tag: str = "span", cls: str = "") -> str:
    """An element whose text can be changed in the browser's edit mode."""
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-k="{key}">{esc(text)}</{tag}>'


def render_title() -> str:
    t = TITLE
    names = "".join(ed(f"t.m{i}", m, "li") for i, m in enumerate(t["members"]))
    # a quiet line drawing: a route from hub to door, with a rider and a robot on it
    art = """<svg class="art" viewBox="0 0 430 720" fill="none" aria-hidden="true">
      <path d="M60 690 C 60 520, 330 560, 320 400 S 120 250, 250 90" stroke="#e8a33d" stroke-width="3" stroke-dasharray="2 12" stroke-linecap="round"/>
      <circle cx="60" cy="690" r="9" fill="#e8a33d"/>
      <g stroke="#cbd2e0" stroke-width="2.5" stroke-linejoin="round">
        <path d="M200 50h100v120H200z"/><path d="M200 50l50-32 50 32"/><path d="M238 170v-38h24v38"/>
        <path d="M222 78h16M262 78h16M222 104h16M262 104h16"/>
      </g>
      <g transform="translate(290 380)" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="0" cy="40" r="13"/><circle cx="58" cy="40" r="13"/><path d="M0 40l18-30h26l14 30"/><path d="M30 10l-6-16h-10"/>
        <rect x="34" y="-18" width="26" height="22" rx="3" fill="#e8a33d" stroke="#e8a33d"/>
      </g>
      <g transform="translate(96 560)" stroke="#8fa0c0" stroke-width="2.5" stroke-linejoin="round">
        <rect x="0" y="0" width="54" height="36" rx="8"/><circle cx="12" cy="44" r="7"/><circle cx="42" cy="44" r="7"/>
        <path d="M27 0v-14"/><circle cx="27" cy="-17" r="3"/>
      </g>
    </svg>"""
    return f"""
<section class="slide title" aria-label="Title">
  <div class="ttext">
    {ed("t.course", t['course'], "p", "course")}
    {ed("t.subtitle", t['subtitle'], "h1")}
    {ed("t.topic", t['topic'], "p", "topic")}
    <div class="rule"></div>
    {ed("t.group", t['group'], "p", "group")}
    <ul class="names">{names}</ul>
  </div>
  {art}
</section>"""


def render_points(s: dict) -> str:
    k = s["key"]
    return "".join(
        f'<div class="point"><span class="ico">{icon(ic)}</span><div>'
        f'{ed(f"{k}.p{i}.t", t, "h3")}{ed(f"{k}.p{i}.b", b, "p")}</div></div>'
        for i, (ic, t, b) in enumerate(s["points"]))


def render_view(s: dict) -> str:
    k = s["key"]
    return (f'<div class="view">{ed(f"{k}.vk", s["view_kicker"], "p", "vk")}'
            f'{ed(f"{k}.vl", s["view_lead"], "p", "vl")}{ed(f"{k}.vb", s["view_body"], "p", "vb")}</div>')


def render_explainer(s: dict) -> str:
    k = s["key"]
    head = (f'<div class="exhead"><span class="tag">● INTERACTIVE EXPLAINER</span>'
            f'{ed(f"{k}.ex", s["explainer_title"], "span", "ex-title")}</div>')
    if s["widget"] == "edge":
        tabs = "".join(f'<div role="tab" tabindex="0" data-tab="{tid}" class="{"on" if i == 0 else ""}">'
                       f'{ed(f"{k}.tab{i}", name)}</div>' for i, (tid, name, _) in enumerate(s["tabs"]))
        panes = "".join(f'<div class="tabpane {"on" if i == 0 else ""}" data-tab="{tid}">'
                        f'{ed(f"{k}.cap{i}", cap, "p", "caption")}<div class="body"></div></div>'
                        for i, (tid, _, cap) in enumerate(s["tabs"]))
        inner = f'<div class="tabs" role="tablist">{tabs}</div>{panes}'
    else:
        rows = "".join(f'<div class="srow" data-s="{sk}">{ed(f"{k}.sl{i}", lab, "label")}<div class="rng"></div></div>'
                       for i, (sk, lab) in enumerate(s["sliders"]))
        inner = (f'<div class="body"></div><div class="sliders"><div class="hd">'
                 f'{ed(f"{k}.cap", s["caption"], "h4")}'
                 f'<div class="presets"><button data-p="today">Today</button><button data-p="future">Signposts move</button></div>'
                 f'</div>{rows}</div>')
    return f'<div class="explainer" data-widget="{s["widget"]}">{head}{inner}</div>'


def render_slide(page: int, s: dict) -> str:
    k = s["key"]
    sub = ed(f"{k}.sub", s["sub"], "p", "sub") if s.get("sub") else ""
    return f"""
<section class="slide content {k}" aria-label="Slide {page}">
  {ed(f"{k}.kicker", s['kicker'], "p", "kicker")}
  {ed(f"{k}.h", s['headline'], "h2")}
  {sub}
  <div class="grid">
    <div class="points">{render_points(s)}</div>
    <div class="right">{render_explainer(s)}{render_view(s)}</div>
  </div>
  <div class="foot"><span>OPIM639 · Week 6 Discussion Assignment · Group 3 · <span class="assume">explainer figures are illustrative assumptions</span></span><span>{page}</span></div>
  <div class="notes"><p class="nk">SPEAKER NOTES</p>{ed(f"{k}.notes", s['notes'], "p")}</div>
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
