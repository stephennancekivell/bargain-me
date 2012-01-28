#!/usr/bin/env python

import sys, BeautifulSoup,urllib,sqlite3

PRICE_UPPER_LIMIT = 700
PRICE_LOWER_LIMIT = 100
BASE_URL = "" # TODO GUESS
DB_FILE = "bargainme.sqlite"
URLS = [
    "http://www."+BASE_URL+"/browse/searchresults.aspx?sort_order=expiry_asc&searchType=0002-0358-0513-6458-&searchString=adsl&x=0&y=0&searchregion=100&type=Search&redirectFromAll=False&generalSearch_keypresses=4&generalSearch_suggested=0",
    "http://www."+BASE_URL+"/browse/searchresults.aspx?sort_order=expiry_asc&searchType=0002-0358-2927-&searchString=wifi&type=Search&generalSearch_keypresses=4&generalSearch_suggested=0"
    ]

class AppURLopener(urllib.FancyURLopener):
    version = "mozilla/3.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/5.0.1"

urllib._urlopener = AppURLopener()

def parseListingCard(c):
    for div in c.findAll('div'):
        for k,v in div.attrs:
            if k=='class' and v=='listingTitle':
                title = div.a.contents[0]
                url = div.a['href']
            elif k=='class' and v=='listingCloseDateTime':
                time = div.contents
            elif k=='class' and v=='listingBidPrice':
                price = div.a.contents[0]

    price = price[1:]
    price = price.replace(",","") # for prices like $1,000 strip the ','
    price = float(price)
    return {'title':title,'time':time,'price':price, 'url':url}

def getListingsFromPage(page):
    soup = BeautifulSoup.BeautifulSoup(page)
    listings = []
    for li in soup.findAll('li'):
        for k,v in li.attrs:
    	    if k=='class' and v=='listingCard':
    	        listings.append(parseListingCard(li))
    return listings

def closesSoon(time):
    if 'min' in time: return True
    if 'hours' in time: return True
    return False

def saveListings(listings):
    """saves the saved listings to the db """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''create table if not exists listings (listing text)''')

    for t in listings:
        c.execute('insert into listings values (?)', (t['url'],))

    conn.commit()
    c.close()

def alreadyReported():
    """ returns all of the already reported listings. TODO these could carry a TimeToLive"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''create table if not exists listings (listing text)''')
    c.execute('select listing from listings')
    l = []
    for row in c:
        l+=[row[0]]

    conn.commit()
    c.close()
    return l

pages = [urllib.urlopen(url) for url in URLS]

listings = []
for page in pages:
    listings += getListingsFromPage(page)

reported = alreadyReported()

cheap = [f for f in listings if (f['price'] < PRICE_UPPER_LIMIT and f['price'] > PRICE_LOWER_LIMIT and closesSoon(str(f['time'])) and f['url'] not in reported )]

if len(cheap)==0:
    sys.exit(2)

saveListings(cheap)

msg = ""
for l in cheap:
    msg +="$%d ::  %s :: %s :: %s</a>\n" % (l['price'],l['time'],l['title'], BASE_URL+"/"+l['url'])

print msg
