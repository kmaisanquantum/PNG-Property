import { useState, useEffect, useCallback, useRef } from "react";
import Landing from "./Landing";

// ── API BASE ──────────────────────────────────────────────────────────────────
// Render: VITE_API_URL is set to the backend Web Service URL in Render dashboard
const API = import.meta.env.VITE_API_URL || "/api";

async function apiFetch(path, opts = {}) {
  const token = localStorage.getItem("png_token");
  const headers = { ...opts.headers };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const r = await fetch(`${API}${path}`, { ...opts, headers });
    if (!r.ok) {
      if (r.status === 401) {
        localStorage.removeItem("png_token");
        localStorage.removeItem("png_user");
      }
      throw new Error(`${r.status}`);
    }
    return r.json();
  } catch {
    return null;
  }
}

// ── MOCK DATA (used when backend is offline) ──────────────────────────────────
const SUBURBS = ["Waigani","Boroko","Gerehu","Gordons","Hohola","Tokarara","Koki","Badili","Six Mile","Eight Mile"];
const SOURCES = ["Hausples","The Professionals","Ray White PNG","Century 21 PNG","MarketMeri","Facebook Marketplace","SRE PNG"];
const TYPES   = ["House","Apartment","Townhouse","Studio","Room","Compound"];

function randRange(lo, hi) { return Math.floor(Math.random() * (hi - lo)) + lo; }

function mockListings(n = 80) {
  const benchmarks = {Waigani:4470,Boroko:3150,Gerehu:1880,Gordons:5957,Hohola:1600,Tokarara:2275,Koki:2900,Badili:3325,"Six Mile":1450,"Eight Mile":1225};
  return Array.from({length:n}, (_,i) => {
    const suburb = SUBURBS[i % SUBURBS.length];
    const src    = SOURCES[i % SOURCES.length];
    const ptype  = TYPES[i % TYPES.length];
    const beds   = ptype === "Studio" ? 1 : randRange(1,5);
    const base   = benchmarks[suburb] || 2500;
    const price  = Math.max(800, Math.round(base * (0.75 + Math.random() * 0.6)));
    const avg    = base;
    const pct    = ((price - avg) / avg) * 100;
    const mv     = pct <= -15 ? {label:"Deal",color:"#4ade80",pct_vs_avg:pct} : pct >= 15 ? {label:"Overpriced",color:"#f87171",pct_vs_avg:pct} : {label:"Fair",color:"#facc15",pct_vs_avg:pct};
    return {
      listing_id:      `mock-${i}`,
      source_site:     src,
      title:           `${beds} Bedroom ${ptype} – ${suburb}`,
      price_raw:       `K${price.toLocaleString()}/month`,
      price_monthly_k: price,
      price_confidence:"high",
      location:        `${suburb}, NCD`,
      suburb,
      listing_url:     `#listing-${i}`,
      is_verified:     src !== "Facebook Marketplace",
      property_type:   ptype,
      bedrooms:        beds,
      scraped_at:      new Date(Date.now() - randRange(0,86400000*3)).toISOString(),
      market_value:    mv,
    };
  });
}

const MOCK_OVERVIEW = {total_listings:240,verified_listings:198,avg_rent_pgk:2847,median_rent_pgk:2500,middleman_flags:17,sources_active:10,suburbs_tracked:12,last_scraped:new Date().toISOString()};
const MOCK_HEATMAP  = {suburbs:SUBURBS.map(s=>({suburb:s,avg_price:({Waigani:4470,Boroko:3150,Gerehu:1880,Gordons:5957,Hohola:1600,Tokarara:2275,Koki:2900,Badili:3325,"Six Mile":1450,"Eight Mile":1225}[s]||2000),listings:randRange(15,75),lat:({Waigani:-9.4171,Boroko:-9.4701,Gerehu:-9.3870,Gordons:-9.4496,Hohola:-9.4533,Tokarara:-9.4343,Koki:-9.4785,Badili:-9.4743,"Six Mile":-9.4536,"Eight Mile":-9.4001}[s]||-9.44),lng:({Waigani:147.1808,Boroko:147.1992,Gerehu:147.1681,Gordons:147.1908,Hohola:147.1754,Tokarara:147.1663,Koki:147.1697,Badili:147.1749,"Six Mile":147.2076,"Eight Mile":147.2097}[s]||147.18)}))};
const MOCK_TRENDS   = {trends:["Jan 19","Jan 26","Feb 2","Feb 9","Feb 16","Feb 22"].map((w,i)=>({week:w,Waigani:4200+i*40+randRange(-80,80),Boroko:3000+i*25+randRange(-60,60),Gerehu:1750+i*20+randRange(-40,40)}))};
const MOCK_SD       = {data:SUBURBS.map(s=>({suburb:s,supply:randRange(15,75),demand_score:randRange(45,90),avg_price:({Waigani:4470,Boroko:3150,Gerehu:1880,Gordons:5957,Hohola:1600,Tokarara:2275,Koki:2900,Badili:3325,"Six Mile":1450,"Eight Mile":1225}[s]||2000)}))};
const MOCK_SOURCES  = {sources:SOURCES.map(s=>({name:s,count:randRange(10,60)}))};

// ── DESIGN TOKENS ─────────────────────────────────────────────────────────────
const C = {
  bg0:"#050d1a", bg1:"#091422", bg2:"#0d1e30", bg3:"#132437",
  border:"#162338", borderHi:"#1e3550",
  text0:"#f0f6ff", text1:"#8ba8c0", text2:"#4a6a80", text3:"#243545",
  teal:"#14b8c8", tealDim:"#0e8a96", tealGlow:"rgba(20,184,200,0.15)",
  amber:"#f59e0b", amberDim:"#b45309",
  green:"#22c55e", red:"#ef4444", violet:"#8b5cf6",
  deal:"#4ade80", fair:"#facc15", over:"#f87171",
};

// ── FONTS ─────────────────────────────────────────────────────────────────────
const FONTS = `
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&family=Barlow:wght@400;500;600&family=Bebas+Neue&family=Fraunces:ital,opsz,wght@0,9..144,100..900;1,9..144,100..900&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: ${C.bg0}; color: ${C.text0}; font-family: 'Barlow', sans-serif; overflow-x: hidden; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: ${C.bg1}; }
::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 2px; }
@keyframes fadeUp { from { opacity:0; transform:translateY(12px);} to { opacity:1; transform:none;} }
@keyframes pulse  { 0%,100%{opacity:1;} 50%{opacity:.35;} }
@keyframes spin   { to { transform: rotate(360deg); } }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.fade-up { animation: fadeUp .4s ease both; }
.kpi-card { transition: all 0.2s ease; cursor: pointer; }
.kpi-card:hover { transform: translateY(-3px); border-color: #14b8a6 !important; background: #0f172a !important; box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
.nav-btn { transition: all 0.2s ease; }
.nav-btn:hover { background: #0f172a !important; color: #14b8a6 !important; border-color: #14b8a6 !important; }
.scrape-btn { transition: all 0.2s ease; }
.scrape-btn:hover { transform: translateY(-1px); filter: brightness(1.1); box-shadow: 0 4px 12px rgba(20,184,166,0.3); }
.link-btn { color: #14b8a6; cursor: pointer; text-decoration: none; font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 4px; transition: gap 0.2s ease; }
.link-btn:hover { gap: 8px; color: #8b5cf6; }

@media (max-width: 768px) {
  .app-shell { flex-direction: column !important; }
  .sidebar-container {
    width: 100% !important; height: 64px !important;
    flex-direction: row !important; padding: 0 !important;
    border-right: none !important; border-top: 1px solid ${C.border} !important;
    order: 2; overflow-x: auto; -webkit-overflow-scrolling: touch;
  }
  .sidebar-logo { display: none !important; }
  .nav-items-wrapper {
    flex-direction: row !important; flex: 1;
    justify-content: flex-start !important;
    padding: 0 12px !important; gap: 8px !important;
  }
  .sidebar-spacer { display: none !important; }
  .logout-btn { display: none !important; }
  .live-indicator { display: none !important; }
  .main-content { height: calc(100vh - 64px) !important; order: 1; }
  .topbar { padding: 0 12px !important; }
  .location-tag, .updated-tag { display: none !important; }
  .user-info { display: flex !important; flex-direction: row !important; align-items: center !important; gap: 8px !important; margin-right: 0 !important; }
  .user-info div { display: none !important; }
  .user-info button { font-size: 11px !important; padding: 4px 8px !important; border: 1px solid ${C.red}44 !important; border-radius: 4px !important; }
  .scrape-text { display: none !important; }
  .scrape-btn { padding: 8px !important; }
  .dashboard-grid-row { grid-template-columns: 1fr !important; }
}
`;

// ── TINY UTILITIES ────────────────────────────────────────────────────────────
const fmt   = n => n != null ? `K${Number(n).toLocaleString()}` : "—";
const rel   = iso => { const d=(Date.now()-new Date(iso))/1000; return d<60?"just now":d<3600?`${Math.floor(d/60)}m ago`:d<86400?`${Math.floor(d/3600)}h ago`:`${Math.floor(d/86400)}d ago`; };
const clamp = (v,lo,hi) => Math.max(lo,Math.min(hi,v));

// ── PRICE → COLOR ─────────────────────────────────────────────────────────────
function priceColor(price, lo=1000, hi=7000) {
  const t = clamp((price-lo)/(hi-lo),0,1);
  const lerp = (a,b) => Math.round(a+(b-a)*t);
  return `rgb(${lerp(32,200)},${lerp(190,70)},${lerp(160,45)})`;
}

// ── COMPONENTS ────────────────────────────────────────────────────────────────

function Badge({label, color, bg, small}) {
  return <span style={{display:"inline-flex",alignItems:"center",gap:4,background:bg||`${color}18`,color:color||C.text1,border:`1px solid ${color||C.border}44`,borderRadius:4,padding:small?"1px 6px":"3px 8px",fontSize:small?9:11,fontWeight:600,fontFamily:"'IBM Plex Mono',monospace",letterSpacing:"0.04em",whiteSpace:"nowrap"}}>{label}</span>;
}

function Pill({children, active, onClick}) {
  return <button onClick={onClick} style={{background:active?C.teal:C.bg3,border:`1px solid ${active?C.teal:C.border}`,borderRadius:20,padding:"4px 12px",color:active?C.bg0:C.text1,fontSize:12,fontWeight:600,cursor:"pointer",transition:"all .15s"}}>{children}</button>;
}

function Card({children, style={}, className="", ...props}) {
  return <div className={className} {...props} style={{background:C.bg1,border:`1px solid ${C.border}`,borderRadius:12,...style}}>{children}</div>;
}

function Spinner() {
  return <div style={{width:18,height:18,border:`2px solid ${C.border}`,borderTopColor:C.teal,borderRadius:"50%",animation:"spin .7s linear infinite",flexShrink:0}} />;
}

function HealthScore({score}) {
  const col = score > 80 ? C.green : score > 50 ? C.amber : C.red;
  return (
    <div style={{display:"flex", alignItems:"center", gap:6}}>
      <div style={{width:40, height:4, background:C.bg3, borderRadius:2, overflow:"hidden"}}>
        <div style={{width:`${score}%`, height:"100%", background:col}} />
      </div>
      <span style={{fontSize:10, color:col, fontWeight:700, fontFamily:"'IBM Plex Mono'"}}>{score}%</span>
    </div>
  );
}

function KpiCard({label, value, sub, accent, icon, delay=0, onClick}) {
  return <Card className={`fade-up ${onClick ? "kpi-card" : ""}`} onClick={onClick} style={{padding:"18px 20px",animationDelay:`${delay}ms`}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
      <div>
        <div style={{fontSize:10,color:C.text2,fontFamily:"'IBM Plex Mono',monospace",letterSpacing:"0.1em",marginBottom:6}}>{label}</div>
        <div style={{fontSize:28,fontWeight:800,fontFamily:"'Barlow Condensed',sans-serif",color:accent||C.text0,lineHeight:1}}>{value}</div>
        {sub && <div style={{fontSize:11,color:C.text2,marginTop:5}}>{sub}</div>}
      </div>
      <div style={{fontSize:20,opacity:.6}}>{icon}</div>
    </div>
  </Card>;
}

// ── SVG LINE CHART ────────────────────────────────────────────────────────────
function LineChart({trends}) {
  if (!trends?.length) return <div style={{height:160,display:"flex",alignItems:"center",justifyContent:"center",color:C.text2}}>No trend data</div>;
  const keys = ["Waigani","Boroko","Gerehu"];
  const colors = {Waigani:C.teal, Boroko:C.violet, Gerehu:C.amber};
  const W=560,H=160,PL=55,PB=28,PT=12,PR=16;
  const iW=W-PL-PR, iH=H-PB-PT;
  const allV = trends.flatMap(d=>keys.map(k=>d[k]).filter(Boolean));
  const minV=Math.min(...allV), maxV=Math.max(...allV), range=maxV-minV||1;
  const toX = i => PL+(i/(trends.length-1))*iW;
  const toY = v => PT+iH-((v-minV)/range)*iH;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:"100%",height:"auto"}}>
      {[0,1,2,3].map(i=>{
        const v=minV+(i/3)*range, y=toY(v);
        return <g key={i}><line x1={PL} x2={W-PR} y1={y} y2={y} stroke={C.bg3} strokeWidth={1}/><text x={PL-6} y={y+4} fill={C.text2} fontSize={9} textAnchor="end" fontFamily="'IBM Plex Mono'">{fmt(Math.round(v/100)*100)}</text></g>;
      })}
      {keys.map(k=>{
        const pts = trends.map((d,i)=>d[k]?`${toX(i)},${toY(d[k])}`:"").filter(Boolean).join(" ");
        if(!pts) return null;
        return <g key={k}>
          <polyline points={pts} fill="none" stroke={colors[k]} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round"/>
          {trends.map((d,i)=>d[k]?<circle key={i} cx={toX(i)} cy={toY(d[k])} r={3} fill={colors[k]}/>:null)}
        </g>;
      })}
      {trends.map((d,i)=><text key={i} x={toX(i)} y={H-4} fill={C.text2} fontSize={9} textAnchor="middle" fontFamily="'IBM Plex Mono'">{d.week}</text>)}
    </svg>
  );
}

