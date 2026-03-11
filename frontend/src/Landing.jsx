import React, { useEffect, useState } from 'react';

const Landing = ({ onEnterDashboard }) => {
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          // Note: animateCounter logic would need to be ported if used
          observer.unobserve(e.target);
        }
      });
    }, { threshold: 0.15 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const [authModal, setAuthModal] = useState(null); // 'login' | 'register' | null

  return (
    <div className="landing-container">
      <style>{`
        :root {
          --bg:       #080f14;
          --bg1:      #0c1820;
          --bg2:      #111f2b;
          --bg3:      #172737;
          --border:   #1a3040;
          --teal:     #0eb5b0;
          --teal2:    #07e8c4;
          --earth:    #c4742a;
          --earth2:   #e8943a;
          --green:    #2db87a;
          --red:      #e05252;
          --text0:    #f2f7fa;
          --text1:    #8db0c5;
          --text2:    #3d6478;
          --text3:    #1e3a4a;
          --font-d:   'Bebas Neue', sans-serif;
          --font-s:   'Fraunces', serif;
          --font-b:   'DM Sans', sans-serif;
          --font-m:   'DM Mono', monospace;
        }

        .landing-container {
          background: var(--bg);
          color: var(--text0);
          font-family: var(--font-b);
          line-height: 1.6;
          overflow-x: hidden;
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
          <button className="btn-ghost" onClick={onEnterDashboard}>Sign In</button>
          <button className="btn-primary" onClick={onEnterDashboard}>Get Access →</button>
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
            <button className="btn-hero-primary" onClick={onEnterDashboard}>
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
        <p>© 2025 PNG Property Dashboard. Built for Papua New Guinea.</p>
      </footer>
    </div>
  );
};

export default Landing;
