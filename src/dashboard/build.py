"""Build the monitoring dashboard as one self-contained HTML file.

Reads only frozen project files (data/processed, features, results, labels, provenance, corpus)
and writes dashboard/index.html, which opens offline. Every number on the page comes from the
payload assembled here; the page code only formats, smooths (3-month means) and standardises it.

    python src/dashboard/build.py                 # dashboard/index.html, D3 inlined (offline)
    python src/dashboard/build.py --cdn OUT.html  # page fragment that loads D3 from cdnjs (for web hosting)
"""
import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RES = ROOT / 'results'

CUTOFF = '2026-10-16'                 # information cutoff of the frozen research round (RESULTS_OVERVIEW.md)
ELECTION = '2026-11-03'
PANDEMIC = ('2020-03', '2021-06')     # months not interpreted (FINDINGS_stage1 F1)
FIRST_OOS = '2020-01'
PROMPT_FILE = 'prompts/label_prompt_v2.md'
D3_FILE = HERE / 'vendor' / 'd3.v7.9.0.min.js'
D3_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js'

GROUPS = {  # media_monthly.csv group -> label, sources, unit
    'national': ('National news', 'NYT + Guardian', 'headline, abstract and lead'),
    'mc_national': ('Other national outlets', 'Media Cloud national collection', 'headline and lead'),
    'local': ('Local news', 'Media Cloud state and local collections', 'headline and lead'),
    'reddit': ('Reddit', 'r/economy, r/Economics, r/personalfinance', 'post title and body'),
    'youtube': ('YouTube comments', 'news-channel videos, top-level comments', 'comment'),
}
TOPICS = ['Layoffs, unemployment up', 'Hiring, job growth', 'Prices rising', 'Inflation easing', 'Economic growth',
          'Recession risk', 'Interest rates, borrowing', 'Housing costs', 'Gas prices', 'Food prices',
          'Tariffs, trade', 'Stock market', 'Other']
TOPIC_COLS = ['topic_layoffs_unemployment_up', 'topic_hiring_jobs_growth', 'topic_prices_rising', 'topic_inflation_easing',
              'topic_economic_growth', 'topic_recession_risk', 'topic_interest_rates_borrowing', 'topic_housing_costs',
              'topic_gas_prices', 'topic_food_prices', 'topic_tariffs_trade', 'topic_stock_market', 'topic_other']
LABEL_TOPIC_COLS = ['T01_layoffs_unemployment_up', 'T02_hiring_jobs_growth', 'T03_prices_rising', 'T04_inflation_easing',
                    'T05_economic_growth', 'T06_recession_risk', 'T07_interest_rates_borrowing', 'T08_housing_costs',
                    'T09_gas_prices', 'T10_food_prices', 'T11_tariffs_trade', 'T12_stock_market', 'T13_other']
DEMO = {'y13': ('Income', 'Bottom third'), 'y23': ('Income', 'Middle third'), 'y33': ('Income', 'Top third'),
        'a1834': ('Age', '18–34'), 'a3554': ('Age', '35–54'), 'a5597': ('Age', '55+'),
        'w': ('Region', 'West'), 'nc': ('Region', 'North Central'), 'ne': ('Region', 'Northeast'), 's': ('Region', 'South'),
        'ehs': ('Education', 'High school or less'), 'esc': ('Education', 'Some college'), 'ecd': ('Education', 'College degree')}
DEMO_PERIODS = ('2021-07..2022-12', '2025-01..2026-08')
DIM_LABEL = {'relevant': 'Relevance', 'tone_overall': 'Tone', 'fact_direction': 'Factual direction',
             'emotional_intensity': 'Emotional intensity', 'price_frame': 'Price framing', 'perspective': 'Perspective',
             'time_frame': 'Time frame', 'numeric_claim': 'Numeric claim', 'definition_error': 'Definition error',
             'actor_1': 'Political actor', 'direction_1': 'Attribution direction', 'admin_attribution': 'Blame or credit to administration',
             'topics': 'Topics (any change)'}
