from urlparse import urlparse,parse_qsl,parse_qs
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

def login(path,params,env):
    logger.info('apply')
    url,token=users.apply('http://'+env['HTTP_HOST']+'/authorized')
    headers=[
      ('Set-Cookie', 'token='+token),
      ('Set-Cookie', 'twitter_name='+params.get('twitter_name','')),
      ('Location', url),
    ]
    return ("302 Found", headers,'') 

def logout(path,params,env):
    headers=[
      ('Set-Cookie', 'token='),
      ('Set-Cookie', 'twitter_name='),
      ('Set-Cookie', 'sina_name='),
      ('Set-Cookie', 'session='),
      ('Set-Cookie', 'userid='),
      ('Location', '/'),
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
    logger.debug(str(user))
    cs1='sina_name=%s'%urllib.quote_plus(user['sina_name'].encode('unicode_escape'))
    cs2='session=%s'%user['session']
    cs3='userid=%s'%user['sina_id']

    headers=[
      ('Content-Type', 'text/plain'),
      ('Location', '/settings'),
      ('Set-Cookie', cs1),
      ('Set-Cookie', cs2),
      ('Set-Cookie', cs3),
    ]

    return ("302 Found", headers, '')

def settings(path,params,env):
   allusers=users.load_users()
   user=__get_user(env,allusers)
   userid=str(user['sina_id'])

   if user :
     print 'authorized'
     # authorized
     try:
        request_body_size = int(env.get('CONTENT_LENGTH', 0))
     except (ValueError):
        request_body_size = 0

     if request_body_size:
       # save settings
       request_body=env['wsgi.input'].read(request_body_size)
       d=parse_qs(request_body)
       allusers[userid]['twitter_name']=twitter_name=d['twitter_name'][0]
       allusers[userid]['activated']=d.get('activated') and True or False
       allusers[userid]['ignore_tag']=d.get('ignore_tag',[''])[0]
       allusers[userid]['no_trunc']=not d.get('keep_original')
       allusers[userid]['rasterize']=d.get('rasterize') and True or False
       users.save_users(allusers)
       # redirect to synced
       status="302 Found"
       headers=[
        ('Content-Type', 'text/plain'),
        ('Location', '/synced'),
        ('Set-Cookie', 'twitter_name=%s'%twitter_name),
       ]
       content=''
     else:
       # render settings
       status="200 OK"
       headers=[('Content-Type', 'text/html;charset=UTF-8')]
       user['activated_checked']=user['activated'] and 'checked="1"' or ''
       user['userinfo']=__render_userinfo(user)
       user['ignore_tag'] = user['ignore_tag'].replace('"', '&quot;')
       user['keep_original'] = (not user.get('no_trunc', True)) and 'checked="1"' or ''
       user['rasterize_checked']=user.get('rasterize') and 'checked="1"' or ''
       content=__template(dirname+'/settings.html',user).encode('utf-8')
   else:
     # unauthorized
     logger.info('unauthorized')
     status="302 Found"
     headers=[
      ('Content-Type', 'text/plain'),
      ('Location', '/'),
     ]
     content=''
   
   return (status, headers, content)


def synced(path,params,env):
    cookie=Cookie.SimpleCookie(env['HTTP_COOKIE'])
    twittername=cookie['twitter_name'].value
    sinaname=cookie['sina_name'].value
    sinaname=urllib.unquote_plus(sinaname).decode('unicode_escape')
    values={'twittername':twittername,'sinaname':sinaname}
    content=__template(dirname+'/synced.html',values)
    return ("200 OK", [('Content-Type', 'text/html;charset=UTF-8')], content.encode('utf-8'))

def index(path,params,env):
    allusers=users.load_users()
    user=__get_user(env,allusers)
    content=__template(dirname+'/index.html',{'userinfo':__render_userinfo(user)})
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

def __template(filename,values):
    f=file(filename,'r')
    content=f.read()
    f.close()
    for k in values:
      tag='${'+k+'}'
      v=values[k]
      if v or type(v)==str:
        content=content.replace(tag,unicode(v))
    return content

def __get_user(env,allusers):
   cookie=Cookie.SimpleCookie(env.get('HTTP_COOKIE'))
   if not cookie:
     return None
   try:
     sina_name=cookie['sina_name'].value.decode('unicode_escape')
     userid=cookie['userid'].value
     session=cookie['session'].value
     user=allusers.get(userid)
     return user and (user['session']==session) and user
   except:
     logger.debug('something wrong')
     user=None

def __render_userinfo(user):
    if user:
      return "Hi %s | [<a href='/logout'>logout</a>]"%user['sina_name']
    else:
      return ""

def application(environ, start_response):
    logger.info('application')
    logger.info(str(sys.argv))
    controller=shift_path_info(environ)
    params=dict(parse_qsl(environ['QUERY_STRING']))
    if controller=='':
      controller='index'

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
