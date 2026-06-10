// alchemy-shared.js
// Shared lookups, helpers, and presentational components for all tabs.
// Loaded before the tab scripts; everything is exposed on `window` (the same
// pattern the tab files use) so calculator/datasets/insights can consume it.
// No build step — this is a Babel-standalone script like the rest.

// ── Data lookups (built once from the Django-injected globals) ─────────────────
const _INGREDIENTS = window.__INGREDIENTS__ || [];
const _EFFECTS     = window.__EFFECTS__     || [];

// name -> effect metadata / ingredient object
const EFFECT_BY_NAME     = new Map(_EFFECTS.map(e => [e.name, e]));
const INGREDIENT_BY_NAME = new Map(_INGREDIENTS.map(i => [i.name, i]));

// effect-name -> ingredients carrying it (drives "all effects" lists + counts)
const _INGREDIENTS_BY_EFFECT = (() => {
  const m = new Map();
  _INGREDIENTS.forEach(ing =>
    ing.effects.forEach(e => {
      if (!e.name) return;
      if (!m.has(e.name)) m.set(e.name, []);
      m.get(e.name).push(ing);
    })
  );
  return m;
})();

// Sorted list of effect names that actually appear on ingredients.
const EFFECT_NAMES   = Array.from(_INGREDIENTS_BY_EFFECT.keys()).sort();
const EFFECT_OPTIONS = ['all', ...EFFECT_NAMES];

const ingredientsWithEffect = name => _INGREDIENTS_BY_EFFECT.get(name) || [];

// ── Utilities ──────────────────────────────────────────────────────────────────
const getCsrf = () =>
  document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';

const sortFn = (a, b, col, dir) => {
  let av = a[col], bv = b[col];
  if (typeof av === 'string') return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
  return dir === 'asc' ? (av || 0) - (bv || 0) : (bv || 0) - (av || 0);
};

const cvToLabel = cv =>
  cv < 0.05 ? 'Very Stable' : cv < 0.12 ? 'Stable' : cv < 0.2 ? 'Moderate' : 'Volatile';

// ── Theme-aware color helpers ───────────────────────────────────────────────────
const rarityColor = (t, r) =>
  ({ common: t.textMuted, uncommon: '#79c0ff', rare: t.accent, very_rare: t.amber, unique: '#f85149' }[r] || t.textMuted);

const dlcColor = (t, d) =>
  ({ dawnguard: '#a78bfa', dragonborn: '#fb923c', hearthfire: '#60a5fa' }[d] || t.textMuted);

const perkColor = (t, p) =>
  ({
    benefactor: '#79c0ff', physician: t.accent, poisoner: '#f85149',
    'benefactor+physician': '#a78bfa', 'benefactor+poisoner': '#fb923c',
    'physician+poisoner': '#60a5fa', all_perks: t.amber, none: t.textMuted,
  }[p] || t.textMuted);

const effectColor = (t, isBeneficial) => (isBeneficial ? t.accent : '#f85149');

// name -> results/ingredients/<slug>.json basename. Mirrors _slugify in
// experiments/profiles.py exactly so the lazy-fetch URL matches the file on disk.
const slugifyIngredient = name =>
  name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');

// ── Presentational components (take `theme`) ───────────────────────────────────
// Slightly larger Badge sizing for the prominent ingredient/effect chips in the
// browser Details (Effects, Carriers) — bigger tap targets than the dense lists.
const DETAIL_CHIP = { fontSize: '11px', padding: '3px 9px' };

function Badge({ theme, color, children, style = {}, onClick, title }) {
  return (
    <span
      onClick={onClick}
      title={title}
      style={{ fontSize: '9px', padding: '2px 7px', borderRadius: 10, background: `${color}22`, color, border: `1px solid ${color}44`, ...(onClick ? { cursor: 'pointer' } : {}), ...style }}
    >
      {children}
    </span>
  );
}

