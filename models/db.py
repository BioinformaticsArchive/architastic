# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

mail.settings.server = settings.email_server
mail.settings.sender = settings.email_sender
mail.settings.login = settings.email_login


def define_tables(db, migrate=True):
    # treestores defines the treestores for the controllers
    db.define_table(
        'treestores',
        Field('name_of_treestore','string'), #name
        Field('url','string'),
        migrate=migrate
        )
    # treestore_names defines the entities that the treestore 'knows' about
    # taxon name, source id (NCBI, etc) and the identifier that the treestore
    # wants to use when referring to that name
    db.define_table(
        'treestore_names',
        Field('treestore_name','string'), # name used by the treestore, might not be unique
        Field('taxon_id','string',unique=True), # ids for taxon_name from the treestore
        Field('name_of_treestore',db.treestores), # name for the treestore itself
        migrate=migrate
        )
    db.define_table(
        'tax_query',
        Field('url', type='string'),
        Field('treestore',type='string'),
        migrate=migrate
        )
    db.define_table(
        'name_from_user',
        Field('tax_query', db.tax_query), # the id of the tax_query that deposited this name
        Field('treestore_name', db.treestore_names), # a reference to a known treestore name record
        Field('original_name', 'string'), # name in the query
        Field('tnrs_json', 'text'), # hack blurb from TNRS
        Field('taxon_name', 'string'), # user's choice of the name for this taxon (from among the valid names)
        Field('taxon_uri', 'string'), # user's choice of the URI for this name
        Field('match_status', 'string'), # hack a field for storing the mechanism used to choose between the tnrs choices 
        migrate=migrate
        )
    db.define_table(
        'treestore_query',
        Field('service_url', 'string'), # the full url for the treestore service, including domain, ports, etc
        Field('headers', 'string'), # headers stored as JSON to be parsed into a dict for the requests module
        Field('query_data', 'string'), # the cql query, wrapped in whatever formatting is required by the treestore
        Field('treestore_name', 'string'), # just the name of the treestore for labeling purposes
        migrate=migrate,
        )
    db.define_table(
        'treestore_result',
        Field('treestore_query_id', db.treestore_query),
        Field('tre_result', 'string'),
        migrate=migrate
        )
define_tables(db)
