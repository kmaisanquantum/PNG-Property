import React, { useEffect, useState } from 'react';

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
           // If provider is not email, we should ideally trigger that provider's flow
           // But for simulation, we'll just go to password if it's email, or OTP if phone
           if (identifier.includes('@')) {
             setProvider('email');
             setStep('login');
           } else {
             setProvider('phone');
             setStep('otp');
           }
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
        if (!identifier.includes('@')) {
          // For phone signups, we transition to OTP step after name is entered
          setStep('otp');
          setLoading(false);
          return;
        }
        const data = await apiFetch('/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: identifier,
            password,
            full_name: fullName
          })
        });

        if (data && data.email) {
          setStep('login');
          setError('Account created! Please sign in.');
        } else setError('Signup failed');
      } else if (step === 'otp') {
        // Simulated OTP
        const data = await apiFetch(`/auth/otp?provider=${provider}&identifier=${identifier}&name=${fullName}`, { method: 'POST' });
        if (data && data.access_token) onEnterDashboard(data);
        else setError('Invalid code');
      }
    } catch (err) {
      setError('An error occurred');
    } finally {
      setLoading(false);
    }
  };



  const AuthModal = () => (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(8,15,20,0.95)', backdropFilter: 'blur(10px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
    }} onClick={() => { setShowAuth(false); setStep('identify'); setIdentifier(''); setPassword(''); setFullName(''); setError(''); setProvider('email'); }}>
      <div style={{
        background: 'var(--bg1)', border: '1px solid var(--border)',
        borderRadius: '24px', padding: '40px', maxWidth: '420px', width: '100%',
        boxShadow: '0 32px 64px rgba(0,0,0,0.5)', position: 'relative'
      }} onClick={e => e.stopPropagation()}>
        <button style={{
          position: 'absolute', top: '20px', right: '20px', background: 'none',
          border: 'none', color: 'var(--text2)', cursor: 'pointer', fontSize: '20px'
        }} onClick={() => { setShowAuth(false); setStep('identify'); setIdentifier(''); setPassword(''); setFullName(''); setError(''); setProvider('email'); }}>✕</button>

        {step === 'identify' && (
          <>
            <h2 style={{fontFamily: 'var(--font-d)', fontSize: '32px', marginBottom: '12px', textAlign: 'center', letterSpacing: '0.05em'}}>
              GET ACCESS
            </h2>
            <p style={{fontSize: '15px', color: 'var(--text1)', textAlign: 'center', marginBottom: '32px'}}>
              Enter your email or phone to continue.
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

            <div style={{display: 'flex', alignItems: 'center', gap: '10px', margin: '20px 0', opacity: 0.5}}>
              <div style={{flex: 1, height: '1px', background: 'var(--border)'}}></div>
              <span style={{fontSize: '12px'}}>QUICK OPTIONS</span>
              <div style={{flex: 1, height: '1px', background: 'var(--border)'}}></div>
            </div>

            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px'}}>
              <AuthButton icon="💬" label="WhatsApp" onClick={() => { setIdentifier('+675'); setProvider('whatsapp'); setStep('identify'); }} color="#25D366" />
              <AuthButton icon="📱" label="Phone" onClick={() => { setIdentifier('+675'); setProvider('phone'); setStep('identify'); }} color="#22c55e" />
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

  const AuthButton = ({ icon, label, onClick, color }) => (
    <button style={{
      display: 'flex', alignItems: 'center', gap: '12px', width: '100%',
      padding: '14px 20px', background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', color: 'var(--text1)', fontSize: '14px', fontWeight: '600',
      cursor: 'pointer', transition: 'all 0.2s', textAlign: 'left'
    }}
    onMouseEnter={e => { e.currentTarget.style.borderColor = color || 'var(--teal)'; e.currentTarget.style.color = 'var(--text0)'; }}
    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text1)'; }}
    onClick={onClick}>
      <span style={{fontSize: '18px'}}>{icon}</span>
      <span>{label}</span>
    </button>
  );

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
          font-size: clamp(64px, 7vw, 100px);
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
        .stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
        .stat-card {
          background:var(--bg1); border:1px solid var(--border);
          border-radius:12px; padding:24px 22px; position:relative; overflow:hidden;
        }

        .preview-section { padding:80px 72px; }
        .features-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }
        .feature-card {
          background:var(--bg1); border:1px solid var(--border);
          border-radius:14px; padding:28px 24px; position:relative; overflow:hidden;
          transition: all .3s;
        }

        @media (max-width:1024px) {
          .hero { grid-template-columns:1fr; padding:120px 40px 60px; }
          .hero-right { display:none; }
          .hero-left { padding:0; }
          nav { padding:0 24px; }
          .nav-links { display:none; }
          .stats-section { grid-template-columns:1fr; padding:60px 32px; }
          .features-grid { grid-template-columns:1fr; padding:0 32px; }
        }
      `}</style>

      <nav>
        <a href="#" className="nav-logo">PNG<span className="dot">●</span>PROPERTY</a>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#suburbs">Heatmap</a>
          <a href="#pricing">Pricing</a>
        </div>
        <div className="nav-cta">
          <button className="btn-ghost" onClick={() => setShowAuth(true)}>Sign In</button>
          <button className="btn-primary" onClick={() => setShowAuth(true)}>Get Access →</button>
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
            <button className="btn-hero-primary" onClick={() => setShowAuth(true)}>
              <span>Enter Dashboard</span> <span>→</span>
            </button>
          </div>
        </div>
        <div className="hero-right">
          <div className="dashboard-preview">
            <div className="scan-line"></div>
            <div style={{padding: '20px', textAlign: 'center'}}>
              <div style={{fontSize: '24px', marginBottom: '10px'}}>Live Analytics</div>
              <div style={{height: '200px', background: 'var(--bg2)', borderRadius: '8px'}}></div>
            </div>
          </div>
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

      <section className="preview-section">
        <div className="features-grid">
          <div className="feature-card reveal">
            <h3>Price Heatmap</h3>
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

      <footer style={{padding: '40px 72px', borderTop: '1px solid var(--border)', textAlign: 'center'}}>
        <p>© 2026 PNG Property Intelligence Dashboard. Built for Papua New Guinea by <a href="https://www.dspng.tech" target="_blank" rel="noopener noreferrer" style={{color: 'var(--teal)', textDecoration: 'none', fontWeight: '600'}}>Deeps Systems</a>.</p>
      </footer>

      {showAuth && <AuthModal />}
    </div>
  );
};

export default Landing;
