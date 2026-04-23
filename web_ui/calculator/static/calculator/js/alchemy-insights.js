// alchemy-insights.js
// Fetches pre-computed analysis results from /api/insights (served by Django).
// Displays Monte Carlo simulation results — read-only, no client-side calculations.

function InsightsTab({ theme }) {
  const t = theme;
  const [data, setData]     = React.useState(null);
  const [loading, setLoad]  = React.useState(true);
  const [error, setError]   = React.useState(null);

  React.useEffect(() => {
    fetch('/api/insights')
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(d => { setData(d); setLoad(false); })
      .catch(e => { setError(e.message); setLoad(false); });
  }, []);

  if (loading) return (
    <div style={{ display:'flex', justifyContent:'center', alignItems:'center', height:400 }}>
      <div><div className="spinner" style={{ margin:'0 auto 12px' }}/><div style={{ fontSize:'12px', color:t.textMuted, textAlign:'center' }}>Loading analysis…</div></div>
    </div>
  );

  if (error) return (
    <div style={{ padding:32, background:`#f8514918`, border:`1px solid #f85149`, borderRadius:8, color:'#f85149', fontSize:'13px', lineHeight:1.6 }}>
      <strong>Could not load analysis data.</strong><br/>
      Run <code style={{ background:'#ffffff18', padding:'1px 6px', borderRadius:3 }}>python analysis/perks.py</code> and <code style={{ background:'#ffffff18', padding:'1px 6px', borderRadius:3 }}>python analysis/rarity.py</code> from the project root to generate results, then restart the server.
      <div style={{ marginTop:8, fontSize:'11px', opacity:0.7 }}>Error: {error}</div>
    </div>
  );

  const { perks, rarity } = data;

  // ── Derived data ─────────────────────────────────────────────────────────────

  const allIngredients = Object.entries(perks.ingredient_performance.baseline)
    .map(([name, d]) => ({ name, avg_value: d.avg_value, appearance_rate: d.appearance_rate }))
    .sort((a, b) => b.avg_value - a.avg_value);

  const topIngredients  = allIngredients.slice(0, 15);
  const worstIngredients = [...allIngredients].reverse().slice(0, 15);

  // Perk sensitivity: top 15 by pct_increase
  const perkSensitivity = Object.entries(perks.perk_sensitivity)
    .map(([name, d]) => ({ name, pct: Math.round(d.pct_increase), benefit: d.max_benefit, best_perk: d.best_perk }))
    .sort((a, b) => b.pct - a.pct)
    .slice(0, 15);

  // Perk value comparison: sum ingredient avg_value per config → total session gold
  const perkValueComparison = Object.entries(perks.ingredient_performance)
    .map(([config, ingredients]) => ({
      config,
      totalValue: Object.values(ingredients).reduce((sum, d) => sum + d.avg_value, 0),
    }));
  const baselineValue = perkValueComparison.find(p => p.config === 'baseline')?.totalValue || 1;
  const perkValueLifts = perkValueComparison
    .filter(p => p.config !== 'baseline')
    .map(p => ({ ...p, lift: p.totalValue - baselineValue, pct: ((p.totalValue - baselineValue) / baselineValue) * 100 }))
    .sort((a, b) => b.lift - a.lift);

  // ── Hero ingredient ──────────────────────────────────────────────────────────

  const heroName = allIngredients[0]?.name;
  const heroData = allIngredients[0];

  // Synergy count: other ingredients sharing at least one effect
  const heroIng     = (window.__INGREDIENTS__ || []).find(i => i.name === heroName);
  const heroEffects = new Set((heroIng?.effects || []).map(e => e.name).filter(Boolean));
  const synergyCount = (window.__INGREDIENTS__ || [])
    .filter(i => i.name !== heroName && i.effects.some(e => heroEffects.has(e.name)))
    .length;

  // Perk sensitivity for hero
  const heroPerkData   = perks.perk_sensitivity[heroName] || {};
  const heroPerkUplift = Math.round(heroPerkData.pct_increase || 0);
  const heroBestPerk   = heroPerkData.best_perk || 'none';

  // Rarity stability
  const heroCV = rarity.tolerance_scores?.[heroName]?.cv ?? null;
  const cvToLabel = cv => cv < 0.05 ? 'Very Stable' : cv < 0.12 ? 'Stable' : cv < 0.2 ? 'Moderate' : 'Volatile';
  const stabilityLabel = heroCV !== null ? cvToLabel(heroCV) : '—';

  // Rarity sparkline: avg_value across 6 distributions
  const DIST_ORDER = ['very_flat', 'flat', 'normal', 'steep', 'very_steep', 'extreme_steep'];
  const DIST_LABELS = ['Flat', '', 'Normal', '', 'Steep', ''];
  const sparkValues = DIST_ORDER.map(dist =>
    rarity.ingredient_performance?.[dist]?.[heroName]?.avg_value ?? 0
  );
  const sparkMax = Math.max(...sparkValues, 1);

  // ── Component helpers ────────────────────────────────────────────────────────

  const HBar = ({ label, value, maxVal, color, right, sub }) => (
    <div style={{ marginBottom:7 }}>
      <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3, alignItems:'baseline', gap:8 }}>
        <span style={{ fontSize:'11px', color:t.text, fontFamily:'IBM Plex Sans', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis', maxWidth:180 }}>{label}</span>
        <div style={{ display:'flex', alignItems:'center', gap:6, flexShrink:0 }}>
          {sub && <span style={{ fontSize:'9px', color:t.textMuted }}>{sub}</span>}
          <span style={{ fontSize:'11px', color, fontFamily:'Space Grotesk', fontWeight:600 }}>{right}</span>
        </div>
      </div>
      <div style={{ height:5, background:t.surfaceAlt, borderRadius:3, overflow:'hidden' }}>
        <div style={{ height:'100%', width:`${Math.max((value / maxVal) * 100, 2)}%`, background:color, borderRadius:3, transition:'width 0.5s ease' }}/>
      </div>
    </div>
  );

  const Card = ({ title, subtitle, children, style={} }) => (
    <div style={{ background:t.surface, borderRadius:10, padding:'20px 24px', border:`1px solid ${t.border}`, ...style }}>
      <div style={{ marginBottom:16 }}>
        <div style={{ fontSize:'13px', fontWeight:700, color:t.text, fontFamily:'Space Grotesk', marginBottom:4 }}>{title}</div>
        <div style={{ fontSize:'11px', color:t.textMuted, lineHeight:1.55 }}>{subtitle}</div>
      </div>
      {children}
    </div>
  );

  const perkColor = p => ({
    benefactor:'#79c0ff', physician:t.accent, poisoner:'#f85149',
    'benefactor+physician':'#a78bfa', 'benefactor+poisoner':'#fb923c',
    'physician+poisoner':'#60a5fa', all_perks:t.amber, none:t.textMuted
  })[p] || t.textMuted;

  const PerkBadge = ({ name }) => (
    <span style={{ fontSize:'9px', padding:'2px 7px', borderRadius:10, background:`${perkColor(name)}22`, color:perkColor(name), border:`1px solid ${perkColor(name)}44`, whiteSpace:'nowrap' }}>{name}</span>
  );

  const StatChip = ({ label, value, color, sub }) => (
    <div style={{ display:'flex', flexDirection:'column', gap:2, minWidth:90 }}>
      <div style={{ fontSize:'20px', fontWeight:700, color: color || t.accent, fontFamily:'Space Grotesk', lineHeight:1.1 }}>{value}</div>
      {sub && <div style={{ fontSize:'9px', color:t.textMuted, letterSpacing:'0.04em' }}>{sub}</div>}
      <div style={{ fontSize:'10px', color:t.textMuted, marginTop:1 }}>{label}</div>
    </div>
  );

  return (
    <div style={{ overflowY:'auto', height:'calc(100vh - 140px)', paddingBottom:40 }}>

      {/* ── Hero Card ─────────────────────────────────────────────────────── */}
      <div style={{
        background: t.surface,
        borderRadius: 12,
        border: `1px solid ${t.border}`,
        borderLeft: `4px solid ${t.accent}`,
        padding: '24px 28px',
        marginBottom: 20,
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Background glow */}
        <div style={{ position:'absolute', top:-40, right:-40, width:200, height:200, borderRadius:'50%', background:`${t.accent}08`, pointerEvents:'none' }}/>

        <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:24, flexWrap:'wrap' }}>
          <div style={{ flex:1, minWidth:220 }}>
            {/* Rank badge + name */}
            <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:8 }}>
              <span style={{ fontSize:'10px', fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase', padding:'3px 10px', borderRadius:10, background:`${t.amber}22`, color:t.amber, border:`1px solid ${t.amber}44`, fontFamily:'Space Grotesk' }}>#1 Ranked</span>
              <span style={{ fontSize:'10px', color:t.textMuted }}>Top Ingredient by Session Value</span>
            </div>
            <div style={{ fontSize:'28px', fontWeight:700, color:t.text, fontFamily:'Space Grotesk', letterSpacing:'-0.01em', marginBottom:4 }}>
              {heroName}
            </div>
            <div style={{ fontSize:'11px', color:t.textMuted, marginBottom:20, lineHeight:1.5 }}>
              Consistently the highest-value ingredient across all Monte Carlo sessions — outperforms the field regardless of rarity distribution or perk configuration.
            </div>

            {/* Stat chips */}
            <div style={{ display:'flex', gap:28, flexWrap:'wrap' }}>
              <StatChip
                label="Avg session value"
                value={`${heroData.avg_value.toLocaleString()}g`}
                color={t.accent}
              />
              <StatChip
                label="Appearance rate"
                value={`${Math.round(heroData.appearance_rate * 100)}%`}
                color={t.accent}
                sub="of crafting sessions"
              />
              <StatChip
                label="Synergises with"
                value={synergyCount}
                color={t.accent}
                sub="other ingredients"
              />
              <StatChip
                label="Rarity stability"
                value={stabilityLabel}
                color={heroCV !== null && heroCV < 0.05 ? t.accent : heroCV < 0.12 ? '#79c0ff' : t.amber}
              />
              <div style={{ display:'flex', flexDirection:'column', gap:2, minWidth:90 }}>
                <div style={{ fontSize:'20px', fontWeight:700, color:heroPerkUplift < 5 ? t.accent : t.amber, fontFamily:'Space Grotesk', lineHeight:1.1 }}>+{heroPerkUplift}%</div>
                <div style={{ fontSize:'9px', color:t.textMuted, letterSpacing:'0.04em', marginTop:1 }}>best perk: <PerkBadge name={heroBestPerk}/></div>
                <div style={{ fontSize:'10px', color:t.textMuted, marginTop:1 }}>Perk uplift</div>
              </div>
            </div>
          </div>

          {/* Sparkline: value across rarity distributions */}
          <div style={{ flexShrink:0, minWidth:160 }}>
            <div style={{ fontSize:'10px', color:t.textMuted, marginBottom:10, letterSpacing:'0.06em', textTransform:'uppercase', fontFamily:'Space Grotesk' }}>Value vs. Rarity Distribution</div>
            <div style={{ display:'flex', alignItems:'flex-end', gap:5, height:64 }}>
              {sparkValues.map((v, i) => (
                <div key={i} style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:4 }}>
                  <div style={{
                    width: 20,
                    height: Math.max(Math.round((v / sparkMax) * 56), 4),
                    background: i === 2 ? t.accent : `${t.accent}55`,
                    borderRadius: '3px 3px 0 0',
                    transition: 'height 0.4s ease',
                  }}/>
                  {DIST_LABELS[i] && (
                    <div style={{ fontSize:'8px', color:t.textMuted, whiteSpace:'nowrap' }}>{DIST_LABELS[i]}</div>
                  )}
                </div>
              ))}
            </div>
            <div style={{ marginTop:8, fontSize:'10px', color:t.textMuted, lineHeight:1.5 }}>
              Range: <span style={{ color:t.text, fontFamily:'Space Grotesk' }}>
                {Math.min(...sparkValues).toLocaleString()}g – {Math.max(...sparkValues).toLocaleString()}g
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Top + Bottom Rankings ─────────────────────────────────────────── */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16 }}>

        <Card
          title="Top Performers"
          subtitle={`Highest average total gold value contributed per crafting session (baseline player, normal rarity distribution, ${perks.metadata.num_simulations.toLocaleString()} simulations).`}
        >
          {topIngredients.map(({ name, avg_value, appearance_rate }) => (
            <HBar
              key={name}
              label={name}
              value={avg_value}
              maxVal={topIngredients[0].avg_value}
              color={t.accent}
              right={`${avg_value.toLocaleString()}g`}
              sub={`${Math.round(appearance_rate * 100)}% of runs`}
            />
          ))}
        </Card>

        <Card
          title="Bottom Performers"
          subtitle="Lowest average session value — these ingredients rarely produce high-value potions and are largely interchangeable with whatever's available."
        >
          {worstIngredients.map(({ name, avg_value, appearance_rate }) => (
            <HBar
              key={name}
              label={name}
              value={avg_value}
              maxVal={worstIngredients[0].avg_value}
              color="#f85149"
              right={`${avg_value.toLocaleString()}g`}
              sub={`${Math.round(appearance_rate * 100)}% of runs`}
            />
          ))}
        </Card>
      </div>

      {/* ── Perk Sensitivity + Perk Config Comparison ─────────────────────── */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>

        <Card
          title="Perk Sensitivity"
          subtitle="Percentage increase in average ingredient value when the best perk is applied vs. baseline (no perks). High uplift = this ingredient is perk-dependent."
        >
          {perkSensitivity.map(({ name, pct, benefit, best_perk }) => (
            <div key={name} style={{ marginBottom:7 }}>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3, alignItems:'center', gap:6 }}>
                <span style={{ fontSize:'11px', color:t.text, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:140 }}>{name}</span>
                <div style={{ display:'flex', alignItems:'center', gap:6, flexShrink:0 }}>
                  <PerkBadge name={best_perk}/>
                  <span style={{ fontSize:'11px', color:t.amber, fontFamily:'Space Grotesk', fontWeight:600 }}>+{pct}%</span>
                </div>
              </div>
              <div style={{ height:5, background:t.surfaceAlt, borderRadius:3, overflow:'hidden' }}>
                <div style={{ height:'100%', width:`${Math.max((pct / perkSensitivity[0].pct) * 100, 2)}%`, background:perkColor(best_perk), borderRadius:3, transition:'width 0.5s ease' }}/>
              </div>
            </div>
          ))}
        </Card>

        <Card
          title="Perk Gold Value Uplift"
          subtitle={`Extra gold earned per session vs. no perks (baseline: ${baselineValue.toLocaleString()}g). Poisoner-heavy builds dominate; physician adds modest value.`}
        >
          {perkValueLifts.map(({ config, lift, pct, totalValue }) => (
            <div key={config} style={{ marginBottom:7 }}>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3, alignItems:'center', gap:6 }}>
                <span style={{ fontSize:'11px', color:t.text, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:160 }}>
                  {config.replace(/\+/g, ' + ')}
                </span>
                <div style={{ display:'flex', alignItems:'center', gap:6, flexShrink:0 }}>
                  <span style={{ fontSize:'9px', color:t.textMuted, fontFamily:'Space Grotesk' }}>{totalValue.toLocaleString()}g total</span>
                  <span style={{ fontSize:'11px', color:perkColor(config), fontFamily:'Space Grotesk', fontWeight:600 }}>+{pct.toFixed(1)}%</span>
                </div>
              </div>
              <div style={{ height:5, background:t.surfaceAlt, borderRadius:3, overflow:'hidden' }}>
                <div style={{ height:'100%', width:`${Math.max((pct / perkValueLifts[0].pct) * 100, 2)}%`, background:perkColor(config), borderRadius:3, transition:'width 0.5s ease' }}/>
              </div>
            </div>
          ))}
          <div style={{ marginTop:14, padding:'10px 12px', background:t.surfaceAlt, borderRadius:6, fontSize:'11px', color:t.textMuted, lineHeight:1.5 }}>
            Baseline (no perks): <span style={{ color:t.text, fontFamily:'Space Grotesk' }}>{baselineValue.toLocaleString()}g</span> avg per session
          </div>
        </Card>
      </div>
    </div>
  );
}

Object.assign(window, { InsightsTab });
