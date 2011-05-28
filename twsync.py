#!/usr/bin/env python
# -*- coding: utf-8 -*-

#to ensure the utf8 encoding environment
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
import base64
import re
import htmlentitydefs
import time
import urllib,Cookie
import pycurl
from StringIO import StringIO
import logging
import yaml
import secure
import getpass

def url_fetch(url,post=None,headers=None,proxy=None,retry=3):
  while(retry>0):
    retry-=1
    try:
      c=pycurl.Curl()
      c.setopt(pycurl.URL,url)
      if proxy:
        c.setopt(pycurl.PROXY,proxy['host'])
        c.setopt(pycurl.PROXYPORT,proxy['port'])
        c.setopt(pycurl.PROXYTYPE,proxy['type'])
      if post:
        c.setopt(pycurl.POST,1)
        c.setopt(pycurl.POSTFIELDS,post)
      if headers:
        c.setopt(pycurl.HTTPHEADER,headers)
      b=StringIO()
      c.setopt(c.WRITEFUNCTION,b.write)
      c.perform()
      retry=0
    except:
      logging.debug("retry %d more"%retry)

    time.sleep(1)

  return {'status_code':c.getinfo(pycurl.HTTP_CODE),'content':b.getvalue()}

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

def send_sina_msgs(username,password,msg):
    logging.info("send_sina_msgs: "+msg)
    auth=base64.b64encode(username+":"+password)
    auth='Basic '+auth
    msg=unescape(msg)
    form_fields = {
      "status": msg,
    }
    form_data = urllib.urlencode(form_fields)
    proxy=config['twitter']['use_proxy'] and sync_proxy
    result = url_fetch("http://api.t.sina.com.cn/statuses/update.xml?source="+sina_appkey,
      proxy=proxy,
      post=form_data,
      headers=['Authorization: '+auth]
      )
    if result['status_code'] == 200:
        bk=result['content']
        logging.debug("sina returned")
        if bk.find("true"):
            logging.info("sina updated")
            return True
    else:
        logging.warning("sina update failed (code:%d) {%s}"%(result['status_code'],result['content']))
    return False

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
                if send_sina_msgs(config['sina']['username'],sina_pwd,text):
                    putLatest(id)
                    time.sleep(1)
            else:
                logging.debug('ignore (%s) %s'%(id,text))
    else:
        logging.warning("get twitter data error:\n"+result['content'])
        
####################
# main starts here
####################
logging.basicConfig(filename='twsync.log',level=logging.DEBUG)
pwd=getpass.getpass('input admin password to start:')
cipher=secure.getcipher(pwd)
f=file('config.yaml','r')
config=yaml.load(f.read())
f.close()
sina_pwd=secure.decode(cipher,config['sina']['password'])
sina_appkey=secure.decode(cipher,config['sina']['appkey'])
if not sina_pwd:
  print 'incorrect admin password.'
  exit()
sync_proxy=config['proxy']
sync_proxy['type']=get_curl_proxy_type(config['proxy']['type'])

while True:
   latest=getLatest() 
   parseTwitter(twitter_id=config['twitter']['username'],since_id=latest)
   time.sleep(300)