// ── SVG HEATMAP BUBBLES ───────────────────────────────────────────────────────
function HeatmapViz({suburbs, selected, onSelect, metric = "avg_price", extraLayers = {}}) {
  if (!suburbs?.length) return null;
  // Precise Projection for Port Moresby - Zoom 11 Stitched Tiles (1861-1862, 1077-1078)
  // Tile 1861/1077 NW: 147.0410, -9.2756
  // Tile 1862/1078 SE: 147.3926, -9.6224
  const LAT_NW = -9.275622, LAT_SE = -9.622414, LNG_NW = 147.041015, LNG_SE = 147.392578;
  const W=520, H=320;

  const toX = lng => ((lng - LNG_NW) / (LNG_SE - LNG_NW)) * W;
  const toY = lat => ((LAT_NW - lat) / (LAT_NW - LAT_SE)) * H;

  const maxL = Math.max(...suburbs.map(s=>s.listings||1));
  const rOf  = l => 22+((l/maxL)**0.5)*28;

  const minV = Math.min(...suburbs.map(s => s[metric] || 0));
  const maxV = Math.max(...suburbs.map(s => s[metric] || 1));

  const getCol = (val) => {
    if (metric === "power_score") {
       const t = clamp((val-20)/80, 0, 1);
       return `rgb(${Math.round(200 - t*150)}, ${Math.round(50 + t*150)}, 50)`;
    }
    return priceColor(val, minV, maxV);
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:"100%",height:"auto", borderRadius: 8, overflow: "hidden", background: C.bg1}}>
      <defs>
        <pattern id="g" x="0" y="0" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="8" cy="8" r=".6" fill={C.bg3}/></pattern>
      </defs>
      <rect width={W} height={H} fill={C.bg1}/>
      <rect width={W} height={H} fill="url(#g)"/>

      {/* Map Background Layer - Stitched Tiles (CartoDB Dark Matter) */}
      {extraLayers.map && (
        <g style={{opacity: 0.45, filter: "grayscale(0.6) contrast(1.2)"}}>
          <image href="https://basemaps.cartocdn.com/dark_all/11/1861/1077.png" x="0" y="0" width={W/2} height={H/2} />
          <image href="https://basemaps.cartocdn.com/dark_all/11/1862/1077.png" x={W/2} y="0" width={W/2} height={H/2} />
          <image href="https://basemaps.cartocdn.com/dark_all/11/1861/1078.png" x="0" y={H/2} width={W/2} height={H/2} />
          <image href="https://basemaps.cartocdn.com/dark_all/11/1862/1078.png" x={W/2} y={H/2} width={W/2} height={H/2} />
        </g>
      )}

      {/* Listing Pins Layer */}
      {extraLayers.pins && extraLayers.listings && extraLayers.listings.map((l, i) => {
        if (!l.suburb) return null;
        const seed = l.listing_id ? l.listing_id.split("").reduce((a,b)=>a+b.charCodeAt(0), 0) : i;
        const jitterX = ((seed % 100) / 100 - 0.5) * 0.015;
        const jitterY = (((seed * 7) % 100) / 100 - 0.5) * 0.01;
        const s = suburbs.find(sb => sb.suburb === l.suburb);
        if (!s) return null;
        const x = toX(s.lng + jitterX), y = toY(s.lat + jitterY);
        return <circle key={i} cx={x} cy={y} r={1.5} fill={priceColor(l.price_monthly_k)} style={{opacity: 0.65}} />;
      })}

      {/* School Pins Layer */}
      {extraLayers.schools && extraLayers.schools.map(s => {
         const x = toX(s.lng), y = toY(s.lat);
         return (
           <g key={s.name}>
             <circle cx={x} cy={y} r={3} fill={C.teal} />
             <text x={x+5} y={y+2} fill={C.text1} fontSize={7} fontWeight={600}>{s.name}</text>
           </g>
         )
      })}

      {/* Infrastructure Projects Layer */}
      {extraLayers.projects && extraLayers.projects.map(p => {
         const x = toX(p.lng), y = toY(p.lat);
         return (
           <g key={p.name}>
             <rect x={x-10} y={y-10} width={20} height={20} rx={4} fill={`${C.amber}22`} stroke={C.amber} strokeWidth={1.5} strokeDasharray="2 2" />
             <path d={`M ${x-4} ${y-4} L ${x+4} ${y+4} M ${x-4} ${y+4} L ${x+4} ${y-4}`} stroke={C.amber} strokeWidth={1.5} />
             <text x={x} y={y+18} textAnchor="middle" fill={C.amber} fontSize={7} fontWeight={800} style={{textShadow:'0 1px 2px rgba(0,0,0,0.8)'}}>{p.name}</text>
           </g>
         )
      })}

      {suburbs.map(s=>{
        if(!s.lat||!s.lng) return null;
        const x=toX(s.lng), y=toY(s.lat), r=rOf(s.listings||20);
        const val = s[metric] || 0;
        const col = getCol(val);
        const sel = selected===s.suburb;
        return <g key={s.suburb} onClick={()=>onSelect(sel?null:s.suburb)} style={{cursor:"pointer"}}>
          <circle cx={x} cy={y} r={r*1.5} fill={`${col}10`}/>
          {sel&&<circle cx={x} cy={y} r={r+8} fill="none" stroke={col} strokeWidth={1.5} strokeDasharray="4 3"/>}
          <circle cx={x} cy={y} r={r} fill={`${col}${selected&&!sel?"30":"CC"}`} stroke={col} strokeWidth={sel?2:1}/>
          <text x={x} y={y-3} textAnchor="middle" fill={selected&&!sel?C.text3:C.text0} fontSize={9} fontWeight={700} fontFamily="'Barlow Condensed'">{s.suburb}</text>
          <text x={x} y={y+9} textAnchor="middle" fill={col} fontSize={8} fontFamily="'IBM Plex Mono'">{metric.includes("yield") ? `${val}%` : metric.includes("rate") ? `${val}d` : fmt(val)}</text>
        </g>;
      })}
    </svg>
  );
}

// ── BAR CHART ─────────────────────────────────────────────────────────────────
function BarChart({data, labelKey, valueKey, color=C.teal}) {
  if(!data?.length) return null;
  const max=Math.max(...data.map(d=>d[valueKey]||0));
  return <div style={{display:"flex",flexDirection:"column",gap:8}}>
    {data.slice(0,10).map((d,i)=>(
      <div key={i}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
          <span style={{fontSize:11,color:C.text1,fontWeight:500}}>{d[labelKey]}</span>
          <span style={{fontSize:11,color,fontFamily:"'IBM Plex Mono'",fontWeight:600}}>{d[valueKey]}</span>
        </div>
        <div style={{height:5,background:C.bg3,borderRadius:3,overflow:"hidden"}}>
          <div style={{width:`${(d[valueKey]/max)*100}%`,height:"100%",background:color,borderRadius:3,transition:"width .8s ease"}}/>
        </div>
      </div>
    ))}
  </div>;
}

// ── SUPPLY DEMAND ─────────────────────────────────────────────────────────────
function SupplyDemand({data, onSeeMore}) {
  if(!data?.length) return null;
  const maxS=Math.max(...data.map(d=>d.supply||0));
  return <div style={{display:"flex",flexDirection:"column",gap:12}}>
    {data.slice(0,10).map((d,i)=>{
      const ratio=(d.demand_score||50)/(Math.min(100,(d.supply/maxS)*100)||1);
      const label=ratio>1.3?"High Demand":ratio<0.7?"Oversupply":"Balanced";
      const lc=ratio>1.3?C.green:ratio<0.7?C.red:C.amber;
      return <div key={i}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:4}}>
          <span style={{fontSize:12,color:C.text1,fontWeight:600}}>{d.suburb}</span>
          <Badge label={label} color={lc} small/>
        </div>
        <div style={{display:"flex",gap:4,alignItems:"center"}}>
          <div style={{flex:1,height:4,background:C.bg3,borderRadius:2,overflow:"hidden"}}>
            <div style={{width:`${d.demand_score||50}%`,height:"100%",background:C.teal,borderRadius:2}}/>
          </div>
          <span style={{fontSize:9,color:C.text2,width:12}}>D</span>
        </div>
        <div style={{display:"flex",gap:4,alignItems:"center",marginTop:2}}>
          <div style={{flex:1,height:4,background:C.bg3,borderRadius:2,overflow:"hidden"}}>
            <div style={{width:`${(d.supply/maxS)*100}%`,height:"100%",background:C.violet,borderRadius:2}}/>
          </div>
          <span style={{fontSize:9,color:C.text2,width:12}}>S</span>
        </div>
      </div>;
    })}
    <div style={{marginTop:10, display:'flex', justifyContent:'center'}}>
      <div className="link-btn" onClick={onSeeMore}>View Full Analytics →</div>
    </div>
  </div>;
}

// ── MARKET VALUE BADGE ────────────────────────────────────────────────────────
function MvBadge({mv}) {
  if(!mv) return null;
  return <Badge label={`${mv.label} ${mv.pct_vs_avg>0?"+":""}${mv.pct_vs_avg?.toFixed(0)}%`} color={mv.color} small/>;
}

// ── LISTING ROW ───────────────────────────────────────────────────────────────
function ListingRow({l, onSearchTitle}) {
  const isFlag = l.market_value?.label==="Overpriced" && l.market_value?.pct_vs_avg>40;
  const isLegalRisk = l.legal_flags?.length > 0;
  const hasDupes = !!l.group_id;

  const tColor = l.title_status === 'State Lease' ? C.green : l.title_status?.includes('Customary') ? C.amber : C.text2;

  return (
    <tr style={{borderBottom:`1px solid ${C.bg3}`,background:isFlag||isLegalRisk?"rgba(239,68,68,.04)":"transparent",transition:"background .15s"}}
      onMouseEnter={e=>e.currentTarget.style.background=isFlag||isLegalRisk?"rgba(239,68,68,.08)":C.bg2}
      onMouseLeave={e=>e.currentTarget.style.background=isFlag||isLegalRisk?"rgba(239,68,68,.04)":"transparent"}>
      <td style={{padding:"9px 12px",color:C.text1,fontSize:12}}>{l.suburb||"—"}</td>
      <td style={{padding:"9px 12px",maxWidth:180}}>
        <div style={{color:C.text0,fontSize:12,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{l.title}</div>
        <div style={{display:'flex', gap:4, marginTop:4, flexWrap:'wrap'}}>
           {hasDupes && <div style={{fontSize:8, color:C.amber, display:'flex', alignItems:'center', gap:2}}>👯 DUPE</div>}
           <Badge label={l.title_status} color={tColor} small />
           {isLegalRisk && <Badge label="⚠️ LEGAL RISK" color={C.red} small />}
        </div>
      </td>
      <td style={{padding:"9px 12px"}}><span style={{fontFamily:"'IBM Plex Mono'",fontSize:12,color:C.teal,fontWeight:600}}>{fmt(l.price_monthly_k)}</span></td>
      <td style={{padding:"9px 12px"}}><MvBadge mv={l.market_value}/></td>
      <td style={{padding:"9px 12px"}}>
        <HealthScore score={l.health_score || 0} />
      </td>
      <td style={{padding:"9px 12px"}}>
        <div style={{display:'flex', flexDirection:'column', gap:3, minWidth:80}}>
           <span style={{background:l.source_site==="Facebook Marketplace"?`${C.violet}20`:`${C.teal}18`,color:l.source_site==="Facebook Marketplace"?C.violet:C.tealDim,borderRadius:4,padding:"2px 7px",fontSize:10,fontWeight:600, width:'fit-content'}}>{l.source_site}</span>
           {l.is_verified ? <Badge label="✓ Verified" color={C.green} small/> : <Badge label="Unverified" color={C.text2} small/>}
        </div>
      </td>
      <td style={{padding:"9px 12px",color:C.text2,fontSize:11}}>{rel(l.scraped_at)}</td>
      <td style={{padding:"9px 12px"}}>
         <div style={{display:'flex', gap:6}}>
            {isFlag&&<span title="Market Flag" style={{background:"#7f1d1d",color:"#fca5a5",borderRadius:4,padding:"2px 7px",fontSize:10,fontWeight:700}}>🚩</span>}
            {isLegalRisk&&<span title="Legal Dispute/Risk" style={{background:"#7f1d1d",color:"#fca5a5",borderRadius:4,padding:"2px 7px",fontSize:10,fontWeight:700}}>⚖️</span>}
         </div>
      </td>
      <td style={{padding:"9px 12px"}}>
         <button onClick={() => onSearchTitle(l.listing_id)} style={{background:'transparent', border:`1px solid ${C.teal}44`, color:C.teal, fontSize:9, fontWeight:700, borderRadius:4, padding:"4px 8px", cursor:'pointer', whiteSpace:'nowrap'}}>SEARCH TITLE</button>
      </td>
    </tr>
  );
}

// ── SCRAPE CONTROL PANEL ──────────────────────────────────────────────────────
function ScrapePanel({onClose, onRefresh}) {
  const [sources, setSources] = useState(["hausples","professionals","agencies"]);
  const [pages, setPages] = useState(3);
  const [includeFb, setIncludeFb] = useState(false);
  const [job, setJob] = useState(null);
  const [polling, setPolling] = useState(false);
  const pollRef = useRef(null);

  const toggleSrc = s => setSources(p=>p.includes(s)?p.filter(x=>x!==s):[...p,s]);

  const trigger = async () => {
    try {
      const include_fb = sources.includes("facebook");
      const data = await apiFetch("/scrape/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sources: sources.filter(s => s !== "facebook"),
          max_pages: pages,
          include_facebook: include_fb,
          headless: true
        })
      });
      if (data) {
        setJob(data);
        setPolling(true);
      } else {
        alert("Failed to start scrape job. Please check your connection or login status.");
      }
    } catch (err) {
      alert("Error starting scrape job: " + err.message);
    }
  };

  useEffect(()=>{
    if(!polling||!job?.job_id) return;
    pollRef.current = setInterval(async()=>{
      const d = await apiFetch(`/scrape/status/${job.job_id}`);
      if(d){ setJob(d); if(d.status==="complete"||d.status==="error"){ setPolling(false); clearInterval(pollRef.current);} }
    }, 1200);
    return ()=>clearInterval(pollRef.current);
  },[polling,job?.job_id]);

  const srcList = [["hausples","Hausples"],["professionals","The Professionals"],["agencies","All Agencies"],["portals","All Portals"],["facebook","Facebook"]];

  return (
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.7)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:1000}} onClick={e=>{if(e.target===e.currentTarget)onClose()}}>
      <Card style={{width:480,padding:28,animation:"fadeUp .3s ease"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24}}>
          <span style={{fontFamily:"'Barlow Condensed'",fontSize:20,fontWeight:700,letterSpacing:"-.01em"}}>⚡ Launch Scrape Job</span>
          <button onClick={onClose} style={{background:"none",border:"none",color:C.text2,fontSize:18,cursor:"pointer"}}>✕</button>
        </div>

        {!job ? <>
          <div style={{marginBottom:18}}>
            <div style={{fontSize:11,color:C.text2,marginBottom:8,fontFamily:"'IBM Plex Mono'"}}>SOURCES</div>
            <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
              {srcList.map(([k,label])=><Pill key={k} active={sources.includes(k)} onClick={()=>toggleSrc(k)}>{label}</Pill>)}
            </div>
          </div>
          <div style={{marginBottom:18}}>
            <div style={{fontSize:11,color:C.text2,marginBottom:8,fontFamily:"'IBM Plex Mono'"}}>PAGES PER SITE</div>
            <div style={{display:"flex",gap:8}}>
              {[1,2,3,5,10].map(n=><Pill key={n} active={pages===n} onClick={()=>setPages(n)}>{n}</Pill>)}
            </div>
          </div>
          <div style={{background:C.bg3,borderRadius:8,padding:"10px 14px",marginBottom:22,fontSize:12,color:C.text1}}>
            ⚠️ Facebook scraping requires <code style={{color:C.teal}}>FB_EMAIL</code> and <code style={{color:C.teal}}>FB_PASSWORD</code> in Render environment variables.
            For 2FA, generate a <code style={{color:C.teal}}>fb_session.json</code> locally and upload it to the <code style={{color:C.teal}}>/app/data</code> persistent disk.
          </div>
          <button onClick={trigger} disabled={sources.length===0} style={{width:"100%",background:`linear-gradient(135deg,${C.teal},${C.violet})`,border:"none",borderRadius:8,padding:"12px",color:"#fff",fontSize:14,fontWeight:700,cursor:sources.length?"pointer":"not-allowed",opacity:sources.length?1:.5}}>
            Start Scraping {sources.length} source{sources.length!==1?"s":""}
          </button>
        </> : <>
          <div style={{marginBottom:16}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
              <span style={{fontSize:13,color:C.text1}}>Job <code style={{color:C.teal,fontFamily:"'IBM Plex Mono'"}}>{job.job_id}</code></span>
              <Badge label={job.status.toUpperCase()} color={job.status==="complete"?C.green:job.status==="error"?C.red:C.teal}/>
            </div>
            <div style={{height:8,background:C.bg3,borderRadius:4,overflow:"hidden",marginBottom:8}}>
              <div style={{height:"100%",width:`${job.progress||0}%`,background:`linear-gradient(90deg,${C.teal},${C.violet})`,borderRadius:4,transition:"width .5s ease"}}/>
            </div>
            <div style={{display:"flex",justifyContent:"space-between",fontSize:11,color:C.text2}}>
              <span>{job.current_source ? `Scraping ${job.current_source}…` : job.status}</span>
              <span>{job.collected||0} listings collected</span>
            </div>
          </div>
          {(job.status==="complete"||job.status==="error")&&<button onClick={()=>{setJob(null);onClose(); if(job.status==="complete" && onRefresh) onRefresh();}} style={{width:"100%",background:C.bg3,border:`1px solid ${C.border}`,borderRadius:8,padding:"10px",color:C.text0,fontSize:13,fontWeight:600,cursor:"pointer"}}>{job.status==="complete"?"✓ Done — Refresh Dashboard":"✗ Dismiss"}</button>}
        </>}
      </Card>
    </div>
  );
}

