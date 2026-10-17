from common import *

PAGES=[
 ('S05','https://www.sca.isr.umich.edu/tables.html','tables.html'),
 ('S05','https://data.sca.isr.umich.edu/tables.php','tables.php.html'),
 ('S05','https://data.sca.isr.umich.edu/survey-description.php','survey-description.html'),
 ('M01','https://fred.stlouisfed.org/docs/api/fred/series_observations.html','api_observations.html'),
 ('M01','https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html','api_vintagedates.html'),
 ('M01','https://fred.stlouisfed.org/docs/api/terms_of_use.html','terms.html'),
 ('N01','https://developer.nytimes.com/faq','developer_faq.html'),
 ('N02','https://open-platform.theguardian.com/access/','access.html'),
 ('N02','https://www.theguardian.com/open-platform/terms-and-conditions','terms.html'),
 ('N03','https://www.mediacloud.org/documentation/search-api-guide','api_guide.html'),
 ('SM01','https://developers.google.com/youtube/v3/determine_quota_cost','quota.html'),
 ('SM01','https://developers.google.com/youtube/terms/developer-policies','policies.html'),
]
if __name__=='__main__':
 for ds,url,name in PAGES:
  fetch(ds,url,name)
