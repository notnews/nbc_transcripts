import sys
import scrapelib
from bs4 import BeautifulSoup
from dateutil import parser
import re
import csv

BASE_URL = 'http://www.nbcnews.com'

all_links = set()
visited = set()

def crawl_full_archive(url):
    if url in visited:
        print("Count: %d" % len(all_links))
        return
    visited.add(url)
    res = s.urlopen(BASE_URL + url)
    soup = BeautifulSoup(res)
    print soup.title.text
    # Link to contents
    for th in soup.find_all('div', {'class': 'textHang'}):
        link = th.find('a')
        if not link.has_attr('ce') or link['ce'] == 'Highlight1':
            href = link['href']
            #print href
            all_links.add(href)
    # Get links to all archive
    archive = soup.find('div', {'cn': 'Archive'})
    if archive:
        for a in archive.find_all('a'):
            href = a['href']
            crawl_full_archive(href)

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding("utf-8")

    s = scrapelib.Scraper(requests_per_minute=60)

    start_url = BASE_URL + '/id/3719710'

    res = s.urlopen(start_url)
    soup = BeautifulSoup(res)
    print soup.title.text
    # Link to contents
    for th in soup.find_all('div', {'class': 'textHang'}):
        link = th.find('a')
        if not link.has_attr('ce') or link['ce'] == 'Highlight1':
            href = link['href']
            #print href
            all_links.add(href)

    # Link to Full archive
    for ts in soup.find_all('div', {'class': 'textSmall'}):
        url = ts.find('a')['href']
        #print url
        crawl_full_archive(url)

    print "Total: %d" % len(all_links)
    f = open('all_links.csv', 'wb')
    for href in all_links:
        f.write("%s\n" % href)
    f.close()
