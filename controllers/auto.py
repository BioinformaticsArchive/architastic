import requests
import json
import subprocess
from StringIO import StringIO
import sys, os
from tempfile import NamedTemporaryFile

_CONF_OBJ_DICT = {}

def _get_conf(request):
    global _CONF_OBJ_DICT
    app_name = request.application
    c = _CONF_OBJ_DICT.get(app_name)
    if c is None:
        from ConfigParser import SafeConfigParser
        c = SafeConfigParser({})
        lcp = "applications/%s/private/localconfig" % app_name
        if os.path.isfile(lcp):
            c.read(lcp)
        else:
            c.read("applications/%s/private/config" % app_name)
        _CONF_OBJ_DICT[app_name] = c
    return c


def tree():
    t = request.post_vars['taxa']
    if not t:
        raise HTTP(503)
    try:
        try:
            exe = _get_conf(request).get("external", "cmdline")
        except:
            _LOG.warn("Config does not have external/cmdline setting")
            raise
        assert(os.path.exists(exe))
    except:
        sys.stderr.write("WARNING: Could not find the names_to_tnrs_to_treestore executable")
        raise HTTP(501, T("Server is not configured to allow names_to_tnrs_to_treestore conversion"))
    
    f = NamedTemporaryFile(delete=False)
    f.write(t)
    n = f.name
    f.close()

    #exe = '/home/mholder/Documents/projects/phylotastic/architastic/tests/names_to_tnrs_to_treestore.py'
    o = subprocess.check_output([sys.executable, exe, n])
    os.unlink(n)
    return json.dumps(o)
