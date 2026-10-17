"""Monthly media indices from frozen-prompt (v2) LLM labels of the stratified corpus sample (task_guide 9.7).

Ratio estimators within group x month with weight w = final_weight (design weight x within-stratum expansion);
YouTube has no design weight, so w = within-month expansion (constant within a month, i.e. unweighted).
Content measures are computed over items labeled relevant = yes; `unsure` items are counted, not used.
"""
import json
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'labels/ai/codex__v2_isolated_r1_corpus'
TOPICS=['T01_layoffs_unemployment_up','T02_hiring_jobs_growth','T03_prices_rising','T04_inflation_easing','T05_economic_growth','T06_recession_risk','T07_interest_rates_borrowing','T08_housing_costs','T09_gas_prices','T10_food_prices','T11_tariffs_trade','T12_stock_market','T13_other']
SOURCE_GAPS={('national','2026-01'):'NYT archive returns only 2026-01-01..07',('national','2026-10'):'NYT archive returns only 2026-10-01..04; month ends at study cutoff 10-14'}
LOW_N=10

def labels():
 rows=[]
 for f in sorted(RUN.glob('corpus_batch_*.jsonl')):
  for line in open(f):
   o=json.loads(line);t=set(o.get('topics') or [])
   rows.append({**{k:o.get(k) for k in ['item_id','relevant','tone_overall','fact_direction','emotional_intensity','price_frame','perspective','time_frame','numeric_claim','claim_text','definition_error','actor_1','direction_1','actor_2','direction_2']},
    **{x:int(x in t) for x in TOPICS},'batch_file':f.name})
 lab=pd.DataFrame(rows).rename(columns={'item_id':'coding_id'})
 key=pd.read_csv(ROOT/'labels/corpus_sample_key.csv')
 d=key.merge(lab,on='coding_id',how='left',validate='one_to_one')
 if d.relevant.isna().any():raise ValueError('coded sample items without labels')
 d['w']=d.final_weight.fillna(d.expansion)
 return d

def wmean(x,w):return float(np.sum(x*w)/np.sum(w)) if np.sum(w)>0 else np.nan

def month_row(g):
 w=g.w.to_numpy();y=(g.relevant=='yes').to_numpy();n=(g.relevant=='no').to_numpy()
 r=g[y];wr=r.w.to_numpy()
 def share(mask):return wmean(mask.astype(float),wr) if len(r) else np.nan
 actors=lambda a,dirn:((r.actor_1==a)&(r.direction_1==dirn))|((r.actor_2==a)&(r.direction_2==dirn))
 priced=r.price_frame.isin(['level','rate','both']);applic=r.definition_error.isin(['yes','no'])
 out=dict(n_coded=len(g),n_relevant=int(y.sum()),n_unsure=int((g.relevant=='unsure').sum()),n_not_relevant=int(n.sum()),
  relevant_share=float(np.sum(w*y)/np.sum(w*(y|n))) if np.sum(w*(y|n))>0 else np.nan,est_relevant_items=float(np.sum(w*y)),
  net_tone=share(r.tone_overall=='positive')-share(r.tone_overall=='negative') if len(r) else np.nan,
  share_negative=share(r.tone_overall=='negative'),share_positive=share(r.tone_overall=='positive'),share_mixed=share(r.tone_overall=='mixed'),
  net_fact=share(r.fact_direction=='good')-share(r.fact_direction=='bad') if len(r) else np.nan,share_no_fact=share(r.fact_direction=='no_fact'),
  emotional_intensity_mean=wmean(r.emotional_intensity.astype(float).to_numpy(),wr) if len(r) else np.nan,
  price_level_share_of_priced=wmean(r[priced].price_frame.isin(['level','both']).astype(float).to_numpy(),r[priced].w.to_numpy()) if priced.any() else np.nan,
  price_frame_share=share(priced),household_share=share(r.perspective.isin(['household','both'])),forecast_share=share(r.time_frame.isin(['forecast','both'])),
  numeric_claim_share=share(r.numeric_claim=='yes'),
  definition_error_rate=wmean((r[applic].definition_error=='yes').astype(float).to_numpy(),r[applic].w.to_numpy()) if applic.any() else np.nan,
  blame_admin_share=share(actors('president_admin','blame')),credit_admin_share=share(actors('president_admin','credit')),
  fed_mention_share=share((r.actor_1=='fed')|(r.actor_2=='fed')),business_blame_share=share(actors('business','blame')))
 for t in TOPICS:out['topic_'+t[4:]]=share(r[t]==1)
 return pd.Series(out)

def main():
 d=labels();(ROOT/'features').mkdir(exist_ok=True)
 d.drop(columns=['batch_file']).to_csv(ROOT/'labels/ai_corpus_labels.csv',index=False)
 m=d.groupby(['group','month']).apply(month_row).reset_index()
 m['low_n_flag']=m.n_relevant<LOW_N
 m['source_gap']=[SOURCE_GAPS.get((g,mo),'') for g,mo in zip(m.group,m.month)]
 m['weighting']=np.where(m.group=='youtube','unweighted (non-probability sample)','design-weighted ratio estimator')
 m.to_csv(ROOT/'features/media_monthly.csv',index=False)
 # Quarterly version with the same estimator, for groups whose monthly cells are thin (Reddit: 10 coded items a month).
 d['quarter']=pd.PeriodIndex(d.month,freq='M').asfreq('Q').astype(str)
 q=d.groupby(['group','quarter']).apply(month_row).reset_index();q['low_n_flag']=q.n_relevant<LOW_N
 q.to_csv(ROOT/'features/media_quarterly.csv',index=False)
 sf=pd.read_excel(next((ROOT/'corpus/raw/N05').glob('*/news_sentiment_data.xlsx')),sheet_name='Data')
 sf['month']=pd.to_datetime(sf.date).dt.strftime('%Y-%m');sfm=sf.groupby('month')['News Sentiment'].mean().rename('sffed_news_sentiment_mean').reset_index()
 sfm.to_csv(ROOT/'features/sffed_news_sentiment_monthly.csv',index=False)
 nat=m[m.group=='national'].merge(sfm,on='month')
 corr=dict(pearson_net_tone_vs_sffed=float(nat.net_tone.corr(nat.sffed_news_sentiment_mean)),pearson_net_fact_vs_sffed=float(nat.net_fact.corr(nat.sffed_news_sentiment_mean)),months=len(nat),
  pearson_net_tone_vs_sffed_3m_avg=float(nat.net_tone.rolling(3).mean().corr(nat.sffed_news_sentiment_mean.rolling(3).mean())))
 (ROOT/'features/media_monthly_summary.json').write_text(json.dumps(dict(rows=len(m),groups=m.groupby('group').month.agg(['count','min','max']).to_dict('index'),
  low_n_months=m[m.low_n_flag].groupby('group').size().to_dict(),labels=d.relevant.value_counts().to_dict(),sffed_correlation=corr),indent=2))
 print(json.dumps(corr),m.groupby('group').agg(months=('month','count'),rel=('n_relevant','sum'),lown=('low_n_flag','sum')).to_dict('index'))

if __name__=='__main__':main()
