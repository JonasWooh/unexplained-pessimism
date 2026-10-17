"""First-day YouTube channel inventory; response fields exclude personal profiles."""
from common import *
HANDLES=['CNN','FoxNews','NBCNews','ABCNews','CBSNews','CNBC','markets','PBSNewsHour','11Alive','FOX10Phoenix','Local4']
LICENSE='YouTube API policies: non-authorized data must be refreshed or deleted within 30 days; no indefinite immutable archive. No personal author fields requested.'
if __name__=='__main__':
 for handle in HANDLES:
  p=fetch('SM01','https://www.googleapis.com/youtube/v3/channels',f'channel_{handle}.json',{'forHandle':handle,'part':'snippet,contentDetails,statistics','fields':'items(id,snippet(title,country),contentDetails/relatedPlaylists/uploads,statistics),pageInfo'},key='youtube',keyparam='key',license_note=LICENSE)
  if p is None:break
