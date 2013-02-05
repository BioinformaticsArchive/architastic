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
    args_to_pass = [sys.executable]
    try:
        try:
            exe = _get_conf(request).get("external", "cmdline")
            args_to_pass.append(exe)
        except:
            _LOG.warn("Config does not have external/cmdline setting")
            raise
        assert(os.path.exists(exe))
    except:
        sys.stderr.write("WARNING: Could not find the names_to_tnrs_to_treestore executable")
        raise HTTP(501, T("Server is not configured to allow names_to_tnrs_to_treestore conversion"))
     
    ts = request.post_vars['treestore']
    if ts:
        args_to_pass.append('-t %s' % ts)

    st = request.post_vars['notnrs']
    if st:
        args_to_pass.append('--no-tnrs')
        
    t = request.post_vars['taxa']
    if not t:
        raise HTTP(503)
   
    f = NamedTemporaryFile(delete=False)
    f.write(t)
    n = f.name
    f.close()
    args_to_pass.append(n)
    
    o = subprocess.check_output(args_to_pass)
    '''
    if treestore:
        o = subprocess.check_output([sys.executable, exe, n, treestore])
    else:
        o = subprocess.check_output([sys.executable, exe, n])
    '''

    os.unlink(n)
    return json.dumps(o)

