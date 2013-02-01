import requests
import json
import time
import sys

def _debug(s):
    sys.stderr.write(s)
    sys.stderr.write('\n')

def _get_tnrs_uri(submit_uri, name_list):
    names_newline_sep = '\n'.join(name_list)
    resp = requests.get(submit_uri,
                        params={'query':names_newline_sep},
                        allow_redirects=True)
    resp.raise_for_status()
    try:
        results = resp.json()
    except:
        results = resp.json
    retrieve_uri = results.get(u'uri')
    if retrieve_uri:
        return retrieve_uri
    elif len(resp.history) > 0:
        return resp.url
    else:
        raise HTTP(503) # not sure if there is a better status code to return here...

# form for entering taxa list
# SQLFORM.factory allows you to create nice forms without pointing 
# to a data model
def enter():
    form = SQLFORM.factory(
        Field('taxalist',requires=IS_NOT_EMPTY()),
        Field('treestore',requires=IS_IN_SET(['opentree','rdf'])))
    if form.process().accepted:
        response.flash='input accepted'
        session.taxalist=form.vars.taxalist
        session.treestore=form.vars.treestore
        redirect(URL('find'))
    elif form.errors:
        response.flash='form has errors'
    return dict(form=form)

# creates the URL for the TNRS and calls the TNRS
def find():
    # session vars come from form in enter()
    raw_taxa_str=session.taxalist

    # and then split on commas
    taxa_list = [i.strip() for i in raw_taxa_str.split(',')]
    
    #@TEMP should be based on the user's TNRS choice...
    domain = 'http://api.phylotastic.org'
    submit_path = 'tnrs/submit'
    submit_uri = domain + '/' + submit_path

    u = _get_tnrs_uri(submit_uri, taxa_list)
    new_id = db.tax_query.insert(url=u,treestore=session.treestore)

    # populate database fields from TNRS call
    for name in taxa_list:
        db.name_from_user.insert(tax_query=new_id,
                                 original_name=name,
                                 tnrs_json='',
                                 taxon_name='',
                                 taxon_uri='',
                                 match_status='')
    return redirect(URL('show', args=(new_id,)))

# Contact tree store to get a tree for the non-empty names
def find_tree():
    try:
        q_id = request.args[-1]
        q = db.tax_query[q_id]
    except:
        raise HTTP(404)
    name_row_list = db(db.name_from_user.tax_query == q).select()
    matched_names = []
    for row in name_row_list:
        s = str(row.taxon_name)
        if s:
            matched_names.append(s)
    return requests.post(URL(a=request.application,
                             c='auto', 
                             f='tree.json',
                             scheme='http'),
                         data={'taxa' : '\n'.join(matched_names)}
                        ).text

# Shows results from TNRS call
def show():
    try:
        q_id = request.args[-1]
        q = db.tax_query[q_id]
    except:
        raise HTTP(404)
    name_row_list = db(db.name_from_user.tax_query == q).select()

    return {'tnrs_url' : q.url,
            'name_row_list' : name_row_list, 
            'tax_query_id': q_id,
            'tax_submission_id' : q_id # at some point the session/submission id may need
                                       #       to be distinct from the query id (if a session calls the TNRS
                                       #       multiple times...)
            }

class NameMatchingTypeFacets:
    PERFECT_AMBIGUOUS = 'multiple perfect matches'
    IMPERFECT_AMBIGUOUS = 'imperfect match and there are multiple matches'
    UNRECOGNIZED = 'not recognized by TNRS'
    NOT_IN_STORE = 'recognized by TNRS but not in tree store'
    USER = 'user matched'
    ONLY_PERFECT_IN_STORE = 'only perfect match in tree store'
    ONLY_MATCH_IN_STORE = 'imperfect but only match in tree store'
    UNCHECKED = ''

force_repopulate_from_json = False # debugging
ncbi_only = False
      
#@ TEMP need to get the names from the tree_store to answer this correctly...
def _is_known_name(name_uri_tuple, source, tree_store_matching_context):
    name, uri = name_uri_tuple
    if ncbi_only:
        return source.upper() in ['NCBI']
    return True

def fix_name():
    try:
        name = request.post_vars['name']
        uri = request.post_vars['uri']
        local_name_id = request.post_vars['localNameId']
        local_query_id = request.post_vars['localQueryId']
    except KeyError:
        raise HTTP(503, "Missing arg")
    query_row = db.tax_query[local_query_id]
    name_row = db.name_from_user[local_name_id]
    name_row.update_record(match_status=NameMatchingTypeFacets.USER,
                    taxon_name=name,
                    taxon_uri=uri)
    db.commit()