// ── SIDEBAR NAV ───────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  {id:"dashboard", icon:"◈", label:"Dashboard"},
  {id:"listings",  icon:"≡", label:"Listings"},
  {id:"heatmap",   icon:"◉", label:"Heatmap"},
  {id:"analytics", icon:"∿", label:"Analytics"},
  {id:"notifications", icon:"🔔", label:"Alerts"},
  {id:"vault",       icon:"💼", label:"Vault"},
  {id:"valuation",   icon:"🏷️", label:"Valuation"},
  {id:"b2b",       icon:"🛰", label:"Agent Intel"},
  {id:"flags",     icon:"⚑", label:"Flagged"},
  {id:"sources", icon:"📡", label:"Sources"},
  {id:"lender", icon:"🏦", label:"Lender Portal"},
  {id:"dev", icon:"💻", label:"Dev Portal"},
  {id:"settings", icon:"⚙️", label:"Settings"},
];

function Sidebar({active, onNav, onLogout, user}) {
  const filteredNav = NAV_ITEMS.filter(n => {
    if (n.id === 'b2b' && user?.role !== 'agent' && user?.role !== 'admin') return false;
    if (n.id === 'lender' && user?.role !== 'lender' && user?.role !== 'admin') return false;
    if (n.id === 'dev' && user?.role !== 'developer' && user?.role !== 'admin') return false;
    return true;
  });

  return (
    <div className="sidebar-container" style={{
      background:C.bg1, borderRight:`1px solid ${C.border}`,
      display:"flex", flexDirection:"column", alignItems:"center",
      padding:"16px 0", gap:4, flexShrink:0, zIndex:10
    }}>
      <div className="sidebar-logo" style={{fontFamily:"'Barlow Condensed'",fontSize:22,fontWeight:800,color:C.teal,marginBottom:20,letterSpacing:"-.02em"}}>PD</div>
      <div className="nav-items-wrapper" style={{display:"flex", flexDirection:"column", gap:4}}>
        {filteredNav.map(n=>(
          <button key={n.id} onClick={()=>onNav(n.id)} title={n.label} className="nav-btn" style={{width:44,height:44,background:active===n.id?C.tealGlow:"transparent",border:`1px solid ${active===n.id?C.teal:C.bg3}`,borderRadius:10,color:active===n.id?C.teal:C.text2,fontSize:18,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",transition:"all .15s"}}>
            {n.icon}
          </button>
        ))}
      </div>
      <div style={{flex:1}} className="sidebar-spacer"/>
      <button onClick={onLogout} title="Logout" className="logout-btn" style={{width:44,minHeight:44,background:'transparent',border:`1px solid ${C.bg3}`,borderRadius:10,color:C.red,fontSize:18,cursor:"pointer",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",marginBottom:16,padding:"4px 0"}}>
        ⎋
        <span style={{fontSize:8,fontWeight:700,marginTop:2}}>LOGOUT</span>
      </button>
      <div style={{width:8,height:8,borderRadius:"50%",background:C.green,boxShadow:`0 0 0 3px ${C.green}30`,animation:"pulse 2s infinite"}} title="Live" className="live-indicator"/>
    </div>
  );
}

// ── TOPBAR ────────────────────────────────────────────────────────────────────
function Topbar({view, overview, onScrape, onLogout, loading, user}) {
  const viewLabels = {dashboard:"Dashboard",listings:"All Listings",heatmap:"Price Heatmap",analytics:"Analytics",notifications:"Alerts & Saved Searches",vault:"Bank-Ready Vault",valuation:"Property Valuation (AVM)",b2b:"Agent Intelligence",flags:"Flagged Listings",sources:"Market Sources", settings: "Account Settings", lender: "Lender Portal", dev: "Developer Portal"};
  return (
    <div className="topbar" style={{height:56,background:C.bg1,borderBottom:`1px solid ${C.border}`,display:"flex",alignItems:"center",justifyContent:"space-between",padding:"0 24px",flexShrink:0}}>
      <div style={{display:"flex",alignItems:"center",gap:12}}>
        <span className="topbar-title" style={{fontFamily:"'Barlow Condensed'",fontSize:18,fontWeight:700,color:C.text0}}>{viewLabels[view]}</span>
        <span className="location-tag" style={{fontSize:10,color:C.text2,fontFamily:"'IBM Plex Mono'"}}>PORT MORESBY · NCD</span>
      </div>
      <div style={{display:"flex",alignItems:"center",gap:14}}>
        <div className="user-info" style={{marginRight:16, textAlign:'right'}}>
           <div style={{fontSize:11, color:C.text0, fontWeight:600}}>{user?.full_name || 'User'}</div>
           <div style={{fontSize:9, color:C.text2, marginBottom:4}}>{user?.email || user?.phone}</div>
           <button onClick={onLogout} style={{
             background: "none", border: "none", padding: 0, color: C.red,
             fontSize: 10, fontWeight: 700, cursor: "pointer", textDecoration: "underline"
           }}>Logout</button>
        </div>
        {overview?.last_scraped&&<span className="updated-tag" style={{fontSize:11,color:C.text2}}>Updated {rel(overview.last_scraped)}</span>}
        {loading&&<Spinner/>}
        <button onClick={onScrape} className="scrape-btn" style={{background:`linear-gradient(135deg,${C.teal},${C.violet})`,border:"none",borderRadius:8,padding:"7px 16px",color:"#fff",fontSize:12,fontWeight:700,cursor:"pointer",display:"flex",alignItems:"center",gap:6}}>
          <span className="scrape-icon">⚡</span> <span className="scrape-text">Run Scrape</span>
        </button>
      </div>
    </div>
  );
}

// ── VIEWS ─────────────────────────────────────────────────────────────────────

function DashboardView({overview, heatmap, trends, sd, sources, onNav}) {
  const [selSuburb, setSelSuburb] = useState(null);
  const o=overview||MOCK_OVERVIEW;
  const h=(heatmap?.suburbs||MOCK_HEATMAP.suburbs);
  const t=(trends?.trends||MOCK_TRENDS.trends);
  const sdData=(sd?.data||MOCK_SD.data);
  const srcData=(sources?.sources||MOCK_SOURCES.sources);
  const keys=[{label:"TOTAL LISTINGS",value:o.total_listings,icon:"🏘",accent:C.teal},{label:"AVG RENT/MONTH",value:fmt(o.avg_rent_pgk),icon:"💰",accent:C.amber},{label:"MIDDLEMAN FLAGS",value:o.middleman_flags,icon:"🚩",accent:C.red},{label:"SOURCES ACTIVE",value:o.sources_active,icon:"📡",accent:C.violet}];

  return <div style={{display:"flex",flexDirection:"column",gap:18}}>
    {/* KPIs */}
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit, minmax(140px, 1fr))",gap:14}}>
      {keys.map((k,i)=>{
        let click = null;
        if(k.label === 'TOTAL LISTINGS') click = () => onNav('listings');
        if(k.label === 'MIDDLEMAN FLAGS') click = () => onNav('flags');
        return <KpiCard key={i} {...k} delay={i*60} onClick={click}/>
      })}
    </div>
    {/* Map + SD */}
    <div className="dashboard-grid-row" style={{display:"grid",gridTemplateColumns:"1fr 280px",gap:14}}>
      <Card style={{padding:20}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
          <span style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",letterSpacing:"0.08em"}}>PRICE HEATMAP · PGK/MONTH</span>
          {selSuburb&&<button onClick={()=>setSelSuburb(null)} style={{background:"none",border:"none",color:C.teal,fontSize:11,cursor:"pointer"}}>Clear ✕</button>}
        </div>
        <HeatmapViz suburbs={h} selected={selSuburb} onSelect={setSelSuburb} extraLayers={{map: true}}/>
        <div style={{marginTop:10,display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:9,color:C.text2}}>Low</span>
          <div style={{flex:1,height:5,borderRadius:3,background:`linear-gradient(to right,rgb(32,190,160),rgb(200,70,45))`}}/>
          <span style={{fontSize:9,color:C.text2}}>High</span>
        </div>
      </Card>
      <Card style={{padding:20}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14}}>SUPPLY / DEMAND</div>
        <SupplyDemand data={sdData} onSeeMore={() => onNav("analytics")}/>
        <div style={{display:"flex",gap:12,marginTop:14}}>
          <div style={{display:"flex",alignItems:"center",gap:5,fontSize:9,color:C.text2}}><div style={{width:16,height:3,background:C.teal,borderRadius:2}}/> Demand</div>
          <div style={{display:"flex",alignItems:"center",gap:5,fontSize:9,color:C.text2}}><div style={{width:16,height:3,background:C.violet,borderRadius:2}}/> Supply</div>
        </div>
      </Card>
    </div>
    {/* Trends + Sources */}
    <div className="dashboard-grid-row" style={{display:"grid",gridTemplateColumns:"1fr 300px",gap:14}}>
      <Card style={{padding:20}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
          <span style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'"}}>RENT TRENDS · 8 WEEKS</span>
          <div style={{display:"flex",gap:8}}>
            {["Waigani","Boroko","Gerehu"].map((s,i)=><div key={s} style={{display:"flex",alignItems:"center",gap:4,fontSize:10,color:C.text1}}><div style={{width:12,height:3,borderRadius:2,background:[C.teal,C.violet,C.amber][i]}}/>{s}</div>)}
          </div>
        </div>
        <LineChart trends={t}/>
      </Card>
      <Card style={{padding:20}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14}}>LISTINGS BY SOURCE</div>
        <BarChart data={srcData} labelKey="name" valueKey="count" color={C.teal}/>
      </Card>
    </div>
  </div>;
}

function ListingsView({suburbFilter}) {
  const [listings, setListings] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [suburb, setSuburb] = useState(suburbFilter||"");
  const [source, setSource] = useState("");
  const [type, setType] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [titleStatus, setTitleStatus] = useState("");
  const [mvFilter, setMvFilter] = useState("");
  const [sort, setSort] = useState("scraped_at");

  const load = useCallback(async()=>{
    setLoading(true);
    const q=new URLSearchParams({page,limit:25,sort,order:"desc"});
    if(suburb) q.set("suburb",suburb);
    if(source) q.set("source",source);
    if(type)   q.set("type",type);
    if(minPrice) q.set("min_price",minPrice);
    if(maxPrice) q.set("max_price",maxPrice);
    if(titleStatus) q.set("title_status",titleStatus);
    const data = await apiFetch(`/listings?${q}`);
    if(data){
      let ls=data.listings||[];
      if(mvFilter) ls=ls.filter(l=>l.market_value?.label===mvFilter);
      setListings(ls); setTotal(data.total||0); setPages(data.pages||1);
    } else {
      let ls=mockListings(100);
      if(suburb) ls=ls.filter(l=>l.suburb===suburb);
      if(source) ls=ls.filter(l=>l.source_site.toLowerCase().includes(source.toLowerCase()));
      if(type)   ls=ls.filter(l=>l.property_type===type);
      if(mvFilter) ls=ls.filter(l=>l.market_value?.label===mvFilter);
      setListings(ls.slice((page-1)*25,(page-1)*25+25)); setTotal(ls.length); setPages(Math.ceil(ls.length/25));
    }
    setLoading(false);
  },[page,suburb,source,type,minPrice,maxPrice,mvFilter,sort]);

  useEffect(()=>{load();},[load]);

  const [showLegalModal, setShowLegalModal] = useState(null);

  const TH=({children,s})=><th onClick={()=>setSort(s||"scraped_at")} style={{padding:"8px 12px",textAlign:"left",fontSize:10,color:sort===s?C.teal:C.text2,fontFamily:"'IBM Plex Mono'",letterSpacing:"0.08em",cursor:"pointer",userSelect:"none",whiteSpace:"nowrap"}}>{children}{sort===s?" ↓":""}</th>;

  const runTitleSearch = async (lid) => {
    const res = await apiFetch(`/legal/title-search?listing_id=${lid}`);
    if (res) setShowLegalModal(res);
  };

  return <div style={{display:"flex",flexDirection:"column",gap:14}}>
     {showLegalModal && (
        <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.8)', zIndex:3000, display:'flex', alignItems:'center', justifyContent:'center'}}>
           <Card style={{width:450, padding:24}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20}}>
                 <span style={{fontWeight:800, color:C.teal}}>Legal Guard: Title Verification</span>
                 <button onClick={()=>setShowLegalModal(null)} style={{background:'none', border:'none', color:C.text2, cursor:'pointer'}}>✕</button>
              </div>
              <div style={{display:'flex', flexDirection:'column', gap:16}}>
                 <div style={{background:C.bg3, padding:14, borderRadius:10}}>
                    <div style={{fontSize:10, color:C.text2, marginBottom:4}}>OFFICIAL TITLE STATUS</div>
                    <div style={{fontSize:18, fontWeight:800, color:showLegalModal.registry_verified ? C.green : C.amber}}>
                       {showLegalModal.title_status} {showLegalModal.registry_verified ? '✓' : ''}
                    </div>
                    <div style={{fontSize:11, color:C.text2, marginTop:4}}>
                       {showLegalModal.registry_verified ? 'Registry record found and matches listing.' : 'No active registry link found for this listing ID.'}
                    </div>
                 </div>

                 <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:10}}>
                    <div style={{background:C.bg3, padding:10, borderRadius:8}}>
                       <div style={{fontSize:9, color:C.text2, marginBottom:2}}>DISPUTE INDEX</div>
                       <div style={{fontSize:13, fontWeight:700, color:showLegalModal.dispute_index === 'Low' ? C.green : C.red}}>{showLegalModal.dispute_index}</div>
                    </div>
                    {showLegalModal.ilg_number && (
                      <div style={{background:C.bg3, padding:10, borderRadius:8}}>
                         <div style={{fontSize:9, color:C.text2, marginBottom:2}}>ILG FILE NO.</div>
                         <div style={{fontSize:13, fontWeight:700, color:C.teal}}>{showLegalModal.ilg_number}</div>
                      </div>
                    )}
                 </div>

                 <div style={{borderTop:`1px solid ${C.bg3}`, paddingTop:14}}>
                    <div style={{fontSize:10, color:C.text2, marginBottom:6}}>LEGAL RECOMMENDATION</div>
                    <div style={{fontSize:13, lineHeight:1.4, color:C.text1}}>{showLegalModal.legal_recommendation}</div>
                 </div>

                 <button style={{width:'100%', background:C.teal, color:C.bg0, border:'none', borderRadius:6, padding:10, fontWeight:700, marginTop:10}}>
                    REQUEST FULL SOLICITOR REPORT
                 </button>
              </div>
           </Card>
        </div>
     )}
    {/* Filters */}
    <Card style={{padding:"14px 18px"}}>
      <div style={{display:"flex",gap:12,flexWrap:"wrap",alignItems:"center"}}>
        <select value={suburb} onChange={e=>setSuburb(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:suburb?C.teal:C.text1,fontSize:12,cursor:"pointer"}}>
          <option value="">All Suburbs</option>
          {SUBURBS.map(s=><option key={s} value={s}>{s}</option>)}
        </select>
        <select value={source} onChange={e=>setSource(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:source?C.teal:C.text1,fontSize:12,cursor:"pointer"}}>
          <option value="">All Sources</option>
          {SOURCES.map(s=><option key={s} value={s}>{s}</option>)}
        </select>
        <select value={type} onChange={e=>setType(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:type?C.teal:C.text1,fontSize:12,cursor:"pointer"}}>
          <option value="">All Types</option>
          {TYPES.map(t=><option key={t} value={t}>{t}</option>)}
        </select>
        <select value={mvFilter} onChange={e=>setMvFilter(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:mvFilter?C.teal:C.text1,fontSize:12,cursor:"pointer"}}>
          <option value="">All Market Values</option>
          <option value="Deal">🟢 Deal</option>
          <option value="Fair">🟡 Fair</option>
          <option value="Overpriced">🔴 Overpriced</option>
        </select>
        <select value={titleStatus} onChange={e=>setTitleStatus(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:titleStatus?C.teal:C.text1,fontSize:12,cursor:"pointer"}}>
          <option value="">All Title Types</option>
          <option value="State Lease">State Lease</option>
          <option value="Customary (ILG)">Customary (ILG)</option>
          <option value="Freehold">Freehold</option>
        </select>
        <input placeholder="Min K" value={minPrice} onChange={e=>setMinPrice(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:C.text0,fontSize:12,width:80}}/>
        <input placeholder="Max K" value={maxPrice} onChange={e=>setMaxPrice(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:C.text0,fontSize:12,width:80}}/>
        <button
          onClick={async () => {
             const name = suburb || type || "New Search";
             const criteria = { suburb, type, min_price: minPrice, max_price: maxPrice };
             const res = await apiFetch("/notifications/follow", {
               method: "POST",
               headers: { "Content-Type": "application/json" },
               body: JSON.stringify({ name, criteria })
             });
             if (res) alert(`Now following: ${name}. You will receive WhatsApp alerts for new matches.`);
          }}
          style={{background:C.bg3, border:`1px solid ${C.teal}`, borderRadius:6, padding:"6px 12px", color:C.teal, fontSize:11, fontWeight:700, cursor:'pointer'}}
        >
          🔔 FOLLOW SEARCH
        </button>
        <span style={{fontSize:11,color:C.text2,marginLeft:"auto"}}>{total} listings</span>
        {loading&&<Spinner/>}
      </div>
    </Card>
    {/* Table */}
    <Card>
      <div style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse"}}>
          <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
            <TH>Suburb</TH><TH>Title</TH><TH s="price_monthly_k">Price/mo</TH><TH>Market</TH><TH s="health_score">Health</TH><TH>Trust</TH><TH s="scraped_at">Posted</TH><TH>Risk</TH><TH>Legal</TH>
          </tr></thead>
          <tbody>{listings.map(l=><ListingRow key={l.listing_id} l={l} onSearchTitle={runTitleSearch}/>)}</tbody>
        </table>
      </div>
      {/* Pagination */}
      {pages>1&&<div style={{padding:"14px 18px",display:"flex",gap:8,alignItems:"center",justifyContent:"center",borderTop:`1px solid ${C.border}`}}>
        <button onClick={()=>setPage(p=>Math.max(1,p-1))} disabled={page===1} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"4px 12px",color:C.text1,cursor:page>1?"pointer":"not-allowed",opacity:page>1?1:.4}}>‹</button>
        <span style={{fontSize:12,color:C.text2,fontFamily:"'IBM Plex Mono'"}}>{page} / {pages}</span>
        <button onClick={()=>setPage(p=>Math.min(pages,p+1))} disabled={page===pages} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"4px 12px",color:C.text1,cursor:page<pages?"pointer":"not-allowed",opacity:page<pages?1:.4}}>›</button>
      </div>}
    </Card>
  </div>;
}

