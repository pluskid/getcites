#!/usr/bin/python

############################################################
# Documentation
# 
# Author: pluskid <pluskid@gmail.com>
# Date: 2009-02-12
############################################################

import re
import sys
import time
import os
import os.path
import urllib2
import urllib
import cookielib

############################################################
# Configuration
############################################################
user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; ' + \
        'en-GB; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5'
sleep_intv = 60 # set this to avoid banning by Google
paper_author = 'Xiaofei He'
index_file = 'papers.txt'
error_file = 'errors.txt'
data_dir = 'paper_cites'


############################################################
# Initialization
############################################################
items_per_page = 100
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
url_base = 'http://scholar.google.com'
headers = {'User-Agent': user_agent}


############################################################
# Utility Functions
############################################################
class PaperError(Exception):
    pass

def retrieve(path):
    url = url_base + path
    req = urllib2.Request(url, None, headers)
    socket = opener.open(req)
    cont = socket.read()
    socket.close()
    time.sleep(sleep_intv)
    return cont

def title2fn(title):
    return re.sub(r'\W+',' ',title).strip().replace(' ','-').lower()

def info(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

def make_search_url(title):
    return ('/scholar?hl=en&num=%d&lr=lang_en&q='%items_per_page) + \
            urllib.quote('"%s" %s' % (title, paper_author))

def get_bibtex(page):
    pat = re.compile(r'<a class=fl href="([^"]+)"' + \
            r'[^>]*>Import into BibTeX')
    matches = pat.findall(page)
    return [retrieve(bib) for bib in matches]

def preprocess_page(page):
    # strip <b> and </b> which Google might insert at any places
    page = page.replace('<b>', '').replace('</b>', '')
    # recover HTML entities like &#39; => ', &#34; => ", etc. which
    # may cause the title not being able to match
    page = re.sub(r'&#(\d+);', lambda x: chr(int(x.group(1))), page)
    return page


def retrieve_cites(title):
    info('%s... ' % title[0:45])
    page = preprocess_page(retrieve(make_search_url(title)))
    pat = re.compile(r'">%s</a></span>' % re.escape(title) + \
            r'(?:.*?<a class=fl href="([^"]+)">' + \
            r'Cited by (\d+)</a>)?(.*?Import into BibTeX)', 
            re.DOTALL | re.IGNORECASE)
    matches = pat.findall(page)
    if len(matches) == 0:
        info('<Not Found>\n')
        raise PaperError("Can't find paper")
    if len(matches) > 1:
        info('<Ambiguity>\n')
        raise PaperError("Ambiguity results")
    grps = matches[0]
    if grps[1] == '':
        info('[no cites]')
        cites = []
    else:
        ncites = int(grps[1])
        info('[%d cites]' % ncites)

        cites = []
        # deal with pages
        starts = 0
        info(' ')
        while len(cites) < ncites:
            cite_page = retrieve('%s&start=%d'%(grps[0],starts))
            cites += get_bibtex(cite_page)
            starts += items_per_page
            info('.')

    my_bib = get_bibtex(grps[2])
    if len(my_bib) == 0:
        info(' <No BibTeX Info>\n')
        raise PaperError("No BibTeX Info")
    info('\n')

    septr = '\n'
    return my_bib[0]+septr+septr.join(cites)


############################################################
# Main Script
############################################################
# Set Google Scholar Preference (stored in cookie) to show BibTeX
url_pref = ('/scholar_setprefs?num=%d&scis=yes'%items_per_page) + \
        '&scisf=4&hl=en&submit=Save+Preferences'
retrieve(url_pref)

# Read all paper titles
papers = [l.strip() for l in open(index_file)]

if not os.path.isdir(data_dir):
    os.makedirs(data_dir)
errors = []
for title in papers:
    try:
        cites = retrieve_cites(title)
        paper_fn = os.path.join(data_dir, '%s.txt'%title2fn(title))
        paper_out = open(paper_fn, 'w')
        paper_out.write(cites)
        paper_out.close()
    except PaperError, e:
        errors.append((title, e.args[0]))

if len(errors) != 0:
    ferr = open(error_file, 'w')
    for tit, msg in errors:
        ferr.write('%s: %s\n' % (tit, msg))
    ferr.close()
    print '%d errors, details saved to errors.txt' % len(errors)
