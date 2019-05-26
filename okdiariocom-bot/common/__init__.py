import calendar
import json

import math
import pytz
import requests

user_agents = [
    # Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    # Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
]


def dt2ts(dt):
    mytz = pytz.timezone('Europe/Madrid')
    dt = mytz.normalize(mytz.localize(dt, is_dst=True))
    return calendar.timegm(dt.utctimetuple())


def heat(ups, downs, timestamp):
    norm_ups = inv_best(best(ups + 1, downs))
    norm_ups = max(ups - downs, 1)

    seconds = timestamp - 316710600
    return round(math.log(norm_ups) + seconds / (6 * 3600.0), 7)


def best(ups, downs):
    n = ups + downs
    if n <= 0:
        return 0.0
    z = 1.96
    phat = 1.0 * ups / n
    return (phat + z * z / (2 * n) - z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)) / (1 + z * z / n)


def inv_best(best):
    if best <= 0:
        return 0.0
    z = 1.96
    ups = -(best * z * z) / (best - 1)
    return ups


def is_comment_ok_for_twitter(body):
    if len(body) > 280 - 24:
        return False
    if '#' in body:
        return False
    if '@' in body:
        return False
    return True


def fetch_okdiariocom_comments(url, disqus_api_key, cursor=None):
    disqus_url = 'https://disqus.com/api/3.0/threads/listPosts.json?api_key=' + disqus_api_key + '&limit=100&forum=okdiario&thread=link:' + url
    if cursor is not None:
        disqus_url = disqus_url + '&cursor=' + cursor
    response = requests.get(disqus_url)
    if response.status_code != 200:
        return []
    disqus_response = json.loads(response.text)
    if disqus_response['code'] != 0:
        return []
    if disqus_response['response'] is None:
        return []
    if not disqus_response['response']:
        return []

    disqus_comments = disqus_response['response']
    if disqus_response['cursor']['hasNext']:
        disqus_comments.append(fetch_okdiariocom_comments(url, disqus_api_key, disqus_response['cursor']['next']))
    return disqus_comments
