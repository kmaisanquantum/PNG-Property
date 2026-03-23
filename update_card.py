with open('frontend/src/App.jsx', 'r') as f:
    content = f.read()

# Update Card to pass onClick and other props
content = content.replace(
    'function Card({children, style={}, className=""}) {',
    'function Card({children, style={}, className="", ...props}) {'
)
content = content.replace(
    'return <div className={className} style={{background:C.bg1,border:`1px solid ${C.border}`,borderRadius:12,...style}}>{children}</div>;',
    'return <div className={className} {...props} style={{background:C.bg1,border:`1px solid ${C.border}`,borderRadius:12,...style}}>{children}</div>;'
)

with open('frontend/src/App.jsx', 'w') as f:
    f.write(content)