function HeatmapView({ user }) {
  const [data, setData] = useState(null);
  const [utilData, setUtilData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [sort, setSort] = useState("avg_price");
  const [metric, setMetric] = useState("avg_price");
  const [showSchools, setShowSchools] = useState(false);
  const [showProjects, setShowProjects] = useState(false);
  const [showMap, setShowMap] = useState(true);
  const [showPins, setShowPins] = useState(false);
  const [listings, setListings] = useState([]);
  const [showReview, setShowReview] = useState(false);

  useEffect(()=>{
    apiFetch("/analytics/heatmap").then(d=>setData(d||MOCK_HEATMAP));
    apiFetch("/utilities/map").then(d=>setUtilData(d));
    apiFetch("/listings?limit=200").then(d=>setListings(d?.listings||[]));
  },[]);
  const suburbs=(data?.suburbs||MOCK_HEATMAP.suburbs);
  const sorted=[...suburbs].sort((a,b)=>b[sort]-a[sort]);
  const sel=selected?suburbs.find(s=>s.suburb===selected):null;

  const combinedSuburbs = suburbs.map(s => {
     const rel = utilData?.reliability[s.suburb] || {power_score: 80, water_score: 90};
     const safety = {safety_score: 75 + (s.suburb.length % 20)}; // Simulated safety score
     return {...s, ...rel, ...safety};
  });

  return <div className="dashboard-grid-row" style={{display:"grid",gridTemplateColumns:"1fr 260px",gap:14,height:"100%"}}>
    {showReview && (
       <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.8)', zIndex:3000, display:'flex', alignItems:'center', justifyContent:'center'}}>
          <Card style={{width:400, padding:24}}>
             <div style={{fontSize:18, fontWeight:800, marginBottom:16}}>Report Utility Reliability</div>
             <div style={{display:'flex', flexDirection:'column', gap:12}}>
                <select style={{background:C.bg3, padding:10, borderRadius:8, color:C.text0}}>
                   <option>Select Suburb</option>
                   {SUBURBS.map(s=><option key={s}>{s}</option>)}
                </select>
                <select style={{background:C.bg3, padding:10, borderRadius:8, color:C.text0}}>
                   <option>PNG Power (Electricity)</option>
                   <option>Water PNG</option>
                </select>
                <div style={{fontSize:12, color:C.text1}}>Reliability Rating (1-5)</div>
                <input type="range" min="1" max="5" style={{accentColor:C.teal}} />
                <textarea placeholder="Specific street or issue..." style={{background:C.bg3, border:`1px solid ${C.border}`, borderRadius:8, padding:10, color:C.text0, height:80}} />
                <div style={{display:'flex', gap:10}}>
                   <button onClick={()=>setShowReview(false)} style={{flex:1, background:C.bg1, border:`1px solid ${C.border}`, color:C.text1, padding:10, borderRadius:6}}>Cancel</button>
                   <button onClick={()=>{alert("Report submitted! Crowdsourced data updated."); setShowReview(false);}} style={{flex:1, background:C.teal, color:C.bg0, border:'none', padding:10, borderRadius:6, fontWeight:700}}>Submit Review</button>
                </div>
             </div>
          </Card>
       </div>
    )}

    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      <Card style={{padding:20}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}>
          <div style={{display:'flex', gap:12, alignItems:'center'}}>
             <span style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'"}}>INTELLIGENCE LAYERS</span>
             <Pill active={showMap} onClick={()=>setShowMap(!showMap)}>🗺️ Map</Pill>
             <Pill active={showPins} onClick={()=>setShowPins(!showPins)}>📍 Pins</Pill>
             <Pill active={showSchools} onClick={()=>setShowSchools(!showSchools)}>🏫 Schools</Pill>
             <Pill active={showProjects} onClick={()=>setShowProjects(!showProjects)}>🏗️ Projects</Pill>
          </div>
          <div style={{display:"flex",gap:6}}>
            <Pill active={metric==="avg_price"} onClick={()=>setMetric("avg_price")}>Rent</Pill>
            <Pill active={metric==="avg_price_sqm"} onClick={()=>setMetric("avg_price_sqm")}>PGK/Sqm</Pill>
            <Pill active={metric==="power_score"} onClick={()=>setMetric("power_score")}>⚡ Power</Pill>
            <Pill active={metric==="safety_score"} onClick={() => {
              if (user?.role === 'buyer') {
                alert("Premium Layer: Safety Heatmaps require an Agency subscription or one-time K5.00 unlock.");
              } else {
                setMetric("safety_score");
              }
            }}>🛡️ Safety</Pill>
          </div>
        </div>
        <HeatmapViz suburbs={combinedSuburbs} selected={selected} onSelect={setSelected} metric={metric} extraLayers={{map: showMap, pins: showPins, listings: listings, schools: showSchools ? utilData?.schools : null, projects: showProjects ? utilData?.projects : null}}/>
        <div style={{marginTop:12,display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:9,color:C.text2}}>Low</span>
          <div style={{flex:1,height:6,borderRadius:3,background:`linear-gradient(to right,rgb(32,190,160),rgb(120,140,180),rgb(200,70,45))`}}/>
          <span style={{fontSize:9,color:C.text2}}>High</span>
        </div>
      </Card>
      {/* Grid tiles */}
      <Card style={{padding:18}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14}}>ALL SUBURBS</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(120px,1fr))",gap:10}}>
          {suburbs.map(s=>{
            const col=priceColor(s.avg_price);
            const isSel=selected===s.suburb;
            return <div key={s.suburb} onClick={()=>setSelected(isSel?null:s.suburb)} style={{background:col,borderRadius:8,padding:"12px 10px",cursor:"pointer",border:`2px solid ${isSel?"#fff":"transparent"}`,opacity:selected&&!isSel?.55:1,transition:"all .2s"}}>
              <div style={{fontSize:12,fontWeight:700,color:"#0f172a",fontFamily:"'Barlow Condensed'"}}>{s.suburb}</div>
              <div style={{fontSize:17,fontWeight:800,color:"#0f172a"}}>{fmt(s.avg_price)}</div>
              <div style={{fontSize:9,color:"#1e293b"}}>{s.listings} listings</div>
            </div>;
          })}
        </div>
      </Card>
    </div>
    {/* Sidebar */}
    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      <Card style={{padding:18}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:12}}>RANKINGS</div>
        <div style={{display:"flex",gap:6,marginBottom:12}}>
          {[["avg_price","Price"],["listings","Supply"]].map(([k,l])=><Pill key={k} active={sort===k} onClick={()=>setSort(k)}>{l}</Pill>)}
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:10}}>
          {sorted.map((s,i)=>{
            const col=priceColor(s.avg_price);
            const pct=((s.avg_price-2500)/2500)*100;
            return <div key={s.suburb} onClick={()=>setSelected(selected===s.suburb?null:s.suburb)} style={{cursor:"pointer",padding:"8px 10px",borderRadius:7,background:selected===s.suburb?C.bg3:"transparent",border:`1px solid ${selected===s.suburb?C.border:"transparent"}`}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
                <span style={{fontSize:12,fontWeight:600,color:C.text1}}>{i+1}. {s.suburb}</span>
                <span style={{fontSize:11,color:col,fontFamily:"'IBM Plex Mono'",fontWeight:600}}>{fmt(s.avg_price)}</span>
              </div>
              <div style={{height:4,background:C.bg3,borderRadius:2,overflow:"hidden"}}>
                <div style={{width:`${clamp((s.avg_price/7000)*100,5,100)}%`,height:"100%",background:col,borderRadius:2}}/>
              </div>
            </div>;
          })}
        </div>
      </Card>
      {sel&&<Card style={{padding:18,border:`1px solid ${priceColor(sel.avg_price)}44`}}>
        <div style={{fontFamily:"'Barlow Condensed'",fontSize:18,fontWeight:700,marginBottom:14}}>{sel.suburb}</div>
        <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:10}}>UTILITY STATUS</div>
        <div style={{display:'flex', flexDirection:'column', gap:8, marginBottom:16}}>
           <div style={{display:'flex', justifyContent:'space-between'}}>
              <span style={{fontSize:12, color:C.text1}}>⚡ Power Reliability</span>
              <span style={{fontSize:12, fontWeight:700, color:C.teal}}>{utilData?.reliability[sel.suburb]?.power_score || 85}%</span>
           </div>
           <div style={{display:'flex', justifyContent:'space-between'}}>
              <span style={{fontSize:12, color:C.text1}}>🌐 Internet (Fibre)</span>
              <Badge label={utilData?.internet[sel.suburb]?.fibre ? "AVAILABLE" : "N/A"} color={utilData?.internet[sel.suburb]?.fibre ? C.green : C.text2} small />
           </div>
        </div>
        {[
          ["Avg Rent", fmt(sel.avg_price)],
          ["Sqm Price", fmt(sel.avg_rent_sqm) + "/m²"],
          ["Rental Yield", sel.rental_yield + "%"],
          ["Days on Market", sel.absorption_rate + "d"],
          ["Listings", sel.listings]
        ].map(([k,v])=><div key={k} style={{display:"flex",justifyContent:"space-between",marginBottom:7,fontSize:12}}><span style={{color:C.text2}}>{k}</span><span style={{color:priceColor(sel.avg_price),fontWeight:600,fontFamily:"'IBM Plex Mono'"}}>{v}</span></div>)}

        {sel.speed_index_pct !== 0 && (
          <div style={{background:`${sel.speed_index_pct > 0 ? C.green : C.red}10`, padding:8, borderRadius:6, marginTop:8, border:`1px solid ${sel.speed_index_pct > 0 ? C.green : C.red}33`}}>
            <div style={{fontSize:10, fontWeight:700, color:sel.speed_index_pct > 0 ? C.green : C.red}}>RELATIVE PERFORMANCE</div>
            <div style={{fontSize:11, color:C.text1}}>
              {sel.speed_index_pct > 0 ? `Sells ${sel.speed_index_pct}% faster` : `Sells ${Math.abs(sel.speed_index_pct)}% slower`} than market average.
            </div>
          </div>
        )}

        <button onClick={()=>setShowReview(true)} style={{width:'100%', marginTop:12, background:C.bg3, border:`1px solid ${C.border}`, color:C.teal, borderRadius:6, padding:8, fontSize:11, fontWeight:700}}>CROWDSOURCE RELIABILITY</button>
      </Card>}
    </div>
  </div>;
}

