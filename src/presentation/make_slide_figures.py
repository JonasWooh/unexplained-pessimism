"""Slide-size chart layers built from frozen result files. Run from the project root:
    python3 src/presentation/make_slide_figures.py
Each chart is split into transparent PNG layers of identical size and axes, so the deck can
reveal them one at a time. Colours follow the report: ink = actual, blue = model, orange = gap.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'results'
OUT = ROOT / 'presentation' / 'build'

INK = '#1f2328'
MUTED = '#6b7280'
GRID = '#e5e7eb'
SHADE = '#f1f2f4'
BLUE = '#2a78d6'
ORANGE = '#eb6834'
DPI = 300

PANDEMIC = ('2020-03', '2021-06')   # months the model is not applied to (frozen design)

_GYRE = Path('/usr/share/texmf/fonts/opentype/public/tex-gyre')


def style():
    if _GYRE.exists():
        for f in _GYRE.glob('texgyreheros-*.otf'):
            font_manager.fontManager.addfont(str(f))
    mpl.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica Neue', 'TeX Gyre Heros', 'Helvetica', 'Arial'],
        'font.size': 13, 'axes.labelsize': 13, 'xtick.labelsize': 12.5, 'ytick.labelsize': 12.5,
        'text.color': INK, 'axes.labelcolor': MUTED, 'xtick.color': MUTED, 'ytick.color': MUTED,
        'axes.edgecolor': '#c7cbd1', 'axes.linewidth': 0.9,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
        'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': GRID, 'grid.linewidth': 0.9,
        'xtick.major.size': 4, 'ytick.major.size': 0, 'xtick.major.width': 0.9,
        'savefig.transparent': True,
    })


def layers(name, size, rect, limits, base, draws):
    """Render one PNG per layer with identical figure size, axes rectangle and limits.
    limits(ax) fixes scales and limits in every layer; base(ax) draws the axes layer;
    draws maps each further layer name to a function that draws only that layer's artists."""
    for lname, fn in [('base', base)] + list(draws.items()):
        fig = plt.figure(figsize=size, dpi=DPI)
        ax = fig.add_axes(rect)
        limits(ax)
        if lname != 'base':
            ax.set_axis_off()
        fn(ax)
        fig.savefig(OUT / f'{name}_{lname}.png', dpi=DPI)
        plt.close(fig)


