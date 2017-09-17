import sys
import scrapelib
from bs4 import BeautifulSoup
from dateutil import parser
import re
import csv

columns = ['url',
           'channel.name',
           'program.name',
           'uid',
           'duration',
           'year',
           'month',
           'date',
           'time',
           'timezone',
           'path',
           'wordcount',
           'subhead',
           'updated',
           'text']

BASE_URL = 'http://www.nbcnews.com'


def extract_transcript(html):
    program = ""
    tz = ""
    date = None
    soup = BeautifulSoup(html)
    title = soup.find('h1', {'class': 'entry-title'})
    m = re.match(r"'?(.*?)'?\s*(?:,|for)\s+(.*)", title.text.strip())
    if m:
        program = m.group(1)
        date = m.group(2)
        date = date.replace('Thusday', 'Thursday')
        print program, date
        try:
            date = parser.parse(date)
        except:
            date = None
            pass
        tz = ""

        #print program, date
    txt = soup.find('div', {'id': 'intelliTXT'})
    lines = []
    for p in txt.find_all('p'):
        lines.append(p.text.strip())

    data = {}
    if date:
        data['year'] = date.year
        data['month'] = date.month
        data['date'] = date.day
        data['time'] = "%02d:%02d" % (date.hour, date.minute)

    data['channel.name'] = 'WWW'
    data['program.name'] = program
    data['timezone'] = tz
    data['subhead'] = title.text.strip()
    data['text'] = '\n'.join(lines)
    data['updated'] = soup.find('abbr', {'class': 'dtstamp updated'}).text.strip()
    return data


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding("utf-8")

    f = open("msnbc-r2.csv", "ab")
    writer = csv.DictWriter(f, fieldnames=columns, dialect='excel')

    writer.writeheader()

    s = scrapelib.Scraper(requests_per_minute=60)

    reader = csv.reader(open("all_links.csv"))

    i = 1
    for r in reader:
        url = BASE_URL + r[0]
        print "#%d: %s" % (i, url)
        try:
            fname = './html/' + '.'.join(r[0].strip('/').split('/')) + '.html'
            with open(fname, 'rb') as f:
                res = f.read()
            data = extract_transcript(res)
            data['url'] = url
            writer.writerow(data)
        except Exception as e:
            print "ERROR: %s" % e
        i += 1
    f.close()