function AnalyticsView({ user }) {
  const [sd,setSd]=useState(null); const [src,setSrc]=useState(null); const [trends,setTrends]=useState(null);
  const [heatmap,setHeatmap]=useState(null);
  const [calc, setCalc] = useState({price: 500000, rent: 4500});
  const [unlocked, setUnlocked] = useState(user?.role === 'agent' || user?.role === 'admin');

  useEffect(()=>{
    apiFetch("/analytics/supply-demand").then(d=>setSd(d||MOCK_SD));
    apiFetch("/analytics/sources").then(d=>setSrc(d||MOCK_SOURCES));
    apiFetch("/analytics/trends").then(d=>setTrends(d||MOCK_TRENDS));
    apiFetch("/analytics/heatmap").then(d=>setHeatmap(d||MOCK_HEATMAP));
  },[]);

  const sdData=(sd?.data||MOCK_SD.data);
  const srcData=(src?.sources||MOCK_SOURCES.sources);
  const trData=(trends?.trends||MOCK_TRENDS.trends);
  const hmData=(heatmap?.suburbs||[]);
  const maxSup=Math.max(...sdData.map(d=>d.supply||0));

  const calculatedYield = ((calc.rent * 12) / calc.price) * 100;

  return <div style={{display:"flex",flexDirection:"column",gap:14}}>
    {/* Investor Insights Row */}
    <div className="dashboard-grid-row" style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:14}}>
      <Card style={{padding:20}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14, letterSpacing:'0.1em'}}>ESTIMATED RENTAL YIELD</div>
        <BarChart data={[...hmData].sort((a,b)=>b.rental_yield-a.rental_yield)} labelKey="suburb" valueKey="rental_yield" color={C.amber}/>
        <div style={{fontSize:9,color:C.text2,marginTop:10}}>* Yield = (Avg Annual Rent / Avg Sale Price)</div>
      </Card>
      <Card style={{padding:20}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14, letterSpacing:'0.1em'}}>ABSORPTION RATE (DAYS)</div>
        <BarChart data={[...hmData].sort((a,b)=>b.absorption_rate-a.absorption_rate)} labelKey="suburb" valueKey="absorption_rate" color={C.violet}/>
        <div style={{fontSize:9,color:C.text2,marginTop:10}}>* Avg Days on Market. Lower is faster.</div>
      </Card>
      <Card style={{padding:20, background:`linear-gradient(135deg, ${C.bg1}, ${C.bg2})`}}>
        <div style={{fontSize:11,color:C.teal,fontFamily:"'IBM Plex Mono'",marginBottom:14, letterSpacing:'0.1em'}}>YIELD CALCULATOR</div>
        <div style={{display:'flex', flexDirection:'column', gap:10}}>
          <div>
            <div style={{fontSize:9, color:C.text2, marginBottom:4}}>ASSET PRICE (PGK)</div>
            <input type="number" value={calc.price} onChange={e=>setCalc({...calc, price: Number(e.target.value)})} style={{width:'100%', background:C.bg3, border:`1px solid ${C.border}`, borderRadius:4, padding:6, color:C.text0, fontSize:12}} />
          </div>
          <div>
            <div style={{fontSize:9, color:C.text2, marginBottom:4}}>MONTHLY RENT (PGK)</div>
            <input type="number" value={calc.rent} onChange={e=>setCalc({...calc, rent: Number(e.target.value)})} style={{width:'100%', background:C.bg3, border:`1px solid ${C.border}`, borderRadius:4, padding:6, color:C.text0, fontSize:12}} />
          </div>
          <div style={{marginTop:8, paddingTop:8, borderTop:`1px solid ${C.bg3}`, textAlign:'center'}}>
            <div style={{fontSize:10, color:C.text1}}>NET GROSS YIELD</div>
            <div style={{fontSize:24, fontWeight:800, color:C.amber}}>{calculatedYield.toFixed(2)}%</div>
          </div>
        </div>
      </Card>
    </div>

    <div className="dashboard-grid-row" style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      <Card style={{padding:20, position:'relative', overflow:'hidden'}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14}}>RENT PRICE TRENDS</div>
        <div style={{display:"flex",gap:10,marginBottom:12}}>
          {[["Waigani",C.teal],["Boroko",C.violet],["Gerehu",C.amber]].map(([s,c])=><div key={s} style={{display:"flex",alignItems:"center",gap:5,fontSize:11,color:C.text1}}><div style={{width:14,height:3,background:c,borderRadius:2}}/>{s}</div>)}
        </div>
        <div style={{filter: unlocked ? 'none' : 'blur(4px)', pointerEvents: unlocked ? 'auto' : 'none', transition: 'all 0.3s'}}>
           <LineChart trends={trData}/>
        </div>
        {!unlocked && (
          <div style={{position:'absolute', inset:0, background:'rgba(5,13,26,0.6)', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:20, textAlign:'center'}}>
             <div style={{fontSize:24, marginBottom:10}}>🔒</div>
             <div style={{fontSize:13, fontWeight:700, marginBottom:4}}>HISTORICAL TRENDS LOCKED</div>
             <div style={{fontSize:10, color:C.text1, marginBottom:16}}>Unlock 12 months of historical data for K10.00</div>
             <button onClick={() => {alert("Redirecting to payment..."); setUnlocked(true);}} style={{background:C.teal, color:C.bg0, border:'none', borderRadius:6, padding:'6px 16px', fontSize:11, fontWeight:700, cursor:'pointer'}}>UNLOCK ACCESS</button>
          </div>
        )}
      </Card>
      <Card style={{padding:20}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14}}>LISTINGS BY SOURCE</div>
        <BarChart data={srcData} labelKey="name" valueKey="count" color={C.teal}/>
      </Card>
    </div>

    <Card style={{padding:20}}>
      <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14}}>SUPPLY / DEMAND BY SUBURB</div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:14}}>
        {sdData.map(d=>{
          const ratio=(d.demand_score||50)/(Math.min(100,(d.supply/maxSup)*100)||50);
          const label=ratio>1.3?"High Demand":ratio<0.7?"Oversupply":"Balanced";
          const lc=ratio>1.3?C.green:ratio<0.7?C.red:C.amber;
          return <div key={d.suburb} style={{background:C.bg2,borderRadius:8,padding:"12px 14px",border:`1px solid ${C.border}`}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
              <span style={{fontSize:13,fontWeight:600,fontFamily:"'Barlow Condensed'"}}>{d.suburb}</span>
              <Badge label={label} color={lc} small/>
            </div>
            <div style={{fontSize:12,color:C.text2,marginBottom:6}}>{d.supply} listings · {fmt(d.avg_price)}/mo</div>
            <div style={{height:4,background:C.bg3,borderRadius:2,overflow:"hidden",marginBottom:4}}>
              <div style={{width:`${d.demand_score||50}%`,height:"100%",background:C.teal,borderRadius:2}}/>
            </div>
            <div style={{fontSize:9,color:C.text2}}>Demand index: {d.demand_score||50}/100</div>
          </div>;
        })}
      </div>
    </Card>
  </div>;
}

