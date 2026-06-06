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

  const subtitle = data.average_value != null
    ? `Average total gold value each ingredient contributes per crafting session, ranked across ${round(data.average_potions)} potions per session at ${round(data.average_value)}g avg session value. Bars and right-hand figure show contribution; "avg" is the mean value of potions the ingredient appears in.`
    : `Average total gold value each ingredient contributes per crafting session. Bars and right-hand figure show contribution; "avg" is the mean value of potions the ingredient appears in.`;

  return (
    <div style={{ overflowY:'auto', height:'calc(100vh - 140px)', paddingBottom:40 }}>
      <Card title="Ingredient Performance" subtitle={subtitle}>
        {ingredients.map((ing, i) => (
          <HBar
            key={ing.name}
            label={`${i + 1}. ${ing.name}`}
            value={ing.avg_contribution}
            maxVal={maxContribution}
            color={t.accent}
            right={`${round(ing.avg_contribution)}g`}
            sub={`${round(ing.avg_potion_value)}g avg`}
          />
        ))}
      </Card>
    </div>
  );
}

Object.assign(window, { InsightsTab });
