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

// ── Presentational components (take `theme`) ───────────────────────────────────
function Badge({ theme, color, children, style = {} }) {
  return (
    <span style={{ fontSize: '9px', padding: '2px 7px', borderRadius: 10, background: `${color}22`, color, border: `1px solid ${color}44`, ...style }}>
      {children}
    </span>
  );
}

function Card({ theme, title, subtitle, children, style = {} }) {
  const t = theme;
  return (
    <div style={{ background: t.surface, borderRadius: 10, padding: '20px 24px', border: `1px solid ${t.border}`, ...style }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: t.text, fontFamily: 'Space Grotesk', marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: '11px', color: t.textMuted, lineHeight: 1.55 }}>{subtitle}</div>
      </div>
      {children}
    </div>
  );
}

function HBar({ theme, label, value, maxVal, color, right, sub }) {
  const t = theme;
  return (
    <div style={{ marginBottom: 7 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3, alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: '11px', color: t.text, fontFamily: 'IBM Plex Sans', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 180 }}>{label}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          {sub && <span style={{ fontSize: '9px', color: t.textMuted }}>{sub}</span>}
          <span style={{ fontSize: '11px', color, fontFamily: 'Space Grotesk', fontWeight: 600 }}>{right}</span>
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

// ── Ingredients-browser scaffolding ────────────────────────────────────────────
// Defined and exposed for the upcoming "ingredients browser" feature. NOT yet
// mounted by any tab — wiring (e.g. datasets row-click) lands in a follow-up PR.

function IngredientDetail({ theme, ingredient }) {
  const t = theme;
  if (!ingredient) return null;
  const effectNames = ingredient.effects.map(e => e.name).filter(Boolean);
  const effectSet = new Set(effectNames);
  const synergyCount = (window.__INGREDIENTS__ || [])
    .filter(i => i.name !== ingredient.name && i.effects.some(e => effectSet.has(e.name)))
    .length;
  return (
    <div style={{ background: t.surface, border: `1px solid ${t.border}`, borderRadius: 10, padding: '18px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: '16px', fontWeight: 700, color: t.text, fontFamily: 'Space Grotesk' }}>{ingredient.name}</span>
        <Badge theme={t} color={rarityColor(t, ingredient.rarity)}>{ingredient.rarity?.replace('_', ' ')}</Badge>
        {ingredient.dlc && ingredient.dlc !== 'base' && (
          <Badge theme={t} color={dlcColor(t, ingredient.dlc)}>{ingredient.dlc}</Badge>
        )}
      </div>
      <div style={{ fontSize: '11px', color: t.textMuted, marginBottom: 12 }}>
        {ingredient.value}g · {ingredient.weight} wt · synergises with {synergyCount} ingredients
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {effectNames.map(name => {
          const c = effectColor(t, EFFECT_BY_NAME.get(name)?.is_beneficial);
          return <Badge key={name} theme={t} color={c}>{name}</Badge>;
        })}
      </div>
    </div>
  );
}

function EffectDetail({ theme, effect }) {
  const t = theme;
  if (!effect) return null;
  const carriers = ingredientsWithEffect(effect.name);
  return (
    <div style={{ background: t.surface, border: `1px solid ${t.border}`, borderRadius: 10, padding: '18px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: '16px', fontWeight: 700, color: t.text, fontFamily: 'Space Grotesk' }}>{effect.name}</span>
        <Badge theme={t} color={effectColor(t, effect.is_beneficial)}>{effect.is_beneficial ? 'Beneficial' : 'Harmful'}</Badge>
      </div>
      <div style={{ fontSize: '11px', color: t.textMuted, marginBottom: 12 }}>
        base cost {effect.base_cost} · scales {effect.varies_duration ? 'duration' : 'magnitude'} · {carriers.length} ingredients
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {carriers.map(ing => (
          <Badge key={ing.name} theme={t} color={rarityColor(t, ing.rarity)}>{ing.name}</Badge>
        ))}
      </div>
    </div>
  );
}

// Dispatches to the right detail panel for a { type, value } selection.
function SelectionReadout({ theme, selection }) {
  if (!selection) return null;
  if (selection.type === 'ingredient') return <IngredientDetail theme={theme} ingredient={selection.value} />;
  if (selection.type === 'effect')     return <EffectDetail theme={theme} effect={selection.value} />;
  return null;
}

Object.assign(window, {
  // lookups
  EFFECT_BY_NAME, INGREDIENT_BY_NAME, EFFECT_NAMES, EFFECT_OPTIONS, ingredientsWithEffect,
  // utils
  getCsrf, sortFn, cvToLabel,
  // colors
  rarityColor, dlcColor, perkColor, effectColor,
  // components
  Badge, Card, HBar, StatChip, TableHeader,
  // ingredients-browser scaffolding (not yet mounted)
  IngredientDetail, EffectDetail, SelectionReadout,
});
