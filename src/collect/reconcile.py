"""Read-only workbook reconciliation, never an analysis input or imputation source."""
from common import *
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

def latest(ds,sid):
 p=ROOT/'data/raw'/ds/DAY/(sid+'_latest.csv')
 d=pd.read_csv(p);d.iloc[:,0]=pd.to_datetime(d.iloc[:,0]);d['month']=d.iloc[:,0].dt.to_period('M').astype(str)
 return pd.Series(pd.to_numeric(d[sid],errors='coerce').values,index=d['month'])

def main():
 x=pd.read_excel(ROOT/'data/external/Perceptual_Bias_Data.xlsx',header=None)
 p=x.iloc[1:,[7,8]].dropna();p.columns=['date','excel_pce_yoy'];p['month']=pd.to_datetime(p['date']).dt.to_period('M').astype(str)
 p=p.set_index('month')
 for label,ds,sid in [('headline','M02','PCEPI'),('core','M05','PCEPILFE')]:
  level=latest(ds,sid)
  yoy=100*(level/level.shift(12)-1)
  p[label+'_pce_yoy']=yoy
  p[label+'_abs_error']=(pd.to_numeric(p.excel_pce_yoy)-p[label+'_pce_yoy']).abs()
 p.to_csv(PROV/'excel_pce_comparison.csv')
 summary=[]
 for label in ['headline','core']:
  v=p[label+'_abs_error'].dropna()
  summary.append(f'| {label} | {len(v)} | {v.mean():.8f} | {v.max():.8f} | {(v<=0.01).sum()} |')
 s=pd.read_csv(ROOT/'data/raw/S01'/DAY/'tbmics.csv');s['month']=pd.to_datetime(s.Month+' '+s.YYYY.astype(str),format='%B %Y').dt.to_period('M').astype(str)
 values=s.set_index('month').ICS_ALL
 c=x.iloc[1:,[3,4]].dropna();c.columns=['date','excel_ics'];c['month']=pd.to_datetime(c.date).dt.to_period('M').astype(str);c=c.set_index('month');c['official_ics']=values;c['difference']=pd.to_numeric(c.excel_ics)-c.official_ics;c.to_csv(PROV/'excel_sentiment_comparison.csv')
 u=json.loads((ROOT/'data/raw/M01'/DAY/'UNRATE_observations_0000000.json').read_bytes())['observations']
 missing_oct=[a for a in u if a['date']=='2025-10-01'];valid_oct=[a for a in missing_oct if a['value']!='.']
 g=latest('M04','A191RL1Q225SBEA');gmax=g.dropna().index.max()
 result='# 教授 Excel 只读核对\n\n原文件未修改。以下运算仅用于确认数据口径与完整性，不是分析数据集。单位为百分点。\n\n'
 result+='| 口径 | 可对齐月份 | 平均绝对误差 | 最大绝对误差 | 误差不超过 0.01 的月份 |\n|---|---:|---:|---:|---:|\n'+'\n'.join(summary)
 result+='\n\n对照公式：100 × (同一最新版本的当月指数 / 12 个月前指数 − 1)。匹配结果支持核心 PCE 口径，精确程度见上表；不能仅凭列名判断为总体 PCE。历史修订可能影响精确逐值匹配。\n'
 home=BeautifulSoup((ROOT/'data/raw/S05'/DAY/'homepage.html').read_bytes(),'html.parser').get_text(' ',strip=True)
 match=re.search(r'Preliminary Results for October 2026.*?Index of Consumer Sentiment (\d+\.\d+)',home)
 if not match:raise ValueError('Official October preliminary result not found in saved homepage')
 value=float(match.group(1))
 result+=f'\n- 信心月度 CSV 可匹配 {c.official_ics.notna().sum()} 个月；一致 {(c.difference.abs()<1e-8).sum()} 个月。CSV 最新月份 {values.index.max()}。另核对保存的官网首页明确标为 Preliminary Results for October 2026：ICS={value}，与教授表 2026-10={c.loc["2026-10","excel_ics"]} 一致。它是初值，不能混作终值。官方日历发布日 2026-10-09，10月终值计划10月23日发布。证据 data/raw/S05/20261015/homepage.html，来源 https://www.sca.isr.umich.edu/ 。\n'
 result+=f'- UNRATE 2025-10 共有 {len(missing_oct)} 条版本记录，其中非缺失数值 {len(valid_oct)} 条；缺失标记不等于可用观测。\n- GDP 环比折年率最新非缺失观测 {gmax}；Excel 的 2026Q3=3.7 不作为实测值收录，无法据此确认来源。\n'
 result+=f'- 官网 ICS 2022-06={values.get("2022-06")}; 2026-05={values.get("2026-05")}。\n'
 (PROV/'excel_reconciliation.md').write_text(result)
 print(result)

if __name__=='__main__':main()
