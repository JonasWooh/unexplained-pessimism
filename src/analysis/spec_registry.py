"""Write results/spec_registry.csv: every specification run so far, with status and output file.
status: pre-registered (research/RESEARCH_DESIGN_v1.md), robustness (listed in the design's robustness
table), implementation (a detail the design left open, fixed before results were seen and recorded in
DECISIONS.md), exploratory (not pre-registered; reported as such)."""
import csv,hashlib
from lib import ROOT
R=[]
def add(stage,hyp,model,dv,window,regs,options,status,output):R.append(dict(spec_id=f'S{len(R)+1:03}',stage=stage,hypothesis=hyp,model=model,dv=dv,window=window,regressors=regs,options=options,status=status,output=output))
X1='unrate_rt,pce_yoy_rt,gdp_qoq_saar_rt';XL='unrate_lw,pce_yoy_lw,gdp_qoq_saar_lw';H='pce_cum36_rt,mortgage30_rt_dd,rdpi_pc_yoy_rt,gas_price_rt_dd'
for dv in ['ics','icc','ice']:add(1,'RQ3','M1',dv,'2010-01..2019-12',X1,'HAC12; seasonal dummies if joint p<0.05; MBB block 12 x 2000','pre-registered','stage1_m1/m1_fit.csv; m1_gap_monthly.csv; m1_periods.csv')
for v,o in [('hac_lags_6','HAC6'),('hac_lags_18','HAC18'),('seasonal_excluded','seasonal dummies reversed'),('gdp_yoy','GDP yoy instead of q/q SAAR'),('cutoff_mich_prelim','cutoff = day before Michigan preliminary release'),('first_difference_no_const','first differences without constant, level path cumulated from 2019-12'),('first_difference_with_const','first differences with constant'),('expanding_recursive','expanding window from 2010-01, re-estimated each month')]:
 add(1,'RQ3/H3c','M1','ics','2010-01..2019-12',X1,o,'robustness','stage1_m1/m1_robustness.csv')
for dv in ['ics','icc','ice']:
 for w in ['2010-01..2019-12','2000-09..2019-12','1978-01..2019-12']:add(1,'H3c','M1',dv,w,XL,'pre-1992 GDP: Philadelphia Fed vintage of month t-1; pre-2000-08 PCE: earliest ALFRED vintage','pre-registered','stage1_windows/m1_windows.csv')
for dv in ['ics','icc','ice']:
 add(1,'H1','M1 (common window)',dv,'2010-06..2019-12',X1,'seasonal choice of main M1','implementation','stage1_h1/h1_models.csv')
 for h in H.split(','):add(1,'H1','M1+'+h,dv,'2010-06..2019-12',X1+','+h,'one at a time','pre-registered','stage1_h1/h1_models.csv')
 add(1,'H1','M1+household_all',dv,'2010-06..2019-12',X1+','+H,'all four','pre-registered','stage1_h1/h1_models.csv')
add(1,'H1','M1+household_all+tdsp','ics','2010-06..2019-12',X1+','+H+',tdsp_rt','','robustness','stage1_h1/h1_models.csv')
add(1,'H1','M1+household_all+u6','ics','2011-04..2019-12',X1+','+H+',u6rate_rt','','robustness','stage1_h1/h1_models.csv')
for dv in ['ics','icc','ice']:
 add(1,'H1a','M1 (2000 window)',dv,'2000-09..2019-12',XL,'','exploratory','stage1_h1/h1_models_with_exploratory.csv')
 add(1,'H1a','M1+pce_cum36 (2000 window)',dv,'2000-09..2019-12',XL+',pce_cum36_rt','','exploratory','stage1_h1/h1_models_with_exploratory.csv')
for dv in ['ics','icc','ice']:
 for reg in ['web_step (2024-07+)','mode_web_share']:
  for drop in ['','drop 2024-04..06']:add(1,'H3a','gap ~ '+reg,dv,'2023-01..2025-12',reg,('HAC12; '+drop).strip('; '),'pre-registered','stage1_h3/h3a_mode.csv')
 add(1,'H3a','gap ~ web_step',dv,'2023-01..2025-03','web_step','ends before April 2025 tariff announcements','exploratory','stage1_h3/h3a_mode.csv')