SPEC_LABEL = {'main': 'Main specification', 'DV ICC': 'Current conditions (ICC)', 'DV ICE': 'Expectations (ICE)',
              'cutoff = Michigan preliminary release': 'Preliminary-release cutoff',
              'GDP yoy': 'GDP growth year on year', 'first differences': 'First differences',
              'excluding 2020-03..2020-12': 'Drop March–December 2020', 'web-mode step dummy': 'Web-mode step dummy',
              'drop 2024-04..06': 'Drop the mixed-mode months', 'media: tone 3-month mean': 'Tone, 3-month mean',
              'media: net_fact': 'Net factual direction', 'media: share_negative': 'Share negative',
              'media: SF Fed index': 'SF Fed news sentiment', 'media: full-frame LM dictionary': 'Dictionary tone, all items',
              'media: NYT only net_tone': 'NYT only',
              'media: media months 2026-01 and 2026-10 missing': 'Drop Jan and Oct 2026 news',
              'media: EPU (real-time)': 'Policy uncertainty index (EPU)', 'tone lag 1-3 by BIC': 'Tone lags 1–3 chosen by BIC',
              'month dummies excluded': 'No calendar-month dummies',
              'excess tone (residual on U, pi, g, H and month t-1 news, per window)': 'Tone net of fundamentals'}
RELEASES = [  # release_calendar.csv indicator -> (label, agency); only the releases the update plan tracks
    ('Michigan ICS/ICC/ICE', None, 'Michigan consumer sentiment', 'University of Michigan'),
    ('GDP', None, 'GDP', 'BEA'),
    ('Personal Income and Outlays', None, 'Personal income and outlays (PCE prices)', 'BEA'),
    ('UNRATE', 'source_release_schedule', 'Employment Situation (unemployment rate)', 'BLS'),
    ('CPIUFDSL', 'source_release_schedule', 'Consumer Price Index', 'BLS'),
]


def rd(x, k=4):
    """JSON-safe rounding; NaN and None become null."""
    if x is None:
        return None
    try:
        if isinstance(x, str):
            return x
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(x, (bool,)):
        return bool(x)
    v = float(x)
    if math.isinf(v):
        return None
    return round(v, k)


def s(x):
    return None if x is None or (not isinstance(x, str) and pd.isna(x)) else str(x)


def align(df, months, col, k=4, key='month'):
    m = dict(zip(df[key], df[col]))
    return [rd(m.get(t), k) if not isinstance(m.get(t), str) else m.get(t) for t in months]


def month_range(a, b):
    return [p.strftime('%Y-%m') for p in pd.period_range(a, b, freq='M')]


# ---------------------------------------------------------------- confidence and the M1 gap
def confidence(months):
    g = pd.read_csv(RES / 'stage1_m1' / 'm1_gap_monthly.csv')
    out = {}
    for dv in ('ics', 'icc', 'ice'):
        d = g[g.dv == dv].set_index('month').reindex(months)
        oos = ~d.in_sample.astype('boolean').fillna(False).astype(bool)
        rec = {'actual': [rd(v, 2) for v in d[dv]], 'pred': [rd(v, 3) for v in d.pred], 'gap': [rd(v, 3) for v in d.gap],
               'in_sample': [bool(v) for v in ~oos]}
        for lv in ('80', '95'):
            for side in ('lo', 'hi'):
                col = f'pi{lv}_{side}_mbb'
                rec[f'pi{lv}{side}'] = [rd(v, 3) if o else None for v, o in zip(d[col], oos)]
        out[dv] = rec
    P = pd.read_csv(RES / 'stage1_m1' / 'm1_periods.csv')
    periods = {}
    for dv in ('ics', 'icc', 'ice'):
        periods[dv] = [{'period': r.period, 'start': r.period.split('..')[0], 'end': r.period.split('..')[1],
                        'n': int(r.n_months), 'actual': rd(r.actual_mean, 2), 'pred': rd(r.pred_mean, 2),
                        'gap': rd(r.mean_gap, 2), 'lo95': rd(r.gap_mean_pi95_lo, 2), 'hi95': rd(r.gap_mean_pi95_hi, 2),
                        'p': rd(r.gap_mean_p_two_sided, 3), 'actual_change': rd(r.actual_change_vs_2019, 2),
                        'explained': rd(r.explained_share, 3)}
                       for r in P[P.dv == dv].itertuples()]
    fit = pd.read_csv(RES / 'stage1_m1' / 'm1_fit.csv')
    W = pd.read_csv(RES / 'stage1_windows' / 'm1_windows.csv')
    W = W[W.dv == 'ics']
    windows = [{'window': r['window'], 'gap2122': rd(r['gap_2021-07..2022-12'], 2), 'gap2025': rd(r['gap_2025-01..2025-12'], 2),
                'gap2026': rd(r['gap_2026-01..2026-10'], 2)} for _, r in W.iterrows()]
    return out, periods, windows


