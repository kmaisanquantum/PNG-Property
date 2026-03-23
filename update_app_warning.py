with open('frontend/src/App.jsx', 'r') as f:
    content = f.read()

search_warning = """          <div style={{background:C.bg3,borderRadius:8,padding:"10px 14px",marginBottom:22,fontSize:12,color:C.text1}}>
            ⚠️ Facebook scraping requires credentials in <code style={{color:C.teal}}>.env</code> and a dedicated account. Runs in visible mode for 2FA.
          </div>"""

replace_warning = """          <div style={{background:C.bg3,borderRadius:8,padding:"10px 14px",marginBottom:22,fontSize:12,color:C.text1}}>
            ⚠️ Facebook scraping requires <code style={{color:C.teal}}>FB_EMAIL</code> and <code style={{color:C.teal}}>FB_PASSWORD</code> in Render environment variables.
            For 2FA, generate a <code style={{color:C.teal}}>fb_session.json</code> locally and upload it to the <code style={{color:C.teal}}>/app/data</code> persistent disk.
          </div>"""

content = content.replace(search_warning, replace_warning)

with open('frontend/src/App.jsx', 'w') as f:
    f.write(content)
