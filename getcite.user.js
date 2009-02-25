// Get publication cites from Google Scholar
// version 0.1
// 2008-02-13
// Copyright (c) 2008, pluskid
// Released under the GPL license
// http://www.gnu.org/copyleft/gpl.html
//
// --------------------------------------------------------------------
//
// This is a Greasemonkey user script.
//
// To install, you need Greasemonkey: http://greasemonkey.mozdev.org/
// Then restart Firefox and revisit this script.
// Under Tools, there will be a new menu item to "Install User Script".
// Accept the default configuration and install.
//
// To uninstall, go to Tools/Manage User Scripts,
// select "Get Cites", and click Uninstall.
//
// --------------------------------------------------------------------
//
// ==UserScript==
// @name          Get Cites
// @namespace     http://pluskid.org/gm
// @description   Get cites of your publications from Google Scholar.
// @include       http://scholar.google.com/
// ==/UserScript==

// Add jQuery
var GM_JQ = document.createElement('script');
GM_JQ.src = 'http://jquery.com/src/jquery-latest.js';
GM_JQ.type = 'text/javascript';
document.getElementsByTagName('head')[0].appendChild(GM_JQ);

// Check if jQuery's loaded
function GM_wait() {
    if(typeof unsafeWindow.jQuery == 'undefined') {
        window.setTimeout(GM_wait,100);
    } else {
        $ = unsafeWindow.jQuery; letsJQuery();
    }
}
GM_wait();

// All your GM code must be inside this function
function letsJQuery() {
    var gc_config = {
        paper_author: 'Xiaofei He',
        items_per_page: 100,
        lang_restrict: 'lang_en',
        lang:'en'
    };
    var E_network = 'Network Error';
    var E_notfound = 'Not Found';
    var E_ambiguity = 'Ambiguity';
    var E_parse = 'Parse Error';

    function mksearch(title) {
        return {
            q: '"'+title+'" '+gc_config.paper_author,
            hl: gc_config.lang,
            lr: gc_config.lang_restrict,
            num: gc_config.items_per_page
        };
    }

    function log(txt) {
        $('body').append(txt);
    }
    
    function scroll_to_bottom() {
        $('body').append('<a id="gc_the_bottom"></a>');
        var offset = $('#gc_the_bottom').offset().top;
        $('html,body').animate({scrollTop: offset}, 500);
        $('body').remove('#gc_the_bottom');
    }

    function retrieve(path, attr) {
        var res = $.ajax({
            type: "GET",
            url: path,
            data: attr,
            async: false
        });

        if (res.status != 200) {
            throw E_network;
        }
        return res.responseText;
    }

    function extract_bibtex(text) {
        var pat = new RegExp('ss=fl href="([^"]+)"[^>]*>Import into BibTeX','g');
        var bibs = new Array();
        while ((res = pat.exec(text)) != null) {
            bibs.push(retrieve(res[1]));
        }
        return bibs;
    }

    function clean_page(text) {
        /* strip <b> and </b> which Google might insert at any position */
        text = text.replace(/<\/?b>/g, '');
        /* Recover HTML entities like &#39; => ', &#34; => ", etc. */
        text = text.replace(/&#(\d+);/g, function (s, code, pos, str) {
            return String.fromCharCode(parseInt(code));
        });
        text = text.replace(/\s+/g, ' ');
        return text;
    }

    function retrieve_cites(title) {
        log('Getting cites for <b>' + title + '</b>...');
        var page = clean_page(retrieve('/scholar', mksearch(title)));
        var pat = new RegExp('>' + title +'</a></span>' + 
                             '(?:.*?<a class=fl href="([^"]+)"[^>]*>' + 
                             'Cited by (\\d+)</a>)?(.*?Import into BibTeX)',
                            'ig');
        
        matches = new Array();
        while ((res = pat.exec(page)) != null) {
            matches.push(res);
        }

        if (matches.length == 0) {
            log('<font color=red>Not Found</font><br />');
            throw E_notfound;
        } else if (matches.length > 1) {
            log('<font color=red>Ambiguity</font><br />');
            throw E_ambiguity;
        }
        var grps = matches[0];
        var cites = new Array();
        if (grps[2] == undefined) {
            log('<font color=blue>No cite</font>');
        } else {
            ncites = parseInt(grps[2]);
            log('<font color=blue>' + ncites + ' cites</font>');

            var starts = 0; 
            var has_next_page = true;
            while (has_next_page) {
                cite_page = retrieve(grps[1]+'&start='+starts);
                cites = cites.concat(extract_bibtex(cite_page));
                starts += gc_config.items_per_page;
                if (/<img src=\/intl\/en\/nav_next.gif width=100/.exec(cite_page)) {
                    has_next_page = true;
                } else {
                    has_next_page = false;
                }
            }
        }

        my_bib = extract_bibtex(grps[3]);
        if (my_bib.length == 0) {
            log('<font color=red>No BibTeX Info</font><br />');
            throw E_parse;
        }
        log('<br />');
        return my_bib[0]+'\n'+cites.join('\n');
    }

    $('body').append('<hr />Thanks for using the citation gathering tool. ' + 
                     'Documentation can be found here. ' + 
                     'Be sure to go to <a href="/scholar_preference">the' +
                     ' preference page<a> to <b>enable BibTeX importing</b>' +
                     ' before using.');
    $('body').append('<h1>Paste titles of your publications below</h1>');
    $('body').append('And the paper author here: <input type="text" ' + 
                     'id="gc_author" size="20" value="' +
                     gc_config.paper_author +
                     '"></input><br />');
    $('body').append('<textarea id="gc_publs" cols="80" ' +
                     'rows="20"></textarea><br />');
    $('body').append('<input type="button" id="gc_go" value="Fetch">' +
                     '</input><br />');
    $('#gc_go').click(function () {
        gc_config.paper_author = $('#gc_author').attr('value');
        var text = $.trim($('#gc_publs').attr('value'));
        var titles = text.split('\n');
        var bibtex = new Array();
        var errors = new Array();
        var i = 0;
        for (; i < titles.length; ++i) {
            title = titles[i];
            try {
                bibtex.push(retrieve_cites(title));
            } catch (e) {
                if (e == E_network) {
                    break;
                } else {
                    errors.push(title + ' <font color=red>' +
                                e + '</font>');
                }
            }
            scroll_to_bottom();
        }
        if (i != titles.length) {
            /* network error */
            for (; i < titles.length; ++i) {
                errors.push(titles[i] + ' <font color=red>' + 
                            E_network + '</font>');
            }
        }
        log('<h1>Fetching Results</h1>');
        if (errors.length != 0) {
            log('There are errors while fetching those papers:<br />');
            log('<pre>');
            for (var i = 0; i < errors.length; ++i) {
                log(errors[i] + '<br />\n');
            }
            log('</pre><hr />\n');
        }
        log('All bibtex are in the text area below:<br />');
        $('body').append('<textarea id="gc_result" cols="80" ' +
                         'rows="30"></textarea></br />');
        $('#gc_result').attr('value', bibtex.join('\n==========\n'));
    });
}