def econ_inputs(months):
    e = pd.read_csv(ROOT / 'data' / 'processed' / 'econ_monthly_realtime.csv').set_index('month').reindex(months)
    cols = {
        'origin': 'origin_date', 'status': 'ics_status', 'mich_prelim': 'mich_prelim_release_date',
        'mich_final': 'mich_final_release_date', 'web': 'mode_web_share',
        'u': 'unrate_rt', 'u_ref': 'unrate_ref', 'u_rel': 'unrate_release_date',
        'pce': 'pce_yoy_rt', 'pce_ref': 'pce_ref', 'pce_rel': 'pce_release_date',
        'gdp': 'gdp_qoq_saar_rt', 'gdp_ref': 'gdp_ref_quarter', 'gdp_rel': 'gdp_release_date', 'gdp_est': 'gdp_release_number',
        'pce_cum': 'pce_cum_since_2021_01_rt', 'mort': 'mortgage30_rt', 'gas': 'gas_price_rt', 'u6': 'u6rate_rt',
        'rdpi': 'rdpi_pc_yoy_rt',
    }
    out = {}
    for k, c in cols.items():
        out[k] = [s(v) if d == object or isinstance(v, str) else rd(v, 3)
                  for v, d in zip(e[c], [e[c].dtype] * len(e))]
    web = e.mode_web_share
    first_mixed = web[web > 0].index.min()
    first_web = web[web >= 1].index.min()
    return out, {'first_mixed': first_mixed, 'first_web': first_web}


# ---------------------------------------------------------------- media measures
def media(months):
    m = pd.read_csv(ROOT / 'features' / 'media_monthly.csv')
    fields = ['n_coded', 'n_relevant', 'net_tone', 'share_negative', 'share_positive', 'net_fact', 'emotional_intensity_mean',
              'price_level_share_of_priced', 'price_frame_share', 'household_share', 'blame_admin_share',
              'credit_admin_share', 'fed_mention_share', 'est_relevant_items'] + TOPIC_COLS
    out = {}
    for gk, (label, src, unit) in GROUPS.items():
        d = m[m.group == gk].set_index('month').reindex(months)
        rec = {'label': label, 'sources': src, 'unit': unit,
               'first': m[m.group == gk].month.min(), 'last': m[m.group == gk].month.max()}
        for f in fields:
            rec[f] = [rd(v, 4) for v in d[f]]
        rec['low_n'] = [bool(v) if not pd.isna(v) else None for v in d.low_n_flag]
        rec['note'] = [s(v) for v in d.source_gap]
        out[gk] = rec
    sf = pd.read_csv(ROOT / 'features' / 'sffed_news_sentiment_monthly.csv')
    sffed = align(sf, months, 'sffed_news_sentiment_mean', 4)
    return out, sffed


def headlines():
    """Coded news items (national, other national, local) with their LLM labels, for the month inspector.
    Social-media items are summarised only in aggregates and never shown as text."""
    lab = pd.read_csv(ROOT / 'labels' / 'ai_corpus_labels.csv')
    lab = lab[lab.group.isin(['national', 'mc_national', 'local'])]
    it = pd.read_parquet(ROOT / 'corpus' / 'items.parquet', columns=['item_id', 'outlet_name', 'title', 'url'])
    d = lab.merge(it, on='item_id', how='left')
    d = d.sort_values(['month', 'date', 'item_id'])
    tone = {'positive': 'p', 'negative': 'n', 'neutral': 'u', 'mixed': 'm'}
    fact = {'good': 'g', 'bad': 'b', 'mixed': 'm', 'neutral': 'u', 'no_fact': '-'}
    rows = {}
    for r in d.itertuples():
        title = re.sub(r'\s+', ' ', str(r.title or '')).strip()
        if len(title) > 170:
            title = title[:167].rstrip() + '…'
        topics = [i for i, c in enumerate(LABEL_TOPIC_COLS) if getattr(r, c) == 1]
        actor = None
        if isinstance(r.actor_1, str) and r.actor_1 not in ('none', ''):
            actor = r.actor_1 + (('/' + r.direction_1) if isinstance(r.direction_1, str) else '')
        rows.setdefault(r.month, []).append([
            r.group, str(r.date)[:10], s(r.outlet_name) or r.source, title, s(r.url),
            {'yes': 1, 'no': 0}.get(r.relevant, -1), tone.get(r.tone_overall), fact.get(r.fact_direction), topics, actor])
    return rows


