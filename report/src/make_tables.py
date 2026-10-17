"""Build report tables (LaTeX booktabs) from frozen result files. Run from the project root:
    python3 src/report/make_tables.py
Outputs to report/tables/. Numbers come from the result files; the only constants are the
human-agreement and LLM-only kappas, copied from results/ai_validation/README.md (see below).
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'results'
OUT = ROOT / 'report' / 'tables'


def num(x, d=1):
    s = f'{x:.{d}f}'
    if s.startswith('-') and float(s) == 0:
        s = s[1:]
    return s.replace('-', '−')


def pval(p):
    return '< 0.001' if p < 0.001 else f'{p:.3f}' if p < 0.1 else f'{p:.2f}'


def peq(p):
    v = pval(p)
    return f'$p {v}$' if v.startswith('<') else f'$p = {v}$'


def period_label(p):
    s, e = p.split('..')
    return f'{s} to {e}'


def wrap_table(label, caption, colspec, head, body, notes, source, size=r'\small'):
    lines = [
        r'\begin{table}[htbp]', r'\centering', r'\begin{threeparttable}',
        r'\caption{\textbf{' + caption + '}}', r'\label{' + label + '}', size,
        r'\begin{tabular}{' + colspec + '}', r'\toprule', head, r'\midrule', body, r'\bottomrule',
        r'\end{tabular}', r'\begin{tablenotes}[flushleft]\footnotesize',
        r'\item \textit{Notes:} ' + notes, r'\item \textit{Source:} ' + source,
        r'\end{tablenotes}', r'\end{threeparttable}', r'\end{table}', '']
    return '\n'.join(lines)


def tab_gap():
    P = pd.read_csv(RES / 'stage1_m1' / 'm1_periods.csv')
    P = P[P.period != '2020-01..2021-06']
    ics = P[P.dv == 'ics'].set_index('period')
    rows = []
    for per, r in ics.iterrows():
        icc = P[(P.dv == 'icc') & (P.period == per)].iloc[0]
        ice = P[(P.dv == 'ice') & (P.period == per)].iloc[0]
        rows.append(' & '.join([
            period_label(per), f'{int(r.n_months)}', num(r.actual_change_vs_2019),
            num(r.mean_gap), f'[{num(r.gap_mean_pi95_lo)}, {num(r.gap_mean_pi95_hi)}]',
            num(r.explained_share, 2), num(icc.mean_gap), num(ice.mean_gap)]) + r' \\')
    head = (r' & & \multicolumn{4}{c}{Index of Consumer Sentiment (ICS)} & \multicolumn{2}{c}{Mean gap}\\' + '\n'
            r'\cmidrule(lr){3-6}\cmidrule(l){7-8}' + '\n'
            r'Period & Months & \makecell[r]{Actual\\change} & \makecell[r]{Mean\\gap} & \makecell{95\% band\\under M1} & '
            r'\makecell[r]{Explained\\share $S$} & ICC & ICE\\')
    notes = (r'Changes are relative to the 2019 average. Gap = actual − M1 out-of-sample prediction; M1 regresses each index on '
             r'real-time U-3 unemployment, PCE inflation (year over year) and real GDP growth (quarter over quarter, annualized), '
             r'fitted on 2010–2019 with month dummies. The band is the 95\% range of the period-mean prediction error under M1 '
             r'(moving-block bootstrap, block length 12, 2,000 draws); every period mean lies outside it ($p < 0.001$). '
             r'$S = 1 - \text{mean gap}/\text{actual change}$, the share of the decline since 2019 that M1 accounts for. '
             r'ICC = Current Economic Conditions; ICE = Consumer Expectations. Pandemic months (2020-01 to 2021-06) are omitted. '
             r'2026-10 is the preliminary reading.')
    tex = wrap_table('tab:gap', 'Sentiment gap relative to the economic-only model (M1), by period',
                     r'@{}l r r r c r r r@{}', head, '\n'.join(rows), notes,
                     r'\texttt{results/stage1\_m1/m1\_periods.csv}.')
    (OUT / 'tab_gap.tex').write_text(tex)


def tab_alt():
    """Alternative explanations: household pressure, estimation window, survey mode, composition."""
    H = pd.read_csv(RES / 'stage1_h1' / 'h1_models_with_exploratory.csv')
    H = H[H.dv == 'ics'].set_index('spec')
    W = pd.read_csv(RES / 'stage1_windows' / 'm1_windows.csv')
    W = W[W.dv == 'ics'].set_index('window')
    R = pd.read_csv(RES / 'stage1_m1' / 'm1_recursive_expanding.csv')
    MD = pd.read_csv(RES / 'stage1_h3' / 'h3a_mode.csv')
    CB = pd.read_csv(RES / 'stage1_h3' / 'h3b_composition_bound.csv')
    cols = ['gap_2021-07..2022-12', 'gap_2025-01..2025-12', 'gap_2026-01..2026-10']

    def row(label, r, extra=''):
        return label + ' & ' + ' & '.join(num(r[c]) for c in cols) + f' & {extra}' + r' \\'
    pv = {'M1+pce_cum36_rt': 'p_pce_cum36_rt', 'M1+mortgage30_rt_dd': 'p_mortgage30_rt_dd',
          'M1+rdpi_pc_yoy_rt': 'p_rdpi_pc_yoy_rt', 'M1+gas_price_rt_dd': 'p_gas_price_rt_dd'}
    lab = {'M1_common': 'M1, 2010-06 to 2019-12',
           'M1+pce_cum36_rt': r'\quad + 36-month cumulative PCE inflation',
           'M1+mortgage30_rt_dd': r'\quad + 30-year mortgage rate',
           'M1+rdpi_pc_yoy_rt': r'\quad + real disposable income per capita',
           'M1+gas_price_rt_dd': r'\quad + gasoline price',
           'M1+household_all': r'\quad + all four household variables'}
    L = [r'\multicolumn{5}{@{}l}{\textit{A. Household pressure (H1), pre-registered}}\\']
    for k, t in lab.items():
        r = H.loc[k]
        extra = peq(r[pv[k]]) if k in pv else ''
        if k == 'M1+household_all':
            ps = [r[c] for c in pv.values()]
            extra = f'$p = {min(ps):.2f}$ to ${max(ps):.2f}$'
        L.append(row(t, r, extra))
    L.append(r'\addlinespace')
    L.append(r'\multicolumn{5}{@{}l}{\textit{B. Estimation window (H3c)}}\\')
    L.append(row('2000-09 to 2019-12, fully real time', W.loc['2000-09..2019-12']))
    L.append(row(r'\quad + 36-month cumulative PCE inflation\textsuperscript{a}', H.loc['exploratory_2000_M1+pce_cum36'],
                 peq(H.loc['exploratory_2000_M1+pce_cum36', 'p_pce_cum36_rt'])))
    L.append(row('1978-01 to 2019-12, quasi real time', W.loc['1978-01..2019-12']))
    rr = R[(R.month >= '2025-01') & (R.month <= '2025-12')].gap.mean()
    L.append(r'Expanding window, re-estimated monthly & & ' + num(rr) + r' & & \\')
    L.append(r'\addlinespace')
    L.append(r'\multicolumn{5}{@{}l}{\textit{C. Measurement (H3a, H3b): estimated effect on the gap}}\\')
    for dv, name in [('ics', 'ICS'), ('icc', 'ICC'), ('ice', 'ICE')]:
        m = MD[(MD.dv == dv) & (MD.regressor == 'web_step') & (~MD.drop_2024_04_06) &
               (MD.window == '2023-01..2025-12')].iloc[0]
        L.append(f'Web-interview step from 2024-07, {name} & \\multicolumn{{3}}{{c}}{{{num(m.coef)} '
                 f'[{num(m.ci95_lo)}, {num(m.ci95_hi)}]}} & {peq(m.p)} \\\\')
    lo, hi = CB.dICS_if_rep_share_falls.abs().min(), CB.dICS_if_rep_share_falls.abs().max()
    L.append(f'Republican share lower by 2 to 6 points, ICS & \\multicolumn{{3}}{{c}}{{{num(-lo)} to {num(-hi)}}} & '
             f'$\\leq$ {CB.abs_share_of_gap.max() * 100:.0f}\\% of gap \\\\')
    head = (r' & \multicolumn{3}{c}{Mean ICS gap} & \\' + '\n' + r'\cmidrule(lr){2-4}' + '\n' +
            r'Specification & 2021-07 to 2022-12 & 2025 & 2026-01 to 2026-10 & Test \\')
    notes = (r'Panels A and B report the mean out-of-sample ICS gap. In Panel A the household variables are added to M1 and the model is '
             r'estimated on 2010-06 to 2019-12, the first month with real-time income data, so the baseline differs slightly from '
             r'\cref{tab:gap}. Test: HAC $p$-value of the added variable(s). Panel C, first three rows: coefficient on a step dummy for '
             r'web-only interviewing in a regression of the 2023--2025 monthly gap, with 95\% confidence interval. Last row: change in the '
             r'2025--2026 ICS if the Republican share of respondents were 2, 4 or 6 points lower, using estimated group shares '
             r'(Democrats 0.26, independents 0.54, Republicans 0.20). \textsuperscript{a}Exploratory, not pre-registered.')
    src = (r'\texttt{results/stage1\_h1/h1\_models\_with\_exploratory.csv}, \texttt{stage1\_windows/m1\_windows.csv}, '
           r'\texttt{stage1\_m1/m1\_recursive\_expanding.csv}, \texttt{stage1\_h3/h3a\_mode.csv}, '
           r'\texttt{stage1\_h3/h3b\_composition\_bound.csv}.')
    tex = wrap_table('tab:alt', 'Alternative explanations of the gap: household pressure, estimation window and measurement',
                     r'@{}l c c c l@{}', head, '\n'.join(L), notes, src, size=r'\footnotesize')
    (OUT / 'tab_alt.tex').write_text(tex)


# Human A-B agreement (all 360 items) and LLM test-set kappa for dimensions without a
# low-cost baseline. Copied from results/ai_validation/README.md, which reports
# labels/agreement_summary.csv and the scored test set.
HUMAN_KAPPA = {'relevant': 0.81, 'tone_overall': 0.79, 'price_frame': 0.93}
LLM_ONLY = [('Factual direction', 0.57, 0.72),
            ('Numeric claim', 0.79, 0.86),
            ('Perspective', 0.63, 0.78),
            ('Time frame', 0.59, 0.82),
            ('Political actor', 0.67, 0.83),
            ('Attribution direction', 0.56, 0.78),
            ('Emotional intensity', 0.56, 0.59),
            ('Definition error', 0.47, 0.77)]


def tab_ai():
    M = pd.read_csv(RES / 'stage2_r35' / 'item_metrics.csv')
    M = M[M.group == 'all']
    A = 'A: gold and LLM relevant'
    ev = {'relevant': 'gold yes/no', 'tone_overall': A, 'price_frame': A}
    others = ['lm', 'vader', 'keyword', 'tfidf_llm', 'tfidf_dev']

    def get(dim, meth):
        mm = 'keyword_all_yes' if (dim == 'relevant' and meth == 'keyword') else meth
        r = M[(M.dimension == dim) & (M.eval_set == ev[dim]) & (M.method == mm)]
        return None if r.empty else r.iloc[0]
    L = []
    names = {'relevant': 'Relevance (yes/no)', 'tone_overall': 'Tone', 'price_frame': 'Price framing'}
    for dim, nm in names.items():
        r = get(dim, 'llm')
        cells = [nm, f'{int(r.n)}', f'{HUMAN_KAPPA[dim]:.2f}', f'{r.kappa:.2f} [{r.kappa_lo:.2f}, {r.kappa_hi:.2f}]']
        for m in others:
            o = get(dim, m)
            cells.append('--' if o is None else f'{o.kappa:.2f}')
        L.append(' & '.join(cells) + r' \\')
    T = M[M.dimension.str.match(r'T\d\d_') & (M.eval_set == A)]
    tm = T.groupby('method').kappa.mean()
    L.append(' & '.join(['Topics (mean of 13)', '174', '--', f"{tm['llm']:.2f}", '--', '--', f"{tm['keyword']:.2f}",
                         f"{tm['tfidf_llm']:.2f}", f"{tm['tfidf_dev']:.2f}"]) + r' \\')
    head = (r' & & Human & & \multicolumn{2}{c}{Dictionary} & & \multicolumn{2}{c}{TF-IDF + logit} \\' + '\n' +
            r'\cmidrule(lr){5-6}\cmidrule(l){8-9}' + '\n' +
            r'Dimension & $n$ & A vs.\ B & LLM [95\% CI] & LM & VADER & Keyword & \makecell{LLM\\labels} & '
            r'\makecell{100 human\\labels} \\')
    notes = (r"Cohen's $\kappa$ against the adjudicated gold standard on the 260-item test set, scored once after the prompt was "
             r'frozen on the 100-item development set. Relevance is scored on items whose gold label is yes or no; the other dimensions '
             r'on the 174 items that both the gold standard and the LLM judge relevant. Human A vs.\ B is the agreement between the two '
             r'independent annotators on all 360 items. LM = Loughran--McDonald; dictionary thresholds were set on the development set. '
             r'The keyword rule marks every item relevant, so its relevance $\kappa$ is zero. Confidence intervals are percentile bootstrap. '
             r'Dimensions without a low-cost baseline, LLM $\kappa$ (human A vs.\ B in parentheses): '
             + '; '.join(f'{nm.lower()} {kl:.2f} ({kh:.2f})' for nm, kl, kh in LLM_ONLY) + '.')
    src = r'\texttt{results/stage2\_r35/item\_metrics.csv}; \texttt{results/ai\_validation/README.md}.'
    tex = wrap_table('tab:ai', 'Agreement with the human gold standard: LLM coding against low-cost baselines',
                     r'@{}l r c c c c c c c@{}', head, '\n'.join(L), notes, src, size=r'\footnotesize')
    (OUT / 'tab_ai.tex').write_text(tex)


def tab_forecast():
    C0 = pd.read_csv(RES / 'stage3_forecast' / 'comparisons.csv')
    C = C0[(C0.h == 1) & (C0.version == 'AR')]
    periods = [('2017-01..2026-10', '2017-01 to 2026-10'),
               ('2017-01..2026-10 excl. 2020-03..12', r'\quad excluding 2020-03 to 2020-12'),
               ('2017-2019', '2017--2019'), ('2020-2022', '2020--2022'), ('2023-2024', '2023--2024'),
               ('2025-2026', '2025--2026')]
    comps = ['M1 vs M2', 'M1c vs M3', 'M1 vs M1c']
    L = []
    for per, lab in periods:
        cells = [lab, str(int(C[(C.comparison == comps[0]) & (C.period == per)].n.iloc[0]))]
        for comp in comps:
            r = C[(C.comparison == comp) & (C.period == per)].iloc[0]
            cells += [f'{r.rmse_ratio_big_over_small:.3f}', pval(r.cw_p)]
        L.append(' & '.join(cells) + r' \\')
    NA = C0[(C0.h == 1) & (C0.version == 'no AR') & (C0.period == '2017-01..2026-10')]
    cells = [r'\textit{2017-01 to 2026-10, no AR term}', '118']
    for comp in comps:
        r = NA[NA.comparison == comp].iloc[0]
        cells += [f'{r.rmse_ratio_big_over_small:.3f}', pval(r.cw_p)]
    L.append(r'\addlinespace')
    L.append(' & '.join(cells) + r' \\')
    head = (r' & & \multicolumn{2}{c}{M2 vs.\ M1} & \multicolumn{2}{c}{M3 vs.\ M1c} & \multicolumn{2}{c}{M1c vs.\ M1} \\' + '\n' +
            r' & & \multicolumn{2}{c}{tone added} & \multicolumn{2}{c}{tone added (primary)} & '
            r'\multicolumn{2}{c}{controls added} \\' + '\n' +
            r'\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(l){7-8}' + '\n' +
            r'Evaluation period & Months & RMSE ratio & $p$ & RMSE ratio & $p$ & RMSE ratio & $p$ \\')
    notes = (r'One-step-ahead recursive forecasts of the ICS from an expanding window starting 2010-06; the first window ends 2016-12. '
             r'All rows except the last include ICS$_{t-1}$. M1: real-time unemployment, PCE inflation and GDP growth; '
             r'M1c: M1 plus the four household variables, a governing-party dummy and a pre-election dummy; M2 and M3 add national '
             r'LLM net tone for month $t-1$. RMSE ratio = larger model / smaller model, so values below 1 favour the larger model. '
             r'$p$: one-sided Clark--West test with HAC variance.')
    src = r'\texttt{results/stage3\_forecast/comparisons.csv}.'
    tex = wrap_table('tab:forecast', 'Out-of-sample forecast comparison',
                     r'@{}l r c c c c c c@{}', head, '\n'.join(L), notes, src)
    (OUT / 'tab_forecast.tex').write_text(tex)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    tab_gap()
    tab_alt()
    tab_ai()
    tab_forecast()
