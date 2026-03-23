with open('frontend/src/App.jsx', 'r') as f:
    content = f.read()

search_srclist = 'const srcList = [["hausples","Hausples"],["professionals","The Professionals"],["agencies","All Agencies"],["facebook","Facebook"]];'
replace_srclist = 'const srcList = [["hausples","Hausples"],["professionals","The Professionals"],["agencies","All Agencies"],["portals","All Portals"],["facebook","Facebook"]];'

content = content.replace(search_srclist, replace_srclist)

with open('frontend/src/App.jsx', 'w') as f:
    f.write(content)
