import requests
import json

def tree():
    t = request.post_vars['taxa']
    taxa_list_with_empties = [i.strip() for i in t.split('\n')]
    taxa_list = [i for i in taxa_list_with_empties if i]
    return json.dumps(taxa_list)