function FlagsView() {
  const [flagged,setFlagged]=useState([]);
  const [loading,setLoading]=useState(true);
  useEffect(()=>{
    setLoading(true);
    apiFetch("/analytics/middleman-flags").then(d=>{
      if(d?.flagged) setFlagged(d.flagged);
      else {
        const ls=mockListings(60).filter(l=>l.market_value?.label==="Overpriced"&&l.market_value?.pct_vs_avg>40);
        setFlagged(ls);
      }
      setLoading(false);
    });
  },[]);

  return <div style={{display:"flex",flexDirection:"column",gap:14}}>
    <Card style={{padding:"14px 18px",background:"rgba(239,68,68,.06)",border:`1px solid ${C.red}30`}}>
      <div style={{display:"flex",alignItems:"center",gap:10}}>
        <span style={{fontSize:18}}>🚩</span>
        <div>
          <div style={{fontFamily:"'Barlow Condensed'",fontSize:16,fontWeight:700}}>Middleman / Overpriced Flags</div>
          <div style={{fontSize:11,color:C.text2}}>Listings priced ≥40% above the suburb average from formal sites. May indicate agent markup or informal middlemen.</div>
        </div>
        <div style={{marginLeft:"auto",fontFamily:"'IBM Plex Mono'",fontSize:22,fontWeight:700,color:C.red}}>{flagged.length}</div>
      </div>
    </Card>
    <Card>
      {loading?<div style={{padding:40,textAlign:"center"}}><Spinner/></div>:
      <div style={{overflowX:"auto", width: "100%"}}>
        <table style={{width:"100%", minWidth: "800px", borderCollapse:"collapse"}}>
          <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
            {["Suburb","Title","Listed Price","Suburb Avg","Overprice %","Source","Posted"].map(h=><th key={h} style={{padding:"8px 12px",textAlign:"left",fontSize:10,color:C.text2,fontFamily:"'IBM Plex Mono'",whiteSpace:"nowrap"}}>{h}</th>)}
          </tr></thead>
          <tbody>{flagged.map(l=>(
            <tr key={l.listing_id} style={{borderBottom:`1px solid ${C.bg3}`,background:"rgba(239,68,68,.04)"}} onMouseEnter={e=>e.currentTarget.style.background="rgba(239,68,68,.08)"} onMouseLeave={e=>e.currentTarget.style.background="rgba(239,68,68,.04)"}>
              <td style={{padding:"9px 12px",color:C.text1,fontSize:12}}>{l.suburb}</td>
              <td style={{padding:"9px 12px",color:C.text0,fontSize:12,maxWidth:180,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{l.title}</td>
              <td style={{padding:"9px 12px",fontFamily:"'IBM Plex Mono'",fontSize:12,color:C.red,fontWeight:600}}>{fmt(l.price_monthly_k)}</td>
              <td style={{padding:"9px 12px",fontFamily:"'IBM Plex Mono'",fontSize:12,color:C.text1}}>{fmt(l.market_value?.benchmark_avg)}</td>
              <td style={{padding:"9px 12px"}}><Badge label={`+${l.market_value?.pct_vs_avg?.toFixed(0)}%`} color={C.red} small/></td>
              <td style={{padding:"9px 12px"}}><span style={{background:`${C.violet}20`,color:C.violet,borderRadius:4,padding:"2px 7px",fontSize:10,fontWeight:600}}>{l.source_site}</span></td>
              <td style={{padding:"9px 12px",color:C.text2,fontSize:11}}>{rel(l.scraped_at)}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>}
    </Card>
  </div>;
}

// ── APP ROOT ──────────────────────────────────────────────────────────────────

const RESOURCES_DATA = [
  {
    category: "Main Property Portals",
    items: [
      { name: "Hausples.com.pg", url: "https://www.hausples.com.pg", desc: "Largest active portal (rentals, sales, land)." },
      { name: "PNGRealEstate.com.pg", url: "https://www.pngrealestate.com.pg", desc: "Major residential and commercial listings." },
      { name: "Marketmeri.com (Real Estate Section)", url: "https://www.marketmeri.com", desc: "General classifieds with very active housing section." },
      { name: "PNGbuynrent.com", url: "https://www.pngbuynrent.com", desc: "Simplified property search platform." }
    ]
  },
  {
    category: "Major Real Estate Agencies",
    items: [
      { name: "LJ Hooker PNG", url: "https://www.ljhooker.com.pg", desc: "Established name, Port Moresby focus." },
      { name: "Ray White PNG", url: "https://www.raywhitepng.com", desc: "Large residential and commercial portfolio." },
      { name: "Strickland Real Estate", url: "https://www.sre.com.pg", desc: "Sales and high-end property management." },
      { name: "The Professionals", url: "https://www.theprofessionals.com.pg", desc: "Broad listings including Lae market." },
      { name: "Century 21 Siule Real Estate", url: "https://www.c21.com.pg", desc: "Global brand agency in PNG." },
      { name: "Budget Real Estate", url: "https://www.budgetrealestatepng.com", desc: "Mid-range and affordable housing." },
      { name: "Arthur Strachan", url: "https://www.arthurstrachan.com.pg", desc: "Go-to for Lae and Morobe Province." },
      { name: "DAC Real Estate", url: "https://www.dac.com.pg", desc: "Specialized property and management services." },
      { name: "Kenmok Real Estate", url: "http://www.kenmok.com.pg", desc: "100% PNG-owned firm (management/construction)." }
    ]
  },
  {
    category: "Developers & Management",
    items: [
      { name: "Pacific Palms Property", url: "https://www.pacificpalmsproperty.com.pg", desc: "Steamships Group (commercial/industrial/residential)." },
      { name: "Credit Corporation Properties", url: "https://www.creditcorporation.com.pg/properties", desc: "High-end assets like Era Matana/Dorina." },
      { name: "Nambawan Super (Property)", url: "https://www.nambawansuper.com.pg/property", desc: "Large owner of various residential estates." },
      { name: "Edai Town", url: "https://www.edaitown.com.pg", desc: "Large-scale residential development near POM." },
      { name: "Tuhava", url: "https://tuhava.com", desc: "Eco-friendly planned township and residential community." }
    ]
  }
];

function B2BView({ user }) {
  const [alerts, setAlerts] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBot, setShowBot] = useState(false);
  const [botStep, setBotStep] = useState(0);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiFetch("/b2b/alerts"),
      apiFetch("/b2b/forecasting"),
      apiFetch("/b2b/leads")
    ]).then(([a, f, l]) => {
      setAlerts(a?.alerts || []);
      setForecast(f?.forecast || []);
      setLeads(l?.leads || []);
      setLoading(false);
    });
  }, []);

  if (loading) return <div style={{padding:40, textAlign:'center'}}><Spinner/></div>;

  const botQuestions = [
    "What is your monthly budget (PGK)?",
    "Which suburb are you most interested in (Waigani, Boroko, etc.)?",
    "When are you planning to move?",
    "Thank you! You have been PRE-QUALIFIED. An agent will contact you soon."
  ];

  return (
    <div style={{display:'flex', flexDirection:'column', gap:20}}>
      {/* Bot Showcase Modal */}
      {showBot && (
        <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.8)', zIndex:2000, display:'flex', alignItems:'center', justifyContent:'center'}}>
           <Card style={{width:400, padding:24, border:`2px solid ${C.teal}`}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20}}>
                 <span style={{fontWeight:700}}>Facebook Messenger Bot (Simulation)</span>
                 <button onClick={()=>setShowBot(false)} style={{background:'none', border:'none', color:C.text2, cursor:'pointer'}}>✕</button>
              </div>
              <div style={{background:C.bg3, padding:12, borderRadius:8, marginBottom:16, fontSize:13}}>
                 <div style={{color:C.teal, fontSize:10, marginBottom:4, fontWeight:700}}>PNG PROPERTY BOT</div>
                 {botQuestions[botStep]}
              </div>
              {botStep < 3 ? (
                <div style={{display:'flex', gap:8}}>
                   <input autoFocus placeholder="Type your answer..." style={{flex:1, background:C.bg1, border:`1px solid ${C.border}`, borderRadius:6, padding:8, color:C.text0, fontSize:13}} onKeyDown={e => e.key === 'Enter' && setBotStep(s => s + 1)} />
                   <button onClick={()=>setBotStep(s=>s+1)} style={{background:C.teal, border:'none', borderRadius:6, padding:'0 16px', color:C.bg0, fontWeight:700, cursor:'pointer'}}>Send</button>
                </div>
              ) : (
                <button onClick={()=>{setShowBot(false); setBotStep(0);}} style={{width:'100%', background:C.teal, border:'none', borderRadius:6, padding:10, color:C.bg0, fontWeight:700, cursor:'pointer'}}>Close & View Lead in Dashboard</button>
              )}
           </Card>
        </div>
      )}

      <Card style={{padding:16, background:`rgba(20,184,200,0.05)`, border:`1px solid ${C.teal}44`, display:'flex', justifyContent:'space-between', alignItems:'center'}}>
         <div>
            <div style={{fontWeight:700, color:C.teal}}>Agent Intelligence Dashboard</div>
            <div style={{fontSize:11, color:C.text2}}>
              {user?.role === 'agent' ? "You have full access to competitor pricing and lead scoring." : "Upgrade to Agent Pro to unlock competitor tracking and hot leads."}
            </div>
         </div>
         <div style={{display:'flex', gap:10}}>
            <button onClick={()=>{alert("Exporting leads to CSV...");}} style={{background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:'8px 16px', color:C.text1, fontWeight:700, cursor:'pointer', fontSize:11}}>Bulk Export (.CSV)</button>
            <button onClick={()=>setShowBot(true)} style={{background:C.teal, border:'none', borderRadius:6, padding:'8px 16px', color:C.bg0, fontWeight:700, cursor:'pointer', fontSize:12}}>Test Messenger Bot Demo</button>
         </div>
      </Card>

      {/* Competitor Price Alerts */}
      <div>
        <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:14, letterSpacing:'0.1em'}}>COMPETITOR PRICING ALERTS</div>
        <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(350px, 1fr))', gap:14}}>
          {alerts.map((a, i) => (
            <Card key={i} style={{padding:18, borderLeft:`4px solid ${C.red}`}}>
              <div style={{fontSize:12, color:C.text2, marginBottom:4}}>YOUR LISTING</div>
              <div style={{fontSize:15, fontWeight:700, marginBottom:10}}>{a.my_listing.title} <span style={{color:C.text2}}>({fmt(a.my_listing.price)})</span></div>
              <div style={{display:'flex', flexDirection:'column', gap:8}}>
                {a.competitors.map((c, j) => (
                  <div key={j} style={{background:C.bg3, padding:10, borderRadius:8, display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                    <div>
                      <div style={{fontSize:10, color:C.text1}}>{c.source}</div>
                      <div style={{fontSize:13, fontWeight:600, color:C.red}}>{fmt(c.price)}</div>
                    </div>
                    <Badge label={`-${c.pct}% UNDER`} color={C.red} small />
                  </div>
                ))}
              </div>
            </Card>
          ))}
          {!alerts.length && <div style={{color:C.text2, fontSize:13, background:C.bg1, padding:20, borderRadius:8, border:`1px solid ${C.border}`}}>No immediate pricing threats detected in your portfolio.</div>}
        </div>
      </div>

      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:20}}>
        {/* Demand Forecasting */}
        <Card style={{padding:20}}>
          <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:16, letterSpacing:'0.1em'}}>MARKET OPPORTUNITY (SUPPLY GAP)</div>
          <div style={{display:'flex', flexDirection:'column', gap:12}}>
            {forecast.slice(0, 8).map((f, i) => (
              <div key={i} style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                <div>
                  <div style={{fontSize:14, fontWeight:700}}>{f.suburb} · {f.property_type}</div>
                  <div style={{fontSize:11, color:C.text2}}>{f.supply} listings available vs high demand</div>
                </div>
                <div style={{textAlign:'right'}}>
                   {f.spike_pct > 0 && <div style={{fontSize:10, color:C.green, fontWeight:700, marginBottom:4}}>📈 +{f.spike_pct}% Spike</div>}
                   <Badge label={`Opportunity: ${f.opportunity_score}%`} color={C.teal} small />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Lead Scoring */}
        <Card style={{padding:20}}>
          <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:16, letterSpacing:'0.1em'}}>HOT LEADS (PLATFORM SCORING)</div>
          <table style={{width:'100%', borderCollapse:'collapse'}}>
            <thead>
              <tr style={{borderBottom:`1px solid ${C.border}`}}>
                <th style={{padding:8, textAlign:'left', fontSize:10, color:C.text2}}>NAME</th>
                <th style={{padding:8, textAlign:'left', fontSize:10, color:C.text2}}>SCORE</th>
                <th style={{padding:8, textAlign:'left', fontSize:10, color:C.text2}}>ACTIVITY</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((l, i) => (
                <tr key={i} style={{borderBottom:`1px solid ${C.bg3}`}}>
                  <td style={{padding:8}}>
                    <div style={{fontSize:13, fontWeight:600}}>{l.name}</div>
                    <div style={{fontSize:10, color:C.text2}}>Interested in {l.interest}</div>
                  </td>
                  <td style={{padding:8}}>
                    <div style={{display:'flex', alignItems:'center', gap:6}}>
                       <Badge label={l.score} color={l.status === 'Hot' ? C.green : C.amber} small />
                       {l.is_qualified && <span title="Bot Qualified" style={{fontSize:12}}>✅</span>}
                    </div>
                  </td>
                  <td style={{padding:8, fontSize:11, color:C.text2}}>{l.last_active}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}

function ValuationView() {
  const [form, setForm] = useState({suburb:"Waigani", type:"House", bedrooms:3, sqm: 200});
  const [estimate, setEstimate] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPay, setShowPay] = useState(false);

  const getEstimate = async () => {
    setLoading(true);
    const res = await apiFetch("/valuation/estimate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(form)
    });
    setEstimate(res);
    setLoading(false);
  };

  const getReport = async (payRef) => {
    setLoading(true);
    const res = await apiFetch(`/valuation/report?payment_ref=${payRef}`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(form)
    });
    if (res) setReport(res);
    setShowPay(false);
    setLoading(false);
  };

  return (
    <div style={{display:'flex', flexDirection:'column', gap:20}}>
      {/* Payment Modal */}
      {showPay && (
        <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.8)', zIndex:2000, display:'flex', alignItems:'center', justifyContent:'center'}}>
           <Card style={{width:400, padding:24, textAlign:'center'}}>
              <div style={{fontSize:18, fontWeight:800, marginBottom:10}}>Detailed Market Comparison</div>
              <div style={{fontSize:13, color:C.text1, marginBottom:20}}>Unlocking this report costs <b>K25.00</b> via Lumi or Cellmoni.</div>
              <div style={{background:C.bg3, padding:16, borderRadius:8, marginBottom:20, textAlign:'left'}}>
                 <div style={{fontSize:10, color:C.text2, marginBottom:4}}>MOCK PAYMENT REFERENCE</div>
                 <code style={{color:C.teal}}>PAY-AVM-123456</code>
              </div>
              <div style={{display:'flex', gap:10}}>
                 <button onClick={()=>setShowPay(false)} style={{flex:1, background:C.bg1, border:`1px solid ${C.border}`, color:C.text1, borderRadius:6, padding:10}}>Cancel</button>
                 <button onClick={()=>getReport("PAY-AVM-123456")} style={{flex:1, background:C.teal, color:C.bg0, border:'none', borderRadius:6, padding:10, fontWeight:700}}>Verify & Unlock</button>
              </div>
           </Card>
        </div>
      )}

      <div className="dashboard-grid-row" style={{display:'grid', gridTemplateColumns:'340px 1fr', gap:20}}>
         <Card style={{padding:24, height:'fit-content'}}>
            <div style={{fontSize:11, color:C.teal, fontFamily:"'IBM Plex Mono'", marginBottom:16, letterSpacing:'0.1em'}}>VALUE MY HOME</div>
            <div style={{display:'flex', flexDirection:'column', gap:16}}>
               <div>
                  <div style={{fontSize:10, color:C.text2, marginBottom:4}}>SUBURB</div>
                  <select value={form.suburb} onChange={e=>setForm({...form, suburb: e.target.value})} style={{width:'100%', background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:8, color:C.text0}}>
                     {SUBURBS.map(s=><option key={s} value={s}>{s}</option>)}
                  </select>
               </div>
               <div>
                  <div style={{fontSize:10, color:C.text2, marginBottom:4}}>PROPERTY TYPE</div>
                  <select value={form.type} onChange={e=>setForm({...form, type: e.target.value})} style={{width:'100%', background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:8, color:C.text0}}>
                     {TYPES.map(t=><option key={t} value={t}>{t}</option>)}
                  </select>
               </div>
               <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:10}}>
                  <div>
                     <div style={{fontSize:10, color:C.text2, marginBottom:4}}>BEDROOMS</div>
                     <input type="number" value={form.bedrooms} onChange={e=>setForm({...form, bedrooms: Number(e.target.value)})} style={{width:'100%', background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:8, color:C.text0}} />
                  </div>
                  <div>
                     <div style={{fontSize:10, color:C.text2, marginBottom:4}}>LAND SIZE (SQM)</div>
                     <input type="number" value={form.sqm} onChange={e=>setForm({...form, sqm: Number(e.target.value)})} style={{width:'100%', background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:8, color:C.text0}} />
                  </div>
               </div>
               <button onClick={getEstimate} style={{width:'100%', background:C.teal, color:C.bg0, border:'none', borderRadius:8, padding:12, fontWeight:700, marginTop:10}}>
                  {loading ? "CALCULATING..." : "GENERATE FREE ESTIMATE"}
               </button>
            </div>
         </Card>

         <div style={{display:'flex', flexDirection:'column', gap:20}}>
            {estimate ? (
               <Card style={{padding:24, background:`linear-gradient(135deg, ${C.bg1}, #0d1e30)`, animation:'fadeUp 0.3s ease'}}>
                  <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:24}}>
                     <div>
                        <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:4}}>ESTIMATED MARKET VALUE</div>
                        <div style={{fontSize:36, fontWeight:800, color:C.text0}}>{fmt(estimate.estimate)}</div>
                        <div style={{fontSize:12, color:C.text1}}>Range: {fmt(estimate.low_bound)} – {fmt(estimate.high_bound)}</div>
                     </div>
                     <div style={{textAlign:'right'}}>
                        <div style={{fontSize:24, fontWeight:800, color:estimate.confidence > 70 ? C.green : C.amber}}>{estimate.confidence}%</div>
                        <div style={{fontSize:9, color:C.text2}}>CONFIDENCE SCORE</div>
                     </div>
                  </div>

                  <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:12}}>LOCAL COMPARABLES (RECENT SCRAPES)</div>
                  <div style={{display:'flex', flexDirection:'column', gap:8, marginBottom:24}}>
                     {estimate.comparables.map((c, i) => (
                        <div key={i} style={{background:C.bg3, padding:10, borderRadius:8, display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                           <div style={{fontSize:13}}>{c.title} <span style={{fontSize:10, color:C.text2}}>via {c.source}</span></div>
                           <div style={{fontWeight:700, color:C.teal}}>{fmt(c.price)}</div>
                        </div>
                     ))}
                  </div>

                  {!report ? (
                    <div style={{background:C.bg2, border:`1px solid ${C.teal}44`, padding:20, borderRadius:12, textAlign:'center'}}>
                       <div style={{fontSize:15, fontWeight:700, marginBottom:8}}>Unlock Premium Market Report</div>
                       <div style={{fontSize:12, color:C.text2, marginBottom:16}}>Get detailed investment analysis, 5-year price forecasts, and demand insights for {form.suburb}.</div>
                       <button onClick={()=>setShowPay(true)} style={{background:C.teal, color:C.bg0, border:'none', borderRadius:6, padding:'8px 16px', fontWeight:700}}>UNLOCK FOR K25.00</button>
                    </div>
                  ) : (
                    <div style={{background:`rgba(34,197,94,0.05)`, border:`1px solid ${C.green}44`, padding:20, borderRadius:12, animation:'fadeUp 0.3s ease'}}>
                       <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:14}}>
                          <div style={{fontSize:15, fontWeight:700, color:C.green}}>✓ Premium Report Unlocked</div>
                          <Badge label={report.report_id} color={C.green} />
                       </div>
                       <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:14, marginBottom:14}}>
                          <div style={{background:C.bg3, padding:12, borderRadius:8}}>
                             <div style={{fontSize:9, color:C.text2, marginBottom:4}}>SUBURB DEMAND</div>
                             <div style={{fontSize:14, fontWeight:700, color:C.teal}}>{report.market_trends.suburb_demand}</div>
                          </div>
                          <div style={{background:C.bg3, padding:12, borderRadius:8}}>
                             <div style={{fontSize:9, color:C.text2, marginBottom:4}}>5-YEAR FORECAST</div>
                             <div style={{fontSize:14, fontWeight:700, color:C.green}}>{report.investment_analysis["5_year_forecast"]}</div>
                          </div>
                       </div>

                       <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:14, marginBottom:14}}>
                          <div style={{background:C.bg3, padding:12, borderRadius:8}}>
                             <div style={{fontSize:9, color:C.text2, marginBottom:4}}>SAFETY SCORE</div>
                             <div style={{fontSize:14, fontWeight:700, color:report.neighborhood_safety.score > 70 ? C.green : C.amber}}>
                               {report.neighborhood_safety.score}% ({report.neighborhood_safety.status})
                             </div>
                             <div style={{fontSize:8, color:C.text2, marginTop:4}}>Patrol: {report.neighborhood_safety.patrol_presence}</div>
                          </div>
                          <div style={{background:C.bg3, padding:12, borderRadius:8}}>
                             <div style={{fontSize:9, color:C.text2, marginBottom:4}}>PRICE HISTORY</div>
                             <div style={{display:'flex', flexDirection:'column', gap:2}}>
                                {report.price_history.slice(-3).map(h => (
                                  <div key={h.year} style={{display:'flex', justifyContent:'space-between', fontSize:10}}>
                                    <span style={{color:C.text2}}>{h.year}</span>
                                    <span style={{fontWeight:600}}>{fmt(h.avg_price)}</span>
                                  </div>
                                ))}
                             </div>
                          </div>
                       </div>
                       <button style={{width:'100%', marginTop:14, background:C.bg3, border:`1px solid ${C.border}`, color:C.text0, borderRadius:6, padding:10, fontWeight:700}}>DOWNLOAD PDF REPORT</button>
                    </div>
                  )}
               </Card>
            ) : (
               <Card style={{padding:60, textAlign:'center', color:C.text2}}>
                  <div style={{fontSize:48, marginBottom:20}}>🏠</div>
                  <div style={{fontSize:18, fontWeight:700, color:C.text1}}>Ready to value your property?</div>
                  <div style={{fontSize:13}}>Fill in the details on the left to generate an instant estimate using PNG Property Big Data.</div>
               </Card>
            )}
         </div>
      </div>
    </div>
  );
}