def factcal():
    c = pd.read_csv(RES / 'stage2_factcal' / 'claims.csv')
    news = c[c.group == 'national']
    claims = [[r.date, r.source, s(r.fragment), r.indicator, rd(r.claim_value, 3), rd(r.official_value_at_pub, 3),
               r.category, s(r.unverifiable_reason)] for r in news.sort_values('date').itertuples()]
    S = pd.read_csv(RES / 'stage2_factcal' / 'summary.csv')
    S = S[(S.tolerance == 'design (0.1)') & (S.by == 'source_type')]
    by_source = [{'source': r.source_type, 'correct': int(r.correct + r.correct_within_rounding), 'wrong': int(r.wrong),
                  'unverifiable': int(r.unverifiable), 'verifiable': int(r.verifiable), 'error_rate': rd(r.error_rate, 4)}
                 for r in S.itertuples()]
    social = c[c.group != 'national'].category.value_counts().to_dict()
    return {'claims': claims, 'by_source': by_source, 'social_categories': {k: int(v) for k, v in social.items()}}


# ---------------------------------------------------------------- measurement quality
def ai_quality():
    T = pd.read_csv(RES / 'ai_validation' / 'codex__v2_isolated_r1_test_metrics.csv')
    T = T[T.group == 'all'].set_index('dimension')
    H = pd.read_csv(ROOT / 'labels' / 'agreement_summary.csv')
    H = H[(H.sheet == 'main') & (H.subset == 'all')].set_index('dimension')
    M = pd.read_csv(RES / 'stage2_r35' / 'item_metrics.csv')
    M = M[M.group == 'all']
    A = 'A: gold and LLM relevant'
    ev = {'relevant': 'gold yes/no', 'tone_overall': A, 'price_frame': A}
    summ = json.loads((RES / 'ai_validation' / 'codex__v2_isolated_r1_test_summary.json').read_text())
    dims = []
    for dim in ['relevant', 'tone_overall', 'price_frame', 'numeric_claim', 'actor_1', 'perspective', 'time_frame',
                'fact_direction', 'emotional_intensity', 'direction_1', 'definition_error']:
        r = T.loc[dim]
        rec = {'dim': dim, 'label': DIM_LABEL[dim], 'n': int(r.n), 'llm': rd(r.cohen_kappa, 3),
               'human': rd(H.loc[dim].cohen_kappa, 3), 'human_n': int(H.loc[dim].n), 'f1': rd(r.macro_f1, 3),
               'self_consistency': rd(summ['self_consistency'].get(dim), 3)}
        if dim in ev:
            row = M[(M.dimension == dim) & (M.eval_set == ev[dim])]
            ll = row[row.method == 'llm'].iloc[0]
            rec['llm_ci'] = [rd(ll.kappa_lo, 3), rd(ll.kappa_hi, 3)]
            base = {}
            for meth, key in [('lm', 'Loughran–McDonald'), ('vader', 'VADER'), ('keyword', 'Keyword rule'),
                              ('keyword_all_yes', 'Keyword rule'), ('tfidf_llm', 'TF-IDF, LLM labels'),
                              ('tfidf_dev', 'TF-IDF, 100 human labels')]:
                b = row[row.method == meth]
                if len(b):
                    base[key] = rd(b.iloc[0].kappa, 3)
            rec['baselines'] = base
        dims.append(rec)
    topics_T = M[M.dimension.str.match(r'T\d\d_') & (M.eval_set == A)].groupby('method').kappa.mean()
    topics = {'llm': rd(topics_T['llm'], 3), 'Keyword rule': rd(topics_T['keyword'], 3),
              'TF-IDF, LLM labels': rd(topics_T['tfidf_llm'], 3), 'TF-IDF, 100 human labels': rd(topics_T['tfidf_dev'], 3)}
    F = pd.read_csv(RES / 'stage2_r37' / 'flip_rates.csv')
    F = F[F.version != 'O2']
    vname = {'S': 'Names and parties swapped', 'F': 'Labelled as Fox News', 'M': 'Labelled as MSNBC'}
    F0 = pd.read_csv(RES / 'stage2_r37' / 'flip_rates.csv')
    base = F0[F0.version == 'O2'].set_index('dimension').flip_rate_vs_O1
    swap = [{'dim': r.dimension, 'label': DIM_LABEL[r.dimension], 'version': vname[r.version],
             'excess': rd(r.excess_flip, 4), 'lo': rd(r.excess_lo, 4), 'hi': rd(r.excess_hi, 4), 'p': rd(r.p_one_sided, 4),
             'base': rd(base[r.dimension], 4)} for r in F.itertuples()]
    R = pd.read_csv(RES / 'stage2_reliability' / 'reliability.csv')
    R = R[(R['index'] == 'net_tone') & (R.variance == 'with finite-population correction')].iloc[0]
    C = pd.read_csv(RES / 'stage2_dictindex' / 'correlations.csv')
    dict_r = C[(C.a == 'dict_net_tone_lm (full frame)') & (C.b == 'sffed') & (C['transform'] == 'level')].pearson.iloc[0]
    return {'test_n': int(summ['items_returned']), 'evidence_quotes': summ['evidence']['quotes'],
            'evidence_verbatim': summ['evidence']['verbatim'], 'repeat_items': summ['self_consistency_items'],
            'dims': dims, 'topics': topics, 'swap': swap,
            'reliability': rd(R.reliability, 3), 'reliability_3m': rd(R.reliability_3m, 3),
            'r_sffed': rd(R.r_sffed, 3), 'r_sffed_3m': rd(R.r_sffed_3m, 3), 'r_sffed_dict_full': rd(dict_r, 3)}


