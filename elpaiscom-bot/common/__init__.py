import calendar
import json
import random
from urllib.parse import urlparse, parse_qs

import math
import pytz
from bs4 import BeautifulSoup

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
    return round(math.log(norm_ups) + seconds / (2 * 3600.0), 7)


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


def clean_comment(raw_body):
    body = ' '.join(raw_body.replace('\n', ' ').replace('\r', '').split())
    return BeautifulSoup(body, "html.parser").text


def fetch_elpaiscom_comments(url, session):
    comments = []
    response = session.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    # <div class="articulo-comentarios-iframe">
    element = soup.find('div', attrs={"class": 'articulo-comentarios-iframe'})
    if element is not None:
        script = element.find('script', attrs={'src': True})
        if script is not None:
            raw_url = 'https:' + script['src']
            session.headers['referer'] = url
            response = session.get(raw_url)
            if response.status_code == 200:
                referer = response.url

                parsed_url = urlparse(raw_url)
                params = parse_qs(parsed_url.query)
                post_id = params['ghi'][0]

                session.headers['referer'] = referer

                rnd = str(random.random())
                comments_url = 'https://elpais.com/Outeskup?s=&rnd=' + rnd + '&th=2&msg=' + post_id + '&p=1&nummsg=80&tt=mv'

                response = session.get(comments_url)
                if response.status_code == 200:
                    raw_comments = json.loads(response.text)
                    if raw_comments is not None:

                        for raw_comment in raw_comments['mensajes']:
                            if raw_comment['idMsgRespuesta'] == post_id:  # Otherwise is a reply
                                body = clean_comment(raw_comment['contenido'])
                                if is_comment_ok_for_twitter(body):
                                    if 'valoracion_positive' not in raw_comment:
                                        raw_comment['valoracion_positive'] = 0
                                    if 'valoracion_negative' not in raw_comment:
                                        raw_comment['valoracion_negative'] = 0
                                    comment = {
                                        'comment_id': raw_comment['idMsg'],
                                        'url': url,
                                        'post_id': post_id,
                                        'posted_at': raw_comment['tsMensaje'],
                                        'ups': raw_comment['valoracion_positive'],
                                        'downs': raw_comment['valoracion_negative'],
                                        'heat': 0,
                                        'body': body
                                    }
                                    comment['heat'] = heat(comment['ups'], comment['downs'], comment['posted_at'])
                                    comments.append(comment)
    return comments
