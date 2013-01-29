def test():
    form = FORM("List of taxa: ",INPUT(_name='taxa', 
    	              _type='TEXTAREA',
    	              requires=IS_NOT_EMPTY()),
                INPUT(_type='submit'))
    if form.accepts(request,session):
        response.flash='form accepted'
    elif form.errors:
        response.flash='form has errors'
    else:
        response.flash='please complete form'
    return dict(form=form)

