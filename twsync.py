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
import os
import searchhtml
import pycurl
from httphelp import url_fetch
from sinaclient import SinaClient
import json

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

def getImageUrl(msg):
    url=None
    m=re.search("http:\/\/((flic\.kr|instagr\.am)\/p|picplz\.com|4sq.com|twitpic.com)\/\w+",msg)
    if m:
      url=str(m.group(0))
      r=url_fetch(url)
      content=r['content']
      logging.info('imagepage:'+url+' status_code:'+str(r['status_code']))
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

def send_sina_msgs(msg,coord=None):
    try:
      logging.info("send_sina_msgs: "+msg)
      msg=unescape(msg)
      image=getImage(msg)
      if image:
        logging.info('send pic')
        f=file('temp.jpg','w')
        f.write(image)
        f.close()
        return sina.send_pic(msg,'temp.jpg',coord)
  
      return sina.send_msg(msg,coord)
    except:
      exc=sys.exc_info()
      logging.error(exc[1].__str__())
      logging.error(str(exc))
      return False

#get one page of to user's replies, 20 messages at most. 
def parseTwitter(twitter_id,since_id="",):
    if since_id:
        url="http://twitter.com/statuses/user_timeline/%s.json?since_id=%s"%(twitter_id,since_id)
    else:
        url="http://twitter.com/statuses/user_timeline/%s.json"%(twitter_id)
    proxy=config['twitter']['use_proxy'] and sync_proxy
    result = url_fetch(url,proxy=proxy)
    if result['status_code'] == 200:
        content=result['content']
        tweets=json.loads(content)
        lastid=None
        for t in reversed(tweets):
            id=str(t['id'])
            text=t['text']
            geo=t['geo']
            coord=geo and geo['coordinates']
            if text[0]!='@':
                logging.info('sync (%s) %s'%(id,text))
                if send_sina_msgs(text,coord):
                    lastid=id
                    time.sleep(1)
            else:
                logging.debug('ignore (%s) %s'%(id,text))
        return lastid
    else:
        logging.warning("get twitter data error: ("+str(result['status_code'])+")\n"+result['content'])
        
def sync_once():
  f=file('users.yaml','r')
  users=yaml.load(f.read())
  f.close()
  synced=0
  for username in users:
    user=users[username]
    sina.set_access_token(user['sina_token'])
    id=parseTwitter(twitter_id=username,since_id=user['last_tweet'])
    if (id):
      users[username]['last_tweet']=id
      synced+=1

  if synced>0:
    f=file('users.yaml','w')
    yaml.dump(users,stream=f)
    f.close()

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
sync_interval=config['sync_interval'] or 300

if len(sys.argv)>1 and sys.argv[1]=='-d':
  pid=os.fork()
  
  if pid:
    print 'start sync daemon'
  else:
    print 'sync daemon started'
    while True:
      sync_once()
      time.sleep(sync_interval)
else:
  print 'sync once'
  sync_once()
