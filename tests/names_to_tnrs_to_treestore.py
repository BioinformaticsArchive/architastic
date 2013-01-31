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

Treestore functions
get_names(self, tree_name=None, format='json')
get_subtree(self, contains=[], match_all=False, format='newick')
'''
import sys, os
try:
    import requests
except ImportError:
    sys.exit('You must install the "requests" package by running\n  pip install requests\n\npip can be obtained from http://pypi.python.org/pypi/pip if you do not have it.')
import time
import datetime
import re

sleep_interval = 1.0
sleep_interval_increase_factor = 1.5

DOMAIN = 'http://api.phylotastic.org'
SUBMIT_PATH = 'tnrs/submit'
SUBMIT_URI = DOMAIN + '/' + SUBMIT_PATH
NAMES_KEY = u'names'
header_written = False
USE_RDF = 'RDFTREESTORE' in os.environ

start_time = time.time()

#open the newline delimited source of taxon names
if len(sys.argv) == 1:
    inp_stream_list = [sys.stdin]
else:
    inp_stream_list = [open(fn, 'rU') for fn in sys.argv[1:]]
if len(inp_stream_list) == 0:
    inp_stream_list = [sys.stdin]

def query_treestore(taxon_uid_tuples, treestore_name='http://opentree-dev.bio.ku.edu'):
    '''DJZ
    Query a treestore, making some strict assumptions about what formats they accept
    requests in.  Currently only works with treestores that return pruned trees based
    on a comma delimited list of taxon names.  The opentree treestore accepts this
    stuck in a raw POST.  An RDF treestore is accessed by passing a list of names to
    functions from the treestore python package.
    
    taxon_uid_tuples - list of doubles with (taxon name, uid), only taxon_names
        currently used
    treestore_name - EITHER a url string for an opentree treestore, or a string containing
        'rdf', for an RDF treestore

    returns tree in newick string currently
    '''

    use_uids = False
    if not use_uids:
        #remove dupe names
        name_list = set([str(tup[0]) for tup in taxon_uid_tuples])
        name_string = ','.join(name_list)
    else:
        exit('sorry, can\'t request by uids yet')
        name_string = ','.join(str(tup[1]) for tup in taxon_uid_tuples)

    if 'opentree' in treestore_name.lower():
        #assuming that this is a url for now
        #port is defined by neo4j
        PORT = 7474
        #probably not stable url
        SUBMIT_PATH = '/db/data/ext/GetJsons/graphdb/subtreeForNames'
        SUBMIT_URI = treestore_name + ':' + str(PORT) + SUBMIT_PATH

        headers = {'Content-Type':'Application/json'}
        #this needs to have the literal curlies and quotes embedded in it, since it is sent raw 
        #and not prettied up by requests
        data = '{"queryString": "%s"}' % name_string
        try:
            resp = requests.post(SUBMIT_URI, headers=headers, data=data)
        except requests.exceptions.ConnectionError as err:
            sys.exit('\nError connecting to treestore %s!\n%s' % (treestore_name, err)) 
        
        return resp.text

    elif 'rdf' in treestore_name.lower():
        try:
            import treestore
        except ImportError:
            sys.exit('You must install the "treestore" package to interface with an RDF treestore.\n Get it from https://github.com/phylotastic/rdf-treestore.')

        #instantiate a treestore object, which will look for an attached 
        rdf_treestore = treestore.Treestore()
        
        #taxon names aren't necessarily standardized in trees, can could have underscores, but won't
        #come back from the TRNS that way.  So, if it finds nothing try again. Currently finding nothing
        #is indicated by the throwing of a base Exception in the treestore module
        try:
            ret_tree = rdf_treestore.get_subtree(contains=name_list, match_all=False, format='newick')
        except:
            name_list = [ re.sub(' ', '_', name) for name in name_list ]
            ret_tree = rdf_treestore.get_subtree(contains=name_list, match_all=False, format='newick')
        
        return ret_tree
    
    else:
        exit('I don\'t know how to contact treestore %s yet' % treestore_name)


def write_resolved_names(submitted_name_list, names_response, outp):
    '''MTH & DJZ
    Writes the submitted, accepted, matched names and the source and URI
    to `outp` in tab-delimited form.
    '''
    global header_written
    col_fields = [u'submittedName', u'acceptedName', u'matchedName', u'score', u'sourceId', u'uri']
    output_names = ['Submitted', 'Accepted', 'Matched', 'Score', 'Source', 'URI']
    fieldDict = dict((out, field) for out, field in zip(output_names, col_fields))
    if not header_written:
        outp.write('%s\n' % ''.join('%30s' % f for f in output_names))
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
                outp.write('%30s' % sn) 
                outp.write('%s\n' % '\t'.join(['%30s' % a_match[f] for f in col_fields[1:]]))
        else:
            outp.write('%s\t\t\t\t\t\n' % sn)
    return matches    

#MTH & DJZ
all_results = []
for inp_stream in inp_stream_list:
    #first split on newlines
    name_list = [unicode(line.strip()) for line in inp_stream if len(line.strip()) > 0]
    #then on commas
    split_list = []
    for n in name_list:
        split_list.extend(n.split(','))
    name_list = [ tax.strip() for tax in split_list ]

    batch_size = 10
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
    
        all_results.extend(retrieve_results[NAMES_KEY])

    #DJZ
    taxon_tuples = []
    for subTaxDict in all_results:
        for singleMatchDict in subTaxDict[u'matches']:
            taxon_tuples.append((singleMatchDict[u'matchedName'], singleMatchDict[u'uri']))
    
    if USE_RDF:
        tree_string = query_treestore(taxon_tuples, treestore_name='rdftreestore')
    else:
        tree_string = query_treestore(taxon_tuples)
    #tree_string = query_treestore(taxon_tuples, treestore_name='rdftreestore')
    tree_string = query_treestore(taxon_tuples)
    sys.stdout.write('%s\n' % tree_string)
    
end_time = time.time()
diff_time = end_time - start_time
td = datetime.timedelta(seconds=diff_time)
min_diff_time = min_time - start_time
min_td = datetime.timedelta(seconds=min_diff_time)
sys.stderr.write('total time = %s\n' % str(td))
sys.stderr.write('min tnrs time = %s\n' % str(min_td))

