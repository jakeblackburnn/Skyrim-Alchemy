# Analysis

Meta-experiments for analyzing Skyrim's alchemy system mechanics.

## Files

**perks.py** - Perk synergy analysis
- Tests all meaningful perk combinations (Benefactor, Physician, Poisoner)
- Identifies which ingredients benefit most from specific perks
- Shows perk sensitivity for each ingredient

**rarity.py** - Rarity tolerance analysis
- Sweeps rarity distributions from flat (all rarities equal) to steep (rare ingredients very unlikely)
- Identifies "stable" ingredients whose value doesn't depend on rarity distribution
- Identifies "volatile" ingredients whose value varies significantly with rarity

## Usage

Run from anywhere (scripts automatically change to project root):

```bash
python analysis/perks.py
python analysis/rarity.py
```

Or from project root:

```bash
python -m analysis.perks
python -m analysis.rarity
```