def coverage():
    st = json.loads((ROOT / 'corpus' / 'items_stats.json').read_text())
    lab = pd.read_csv(ROOT / 'labels' / 'ai_corpus_labels.csv')
    srcmap = {'NYT': 'NYT', 'Guardian': 'Guardian', 'MediaCloud_National': 'MediaCloud_National',
              'MediaCloud_Local': 'MediaCloud_Local', 'Reddit': 'Reddit', 'YouTube': 'YouTube'}
    coded = lab.groupby('source').size().to_dict()
    rel = lab[lab.relevant == 'yes'].groupby('source').size().to_dict()
    label = {'NYT': 'New York Times', 'Guardian': 'Guardian (US economy)', 'MediaCloud_National': 'Other national (Media Cloud)',
             'MediaCloud_Local': 'Local news (Media Cloud)', 'Reddit': 'Reddit', 'YouTube': 'YouTube comments'}
    rows = []
    for k in ['NYT', 'Guardian', 'MediaCloud_National', 'MediaCloud_Local', 'Reddit', 'YouTube']:
        kk = srcmap[k]
        rows.append({'source': label[k], 'frame': int(st['by_source'][k]), 'coded': int(coded.get(kk, 0)),
                     'relevant': int(rel.get(kk, 0))})
    return {'rows': rows, 'total_frame': int(st['rows']), 'total_coded': int(len(lab)),
            'total_relevant': int((lab.relevant == 'yes').sum()), 'duplicates': int(st['duplicates']),
            'reposts': int(st['reposts'])}


# ---------------------------------------------------------------- groups, party, events
def party(months):
    p = pd.read_csv(RES / 'stage1_h3' / 'h3b_party_monthly.csv')
    out = {k: align(p, months, f'dev_{k}', 2) for k in ('dem', 'ind', 'rep')}
    P = pd.read_csv(RES / 'stage1_h3' / 'h3b_party_periods.csv')
    out['periods'] = [{'period': r.period, 'dem': rd(r.dev_dem, 2), 'ind': rd(r.dev_ind, 2), 'rep': rd(r.dev_rep, 2)}
                      for r in P.itertuples()]
    B = pd.read_csv(RES / 'stage1_h3' / 'h3b_composition_bound.csv')
    out['composition_max'] = rd(B.dICS_if_rep_share_falls.abs().max(), 2)
    return out


def demo_groups():
    g = pd.read_csv(RES / 'stage5_mechanisms' / 'group_gaps_monthly.csv')
    out = []
    for k, (dim, lab) in DEMO.items():
        vals = []
        for per in DEMO_PERIODS:
            a, b = per.split('..')
            x = g[(g.month >= a) & (g.month <= b)][f'gap_ics_{k}']
            vals.append(rd(x.mean(), 2))
        out.append({'key': k, 'dim': dim, 'label': lab, 'p1': vals[0], 'p2': vals[1]})
    return {'periods': list(DEMO_PERIODS), 'rows': out}