# grab JSON from the TNRS and return it. This avoids problems with cross-domain scripting
#   restriction
def proxy_tnrs():
    '''
    When called with an ID of a taxa query, this will return a transformation of the 
    JSON returned from the TNRS
    
    list of dicts with the following keys for each name submitted in the query:
    tnrsQueryId   = id in the tax_query table
    nameIdInQuery = id in name_from_user table
    matches : matches from tnrs JSON
    matchStatus' : status of the name in name_from_user table (see NameMatchingTypeFacets)
    taxonName ' : name to send to tree store,
    taxonUri' : uri to send to tree store,
    submittedName' : raw name 
    '''
    try:
        q_id = request.args[-1]
        q = db.tax_query[q_id]
    except:
        raise HTTP(404)
    name_row_list = db(db.name_from_user.tax_query == q).select()
    
    response.headers['content-type'] = 'json'
    json2return = {}
    populated = False
    name_row_list = db(db.name_from_user.tax_query == q).select()
    _debug('len(name_row_list) = %d' % len(name_row_list))
    for row in name_row_list:
        _debug('row.match_status = %s \n' % row.match_status)
    
        if row.match_status == NameMatchingTypeFacets.UNCHECKED:
            all_matches = []
            mj = json.dumps(all_matches)
            match_status = NameMatchingTypeFacets.UNRECOGNIZED
            row.update_record(tnrs_json=mj,
                       match_status=match_status,
                       taxon_name='',
                       taxon_uri='')
            taxon_uri = ''
            taxon_name = ''
        else:
            if row.tnrs_json:
                all_matches = json.loads(row.tnrs_json)
            else:
                all_matches = []
            match_status = row.match_status
            taxon_name = row.taxon_name
            taxon_uri = row.taxon_uri
            populated = True
        row_key = str(q_id) + ' ' + str(row.id)
        json2return[row_key] = {
                'tnrsQueryId' : q_id,
                'nameIdInQuery' : str(row.id),
                'matches' : all_matches,
                'matchStatus' : match_status,
                'taxonName' : taxon_name,
                'taxonUri' : taxon_uri,
                'submittedName' : str(row.original_name)
            }

    # no need to grab the JSON twice...
    if populated and not force_repopulate_from_json:
        _debug('Returning JSON representation of the populated name row')
        db.commit()
        return json.dumps([v for v in json2return.itervalues()])
    _debug('Reading JSON from ' + q.url)
    # block while the TNRS is thinking....
    matchedList = None
    sleep_interval = 1.0
    sleep_interval_increase_factor = 1.05
    while matchedList is None:
        resp = requests.get(q.url)
        data = resp.json()
        try:
            matchedList = data['names']
        except KeyError:
            if not 'message' in data:
                raise HTTP(503)
            time.sleep(sleep_interval)
            sleep_interval *= sleep_interval_increase_factor

    tree_store_matching_context = None #@TEMP dummy placeholder
    for matchBlob in matchedList:
        all_matches = matchBlob['matches']
        perfect_matches = []
        known_matches = []
        for curr_match in all_matches:
            source = curr_match['sourceId']
            m_n = curr_match['matchedName']
            m_u = curr_match['uri']
            is_in_tree_store = _is_known_name((m_n, m_u), source, tree_store_matching_context)
            is_perfect_match = curr_match['score'].startswith('1')
            curr_match['is_in_tree_store'] = is_in_tree_store
            curr_match['is_perfect_match'] = is_perfect_match
            curr_match['is_only_known_perfect_match'] = False
            if is_in_tree_store:
                known_matches.append(curr_match)
                if is_perfect_match:
                    perfect_matches.append(curr_match)
                    curr_match['match_status'] = NameMatchingTypeFacets.PERFECT_AMBIGUOUS
                else:
                    curr_match['match_status'] = NameMatchingTypeFacets.IMPERFECT_AMBIGUOUS
            else:
                curr_match['match_status'] = NameMatchingTypeFacets.NOT_IN_STORE
        taxon_name = ''
        taxon_uri = ''
        if len(perfect_matches) == 1:
            pm = perfect_matches[0]
            pm['match_status'] = NameMatchingTypeFacets.ONLY_PERFECT_IN_STORE
            match_status = NameMatchingTypeFacets.ONLY_PERFECT_IN_STORE
            taxon_name = pm['acceptedName']
            taxon_uri = pm['uri']
        elif len(perfect_matches) > 1:
            match_status = NameMatchingTypeFacets.PERFECT_AMBIGUOUS
        elif len(known_matches) == 1:
            km = known_matches[0]
            km['match_status'] = NameMatchingTypeFacets.ONLY_MATCH_IN_STORE
            match_status = NameMatchingTypeFacets.ONLY_MATCH_IN_STORE
            taxon_name = km['acceptedName']
            taxon_uri = km['uri']
        elif len(known_matches) > 1:
            match_status = NameMatchingTypeFacets.IMPERFECT_AMBIGUOUS
        else:
            match_status = NameMatchingTypeFacets.NOT_IN_STORE
        mj = json.dumps(all_matches)
        submitted_name = matchBlob['submittedName']
        matched_db_row_list = db( (db.name_from_user.tax_query == q) & (db.name_from_user.original_name == submitted_name)).select()
        for matched_db_row in matched_db_row_list:
            matched_db_row.update_record(tnrs_json=mj,
                                  match_status=match_status,
                                  taxon_name=taxon_name,
                                  taxon_uri=taxon_uri)
            db.commit()
            row_key = str(q_id) + ' ' + str(matched_db_row.id)
            json2return[row_key] = {
                'tnrsQueryId' : q_id,
                'nameIdInQuery' : str(matched_db_row.id),
                'matches' : all_matches,
                'matchStatus' : match_status,
                'taxonName' : taxon_name,
                'taxonUri' : taxon_uri,
                'submittedName' : str(matched_db_row.original_name)
            }
            _debug('at the end matched_db_row.match_status = %s' % matched_db_row.match_status)

    db.commit()
    nrl = db(db.name_from_user.tax_query == q).select()
    _debug('at the end len(name_row_list) = %d' % len(nrl))
    for row in nrl:
        _debug('at the end row.match_status = %s' % row.match_status)

    return json.dumps([v for v in json2return.itervalues()])
