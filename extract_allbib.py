#!/usr/bin/python

import re
import os
import os.path

bibfile = 'allbib.txt'
destdir = 'paper_cites'

sep = '\n'+('='*10)+'\n'
pat = re.compile(r'title=\{\{([^}]+)\}\}')

def title2fn(title):
    return re.sub(r'\W+',' ',title).strip().replace(' ','-').lower()

if not os.path.exists(destdir):
    os.makedirs(destdir)
allbib = open(bibfile).read().split(sep)
print '%d bibs found' % len(allbib)
for bib in allbib:
    title = pat.search(bib).group(1)
    fn = os.path.join(destdir, title2fn(title)+'.txt')
    file = open(fn, 'w')
    file.write(bib)
    file.close()

