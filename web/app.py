from urlparse import urlparse,parse_qsl
from wsgiref.util import shift_path_info
import re
import Cookie
import logging
import sys
import os
import urllib

dirname=os.path.dirname(os.path.realpath(__file__))
logger=logging.getLogger('webtwsync')
h=logging.FileHandler(dirname+'/webtwsync.log')
fmt=logging.Formatter('%(asctime)s %(levelname)s %(message)s')
h.setFormatter(fmt)
logger.addHandler(h)
logger.setLevel(logging.DEBUG)

sys.path.append(dirname+'/../')
import users

def apply(path,params,env):
    logger.info('apply')
    url,token=users.apply('http://'+env['HTTP_HOST']+'/authorized')
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
    succ,user=users.add(token,verifier,name)
    logger.info('add user '+(succ and 'ok' or 'failed'))
    cookiestr='sina_name=%s'%urllib.quote_plus(user['sina_name'].encode('unicode_escape'))

    headers=[
      ('Content-Type', 'text/plain'),
      ('Location', '/synced'),
      ('Set-Cookie', cookiestr),
    ]

    return ("302 Found", headers, '')

def synced(path,params,env):
    f=file(dirname+'/synced.html','r')
    content=f.read()
    f.close()
    cookie=Cookie.SimpleCookie(env['HTTP_COOKIE'])
    twittername=cookie['twitter_name'].value
    sinaname=cookie['sina_name'].value
    print 'sinaname=',sinaname
    sinaname=urllib.unquote_plus(sinaname).decode('unicode_escape')
    print 'decoded sinaname=',sinaname
    content=content.replace('{twittername}',twittername)
    content=content.replace('{sinaname}',sinaname)
    return ("200 OK", [('Content-Type', 'text/html;charset=UTF-8')], content.encode('utf-8'))

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
    return [content]


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