# ---------------------------------------------------------------- slide 2: the gap
def fig_gap():
    g = pd.read_csv(RES / 'stage1_m1' / 'm1_gap_monthly.csv').query("dv == 'ics'").copy()
    g['date'] = pd.to_datetime(g.month)
    pand = (g.month >= PANDEMIC[0]) & (g.month <= PANDEMIC[1])
    oos = ~g.in_sample.astype(bool)
    pre = oos & (g.month < PANDEMIC[0])
    post = oos & (g.month > PANDEMIC[1])
    p0 = pd.Timestamp(PANDEMIC[0] + '-01')
    p1 = pd.Timestamp(PANDEMIC[1] + '-01') + pd.offsets.MonthEnd(0)
    x0, x1 = pd.Timestamp('2010-01-01'), pd.Timestamp('2026-12-31')
    last = g.iloc[-1]

    def limits(ax):
        ax.set_xlim(x0, x1)
        ax.set_ylim(35, 112)

    def setup(ax):
        ax.set_yticks([40, 60, 80, 100])
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.axvspan(p0, p1, color=SHADE, lw=0, zorder=0)
        ax.text(p0 + (p1 - p0) / 2, 38, 'Pandemic', color=MUTED, fontsize=11, ha='center', va='bottom')
        ax.axvline(pd.Timestamp('2020-01-01'), color='#c7cbd1', lw=0.9, ls=(0, (3, 3)), zorder=1)
        ax.text(pd.Timestamp('2010-03-01'), 108, 'Model fit 2010–19', color=MUTED, fontsize=11.5, va='center')
        ax.text(pd.Timestamp('2020-03-01'), 108, 'Out of sample', color=MUTED, fontsize=11.5, va='center')
        ax.set_ylabel('Michigan sentiment index')

    def model(ax):
        for m in (pre, post):
            d = g[m]
            ax.fill_between(d.date, d.pi95_lo_mbb, d.pi95_hi_mbb, color=BLUE, alpha=0.14, lw=0)
            ax.plot(d.date, d.pred, color=BLUE, lw=2.6, solid_capstyle='round')
        fit = g[~oos]
        ax.plot(fit.date, fit.pred, color=BLUE, lw=2.0, ls=(0, (4, 2.5)))
        ax.text(pd.Timestamp('2023-10-01'), 103.5, 'Economy predicts', color=BLUE, fontsize=13,
                fontweight='bold', ha='left', va='bottom')

    def actual(ax):
        ax.plot(g.date, g.ics, color=INK, lw=2.4, solid_capstyle='round', zorder=4)
        ax.annotate('People say', (last.date, last.ics), xytext=(-6, -18), textcoords='offset points',
                    color=INK, fontsize=13, fontweight='bold', ha='right', va='top')

    def gap(ax):
        d = g[post]
        ax.fill_between(d.date, d.ics, d.pred, color=ORANGE, alpha=0.30, lw=0, zorder=2)
        mid = d[d.month == '2025-06'].iloc[0]
        ax.text(mid.date, (mid.ics + mid.pred) / 2, 'Gap', color=ORANGE, fontsize=15, fontweight='bold',
                ha='center', va='center', zorder=5)

    layers('gap', (8.7, 4.95), [0.085, 0.09, 0.9, 0.89], limits, setup,
           {'model': model, 'actual': actual, 'gap': gap})


# ---------------------------------------------------------------- slide 4: groups
GROUPS = [
    ('Income', [('y13', 'Bottom third'), ('y23', 'Middle third'), ('y33', 'Top third')]),
    ('Age', [('a1834', '18–34'), ('a3554', '35–54'), ('a5597', '55+')]),
    ('Region', [('w', 'West'), ('nc', 'North Central'), ('ne', 'Northeast'), ('s', 'South')]),
    ('Education', [('ehs', 'High school or less'), ('esc', 'Some college'), ('ecd', 'College degree')]),
]


def fig_groups():
    gg = pd.read_csv(RES / 'stage5_mechanisms' / 'group_gaps_monthly.csv')
    gg = gg[(gg.month >= '2025-01') & (gg.month <= '2026-08')]
    rows, heads, y = [], [], 0.0
    for head, items in GROUPS:
        heads.append((head, y))
        y += 0.85
        for k, lab in items:
            rows.append((lab, gg[f'gap_ics_{k}'].mean(), y))
            y += 1.0
        y += 0.35
    ymax = y
    vals = [r[1] for r in rows]

    def limits(ax):
        ax.set_xlim(-50, 0)
        ax.set_ylim(ymax - 0.2, -0.6)

    def setup(ax):
        ax.set_yticks([])
        ax.grid(axis='y', visible=False)
        ax.grid(axis='x', color=GRID, lw=0.9)
        ax.set_xticks([-50, -40, -30, -20, -10, 0])
        ax.set_xticklabels(['−50', '−40', '−30', '−20', '−10', '0'])
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(axis='x', length=0)
        ax.axvline(0, color=INK, lw=1.1)
        ax.set_xlabel('Gap vs. own-group economic model, 2025–26', labelpad=8)
        ax.axvspan(min(vals), max(vals), color=ORANGE, alpha=0.08, lw=0)
        for head, yh in heads:
            ax.text(-50.6, yh + 0.1, head.upper(), color=MUTED, fontsize=10.5, fontweight='bold',
                    ha='right', va='center')
        for lab, v, yr in rows:
            ax.text(-50.6, yr, lab, color=INK, fontsize=12.5, ha='right', va='center')
            ax.plot([v, 0], [yr, yr], color=GRID, lw=1.6, zorder=1)
            ax.scatter([v], [yr], s=95, color=ORANGE, edgecolor='white', lw=1.2, zorder=3)

    layers('groups', (6.9, 5.0), [0.33, 0.12, 0.64, 0.86], limits, setup, {})