add(1,'H3b','party index minus own 2017-02..2019-12 mean','ics_dem/ind/rep','2017-02..2026-08','','jump = mean(t..t+2) - mean(t-3..t-1) at 2021-01 and 2025-01','pre-registered (jump window: implementation)','stage1_h3/h3b_party_jumps.csv; h3b_party_periods.csv')
add(1,'H3b','party deviation net of aggregate M1 predicted change','ics_dem/ind/rep','2017-02..2026-08','','supplementary column netgap_*','exploratory','stage1_h3/h3b_party_periods.csv')
add(1,'H3b','composition bound ds x (ICS_rep - ICS_rest)','ics','2025-01..2026-10','','ds = 2,4,6 pp; shares by constrained LS on 2017-02..2026-08','pre-registered (shares: implementation)','stage1_h3/h3b_composition_bound.csv')
add(1,'diagnostic','ADF/KPSS and Engle-Granger','ics,icc,ice','2010-01..2019-12',X1,'','implementation','stage1_m1/unit_roots_main_window.csv')
# ---------- stage 2 (measurement validation and benchmarks) ----------
add(2,'RQ1/R3.5','LLM vs LM, VADER, keyword rules, TF-IDF+LR (LLM-trained, dev-trained)','relevant,tone_overall,price_frame,T01-T13','260-item test set','','dictionary cut-offs on dev; sets A and B; 2,000 item bootstraps','pre-registered','stage2_r35/item_metrics.csv; item_per_class.csv; topics_summary.csv')
add(2,'RQ1/R3.5','set-B kappa counts an LLM not-relevant as its own category','tone_overall,price_frame,topics','260-item test set','','','implementation','stage2_r35/item_metrics.csv')
add(2,'RQ1/R3.5','full-frame dictionary index (TF-IDF relevance, cross-fitted; LM and VADER tone)','dict_net_tone_lm,dict_net_tone_vader','2010-01..2026-10','','correlations with LLM index and SF Fed; levels, 3-month means, first differences','pre-registered (cross-fitting: implementation)','stage2_dictindex/correlations.csv; features/media_dict_monthly.csv')
add(2,'RQ1/R3.5','LM dictionary on the LLM-sampled units only','dict_net_tone_lm_llmsample','2010-01..2026-10','','separates method from sample size','exploratory','stage2_dictindex/correlations.csv')
add(2,'RQ1/R3.7','flip rates O2/S/F/M vs O1, excess = V - O2','13 coded dimensions','120 items','','paired item bootstrap 2,000','pre-registered','stage2_r37/flip_rates.csv')
add(2,'RQ1/R3.7','directional tests: tone score and admin blame, S - O2 by swap direction; F - M','tone score, admin blame','120 items','','bootstrap within strata','pre-registered (S - O2 contrast: implementation)','stage2_r37/directional.csv')
add(2,'RQ1','fact calibration vs ALFRED vintage at publication','unemployment, inflation (CPI/PCE), GDP, payrolls','claim_text, all coded groups','','tolerance 0.1 pp (payrolls 1k); CPI 12-month 0.2 sensitivity; inflation measure must be named (rules revised after the 30-claim manual check)','pre-registered (CPI 0.2: robustness; parse rules: implementation)','stage2_factcal/claims.csv; summary.csv')
for nm in ['main (1-month changes)','with lagged tone','excluding 2020-03..2020-12','3-month changes']:
 add(2,'H2a','net_tone ~ bad/good parts of dU, dpi, dg','net_tone (national)','2010-01..2026-09','U_bad,U_good,pi_bad,pi_good,g_bad,g_good',nm,'pre-registered' if nm.startswith('main') else 'implementation','stage2_bias/tone_asymmetry.csv')
for ch in ['1-month changes','3-month changes']:add(2,'R3.3 selection','topic share ~ rising / falling part of dpi, dU','prices_rising, inflation_easing, layoffs, hiring','2010-01..2026-09','',ch+'; MBB 12 x 2,000','pre-registered' if ch.startswith('1') else 'implementation','stage2_bias/topic_selection.csv')
add(2,'R3.3 framing','frame shares ~ pi + post-peak (+ cum36)','price_level_share_of_priced, household_share, price_frame_share','2010-01..2026-09','pi_end,cum36_end,post_peak','peak = real-time PCE peak 2021-2023','pre-registered (specification: implementation)','stage2_bias/framing.csv')
add(2,'R3.3 attribution','admin shares ~ fundamentals + administration dummies','blame_admin_share, credit_admin_share','2010-01..2026-09','U_end,pi_end,g_end,trump1,biden,trump2','Wald equal administrations','pre-registered','stage2_bias/attribution.csv')
add(2,'R3.3 cross-source','group minus national on common months (Reddit quarters)','9 content metrics','group windows','','item bootstrap within group x cell','pre-registered','stage2_bias/cross_source.csv')
add(2,'R3.3 reliability','within-month bootstrap reliability; SF Fed checks (3-month, Guardian full text, macro topics)','net_tone, net_fact','2010-01..2026-10','','fpc and no fpc','pre-registered','stage2_reliability/reliability.csv; sffed_checks.csv')
# ---------- stage 3 (forecast comparison) ----------
for h in (1,3):
 for ar in ('AR','no AR'):
  for s,bg in [('M1','M2'),('M1','M1c'),('M1c','M3'),('M1','M3')]:
   add(3,'H2b/RQ5',f'{s} vs {bg}','ics',f'expanding from 2010-06; eval 2017-01..2026-10; h={h}','see stage3_forecast.py',f'{ar}; month dummies; Clark-West; MBB RMSE ratio','pre-registered'+(' (AR primary: implementation, set before results)' if ar=='AR' and h==1 and s=='M1c' else ''),'stage3_forecast/comparisons.csv')
