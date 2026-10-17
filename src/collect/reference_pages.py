from common import *
PAGES=[
 ('M12','https://www.policyuncertainty.com/us_monthly.html','us_monthly.html'),
 ('M13','https://www.atlantafed.org/','atlanta.html'),
 ('M17','https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/real-time-data-set-for-macroeconomists','realtime.html'),
 ('N05','https://www.frbsf.org/research-and-insights/data-and-indicators/daily-news-sentiment-index/','news_sentiment.html'),
 ('R01','https://www.bea.gov/news/schedule','bea_schedule.html'),
 ('R02','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm','fomccalendars.htm'),
 ('R04','https://www.pewresearch.org/internet/2025/11/20/americans-social-media-use-2025/','social_media_2025.html'),
 ('R05','https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/survey-of-professional-forecasters','spf.html'),
]
if __name__=='__main__':
 for ds,u,n in PAGES:
  p=fetch(ds,u,n)
  for t,link in links(p,u):
   if any(x in link.lower() for x in ['.xlsx','.xls','.csv','.zip','affordab','historical-data']):print(ds,t[:70],link,flush=True)
