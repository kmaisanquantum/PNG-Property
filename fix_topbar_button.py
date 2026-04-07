import re

file_path = 'frontend/src/App.jsx'
with open(file_path, 'r') as f:
    content = f.read()

# Target part of the style to uniquely identify the button
search_str = 'className="scrape-btn" style={{background:`linear-gradient(135deg,${C.teal},${C.violet})`'

replacement_button = '''<button onClick={async () => {
          if (window.confirm("Clear all existing listing and analytics data? This cannot be undone.")) {
            const res = await apiFetch("/scrape/clear", { method: "POST" });
            if (res) onLogout();
          }
        }} className="clear-btn" style={{background:C.bg3, border:`1px solid ${C.red}`, borderRadius:6, padding:"6px 12px", color:C.red, fontSize:11, fontWeight:700, cursor:"pointer", display:"flex", alignItems:"center", gap:5}}>
          <span style={{fontSize:12}}>🗑</span> Clear Data
        </button>
        <button'''

if search_str in content:
    new_content = content.replace('<button onClick={onScrape} className="scrape-btn"', replacement_button + ' onClick={onScrape} className="scrape-btn"')
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("Topbar updated successfully")
else:
    print("Could not find button pattern")
