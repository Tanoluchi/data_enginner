import argparse
from asyncore import write
import logging
import re
import csv
import datetime as dt

from requests.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError

import news_page_objects as news

from common import config

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
is_well_formed_link = re.compile(r'^https?://.+/.+$') # https://example.com/hello
is_root_path = re.compile(r'^/.+$') # /some-text


def _news_scraper(news_site_uid):
    """Aquí inicia el scraper, trayendo las url"""
    host = config()['news_sites'][news_site_uid]['url']
    
    logging.info(f'Beginning scraper for {host}')
    logging.info('Finding links in homepage...')
    homepage = news.HomePage(news_site_uid, host)
    
    articles = []
    for link in homepage.article_links:
        article = _fetch_article(news_site_uid, host, link)
        
        if article:
            logger.info('Article fetched!!')
            articles.append(article)
        
    _save_articles(news_site_uid, articles)
    
def _save_articles(news_site_uid, articles):
    now = dt.datetime.now().strftime('%Y_%m_%d')
    out_file_name = f'{news_site_uid}_{now}_articles.csv'
    csv_headers = list(filter(lambda property: not property.startswith('_'),
                         dir(articles[0])))
    print(csv_headers)
    
    with open(out_file_name, mode='w+', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        
        for article in articles:
            row = [str(getattr(article, prop)) for prop in csv_headers]
            writer.writerow(row)

def _fetch_article(news_site_uid, host, link):
    """ Se comienza a screpear los articulos,
    y a mirar si tienen cuerpo"""
    logger.info(f'Start fetching article at {link}')

    article = None
    try:
        article = news.ArticlePage(news_site_uid, _build_link(host, link))
    except (HTTPError, MaxRetryError) as e:
        logger.warning('Error while fetchting the article', exc_info=False)
        
    if article and not article.body:
        logger.warning('Invalid article. There is no body')
        return None
    
    return article
    
def _build_link(host, link):
    """Se hace una reconstrucción de los links,
    ya que aveces llegan relativos"""
    if is_well_formed_link.match(link):
        return link
    elif is_root_path.match(link):
        return f'{host}{link}'
    else:
        return f'{host}/{link}'
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    new_site_choices = list(config()['news_sites'].keys())
    parser.add_argument('news_site', 
                        help='The news site that you want to scrape',
                        type=str,
                        choices=new_site_choices)
    
    args = parser.parse_args()
    print(args.news_site)
    _news_scraper(args.news_site)