def events():
    e = pd.read_csv(ROOT / 'provenance' / 'events.csv')
    cat = {'monetary_policy_statement': 'fomc', 'shutdown_start': 'shutdown', 'shutdown_end': 'shutdown',
           'shutdown_reopening_notice': 'shutdown', 'shutdown_lapse': 'shutdown', 'tariff_announcement': 'trade',
           'trade_agreement_signed': 'trade', 'trade_agreement_effective': 'trade', 'pandemic': 'other',
           'business_cycle_announcement': 'other', 'bank_resolution': 'other', 'financial_policy': 'other'}
    out = [{'date': r.date, 'label': r.event, 'kind': cat.get(r.category, 'other'), 'url': s(r.source_url)}
           for r in e.itertuples()]
    el = pd.read_csv(ROOT / 'provenance' / 'political_elections.csv')
    for r in el.itertuples():
        out.append({'date': r.date, 'label': r.event + (' (scheduled)' if 'scheduled' in r.status else ''),
                    'kind': 'election', 'url': s(r.source_url)})
    return sorted(out, key=lambda x: x['date'])


def releases():
    c = pd.read_csv(ROOT / 'provenance' / 'release_calendar.csv')
    out = []
    for ind, rtype, label, agency in RELEASES:
        d = c[(c.indicator == ind) & (c.release_date >= '2026-10-01') & (c.release_date <= '2026-12-31')]
        if rtype:
            d = d[d.release_type == rtype]
        for r in d.drop_duplicates('release_date').itertuples():
            ref = s(r.reference_period)
            kind = s(r.release_type) if r.release_type not in ('source_release_schedule', 'monthly') else None
            out.append({'date': r.release_date, 'label': label, 'agency': agency, 'ref': ref, 'kind': kind,
                        'url': s(r.source_url) if 'api.stlouisfed' not in str(r.source_url) else
                        'https://fred.stlouisfed.org/releases/calendar'})
    return sorted(out, key=lambda x: (x['date'], x['label']))


# ---------------------------------------------------------------- forecasting and falsification
def forecasting():
    V = pd.read_csv(RES / 'stage3_robustness' / 'variants.csv')
    V = V[V.version == 'AR']
    specs = []
    for name in V.variant.unique():
        d = V[V.variant == name]
        a = d[d.comparison == 'M1 vs M2']
        b = d[d.comparison == 'M1c vs M3']
        if a.empty or b.empty:
            continue
        specs.append({'key': name, 'label': SPEC_LABEL.get(name, name), 'p_m2': rd(a.cw_p.iloc[0], 4),
                      'p_m3': rd(b.cw_p.iloc[0], 4), 'ratio_m2': rd(a.rmse_ratio.iloc[0], 4),
                      'ratio_m3': rd(b.rmse_ratio.iloc[0], 4)})
    L = pd.read_csv(RES / 'stage4_timing' / 'local_projections.csv')
    L = L[L.spec == L.spec.iloc[0]]
    lp = [{'dir': r.direction, 'h': str(r.horizon), 'coef': rd(r.coef, 4), 'se': rd(r.se, 4), 'p': rd(r.p_two, 4),
           'p1': rd(r.p_one_positive, 4)}
          for r in L.itertuples()]
    C = pd.read_csv(RES / 'stage3_forecast' / 'comparisons.csv')
    C = C[(C.h == 1) & (C.period == '2017-01..2026-10')]
    comp = [{'comparison': r.comparison, 'version': r.version, 'n': int(r.n), 'rmse_small': rd(r.rmse_small, 3),
             'rmse_big': rd(r.rmse_big, 3), 'ratio': rd(r.rmse_ratio_big_over_small, 4), 'p': rd(r.cw_p, 4)}
            for r in C.itertuples()]
    Mg = pd.read_csv(RES / 'stage3_robustness' / 'magnitude.csv')
    Mg = Mg[Mg.version.str.startswith('AR')]
    share = rd(Mg.share_of_gap.abs().max(), 3)
    return {'specs': specs, 'lp': lp, 'lp_spec': L.spec.iloc[0], 'comparisons': comp, 'tone_share_max': share}


