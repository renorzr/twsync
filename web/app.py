from urlparse import urlparse,parse_qsl
from wsgiref.util import shift_path_info
import re
import commands
import Cookie
import logging
import sys
import os

dirname=os.path.dirname(os.path.realpath(__file__))
logger=logging.getLogger('webtwsync')
h=logging.FileHandler(dirname+'/webtwsync.log')
fmt=logging.Formatter('%(asctime)s %(levelname)s %(message)s')
h.setFormatter(fmt)
logger.addHandler(h)
logger.setLevel(logging.DEBUG)

def apply(path,params,env):
    logger.info('apply')
    cmd='cd '+dirname+'/..;python users.py apply http://'+env['HTTP_HOST']+'/authorized'
    logger.debug(cmd)
    status,output=commands.getstatusoutput(cmd)
    logger.info('user apply status='+str(status))
    logger.debug(output)
    url,token=output.split("\n")
    headers=[
      ('Content-Type', 'text/plain'),
      ('Set-Cookie', 'token='+token),
      ('Set-Cookie', 'twitter_name='+params['twitter_name']),
      ('Location', url),
    ]
    return ("302 Found", headers,'') 

def authorized(path,params,env):
    logger.info('authorized')
    cookie=Cookie.SimpleCookie(env['HTTP_COOKIE'])
    token=cookie['token'].value
    verifier=params['oauth_verifier']
    name=cookie['twitter_name'].value
    logger.debug('token=%s verfier=%s name=%s'%(token,verifier,name))
    cmd='cd '+dirname+'/..;python users.py add "%s" %s %s'%(token,verifier,name)
    logger.debug(cmd)
    status,output=commands.getstatusoutput(cmd)
    logger.info('user add status='+str(status))
    logger.debug(output)

    headers=[
      ('Content-Type', 'text/plain'),
      ('Location', '/static/synced.html'),
    ]

    return ("302 Found", headers, '')

def static(path,params,env):
    m=re.search('\.(jpg|gif|png|htm|html|js|css|txt)$',path)
    if not m:
      return ("403 Forbidden",[('Content-Type', 'text/plain')],"Forbidden")

    t=m.groups(0)[0]
    if t=='jpg' or t=='gif' or t=='png':
      content_type='image/'+t
    elif t=='html' or t=='htm' or t=='js' or t=='css' or t=='txt':
      content_type='text/'+t
    else:
      content_type='text/plain'
    headers=[('Content-Type',content_type)]

    f=file(dirname+'/'+path,'r')
    content=f.read()
    f.close()
    return ("200 OK", headers,content) 

def application(environ, start_response):
    logger.info('application')
    logger.info(str(sys.argv))
    controller=shift_path_info(environ)
    params=dict(parse_qsl(environ['QUERY_STRING']))
    if controller=='':
      controller='static'
      environ['PATH_INFO']='index.html'

    controller=globals().get(controller)
    if controller:
      status, headers, content=controller(environ['PATH_INFO'],params,environ)
    else:
      status="404 Not Found"
      headers=[]
      content="Page Not Found"

    start_response(status,headers)
    yield content


if __name__ == "__main__":
  try:
    from wsgiref.simple_server import make_server
    port=(len(sys.argv)>1) and int(sys.argv[1]) or 8000
    print 'server on port: %i'%port
    httpd = make_server('', port, application)
    httpd.serve_forever()
  except Exception, e:
    print e
    import wsgiref.handlers
    wsgiref.handlers.CGIHandler().run(application)
