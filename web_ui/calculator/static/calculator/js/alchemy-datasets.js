// alchemy-datasets.js
// Reads from window.__INGREDIENTS__ and window.__EFFECTS__ injected by Django.

function DatasetsTab({ theme }) {
  const t           = theme;
  const ingredients = window.__INGREDIENTS__ || [];
  const effects     = window.__EFFECTS__     || [];

  const [tab, setTab]           = React.useState('ingredients');
  const [search, setSearch]     = React.useState('');
  const [effectFilter, setEF]   = React.useState('all');
  const [typeFilter, setTF]     = React.useState('all');
  const [sortCol, setSortCol]   = React.useState('name');
  const [sortDir, setSortDir]   = React.useState('asc');

  const effectOptions = React.useMemo(() => {
    const s = new Set();
    ingredients.forEach(i => i.effects.forEach(e => s.add(e.name)));
    return ['all', ...Array.from(s).sort()];
  }, []);

  const sortFn = (a, b, col, dir) => {
    let av = a[col], bv = b[col];
    if (typeof av === 'string') return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    return dir === 'asc' ? (av||0) - (bv||0) : (bv||0) - (av||0);
  };

  const filteredIngredients = React.useMemo(() => {
    return ingredients
      .filter(ing =>
        ing.name.toLowerCase().includes(search.toLowerCase()) &&
        (effectFilter === 'all' || ing.effects.some(e => e.name === effectFilter))
      )
      .sort((a,b) => sortFn(a, b, sortCol, sortDir));
  }, [search, effectFilter, sortCol, sortDir]);

  const filteredEffects = React.useMemo(() => {
    return effects
      .filter(e =>
        e.name.toLowerCase().includes(search.toLowerCase()) &&
        (typeFilter === 'all' || (typeFilter === 'beneficial' ? e.is_beneficial : e.is_poison))
      )
      .sort((a,b) => sortFn(a, b, sortCol, sortDir));
  }, [search, typeFilter, sortCol, sortDir]);

  const sort = col => { if (sortCol === col) setSortDir(d => d==='asc'?'desc':'asc'); else { setSortCol(col); setSortDir('asc'); } };

  const Th = ({ col, children, style={} }) => (
    <th onClick={()=>sort(col)} style={{ padding:'8px 12px', textAlign:'left', fontSize:'10px', fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase', color: sortCol===col ? t.accent : t.textMuted, fontFamily:'Space Grotesk', cursor:'pointer', whiteSpace:'nowrap', borderBottom:`1px solid ${t.border}`, background:t.surface, userSelect:'none', ...style }}>
      {children}{sortCol===col ? (sortDir==='asc'?' ↑':' ↓') : ''}
    </th>
  );
  const StaticTh = ({ children }) => (
    <th style={{ padding:'8px 12px', textAlign:'left', fontSize:'10px', fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase', color:t.textMuted, fontFamily:'Space Grotesk', borderBottom:`1px solid ${t.border}`, background:t.surface, whiteSpace:'nowrap' }}>{children}</th>
  );

  const rarityBadge = r => {
    const c = { common:t.textMuted, uncommon:'#79c0ff', rare:t.accent, very_rare:t.amber, unique:'#f85149' }[r] || t.textMuted;
    return <span style={{ fontSize:'9px', padding:'2px 7px', borderRadius:10, background:`${c}22`, color:c, border:`1px solid ${c}44` }}>{r?.replace('_',' ')}</span>;
  };
  const dlcBadge = d => {
    if (!d || d === 'base') return null;
    const c = { dawnguard:'#a78bfa', dragonborn:'#fb923c', hearthfire:'#60a5fa' }[d] || t.textMuted;
    return <span style={{ fontSize:'9px', padding:'2px 7px', borderRadius:10, background:`${c}22`, color:c, border:`1px solid ${c}44`, marginLeft:4 }}>{d}</span>;
  };

  const ingCount = name => ingredients.filter(i => i.effects.some(e => e.name === name)).length;

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'calc(100vh - 140px)', minHeight:600 }}>
      {/* Sub-tabs */}
      <div style={{ display:'flex', gap:0, marginBottom:16, background:t.surfaceAlt, borderRadius:8, padding:4, alignSelf:'flex-start' }}>
        {[['ingredients',`Ingredients (${ingredients.length})`],['effects',`Effects (${effects.length})`]].map(([id,label])=>(
          <button key={id} onClick={()=>{ setTab(id); setSearch(''); setSortCol('name'); setSortDir('asc'); }} style={{ padding:'6px 20px', borderRadius:5, border:'none', cursor:'pointer', background: tab===id ? t.accent : 'transparent', color: tab===id ? '#0d1117' : t.textMuted, fontFamily:'Space Grotesk', fontWeight:700, fontSize:'11px', letterSpacing:'0.06em', textTransform:'uppercase', transition:'all 0.15s' }}>{label}</button>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display:'flex', gap:8, marginBottom:12 }}>
        <div style={{ position:'relative', flex:1, maxWidth:280 }}>
          <svg width="13" height="13" viewBox="0 0 13 13" style={{ position:'absolute', left:10, top:'50%', transform:'translateY(-50%)', color:t.textMuted }} fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="5.5" cy="5.5" r="4"/><line x1="9" y1="9" x2="12" y2="12"/></svg>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder={`Search ${tab}…`} style={{ width:'100%', background:t.surface, border:`1px solid ${t.border}`, borderRadius:6, padding:'7px 10px 7px 28px', color:t.text, fontSize:'12px', outline:'none', boxSizing:'border-box' }}/>
        </div>
        {tab === 'ingredients' && (
          <select value={effectFilter} onChange={e=>setEF(e.target.value)} style={{ background:t.surface, border:`1px solid ${t.border}`, borderRadius:6, color:t.text, fontSize:'11px', padding:'7px 10px', outline:'none' }}>
            {effectOptions.map(e=><option key={e} value={e}>{e==='all'?'All Effects':e}</option>)}
          </select>
        )}
        {tab === 'effects' && (
          <select value={typeFilter} onChange={e=>setTF(e.target.value)} style={{ background:t.surface, border:`1px solid ${t.border}`, borderRadius:6, color:t.text, fontSize:'11px', padding:'7px 10px', outline:'none' }}>
            <option value="all">All Types</option>
            <option value="beneficial">Beneficial</option>
            <option value="harmful">Harmful</option>
          </select>
        )}
        <a href={tab==='ingredients' ? '/datasets/download/ingredients' : '/datasets/download/effects'} style={{ marginLeft:'auto', padding:'7px 14px', background:'transparent', border:`1px solid ${t.border}`, borderRadius:6, color:t.textMuted, fontSize:'11px', textDecoration:'none', display:'flex', alignItems:'center' }}>↓ CSV</a>
      </div>

      {/* Table */}
      <div style={{ flex:1, overflowY:'auto', background:t.surface, borderRadius:8, border:`1px solid ${t.border}` }}>
        {tab === 'ingredients' ? (
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'12px' }}>
            <thead style={{ position:'sticky', top:0, zIndex:1 }}>
              <tr><Th col="name">Ingredient</Th><Th col="rarity">Rarity</Th><Th col="value">Value</Th><Th col="weight">Weight</Th><StaticTh>Effects</StaticTh></tr>
            </thead>
            <tbody>
              {filteredIngredients.map((ing, idx) => (
                <tr key={ing.name} style={{ background: idx%2===0 ? 'transparent' : `${t.surfaceAlt}60` }}>
                  <td style={{ padding:'8px 12px', color:t.text, fontWeight:500 }}>{ing.name}{dlcBadge(ing.dlc)}</td>
                  <td style={{ padding:'8px 12px' }}>{rarityBadge(ing.rarity)}</td>
                  <td style={{ padding:'8px 12px', color:t.amber, fontFamily:'Space Grotesk', fontWeight:600 }}>{ing.value}g</td>
                  <td style={{ padding:'8px 12px', color:t.textMuted }}>{ing.weight}</td>
                  <td style={{ padding:'8px 12px' }}>
                    <div style={{ display:'flex', flexWrap:'wrap', gap:3 }}>
                      {ing.effects.map((e,i) => {
                        const eff = (window.__EFFECTS__||[]).find(x=>x.name===e.name);
                        const c   = eff?.is_beneficial ? t.accent : '#f85149';
                        return <span key={i} style={{ fontSize:'9px', padding:'1px 6px', borderRadius:8, background:`${c}18`, color:c, border:`1px solid ${c}33` }}>{e.name}</span>;
                      })}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'12px' }}>
            <thead style={{ position:'sticky', top:0, zIndex:1 }}>
              <tr><Th col="name">Effect</Th><StaticTh>Type</StaticTh><Th col="base_cost">Base Cost</Th><StaticTh>Ingredients</StaticTh><StaticTh>Varies</StaticTh></tr>
            </thead>
            <tbody>
              {filteredEffects.map((eff, idx) => {
                const c  = eff.is_beneficial ? t.accent : '#f85149';
                const ct = ingCount(eff.name);
                return (
                  <tr key={eff.name} style={{ background: idx%2===0 ? 'transparent' : `${t.surfaceAlt}60` }}>
                    <td style={{ padding:'8px 12px', color:t.text, fontWeight:500 }}>{eff.name}</td>
                    <td style={{ padding:'8px 12px' }}><span style={{ fontSize:'9px', padding:'2px 7px', borderRadius:10, background:`${c}18`, color:c, border:`1px solid ${c}33` }}>{eff.is_beneficial ? 'Beneficial' : 'Harmful'}</span></td>
                    <td style={{ padding:'8px 12px', color:t.amber, fontFamily:'Space Grotesk', fontWeight:600 }}>{eff.base_cost}</td>
                    <td style={{ padding:'8px 12px' }}>
                      <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                        <div style={{ width:Math.min(ct*8,80), height:4, borderRadius:2, background:t.accent, opacity:0.7 }}/>
                        <span style={{ fontSize:'11px', color:t.textMuted }}>{ct}</span>
                      </div>
                    </td>
                    <td style={{ padding:'8px 12px' }}>{eff.varies_duration && <span style={{ fontSize:'9px', color:t.accent }}>duration</span>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { DatasetsTab });
