# controller to request list of names from treestore
# stores in local DB for later query against TNRS results
 
import json
import requests
import os

# request names and identifiers from treestore

# takes a url, expects a json response
def _get_data_from_url(url):
    # get JSON from treestore
    r = requests.get(url)
    if r.status_code==200:
        return r.json()
    else:
        raise HTTP(503)


# perform some cursory checks on the results from
# the treestore; making sure that all expected blocks
# are present
# called from viewnames
def _checknames(phylodump):
    ok=0
    blocks=['metadata','names','externalSources']
    for text in blocks:
        if phylodump[text]:
            ok=ok+1
    if ok==3:
        ok=1;
    return int(ok)

# parses phylodump and inserts names into database
# checks that identifier does not already exist
# TODO: possible that name might change when identifer doesn't?
# called from viewnames
def _insert_into_database(phylodump):
    inserted_names={};
    names=phylodump['names']
    for i in names:
        # get the taxon name and the identifier that the treestore
        # uses for that name
        name=i['name']
        identifier=i['treestoreId']
        treestorename = session.treestore;
        rows = db(db.treestore_names.taxon_id==identifier).select()
        if not rows:
            inserted_names[identifier]=name
            rows = db(db.treestores.shortName==treestorename).select()
            treestore_id = rows[0].id
            db.treestore_names.insert(
                name_of_treestore=treestore_id,
                treestore_name=name,
                taxon_id=identifier
                )
    return dict(inserted_names)

def _add_treestore():
    treestore_data = _get_data_from_url(session.treestore_metadata)
    version=treestore_data['metadata']['version']
    treestoreMetadata=treestore_data['metadata']['treestoreMetadata']
    treestoreShortName=treestoreMetadata['treestoreShortName']
    treestoreLongName=treestoreMetadata['treestoreLongName']
    treestoreUrlPrefix=treestoreMetadata['urlPrefix']
    treestoreDomain=treestoreMetadata['weburl']
    rows = db(db.treestores.shortName==treestoreShortName).select()
    if not rows:
        db.treestores.insert(
            shortName=treestoreShortName,
            longName=treestoreLongName,
            urlPrefix=treestoreUrlPrefix,
            weburl=treestoreDomain,
            dumpVersion=version
            )
    return dict(treestore_data)
    
def viewtreestore():
    treestore_data=_add_treestore()
    return dict(treestore_data)

# add a new treestore
def add():
    form = SQLFORM.factory(
        Field('treestore_metadata',requires=IS_NOT_EMPTY())
    )
    if form.process().accepted:
        response.flash='input accepted'
        session.treestore_metadata=form.vars.treestore_metadata
        redirect(URL('viewtreestore'))
    elif form.errors:
        response.flash='please enter url to treestore metadata'
    return dict(form=form)

# form for entering treestore url
# gets a name for the treestore and a url to the json dump of names
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

# calls functions for parsing phylodump, checking format
# inserting names into databases
# returns list of inserted names
def viewnames():
#try:
    phylodump = _get_data_from_url(session.json_dump_url)
    if _checknames(phylodump):
        inserted_names=_insert_into_database(phylodump)
    #except:
    #    raise HTTP(404)
    return locals()
    #return redirect(URL('treestore', args=(taxid,)))                
