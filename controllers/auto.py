import requests
import json

def tree():
    taxa_list = [i.strip() for i in request.post_vars['taxa'].split('\n')]
    return json.loads(taxa_list)