function VaultView({ user }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [packaging, setPackaging] = useState(false);
  const [shareData, setShareData] = useState(null);

  const checklist = [
    {id: "ID", label: "National ID / Passport"},
    {id: "Slip", label: "Last 3 Salary Slips"},
    {id: "Nasfund", label: "NASFUND Statement"},
    {id: "Nambawan", label: "Nambawan Super Statement"},
    {id: "Offer", label: "Letter of Offer"}
  ];

  const refresh = useCallback(async () => {
    setLoading(true);
    const d = await apiFetch("/vault/status");
    setDocs(d?.documents || []);
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const onUpload = async (type, file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await apiFetch(`/vault/upload?doc_type=${type}`, {
      method: "POST",
      body: formData
    });
    if (res) refresh();
  };

  const onPackage = async () => {
    setPackaging(true);
    const res = await apiFetch("/vault/package", { method: "POST" });
    if (res) setShareData(res);
    setPackaging(false);
  };

  if (loading) return <div style={{padding:40, textAlign:'center'}}><Spinner/></div>;

  const getDoc = (type) => docs.find(d => d.type === type);

  return (
    <div style={{display:'flex', flexDirection:'column', gap:20}}>
       <Card style={{padding:20, background:`linear-gradient(135deg, ${C.bg1}, #0a202d)`}}>
          <div style={{fontSize:11, color:C.teal, fontFamily:"'IBM Plex Mono'", marginBottom:14, letterSpacing:'0.1em'}}>MORTGAGE READINESS</div>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start'}}>
             <div style={{maxWidth:600}}>
                <div style={{fontSize:18, fontWeight:800, marginBottom:8}}>Bank-Ready Document Vault</div>
                <div style={{fontSize:13, color:C.text1, lineHeight:1.5}}>
                   Skip the 3-month wait. Upload your required documents now to create a pre-packaged digital folder.
                   Share it directly with BSP or Kina Bank lending officers once you find your dream home.
                </div>
             </div>
             <div style={{textAlign:'right'}}>
                <div style={{fontSize:24, fontWeight:800, color:docs.length === checklist.length ? C.green : C.amber}}>{Math.round((docs.length/checklist.length)*100)}%</div>
                <div style={{fontSize:10, color:C.text2}}>COMPLETION</div>
             </div>
          </div>
       </Card>

       <div className="dashboard-grid-row" style={{display:'grid', gridTemplateColumns:'1fr 340px', gap:14}}>
          <Card style={{padding:20}}>
             <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:16}}>DOCUMENT CHECKLIST</div>
             <div style={{display:'flex', flexDirection:'column', gap:12}}>
                {checklist.map(item => {
                   const doc = getDoc(item.id);
                   return (
                     <div key={item.id} style={{display:'flex', justifyContent:'space-between', alignItems:'center', padding:"12px 16px", background:C.bg3, borderRadius:10, border:`1px solid ${doc ? C.teal+'44' : C.border}`}}>
                        <div>
                           <div style={{fontSize:14, fontWeight:700, color:doc ? C.text0 : C.text1}}>{item.label}</div>
                           {doc && <div style={{fontSize:10, color:C.teal}}>Uploaded {rel(doc.uploaded_at)} · {doc.filename}</div>}
                        </div>
                        {doc ? (
                          <Badge label="✓ READY" color={C.green} />
                        ) : (
                          <label style={{background:C.bg1, border:`1px solid ${C.border}`, borderRadius:6, padding:"6px 12px", fontSize:11, cursor:'pointer', fontWeight:700, color:C.text2}}>
                             UPLOAD
                             <input type="file" style={{display:'none'}} onChange={e => onUpload(item.id, e.target.files[0])} />
                          </label>
                        )}
                     </div>
                   );
                })}
             </div>
          </Card>

          <div style={{display:'flex', flexDirection:'column', gap:14}}>
             <Card style={{padding:20, background:C.bg2, textAlign:'center'}}>
                <div style={{fontSize:32, marginBottom:10}}>📁</div>
                <div style={{fontSize:15, fontWeight:700, marginBottom:8}}>Package for Bank</div>
                <div style={{fontSize:12, color:C.text2, marginBottom:20}}>Generate a secure single-link access for your lending officer at BSP or Kina Bank.</div>
                <button
                  disabled={docs.length === 0 || packaging}
                  onClick={onPackage}
                  style={{width:'100%', background:C.teal, color:C.bg0, border:'none', borderRadius:8, padding:12, fontWeight:700, cursor:docs.length ? 'pointer' : 'not-allowed', opacity:docs.length ? 1 : 0.5}}
                >
                   {packaging ? "PACKAGING..." : "CREATE BANK FOLDER"}
                </button>
             </Card>

             {shareData && (
               <Card style={{padding:20, border:`1px solid ${C.green}44`, animation:'fadeUp 0.3s ease'}}>
                  <div style={{fontSize:11, color:C.green, fontWeight:700, marginBottom:10}}>✓ FOLDER READY</div>
                  <div style={{background:C.bg3, padding:8, borderRadius:6, fontSize:10, color:C.teal, fontFamily:"'IBM Plex Mono'", marginBottom:10, wordBreak:'break-all'}}>
                     {shareData.share_url}
                  </div>
                  <div style={{fontSize:11, color:C.text2, marginBottom:16}}>Expires in 7 days. Share this link with your bank officer.</div>

                  <div style={{fontSize:10, color:C.text1, marginBottom:8, borderTop:`1px solid ${C.bg3}`, paddingTop:12}}>DIRECT SUBMISSION</div>
                  <div style={{display:'flex', flexDirection:'column', gap:8}}>
                     <button onClick={()=>{alert("Application submitted to BSP Lending Team!");}} style={{background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:8, color:C.text0, fontSize:10, fontWeight:700, cursor:'pointer'}}>SUBMIT TO BSP</button>
                     <button onClick={()=>{alert("Application submitted to Kina Bank!");}} style={{background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:8, color:C.text0, fontSize:10, fontWeight:700, cursor:'pointer'}}>SUBMIT TO KINA BANK</button>
                  </div>
               </Card>
             )}
          </div>
       </div>
    </div>
  );
}

