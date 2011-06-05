#!/usr/bin/env python
# -*- coding: utf-8 -*-

#to ensure the utf8 encoding environment
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
import re
import htmlentitydefs
import time
import logging
import yaml
import getpass
import os
import searchhtml
from httphelp import url_fetch
from httphelp import pic_multiple_body
from sinaclient import SinaClient

def make_cookie_header(cookie):
    ret = ""
    for val in cookie.values():
        ret+="%s=%s; "%(val.key, val.value)
    return ret

def get_curl_proxy_type(t):
    if t=='socks5':
        return pycurl.PROXYTYPE_SOCKS5
    elif t=='sockss':
        return pycurl.PROXYTYPE_SOCKS4
    elif t=='http':
        return pycurl.PROXYTYPE_HTTP

    raise Exception('supported proxy types: http, socks4 and socks5')

def unescape(text):
   """Removes HTML or XML character references 
      and entities from a text string.
   from Fredrik Lundh
   http://effbot.org/zone/re-sub.htm#unescape-html
   """
   def fixup(m):
       text = m.group(0)
       if text[:2] == "&#":
           # character reference
           try:
               if text[:3] == "&#x":
                   return unichr(int(text[3:-1], 16))
               else:
                   return unichr(int(text[2:-1]))
           except ValueError:
               pass
       else:
           # named entity
           try:
               text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
           except KeyError:
               pass
       return text # leave as is
   return re.sub("&#?\w+;", fixup, text)

def getLatest():
  try:
    f=file('latest','r')
    l=f.readline()
    f.close()
    return l
  except:
    return None

def putLatest(id):
    f=file('latest','w')
    f.write(id)
    f.close

def getImageUrl(msg):
    url=None
    m=re.search("http:\/\/((flic\.kr|instagr\.am)\/p|picplz\.com)\/\w+",msg)
    if m:
      url=m.group(0)
      content=url_fetch(url)['content']
      url=searchhtml.searchImage(url,content)
    else:
      m=re.search("\[pic\](http:\/\/[^s]+)",msg)
      url=m and m.group(1)

    return url

def getImage(msg):
    url=getImageUrl(msg)
    if url:
      return url_fetch(url)['content']
    return None

def send_sina_msgs(msg):
    logging.info("send_sina_msgs: "+msg)
    msg=unescape(msg)
#    if image:
#      f=file('pic.tmp','w')
#      f.write(image)
#      f.close()
#      cmd='curl -u "%s:%s" -F "pic=@pic.tmp" -F "status=%s" "http://api.t.sina.com.cn/statuses/upload.json?source=%s"'%(username,password,msg,sina_appkey)
#      return os.system(cmd)==0:

    return sina.send_msg(msg)

#get one page of to user's replies, 20 messages at most. 
def parseTwitter(twitter_id,since_id="",):
    if since_id:
        url="http://twitter.com/statuses/user_timeline/%s.xml?since_id=%s"%(twitter_id,since_id)
    else:
        url="http://twitter.com/statuses/user_timeline/%s.xml"%(twitter_id)
    proxy=config['twitter']['use_proxy'] and sync_proxy
    result = url_fetch(url,proxy=proxy)
    if result['status_code'] == 200:
        content=result['content']
        m= re.findall(r"(?i)<id>([^<]+)</id>\s*<text>(?!@)([^<]+)</text>", content)
        for x in reversed(m):
            id=x[0]
            text=x[1]
            if text[1]!='@':
                logging.info('sync (%s) %s'%(id,text))
                if send_sina_msgs(text):
                    putLatest(id)
                    time.sleep(1)
            else:
                logging.debug('ignore (%s) %s'%(id,text))
    else:
        logging.warning("get twitter data error:\n"+result['content'])
        
def save_access_token(token):
  f=file('token','w')
  f.write(token)
  f.close()

def read_access_token():
  try:
    f=file('token','r')
    t=f.read()
    f.close()
    return t
  except:
    return False

def sync_once():
  latest=getLatest() 
  parseTwitter(twitter_id=config['twitter']['username'],since_id=latest)

####################
# main starts here
####################
logging.basicConfig(filename='twsync.log',level=logging.DEBUG)
f=file('config.yaml','r')
config=yaml.load(f.read())
f.close()

sync_proxy=config['proxy']
use_proxy=config['sina']['use_proxy'] or config['twitter']['use_proxy']
sync_proxy['type']=use_proxy and get_curl_proxy_type(config['proxy']['type'])

sina=SinaClient(config['sina']['key'],config['sina']['secret'])
token=read_access_token()
if not token:
  url=sina.get_auth_url()
  verifier=raw_input('goto '+url+' get pin code:')
  sina.set_verifier(verifier)
  token=sina.get_access_token()
  save_access_token(token)

sina.set_access_token(token)

if len(sys.argv)>1 and sys.argv[1]=='-d':
  pid=os.fork()
  
  if pid:
    print 'start sync daemon'
  else:
    print 'sync daemon started'
    while True:
      sync_once()
      time.sleep(300)
else:
  sync_once()
