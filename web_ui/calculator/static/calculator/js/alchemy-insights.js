// alchemy-insights.js
// Fetches pre-computed analysis results from /api/insights (served by Django).
// Displays the base ingredient performance ranking — read-only, no client-side
// calculations.

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
      Run <code style={{ background:'#ffffff18', padding:'1px 6px', borderRadius:3 }}>python experiments/base_perf.py</code> from the project root to generate results, then restart the server.
      <div style={{ marginTop:8, fontSize:'11px', opacity:0.7 }}>Error: {error}</div>
    </div>
  );

  // ── Derived data ─────────────────────────────────────────────────────────────
  // Rank every ingredient by its average contribution to session value.
  // Ingredients never sampled in the experiment (e.g. Jarrin Root, which is
  // excluded from inventory generation) have a null contribution — drop them.
  const ingredients = Object.entries(data.average_performance || {})
    .map(([name, d]) => ({
      name,
      avg_potion_value: d.avg_potion_value,
      stderr_potion_value: d.stderr_potion_value,
      avg_contribution: d.avg_contribution,
      appearance_rate: d.appearance_rate,
    }))
    .filter(ing => ing.avg_contribution != null)
    .sort((a, b) => b.avg_contribution - a.avg_contribution);

  const maxContribution = ingredients[0]?.avg_contribution || 1;
  const round = v => Math.round(v).toLocaleString();

  // ── Shared component wrappers (inject theme) ──────────────────────────────────
  const Shared = window;
  const HBar = (props) => <Shared.HBar theme={t} {...props}/>;
  const Card = (props) => <Shared.Card theme={t} {...props}/>;
  const StatChip = (props) => <Shared.StatChip theme={t} {...props}/>;

  const subtitle = 'Average potion value contribution across a massive number of random simulations.';

  // Global stats — derived from the run-level fields the API already returns.
  // `n` (simulation count) isn't stored directly; recover it from totals/averages.
  const simulations = data.average_potions ? Math.round(data.total_potions / data.average_potions) : null;
  const globalStats = [
    simulations != null && { label: 'Simulations',       value: round(simulations) },
    data.total_potions != null && { label: 'Total Potions',     value: round(data.total_potions) },
    data.total_value   != null && { label: 'Total Value',       value: `${round(data.total_value)}g` },
    data.average_value != null && { label: 'Avg Session Value', value: `${round(data.average_value)}g` },
  ].filter(Boolean);

  // Native tooltip per ingredient, from the fields present in the results JSON.
  const hoverTitle = ing => [
    `Appearance rate: ${(ing.appearance_rate * 100).toFixed(1)}%`,
    `Avg potion value: ${round(ing.avg_potion_value)}g`,
    ing.stderr_potion_value != null ? `Std error: ±${ing.stderr_potion_value.toFixed(1)}g` : null,
    `Contribution: ${round(ing.avg_contribution)}g`,
  ].filter(Boolean).join('\n');

  return (
    <div style={{ overflowY:'auto', height:'calc(100vh - 140px)', paddingBottom:40 }}>
      <Card title="Ingredient Performance" subtitle={subtitle}>
        {globalStats.length > 0 && (
          <div style={{ display:'flex', flexWrap:'wrap', gap:24, marginBottom:20, paddingBottom:16, borderBottom:`1px solid ${t.border}` }}>
            {globalStats.map(s => <StatChip key={s.label} label={s.label} value={s.value}/>)}
          </div>
        )}
        {ingredients.map((ing, i) => (
          <HBar
            key={ing.name}
            label={`${i + 1}. ${ing.name}`}
            value={ing.avg_contribution}
            maxVal={maxContribution}
            color={t.accent}
            right={`${round(ing.avg_contribution)}g`}
            title={hoverTitle(ing)}
          />
        ))}
      </Card>
    </div>
  );
}

Object.assign(window, { InsightsTab });
