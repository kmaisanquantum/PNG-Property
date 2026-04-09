import re

file_path = 'frontend/src/App.jsx'
with open(file_path, 'r') as f:
    content = f.read()

# 1. Update Topbar signature and button call
content = content.replace(
    'function Topbar({view, overview, onScrape, onLogout, loading, user}) {',
    'function Topbar({view, overview, onScrape, onLogout, onRefresh, loading, user}) {'
)
content = content.replace(
    'if (res) onLogout();',
    'if (res && onRefresh) onRefresh();'
)

# 2. Update App to pass loadAll as onRefresh to Topbar
content = content.replace(
    '<Topbar view={view} overview={overview} onScrape={()=>setShowScrape(true)} onLogout={handleLogout} loading={loading} user={user}/>',
    '<Topbar view={view} overview={overview} onScrape={()=>setShowScrape(true)} onLogout={handleLogout} onRefresh={loadAll} loading={loading} user={user}/>'
)

with open(file_path, 'w') as f:
    f.write(content)