function Card({ theme, title, subtitle, children, style = {} }) {
  const t = theme;
  return (
    <div style={{ background: t.surface, borderRadius: 10, padding: '20px 24px', border: `1px solid ${t.border}`, ...style }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: '14px', fontWeight: 700, color: t.text, fontFamily: 'Space Grotesk', marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: '12px', color: t.textMuted, lineHeight: 1.55 }}>{subtitle}</div>
      </div>
      {children}
    </div>
  );
}

function HBar({ theme, label, value, maxVal, color, right, sub, title }) {
  const t = theme;
  return (
    <div style={{ marginBottom: 7 }} title={title}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3, alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: '12px', color: t.text, fontFamily: 'IBM Plex Sans', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 180 }}>{label}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          {sub && <span style={{ fontSize: '9px', color: t.textMuted }}>{sub}</span>}
          <span style={{ fontSize: '12px', color, fontFamily: 'Space Grotesk', fontWeight: 600 }}>{right}</span>
        </div>
      </div>
      <div style={{ height: 5, background: t.surfaceAlt, borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${Math.max((value / maxVal) * 100, 2)}%`, background: color, borderRadius: 3, transition: 'width 0.5s ease' }}/>
      </div>
    </div>
  );
}

function StatChip({ theme, label, value, color, sub }) {
  const t = theme;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 90 }}>
      <div style={{ fontSize: '20px', fontWeight: 700, color: color || t.accent, fontFamily: 'Space Grotesk', lineHeight: 1.1 }}>{value}</div>
      {sub && <div style={{ fontSize: '9px', color: t.textMuted, letterSpacing: '0.04em' }}>{sub}</div>}
      <div style={{ fontSize: '10px', color: t.textMuted, marginTop: 1 }}>{label}</div>
    </div>
  );
}

// Sortable (or static, when no onSort) table header cell.
function TableHeader({ theme, col, sortCol, sortDir, onSort, children, style = {} }) {
  const t = theme;
  const sortable = !!onSort;
  const active = sortable && sortCol === col;
  return (
    <th
      onClick={sortable ? () => onSort(col) : undefined}
      style={{
        padding: '8px 12px', textAlign: 'left', fontSize: '10px', fontWeight: 700, letterSpacing: '0.1em',
        textTransform: 'uppercase', color: active ? t.accent : t.textMuted, fontFamily: 'Space Grotesk',
        borderBottom: `1px solid ${t.border}`, background: t.surface, whiteSpace: 'nowrap',
        ...(sortable ? { cursor: 'pointer', userSelect: 'none' } : {}), ...style,
      }}
    >
      {children}{active ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
    </th>
  );
}

// ── esv-alchemy browser — Detail scaffolding ────────────────────────────────────
// Building blocks for the two-panel browser (see CLAUDE.md "esv-alchemy browser").
// A Detail is a stack of named Sections; each Section is tagged with the data
// source that will eventually feed it: `globals` (Django-injected, live now),
// `results` (precomputed experiment JSON), or `live` (a future engine endpoint).
// Sections without content yet render a placeholder so the structure is visible.

const SECTION_SOURCE_LABEL = { globals: 'data', results: 'analysis', live: 'live' };

// A titled block inside a Detail. Renders `children`, or a placeholder stub when
// empty (the scaffolding state). `source` documents where the content comes from.
function Section({ theme, title, source = 'globals', children }) {
  const t = theme;
  const filled = React.Children.count(children) > 0;
  return (
    <div style={{ borderTop: `1px solid ${t.border}`, padding: '12px 0' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: filled ? 8 : 0 }}>
        <span style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: t.textMuted, fontFamily: 'Space Grotesk' }}>{title}</span>
        <span style={{ fontSize: '8px', letterSpacing: '0.08em', textTransform: 'uppercase', color: t.textMuted, opacity: 0.5 }}>{SECTION_SOURCE_LABEL[source] || source}</span>
      </div>
      {filled
        ? children
        : <div style={{ fontSize: '11px', color: t.textMuted, opacity: 0.6, fontStyle: 'italic' }}>— placeholder —</div>}
    </div>
  );
}

// A compact readout of one precomputed recipe (the ideal_2/3 potion dicts from
// profiles.py: name, ingredients, total_value, effects). Ingredient names are
// clickable Links into the ingredient panel when `onSelectIngredient` is given.
function PotionMini({ theme, potion, onSelectIngredient }) {
  const t = theme;
  if (!potion) return null;
  const dominantPoison = potion.effects?.some(e => e.is_poison);
  return (
    <div style={{ background: t.surfaceAlt, border: `1px solid ${t.border}`, borderRadius: 6, padding: '8px 10px', marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: t.text, fontFamily: 'Space Grotesk' }}>{potion.name}</span>
        <span style={{ fontSize: '12px', fontWeight: 700, color: dominantPoison ? '#f85149' : t.accent, fontFamily: 'Space Grotesk', whiteSpace: 'nowrap' }}>{potion.total_value}g</span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: potion.effects?.length ? 5 : 0 }}>
        {potion.ingredients.map(n => (
          <Badge key={n} theme={t} color={rarityColor(t, INGREDIENT_BY_NAME.get(n)?.rarity)}
                 onClick={onSelectIngredient ? () => onSelectIngredient(n) : undefined}
                 title={onSelectIngredient ? `Show ${n}` : undefined}>{n}</Badge>
        ))}
      </div>
      {potion.effects?.map(e => (
        <div key={e.name} style={{ fontSize: '10px', color: t.textMuted, lineHeight: 1.5 }}>
          <span style={{ color: effectColor(t, !e.is_poison) }}>•</span> {e.name} — {e.value}g
        </div>
      ))}
    </div>
  );
}

function IngredientDetail({ theme, ingredient, profile, performance, onSelectEffect, onSelectIngredient }) {
  const t = theme;
  if (!ingredient) return null;
  const effectNames = ingredient.effects.map(e => e.name).filter(Boolean);
  const p = profile === 'loading' || profile === 'error' ? null : profile;
  const profileState = profile; // 'loading' | 'error' | object | null
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: '17px', fontWeight: 700, color: t.text, fontFamily: 'Space Grotesk' }}>{ingredient.name}</span>
        <Badge theme={t} color={rarityColor(t, ingredient.rarity)}>{ingredient.rarity?.replace('_', ' ')}</Badge>
        {ingredient.dlc && ingredient.dlc !== 'base' && (
          <Badge theme={t} color={dlcColor(t, ingredient.dlc)}>{ingredient.dlc}</Badge>
        )}
      </div>

      <Section theme={t} title="Identity" source="globals">
        <div style={{ fontSize: '12px', color: t.textMuted }}>
          cost: {ingredient.value}g · weight: {ingredient.weight}{ingredient.source ? ` · source: ${ingredient.source}` : ''}
        </div>
      </Section>

      <Section theme={t} title="Effects" source="globals">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          {effectNames.map(name => {
            const c = effectColor(t, EFFECT_BY_NAME.get(name)?.is_beneficial);
            return (
              <Badge key={name} theme={t} color={c} style={DETAIL_CHIP}
                     onClick={onSelectEffect ? () => onSelectEffect(name) : undefined}
                     title={onSelectEffect ? `Show ${name}` : undefined}>
                {name}
              </Badge>
            );
          })}
        </div>
      </Section>

      <Section theme={t} title="Synergies" source="results">
        <ResultsBody theme={t} state={profileState}>
          {p && (() => {
            const sbo = p.synergy_by_order || {};
            const partners = p.synergizing_by_order || {};
            return (
              <div>
                <div style={{ display: 'flex', gap: 14, marginBottom: 8, flexWrap: 'wrap' }}>
                  <MiniStat theme={t} label="compatible" value={p.compatible_count}
                            title="Number of other ingredients that share at least one effect with this one."/>
                  <MiniStat theme={t} label="synergy wt" value={p.total_synergy_weight}
                            title="Total shared effects across all compatible partners (a partner sharing 2 effects counts twice). Higher = more ways to combine."/>
                </div>
                {['4','3','2','1'].filter(k => (partners[k] || []).length).map(k => (
                  <div key={k} style={{ marginBottom: 6 }}>
                    <div style={{ fontSize: '9px', color: t.textMuted, marginBottom: 3 }}>
                      shares {k} effect{k === '1' ? '' : 's'} · {partners[k].length}
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {partners[k].map(n => (
                        <Badge key={n} theme={t} color={rarityColor(t, INGREDIENT_BY_NAME.get(n)?.rarity)}
                               onClick={onSelectIngredient ? () => onSelectIngredient(n) : undefined}
                               title={onSelectIngredient ? `Show ${n}` : undefined}>{n}</Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            );
          })()}
        </ResultsBody>
      </Section>

      <Section theme={t} title="Best Recipes" source="results">
        <ResultsBody theme={t} state={profileState}>
          {p && (p.ideal_2_ingredient_potion || p.ideal_3_ingredient_potion) && (
            <div>
              {p.ideal_2_ingredient_potion && (
                <div style={{ fontSize: '9px', color: t.textMuted, marginBottom: 3 }}>best 2-ingredient</div>
              )}
              <PotionMini theme={t} potion={p.ideal_2_ingredient_potion} onSelectIngredient={onSelectIngredient}/>
              {p.ideal_3_ingredient_potion && (
                <div style={{ fontSize: '9px', color: t.textMuted, margin: '6px 0 3px' }}>best 3-ingredient</div>
              )}
              <PotionMini theme={t} potion={p.ideal_3_ingredient_potion} onSelectIngredient={onSelectIngredient}/>
              <div style={{ fontSize: '9px', color: t.textMuted, opacity: 0.7, marginTop: 6, fontStyle: 'italic' }}>
                Highest-value base-player recipe at each size.{ingredient.name !== 'Jarrin Root' ? ' Excludes Jarrin Root (a quest item).' : ''}
              </div>
            </div>
          )}
        </ResultsBody>
      </Section>

      <Section theme={t} title="Performance" source="results">
        {performance ? (
          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
            <MiniStat theme={t} label="appearance" value={`${(performance.appearance_rate * 100).toFixed(1)}%`}/>
            <MiniStat theme={t} label="avg potion" value={`${Math.round(performance.avg_potion_value)}g`}/>
            <MiniStat theme={t} label="contribution" value={`${Math.round(performance.avg_contribution)}g`}/>
          </div>
        ) : (
          <div style={{ fontSize: '11px', color: t.textMuted, opacity: 0.6, fontStyle: 'italic' }}>
            Not sampled in the performance run.
          </div>
        )}
      </Section>
    </div>
  );
}

// Renders results-backed Section content with graceful loading / error / empty
// states (mirrors the insights tab's 404 handling). `state` is the fetch result:
// 'loading', 'error', null (no profile), or the profile object passed as children.
function ResultsBody({ theme, state, children }) {
  const t = theme;
  const msg = s => <div style={{ fontSize: '11px', color: t.textMuted, opacity: 0.6, fontStyle: 'italic' }}>{s}</div>;
  if (state === 'loading') return msg('Loading analysis…');
  if (state === 'error' || state == null) return msg('No analysis — run experiments/profiles.py.');
  return children;
}

// Inline label + value stat used inside browser Sections. `title` adds a native
// hover tooltip explaining the stat.
function MiniStat({ theme, label, value, title }) {
  const t = theme;
  return (
    <div title={title} style={{ display: 'flex', flexDirection: 'column', gap: 1, ...(title ? { cursor: 'help' } : {}) }}>
      <span style={{ fontSize: '15px', fontWeight: 700, color: t.text, fontFamily: 'Space Grotesk', lineHeight: 1.1 }}>{value}</span>
      <span style={{ fontSize: '9px', color: t.textMuted, letterSpacing: '0.04em', ...(title ? { borderBottom: `1px dotted ${t.textMuted}66` } : {}) }}>{label}</span>
    </div>
  );
}

function EffectDetail({ theme, effect, onSelectIngredient }) {
  const t = theme;
  if (!effect) return null;
  const carriers = ingredientsWithEffect(effect.name);
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: '17px', fontWeight: 700, color: t.text, fontFamily: 'Space Grotesk' }}>{effect.name}</span>
        <Badge theme={t} color={effectColor(t, effect.is_beneficial)}>{effect.is_beneficial ? 'Beneficial' : 'Harmful'}</Badge>
      </div>

      <Section theme={t} title="Identity" source="globals">
        <div style={{ fontSize: '12px', color: t.textMuted }}>
          {effect.is_beneficial ? 'Beneficial' : 'Harmful'} · scales {effect.varies_duration ? 'duration' : 'magnitude'}
        </div>
      </Section>

      <Section theme={t} title="Base Stats" source="globals">
        <div style={{ fontSize: '12px', color: t.textMuted }}>
          base cost {effect.base_cost} · base mag {effect.base_magnitude} · base dur {effect.base_duration}
        </div>
      </Section>

      <Section theme={t} title="Carriers" source="globals">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          {carriers.map(ing => (
            <Badge key={ing.name} theme={t} color={rarityColor(t, ing.rarity)} style={DETAIL_CHIP}
                   onClick={onSelectIngredient ? () => onSelectIngredient(ing.name) : undefined}
                   title={onSelectIngredient ? `Show ${ing.name}` : undefined}>
              {ing.name}
            </Badge>
          ))}
        </div>
      </Section>

      <Section theme={t} title="Perk Alignment" source="results" />
    </div>
  );
}

// Dispatches to the right Detail for a { type, value } selection.
function SelectionReadout({ theme, selection, profile, performance, onSelectIngredient, onSelectEffect }) {
  if (!selection) return null;
  if (selection.type === 'ingredient') return <IngredientDetail theme={theme} ingredient={selection.value} profile={profile} performance={performance} onSelectEffect={onSelectEffect} onSelectIngredient={onSelectIngredient} />;
  if (selection.type === 'effect')     return <EffectDetail theme={theme} effect={selection.value} onSelectIngredient={onSelectIngredient} />;
  return null;
}

// Centered modal overlay that hosts a Detail. Closes on backdrop click, the [x]
// button, or Escape. Children render inside the panel.
function DetailModal({ theme, onClose, children }) {
  const t = theme;
  React.useEffect(() => {
    const h = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [onClose]);
  return (
    <div
      onClick={onClose}
      style={{ position: 'fixed', inset: 0, background: '#00000099', backdropFilter: 'blur(2px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{ position: 'relative', background: t.surface, border: `1px solid ${t.border}`, borderRadius: 12, padding: '22px 26px', width: 'min(560px, 92vw)', maxHeight: '82vh', overflowY: 'auto', boxShadow: '0 16px 48px #00000088' }}
      >
        <button
          onClick={onClose}
          aria-label="Close"
          style={{ position: 'absolute', top: 12, right: 14, background: 'transparent', border: 'none', color: t.textMuted, fontSize: '18px', lineHeight: 1, cursor: 'pointer' }}
        >×</button>
        {children}
      </div>
    </div>
  );
}

Object.assign(window, {
  // lookups
  EFFECT_BY_NAME, INGREDIENT_BY_NAME, EFFECT_NAMES, EFFECT_OPTIONS, ingredientsWithEffect,
  // utils
  getCsrf, sortFn, cvToLabel,
  // colors
  rarityColor, dlcColor, perkColor, effectColor,
  // utils
  slugifyIngredient,
  // components
  Badge, Card, HBar, StatChip, TableHeader,
  // esv-alchemy browser scaffolding
  Section, ResultsBody, MiniStat, PotionMini, IngredientDetail, EffectDetail, SelectionReadout, DetailModal,
});
