import time
from StringIO import StringIO
import pycurl
import base64
import searchhtml

class Storage:
    def __init__(self):
        self.contents = ''

    def store(self, buf):
        self.contents = self.contents+buf

    def __str__(self):
        return self.contents

    def headers(self):
        h=[]
        r={}
        for l in self.contents.split('\n'):
          if l.strip()=='':
            len(r) and h.append(r)
            r={}
          else: 
            spidx=l.find(':')
            r[l[:spidx]]=l[spidx+1:].strip()
        return h

class LimitedBuffer():
  def __init__(self, buffer = None, maxsize = 2 * 1024 * 1024):
    self.buffer  = ''
    self.maxsize = maxsize

  def write(self, s):
    self.buffer += s
    if (len(self.buffer) > self.maxsize):
      return -1
    else:
      return len(s)

  def getvalue(self):
    return self.buffer

def url_fetch(url,post=None,headers=None,proxy=None,retry=3):
  b=LimitedBuffer() #StringIO()
  res_headers=Storage()
  while(retry>0):
    retry-=1
    try:
      c=pycurl.Curl()
      c.setopt(pycurl.URL,str(url))
      c.setopt(pycurl.FOLLOWLOCATION,1)
      if proxy:
        c.setopt(pycurl.PROXY,proxy['host'])
        c.setopt(pycurl.PROXYPORT,proxy['port'])
        c.setopt(pycurl.PROXYTYPE,proxy['type'])
      if post:
        c.setopt(pycurl.POST,1)
        c.setopt(pycurl.POSTFIELDS,post)
      if headers:
        c.setopt(pycurl.HTTPHEADER,headers)
      c.setopt(c.WRITEFUNCTION,b.write)
      c.setopt(c.HEADERFUNCTION, res_headers.store)
      c.perform()
      retry=0
    except:
      pass

    time.sleep(1)

  return {'status_code':c.getinfo(pycurl.HTTP_CODE),'content':b.getvalue(),'headers':res_headers.headers()}

def getImage(url,proxy=None):
  r=url_fetch(url,proxy)

  content_type = r['headers'] and r['headers'][-1]['Content-Type']
  if content_type and content_type[:5]=='image':
    return r['content']

  if content_type and content_type[:9]=='text/html':
    url=searchhtml.searchImage(r['content'])
    r=url_fetch(url,proxy)
    return r['content']

  return None
