// alchemy-browser.js
// The esv-alchemy browser (see CLAUDE.md "esv-alchemy browser"). Two side-by-side
// Panels — ingredients (left) + effects (right) — each independently searchable.
// Selecting a row replaces that panel's list with the item's Detail readout in
// place; the other panel stays a list with the related rows highlighted. The list
// returns when the user backs out of the Detail or focuses the search box again.
// Reads only the Django-injected globals via helpers from alchemy-shared.js; no
// alchemy math runs here.

// A generic column with two views: a searchable list, or — when `showDetail` is
// set — the selection's Detail in place of the list. The search box stays visible;
// focusing it exits the Detail back to the list. `kind` is cosmetic (placeholder
// text / key). The parent owns selection + cross-panel highlight state.
function Panel({ theme, kind, rows, renderRow, selectedName, highlightSet, onSelect, showDetail, detail, onExitDetail }) {
  const t = theme;
  const [search, setSearch] = React.useState('');

  const filtered = React.useMemo(
    () => rows.filter(r => r.name.toLowerCase().includes(search.toLowerCase())),
    [rows, search]
  );

  return (
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', background: t.surface, border: `1px solid ${t.border}`, borderRadius: 8 }}>
      {/* Search — focusing it returns to the list from a Detail */}
      <div style={{ padding: 10, borderBottom: `1px solid ${t.border}` }}>
        <div style={{ position: 'relative' }}>
          <svg width="13" height="13" viewBox="0 0 13 13" style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: t.textMuted }} fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="5.5" cy="5.5" r="4"/><line x1="9" y1="9" x2="12" y2="12"/></svg>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            onFocus={() => { if (showDetail) onExitDetail(); }}
            placeholder={`Search ${kind}…`}
            style={{ width: '100%', background: t.surfaceAlt, border: `1px solid ${t.border}`, borderRadius: 6, padding: '7px 10px 7px 28px', color: t.text, fontSize: '13px', outline: 'none', boxSizing: 'border-box' }}
          />
        </div>
      </div>

      {showDetail ? (
        /* Detail view — fills the panel in place of the list */
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 14px 16px' }}>
          <button
            onClick={onExitDetail}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: 'transparent', border: `1px solid ${t.border}`, borderRadius: 6, padding: '4px 10px', color: t.textMuted, fontSize: '11px', fontFamily: 'Space Grotesk', cursor: 'pointer', marginBottom: 10 }}
          >← Back to list</button>
          {detail}
        </div>
      ) : (
        /* List view */
        <div style={{ flex: 1, overflowY: 'auto', padding: 6 }}>
          {filtered.map(row => {
            const isSelected  = row.name === selectedName;
            const isHighlight = highlightSet && highlightSet.has(row.name);
            const border = isSelected ? t.accent : isHighlight ? `${t.accent}66` : 'transparent';
            return (
              <div
                key={row.name}
                onClick={() => onSelect(row)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px', marginBottom: 3,
                  borderRadius: 6, cursor: 'pointer', border: `1px solid ${border}`,
                  background: isSelected ? t.accentDim : isHighlight ? `${t.accent}10` : 'transparent',
                }}
              >
                {renderRow(row)}
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div style={{ padding: '20px 12px', fontSize: '12px', color: t.textMuted, textAlign: 'center' }}>No matches.</div>
          )}
        </div>
      )}
    </div>
  );
}