def falsification(fc, conf_periods):
    E = pd.read_csv(RES / 'stage4_timing' / 'excess_tone_since_2021.csv')
    e_all = E[(E.fit == 'fit 2010-01..2019-12') & (E.period == '2021-01..2026-10')].iloc[0]
    e_25 = E[(E.fit == 'fit 2010-01..2019-12') & (E.period == '2025-01..2026-10')].iloc[0]
    main = next(x for x in fc['specs'] if x['key'] == 'main')
    n_sig = sum(1 for x in fc['specs'] if x['p_m3'] is not None and x['p_m3'] < 0.05)
    lp_avg = [x for x in fc['lp'] if x['h'].startswith('avg')]
    R = pd.read_csv(RES / 'stage4_timing' / 'recall_unique_r2.csv').iloc[0]
    F = pd.read_csv(RES / 'stage2_r37' / 'flip_rates.csv')
    F = F[F.version != 'O2']
    n_flip_sig = int((F.p_one_sided < 0.05).sum())
    mode = pd.read_csv(RES / 'stage1_h3' / 'h3a_mode.csv')
    mode = mode[(mode.dv == 'icc') & (mode.regressor == 'web_step') & (mode.status == 'pre-registered') & (~mode.drop_2024_04_06)]
    comp = pd.read_csv(RES / 'stage1_h3' / 'h3b_composition_bound.csv').dICS_if_rep_share_falls.abs().max()

    def f(x, k=2, sign=False):
        t = f'{x:+.{k}f}' if sign else f'{x:.{k}f}'
        return t.replace('-', '−')
    items = [
        (1, 'Tone is explained by fundamentals',
         f"Residual tone since 2021 {f(e_all.mean_residual, sign=True)} (p = {e_all.p:.3f}), less negative than fundamentals predict; "
         f"2025–26 {f(e_25.mean_residual, sign=True)} (p = {e_25.p:.2f}).", False, 'Not triggered; the sign runs against media bias'),
        (2, 'No out-of-sample gain',
         f"M3 vs M1c: p = {main['p_m3']:.2f}; {n_sig} of {len(fc['specs'])} specifications significant at 5%.", True, 'Triggered'),
        (3, 'Sentiment leads media',
         f"Average 0–6 month response, one-sided: p = {lp_avg[0]['p1']:.2f} forward, p = {lp_avg[1]['p1']:.2f} reverse.", False,
         'Not triggered; media do not lead either'),
        (4, 'Real pressures explain the gap', 'Household-stress variables leave the gap unchanged but are not identified in 2010–2019.',
         False, 'Not triggered (low power)'),
        (5, 'Gap is measurement or partisanship',
         f"Survey mode shifts ICC by {f(abs(mode.coef.iloc[0]), 1)} points; party composition at most {f(comp, 1)} points.", False,
         'Not triggered'),
        (6, 'Recall follows the economy',
         f"Unique R² for unfavourable news heard: fundamentals {R.unique_B:.2f}, tone {R.unique_A:.2f}.", True, 'Triggered'),
        (7, 'No difference across groups', 'Party and age gaps differ, and they differ along partisan lines.', False, 'Not triggered'),
        (8, 'Measurement is unstable',
         f"{n_flip_sig} of {len(F)} excess flip rates significant in the name and outlet swap test.", False, 'Not triggered'),
    ]
    return [{'n': n, 'criterion': c, 'result': r, 'triggered': t, 'verdict': v} for n, c, r, t, v in items]


def mode_effects():
    m = pd.read_csv(RES / 'stage1_h3' / 'h3a_mode.csv')
    m = m[(m.regressor == 'web_step') & (m.status == 'pre-registered') & (~m.drop_2024_04_06)]
    return {r.dv: {'coef': rd(r.coef, 3), 'p': rd(r.p, 4), 'lo': rd(r.ci95_lo, 3), 'hi': rd(r.ci95_hi, 3), 'window': r.window}
            for r in m.itertuples()}


def bias():
    A = pd.read_csv(RES / 'stage2_bias' / 'attribution_means.csv')
    order = ['Obama 2010-2016', 'Trump 2017-2020', 'Biden 2021-2024', 'Trump 2025-']
    A = A.set_index('administration').loc[order]
    span = {'Obama 2010-2016': ('2010-01', '2016-12'), 'Trump 2017-2020': ('2017-01', '2020-12'),
            'Biden 2021-2024': ('2021-01', '2024-12'), 'Trump 2025-': ('2025-01', None)}
    label = {'Obama 2010-2016': 'Obama 2010–16', 'Trump 2017-2020': 'Trump 2017–20', 'Biden 2021-2024': 'Biden 2021–24',
             'Trump 2025-': 'Trump 2025–'}
    return [{'admin': label[k], 'start': span[k][0], 'end': span[k][1], 'blame': rd(r.blame_admin_share, 3),
             'credit': rd(r.credit_admin_share, 3), 'tone': rd(r.net_tone, 3)} for k, r in A.iterrows()]


