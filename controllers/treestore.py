# controller to request list of names from treestore
# stores in local DB for later query against TNRS results
 
import json
import requests

# request names and identifiers from treestore

# eventually want to check name and diff
#def _get_version_from_treestore
    # get current taxalist version from treestore

# takes a url, expects a json response
def _get_taxa_from_treestore(url):
    # get JSON from treestore
    r = requests.get(url)

    if r.status_code==200:
        return r.json()
    else:
        raise HTTP(503)

# form for entering treestore url
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

# at this point, does no checking for duplicates
def _insert_into_database(phylodump):
    inserted_names={};
    if phylodump['names']:
        names=phylodump['names']
        for i in names:
            name=i['name']
            identifier=i['treestoreId']
            rows = db(db.treestore_names.treestore_id==identifier).select()
            if not rows:
                inserted_names[identifier]=name
                #db.treestore_names.insert(taxon_name=name,treestore_id=identifer)
    else:
       response.flash='no names block'
    return dict(inserted_names)

def viewnames():
#try:
    phylodump = _get_taxa_from_treestore(session.json_dump_url)
    inserted_names=_insert_into_database(phylodump)
    #except:
    #    raise HTTP(404)
    return locals()
    #return redirect(URL('treestore', args=(taxid,)))                
