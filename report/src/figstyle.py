"""Shared matplotlib style for report figures (print, light background).

Palette slots are fixed by role and never cycled:
  ACTUAL  observed series (near-black ink)
  BLUE    model prediction / first categorical series
  ORANGE  gap or second categorical series
  AQUA    third categorical series
Text never takes a series color.
"""
from pathlib import Path
import matplotlib as mpl
from matplotlib import font_manager

INK = '#1f2328'
MUTED = '#6b7280'
GRID = '#e5e7eb'
SHADE = '#f1f2f4'
BLUE = '#2a78d6'
ORANGE = '#eb6834'
AQUA = '#1baf7a'
YELLOW = '#eda100'

TEXT_WIDTH_IN = 6.5   # US Letter with 1-inch margins

_GYRE = Path('/usr/share/texmf/fonts/opentype/public/tex-gyre')


def apply():
    if _GYRE.exists():
        for f in _GYRE.glob('texgyreheros-*.otf'):
            font_manager.fontManager.addfont(str(f))
    mpl.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['TeX Gyre Heros', 'Helvetica', 'Arial', 'DejaVu Sans'],
        'font.size': 8, 'axes.labelsize': 8, 'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
        'legend.fontsize': 7.5, 'axes.titlesize': 8,
        'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
        'axes.edgecolor': MUTED, 'axes.linewidth': 0.6,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': GRID, 'grid.linewidth': 0.5,
        'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'xtick.major.size': 3, 'ytick.major.size': 0,
        'lines.linewidth': 1.3, 'legend.frameon': False,
        'pdf.fonttype': 42, 'svg.fonttype': 'none',
        'savefig.bbox': 'tight', 'savefig.pad_inches': 0.02,
    })


def panel_label(ax, s, x=-0.075):
    ax.text(x, 1.02, s, transform=ax.transAxes, fontweight='bold', fontsize=8.5,
            va='bottom', ha='left', color=INK)