function NotificationsView() {
  const [searches, setSearches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/notifications/active").then(d => {
      setSearches(d?.saved_searches || []);
      setLoading(false);
    });
  }, []);

  if (loading) return <div style={{padding:40, textAlign:'center'}}><Spinner/></div>;

  return (
    <div style={{display:'flex', flexDirection:'column', gap:20}}>
       <Card style={{padding:20, background:`linear-gradient(135deg, ${C.bg1}, ${C.bg2})`}}>
          <div style={{fontSize:11, color:C.teal, fontFamily:"'IBM Plex Mono'", marginBottom:14, letterSpacing:'0.1em'}}>WHATSAPP PRICE DROP ALERTS</div>
          <div style={{fontSize:14, color:C.text1, lineHeight:1.5}}>
             PNG users on social plans can now "Follow" any search or specific listing.
             Our engine monitors the market 24/7 and pings your WhatsApp immediately when:
             <ul style={{marginTop:10, marginLeft:20}}>
                <li>A property price drops by &gt;5%</li>
                <li>A new listing matching your criteria is discovered</li>
                <li>A verified agency listing becomes available</li>
             </ul>
          </div>
       </Card>

       <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:4, letterSpacing:'0.1em'}}>YOUR ACTIVE ALERTS</div>
       <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(300px, 1fr))', gap:14}}>
          {searches.map((s, i) => (
            <Card key={i} style={{padding:18}}>
               <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:10}}>
                  <div style={{fontSize:15, fontWeight:700}}>{s.name}</div>
                  <Badge label="ACTIVE" color={C.green} small />
               </div>
               <div style={{fontSize:11, color:C.text2, marginBottom:12}}>
                  Criteria: {Object.entries(s.criteria).filter(([_,v])=>v).map(([k,v]) => `${k}=${v}`).join(", ")}
               </div>
               <div style={{display:'flex', gap:8}}>
                  <button style={{flex:1, background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:6, color:C.text2, fontSize:11}}>Edit</button>
                  <button style={{flex:1, background:C.bg3, border:`1px solid ${C.red}44`, borderRadius:6, padding:6, color:C.red, fontSize:11}}>Delete</button>
               </div>
            </Card>
          ))}
          {!searches.length && <div style={{color:C.text2, fontSize:13}}>No active followed searches yet. Go to Listings to start following.</div>}
       </div>
    </div>
  );
}

function LenderPortalView() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching mortgage-ready leads
    setTimeout(() => {
      setLeads([
        {id: "L1", name: "John Doe", suburb: "Waigani", budget: "K500,000", score: 88, docs: 5},
        {id: "L2", name: "Sarah Smith", suburb: "Boroko", budget: "K750,000", score: 92, docs: 5},
        {id: "L3", name: "Michael Wong", suburb: "Gordons", budget: "K1,200,000", score: 75, docs: 4},
      ]);
      setLoading(false);
    }, 800);
  }, []);

  if (loading) return <div style={{padding:40, textAlign:'center'}}><Spinner/></div>;

  return (
    <div style={{display:'flex', flexDirection:'column', gap:20}}>
       <Card style={{padding:20, background:`linear-gradient(135deg, ${C.bg1}, ${C.bg2})`}}>
          <div style={{fontSize:11, color:C.teal, fontFamily:"'IBM Plex Mono'", marginBottom:14}}>LENDER DASHBOARD (LEAD GEN)</div>
          <div style={{fontSize:15, fontWeight:700, marginBottom:8}}>Qualified Mortgage Leads</div>
          <div style={{fontSize:12, color:C.text1}}>These users have completed their Document Vault and are ready for pre-approval.</div>
       </Card>

       <Card>
          <table style={{width:'100%', borderCollapse:'collapse'}}>
             <thead>
                <tr style={{borderBottom:`1px solid ${C.border}`}}>
                   <th style={{padding:12, textAlign:'left', fontSize:10, color:C.text2}}>APPLICANT</th>
                   <th style={{padding:12, textAlign:'left', fontSize:10, color:C.text2}}>TARGET SUBURB</th>
                   <th style={{padding:12, textAlign:'left', fontSize:10, color:C.text2}}>BUDGET</th>
                   <th style={{padding:12, textAlign:'left', fontSize:10, color:C.text2}}>READINESS</th>
                   <th style={{padding:12, textAlign:'left', fontSize:10, color:C.text2}}>ACTION</th>
                </tr>
             </thead>
             <tbody>
                {leads.map(l => (
                   <tr key={l.id} style={{borderBottom:`1px solid ${C.bg3}`}}>
                      <td style={{padding:12}}>
                         <div style={{fontSize:13, fontWeight:600}}>{l.name}</div>
                         <div style={{fontSize:10, color:C.text2}}>ID: {l.id}</div>
                      </td>
                      <td style={{padding:12, fontSize:12}}>{l.suburb}</td>
                      <td style={{padding:12, fontSize:12, fontWeight:700, color:C.teal}}>{l.budget}</td>
                      <td style={{padding:12}}>
                         <div style={{display:'flex', alignItems:'center', gap:8}}>
                            <Badge label={`${l.docs}/5 DOCS`} color={l.docs === 5 ? C.green : C.amber} small />
                            <span style={{fontSize:10, color:C.text1}}>{l.score}% Score</span>
                         </div>
                      </td>
                      <td style={{padding:12}}>
                         <button style={{background:C.teal, border:'none', borderRadius:4, padding:"6px 12px", color:C.bg0, fontSize:10, fontWeight:700, cursor:'pointer'}}>VIEW BANK FOLDER</button>
                      </td>
                   </tr>
                ))}
             </tbody>
          </table>
       </Card>
    </div>
  );
}

function DeveloperPortalView() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadKeys = async () => {
    setLoading(true);
    const res = await apiFetch("/developer/keys");
    if (res) setKeys(res.api_keys || []);
    setLoading(false);
  };

  useEffect(() => { loadKeys(); }, []);

  const generateKey = async () => {
    const res = await apiFetch("/developer/keys", { method: "POST" });
    if (res) loadKeys();
  };

  if (loading) return <div style={{padding:40, textAlign:'center'}}><Spinner/></div>;

  return (
    <div style={{display:'flex', flexDirection:'column', gap:20}}>
       <Card style={{padding:20, background:`linear-gradient(135deg, ${C.bg1}, ${C.bg2})`}}>
          <div style={{fontSize:11, color:C.teal, fontFamily:"'IBM Plex Mono'", marginBottom:14}}>DEVELOPER PORTAL</div>
          <div style={{fontSize:15, fontWeight:700, marginBottom:8}}>Structured Data API</div>
          <div style={{fontSize:12, color:C.text1, lineHeight:1.5}}>
             Integrate PNG property data into your own applications. Our API provides cleaned,
             deduplicated listings in JSON format. Usage is billed per 1,000 requests.
          </div>
       </Card>

       <Card style={{padding:24}}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20}}>
             <div style={{fontSize:16, fontWeight:700}}>Your API Keys</div>
             <button onClick={generateKey} style={{background:C.teal, color:C.bg0, border:'none', borderRadius:6, padding:'8px 16px', fontWeight:700, cursor:'pointer'}}>Generate New Key</button>
          </div>

          <div style={{display:'flex', flexDirection:'column', gap:12}}>
             {keys.map((k, i) => (
               <div key={i} style={{background:C.bg3, padding:16, borderRadius:12, border:`1px solid ${C.border}`}}>
                  <div style={{display:'flex', justifyContent:'space-between', marginBottom:10}}>
                     <code style={{color:C.teal, fontSize:13, fontWeight:700}}>{k.key}</code>
                     <Badge label="ACTIVE" color={C.green} small />
                  </div>
                  <div style={{display:'flex', gap:20, fontSize:11, color:C.text2}}>
                     <span>Created: {rel(k.created_at)}</span>
                     <span>Requests: {k.usage_count}</span>
                  </div>
               </div>
             ))}
             {!keys.length && <div style={{textAlign:'center', padding:20, color:C.text2, fontSize:13}}>No API keys generated yet.</div>}
          </div>
       </Card>

       <Card style={{padding:24}}>
          <div style={{fontSize:16, fontWeight:700, marginBottom:16}}>Documentation Quickstart</div>
          <div style={{background:C.bg0, padding:16, borderRadius:8, fontFamily:"'IBM Plex Mono'", fontSize:12, color:C.teal, border:`1px solid ${C.border}`}}>
             GET /api/v1/listings/export?api_key=YOUR_KEY
          </div>
       </Card>
    </div>
  );
}

function SettingsView({ user }) {
  const planNames = {buyer: "Free Plan", agent: "Agency Pro (K150/mo)", lender: "Lender Enterprise", developer: "Developer API Access"};
  return (
    <div style={{display:'flex', flexDirection:'column', gap:20}}>
       <Card style={{padding:24}}>
          <div style={{fontSize:18, fontWeight:800, marginBottom:16}}>Subscription & Billing</div>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', background:C.bg3, padding:16, borderRadius:12}}>
             <div>
                <div style={{fontSize:10, color:C.text2, marginBottom:4}}>CURRENT PLAN</div>
                <div style={{fontSize:16, fontWeight:700, color:C.teal}}>{planNames[user?.role] || "Unknown Plan"}</div>
             </div>
             <button style={{background:C.teal, color:C.bg0, border:'none', borderRadius:6, padding:'8px 16px', fontWeight:700, cursor:'pointer'}}>Manage Plan</button>
          </div>
          <div style={{marginTop:20, fontSize:12, color:C.text1}}>
             Your next billing date is April 15, 2024.
          </div>
       </Card>
       <Card style={{padding:24}}>
          <div style={{fontSize:18, fontWeight:800, marginBottom:16}}>Personal Information</div>
          <div style={{display:'flex', flexDirection:'column', gap:12}}>
             <div style={{display:'grid', gridTemplateColumns:'120px 1fr'}}>
                <span style={{fontSize:12, color:C.text2}}>Full Name</span>
                <span style={{fontSize:12, fontWeight:600}}>{user?.full_name}</span>
             </div>
             <div style={{display:'grid', gridTemplateColumns:'120px 1fr'}}>
                <span style={{fontSize:12, color:C.text2}}>Identifier</span>
                <span style={{fontSize:12, fontWeight:600}}>{user?.email || user?.phone}</span>
             </div>
          </div>
       </Card>
    </div>
  );
}

function ResourcesView() {
  return (
    <div style={{display:"flex", flexDirection:"column", gap:24}}>
      {RESOURCES_DATA.map(cat => (
        <div key={cat.category}>
          <div style={{fontSize:11, color:C.text2, fontFamily:"'IBM Plex Mono'", marginBottom:16, letterSpacing:"0.1em"}}>{cat.category.toUpperCase()}</div>
          <div style={{display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(280px, 1fr))", gap:16}}>
            {cat.items.map(item => (
              <Card key={item.name} className="fade-up kpi-card" style={{padding:18}} onClick={() => window.open(item.url, "_blank")}>
                <div style={{display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:8}}>
                  <div style={{fontSize:15, fontWeight:700, fontFamily:"'Barlow Condensed'", color:C.teal}}>{item.name}</div>
                  <span style={{fontSize:14}}>↗</span>
                </div>
                <div style={{fontSize:12, color:C.text2, lineHeight:1.4}}>{item.desc}</div>
                <div style={{marginTop:12, fontSize:10, color:C.text1, fontFamily:"'IBM Plex Mono'", opacity:0.6}}>{new URL(item.url).hostname}</div>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("png_user") || "null"));
  const [showDashboard, setShowDashboard] = useState(!!localStorage.getItem("png_token"));
  const [view,setView]=useState("dashboard");
  const [showScrape,setShowScrape]=useState(false);
  const [overview,setOverview]=useState(null);
  const [heatmap,setHeatmap]=useState(null);
  const [trends,setTrends]=useState(null);
  const [sd,setSd]=useState(null);
  const [sources,setSources]=useState(null);
  const [loading,setLoading]=useState(true);

  const handleAuthSuccess = (authData) => {
    localStorage.setItem("png_token", authData.access_token);
    localStorage.setItem("png_user", JSON.stringify(authData.user));
    setUser(authData.user);
    setShowDashboard(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("png_token");
    localStorage.removeItem("png_user");
    setUser(null);
    setShowDashboard(false);
  };

  const loadAll=useCallback(async()=>{
    if (!showDashboard) return;
    setLoading(true);
    const [ov,hm,tr,s,sr]=await Promise.all([
      apiFetch("/analytics/overview"),apiFetch("/analytics/heatmap"),
      apiFetch("/analytics/trends"),apiFetch("/analytics/supply-demand"),apiFetch("/analytics/sources"),
    ]);
    setOverview(ov||MOCK_OVERVIEW); setHeatmap(hm||MOCK_HEATMAP);
    setTrends(tr||MOCK_TRENDS); setSd(s||MOCK_SD); setSources(sr||MOCK_SOURCES);
    setLoading(false);
  },[showDashboard]);

  useEffect(()=>{loadAll();},[loadAll]);

  return (
    <>
      <style>{FONTS}</style>
      {!showDashboard ? (
        <Landing onEnterDashboard={handleAuthSuccess} apiFetch={apiFetch} />
      ) : (
      <div className="app-shell" style={{display:"flex",height:"100vh",overflow:"hidden"}}>
        <Sidebar active={view} onNav={setView} onLogout={handleLogout} user={user}/>
        <div className="main-content" style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
          <Topbar view={view} overview={overview} onScrape={()=>setShowScrape(true)} onLogout={handleLogout} loading={loading} user={user}/>
          <div style={{flex:1,overflow:"auto",padding:20}}>
            {view==="dashboard"&&<DashboardView overview={overview} heatmap={heatmap} trends={trends} sd={sd} sources={sources} onNav={setView}/>}
            {view==="listings" &&<ListingsView/>}
            {view==="heatmap"  &&<HeatmapView user={user}/>}
            {view==="analytics"&&<AnalyticsView user={user}/>}
            {view==="notifications" && <NotificationsView />}
            {view==="vault" && <VaultView user={user}/>}
            {view==="valuation" && <ValuationView />}
            {view==="b2b"      &&<B2BView user={user}/>}
            {view==="flags"    &&<FlagsView/>}
            {view==="sources"&&<ResourcesView/>}
            {view==="lender" && <LenderPortalView />}
            {view==="dev" && <DeveloperPortalView />}
            {view==="settings" && <SettingsView user={user}/>}
          </div>
        </div>
      </div>
      )}
      {showScrape&&<ScrapePanel onClose={()=>setShowScrape(false)} onRefresh={loadAll}/>}
    </>
  );
}
