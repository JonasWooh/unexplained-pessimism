from common import *
import collections

def write(name,rows):
 if not rows:return
 with (PROV/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

def main():
 folder=ROOT/'corpus/raw/SM01'/DAY;channels=[];coverage=[];months=[]
 states={x['channel']:x for x in json.loads((PROV/'youtube_inventory_state.json').read_text())}
 for p in sorted(folder.glob('channel_*.json')):
  for ch in json.loads(p.read_bytes()).get('items',[]):
   cid=ch['id'];title=ch['snippet']['title'];channels.append(dict(channel_id=cid,name=title,country=ch['snippet'].get('country',''),collection_group='local' if title in ['11Alive','FOX 10 Phoenix'] else 'national',state='not_verified',selection_reason='Institutional news channel; no political stance inferred'))
   videos=[]
   for f in folder.glob(f'uploads_{cid}_*.json'):videos.extend(json.loads(f.read_bytes())['items'])
   ids=[v['contentDetails']['videoId'] for v in videos];dates=[v['contentDetails']['videoPublishedAt'] for v in videos if v['contentDetails'].get('videoPublishedAt')]
   coverage.append(dict(channel_id=cid,name=title,inventory_rows=len(videos),unique_videos=len(set(ids)),earliest=min(dates,default=''),latest=max(dates,default=''),reached_2023_boundary=bool(dates and min(dates)<'2023-01-01'),playlist_ended_without_2023=bool(dates and min(dates)>='2023-01-01' and not states[cid]['token']),next_page=states[cid]['page']))
   for period,n in sorted(collections.Counter(d[:7] for d in dates).items()):months.append(dict(channel_id=cid,month=period,rows=n))
 write('youtube_channels.csv',channels);write('youtube_coverage.csv',coverage);write('youtube_monthly_inventory_counts.csv',months)
 groups=collections.defaultdict(list)
 for p in folder.glob('comments_*.json'):groups[p.name[len('comments_'):].rsplit('_',1)[0]].append(p)
 statuses=[]
 for vid,paths in groups.items():
  paths.sort();objs=[json.loads(p.read_bytes()) for p in paths];a=[x for o in objs for x in o['items']];dates=[x['snippet']['topLevelComment']['snippet']['publishedAt'] for x in a]
  token=bool(objs[-1].get('nextPageToken'));status='2000_cap' if token and len(paths)==20 else 'partial_paused' if token else 'complete_top_level_metadata'
  statuses.append(dict(video_id=vid,pages=len(paths),rows=len(a),status=status,earliest=min(dates,default=''),latest=max(dates,default=''),text_collected=False,author_fields_collected=False))
 write('youtube_comment_status.csv',statuses)
 text_groups=collections.defaultdict(list)
 for p in folder.glob('comment_text_*.json'):text_groups[p.name[len('comment_text_'):].rsplit('_',1)[0]].append(p)
 text_status=[]
 for vid,paths in text_groups.items():
  paths.sort();objs=[json.loads(p.read_bytes()) for p in paths];items=[x for o in objs for x in o.get('items',[])];dates=[x['snippet']['topLevelComment']['snippet']['publishedAt'] for x in items]
  token=bool(objs[-1].get('nextPageToken'))
  text_status.append(dict(video_id=vid,pages=len(paths),rows=len(items),unique_comments=len({x['snippet']['topLevelComment']['id'] for x in items}),status='partial' if token else 'complete_top_level',earliest=min(dates,default=''),latest=max(dates,default=''),text_collected=True,author_fields_collected=False))
 write('youtube_comment_text_status.csv',text_status)
 errors=[e for e in (json.loads(line) for line in (PROV/'requests.jsonl').read_text().splitlines()) if e.get('dataset_id')=='SM01' and e.get('api_reasons')]
 (PROV/'youtube_api_errors.json').write_text(json.dumps(errors,indent=2))
 print('Channels',len(channels),'comment videos',len(statuses),'comment pages',sum(len(a) for a in groups.values()))

if __name__=='__main__':main()
