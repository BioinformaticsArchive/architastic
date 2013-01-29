def enter():
    form = FORM(INPUT(_name='taxa', 
                      _type='TEXTAREA',
                      requires=IS_NOT_EMPTY()),
                INPUT(_type='submit'),
                _action=URL('find'))
    return dict(form=form)

def find():
    raw_taxa_str = request.vars.taxa
    taxa_list = [i.strip() for i in raw_taxa_str.split(',')]
    new_id = db.tax_query.insert(url='bogus')
    return redirect(URL('show', args=(new_id,)))

def show():
    try:
        q_id = request.args[-1]
        q = db.tax_query[q_id]
    except:
        raise HTTP(404)
    return q.url