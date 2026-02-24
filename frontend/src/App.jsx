import { useState, useEffect, useCallback, useRef } from "react";

// ── API BASE ──────────────────────────────────────────────────────────────────
const API = "http://localhost:8000/api";

async function apiFetch(path, opts = {}) {
  try {
    const r = await fetch(`${API}${path}`, opts);
    if (!r.ok) throw new Error(`${r.status}`);
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
const MOCK_HEATMAP  = {suburbs:SUBURBS.map(s=>({suburb:s,avg_price:({Waigani:4470,Boroko:3150,Gerehu:1880,Gordons:5957,Hohola:1600,Tokarara:2275,Koki:2900,Badili:3325,"Six Mile":1450,"Eight Mile":1225}[s]||2000),listings:randRange(15,75),lat:({Waigani:-9.4298,Boroko:-9.4453,Gerehu:-9.4736,Gordons:-9.4201,Hohola:-9.4512,Tokarara:-9.4580,Koki:-9.4721,Badili:-9.4600,"Six Mile":-9.4150,"Eight Mile":-9.3900}[s]||-9.44),lng:({Waigani:147.1812,Boroko:147.1769,Gerehu:147.1609,Gordons:147.1739,Hohola:147.1651,Tokarara:147.1700,Koki:147.1847,Badili:147.1900,"Six Mile":147.1500,"Eight Mile":147.1420}[s]||147.18)}))};
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
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&family=Barlow:wght@400;500;600&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: ${C.bg0}; color: ${C.text0}; font-family: 'Barlow', sans-serif; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: ${C.bg1}; }
::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 2px; }
@keyframes fadeUp { from { opacity:0; transform:translateY(12px);} to { opacity:1; transform:none;} }
@keyframes pulse  { 0%,100%{opacity:1;} 50%{opacity:.35;} }
@keyframes spin   { to { transform: rotate(360deg); } }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.fade-up { animation: fadeUp .4s ease both; }
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

function Card({children, style={}, className=""}) {
  return <div className={className} style={{background:C.bg1,border:`1px solid ${C.border}`,borderRadius:12,...style}}>{children}</div>;
}

function Spinner() {
  return <div style={{width:18,height:18,border:`2px solid ${C.border}`,borderTopColor:C.teal,borderRadius:"50%",animation:"spin .7s linear infinite",flexShrink:0}} />;
}

