import React, { useEffect, useState } from 'react';

const AuthModal = ({ setShowAuth, step, setStep, identifier, setIdentifier, password, setPassword, fullName, setFullName, error, setError, loading, handleIdentify, handleAuth, authMode, setAuthMode }) => (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(8,15,20,0.95)', backdropFilter: 'blur(10px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
    }} onClick={() => { setShowAuth(false); setStep('identify'); setIdentifier(''); setPassword(''); setFullName(''); setError(''); setProvider('email'); }}>
      <div className="auth-modal-card" style={{
        background: 'var(--bg1)', border: '1px solid var(--border)',
        borderRadius: '24px', padding: '40px', maxWidth: '420px', width: '100%',
        boxShadow: '0 32px 64px rgba(0,0,0,0.5)', position: 'relative'
      }} onClick={e => e.stopPropagation()}>
        <style>{`
          @media (max-width: 480px) {
            .auth-modal-card { padding: 24px 16px !important; border-radius: 16px !important; }
            .auth-modal-card h2 { font-size: 22px !important; margin-bottom: 8px !important; }
            .auth-modal-card p { font-size: 13px !important; margin-bottom: 24px !important; }
            .auth-modal-card input { padding: 12px 14px !important; font-size: 14px !important; }
          }
        `}</style>
        <button style={{
          position: 'absolute', top: '20px', right: '20px', background: 'none',
          border: 'none', color: 'var(--text2)', cursor: 'pointer', fontSize: '20px'
        }} onClick={() => { setShowAuth(false); setStep('identify'); setIdentifier(''); setPassword(''); setFullName(''); setError(''); setProvider('email'); }}>✕</button>

        {step === 'identify' && (
          <>
            <h2 style={{fontFamily: 'var(--font-d)', fontSize: '32px', marginBottom: '12px', textAlign: 'center', letterSpacing: '0.05em'}}>
              {authMode === 'signup' ? 'CREATE ACCOUNT' : 'WELCOME BACK'}
            </h2>
            <p style={{fontSize: '15px', color: 'var(--text1)', textAlign: 'center', marginBottom: '32px'}}>
              {authMode === 'signup' ? 'Enter your email or phone to get started.' : 'Enter your email or phone to continue.'}
            </p>

            <form onSubmit={handleIdentify} style={{display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px'}}>
               <input
                  type="text" required placeholder="Email or Phone number" value={identifier} onChange={e => setIdentifier(e.target.value)}
                  style={{padding: '14px 18px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', color: '#fff', fontSize: '15px'}}
                />
                <button type="submit" disabled={loading} style={{
                  padding: '14px', borderRadius: '12px', border: 'none',
                  background: 'linear-gradient(135deg, var(--teal), #0891b2)', color: '#fff',
                  fontWeight: '700', cursor: 'pointer', fontSize: '15px'
                }}>
                  {loading ? 'Checking...' : 'Continue'}
                </button>
            </form>

            <div style={{textAlign: 'center', fontSize: '14px', color: 'var(--text2)'}}>
              {authMode === 'login' ? (
                <>
                  Don't have an account? <button onClick={() => setAuthMode('signup')} style={{background: 'none', border: 'none', color: 'var(--teal)', cursor: 'pointer', fontWeight: '600', textDecoration: 'underline'}}>Sign Up</button>
                </>
              ) : (
                <>
                  Already have an account? <button onClick={() => setAuthMode('login')} style={{background: 'none', border: 'none', color: 'var(--teal)', cursor: 'pointer', fontWeight: '600', textDecoration: 'underline'}}>Sign In</button>
                </>
              )}
            </div>
          </>
        )}

        {(step === 'login' || step === 'signup' || step === 'otp') && (
          <>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px'}}>
               <button onClick={() => setStep('identify')} style={{background: 'none', border: 'none', color: 'var(--teal)', cursor: 'pointer', fontSize: '18px'}}>←</button>
               <h2 style={{fontFamily: 'var(--font-d)', fontSize: '24px', letterSpacing: '0.02em'}}>
                 {step === 'login' ? 'WELCOME BACK' : step === 'signup' ? 'CREATE ACCOUNT' : 'VERIFY PHONE'}
               </h2>
            </div>

            <form onSubmit={handleAuth} style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
              {step === 'signup' && (
                <div style={{display: 'flex', flexDirection: 'column', gap: '6px'}}>
                  <label style={{fontSize: '11px', color: 'var(--text2)', fontWeight: '700'}}>FULL NAME</label>
                  <input
                    type="text" required value={fullName} onChange={e => setFullName(e.target.value)}
                    style={{padding: '12px 16px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', color: '#fff'}}
                  />
                </div>
              )}

              {(!(step === 'signup' && !identifier.includes('@'))) && (
                <div style={{display: 'flex', flexDirection: 'column', gap: '6px'}}>
                  <label style={{fontSize: '11px', color: 'var(--text2)', fontWeight: '700'}}>
                    {step === 'otp' ? 'VERIFICATION CODE' : 'PASSWORD'}
                  </label>
                  <input
                    type={step === 'otp' ? 'text' : 'password'} required
                    placeholder={step === 'otp' ? 'Enter 6-digit code' : '••••••••'}
                    value={password} onChange={e => setPassword(e.target.value)}
                    style={{padding: '12px 16px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', color: '#fff'}}
                  />
                </div>
              )}

              {error && <div style={{color: 'var(--red)', fontSize: '13px', textAlign: 'center'}}>{error}</div>}

              <button type="submit" disabled={loading} style={{
                marginTop: '12px', padding: '14px', borderRadius: '12px', border: 'none',
                background: 'linear-gradient(135deg, var(--teal), #0891b2)', color: '#fff',
                fontWeight: '700', cursor: 'pointer'
              }}>
                {loading ? 'Processing...' : step === 'login' ? 'Sign In' : (step === 'signup' && !identifier.includes('@')) ? 'Continue' : step === 'signup' ? 'Create Account' : 'Verify & Enter'}
              </button>
            </form>
          </>
        )}

        <div style={{marginTop: '32px', textAlign: 'center', fontSize: '12px', color: 'var(--text2)'}}>
          By continuing, you agree to our <a href="#" style={{color: 'var(--teal)', textDecoration: 'underline'}}>Terms of Service</a>.
        </div>
      </div>
    </div>
);

const Landing = ({ onEnterDashboard, apiFetch }) => {
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'
  const [identifier, setIdentifier] = useState(''); // email or phone
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('identify'); // 'identify', 'login', 'signup', 'otp'

  useEffect(() => {
    const reveals = document.querySelectorAll('.reveal');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
      });
    }, { threshold: 0.1 });
    reveals.forEach(r => observer.observe(r));
    return () => observer.disconnect();
  }, []);

  const handleIdentify = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await apiFetch(`/auth/check-identifier?q=${encodeURIComponent(identifier)}`);
      if (data) {
        if (data.exists) {
           if (identifier.includes('@')) setStep('login');
           else setStep('otp');
        } else {
           setStep('signup');
        }
      }
    } catch (err) {
      setError('Connection error');
    } finally {
      setLoading(false);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (step === 'login') {
        const formData = new URLSearchParams();
        formData.append('username', identifier);
        formData.append('password', password);

        const data = await apiFetch('/auth/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString()
        });

        if (data && data.access_token) onEnterDashboard(data);
        else setError('Invalid credentials');
      } else if (step === 'signup') {
        const data = await apiFetch('/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: identifier.includes('@') ? identifier : undefined,
            phone: !identifier.includes('@') ? identifier : undefined,
            password,
            full_name: fullName
          })
        });

        if (data && (data.email || data.phone)) {
          setStep('login');
          setError('Account created! Please sign in.');
        } else setError('Signup failed');
      } else if (step === 'otp') {
        const data = await apiFetch(`/auth/external?provider=phone&identifier=${identifier}&name=${fullName}`, { method: 'POST' });
        if (data && data.access_token) onEnterDashboard(data);
        else setError('Invalid code');
      }
    } catch (err) {
      setError('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="landing-container">
      <style>{`
        :root {
          --bg: #080f14;
          --bg1: #0d161d;
          --bg2: #141f28;
          --border: #1e2d38;
          --text0: #ffffff;
          --text1: #a0aec0;
          --text2: #718096;
          --teal: #0eb5b0;
          --amber: #f59e0b;
          --violet: #8b5cf6;
          --red: #ef4444;
          --green: #10b981;
          --earth1: #c4742a;
          --earth2: #8b4513;
          --font-d: 'Barlow Condensed', sans-serif;
          --font-b: 'Inter', sans-serif;
          --font-s: 'Source Serif 4', serif;
        }

        .landing-container {
          background: var(--bg);
          color: var(--text0);
          font-family: var(--font-b);
          line-height: 1.6;
          overflow-x: hidden;
          min-height: 100vh;
        }

        @keyframes fadeUp   { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:none; } }
        @keyframes pulse    { 0%,100% { opacity:1; } 50% { opacity:.3; } }
        @keyframes float    { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-10px); } }
        @keyframes scan     { 0%,100% { top:0; } 50% { top:calc(100% - 2px); } }

        .reveal { opacity:0; transform:translateY(20px); transition: opacity .7s ease, transform .7s ease; }
        .reveal.visible { opacity:1; transform:none; }

        nav {
          position: fixed; top:0; left:0; right:0; z-index: 100;
          display: flex; align-items: center; justify-content: space-between;
          padding: 0 48px; height: 64px;
          background: rgba(8,15,20,.85);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid var(--border);
        }
        @media (max-width: 768px) {
          nav { padding: 0 16px; }
          .nav-logo { font-size: 18px; }
          .nav-cta { gap: 8px; }
          .btn-ghost { padding: 6px 12px; font-size: 12px; }
          .btn-primary { padding: 6px 14px; font-size: 12px; }
        }
        .nav-logo {
          display: flex; align-items: center; gap: 10px;
          font-family: var(--font-d); font-size: 22px; letter-spacing: .04em;
          color: var(--text0); text-decoration: none;
        }
        .nav-logo .dot { color: var(--teal); }
        .nav-links { display: flex; align-items: center; gap: 32px; }
        .nav-links a {
          color: var(--text1); text-decoration: none; font-size: 14px; font-weight: 500;
          transition: color .2s;
        }
        .nav-links a:hover { color: var(--text0); }

        .nav-cta { display: flex; align-items: center; gap: 12px; }

        .btn-ghost {
          background: none; border: 1px solid var(--border);
          border-radius: 8px; padding: 8px 20px; color: var(--text1);
          font-family: var(--font-b); font-size: 14px; font-weight: 500;
          cursor: pointer; transition: all .2s;
        }
        .btn-ghost:hover { border-color: var(--teal); color: var(--teal); }
        .btn-primary {
          background: linear-gradient(135deg, var(--teal), #0891b2);
          border: none; border-radius: 8px; padding: 8px 22px;
          color: #fff; font-family: var(--font-b); font-size: 14px; font-weight: 600;
          cursor: pointer; transition: all .2s;
        }

        .hero {
          min-height: 100vh; display: grid;
          grid-template-columns: 1fr 1fr;
          align-items: center; gap: 0;
          padding: 100px 0 60px;
          position: relative; overflow: hidden;
        }
        @media (max-width: 1024px) {
          .hero { grid-template-columns: 1fr; padding: 100px 24px 60px; text-align: center; }
          .hero-left { padding: 0; display: flex; flex-direction: column; align-items: center; }
          .hero-sub { margin-left: auto; margin-right: auto; }
          .hero-actions { justify-content: center; }
          .hero-title { font-size: 48px !important; }
        }
        .hero-bg {
          position: absolute; inset: 0; z-index: 0;
          background:
            radial-gradient(ellipse 60% 50% at 70% 40%, rgba(14,181,176,.08) 0%, transparent 70%),
            radial-gradient(ellipse 40% 40% at 20% 80%, rgba(196,116,42,.06) 0%, transparent 60%),
            radial-gradient(ellipse 30% 30% at 80% 80%, rgba(45,184,122,.05) 0%, transparent 60%);
        }
        .hero-left {
          padding: 0 48px 0 72px; z-index:1; position:relative;
        }
        .hero-title {
          font-family: var(--font-d);
          font-size: clamp(42px, 8vw, 100px);
          line-height: .92;
          letter-spacing: .01em;
          color: var(--text0);
          animation: fadeUp .6s .1s ease both;
        }
        .hero-title .accent { color: var(--teal); }
        .hero-title .earth  { color: var(--earth2); font-style: italic; font-family: var(--font-s); font-size: .8em; }
        .hero-sub {
          margin-top: 22px; font-size: 16px; color: var(--text1); max-width: 460px; line-height: 1.7;
          animation: fadeUp .6s .2s ease both;
        }
        .hero-actions {
          margin-top: 36px; display: flex; align-items: center; gap: 16px;
          animation: fadeUp .6s .3s ease both;
        }

        .btn-hero-primary {
          background: linear-gradient(135deg, var(--teal), #0891b2);
          border: none; border-radius: 10px; padding: 14px 32px;
          color: #fff; font-family: var(--font-b); font-size: 15px; font-weight: 600;
          cursor: pointer; transition: all .25s; display:flex; align-items:center; gap:8px;
        }
        .btn-hero-secondary {
          background: none; border: 1px solid var(--border);
          border-radius: 10px; padding: 14px 28px;
          color: var(--text1); font-family: var(--font-b); font-size: 15px; font-weight: 500;
          cursor: pointer; transition: all .2s;
        }

        .hero-right {
          z-index:1; padding: 0 48px 0 0; position:relative;
          animation: fadeUp .8s .2s ease both;
        }
        .dashboard-preview {
          background: var(--bg1);
          border: 1px solid var(--border);
          border-radius: 16px;
          overflow: hidden;
          box-shadow: 0 32px 80px rgba(0,0,0,.6), 0 0 0 1px var(--border);
          animation: float 6s ease-in-out infinite;
          position: relative;
        }
        .scan-line {
          position:absolute; left:0; right:0; height:2px;
          background:linear-gradient(90deg, transparent, rgba(14,181,176,.4), transparent);
          animation: scan 4s ease-in-out infinite;
          pointer-events:none; z-index:10;
        }

        .stats-section {
          padding: 100px 72px;
          display:grid; grid-template-columns:1fr 1fr;
          align-items:center; gap:80px;
          position:relative;
        }
        @media (max-width: 768px) {
          .stats-section { padding: 60px 24px; gap: 40px; }
          .stat-grid { grid-template-columns: 1fr; }
        }
        .stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
        .stat-card {
          background:var(--bg1); border:1px solid var(--border);
          border-radius:12px; padding:24px 22px; position:relative; overflow:hidden;
        }

        .preview-section { padding:80px 72px; }
        @media (max-width: 768px) {
          .preview-section { padding: 40px 24px; }
        }
        .features-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }
        .feature-card {
          background:var(--bg1); border:1px solid var(--border);
          border-radius:14px; padding:28px 24px; position:relative; overflow:hidden;
          transition: all .3s;
        }

        @media (max-width:1024px) {
          .hero-right { display:none; }
          .nav-links { display:none; }
          .stats-section { grid-template-columns:1fr; }
          .features-grid { grid-template-columns:1fr; }
        }
      `}</style>

      <nav>
        <a href="#" className="nav-logo">PNG<span className="dot">●</span>PROPERTY</a>
        <div className="nav-links"><a href="#how-it-works">Process</a>
          <a href="#features">Features</a>
          <a href="#suburbs">Suburbs</a>
          <a href="#pricing">Pricing</a>
        </div>
        <div className="nav-cta">
          <button className="btn-ghost" onClick={() => { setAuthMode('login'); setShowAuth(true); }}>Sign In</button>
          <button className="btn-primary" onClick={() => { setAuthMode('signup'); setShowAuth(true); }}>Get Access →</button>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-bg"></div>
        <div className="hero-left">
          <h1 className="hero-title">
            PNG'S FIRST<br/>
            <span className="earth">Real Estate</span><br/>
            <span className="accent">INTELLIGENCE</span><br/>
            PLATFORM
          </h1>
          <p className="hero-sub">
            Aggregated listings from Hausples, The Professionals, Ray White, Century 21 and Facebook — normalised, scored, and delivered as actionable analytics for PNG's property market.
          </p>
          <div className="hero-actions">
            <button className="btn-hero-primary" onClick={() => { setAuthMode('signup'); setShowAuth(true); }}>
              <span>Enter Dashboard</span> <span>→</span>
            </button>
          </div>
        </div>
        <div className="hero-right">
          <div className="dashboard-preview">
            <div className="scan-line"></div>
            <div style={{padding: '20px', textAlign: 'center'}}>
              <div style={{fontSize: '24px', marginBottom: '10px'}}>Live Analytics</div>

              <div style={{height: '240px', background: 'var(--bg2)', borderRadius: '12px', padding: '15px', textAlign: 'left', overflow: 'hidden', position: 'relative'}}>
                <div style={{fontSize: '10px', color: 'var(--teal)', fontFamily: 'var(--font-m)', marginBottom: '10px', display: 'flex', justifyContent: 'space-between'}}>
                  <span>MARKET FEED</span>
                  <span style={{opacity: 0.6}}>LIVE UPDATE • 4s AGO</span>
                </div>
                {[
                  { s: 'Hausples', l: '3BR House, Waigani', p: 'K4,500', v: 'DEAL' },
                  { s: 'Facebook', l: 'Studio, Boroko', p: 'K1,200', v: 'OVERPRICED' },
                  { s: 'Ray White', l: '2BR Apt, Gordons', p: 'K5,500', v: 'FAIR' },
                  { s: 'Professionals', l: '4BR House, Gerehu', p: 'K2,800', v: 'DEAL' },
                  { s: 'Hausples', l: 'Townhouse, 8 Mile', p: 'K1,800', v: 'FAAL' }
                ].map((item, idx) => (
                  <div key={idx} style={{display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)', opacity: 1 - idx*0.15}}>
                    <div style={{width: '6px', height: '6px', borderRadius: '50%', background: item.v === 'DEAL' ? 'var(--green)' : (item.v === 'OVERPRICED' ? 'var(--red)' : 'var(--amber)')}}></div>
                    <div style={{flex: 1}}>
                      <div style={{fontSize: '11px', color: 'var(--text0)', fontWeight: 600}}>{item.l}</div>
                      <div style={{fontSize: '9px', color: 'var(--text2)'}}>{item.s} • {item.v}</div>
                    </div>
                    <div style={{fontSize: '11px', color: 'var(--teal)', fontFamily: 'var(--font-m)'}}>{item.p}</div>
                  </div>
                ))}
                <div style={{position: 'absolute', bottom: 0, left: 0, right: 0, height: '40px', background: 'linear-gradient(transparent, var(--bg2))'}}></div>
              </div>
            </div>
          </div>
        </div>
      </section>


      <section className="stats-section reveal" id="how-it-works" style={{paddingBottom: 0}}>
        <div style={{gridColumn: '1 / -1', textAlign: 'center', marginBottom: 60}}>
          <div style={{fontSize: '12px', color: 'var(--teal)', fontWeight: 700, letterSpacing: '0.1em', marginBottom: 12}}>THE PROCESS</div>
          <h2 style={{fontFamily: 'var(--font-d)', fontSize: 'clamp(32px, 5vw, 48px)', lineHeight: 1.1}}>HOW IT WORKS</h2>
        </div>
        <div style={{gridColumn: '1 / -1', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '30px'}}>
          {[
            { step: '01', t: 'AGGREGATE', d: 'We scrape 10+ major property portals and Facebook Marketplace every 6 hours, centralizing thousands of fragmented listings.' },
            { step: '02', t: 'NORMALISE', d: 'Our engine cleans inconsistent data—converting prices to monthly PGK, identifying property types, and verifying suburbs.' },
            { step: '03', t: 'INTELLIGENCE', d: 'Listings are cross-referenced with agency benchmarks to score market value and detect inflated middleman markups.' }
          ].map((item, idx) => (
            <div key={idx} style={{padding: '30px', background: 'var(--bg1)', borderRadius: '16px', border: '1px solid var(--border)', position: 'relative'}}>
              <div style={{fontSize: '48px', fontFamily: 'var(--font-d)', color: 'var(--teal)', opacity: 0.1, position: 'absolute', top: '15px', right: '20px'}}>{item.step}</div>
              <h3 style={{fontSize: '18px', color: 'var(--text0)', marginBottom: '15px', fontFamily: 'var(--font-b)'}}>{item.t}</h3>
              <p style={{fontSize: '14px', color: 'var(--text1)', lineHeight: 1.6}}>{item.d}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="stats-section reveal" id="features">
        <div className="stats-left">
          <h2>THE PULSE OF PNG'S PROPERTY MARKET</h2>
          <p>We scrape, normalise and analyse thousands of listings every 6 hours — so you don't have to call 12 different agents to find a fair price.</p>
        </div>
        <div className="stat-grid">
          <div className="stat-card reveal">
            <div style={{fontSize: '32px', color: 'var(--teal)'}}>1,847</div>
            <div style={{fontSize: '12px', color: 'var(--text1)'}}>Active Listings</div>
          </div>
          <div className="stat-card reveal">
            <div style={{fontSize: '32px', color: 'var(--teal)'}}>10+</div>
            <div style={{fontSize: '12px', color: 'var(--text1)'}}>Data Sources</div>
          </div>
        </div>
      </section>

      <section className="preview-section" id="suburbs">
        <div className="features-grid">
          <div className="feature-card reveal">
            <h3>Suburbs Heatmap</h3>
            <p>Visualise average rents by suburb. Compare Gordons vs Gerehu vs Boroko at a glance.</p>
          </div>
          <div className="feature-card reveal">
            <h3>Market Value Score</h3>
            <p>Every listing gets a Deal / Fair / Overpriced badge calculated against verified agency data.</p>
          </div>
          <div className="feature-card reveal">
            <h3>Middleman Detection</h3>
            <p>Identify agent markups before you commit.</p>
          </div>
        </div>
      </section>


      <section className="stats-section reveal" id="pricing" style={{paddingTop: 0, borderTop: '1px solid var(--border)'}}>
        <div style={{gridColumn: '1 / -1', textAlign: 'center', marginBottom: 40, marginTop: 80}}>
          <h2 style={{fontFamily: 'var(--font-d)', fontSize: '42px'}}>PRICING PLANS</h2>
          <p style={{color: 'var(--text1)', maxWidth: '600px', margin: '10px auto'}}>Get the full intelligence package for PNG's property market.</p>
        </div>
        <div className="stat-grid" style={{gridColumn: '1 / -1', maxWidth: '400px', margin: '0 auto', width: '100%'}}>
          <div className="stat-card reveal" style={{textAlign: 'center', border: '1px solid var(--teal)', background: 'rgba(20,184,200,0.05)'}}>
            <div style={{fontSize: '12px', color: 'var(--teal)', fontWeight: 700, letterSpacing: '0.1em', marginBottom: 10}}>LIFETIME ACCESS</div>
            <div style={{fontSize: '48px', color: 'var(--text0)', fontFamily: 'var(--font-d)'}}>FREE<span style={{fontSize: 20, color: 'var(--text2)'}}>*</span></div>
            <p style={{fontSize: '12px', color: 'var(--text2)', marginBottom: 20}}>*Limited time offer for early adopters</p>
            <ul style={{listStyle: 'none', padding: 0, margin: '20px 0', color: 'var(--text1)', fontSize: 14, textAlign: 'left', display: 'inline-block'}}>
              <li style={{marginBottom: 10}}>✓ Unlimited Listing Access</li>
              <li style={{marginBottom: 10}}>✓ Real-time Heatmaps</li>
              <li style={{marginBottom: 10}}>✓ Middleman Detection</li>
              <li style={{marginBottom: 10}}>✓ 24/7 Market Monitoring</li>
            </ul>
            <button className="btn-primary" style={{width: '100%', marginTop: 20}} onClick={() => { setAuthMode('signup'); setShowAuth(true); }}>Join Free Now →</button>
          </div>
        </div>
      </section>
      <footer style={{padding: '40px 72px', borderTop: '1px solid var(--border)', textAlign: 'center'}}>
        <p>© 2026 PNG Property Intelligence Dashboard. Built for Papua New Guinea by <a href="https://www.dspng.tech" target="_blank" rel="noopener noreferrer" style={{color: 'var(--teal)', textDecoration: 'none', fontWeight: '600'}}>Deeps Systems</a>.</p>
      </footer>

      {showAuth && (
        <AuthModal
          setShowAuth={setShowAuth} step={step} setStep={setStep}
          identifier={identifier} setIdentifier={setIdentifier}
          password={password} setPassword={setPassword}
          fullName={fullName} setFullName={setFullName}
          error={error} setError={setError} loading={loading}
          handleIdentify={handleIdentify} handleAuth={handleAuth}
          authMode={authMode} setAuthMode={setAuthMode}
        />
      )}
    </div>
  );
};

export default Landing;
