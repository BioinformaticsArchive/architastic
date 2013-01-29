def test():
    form = FORM(INPUT(_name='taxa', 
    	              _type='TEXTAREA',
    	              requires=IS_NOT_EMPTY()),
                INPUT(_type='submit'),
                _action=URL('second'))
    return dict(form=form)
