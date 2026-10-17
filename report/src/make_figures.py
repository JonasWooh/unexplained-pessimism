"""Build report figures from frozen result files. Run from the project root:
    python3 src/report/make_figures.py
Outputs vector PDFs to report/figures/.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle as S

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'results'
OUT = ROOT / 'report' / 'figures'

PANDEMIC = ('2020-03', '2021-06')   # months not interpreted (FINDINGS_stage1 F1)
WEB_ONLY = '2024-07'                # first web-only Michigan month (stage1_h3)


def fig_gap():
    g = pd.read_csv(RES / 'stage1_m1' / 'm1_gap_monthly.csv')
    g = g[g.dv == 'ics'].copy()
    g['date'] = pd.to_datetime(g.month)
    pand = (g.month >= PANDEMIC[0]) & (g.month <= PANDEMIC[1])
    oos = ~g.in_sample.astype(bool)
    show = oos & ~pand
    pre = oos & (g.month < PANDEMIC[0])
    post = oos & (g.month > PANDEMIC[1])

    fig, (a, b) = plt.subplots(2, 1, figsize=(S.TEXT_WIDTH_IN, 3.35), sharex=True,
                               gridspec_kw={'height_ratios': [1.65, 1], 'hspace': 0.16})
    p0, p1 = pd.Timestamp(PANDEMIC[0] + '-01'), pd.Timestamp(PANDEMIC[1] + '-01') + pd.offsets.MonthEnd(0)
    for ax in (a, b):
        ax.axvspan(p0, p1, color=S.SHADE, lw=0, zorder=0)
        ax.axvline(pd.Timestamp('2020-01-01'), color=S.MUTED, lw=0.6, ls=(0, (2, 2)), zorder=1)

    # (a) levels
    for m in (pre, post):
        d = g[m]
        a.fill_between(d.date, d.pi95_lo_mbb, d.pi95_hi_mbb, color=S.BLUE, alpha=0.16, lw=0, zorder=2)
    fit = g[~oos]
    a.plot(fit.date, fit.pred, color=S.BLUE, lw=1.0, ls=(0, (4, 2)), zorder=3)
    for m in (pre, post):
        d = g[m]
        a.plot(d.date, d.pred, color=S.BLUE, lw=1.4, zorder=3)
    a.plot(g.date, g.ics, color=S.INK, lw=1.3, zorder=4)
    a.set_ylim(40, 112)
    a.set_ylabel('Index (1966Q1 = 100)')
    a.text(pd.Timestamp('2010-03-01'), 107.5, 'Estimation window 2010–2019', color=S.MUTED, fontsize=7, va='center')
    a.text(pd.Timestamp('2020-02-01'), 107.5, 'Out of sample', color=S.MUTED, fontsize=7, va='center')
    a.text(p0 + (p1 - p0) / 2, 44, 'Pandemic\nmonths', color=S.MUTED, fontsize=6.5, ha='center', va='bottom')
    # direct labels on the right edge
    last = g.iloc[-1]
    a.annotate('Actual', (last.date, last.ics), xytext=(4, -2), textcoords='offset points',
               color=S.INK, fontsize=7.5, va='center')
    a.annotate('M1 prediction', (last.date, last.pred), xytext=(4, 0), textcoords='offset points',
               color=S.INK, fontsize=7.5, va='center')
    S.panel_label(a, '(a)')

    # (b) gap with the 95% band of the prediction error around zero
    for m in (pre, post):
        d = g[m]
        b.fill_between(d.date, d.pi95_lo_mbb - d.pred, d.pi95_hi_mbb - d.pred, color=S.BLUE, alpha=0.16, lw=0, zorder=2)
    b.plot(fit.date, fit.gap, color=S.MUTED, lw=0.9, zorder=3)
    for m in (pre, post):
        d = g[m]
        b.plot(d.date, d.gap, color=S.ORANGE, lw=1.4, zorder=4)
    b.axhline(0, color=S.INK, lw=0.6, zorder=3)
    P = pd.read_csv(RES / 'stage1_m1' / 'm1_periods.csv')
    P = P[(P.dv == 'ics') & (P.period != '2020-01..2021-06')]
    for _, r in P.iterrows():
        s, e = r.period.split('..')
        s, e = pd.Timestamp(s + '-01'), pd.Timestamp(e + '-01') + pd.offsets.MonthEnd(0)
        b.plot([s, e], [r.mean_gap] * 2, color=S.INK, lw=1.0, zorder=5)
        b.text(s + (e - s) / 2, -57, f'{r.mean_gap:.1f}'.replace('-', '−'),
               ha='center', va='center', fontsize=7, color=S.INK)
    w = pd.Timestamp(WEB_ONLY + '-01')
    b.axvline(w, color=S.MUTED, lw=0.6, ls=(0, (1, 1.5)), zorder=1)
    b.text(w, 19, ' Web-only interviews', color=S.MUTED, fontsize=6.5, va='top', ha='left')
    b.set_ylim(-62, 21)
    b.set_yticks([-60, -40, -20, 0])
    b.set_ylabel('Gap (index points)')
    S.panel_label(b, '(b)')
    b.xaxis.set_major_locator(mdates.YearLocator(2))
    b.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    b.set_xlim(pd.Timestamp('2010-01-01'), pd.Timestamp('2027-03-01'))

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    h = [Line2D([], [], color=S.INK, lw=1.3), Line2D([], [], color=S.BLUE, lw=1.4),
         Line2D([], [], color=S.BLUE, lw=1.0, ls=(0, (4, 2))), Patch(color=S.BLUE, alpha=0.16, lw=0),
         Line2D([], [], color=S.ORANGE, lw=1.4), Line2D([], [], color=S.MUTED, lw=0.9)]
    lab = ['Michigan ICS', 'M1 out-of-sample prediction', 'M1 in-sample fit', '95% prediction interval',
           'Gap, out of sample', 'Residual, in sample']
    fig.legend(h, lab, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.075), handlelength=2.2,
               columnspacing=1.6)
    fig.savefig(OUT / 'fig_gap.pdf')
    plt.close(fig)


ADMIN = [('Obama', '2010-01', '2017-01'), ('Trump I', '2017-01', '2021-01'),
         ('Biden', '2021-01', '2025-01'), ('Trump II', '2025-01', '2026-11')]
ADMIN_KEY = {'Obama': 'Obama 2010-2016', 'Trump I': 'Trump 2017-2020', 'Biden': 'Biden 2021-2024',
             'Trump II': 'Trump 2025-'}


def _z(x):
    return (x - x.mean()) / x.std()


def fig_media():
    """National LLM tone vs SF Fed news sentiment; government-blame share by administration."""
    m = pd.read_csv(ROOT / 'features' / 'media_monthly.csv')
    m = m[m.group == 'national'].copy()
    m['date'] = pd.to_datetime(m.month)
    sf = pd.read_csv(ROOT / 'features' / 'sffed_news_sentiment_monthly.csv')
    sf = sf[(sf.month >= '2010-01') & (sf.month <= '2026-10')].copy()
    sf['date'] = pd.to_datetime(sf.month)
    am = pd.read_csv(RES / 'stage2_bias' / 'attribution_means.csv').set_index('administration')

    fig, (a, b) = plt.subplots(2, 1, figsize=(S.TEXT_WIDTH_IN, 3.05), sharex=True,
                               gridspec_kw={'height_ratios': [1.25, 1], 'hspace': 0.18})
    tz = _z(m.net_tone)
    a.plot(m.date, tz, color=S.BLUE, lw=0.6, alpha=0.35, zorder=2)
    a.plot(m.date, tz.rolling(3).mean(), color=S.BLUE, lw=1.4, zorder=3)
    sz = _z(sf.sffed_news_sentiment_mean)
    a.plot(sf.date, sz.rolling(3).mean(), color=S.AQUA, lw=1.4, zorder=3)
    a.axhline(0, color=S.INK, lw=0.5)
    a.set_ylabel('Standardized units')
    a.set_ylim(-4.2, 2.6)
    S.panel_label(a, '(a)')

    for name, s0, s1 in ADMIN:
        x0, x1 = pd.Timestamp(s0 + '-01'), pd.Timestamp(s1 + '-01')
        if name in ('Trump I', 'Trump II'):
            b.axvspan(x0, x1, color=S.SHADE, lw=0, zorder=0)
        v = am.loc[ADMIN_KEY[name], 'blame_admin_share']
        b.plot([x0, x1], [v, v], color=S.INK, lw=1.1, zorder=4)
        b.text(x0 + (x1 - x0) / 2, 0.66, f'{name}\nmean {v:.2f}', ha='center', va='center', fontsize=6.8,
               color=S.MUTED, linespacing=1.15)
    b.plot(m.date, m.blame_admin_share.rolling(3).mean(), color=S.BLUE, lw=1.1, zorder=3)
    b.set_ylim(0, 0.76)
    b.set_ylabel('Share of relevant items')
    S.panel_label(b, '(b)')
    b.xaxis.set_major_locator(mdates.YearLocator(2))
    b.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    b.set_xlim(pd.Timestamp('2010-01-01'), pd.Timestamp('2026-11-01'))

    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=S.BLUE, lw=0.6, alpha=0.35), Line2D([], [], color=S.BLUE, lw=1.4),
         Line2D([], [], color=S.AQUA, lw=1.4), Line2D([], [], color=S.INK, lw=1.1)]
    lab = ['LLM net tone, monthly', 'LLM measure, 3-month mean', 'SF Fed news sentiment, 3-month mean',
           'Administration mean']
    fig.legend(h, lab, loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.085), handlelength=2.2, columnspacing=1.6)
    fig.savefig(OUT / 'fig_media.pdf')
    plt.close(fig)


SPEC_LABEL = {
    'main': 'Main specification',
    'DV ICC': 'Dependent variable: ICC', 'DV ICE': 'Dependent variable: ICE',
    'cutoff = Michigan preliminary release': 'Cutoff: Michigan preliminary release',
    'GDP yoy': 'GDP year over year', 'first differences': 'First differences',
    'excluding 2020-03..2020-12': 'Excluding 2020-03 to 2020-12',
    'web-mode step dummy': 'Web-mode step dummy', 'drop 2024-04..06': 'Drop 2024-04 to 2024-06',
    'media: tone 3-month mean': 'Tone, 3-month mean', 'media: net_fact': 'Factual direction (net)',
    'media: share_negative': 'Share negative', 'media: SF Fed index': 'SF Fed news sentiment',
    'media: full-frame LM dictionary': 'Full-frame LM dictionary', 'media: NYT only net_tone': 'NYT only',
    'media: media months 2026-01 and 2026-10 missing': 'Incomplete media months set missing',
    'media: EPU (real-time)': 'Economic policy uncertainty', 'tone lag 1-3 by BIC': 'Tone lag 1 to 3 by BIC',
    'month dummies excluded': 'No month dummies',
}


def fig_spec():
    """Clark-West p-values across the 21 specifications, AR version."""
    v = pd.read_csv(RES / 'stage3_robustness' / 'variants.csv')
    v = v[v.version == 'AR']
    v['label'] = v.variant.map(lambda x: SPEC_LABEL.get(x, 'Excess tone (residualized)'))
    w = v.pivot_table(index='label', columns='comparison', values='cw_p')
    w = w.sort_values('M1c vs M3', ascending=False)
    main = 'Main specification'
    order = [i for i in w.index if i != main] + [main]
    w = w.loc[order]
    y = np.arange(len(w))
    fig, ax = plt.subplots(figsize=(S.TEXT_WIDTH_IN, 3.15))
    ax.axvspan(0.001, 0.05, color=S.SHADE, lw=0, zorder=0)
    ax.axvline(0.05, color=S.MUTED, lw=0.7, ls=(0, (2, 2)))
    for yi, (lab, r) in zip(y, w.iterrows()):
        ax.plot([r['M1 vs M2'], r['M1c vs M3']], [yi, yi], color=S.GRID, lw=1.2, zorder=1)
    ax.scatter(w['M1 vs M2'], y, s=22, facecolor='white', edgecolor=S.BLUE, lw=1.2, zorder=3,
               label='M2 vs M1: tone added to fundamentals')
    ax.scatter(w['M1c vs M3'], y, s=24, color=S.ORANGE, edgecolor='white', lw=0.6, zorder=4,
               label='M3 vs M1c: tone added to fundamentals + household + political')
    ax.set_xscale('log')
    ax.set_xlim(0.003, 1.0)
    ax.set_xticks([0.005, 0.01, 0.05, 0.1, 0.5, 1])
    ax.set_xticklabels(['0.005', '0.01', '0.05', '0.1', '0.5', '1'])
    ax.set_yticks(y)
    ax.set_yticklabels(w.index, fontsize=7)
    for t in ax.get_yticklabels():
        if t.get_text() == main:
            t.set_fontweight('bold')
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='y', visible=False)
    ax.grid(axis='x', color=S.GRID, lw=0.5)
    ax.set_xlabel('Clark–West one-sided p-value (log scale)')
    ax.text(0.0034, -0.45, 'Significant at 5%', color=S.MUTED, fontsize=7, va='center')
    ax.set_ylim(-0.7, len(w) - 0.1)
    ax.legend(loc='lower center', bbox_to_anchor=(0.36, -0.29), ncol=1, frameon=False)
    fig.savefig(OUT / 'fig_spec.pdf')
    plt.close(fig)


def fig_lp():
    """Local projections in both directions (main specification)."""
    L = pd.read_csv(RES / 'stage4_timing' / 'local_projections.csv')
    L = L[L.spec.str.startswith('main')]
    fig, axes = plt.subplots(1, 2, figsize=(S.TEXT_WIDTH_IN, 2.05), sharey=False,
                             gridspec_kw={'wspace': 0.28})
    titles = {'forward': ('(a)', 'Response of sentiment to news tone'),
              'reverse': ('(b)', 'Response of news tone to sentiment')}
    for ax, d in zip(axes, ['forward', 'reverse']):
        r = L[L.direction == d]
        avg = r[r.horizon == 'avg 0-6'].iloc[0]
        r = r[r.horizon != 'avg 0-6'].assign(h=lambda x: x.horizon.astype(int)).sort_values('h')
        lo, hi = r.coef - 1.96 * r.se, r.coef + 1.96 * r.se
        ax.fill_between(r.h, lo, hi, color=S.BLUE, alpha=0.16, lw=0)
        ax.plot(r.h, r.coef, color=S.BLUE, lw=1.4, marker='o', ms=3.5, mfc='white', mew=1.1)
        xa = 7.6
        ax.errorbar([xa], [avg.coef], yerr=[[1.96 * avg.se], [1.96 * avg.se]], fmt='s', ms=4,
                    color=S.INK, ecolor=S.INK, elinewidth=1.0, capsize=0)
        ax.axhline(0, color=S.INK, lw=0.6)
        ax.axvline(6.8, color=S.GRID, lw=0.8)
        ax.set_xticks(list(range(0, 7)) + [xa])
        ax.set_xticklabels([str(i) for i in range(0, 7)] + ['Avg\n0–6'])
        ax.set_xlim(-0.4, 8.1)
        ax.set_xlabel('Months after the shock (h)')
        S.panel_label(ax, titles[d][0])
        ax.text(0.06, 1.02, titles[d][1], transform=ax.transAxes, fontsize=7.5, va='bottom', color=S.INK)
    axes[0].set_ylabel('Standard deviations')
    fig.savefig(OUT / 'fig_lp.pdf')
    plt.close(fig)


GROUP_LABEL = {'y13': 'Income: bottom third', 'y23': 'Income: middle third', 'y33': 'Income: top third',
               'a1834': 'Age 18–34', 'a3554': 'Age 35–54', 'a5597': 'Age 55+',
               'w': 'West', 'nc': 'North Central', 'ne': 'Northeast', 's': 'South',
               'ehs': 'High school or less', 'esc': 'Some college', 'ecd': 'College degree'}
P1, P2 = ('2021-07', '2022-12'), ('2025-01', '2026-08')


def fig_groups():
    g = pd.read_csv(RES / 'stage5_mechanisms' / 'group_gaps_monthly.csv')
    p = pd.read_csv(RES / 'stage4_timing' / 'group_gaps_monthly.csv')

    def pm(df, col, per):
        x = df[(df.month >= per[0]) & (df.month <= per[1])][col]
        return x.mean()
    rows = [(GROUP_LABEL[k], pm(g, f'gap_ics_{k}', P1), pm(g, f'gap_ics_{k}', P2)) for k in GROUP_LABEL]
    party = [('Democrats', pm(p, 'gap_ics_dem', P1), pm(p, 'gap_ics_dem', P2)),
             ('Republicans', pm(p, 'gap_ics_rep', P1), pm(p, 'gap_ics_rep', P2))]
    fig, (a, b) = plt.subplots(1, 2, figsize=(S.TEXT_WIDTH_IN, 2.75),
                               gridspec_kw={'width_ratios': [1.55, 1], 'wspace': 0.5})

    def draw(ax, rr, xlim):
        y = np.arange(len(rr))[::-1].astype(float)
        for yi, (lab, v1, v2) in zip(y, rr):
            ax.plot([v1, v2], [yi, yi], color=S.GRID, lw=1.2, zorder=1)
        ax.scatter([r[1] for r in rr], y, s=22, facecolor='white', edgecolor=S.BLUE, lw=1.2, zorder=3)
        ax.scatter([r[2] for r in rr], y, s=24, color=S.ORANGE, edgecolor='white', lw=0.6, zorder=4)
        ax.axvline(0, color=S.INK, lw=0.6)
        ax.set_yticks(y)
        ax.set_yticklabels([r[0] for r in rr], fontsize=7)
        ax.tick_params(axis='y', length=0)
        ax.grid(axis='y', visible=False)
        ax.grid(axis='x', color=S.GRID, lw=0.5)
        ax.set_xlim(*xlim)
    # gaps between dimension blocks
    draw(a, rows, (-50, 5))
    for yb in (9.5, 6.5, 2.5):
        a.axhline(yb, color=S.GRID, lw=0.6)
    a.set_xlabel('Gap relative to the group’s own M1 (index points)')
    S.panel_label(a, '(a)', x=-0.42)
    draw(b, party, (-85, 15))
    b.set_xlabel('Change from own 2017–19 mean (points)')
    b.set_ylim(-0.8, 1.8)
    S.panel_label(b, '(b)', x=-0.36)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], ls='', marker='o', mfc='white', mec=S.BLUE, mew=1.2, ms=5),
         Line2D([], [], ls='', marker='o', color=S.ORANGE, ms=5.5)]
    fig.legend(h, ['2021-07 to 2022-12', '2025-01 to 2026-08'], loc='lower center', ncol=2,
               bbox_to_anchor=(0.5, -0.13))
    fig.savefig(OUT / 'fig_groups.pdf')
    plt.close(fig)


if __name__ == '__main__':
    S.apply()
    OUT.mkdir(parents=True, exist_ok=True)
    fig_gap()
    fig_media()
    fig_spec()
    fig_lp()
    fig_groups()
