# controller to request list of names from treestore
# stores in local DB for later query against TNRS results
 
import json
import requests

# request names and identifiers from treestore

# eventually want to check name and diff
#def _get_version_from_treestore
    # get current taxalist version from treestore

def _get_taxa_from_treestore(url):
    # get JSON from treestore
    r = requests.get(url)
    if r.status_code==200:
        return r.json()
    else:
        raise HTTP(503)

def getnames():
    form = SQLFORM.factory(
        Field('treestore',requires=IS_IN_SET(['opentree','rdf'])),
        Field('json_dump_url',requires=IS_NOT_EMPTY()))
    if form.process().accepted:
        response.flash='input accepted'
        session.json_dump_url=form.vars.json_dump_url
        session.treestore=form.vars.treestore
        redirect(URL('viewnames'))
    elif form.errors:
        response.flash='form has errors'
    return dict(form=form)

def viewnames():
#try:
    results = _get_taxa_from_treestore(session.json_dump_url)
    #except:
    #    raise HTTP(404)
    return dict(results)
    #return redirect(URL('treestore', args=(taxid,)))                
