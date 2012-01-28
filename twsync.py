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
import urllib
import random

def rasterize_msg(msg, coord, pic):
    params = {'text': msg.encode('utf-8')}
    result = url_fetch(config['raster_url'], urllib.urlencode(params))
    return result['content']

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

def findUrls(msg):
    exp = re.compile("http:\/\/[^\s]+")
    return exp.findall(msg)
    
def resolveShortUrls(msg):
    urls = findUrls(msg)
    for url in urls:
      try:
        dest = urllib.urlopen(url).url
        msg = msg.replace(url, dest)
      except:
        pass

    return urls, msg

def send_sina_msgs(msg,coord=None,rasterize=False):
    try:
      msg=unescape(msg)
      urls, msg = resolveShortUrls(msg)
      logger.info("send_sina_msgs: "+msg)

      image = urls and urls[0] and getImage(urls[0])
      if image:
        logger.info('send pic')
        try:
          return sina.send_pic(msg,image,coord)
        except:
          exc = sys.exc_info()
          logger.warn(exc[1].__str__())
  
      return sina.send_msg(msg,coord)
    except:
      exc=sys.exc_info()
      logger.error(exc[1].__str__())
      logger.error(len(exc)>2 and traceback.format_exc(exc[2]) or str(exc))
      return False

def send_pic_sina_msg(t):
    try:
      geo=t['geo']
      coord=geo and geo['coordinates']
      msg = t['text']
      if t.get('retweeted_status'):
        msg = msg.split(': ')[0] + ': ' + t['retweeted_status']['text']
      pic = t.get('media_url')
      rasterized = rasterize_msg(msg, coord, pic)
      tweet_time = t['created_at']
      return sina.send_pic('from twitter (by twsync.zhirui.org) ' + tweet_time, rasterized, coord)
    except:
      logger.error('failed to send rasterized')
      exc=sys.exc_info()
      logger.error(exc[1].__str__())
      logger.error(len(exc)>2 and traceback.format_exc(exc[2]) or str(exc))
      return False

#get one page of to user's replies, 20 messages at most. 
def parseTwitter(twitter_id, since_id=None, ignore_tag='@', no_trunc=False, rasterize=False):
    if since_id:
        url="http://api.twitter.com/1/statuses/user_timeline.json?trim_user=true&include_rts=true&screen_name=%s&since_id=%s"%(twitter_id,since_id)
    else:
        url="http://api.twitter.com/1/statuses/user_timeline.json?trim_user=true&include_rts=true&screen_name=%s&count=5"%twitter_id
    proxy=config['twitter']['use_proxy'] and sync_proxy
    result = url_fetch(url,proxy=proxy)
    if result['status_code'] == 200:
        content=result['content']
        tweets=json.loads(content)
        lastid=None
        for t in reversed(tweets):
            id=str(t['id'])
            rt=t.get('retweeted_status')
            text=(rt and t['truncated'] and no_trunc) and rt['text'] or t['text']
            geo=t['geo']
            coord=geo and geo['coordinates']
            if not (ignore_tag and text.startswith(ignore_tag)):
                logger.info('sync (%s) %s'%(id,text))
                if rasterize:
                    if send_pic_sina_msg(t):
                        lastid=id
                        time.sleep(1)
                elif send_sina_msgs(text,coord):
                    lastid=id
                    time.sleep(1)
            else:
                logger.debug('ignore (%s) %s'%(id,text))
                lastid=id
        return lastid
    else:
        logger.warning("get twitter data error: ("+str(result['status_code'])+")\n"+result['content'])
        
def sync_once():
  users=load_users()
  synced=0
  for username in users:
    user=users[username]
    if user.get('activated') and user.has_key('twitter_name'):
      id=sync_user(user)
      if (id):
        users[username]['last_tweet']=id
        synced+=1

  if synced>0:
    save_users(users)

def sync_user(user):
  logger.info('sync user %s <- %s'%(user['sina_name'],user['twitter_name']))
  sina.set_access_token(user['sina_token'])
  return parseTwitter(twitter_id=user['twitter_name'],since_id=user.get('last_tweet'),ignore_tag=user.get('ignore_tag','@'),no_trunc=user.get('no_trunc',False),rasterize=user.get('rasterize'))

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
      logger.info('begin sync cycle')
      sync_once()
      logger.info('end sync cycle')
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
logger=logging.getLogger('twsync')
h=logging.FileHandler('twsync.log')
fmt=logging.Formatter('%(asctime)s %(levelname)s %(message)s')
h.setFormatter(fmt)
logger.addHandler(h)
logger.setLevel(logging.DEBUG)

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
