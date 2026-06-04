// alchemy-calculator.js
// Reads ingredient list from window.__INGREDIENTS__ (injected by Django).
// All potion calculation is done by the Python backend via POST /api/calculate.

function CalculatorTab({ theme }) {
  const t = theme;
  const ingredients = window.__INGREDIENTS__ || [];

  const [skill, setSkill]               = React.useState(50);
  const [fortify, setFortify]           = React.useState(0);
  const [alchemistRank, setRank]        = React.useState(0);
  const [perks, setPerks]               = React.useState({ physician:false, benefactor:false, poisoner:false, purity:false, seeker:false });
  const [search, setSearch]             = React.useState('');
  const [effectFilter, setEffectFilter] = React.useState('all');
  const [selected, setSelected]         = React.useState(new Set());
  const [results, setResults]           = React.useState(null);
  const [error, setError]               = React.useState(null);
  const [loading, setLoading]           = React.useState(false);
  const [sortBy, setSortBy]             = React.useState('value');

  const togglePerk = k => setPerks(p => ({ ...p, [k]: !p[k] }));

  const allEffects = React.useMemo(() => {
    const s = new Set();
    ingredients.forEach(i => i.effects.forEach(e => s.add(e.name)));
    return ['all', ...Array.from(s).sort()];
  }, []);

  const filtered = React.useMemo(() =>
    ingredients.filter(ing =>
      ing.name.toLowerCase().includes(search.toLowerCase()) &&
      (effectFilter === 'all' || ing.effects.some(e => e.name === effectFilter))
    ), [search, effectFilter]);

  const toggle   = name => setSelected(p => { const n = new Set(p); n.has(name) ? n.delete(name) : n.add(name); return n; });
  const selectAll = () => setSelected(new Set(filtered.map(i => i.name)));
  const clearAll  = () => setSelected(new Set());

  const getCsrf = () => document.cookie.split(';').map(c=>c.trim()).find(c=>c.startsWith('csrftoken='))?.split('=')[1] || '';

  const calculate = async () => {
    if (selected.size < 2) return;
    setLoading(true); setError(null);
    try {
      const res = await fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify({
          skill, fortify, alchemist_rank: alchemistRank,
          physician: perks.physician, benefactor: perks.benefactor,
          poisoner: perks.poisoner, purity: perks.purity, seeker: perks.seeker,
          ingredients: [...selected],
        }),
      });
      const data = await res.json();
      if (res.ok) setResults(data.potions);
      else        setError(data.error || 'Calculation failed');
    } catch (e) {
      setError('Network error: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const sorted = React.useMemo(() => {
    if (!results) return null;
    if (sortBy === 'value')   return [...results].sort((a,b) => b.total_value - a.total_value);
    if (sortBy === 'effects') return [...results].sort((a,b) => b.effects.length - a.effects.length);
    if (sortBy === 'type')    return [...results].sort((a,b) => {
      const typeOf = p => p.effects.every(e => e.is_poison) ? 'poison' : p.effects.every(e => !e.is_poison) ? 'potion' : 'mixed';
      return typeOf(a).localeCompare(typeOf(b));
    });
    return results;
  }, [results, sortBy]);

  return (
    <div style={{ display:'grid', gridTemplateColumns:'260px 1fr 300px', gap:16, height:'calc(100vh - 140px)', minHeight:600 }}>

      {/* ── Left: Player Config ── */}
      <div style={{ background:t.surface, borderRadius:8, padding:20, overflowY:'auto', display:'flex', flexDirection:'column', gap:20 }}>
        <div>
          <div style={{ color:t.textMuted, fontSize:'10px', fontWeight:700, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:12, fontFamily:'Space Grotesk' }}>Player Stats</div>
          {[['Alchemy Skill', skill, setSkill, 0, 100, v => `${v}`],
            ['Fortify Alchemy', fortify, setFortify, 0, 143, v => `${v}%`]].map(([label, val, set, min, max, fmt]) => (
            <div key={label} style={{ marginBottom:14 }}>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:6 }}>
                <span style={{ fontSize:'12px', color:t.text }}>{label}</span>
                <span style={{ fontSize:'12px', color:t.accent, fontWeight:600, fontFamily:'Space Grotesk' }}>{fmt(val)}</span>
              </div>
              <input type="range" min={min} max={max} value={val} onChange={e=>set(+e.target.value)} className="styled-range" style={{ width:'100%' }}/>
            </div>
          ))}
        </div>

        <div>
          <div style={{ color:t.textMuted, fontSize:'10px', fontWeight:700, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:10, fontFamily:'Space Grotesk' }}>Alchemist Rank</div>
          <div style={{ display:'flex', gap:4 }}>
            {[0,1,2,3,4,5].map(r => (
              <button key={r} onClick={()=>setRank(r)} style={{ flex:1, padding:'4px 0', fontSize:'11px', fontFamily:'Space Grotesk', background: alchemistRank >= r && r > 0 ? t.accent : t.surfaceAlt, color: alchemistRank >= r && r > 0 ? '#0d1117' : t.textMuted, border:`1px solid ${alchemistRank===r ? t.accent : t.border}`, borderRadius:4, cursor:'pointer', fontWeight:600 }}>{r}</button>
            ))}
          </div>
          <div style={{ fontSize:'10px', color:t.textMuted, marginTop:4 }}>+{[0,0,20,40,60,80,100][alchemistRank]}% strength</div>
        </div>

        <div>
          <div style={{ color:t.textMuted, fontSize:'10px', fontWeight:700, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:10, fontFamily:'Space Grotesk' }}>Perks</div>
          {[['physician','Physician','+25% restore'],['benefactor','Benefactor','+25% beneficial'],['poisoner','Poisoner','+25% harmful'],['purity','Purity','Pure effects only'],['seeker','Seeker of Shadows','+15% all']].map(([k,l,d]) => (
            <div key={k} onClick={()=>togglePerk(k)} style={{ display:'flex', alignItems:'center', gap:10, padding:'7px 8px', borderRadius:6, cursor:'pointer', marginBottom:2, background: perks[k] ? t.accentDim : 'transparent', transition:'background 0.15s' }}>
              <div style={{ width:14, height:14, borderRadius:3, border:`2px solid ${perks[k] ? t.accent : t.border}`, background: perks[k] ? t.accent : 'transparent', flexShrink:0, display:'flex', alignItems:'center', justifyContent:'center' }}>
                {perks[k] && <svg width="8" height="6" viewBox="0 0 8 6"><polyline points="1,3 3,5 7,1" stroke="#0d1117" strokeWidth="1.5" fill="none"/></svg>}
              </div>
              <div>
                <div style={{ fontSize:'12px', color: perks[k] ? t.accent : t.text, fontWeight: perks[k] ? 600 : 400 }}>{l}</div>
                <div style={{ fontSize:'10px', color:t.textMuted }}>{d}</div>
              </div>
            </div>
          ))}
        </div>

        <button onClick={calculate} disabled={selected.size < 2 || loading} style={{ padding:10, background: selected.size >= 2 ? t.accent : t.surfaceAlt, color: selected.size >= 2 ? '#0d1117' : t.textMuted, border:'none', borderRadius:6, cursor: selected.size >= 2 ? 'pointer' : 'not-allowed', fontFamily:'Space Grotesk', fontWeight:700, fontSize:'13px', letterSpacing:'0.05em', transition:'all 0.2s', marginTop:'auto' }}>
          {loading ? 'Brewing…' : `Calculate (${selected.size} selected)`}
        </button>
      </div>

      {/* ── Center: Ingredient Selector ── */}
      <div style={{ background:t.surface, borderRadius:8, padding:20, display:'flex', flexDirection:'column', overflow:'hidden' }}>
        <div style={{ marginBottom:10 }}>
          <div style={{ display:'flex', gap:8, marginBottom:8 }}>
            <div style={{ flex:1, position:'relative' }}>
              <svg width="13" height="13" viewBox="0 0 13 13" style={{ position:'absolute', left:10, top:'50%', transform:'translateY(-50%)', color:t.textMuted }} fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="5.5" cy="5.5" r="4"/><line x1="9" y1="9" x2="12" y2="12"/></svg>
              <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search ingredients…" style={{ width:'100%', background:t.surfaceAlt, border:`1px solid ${t.border}`, borderRadius:6, padding:'7px 10px 7px 28px', color:t.text, fontSize:'12px', outline:'none', boxSizing:'border-box' }}/>
            </div>
            <select value={effectFilter} onChange={e=>setEffectFilter(e.target.value)} style={{ background:t.surfaceAlt, border:`1px solid ${t.border}`, borderRadius:6, color:t.text, fontSize:'11px', padding:'7px 10px', outline:'none', maxWidth:170 }}>
              {allEffects.map(e => <option key={e} value={e}>{e === 'all' ? 'All Effects' : e}</option>)}
            </select>
          </div>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
            <span style={{ fontSize:'11px', color:t.textMuted }}>{filtered.length} shown · {selected.size} selected</span>
            <div style={{ display:'flex', gap:8 }}>
              <button onClick={selectAll} style={{ fontSize:'11px', color:t.accent, background:'none', border:'none', cursor:'pointer', padding:0 }}>Select all</button>
              <button onClick={clearAll}  style={{ fontSize:'11px', color:t.textMuted, background:'none', border:'none', cursor:'pointer', padding:0 }}>Clear</button>
            </div>
          </div>
        </div>

        <div style={{ overflowY:'auto', flex:1 }}>
          <div style={{ display:'flex', flexWrap:'wrap', gap:6, alignContent:'flex-start' }}>
            {filtered.map(ing => {
              const isSel = selected.has(ing.name);
              const rc = { common:t.textMuted, uncommon:'#79c0ff', rare:t.accent, very_rare:t.amber, unique:'#f85149' }[ing.rarity] || t.textMuted;
              return (
                <button key={ing.name} onClick={()=>toggle(ing.name)} title={ing.effects.map(e=>e.name).join(' · ')} style={{ padding:'5px 10px', borderRadius:20, fontSize:'11px', cursor:'pointer', background: isSel ? t.accentDim : t.surfaceAlt, border:`1px solid ${isSel ? t.accent : t.border}`, color: isSel ? t.accent : t.text, transition:'all 0.15s', display:'flex', alignItems:'center', gap:4 }}>
                  <span style={{ width:5, height:5, borderRadius:'50%', background:rc, display:'inline-block', flexShrink:0 }}/>
                  {ing.name}
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ marginTop:10, paddingTop:10, borderTop:`1px solid ${t.border}`, display:'flex', gap:12, flexWrap:'wrap' }}>
          {[['common',t.textMuted,'Common'],['uncommon','#79c0ff','Uncommon'],['rare',t.accent,'Rare'],['very_rare',t.amber,'Very Rare']].map(([r,c,l])=>(
            <div key={r} style={{ display:'flex', alignItems:'center', gap:4, fontSize:'10px', color:t.textMuted }}>
              <span style={{ width:6, height:6, borderRadius:'50%', background:c, display:'inline-block' }}/>{l}
            </div>
          ))}
        </div>
      </div>

      {/* ── Right: Results ── */}
      <div style={{ background:t.surface, borderRadius:8, padding:20, display:'flex', flexDirection:'column', overflow:'hidden' }}>
        <div style={{ marginBottom:12, display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <span style={{ color:t.textMuted, fontSize:'10px', fontWeight:700, letterSpacing:'0.12em', textTransform:'uppercase', fontFamily:'Space Grotesk' }}>
            {sorted ? `${sorted.length} Potions` : 'Results'}
          </span>
          {sorted && (
            <select value={sortBy} onChange={e=>setSortBy(e.target.value)} style={{ background:t.surfaceAlt, border:`1px solid ${t.border}`, borderRadius:4, color:t.textMuted, fontSize:'10px', padding:'3px 6px', outline:'none' }}>
              <option value="value">By Value</option>
              <option value="effects">By Effects</option>
              <option value="type">By Type</option>
            </select>
          )}
        </div>

        <div style={{ overflowY:'auto', flex:1 }}>
          {!sorted && !loading && !error && (
            <div style={{ textAlign:'center', padding:'40px 20px', color:t.textMuted, fontSize:'12px', lineHeight:1.6 }}>
              <div style={{ fontSize:'24px', marginBottom:12, opacity:0.3 }}>⚗</div>
              Select ingredients and click<br/>Calculate to brew potions
            </div>
          )}
          {loading && <div style={{ display:'flex', justifyContent:'center', padding:40 }}><div className="spinner"/></div>}
          {error && <div style={{ padding:16, background:'#f8514922', border:'1px solid #f85149', borderRadius:6, color:'#f85149', fontSize:'12px' }}>{error}</div>}
          {sorted && sorted.length === 0 && <div style={{ textAlign:'center', padding:'40px 20px', color:t.textMuted, fontSize:'12px' }}>No potions found. Try more ingredients.</div>}
          {sorted && sorted.map((p, i) => {
            const type = p.effects.every(e => e.is_poison) ? 'poison' : p.effects.every(e => !e.is_poison) ? 'potion' : 'mixed';
            const tc   = type === 'potion' ? t.accent : type === 'poison' ? '#f85149' : t.amber;
            return (
              <div key={i} style={{ padding:'10px 12px', borderRadius:6, marginBottom:6, background:t.surfaceAlt, border:`1px solid ${t.border}`, borderLeft:`3px solid ${tc}` }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:4 }}>
                  <div style={{ fontSize:'12px', fontWeight:600, color:t.text, fontFamily:'Space Grotesk', lineHeight:1.3 }}>{p.name}</div>
                  <div style={{ fontSize:'13px', fontWeight:700, color:tc, fontFamily:'Space Grotesk', flexShrink:0, marginLeft:8 }}>{p.total_value}g</div>
                </div>
                <div style={{ fontSize:'10px', color:t.textMuted, marginBottom:5, fontStyle:'italic' }}>{p.ingredients.join(' + ')}</div>
                <div style={{ display:'flex', flexWrap:'wrap', gap:3 }}>
                  {p.effects.map((ef, j) => {
                    const c = ef.is_poison ? '#f85149' : t.accent;
                    return <span key={j} style={{ fontSize:'9px', padding:'2px 6px', borderRadius:10, background:`${c}18`, color:c, border:`1px solid ${c}33` }}>{ef.name}</span>;
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { CalculatorTab });
