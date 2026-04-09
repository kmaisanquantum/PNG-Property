import re

file_path = 'frontend/src/App.jsx'
with open(file_path, 'r') as f:
    content = f.read()

# 1. Update form state and add error state
old_state = 'const [form, setForm] = useState({suburb:"Waigani", property_type:"House", bedrooms:3, sqm: 200});'
new_state = 'const [form, setForm] = useState({suburb:"Waigani", property_type:"House", bedrooms:3, sqm: 200, is_for_sale: true});\n  const [error, setError] = useState(null);'
content = content.replace(old_state, new_state)

# 2. Update getEstimate to handle errors and payload cleaning
old_get_estimate = '''  const getEstimate = async () => {
    setLoading(true);
    const res = await apiFetch("/valuation/estimate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(form)
    });
    setEstimate(res);
    setLoading(false);
  };'''

new_get_estimate = '''  const getEstimate = async () => {
    setLoading(true);
    setError(null);
    setEstimate(null);

    // Clean payload for Pydantic (empty string -> null)
    const payload = {
      ...form,
      bedrooms: form.bedrooms === "" ? null : Number(form.bedrooms),
      sqm: form.sqm === "" ? null : Number(form.sqm)
    };

    try {
      const res = await apiFetch("/valuation/estimate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      if (res && !res.error) {
        setEstimate(res);
      } else {
        setError(res?.error || "Unable to calculate estimate with current data.");
      }
    } catch (err) {
      setError("Server error. Please try again later.");
    }
    setLoading(false);
  };'''

content = content.replace(old_get_estimate, new_get_estimate)

# 3. Add Purpose (Rent vs Sale) select and display Error
# Search for the SUBURB container to insert the PURPOSE select above it
suburb_container = '''               <div>
                  <div style={{fontSize:10, color:C.text2, marginBottom:4}}>SUBURB</div>'''

purpose_container = '''               {error && <div style={{background:C.red + '22', border:`1px solid ${C.red}44`, color:C.red, padding:10, borderRadius:8, fontSize:12, marginBottom:8}}>{error}</div>}
               <div>
                  <div style={{fontSize:10, color:C.text2, marginBottom:4}}>PURPOSE</div>
                  <select value={form.is_for_sale ? "sale" : "rent"} onChange={e=>setForm({...form, is_for_sale: e.target.value === "sale"})} style={{width:'100%', background:C.bg3, border:`1px solid ${C.border}`, borderRadius:6, padding:8, color:C.text0, fontWeight:700}}>
                     <option value="sale">FOR SALE</option>
                     <option value="rent">FOR RENT</option>
                  </select>
               </div>\n'''

content = content.replace(suburb_container, purpose_container + suburb_container)

with open(file_path, 'w') as f:
    f.write(content)