function BrowserTab({ theme }) {
  const t = theme;
  const ingredients = window.__INGREDIENTS__ || [];
  const effects     = window.__EFFECTS__     || [];

  const [selectedIngredient, setSelIng] = React.useState(null); // name | null
  const [selectedEffect,     setSelEff] = React.useState(null); // name | null
  const [ingredientView,     setIngView] = React.useState('list'); // 'list' | 'detail'
  const [effectView,         setEffView] = React.useState('list'); // 'list' | 'detail'

  // Per-ingredient profiles (synergies, ideal recipes, ...) are lazy-fetched from
  // /api/ingredient/<slug> on selection and cached here: name -> 'loading' |
  // 'error' | profile object. base_perf performance is fetched once up front.
  const [profiles, setProfiles] = React.useState({});
  const [perfMap,  setPerfMap]  = React.useState(null); // name -> performance entry

  React.useEffect(() => {
    fetch('/api/insights')
      .then(r => (r.ok ? r.json() : null))
      .then(d => setPerfMap(d?.average_performance || {}))
      .catch(() => setPerfMap({}));
  }, []);

  React.useEffect(() => {
    const name = selectedIngredient;
    if (!name || profiles[name]) return;
    setProfiles(prev => ({ ...prev, [name]: 'loading' }));
    fetch(`/api/ingredient/${slugifyIngredient(name)}`)
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(d => setProfiles(prev => ({ ...prev, [name]: d.profile })))
      .catch(() => setProfiles(prev => ({ ...prev, [name]: 'error' })));
  }, [selectedIngredient]);

  // Cross-panel highlight: a selected ingredient lights up its effects, and a
  // selected effect lights up its carrier ingredients. Highlights persist while
  // a selection is live, even after backing out of that panel's Detail.
  const effectHighlight = React.useMemo(() => {
    if (!selectedIngredient) return null;
    const ing = INGREDIENT_BY_NAME.get(selectedIngredient);
    return ing ? new Set(ing.effects.map(e => e.name).filter(Boolean)) : null;
  }, [selectedIngredient]);

  const ingredientHighlight = React.useMemo(() => {
    if (!selectedEffect) return null;
    return new Set(ingredientsWithEffect(selectedEffect).map(i => i.name));
  }, [selectedEffect]);

  const pickIngredient = ing => { setSelIng(ing.name); setIngView('detail'); };
  const pickEffect     = eff => { setSelEff(eff.name); setEffView('detail'); };

  // Cross-panel links from inside a Detail: a name opens the matching Detail in
  // the *other* panel (effect badges → Effect panel, carrier badges → Ingredient).
  const openIngredient = name => { setSelIng(name); setIngView('detail'); };
  const openEffect     = name => { setSelEff(name); setEffView('detail'); };

  const ingredientDetail = selectedIngredient
    ? <SelectionReadout theme={t} selection={{ type: 'ingredient', value: INGREDIENT_BY_NAME.get(selectedIngredient) }}
                        profile={profiles[selectedIngredient] ?? 'loading'}
                        performance={perfMap?.[selectedIngredient]?.avg_contribution != null ? perfMap[selectedIngredient] : null}
                        onSelectEffect={openEffect} onSelectIngredient={openIngredient}/>
    : null;
  const effectDetail = selectedEffect
    ? <SelectionReadout theme={t} selection={{ type: 'effect', value: EFFECT_BY_NAME.get(selectedEffect) }} onSelectIngredient={openIngredient}/>
    : null;

  const renderIngredientRow = ing => {
    const c = rarityColor(t, ing.rarity);
    return (
      <React.Fragment>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: c, flexShrink: 0 }}/>
        <span style={{ flex: 1, minWidth: 0, fontSize: '13px', color: t.text, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ing.name}</span>
      </React.Fragment>
    );
  };

  const renderEffectRow = eff => {
    const c = effectColor(t, eff.is_beneficial);
    return (
      <React.Fragment>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: c, flexShrink: 0 }}/>
        <span style={{ flex: 1, minWidth: 0, fontSize: '13px', color: t.text, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{eff.name}</span>
      </React.Fragment>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)', minHeight: 600 }}>
      <div style={{ fontSize: '12px', color: t.textMuted, marginBottom: 12 }}>
        data browser: select an ingredient / effect for details.
      </div>

      <div style={{ flex: 1, display: 'flex', gap: 12, minHeight: 0 }}>
        <Panel theme={t} kind="ingredients" rows={ingredients} renderRow={renderIngredientRow}
               selectedName={selectedIngredient} highlightSet={ingredientHighlight} onSelect={pickIngredient}
               showDetail={ingredientView === 'detail' && !!ingredientDetail} detail={ingredientDetail}
               onExitDetail={() => setIngView('list')}/>
        <Panel theme={t} kind="effects" rows={effects} renderRow={renderEffectRow}
               selectedName={selectedEffect} highlightSet={effectHighlight} onSelect={pickEffect}
               showDetail={effectView === 'detail' && !!effectDetail} detail={effectDetail}
               onExitDetail={() => setEffView('list')}/>
      </div>
    </div>
  );
}

Object.assign(window, { BrowserTab, Panel });