for ar in ('AR','no AR'):
 add(3,'secondary media','M1 + one of six media variables (lag 1-3 by BIC) and PC1','ics','expanding from 2010-06','',f'{ar}; BH q=0.10','pre-registered','stage3_forecast/secondary.csv')
add(3,'H2b','in-sample gamma of M2/M3','ics','2010-06..2026-10; 2010-06..2019-12','','HAC 6/12/18; AR and no AR','pre-registered','stage3_forecast/media_coefficients.csv')
for v in ['DV ICC','DV ICE','cutoff = Michigan preliminary release','GDP yoy','first differences','excluding 2020-03..2020-12','web-mode step dummy','drop 2024-04..06','media: tone 3-month mean','media: net_fact','media: share_negative','media: SF Fed index','media: full-frame LM dictionary','media: NYT only net_tone','media: media months 2026-01 and 2026-10 missing','media: EPU (real-time)','tone lag 1-3 by BIC','month dummies excluded']:
 add(3,'H2b robustness','M1 vs M2; M1c vs M3; gamma of M3','ics' if not v.startswith('DV') else v[3:].lower(),'expanding from 2010-06',v,'AR and no AR','robustness','stage3_robustness/variants.csv')
add(3,'H2b','excess tone = residual on U, pi, g, H and month t-1 news, per window','ics','expanding from 2010-06','','literal residual on U, pi, g is identical by FWL; deviation','pre-registered (fundamentals set: deviation)','stage3_robustness/variants.csv')
add(3,'stability','60-month rolling gamma; gamma shift at 2020-03, 2024-07, 2025-01; VIF','ics','2010-06..2026-10','M3','HAC 12','pre-registered (shift test form: implementation)','stage3_robustness/rolling_gamma.csv; gamma_breaks.csv; vif.csv')
add(3,'magnitude','gamma(M3, 2010-06..2019-12) x tone deviation from 2019 / stage 1 gap','ics','gap periods','','AR long-run gamma/(1-rho)','pre-registered','stage3_robustness/magnitude.csv')
# ---------- stage 4 (time order and falsification) ----------
for sp,st in [('main: X, surprises, events','pre-registered (event and surprise definitions: implementation)'),('X only','implementation'),('excluding 2020-03..2020-12','robustness')]:
 for d in ('forward','reverse'):
  add(4,'H2c/RQ2/falsification 3',f'local projection {d}, h=0..6 and average 0-6','ics (z)' if d=='forward' else 'net_tone (z)','2010-06..2026-10',sp,'HAC 12; month dummies; average-horizon one-sided 5% = summary test (set before results)',st,'stage4_timing/local_projections.csv')
for w in ('2010-01..2019-12','2010-01..2026-10'):
 add(4,'falsification 1','net_tone ~ U, pi, g, H (end-of-month real-time); mean residual by period','net_tone (national)',f'fit {w}; test 2021-01..2026-10 and sub-periods','U,pi,g,'+H,'HAC 12','pre-registered' if w.startswith('2010-01..2019') else 'robustness','stage4_timing/excess_tone_since_2021.csv')
for w in ('2010-06..2026-08','2010-06..2024-03'):
 add(4,'H2d/falsification 6','recall path: news_u_all ~ tone_l1 | X (unique R2); ICS ~ news_u_all; topic correspondence with placebo','news_u_all, newsrn_u_pri_all, newsrn_u_emp_all, ics',w,'tone_l1, topic_prices_rising_l1, topic_layoffs_l1, X','HAC 12; month dummies; web dummy after 2024-06','pre-registered' if w.endswith('2026-08') else 'robustness','stage4_timing/recall_unique_r2.csv; recall_regressions.csv')
