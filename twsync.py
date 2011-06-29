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
import signal
import searchhtml
import pycurl
import traceback
from httphelp import url_fetch
from httphelp import getImage
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

def findUrl(msg):
    m=re.search("http:\/\/[^\s]+",msg)
    return m and str(m.group(0))

def send_sina_msgs(msg,coord=None):
    try:
      logging.info("send_sina_msgs: "+msg)
      msg=unescape(msg)
      url=findUrl(msg)
      image=url and getImage(url)
      if image:
        logging.info('send pic')
        return sina.send_pic(msg,image,coord)
  
      return sina.send_msg(msg,coord)
    except:
      exc=sys.exc_info()
      logging.error(exc[1].__str__())
      logging.error(len(exc)>2 and traceback.format_exc(exc[2]) or str(exc))
      return False

#get one page of to user's replies, 20 messages at most. 
def parseTwitter(twitter_id,since_id="",):
    if since_id:
        url="http://api.twitter.com/1/statuses/user_timeline.json?trim_user=true&include_rts=true&screen_name=%s&since_id=%s"%(twitter_id,since_id)
    else:
        url="http://api.twitter.com/1/statuses/user_timeline.json?trim_user=true&include_rts=true&screen_name=%s"%twitter_id
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
  users=load_users()
  synced=0
  for username in users:
    user=users[username]
    if user['activated']:
      id=sync_user(user)
      if (id):
        users[username]['last_tweet']=id
        synced+=1

  if synced>0:
    save_users(users)

def sync_user(user):
  sina.set_access_token(user['sina_token'])
  return parseTwitter(twitter_id=user['twitter_name'],since_id=user['last_tweet'])

def find_user(username):
  return load_users()[username]

def load_users():
  f=file('users.yaml','r')
  users=yaml.load(f.read())
  f.close()
  return users

def save_users(users):
  f=file('users.yaml','w')
  yaml.dump(users,stream=f)
  f.close()

def start_daemon():
  pid=os.fork()
  if pid:
    f=file('twsync.pid','w')
    f.write(str(pid))
    f.close()
    print 'start sync daemon'
  else:
    print 'sync daemon started'
    while True:
      sync_once()
      time.sleep(sync_interval)

def stop_daemon():
  pid=get_running_daemon()
  if pid:
    os.kill(pid,signal.SIGHUP)
    print 'twsync daemon (%d) killed'%pid
  else:
    print 'Error: twsync is not started'

def display_help():
  print 'Usage:'
  print 'python twsync.py {start|stop|restart}'
  print 'python twsync.py status'
  print 'python twsync.py once [username]'
  print ''

def get_running_daemon():
  if os.path.exists('twsync.pid'):
    try:
      f=file('twsync.pid','r')
      pid=f.read()
      f.close()
      for line in os.popen('ps ax'):
        if pid==line.split()[0]:
          return int(pid)
    except:
      pass
  return 0

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
sync_interval=config.get('sync_interval') or 300

if len(sys.argv)<2:
  display_help()
  exit()

if sys.argv[1]=='start':
  if get_running_daemon():
    print 'Error: twsync is already started'
  else:
    start_daemon()
elif sys.argv[1]=="stop":
  stop_daemon()
elif sys.argv[1]=="restart":
  stop_daemon()
  start_daemon()
elif sys.argv[1]=="status":
  pid=get_running_daemon()
  if pid:
    print 'twsync is running (pid:%d)'%pid
  else:
    print 'twsync is not running'
elif sys.argv[1]=="once":
  if len(sys.argv)>2:
    username=sys.argv[2]
    print 'sync user '+username
    sync_user(find_user(username))
  else:
    print 'sync once'
    sync_once()
else:
  display_help()
