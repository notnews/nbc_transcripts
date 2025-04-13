## NBC transcripts

NBC used to provide transcripts of some of its shows at the now defunct http://www.nbcnews.com/id/3719710. Check out this archive.org page [https://web.archive.org/web/20170601234403/http://www.nbcnews.com/id/3719710](https://web.archive.org/web/20170601234403/http://www.nbcnews.com/id/3719710).

[nbc_crawl.py](scripts/nbc_crawl.py) crawls all the links to news transcripts. The script produces a [list of all links](data/all_links.csv). And [nbc_extract.py](scripts/nbc_extract.py) downloads and parses the news transcripts and appends some meta data and dumps it to a CSV file. 

The raw html files and the final csv can be downloaded from [http://dx.doi.org/10.7910/DVN/ND1TCV](http://dx.doi.org/10.7910/DVN/ND1TCV).

And a list of all the links along with the title of the show and the date, see [here](data/out.txt).

Here's the yearly breakdown of the final dataset (5,369 rows):

```
2008 2009 2010 2011 2012 2013 2014 
  76  434  752 1042 1164 1177  724 
```

### Notes

* Scripts from 2014.
* Some news transcripts had a typo in the date string, e.g. 'Thusday','Februrary', etc. That caused the script to fail to fill in the date column.

## 🔗 Adjacent Repositories

- [notnews/cnn_transcripts](https://github.com/notnews/cnn_transcripts) — CNN Transcripts 2000--2025
- [notnews/fox_news_transcripts](https://github.com/notnews/fox_news_transcripts) — Fox News Transcripts 2003--2025
- [notnews/stanford_tv_news](https://github.com/notnews/stanford_tv_news) — Stanford Cable TV News Dataset
- [notnews/archive_news_cc](https://github.com/notnews/archive_news_cc) — Closed Caption Transcripts of News Videos from archive.org 2014--2023
- [notnews/lacc_to_csv](https://github.com/notnews/lacc_to_csv) — Los Angeles Closed-Caption Television News Archive Data to CSV