function KpiCard({label, value, sub, accent, icon, delay=0}) {
  return <Card className="fade-up" style={{padding:"18px 20px",animationDelay:`${delay}ms`}}>
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
function HeatmapViz({suburbs, selected, onSelect}) {
  if (!suburbs?.length) return null;
  const LAT0=-9.505,LAT1=-9.37,LNG0=147.13,LNG1=147.21,W=520,H=320;
  const toX = lng => ((lng-LNG0)/(LNG1-LNG0))*W;
  const toY = lat => ((lat-LAT0)/(LAT1-LAT0))*H;
  const maxL = Math.max(...suburbs.map(s=>s.listings||1));
  const rOf  = l => 22+((l/maxL)**0.5)*28;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:"100%",height:"auto"}}>
      <defs><pattern id="g" x="0" y="0" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="8" cy="8" r=".6" fill={C.bg3}/></pattern></defs>
      <rect width={W} height={H} fill="url(#g)"/>
      {suburbs.map(s=>{
        if(!s.lat||!s.lng) return null;
        const x=toX(s.lng), y=toY(s.lat), r=rOf(s.listings||20);
        const col=priceColor(s.avg_price);
        const sel=selected===s.suburb;
        return <g key={s.suburb} onClick={()=>onSelect(sel?null:s.suburb)} style={{cursor:"pointer"}}>
          <circle cx={x} cy={y} r={r*1.5} fill={`${col}10`}/>
          {sel&&<circle cx={x} cy={y} r={r+8} fill="none" stroke={col} strokeWidth={1.5} strokeDasharray="4 3"/>}
          <circle cx={x} cy={y} r={r} fill={`${col}${selected&&!sel?"30":"CC"}`} stroke={col} strokeWidth={sel?2:1}/>
          <text x={x} y={y-3} textAnchor="middle" fill={selected&&!sel?C.text3:C.text0} fontSize={9} fontWeight={700} fontFamily="'Barlow Condensed'">{s.suburb}</text>
          <text x={x} y={y+9} textAnchor="middle" fill={col} fontSize={8} fontFamily="'IBM Plex Mono'">{fmt(s.avg_price)}</text>
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
function SupplyDemand({data}) {
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
  </div>;
}

// ── MARKET VALUE BADGE ────────────────────────────────────────────────────────
function MvBadge({mv}) {
  if(!mv) return null;
  return <Badge label={`${mv.label} ${mv.pct_vs_avg>0?"+":""}${mv.pct_vs_avg?.toFixed(0)}%`} color={mv.color} small/>;
}

// ── LISTING ROW ───────────────────────────────────────────────────────────────
function ListingRow({l}) {
  const isFlag = l.market_value?.label==="Overpriced" && l.market_value?.pct_vs_avg>40;
  return (
    <tr style={{borderBottom:`1px solid ${C.bg3}`,background:isFlag?"rgba(239,68,68,.04)":"transparent",transition:"background .15s"}}
      onMouseEnter={e=>e.currentTarget.style.background=isFlag?"rgba(239,68,68,.08)":C.bg2}
      onMouseLeave={e=>e.currentTarget.style.background=isFlag?"rgba(239,68,68,.04)":"transparent"}>
      <td style={{padding:"9px 12px",color:C.text1,fontSize:12}}>{l.suburb||"—"}</td>
      <td style={{padding:"9px 12px",color:C.text0,fontSize:12,maxWidth:180,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{l.title}</td>
      <td style={{padding:"9px 12px"}}><span style={{fontFamily:"'IBM Plex Mono'",fontSize:12,color:C.teal,fontWeight:600}}>{fmt(l.price_monthly_k)}</span></td>
      <td style={{padding:"9px 12px"}}><MvBadge mv={l.market_value}/></td>
      <td style={{padding:"9px 12px"}}>
        <span style={{background:l.source_site==="Facebook Marketplace"?`${C.violet}20`:`${C.teal}18`,color:l.source_site==="Facebook Marketplace"?C.violet:C.tealDim,borderRadius:4,padding:"2px 7px",fontSize:10,fontWeight:600}}>{l.source_site}</span>
      </td>
      <td style={{padding:"9px 12px"}}>{l.is_verified?<Badge label="✓ Verified" color={C.green} small/>:<Badge label="Social" color={C.text2} small/>}</td>
      <td style={{padding:"9px 12px",color:C.text2,fontSize:11}}>{rel(l.scraped_at)}</td>
      <td style={{padding:"9px 12px"}}>{isFlag&&<span style={{background:"#7f1d1d",color:"#fca5a5",borderRadius:4,padding:"2px 7px",fontSize:10,fontWeight:700}}>🚩</span>}</td>
    </tr>
  );
}

// ── SCRAPE CONTROL PANEL ──────────────────────────────────────────────────────
function ScrapePanel({onClose}) {
  const [sources, setSources] = useState(["hausples","professionals","agencies"]);
  const [pages, setPages] = useState(3);
  const [includeFb, setIncludeFb] = useState(false);
  const [job, setJob] = useState(null);
  const [polling, setPolling] = useState(false);
  const pollRef = useRef(null);

  const toggleSrc = s => setSources(p=>p.includes(s)?p.filter(x=>x!==s):[...p,s]);

  const trigger = async () => {
    const data = await apiFetch("/scrape/trigger",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sources,max_pages:pages,include_facebook:includeFb,headless:true})});
    if(data) { setJob(data); setPolling(true); }
  };

  useEffect(()=>{
    if(!polling||!job?.job_id) return;
    pollRef.current = setInterval(async()=>{
      const d = await apiFetch(`/scrape/status/${job.job_id}`);
      if(d){ setJob(d); if(d.status==="complete"||d.status==="error"){ setPolling(false); clearInterval(pollRef.current);} }
    }, 1200);
    return ()=>clearInterval(pollRef.current);
  },[polling,job?.job_id]);

  const srcList = [["hausples","Hausples"],["professionals","The Professionals"],["agencies","All Agencies"],["facebook","Facebook"]];

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
            ⚠️ Facebook scraping requires credentials in <code style={{color:C.teal}}>.env</code> and a dedicated account. Runs in visible mode for 2FA.
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
              <span>{job.current_source ? `Scraping ${job.current_source} p.${job.current_page}…` : job.status}</span>
              <span>{job.collected||0} listings collected</span>
            </div>
          </div>
          {(job.status==="complete"||job.status==="error")&&<button onClick={()=>{setJob(null);onClose();}} style={{width:"100%",background:C.bg3,border:`1px solid ${C.border}`,borderRadius:8,padding:"10px",color:C.text0,fontSize:13,fontWeight:600,cursor:"pointer"}}>{job.status==="complete"?"✓ Done — Refresh Dashboard":"✗ Dismiss"}</button>}
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
  {id:"flags",     icon:"⚑", label:"Flagged"},
];

function Sidebar({active, onNav}) {
  return (
    <div style={{width:64,background:C.bg1,borderRight:`1px solid ${C.border}`,display:"flex",flexDirection:"column",alignItems:"center",padding:"16px 0",gap:4,flexShrink:0,zIndex:10}}>
      <div style={{fontFamily:"'Barlow Condensed'",fontSize:22,fontWeight:800,color:C.teal,marginBottom:20,letterSpacing:"-.02em"}}>PD</div>
      {NAV_ITEMS.map(n=>(
        <button key={n.id} onClick={()=>onNav(n.id)} title={n.label} style={{width:44,height:44,background:active===n.id?C.tealGlow:"transparent",border:`1px solid ${active===n.id?C.teal:C.bg3}`,borderRadius:10,color:active===n.id?C.teal:C.text2,fontSize:18,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",transition:"all .15s"}}>
          {n.icon}
        </button>
      ))}
      <div style={{flex:1}}/>
      <div style={{width:8,height:8,borderRadius:"50%",background:C.green,boxShadow:`0 0 0 3px ${C.green}30`,animation:"pulse 2s infinite"}} title="Live"/>
    </div>
  );
}

// ── TOPBAR ────────────────────────────────────────────────────────────────────
function Topbar({view, overview, onScrape, loading}) {
  const viewLabels = {dashboard:"Dashboard",listings:"All Listings",heatmap:"Price Heatmap",analytics:"Analytics",flags:"Flagged Listings"};
  return (
    <div style={{height:56,background:C.bg1,borderBottom:`1px solid ${C.border}`,display:"flex",alignItems:"center",justifyContent:"space-between",padding:"0 24px",flexShrink:0}}>
      <div style={{display:"flex",alignItems:"center",gap:12}}>
        <span style={{fontFamily:"'Barlow Condensed'",fontSize:18,fontWeight:700,color:C.text0}}>{viewLabels[view]}</span>
        <span style={{fontSize:10,color:C.text2,fontFamily:"'IBM Plex Mono'"}}>PORT MORESBY · NCD</span>
      </div>
      <div style={{display:"flex",alignItems:"center",gap:14}}>
        {overview?.last_scraped&&<span style={{fontSize:11,color:C.text2}}>Updated {rel(overview.last_scraped)}</span>}
        {loading&&<Spinner/>}
        <button onClick={onScrape} style={{background:`linear-gradient(135deg,${C.teal},${C.violet})`,border:"none",borderRadius:8,padding:"7px 16px",color:"#fff",fontSize:12,fontWeight:700,cursor:"pointer",display:"flex",alignItems:"center",gap:6}}>
          ⚡ Run Scrape
        </button>
      </div>
    </div>
  );
}

// ── VIEWS ─────────────────────────────────────────────────────────────────────

function DashboardView({overview, heatmap, trends, sd, sources}) {
  const [selSuburb, setSelSuburb] = useState(null);
  const o=overview||MOCK_OVERVIEW;
  const h=(heatmap?.suburbs||MOCK_HEATMAP.suburbs);
  const t=(trends?.trends||MOCK_TRENDS.trends);
  const sdData=(sd?.data||MOCK_SD.data);
  const srcData=(sources?.sources||MOCK_SOURCES.sources);
  const keys=[{label:"TOTAL LISTINGS",value:o.total_listings,icon:"🏘",accent:C.teal},{label:"AVG RENT/MONTH",value:fmt(o.avg_rent_pgk),icon:"💰",accent:C.amber},{label:"MIDDLEMAN FLAGS",value:o.middleman_flags,icon:"🚩",accent:C.red},{label:"SOURCES ACTIVE",value:o.sources_active,icon:"📡",accent:C.violet}];

  return <div style={{display:"flex",flexDirection:"column",gap:18}}>
    {/* KPIs */}
    <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14}}>
      {keys.map((k,i)=><KpiCard key={i} {...k} delay={i*60}/>)}
    </div>
    {/* Map + SD */}
    <div style={{display:"grid",gridTemplateColumns:"1fr 280px",gap:14}}>
      <Card style={{padding:20}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
          <span style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",letterSpacing:"0.08em"}}>PRICE HEATMAP · PGK/MONTH</span>
          {selSuburb&&<button onClick={()=>setSelSuburb(null)} style={{background:"none",border:"none",color:C.teal,fontSize:11,cursor:"pointer"}}>Clear ✕</button>}
        </div>
        <HeatmapViz suburbs={h} selected={selSuburb} onSelect={setSelSuburb}/>
        <div style={{marginTop:10,display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:9,color:C.text2}}>Low</span>
          <div style={{flex:1,height:5,borderRadius:3,background:`linear-gradient(to right,rgb(32,190,160),rgb(200,70,45))`}}/>
          <span style={{fontSize:9,color:C.text2}}>High</span>
        </div>
      </Card>
      <Card style={{padding:20}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14}}>SUPPLY / DEMAND</div>
        <SupplyDemand data={sdData}/>
        <div style={{display:"flex",gap:12,marginTop:14}}>
          <div style={{display:"flex",alignItems:"center",gap:5,fontSize:9,color:C.text2}}><div style={{width:16,height:3,background:C.teal,borderRadius:2}}/> Demand</div>
          <div style={{display:"flex",alignItems:"center",gap:5,fontSize:9,color:C.text2}}><div style={{width:16,height:3,background:C.violet,borderRadius:2}}/> Supply</div>
        </div>
      </Card>
    </div>
    {/* Trends + Sources */}
    <div style={{display:"grid",gridTemplateColumns:"1fr 300px",gap:14}}>
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

  const TH=({children,s})=><th onClick={()=>setSort(s||"scraped_at")} style={{padding:"8px 12px",textAlign:"left",fontSize:10,color:sort===s?C.teal:C.text2,fontFamily:"'IBM Plex Mono'",letterSpacing:"0.08em",cursor:"pointer",userSelect:"none",whiteSpace:"nowrap"}}>{children}{sort===s?" ↓":""}</th>;

  return <div style={{display:"flex",flexDirection:"column",gap:14}}>
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
        <input placeholder="Min K" value={minPrice} onChange={e=>setMinPrice(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:C.text0,fontSize:12,width:80}}/>
        <input placeholder="Max K" value={maxPrice} onChange={e=>setMaxPrice(e.target.value)} style={{background:C.bg3,border:`1px solid ${C.border}`,borderRadius:6,padding:"6px 10px",color:C.text0,fontSize:12,width:80}}/>
        <span style={{fontSize:11,color:C.text2,marginLeft:"auto"}}>{total} listings</span>
        {loading&&<Spinner/>}
      </div>
    </Card>
    {/* Table */}
    <Card>
      <div style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse"}}>
          <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
            <TH>Suburb</TH><TH>Title</TH><TH s="price_monthly_k">Price/mo</TH><TH>Market</TH><TH>Source</TH><TH>Status</TH><TH s="scraped_at">Posted</TH><TH></TH>
          </tr></thead>
          <tbody>{listings.map(l=><ListingRow key={l.listing_id} l={l}/>)}</tbody>
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

function HeatmapView() {
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [sort, setSort] = useState("avg_price");
  useEffect(()=>{apiFetch("/analytics/heatmap").then(d=>setData(d||MOCK_HEATMAP));},[]);
  const suburbs=(data?.suburbs||MOCK_HEATMAP.suburbs);
  const sorted=[...suburbs].sort((a,b)=>b[sort]-a[sort]);
  const sel=selected?suburbs.find(s=>s.suburb===selected):null;

  return <div style={{display:"grid",gridTemplateColumns:"1fr 260px",gap:14,height:"100%"}}>
    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      <Card style={{padding:20}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:16}}>SUBURB PRICE MAP · PGK/MONTH AVG · Click to select</div>
        <HeatmapViz suburbs={suburbs} selected={selected} onSelect={setSelected}/>
        <div style={{marginTop:12,display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:9,color:C.text2}}>Budget</span>
          <div style={{flex:1,height:6,borderRadius:3,background:`linear-gradient(to right,rgb(32,190,160),rgb(120,140,180),rgb(200,70,45))`}}/>
          <span style={{fontSize:9,color:C.text2}}>Premium</span>
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
        {[["Avg Rent",fmt(sel.avg_price)],["Median",fmt(sel.median_price)],["Min",fmt(sel.min_price)],["Max",fmt(sel.max_price)],["Listings",sel.listings]].map(([k,v])=><div key={k} style={{display:"flex",justifyContent:"space-between",marginBottom:7,fontSize:12}}><span style={{color:C.text2}}>{k}</span><span style={{color:priceColor(sel.avg_price),fontWeight:600,fontFamily:"'IBM Plex Mono'"}}>{v}</span></div>)}
      </Card>}
    </div>
  </div>;
}

function AnalyticsView() {
  const [sd,setSd]=useState(null); const [src,setSrc]=useState(null); const [trends,setTrends]=useState(null);
  useEffect(()=>{
    apiFetch("/analytics/supply-demand").then(d=>setSd(d||MOCK_SD));
    apiFetch("/analytics/sources").then(d=>setSrc(d||MOCK_SOURCES));
    apiFetch("/analytics/trends").then(d=>setTrends(d||MOCK_TRENDS));
  },[]);
  const sdData=(sd?.data||MOCK_SD.data);
  const srcData=(src?.sources||MOCK_SOURCES.sources);
  const trData=(trends?.trends||MOCK_TRENDS.trends);
  const maxSup=Math.max(...sdData.map(d=>d.supply||0));

  return <div style={{display:"flex",flexDirection:"column",gap:14}}>
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      <Card style={{padding:20}}>
        <div style={{fontSize:11,color:C.text2,fontFamily:"'IBM Plex Mono'",marginBottom:14}}>RENT PRICE TRENDS</div>
        <div style={{display:"flex",gap:10,marginBottom:12}}>
          {[["Waigani",C.teal],["Boroko",C.violet],["Gerehu",C.amber]].map(([s,c])=><div key={s} style={{display:"flex",alignItems:"center",gap:5,fontSize:11,color:C.text1}}><div style={{width:14,height:3,background:c,borderRadius:2}}/>{s}</div>)}
        </div>
        <LineChart trends={trData}/>
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
      <div style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse"}}>
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
export default function App() {
  const [view,setView]=useState("dashboard");
  const [showScrape,setShowScrape]=useState(false);
  const [overview,setOverview]=useState(null);
  const [heatmap,setHeatmap]=useState(null);
  const [trends,setTrends]=useState(null);
  const [sd,setSd]=useState(null);
  const [sources,setSources]=useState(null);
  const [loading,setLoading]=useState(true);

  const loadAll=useCallback(async()=>{
    setLoading(true);
    const [ov,hm,tr,s,sr]=await Promise.all([
      apiFetch("/analytics/overview"),apiFetch("/analytics/heatmap"),
      apiFetch("/analytics/trends"),apiFetch("/analytics/supply-demand"),apiFetch("/analytics/sources"),
    ]);
    setOverview(ov||MOCK_OVERVIEW); setHeatmap(hm||MOCK_HEATMAP);
    setTrends(tr||MOCK_TRENDS); setSd(s||MOCK_SD); setSources(sr||MOCK_SOURCES);
    setLoading(false);
  },[]);

  useEffect(()=>{loadAll();},[loadAll]);

  return (
    <>
      <style>{FONTS}</style>
      <div style={{display:"flex",height:"100vh",overflow:"hidden"}}>
        <Sidebar active={view} onNav={setView}/>
        <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
          <Topbar view={view} overview={overview} onScrape={()=>setShowScrape(true)} loading={loading}/>
          <div style={{flex:1,overflow:"auto",padding:20}}>
            {view==="dashboard"&&<DashboardView overview={overview} heatmap={heatmap} trends={trends} sd={sd} sources={sources}/>}
            {view==="listings" &&<ListingsView/>}
            {view==="heatmap"  &&<HeatmapView/>}
            {view==="analytics"&&<AnalyticsView/>}
            {view==="flags"    &&<FlagsView/>}
          </div>
        </div>
      </div>
      {showScrape&&<ScrapePanel onClose={()=>setShowScrape(false)}/>}
    </>
  );
}
