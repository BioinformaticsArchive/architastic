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
import sys
try:
    import requests
except:
    sys.exit('You must install the "requests" package by running\n  pip install requests\n\npip can be obtained from http://pypi.python.org/pypi/pip if you do not have it.')
import time
import datetime
import itertools
import re
import json

sleep_interval = 1.0
sleep_interval_increase_factor = 1.5

DOMAIN = 'http://127.0.0.1:8000'
SUBMIT_PATH = 'architastic/auto/tree.json'
SUBMIT_URI = DOMAIN + '/' + SUBMIT_PATH
#this needs to have the literal curlies and quotes embedded in it, since it is sent raw 
#and not prettied up by requests
data = {"taxa" : open(sys.argv[1], 'rU').read()}
print data
resp = requests.post(SUBMIT_URI,
    data=data)

print resp.text