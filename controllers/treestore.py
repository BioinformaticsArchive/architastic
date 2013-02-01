# controller to request list of names from treestore
# stores in local DB for later query against TNRS results
 
import json
import requests
import os

# request names and identifiers from treestore

# eventually want to check name and diff
#def _get_version_from_treestore
    # get current taxalist version from treestore

def _intializeTreestores():
    stores = {'opentree':'http://opentreeoflife.org','rdf':'http://phylotastic.org'}
    for i in stores:
        treestorename = i
        url = stores[i]
        rows = db(db.treestores.name_of_treestore==treestorename).select()
        if not rows:
            db.treestores.insert(name_of_treestore=treestorename,url=url)
    
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
        Field('json_dump_url',requires=IS_NOT_EMPTY()),
        )
    if form.process().accepted:
        response.flash='input accepted'
        session.json_dump_url=form.vars.json_dump_url
        session.treestore=form.vars.treestore
        redirect(URL('viewnames'))
    elif form.errors:
        response.flash='form has errors'
    return dict(form=form)

# perform some cursory checks on the results
# from the treestore
def _checknames():
    phylodump = _get_taxa_from_treestore(session.json_dump_url)
    datablock=phylodump['metadata']
    ok=0
    blocks=['names','version','treestoreMetadata','externalSources']
    for text in blocks:
        if datablock[text]:
            ok=ok+1
    if ok==4:
        ok=1;
    return int(ok)

# inserts names into database
# checks that identifier does not already exist
# TODO: possible that name might change when identifer doesn't?
def _insert_into_database(phylodump):
    inserted_names={};
    datablock = phylodump['metadata']
    names=datablock['names']
    for i in names:
        # get the taxon name and the identifier that the treestore
        # uses for that name
        name=i['name']
        identifier=i['treestoreId']
        treestorename = session.treestore;
        rows = db(db.treestore_names.taxon_id==identifier).select()
        if not rows:
            inserted_names[identifier]=name
            rows = db(db.treestores.name_of_treestore==treestorename).select()
            treestore_id = rows[0].id
            db.treestore_names.insert(
                name_of_treestore=treestore_id,
                treestore_name=name,
                taxon_id=identifier
                )
    return dict(inserted_names)

def viewnames():
#try:
    # this should definitely not be here, but it is here for now
    _intializeTreestores()
    phylodump = _get_taxa_from_treestore(session.json_dump_url)
    if _checknames():
        inserted_names=_insert_into_database(phylodump)
    #except:
    #    raise HTTP(404)
    return locals()
    #return redirect(URL('treestore', args=(taxid,)))                
