"""Hand-off layout (task_guide 6.1): labels/ and codebook/ from annotation/, and YouTube video-level metadata."""
import csv,json,shutil,glob
from pathlib import Path
import pandas as pd,openpyxl
ROOT=Path(__file__).resolve().parents[2];ANN=ROOT/'annotation';LAB=ROOT/'labels';CB=ROOT/'codebook'

def sheet_rows(path,sheet):
 ws=openpyxl.load_workbook(path,read_only=True)[sheet];rows=list(ws.iter_rows(values_only=True))
 return [dict(zip(rows[0],r)) for r in rows[1:] if r[0]]

def main():
 LAB.mkdir(exist_ok=True);(LAB/'ai').mkdir(exist_ok=True);CB.mkdir(exist_ok=True)
 key=pd.read_csv(ANN/'sample_key_DO_NOT_SHOW_ANNOTATORS.csv')
 key[['item_id','split','date','unit_type','context','text']].to_csv(LAB/'sample_for_annotation.csv',index=False)
 key.to_csv(LAB/'sample_key.csv',index=False)
 for who in 'AB':
  rows=[dict(sheet=s,**r) for s in ['calibration','main'] for r in sheet_rows(ANN/f'annotation_workbook_{who}.xlsx',s)]
  pd.DataFrame(rows).drop(columns=['date','unit_type','context','text']).to_csv(LAB/f'annotator_{who}.csv',index=False)
  tl=[r for r in sheet_rows(ANN/f'annotation_workbook_{who}.xlsx','time_log') if any(v not in (None,'') for k,v in r.items() if k!='session')]
  pd.DataFrame(tl).to_csv(LAB/f'annotator_{who}_time_log.csv',index=False)
 shutil.copy2(ANN/'gold_standard_v1.csv',LAB/'adjudicated.csv');shutil.copy2(ANN/'gold_calibration_v1.csv',LAB/'adjudicated_calibration.csv')
 shutil.copy2(ANN/'agreement/adjudication_disagreements.xlsx',LAB/'adjudication_log.xlsx')
 for f in ['agreement_summary.csv','confusion_matrices.csv','gold_overview.json']:shutil.copy2(ANN/'agreement'/f,LAB/f)
 for f in ['sampling_design.json','sampling_frame_sizes.csv']:shutil.copy2(ANN/f,LAB/f)
 shutil.copy2(ANN/'codebook_v1.md',CB/'codebook.md')
 # examples.md: up to three gold calibration/main item ids per label value, with a short excerpt.
 gold=pd.read_csv(LAB/'adjudicated.csv',dtype=str).fillna('');txt=key.set_index('item_id').text
 lines=['# 标签示例（来自金标准，供手册对照）','','每个取值最多列 3 条金标准条目；摘录为单位文本前 30 词。完整文本见 labels/sample_for_annotation.csv。','']
 dims=['relevant','tone_overall','fact_direction','emotional_intensity','price_frame','perspective','time_frame','numeric_claim','definition_error','actor_1','direction_1']
 for d in dims:
  lines.append(f'## {d}');lines.append('')
  for v in sorted(x for x in gold[d].unique() if x):
   ids=gold[gold[d]==v].item_id.head(3)
   lines.append(f'**{v}**（金标准 {int((gold[d]==v).sum())} 条）')
   for i in ids:lines.append(f'- {i}：'+' '.join(str(txt[i]).split()[:30]).replace('|','/')+' …')
   lines.append('')
 (CB/'examples.md').write_text('\n'.join(lines))
 # YouTube video-level metadata (consumption/engagement proxy, R2.4).
 freeze=Path(sorted(glob.glob(str(ROOT/'provenance/youtube_freeze_v1_*')))[-1])
 st=json.loads((ROOT/'provenance/youtube_claude_state.json').read_text())['stats']
 cand=pd.read_csv(freeze/'youtube_claude_candidates.csv',dtype=str);cand=cand[cand.main_set=='True']
 man=pd.read_csv(freeze/'youtube_comment_videos_manifest.csv',dtype=str).set_index('video_id')
 ch=pd.read_csv(ROOT/'provenance/youtube_channels.csv',dtype=str).set_index('channel_id')
 rows=[]
 for _,r in cand.iterrows():
  s=st.get(r.video_id,{})
  rows.append(dict(video_id=r.video_id,channel_id=r.channel,channel=ch.name.get(r.channel),channel_group=ch.collection_group.get(r.channel),published_utc=r.published,title=r.title,routes=r.routes,
   search_only_supplement=r.search_only_supplement,available=s.get('available'),view_count=s.get('views'),comment_count_snapshot=s.get('comment_count'),duration=s.get('duration'),
   comments_collected=r.video_id in man.index,window_comments=man.window_comments.get(r.video_id),stats_retrieved='2026-10-15 (videos.list snapshot)'))
 (ROOT/'data/processed').mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(ROOT/'data/processed/youtube_videos.csv',index=False)
 print('labels, codebook, youtube_videos written',len(rows))

if __name__=='__main__':main()