add(4,'RQ2 partisan','ics_g ~ tone_l1 | X, own lag, rep_admin; Dem - Rep stacked','ics_dem/ind/rep','2017-02..2026-08','tone_l1,'+X1,'HAC 12; month dummies','pre-registered (stacked contrast: implementation)','stage4_timing/partisan_gamma.csv')
add(4,'falsification 7','group gap shapes: age 18-34 vs 55+ (group M1 gaps), Dem vs Rep (own 2017-02..2019-12 mean)','ics_a1834/a5597, ics_dem/rep','2021-01..2026-08','','mean difference HAC 12; correlation of gap paths','pre-registered (gap definitions: implementation)','stage4_timing/group_gap_differences.csv; group_gaps_monthly.csv')
# added after the stage 2 freeze (kept at the end so earlier spec ids do not move)
add(2,'RQ1','unnamed-measure inflation figures vs every admissible reading (CPI/PCE x 12-month/1-month)','inflation','claim_text, all coded groups','','descriptive only, not in error rates','exploratory','stage2_factcal/unnamed_inflation.csv')
# ---------- stage 5 (mechanisms, heterogeneity, method) ----------
for sp in ['main: 1-month, 2010-02..2026-10','excluding 2020-03..2021-06','2010-02..2019-12','3-month changes, excluding 2020-03..2021-06']:
 add(5,'RQ4 negativity (confidence side)','dICS ~ bad and good parts of data news (U, pi, g)','ics change',sp,'bad/good parts','HAC 12; month dummies; test beta_bad + beta_good = 0','pre-registered' if sp.startswith('main') else 'implementation','stage5_mechanisms/negativity_confidence.csv')
for mech,regs in [('availability','gas_price_rt_dd,food_cpi_yoy_rt'),('anchoring','pce_cum36_rt'),('both','gas_price_rt_dd,food_cpi_yoy_rt,pce_cum36_rt')]:
 for w in ['2010-06..2019-12','2010-06..2026-10 without 2020-03..2021-06']:
  add(5,'RQ4 '+mech,'ICS ~ X + '+regs,'ics',w,X1+','+regs,'HAC 12; month dummies; gap recomputed from the 2010-2019 fit','pre-registered' if mech!='both' else 'implementation','stage5_mechanisms/competition_regressions.csv; competition_gap_reduction.csv')
add(5,'RQ4 anchoring','reasons citing high prices ~ pce_yoy + pce_cum36 + U + web step','pagorn_hp_all, durrn_hp_all, vehrn_hp_all, homrn_hp_all','2010-06..2026-08 without 2020-03..2021-06','pce_yoy_rt,pce_cum36_rt,unrate_rt,web','HAC 12; month dummies','pre-registered (specification: implementation)','stage5_mechanisms/price_reasons.csv; price_reasons_periods.csv')
add(5,'R5.2','group M1 gaps by income, age, region, education; differences vs reference group','ics/icc/ice by group','fit 2010-01..2019-12; gaps to 2026-08','X1','HAC 12; month dummies','pre-registered','stage5_mechanisms/group_gaps.csv; group_gap_differences.csv; group_gaps_monthly.csv')
add(5,'R5.3','web step in survey-side measures; gap change within the web era','news_u_all, newsrn_u_pri_all, pagorn_hp_all, px1_med_all; ics/icc/ice gaps','2023-01..2025-12; 2024-07..2026-08','web, X1','HAC 12; with and without 2024-04..06','pre-registered (measures: implementation)','stage5_mechanisms/mode_steps.csv; mode_gap_changes.csv')
add(5,'R5.4','midterm years Jan-Apr vs May-Oct; dGap ~ midterm and presidential pre-election dummies','ics gap, net_tone','2010-02..2026-10 without 2020-03..2021-06; 2010-02..2019-12','mid_pre, pres_pre','HAC 12; month dummies','pre-registered (specification: implementation)','stage5_mechanisms/pre_election_years.csv; pre_election_regression.csv')
add(5,'recent sources','tone (t-1) vs ICS gap: YouTube, local, Media Cloud monthly; Reddit quarterly','ics gap','each source window','net_tone','levels and first differences; national on the same months','pre-registered (descriptive)','stage5_mechanisms/recent_sources.csv')
out=ROOT/'results/spec_registry.csv'
with open(out,'w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(R[0]));w.writeheader();w.writerows(R)
sh=ROOT/'results/script_sha256.csv'
with open(sh,'w',newline='') as f:
 w=csv.writer(f);w.writerow(['file','sha256'])
 for p in sorted((ROOT/'src/analysis').glob('*.py'))+sorted((ROOT/'src/analysis').glob('*.sh')):w.writerow([str(p.relative_to(ROOT)),hashlib.sha256(p.read_bytes()).hexdigest()])
print(out,len(R))