# ---------------------------------------------------------------- slide 7: specification strip
def fig_spec():
    v = pd.read_csv(RES / 'stage3_robustness' / 'variants.csv').query("version == 'AR'")
    rows = [('M1 vs M2', 1.0, BLUE, 'Tone added to the economy model'),
            ('M1c vs M3', 0.0, ORANGE, 'Tone added after household and political controls')]

    def limits(ax):
        ax.set_xscale('log')
        ax.set_xlim(0.003, 1.0)
        ax.set_ylim(-0.55, 1.75)

    def setup(ax):
        ax.set_yticks([])
        ax.grid(axis='y', visible=False)
        ax.grid(axis='x', color=GRID, lw=0.9)
        ax.set_xticks([0.005, 0.01, 0.05, 0.1, 0.5, 1])
        ax.set_xticklabels(['0.005', '0.01', '0.05', '0.1', '0.5', '1'])
        ax.minorticks_off()
        ax.axvspan(0.003, 0.05, color=SHADE, lw=0, zorder=0)
        ax.axvline(0.05, color=MUTED, lw=1.1, ls=(0, (3, 3)))
        ax.text(0.0034, 1.62, 'Significant (p < 0.05)', color=MUTED, fontsize=11.5, va='center')
        ax.set_xlabel('p-value of the forecast test, 20 specifications per row (log scale)', labelpad=8)

    def draw_row(comp, y0, color, label):
        def fn(ax):
            d = v[v.comparison == comp].sort_values('cw_p').reset_index(drop=True)
            jit = np.where(np.arange(len(d)) % 2 == 0, 0.07, -0.07)   # display offset only
            other = d.variant != 'main'
            ax.scatter(d.cw_p[other], y0 + jit[other], s=110, color=color, alpha=0.85,
                       edgecolor='white', lw=1.0, zorder=3)
            mn = d[d.variant == 'main']
            ax.scatter(mn.cw_p, y0 + jit[mn.index], s=210, color=color, edgecolor=INK, lw=1.8, zorder=4)
            nsig = int((d.cw_p < 0.05).sum())
            ax.text(0.0034, y0 + 0.33, label, color=INK, fontsize=13, fontweight='bold', va='center')
            ax.text(0.97, y0 + 0.33, f'{nsig} of {len(d)} significant', color=color, fontsize=14,
                    fontweight='bold', va='center', ha='right')
        return fn

    layers('spec', (11.6, 3.55), [0.03, 0.2, 0.94, 0.78], limits, setup,
           {f'row{i + 1}': draw_row(*r) for i, r in enumerate(rows)})


# ---------------------------------------------------------------- slide 1: decoration
def fig_title_lines():
    g = pd.read_csv(RES / 'stage1_m1' / 'm1_gap_monthly.csv').query("dv == 'ics'").copy()
    g['date'] = pd.to_datetime(g.month)
    pand = (g.month >= PANDEMIC[0]) & (g.month <= PANDEMIC[1])
    fig = plt.figure(figsize=(13.333, 2.6), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    pred = g.pred.where(~pand)
    post = g.month > PANDEMIC[1]
    ax.fill_between(g.date[post], g.ics[post], g.pred[post], color=ORANGE, alpha=0.7, lw=0)
    ax.plot(g.date, pred, color='#6fa8ef', lw=2.0, alpha=0.8)
    ax.plot(g.date, g.ics, color='#ffffff', lw=2.0, alpha=0.75)
    ax.set_xlim(g.date.min(), g.date.max())
    ax.set_ylim(30, 115)
    fig.savefig(OUT / 'title_lines.png', dpi=DPI)
    plt.close(fig)


if __name__ == '__main__':
    style()
    OUT.mkdir(parents=True, exist_ok=True)
    fig_gap()
    fig_groups()
    fig_spec()
    fig_title_lines()
