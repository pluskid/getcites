#!/usr/bin/python
# -*- coding: utf-8 -*-

############################################################
# Documentation
# 
# Author: pluskid <pluskid@gmail.com>
# Date: 2009-02-12
############################################################

import re
import sys
import os
import os.path
import shutil

############################################################
# Configuration
############################################################
tex_title = 'Publications and Citations'
tex_author = 'Xiaofei He'
tex_filename = 'papers' # no .tex suffix
data_dir = 'paper_cites'
tmp_dir = 'tmp'


############################################################
# Initialization
############################################################
append_seed = 1
bibitem_tex = {}
publications = []
citations = []
tmptex_header = r"""\documentclass{article}
\usepackage{xeCJK}
\setCJKmainfont{Sun-ExtA}
\begin{document}
"""
tmptex_footer = r"""
\bibliographystyle{plain}
\bibliography{foo}
\end{document}
"""
finaltex_header = r"""\documentclass{article}
\usepackage{xeCJK}
\setCJKmainfont{Sun-ExtA}
\usepackage[usenames]{color}
\setlength{\parindent}{0in}
\title{%s}
\author{%s}
\date{\today}
\begin{document}
\maketitle
""" % (tex_title, tex_author)
finaltex_footer = r"""
\end{document}
"""

############################################################
# Utility Functions
############################################################
def get_bibs(text):
    bibs = text.strip().split('\n\n')
    pat = re.compile(r'@(\w+)\{([^,]+),')
    for i in range(len(bibs)):
        bib = bibs[i]
        bibkey = pat.search(bib).group(2)
        # We use generated key here for two reasons:
        #  1. to avoid duplication
        #  2. bibtex seems unable to handle Chinese keys
        global append_seed
        newkey = 'bibkey%d' % append_seed
        append_seed += 1
        bibs[i] = pat.sub(r'@\1{%s,' % newkey, bib, 1)
        bibs[i] = (newkey, bibs[i])
    return bibs

def sh_in_tmp(cmd):
    res = os.system('cd %s && %s' % (tmp_dir, cmd))
    if res != 0:
        print 'Error executing: %s' % cmd
        sys.exit(-1)

def get_authors(bib):
    pat = re.compile(r'author=\{([^}]+)\}')
    authors = pat.search(bib).group(1)
    return set(authors.split(' and '))

def classify_cites(publication, cites):
    "Classify self-cite and other-cite"
    self_authors = get_authors(publication[1])
    self_cites = []
    other_cites = []
    for bibkey, bib in cites:
        authors = get_authors(bib)
        if len(self_authors.intersection(authors)) == 0:
            other_cites.append((bibkey, bib))
        else:
            self_cites.append((bibkey, bib))
    return self_cites, other_cites

def format_ncite(nself_cite, nother_cite):
    def format_cite(n, adj=''):
        if n == 0:
            return 'no %scite' % adj
        if n == 1:
            return '1 %scite' % adj
        return '%d %scites' % (n, adj)
    nall = nself_cite + nother_cite
    fmt = format_cite(nall)
    if nall == 0:
        return fmt
    fmt += ' ('
    arr = []
    if nself_cite != 0:
        arr.append(format_cite(nself_cite, 'self '))
    if nother_cite != 0:
        arr.append(format_cite(nother_cite, 'other '))
    fmt += ', '.join(arr) + ')'
    return fmt


############################################################
# Main Script
############################################################
# Gether bibtex
pat_bibfn = re.compile(r'\d+\..*\.bib')
for fn in os.listdir(data_dir):
    if pat_bibfn.match(fn) is None:
        continue
    publ_fn = os.path.join(data_dir, fn)
    publ_file = open(publ_fn)
    bibs = get_bibs(publ_file.read())
    publications.append(bibs[0])
    citations.append(bibs[1:])
    publ_file.close()

if not os.path.isdir(tmp_dir):
    os.makedirs(tmp_dir)

# Generate LaTeX code for bibtex
tex_file = open(os.path.join(tmp_dir, 'foo.tex'), 'w')
bib_file = open(os.path.join(tmp_dir, 'foo.bib'), 'w')
tex_file.write(tmptex_header)
for i in range(len(publications)):
    publ_key, publ_bib = publications[i]
    tex_file.write('\\cite{%s},\n' % publ_key)
    bib_file.write('%s\n\n' % publ_bib)
    for cite_key, cite_bib in citations[i]:
        tex_file.write('\\cite{%s},\n' % cite_key)
        bib_file.write('%s\n\n' % cite_bib)
tex_file.write(tmptex_footer)
tex_file.close()
bib_file.close()
sh_in_tmp('xelatex foo')
sh_in_tmp('bibtex foo')

bbl_file = open(os.path.join(tmp_dir, 'foo.bbl'))
bib_tex = bbl_file.read().split('\n\n')[1:-1]
bbl_file.close()

pat_bibkey = re.compile(r'\\bibitem\{([^}]+)\}')
for bib in bib_tex:
    bibkey = pat_bibkey.search(bib).group(1)
    tex = bib[bib.find('\n')+1:]
    bibitem_tex[bibkey] = tex

# Classify citations as self-cite and other-cite
npubl = len(publications)
nself_cite = 0
nother_cite = 0
self_cites = [0]*npubl
other_cites = [0]*npubl
for i in range(npubl):
    self_cites[i], other_cites[i] = \
            classify_cites(publications[i], citations[i])
    nself_cite += len(self_cites[i])
    nother_cite += len(other_cites[i])

# Generate our final tex file
tex_file = open(os.path.join(tmp_dir, tex_filename+'.tex'), 'w')
tex_file.write(finaltex_header)
tex_file.write('My %d papers have %s in all.\n' % \
        (len(publications), format_ncite(nself_cite, nother_cite)))
tex_file.write('For each one of them, I list the works that ' + \
        'reference or cite it as follows:\n\n')
for i in range(len(publications)):
    publ_key = publications[i][0]
    tex_file.write('\\vspace{.1in}\\rule{\\linewidth}{.05mm}\n')
    tex_file.write('{\\color{blue}%d,} My paper \\textbf{' % (i+1))
    tex_file.write(bibitem_tex[publ_key])
    tex_file.write('} has %s. self cites are marked with *.\n' % \
            format_ncite(len(self_cites[i]), len(other_cites[i])))

    if (len(self_cites[i])+len(other_cites[i]) == 0):
        tex_file.write('\n')
    else:
        tex_file.write('\\begin{enumerate}\n')
        for cite_key, cite_bib in self_cites[i]:
            tex_file.write('\\item * %s\n' % bibitem_tex[cite_key])
        for cite_key, cite_bib in other_cites[i]:
            tex_file.write('\\item %s\n' % bibitem_tex[cite_key])
        tex_file.write('\\end{enumerate}\n')

tex_file.write(finaltex_footer)
tex_file.close()
sh_in_tmp('xelatex %s.tex' % tex_filename)
shutil.copy(os.path.join(tmp_dir, tex_filename+'.tex'), '.')
shutil.copy(os.path.join(tmp_dir, tex_filename+'.pdf'), '.')
