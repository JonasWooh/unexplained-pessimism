"""Stage 3 figures: specification curve of the Clark-West statistic (M1 vs M2 and M1c vs M3) across all robustness
variants, AR and no-AR versions, and the rolling 60-month gamma of M3. Outputs: results/stage3_robustness/*.png."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from lib import ROOT
OUT=ROOT/'results/stage3_robustness'
V=pd.read_csv(OUT/'variants.csv')
fig,axes=plt.subplots(2,2,figsize=(14,10))
for i,ver in enumerate(['AR','no AR']):
 for j,comp in enumerate(['M1 vs M2','M1c vs M3']):
  ax=axes[i,j];d=V[(V.version==ver)&(V.comparison==comp)].sort_values('cw_stat').reset_index(drop=True)
  col=['tab:red' if v=='main' else ('tab:blue' if p<0.05 else 'tab:gray') for v,p in zip(d.variant,d.cw_p)]
  ax.scatter(d.cw_stat,range(len(d)),c=col,s=22);ax.axvline(1.645,ls='--',c='k',lw=0.8)
  ax.set_yticks(range(len(d)));ax.set_yticklabels(d.variant,fontsize=7);ax.set_title(f'{comp}, {ver} (Clark-West, 1-step)',fontsize=10)
  ax.set_xlabel('CW statistic (dashed: 5% one-sided)')
fig.tight_layout();fig.savefig(OUT/'fig_spec_curve_cw.png',dpi=150)
R=pd.read_csv(OUT/'rolling_gamma.csv')
fig,ax=plt.subplots(figsize=(10,4))
for ver,c in [('AR','tab:blue'),('no AR','tab:orange')]:
 d=R[R.version==ver];x=pd.to_datetime(d.window_end);ax.plot(x,d.gamma,c=c,label=f'M3 gamma ({ver})');ax.fill_between(x,d.lo,d.hi,color=c,alpha=0.15)
ax.axhline(0,c='k',lw=0.6);ax.set_title('Rolling 60-month coefficient on national net tone (t-1), M3, HAC 95% band');ax.legend()
fig.tight_layout();fig.savefig(OUT/'fig_rolling_gamma.png',dpi=150);print('ok')
