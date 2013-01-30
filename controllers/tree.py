import requests

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
b='''        sys.exit('Did not get a URI or redirect from the submit GET operation. Got:\n %s\n' % str(results))
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
'''

# form for entering taxa list
def enter():
    form = SQLFORM.factory(
        Field('taxalist',requires=IS_NOT_EMPTY()),
        Field('treestore',requires=IS_IN_SET(['opentree','rdf'])))
    if form.process().accepted:
        response.flash='form accepted'
        session.taxalist=form.vars.taxalist
        session.treestore=form.vars.treestore
        redirect(URL('find'))
    elif form.errors:
        response.flash='form has errors'
    return dict(form=form)


# creates the URL for the TNRS and calls the TNRS
def find():
    raw_taxa_str=session.taxalist
    #raw_taxa_str = request.vars.taxa
    taxa_list = [i.strip() for i in raw_taxa_str.split(',')]
    
    #@TEMP should be based on the user's TNRS choice...
    domain = 'http://api.phylotastic.org'
    submit_path = 'tnrs/submit'
    submit_uri = domain + '/' + submit_path

    u = _get_tnrs_uri(submit_uri, taxa_list)
    new_id = db.tax_query.insert(url=u)

    # populate database fields from TNRS call
    for name in taxa_list:
        db.name_from_user.insert(tax_query=new_id,
                                 original_name=name,
                                 tnrs_json='',
                                 taxon_uri='',
                                 match_method='')
    return redirect(URL('show', args=(new_id,)))

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
            'tax_query_id': q_id }

def proxy_tnrs():
    try:
        q_id = request.args[-1]
        q = db.tax_query[q_id]
    except:
        raise HTTP(404)
    response.headers['content-type'] = 'json'
    return requests.get(q.url).text
