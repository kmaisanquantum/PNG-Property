import re

file_path = 'frontend/src/App.jsx'
with open(file_path, 'r') as f:
    content = f.read()

# Fix bedrooms and sqm onChange to handle empty strings/invalid numbers
content = content.replace(
    'onChange={e=>setForm({...form, bedrooms: Number(e.target.value)})}',
    'onChange={e=>setForm({...form, bedrooms: e.target.value === "" ? "" : Number(e.target.value)})}'
)
content = content.replace(
    'onChange={e=>setForm({...form, sqm: Number(e.target.value)})}',
    'onChange={e=>setForm({...form, sqm: e.target.value === "" ? "" : Number(e.target.value)})}'
)

with open(file_path, 'w') as f:
    f.write(content)
