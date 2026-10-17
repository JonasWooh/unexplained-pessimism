"""Stage 3 robustness, excess tone, coefficient stability and magnitude (research design v1, sections on M2/M3 and the
robustness table). Every variant re-runs the recursive 1-step forecasts of M1, M2, M1c, M3 (AR and no-AR versions) and
the full-window in-sample media coefficient gamma of M3 (HAC 12), and is recorded in results/stage3_robustness/variants.csv.

Variants: DV ICC / ICE; cutoff = Michigan preliminary release (core U, pi, g from econ_monthly_realtime_prelim_cutoff.csv,
household controls unchanged); GDP yoy; first differences (forecasts converted back to levels); pandemic months
2020-03..12 dropped from training and evaluation; web-mode step dummy (2024-07 on) in every model; 2024-04..06 dropped;
media measure = 3-month mean of net_tone, net_fact, share_negative, SF Fed index (month t-1), full-frame LM dictionary index,
EPU (real-time at cutoff t); NYT-only net_tone; media months 2026-01 and 2026-10 (incomplete) set missing; tone lag 1-3 by
BIC; month dummies excluded. Excess tone: in every training window net_tone_{t-1} is regressed on the real-time
fundamentals at cutoff t (U, pi, g), and the residual (out of sample for the origin) replaces tone.
Stability: 60-month rolling gamma of M3; Chow-type tests of a shift in gamma (tone x post dummy, plus intercept shift)
at 2020-03, 2024-07, 2025-01 on the full window. VIF of M3 regressors on the first training window and the full window.
Magnitude: gamma of M3 (2010-06..2019-12 fit, the gap window) times mean(Tone_{t-1} - 2019 mean) by period, divided by
the stage 1 mean ICS gap of that period: an upper-bound association share, not a causal effect.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from lib import ROOT,SEED,ols,clark_west,PERIODS,GAP_PERIODS
import stage3_forecast as S

OUT=ROOT/'results/stage3_robustness';OUT.mkdir(parents=True,exist_ok=True)

def nat_media():
 M=pd.read_csv(ROOT/'features/media_monthly.csv');return M[M.group=='national'].sort_values('month').reset_index(drop=True)

def media_alt(series):
 """Media frame whose net_tone column is the given monthly series (index = month of publication)."""
 M=nat_media()[['month']].copy();M['net_tone']=M.month.map(series);return M

def nyt_only():
 L=pd.read_csv(ROOT/'labels/ai_corpus_labels.csv');L=L[(L.group=='national')&(L.source=='NYT')&(L.relevant=='yes')]
 L['s']=np.select([L.tone_overall=='positive',L.tone_overall=='negative'],[1.0,-1.0],0.0)
 return L.groupby('month').apply(lambda g:np.sum(g.s*g.w)/np.sum(g.w))

def cw_pair(D,small,big,ar,seasonal=True,lag_select=None,rows_mask=None,diff=False):
 Fs=S.recursive(D,small,ar=ar,seasonal=seasonal);Fb=S.recursive(D,big,ar=ar,seasonal=seasonal,lag_select=lag_select)
 if diff:
  base=D.set_index('month').y_level_l1
  for F in (Fs,Fb):F['f']=F.f+F.target_month.map(base).values;F['y']=F.y+F.target_month.map(base).values
 m=(np.ones(len(Fs),bool) if rows_mask is None else rows_mask(Fs))&Fs.f.notna().to_numpy()&Fb.f.notna().to_numpy()
 st,p,ms,mb=S.clark_west(Fs.y[m],Fs.f[m],Fb.f[m],lags=int(np.floor(m.sum()**(1/3))))
 return dict(cw_stat=st,cw_p=p,rmse_ratio=np.sqrt(mb/ms),n_eval=int(m.sum()))

def gamma(D,cols,ar,seasonal=True,lags=12):
 X=cols+(['y_l1'] if ar else [])+(S.SEAS if seasonal else []);Z=D[X+['y']].dropna();f=ols(Z.y,Z[X],lags)
 return f.params['tone_l1'],f.bse['tone_l1'],f.pvalues['tone_l1'],int(f.nobs)

def run_variant(name,D,ar_versions=(True,False),seasonal=True,extra=[],lag_select=None,rows_mask=None,diff=False,status='robustness'):
 rows=[]
 m=S.models()
 for ar in ar_versions:
  for s,b in [('M1','M2'),('M1c','M3')]:
   r=cw_pair(D,m[s]+extra,m[b]+extra,ar,seasonal,lag_select if b in ('M2','M3') else None,rows_mask,diff)
   g=gamma(D,m['M3']+extra,ar,seasonal) if not lag_select else (np.nan,np.nan,np.nan,np.nan)
   rows.append(dict(variant=name,status=status,version='AR' if ar else 'no AR',comparison=f'{s} vs {b}',**r,gamma_M3=g[0],gamma_se=g[1],gamma_p=g[2],n_insample=g[3]))
 return rows

EXCESS_F=S.X1+S.H+['d_unrate_rt','d_pce_yoy_rt','d_gdp_qoq_saar_rt']

def excess_tone_forecasts(D,ar):
 """Recursive forecasts where tone is replaced by its residual on fundamentals, estimated in each training window.
 Residualising on exactly the regressors already in the model (U, pi, g) changes nothing (Frisch-Waugh-Lovell: the
 span of the regressors and hence every fitted value and forecast is identical). The fundamentals set is therefore
 EXCESS_F = U, pi, g levels + household controls H + the news released during month t-1 (change of U, pi, g between
 cutoffs t-1 and t), so the excess tone also nets out what M2 does not otherwise contain."""
 D=D.copy()
 for c in S.X1:D['d_'+c]=D[c].diff()
 out={}
 for name,cols in S.models().items():
  if 'tone_l1' not in cols:out[name]=S.recursive(D,cols,ar=ar);continue
  X=[c if c!='tone_l1' else 'xtone' for c in cols]+(['y_l1'] if ar else [])+S.SEAS;res=[]
  for o in D.index[D.month>=S.FIRST_EVAL]:
   tr=D.loc[:o-1].dropna(subset=['tone_l1']+EXCESS_F)
   a=S.lstsq_fit(tr.tone_l1.values,tr[EXCESS_F].values)
   T=D.loc[:o].copy();T['xtone']=T.tone_l1-(a[0]+T[EXCESS_F].values@a[1:])
   Z=T.loc[:o-1,X+['y']].dropna();b=S.lstsq_fit(Z.y.values,Z[X].values)
   res.append(dict(origin=D.loc[o,'month'],target_month=D.loc[o,'month'],y=D.loc[o,'y'],f=float(b[0]+T.loc[o,X].values.astype(float)@b[1:])))
  out[name]=pd.DataFrame(res)
 return out

def main():
 rng=np.random.default_rng(SEED);V=[]
 D0=S.panel()
 V+=run_variant('main',D0,status='main')
 for dv in ('icc','ice'):V+=run_variant(f'DV {dv.upper()}',S.panel(dv=dv))
 # preliminary-release cutoff
 E=pd.read_csv(ROOT/'data/processed/econ_monthly_realtime_prelim_cutoff.csv').set_index('month')
 Pn=pd.read_csv(ROOT/'data/processed/research_panel.csv')
 for c in S.X1:Pn[c]=Pn.month.map(E[c]).where(Pn.month>='2010-01',Pn[c])
 V+=run_variant('cutoff = Michigan preliminary release',S.panel(panel_df=Pn))
 Pg=pd.read_csv(ROOT/'data/processed/research_panel.csv');Pg['gdp_qoq_saar_rt']=Pg['gdp_yoy_rt']
 V+=run_variant('GDP yoy',S.panel(panel_df=Pg))
 # first differences
 Dd=D0.copy();Dd['y_level_l1']=Dd.y_l1
 for c in S.X1+S.H+S.P+['tone_l1']:Dd[c]=Dd[c].diff()
 Dd['y']=D0.y-D0.y_l1;Dd['y_l1']=Dd.y.shift(1);Dd=Dd.iloc[1:].reset_index(drop=True)
 V+=run_variant('first differences',Dd,diff=True)
 # pandemic months dropped from training and evaluation
 V+=run_variant('excluding 2020-03..2020-12',D0[~D0.month.between('2020-03','2020-12')].reset_index(drop=True))
 Dw=D0.copy();Dw['web']=(Dw.month>='2024-07').astype(float)
 V+=run_variant('web-mode step dummy',Dw,extra=['web'])
 V+=run_variant('drop 2024-04..06',D0[~D0.month.between('2024-04','2024-06')].reset_index(drop=True))
 nm=nat_media().set_index('month')
 alts={'tone 3-month mean':nm.net_tone.rolling(3).mean(),'net_fact':nm.net_fact,'share_negative':nm.share_negative,
  'SF Fed index':pd.read_csv(ROOT/'features/sffed_news_sentiment_monthly.csv').set_index('month').sffed_news_sentiment_mean,
  'full-frame LM dictionary':pd.read_csv(ROOT/'features/media_dict_monthly.csv').set_index('month').dict_net_tone_lm,
  'NYT only net_tone':nyt_only(),'media months 2026-01 and 2026-10 missing':nm.net_tone.where(~nm.index.isin(['2026-01','2026-10']))}
 for k,s in alts.items():V+=run_variant('media: '+k,S.panel(media=media_alt(s)))
 De=D0.copy();De['tone_l1']=De.epu_rt;De=De.dropna(subset=['tone_l1']).reset_index(drop=True)
 V+=run_variant('media: EPU (real-time)',De)
 Dl,c=S.secondary_lags(D0.copy(),'net_tone')
 V+=run_variant('tone lag 1-3 by BIC',Dl,lag_select={'tone_l1':c})
 V+=run_variant('month dummies excluded',D0,seasonal=False)
 # excess tone
 for ar in (True,False):
  F=excess_tone_forecasts(D0,ar)
  for s,b in [('M1','M2'),('M1c','M3')]:
   st,p,ms,mb=clark_west(F[s].y,F[s].f,F[b].f,lags=4)
   V.append(dict(variant='excess tone (residual on U, pi, g, H and month t-1 news, per window)',status='pre-registered',version='AR' if ar else 'no AR',comparison=f'{s} vs {b}',cw_stat=st,cw_p=p,rmse_ratio=np.sqrt(mb/ms),n_eval=len(F[s])))
 R=pd.DataFrame(V);R.to_csv(OUT/'variants.csv',index=False)
 # stability: rolling 60-month gamma; shift tests
 roll=[]
 for ar in (True,False):
  X=S.models()['M3']+(['y_l1'] if ar else [])+S.SEAS
  for end in range(59,len(D0)):
   Z=D0.iloc[end-59:end+1][X+['y']].dropna()
   if len(Z)<50:continue
   f=ols(Z.y,Z[X],12);roll.append(dict(version='AR' if ar else 'no AR',window_end=D0.month[end],gamma=f.params['tone_l1'],lo=f.params['tone_l1']-1.96*f.bse['tone_l1'],hi=f.params['tone_l1']+1.96*f.bse['tone_l1']))
 pd.DataFrame(roll).to_csv(OUT/'rolling_gamma.csv',index=False)
 br=[]
 for ar in (True,False):
  for bd in ('2020-03','2024-07','2025-01'):
   Db=D0.copy();Db['post']=(Db.month>=bd).astype(float);Db['tone_post']=Db.tone_l1*Db.post
   X=S.models()['M3']+(['y_l1'] if ar else [])+S.SEAS+['post','tone_post'];Z=Db[X+['y']].dropna();f=ols(Z.y,Z[X],12)
   br.append(dict(version='AR' if ar else 'no AR',break_date=bd,gamma_before=f.params['tone_l1'],gamma_shift=f.params['tone_post'],shift_se=f.bse['tone_post'],shift_p=f.pvalues['tone_post'],intercept_shift=f.params['post'],intercept_shift_p=f.pvalues['post']))
 pd.DataFrame(br).to_csv(OUT/'gamma_breaks.csv',index=False)
 from statsmodels.stats.outliers_influence import variance_inflation_factor as vif
 vr=[]
 for win,(a,b) in {'first training window 2010-06..2016-12':(S.START,'2016-12'),'full 2010-06..2026-10':(S.START,S.LAST)}.items():
  X=S.models()['M3'];Z=D0[(D0.month>=a)&(D0.month<=b)][X].dropna();Zc=sm.add_constant(Z).values
  for i,c in enumerate(X):vr.append(dict(window=win,regressor=c,vif=vif(Zc,i+1)))
 pd.DataFrame(vr).to_csv(OUT/'vif.csv',index=False)
 # magnitude
 G=pd.read_csv(ROOT/'results/stage1_m1/m1_gap_monthly.csv')
 gcol=[c for c in G.columns if c.startswith('gap')][0] if 'gap' not in G.columns else 'gap'
 G=G[G.dv=='ics'] if 'dv' in G.columns else G
 base19=D0[D0.month.between('2019-01','2019-12')].tone_l1.mean()
 mag=[]
 for ar in (True,False):
  X=S.models()['M3']+(['y_l1'] if ar else [])+S.SEAS;Z=D0[(D0.month>=S.START)&(D0.month<='2019-12')][X+['y']].dropna();f=ols(Z.y,Z[X],12)
  g=f.params['tone_l1'];rho=f.params.get('y_l1',0.0)
  for per in GAP_PERIODS:
   a,b=PERIODS[per];dt=D0[D0.month.between(a,b)].tone_l1.mean()-base19;gap=G[G.month.between(a,b)][gcol].mean()
   imp=g*dt if not ar else g*dt/(1-rho)
   mag.append(dict(version='AR (long-run gamma/(1-rho))' if ar else 'no AR',period=per,gamma=g,rho=rho if ar else np.nan,tone_dev_from_2019=dt,implied_points=imp,stage1_mean_gap=gap,share_of_gap=imp/gap))
 pd.DataFrame(mag).to_csv(OUT/'magnitude.csv',index=False)
 pd.set_option('display.width',250);pd.set_option('display.max_columns',30)
 print(R.round(3).to_string());print(pd.DataFrame(br).round(3).to_string());print(pd.DataFrame(vr).round(2).to_string());print(pd.DataFrame(mag).round(3).to_string())

if __name__=='__main__':main()
