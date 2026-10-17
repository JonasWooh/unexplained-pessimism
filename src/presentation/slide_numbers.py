"""Every number shown on the slides or read in the script, computed from frozen files.
Run from the project root:  python3 src/presentation/slide_numbers.py
Writes presentation/build/numbers.json (value + source file for each entry).
"""
from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'results'
OUT = ROOT / 'presentation' / 'build'


def _src(p):
    return str(Path(p).relative_to(ROOT))


def compute():
    N, S = {}, {}

    def put(k, v, src):
        N[k] = v
        S[k] = _src(src)

    # Stage 1: gap by period (ICS)
    f = RES / 'stage1_m1' / 'm1_periods.csv'
    P = pd.read_csv(f).query("dv == 'ics'").set_index('period')
    put('gap_2025', P.loc['2025-01..2025-12', 'mean_gap'], f)
    put('gap_2026', P.loc['2026-01..2026-10', 'mean_gap'], f)
    put('actual_2026', P.loc['2026-01..2026-10', 'actual_mean'], f)
    put('pred_2026', P.loc['2026-01..2026-10', 'pred_mean'], f)
    post = P.loc[['2023-01..2024-12', '2025-01..2025-12', '2026-01..2026-10'], 'explained_share']
    put('explained_lo', post.min(), f)
    put('explained_hi', post.max(), f)

    # Lowest headline reading before 2020 (Michigan table, 1952 onward)
    f = ROOT / 'data' / 'raw' / 'S01' / '20261015' / 'tbmics.csv'
    t = pd.read_csv(f)
    pre = t[t.YYYY < 2020]
    r = pre.loc[pre.ICS_ALL.idxmin()]
    put('pre2020_min', float(r.ICS_ALL), f)
    put('pre2020_min_when', f'{r.Month} {int(r.YYYY)}', f)
    put('michigan_first_year', int(t.YYYY.min()), f)

    # H3: survey mode, composition, election timing, groups
    f = RES / 'stage1_h3' / 'h3a_mode.csv'
    m = pd.read_csv(f)
    m = m[(m.dv == 'icc') & (m.regressor == 'web_step') & (~m.drop_2024_04_06) & (m.status == 'pre-registered')]
    put('mode_icc_step', float(m.coef.iloc[0]), f)
    f = RES / 'stage5_mechanisms' / 'mode_gap_changes.csv'
    g = pd.read_csv(f).query("index == 'ics'").set_index('comparison')
    row = g.loc['web era: 2024-07..12 to 2026-01..08']
    put('web_gap_start', row.gap_before, f)
    put('web_gap_end', row.gap_after, f)
    f = RES / 'stage1_h3' / 'h3b_composition_bound.csv'
    put('party_bound', pd.read_csv(f).dICS_if_rep_share_falls.abs().max(), f)
    f = RES / 'stage5_mechanisms' / 'pre_election_years.csv'
    y = pd.read_csv(f).set_index('year').loc[2026]
    put('gap_2026_janapr', y.gap_jan_apr, f)
    put('gap_2026_mayoct', y.gap_may_oct, f)
    f = RES / 'stage5_mechanisms' / 'group_gaps_monthly.csv'
    gg = pd.read_csv(f)
    cols = [c for c in gg.columns if c.startswith('gap_ics_')]
    gm = gg[(gg.month >= '2025-01') & (gg.month <= '2026-08')][cols].mean()
    put('group_gap_min', gm.min(), f)
    put('group_gap_max', gm.max(), f)
    put('n_groups', len(cols), f)

    # Corpus and coding
    f = ROOT / 'corpus' / 'corpus_documentation.md'
    txt = f.read_text()
    sec = txt.split('## 2.')[1].split('## 3.')[0]
    counts = [int(x.replace(',', '')) for x in re.findall(r'\|\s*([\d,]+)\s*\|\s*$', sec, flags=re.M)]
    put('corpus_items', sum(counts), f)
    f = ROOT / 'labels' / 'ai_corpus_labels.csv'
    put('coded_items', len(pd.read_csv(f, usecols=['item_id'])), f)
    f = ROOT / 'labels' / 'gold_overview.json'
    put('gold_items', json.loads(f.read_text())['main_items'], f)

    # AI validation: tone kappa (test set) and human A vs B (all 360)
    f = RES / 'stage2_r35' / 'item_metrics.csv'
    im = pd.read_csv(f).query("dimension == 'tone_overall' and group == 'all' and eval_set == 'A: gold and LLM relevant'").set_index('method')
    for k, meth in [('kappa_llm', 'llm'), ('kappa_lm', 'lm'), ('kappa_vader', 'vader'), ('kappa_tfidf', 'tfidf_llm')]:
        put(k, im.loc[meth, 'kappa'], f)
    f = ROOT / 'labels' / 'agreement_summary.csv'
    a = pd.read_csv(f)
    a = a[(a.sheet == 'main') & (a.subset == 'all') & (a.dimension == 'tone_overall')]
    put('kappa_human', float(a.cohen_kappa.iloc[0]), f)
    f = RES / 'stage2_r37' / 'flip_rates.csv'
    fr = pd.read_csv(f).dropna(subset=['excess_flip'])
    put('swap_tests', len(fr), f)
    put('swap_sig', int((fr.p_one_sided < 0.05).sum()), f)

    # Bias benchmarks
    f = RES / 'stage2_factcal' / 'summary.csv'
    fc = pd.read_csv(f)
    fc = fc[(fc.tolerance == 'design (0.1)') & (fc.by == 'source_type') & (fc.source_type == 'national news')]
    put('fact_wrong', int(fc.wrong.iloc[0]), f)
    put('fact_checkable', int(fc.verifiable.iloc[0]), f)
    f = RES / 'stage2_bias' / 'attribution_means.csv'
    am = pd.read_csv(f).set_index('administration').blame_admin_share
    for k, adm in [('blame_obama', 'Obama 2010-2016'), ('blame_trump1', 'Trump 2017-2020'),
                   ('blame_biden', 'Biden 2021-2024'), ('blame_trump2', 'Trump 2025-')]:
        put(k, am.loc[adm], f)

    # Forecast tests
    f = RES / 'stage3_robustness' / 'variants.csv'
    v = pd.read_csv(f).query("version == 'AR'")
    for k, comp in [('m2', 'M1 vs M2'), ('m3', 'M1c vs M3')]:
        d = v[v.comparison == comp]
        put(f'{k}_n_specs', len(d), f)
        put(f'{k}_n_sig', int((d.cw_p < 0.05).sum()), f)
        put(f'{k}_p_main', float(d[d.variant == 'main'].cw_p.iloc[0]), f)
    f = RES / 'stage3_robustness' / 'magnitude.csv'
    mg = pd.read_csv(f)
    mg = mg[mg.version.str.startswith('AR') & mg.period.isin(['2025-01..2025-12', '2026-01..2026-10'])]
    put('tone_share_max', mg.share_of_gap.max(), f)
    return N, S


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    N, S = compute()
    out = {k: {'value': (float(v) if not isinstance(v, str) else v), 'source': S[k]} for k, v in N.items()}
    (OUT / 'numbers.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for k, v in N.items():
        print(f'{k:20s} {v}')
