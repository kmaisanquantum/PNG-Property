import sys

with open('frontend/src/App.jsx', 'r') as f:
    content = f.read()

# 1. Update NAV_ITEMS
content = content.replace(
    '{id:"flags",     icon:"⚑", label:"Flagged"},',
    '{id:"flags",     icon:"⚑", label:"Flagged"},\n  {id:"resources", icon:"🔗", label:"Resources"},'
)

# 2. Update Topbar labels
content = content.replace(
    'const viewLabels = {dashboard:"Dashboard",listings:"All Listings",heatmap:"Price Heatmap",analytics:"Analytics",flags:"Flagged Listings"};',
    'const viewLabels = {dashboard:"Dashboard",listings:"All Listings",heatmap:"Price Heatmap",analytics:"Analytics",flags:"Flagged Listings",resources:"Market Resources"};'
)

# 3. Add ResourcesView and RESOURCES_DATA
resources_code = """
const RESOURCES_DATA = [
  {
    category: "Main Property Portals",
    items: [
      { name: "Hausples.com.pg", url: "https://www.hausples.com.pg", desc: "Largest active portal (rentals, sales, land)." },
      { name: "PNGRealEstate.com.pg", url: "https://www.pngrealestate.com.pg", desc: "Major residential and commercial listings." },
      { name: "MarketMeri", url: "https://www.marketmeri.com", desc: "General classifieds with very active housing section." },
      { name: "PNGbuynrent.com", url: "https://www.pngbuynrent.com", desc: "Simplified property search platform." }
    ]
  },
  {
    category: "Major Real Estate Agencies",
    items: [
      { name: "LJ Hooker PNG", url: "https://www.ljhooker.com.pg", desc: "Established name, Port Moresby focus." },
      { name: "Ray White PNG", url: "https://www.raywhitepng.com", desc: "Large residential and commercial portfolio." },
      { name: "Strickland RE", url: "https://www.sre.com.pg", desc: "Sales and high-end property management." },
      { name: "The Professionals", url: "https://www.theprofessionals.com.pg", desc: "Broad listings including Lae market." },
      { name: "Century 21", url: "https://www.c21.com.pg", desc: "Global brand agency in PNG." },
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
      { name: "Credit Corp Properties", url: "https://www.creditcorporation.com.pg/properties", desc: "High-end assets like Era Matana/Dorina." },
      { name: "Nambawan Super", url: "https://www.nambawansuper.com.pg/property", desc: "Large owner of various residential estates." },
      { name: "Edai Town", url: "https://www.edaitown.com.pg", desc: "Large-scale residential development near POM." }
    ]
  }
];

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
"""

# Find a place to insert ResourcesView - before App component
content = content.replace("export default function App() {", resources_code + "\nexport default function App() {")

# 4. Update App component's main render
content = content.replace(
    '{view==="flags"    &&<FlagsView/>}',
    '{view==="flags"    &&<FlagsView/>}\n            {view==="resources"&&<ResourcesView/>}'
)

with open('frontend/src/App.jsx', 'w') as f:
    f.write(content)
