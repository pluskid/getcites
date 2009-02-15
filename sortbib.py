#!/usr/bin/python

############################################################
# Documentation
# 
# Author: pluskid <pluskid@gmail.com>
# Date: 2009-02-12
############################################################

import re
import os.path
import shutil

############################################################
# Configuration
############################################################
data_dir = 'paper_cites'
index_file = 'all_papers.txt'


############################################################
# Utility Functions
############################################################
def title2fn(title):
    return re.sub(r'\W+',' ',title).strip().replace(' ','-').lower()

############################################################
# Main Script
############################################################
index = 0
for title in open(index_file):
    index += 1
    paper_fn = title2fn(title)
    fn_txt = os.path.join(data_dir, '%s.txt' % paper_fn)
    fn_bib = os.path.join(data_dir, '%03d.%s.bib' % (index,paper_fn))
    if os.path.exists(fn_txt):
        shutil.copy(fn_txt, fn_bib)
    else:
        print 'NOT FOUND: %s' % title


