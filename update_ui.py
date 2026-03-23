import os

with open('frontend/src/App.jsx', 'r') as f:
    content = f.read()

# CSS Color constants from the file (or we can use interpolation if we read them, but they are hardcoded in the string below)
# We'll use the literals directly in the string to avoid interpolation issues.

new_fonts = """
.fade-up { animation: fadeUp .4s ease both; }
.kpi-card { transition: all 0.2s ease; cursor: pointer; }
.kpi-card:hover { transform: translateY(-3px); border-color: #14b8a6 !important; background: #0f172a !important; box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
.nav-btn { transition: all 0.2s ease; }
.nav-btn:hover { background: #0f172a !important; color: #14b8a6 !important; border-color: #14b8a6 !important; }
.scrape-btn { transition: all 0.2s ease; }
.scrape-btn:hover { transform: translateY(-1px); filter: brightness(1.1); box-shadow: 0 4px 12px rgba(20,184,166,0.3); }
.link-btn { color: #14b8a6; cursor: pointer; text-decoration: none; font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 4px; transition: gap 0.2s ease; }
.link-btn:hover { gap: 8px; color: #8b5cf6; }
"""

content = content.replace('.fade-up { animation: fadeUp .4s ease both; }', new_fonts.strip())

# 2. Update KpiCard
search_kpicard = "function KpiCard({label, value, sub, accent, icon, delay=0}) {"
replace_kpicard = "function KpiCard({label, value, sub, accent, icon, delay=0, onClick}) {"
content = content.replace(search_kpicard, replace_kpicard)

content = content.replace(
    'return <Card className="fade-up" style={{padding:"18px 20px",animationDelay:`${delay}ms`}}>',
    'return <Card className={`fade-up ${onClick ? "kpi-card" : ""}`} onClick={onClick} style={{padding:"18px 20px",animationDelay:`${delay}ms`}}>'
)

# 3. Update DashboardView signature and links
content = content.replace(
    'function DashboardView({overview, heatmap, trends, sd, sources}) {',
    'function DashboardView({overview, heatmap, trends, sd, sources, onNav}) {'
)

search_keys_map = '{keys.map((k,i)=><KpiCard key={i} {...k} delay={i*60}/>)}'
replace_keys_map = """{keys.map((k,i)=>{
        let click = null;
        if(k.label === 'TOTAL LISTINGS') click = () => onNav('listings');
        if(k.label === 'MIDDLEMAN FLAGS') click = () => onNav('flags');
        return <KpiCard key={i} {...k} delay={i*60} onClick={click}/>
      })}"""
content = content.replace(search_keys_map, replace_keys_map)

# 4. Update App component's render of DashboardView
content = content.replace(
    '{view==="dashboard"&&<DashboardView overview={overview} heatmap={heatmap} trends={trends} sd={sd} sources={sources}/>}',
    '{view==="dashboard"&&<DashboardView overview={overview} heatmap={heatmap} trends={trends} sd={sd} sources={sources} onNav={setView}/>}'
)

# 5. SupplyDemand component updates
content = content.replace(
    'function SupplyDemand({data}) {',
    'function SupplyDemand({data, onSeeMore}) {'
)

search_sd_end = """      </div>;
    })}
  </div>;
}"""
replace_sd_end = """      </div>;
    })}
    <div style={{marginTop:10, display:'flex', justifyContent:'center'}}>
      <div className="link-btn" onClick={onSeeMore}>View Full Analytics →</div>
    </div>
  </div>;
}"""
content = content.replace(search_sd_end, replace_sd_end)

# Update DashboardView usage of SupplyDemand
content = content.replace(
    '<SupplyDemand data={sdData}/>',
    '<SupplyDemand data={sdData} onSeeMore={() => onNav("analytics")}/>'
)

# 6. Button hover classes
content = content.replace('style={{width:44,height:44,', 'className="nav-btn" style={{width:44,height:44,')
content = content.replace(
    'style={{background:`linear-gradient(135deg,${C.teal},${C.violet})`,',
    'className="scrape-btn" style={{background:`linear-gradient(135deg,${C.teal},${C.violet})`,'
)

with open('frontend/src/App.jsx', 'w') as f:
    f.write(content)
