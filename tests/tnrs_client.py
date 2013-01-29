#!/usr/bin/env python
'''
Example of a client of the demo of the TNRS API described at:
    http://www.evoio.org/wiki/Phylotastic/TNRS

Reads names (separated by newline characters) from file names passed in as
    command-line arguments (or reads name from standard input if no arguments
    are given).

Outputs tab-delimited summary of the matches for each query sorted by score of 
    the match (or the submitted name followed tabs and a newline if no match
    was found).

Writes status message and a summary of the time taken to standard error (note
    that some of the time taken in the summary is the reading and writing of 
    names in this script, not the TNRS service).
'''
import sys
try:
    import requests
except:
    sys.exit('You must install the "requests" package by running\n  pip install requests\n\npip can be obtained from http://pypi.python.org/pypi/pip if you do not have it.')
import time
import datetime

sleep_interval = 1.0
sleep_interval_increase_factor = 1.5

DOMAIN = 'http://api.phylotastic.org'
SUBMIT_PATH = 'tnrs/submit'
SUBMIT_URI = DOMAIN + '/' + SUBMIT_PATH
NAMES_KEY = u'names'
header_written = False


start_time = time.time()

if len(sys.argv) == 1:
    inp_stream_list = [sys.stdin]
else:
    inp_stream_list = [open(fn, 'rU') for fn in sys.argv[1:]]
if len(inp_stream_list) == 0:
    inp_stream_list = [sys.stdin]


def write_resolved_names(submitted_name_list, names_response, outp):
    '''Writes the submitted, accepted, matched names and the source and URI
    to `outp` in tab-delimited form.
    '''
    global header_written
    if not header_written:
        outp.write('Submitted\tAccepted\tMatched\tScore\tSource\tURI\n')
        header_written = True
    by_sub_name = {}
    for match in names_response:
        sn = match[u'submittedName']
        by_sub_name[sn] = match[u'matches']
    matches = {}
    
    for sn in submitted_name_list:
        m = by_sub_name.get(sn)
        matches[sn] = m
        if m:
            sorted_list = [(float(i[u'score']), i) for i in m]
            sorted_list.sort(reverse=True)
            for score_float, a_match in sorted_list:
                accepted = a_match[u'acceptedName']
                matched = a_match[u'matchedName']
                score = a_match[u'score']
                source = a_match[u'sourceId']
                uri = a_match[u'uri']
                outp.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (sn, accepted, matched, score, source, uri))
        else:
            outp.write('%s\t\t\t\t\t\n' % sn)
    return matches    

for inp_stream in inp_stream_list:
    name_list = [unicode(line.strip()) for line in inp_stream if len(line.strip()) > 0]
    batch_size = 1
    curr_ind = 0
    while curr_ind < len(name_list): 
        end_ind = curr_ind + batch_size
        if end_ind > len(name_list):
            end_ind = len(name_list)
        this_batch = name_list[curr_ind:end_ind]
        names_newline_sep = '\n'.join(this_batch)
        resp = requests.get(SUBMIT_URI,
                            params={'query':names_newline_sep},
                            allow_redirects=True)
        sys.stderr.write('Sent GET to %s\n' %(resp.url))
        resp.raise_for_status()
        results = resp.json()
        retrieve_uri = results.get(u'uri')
        if retrieve_uri:
            sys.stderr.write('Retrieving names from %s\n' % (retrieve_uri))
        elif len(resp.history) > 0:
            retrieve_uri = resp.url
        else:
            sys.exit('Did not get a URI or redirect from the submit GET operation. Got:\n %s\n' % str(results))
        min_time = time.time()
        sleep_interval = 1.0
        while retrieve_uri:
            retrieve_response = requests.get(retrieve_uri)
            retrieve_response.raise_for_status()
            retrieve_results = retrieve_response.json()
            if NAMES_KEY in retrieve_results:
                break
            min_time = time.time()
            sys.stderr.write('Waiting (%f sec) for processing by tnrs.\n' % sleep_interval)
            time.sleep(sleep_interval)
            sleep_interval *= sleep_interval_increase_factor
            
        write_resolved_names(this_batch, retrieve_results[NAMES_KEY], sys.stdout)
        curr_ind += batch_size
    
end_time = time.time()
diff_time = end_time - start_time
td = datetime.timedelta(seconds=diff_time)
min_diff_time = min_time - start_time
min_td = datetime.timedelta(seconds=min_diff_time)
sys.stderr.write('total time = %s\n' % str(td))
sys.stderr.write('min tnrs time = %s\n' % str(min_td))