# ---------------------------------------------------------------- meta
def meta(months, conf, econ, med, mode):
    last_ics = max(i for i, v in enumerate(conf['ics']['actual']) if v is not None)
    runs = pd.read_csv(ROOT / 'labels' / 'ai' / 'run_log.csv')
    sha = runs[runs.prompt_file.str.endswith(PROMPT_FILE.split('/')[-1])].prompt_sha256.unique()
    sha = sha[0] if len(sha) == 1 else None   # archived hash of the frozen prompt used in every v2 run
    decl = json.loads((ROOT / 'labels' / 'ai' / 'model_declaration.json').read_text())

    def last(key, ref, rel):
        idx = max(i for i, v in enumerate(econ[key]) if v is not None)
        return {'value': econ[key][idx], 'ref': econ[ref][idx], 'released': econ[rel][idx], 'month': months[idx]}
    nat = med['national']
    return {
        'cutoff': CUTOFF, 'election': ELECTION, 'pandemic': list(PANDEMIC), 'first_oos': FIRST_OOS,
        'months': [months[0], months[-1]], 'mode': mode,
        'michigan': {'month': months[last_ics], 'value': conf['ics']['actual'][last_ics], 'status': econ['status'][last_ics],
                     'released': econ['mich_prelim'][last_ics] if econ['status'][last_ics] != 'final' else econ['mich_final'][last_ics],
                     'final_due': econ['mich_final'][last_ics]},
        'unemployment': last('u', 'u_ref', 'u_rel'), 'pce': last('pce', 'pce_ref', 'pce_rel'),
        'gdp': last('gdp', 'gdp_ref', 'gdp_rel'),
        'media_last': nat['last'], 'media_note': next((n for n in reversed(nat['note']) if n), None),
        'prompt': PROMPT_FILE.split('/')[-1], 'prompt_sha256': sha,
        'model': decl['model'], 'effort': decl['reasoning_effort'],
        'repo': '[GitHub repository URL]',
    }


def build_payload():
    econ_df = pd.read_csv(ROOT / 'data' / 'processed' / 'econ_monthly_realtime.csv')
    months = list(econ_df.month)
    conf, periods, windows = confidence(months)
    econ, mode = econ_inputs(months)
    med, sffed = media(months)
    fc = forecasting()
    P = {
        'months': months, 'conf': conf, 'periods': periods, 'econ': econ, 'media': med, 'sffed': sffed,
        'topics': TOPICS, 'party': party(months), 'demo': demo_groups(), 'events': events(), 'releases': releases(),
        'factcal': factcal(), 'ai': ai_quality(), 'coverage': coverage(), 'forecast': fc,
        'falsification': falsification(fc, periods), 'bias': bias(), 'headlines': headlines(),
        'windows': windows, 'mode_effects': mode_effects(),
    }
    P['meta'] = meta(months, conf, econ, med, mode)
    return P


def render(payload, cdn_fragment=False):
    tpl = (HERE / 'template.html').read_text()
    css = (HERE / 'style.css').read_text()
    js = (HERE / 'app.js').read_text()
    data = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    if cdn_fragment:
        d3_tag = f'<script src="{D3_CDN}"></script>'
    else:
        d3_tag = '<script>/* D3 v7.9.0, ISC License, Copyright 2010-2023 Mike Bostock */\n' + D3_FILE.read_text() + '</script>'
    html = (tpl.replace('/*__CSS__*/', css).replace('<!--__D3__-->', d3_tag)
            .replace('/*__DATA__*/', 'window.PGM_DATA = ' + data + ';').replace('/*__APP__*/', js))
    if cdn_fragment:  # the web host supplies <!doctype html><html><head><body>
        html = re.sub(r'(?s)^.*?<!--__FRAGMENT_START__-->', '', html)
        html = re.sub(r'(?s)<!--__FRAGMENT_END__-->.*$', '', html)
        html = re.sub(r'</head>\s*<body>', '', html, count=1)
    else:
        html = html.replace('<!--__FRAGMENT_START__-->', '').replace('<!--__FRAGMENT_END__-->', '')
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cdn', metavar='OUT', help='write a web fragment that loads D3 from cdnjs instead')
    ap.add_argument('--json', metavar='OUT', help='also write the payload as JSON')
    a = ap.parse_args()
    payload = build_payload()
    if a.json:
        Path(a.json).write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    if a.cdn:
        Path(a.cdn).write_text(render(payload, cdn_fragment=True))
        print('wrote', a.cdn)
    else:
        out = ROOT / 'dashboard' / 'index.html'
        out.parent.mkdir(exist_ok=True)
        out.write_text(render(payload))
        print('wrote', out, f'{out.stat().st_size / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
