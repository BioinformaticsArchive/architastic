# -*- coding: utf-8 -*-
### required - do no delete
def user(): return dict(form=auth())
def download(): return response.download(request,db)
def call(): return service()
### end requires
def index():
    return dict()

def error():
    return dict()
def test():
	form = FORM(_name='taxa',
                requires=IS_NOT_EMPTY(),
                INPUT(),
                _action=URL('second'))
    return dict(form=form)

