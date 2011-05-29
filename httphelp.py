import time
import pycurl

def url_fetch(url,post=None,headers=None,proxy=None,retry=3):
  b=StringIO()
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
      c.setopt(c.WRITEFUNCTION,b.write)
      c.perform()
      retry=0
    except:
      logging.debug("retry %d more"%retry)

    time.sleep(1)

  return {'status_code':c.getinfo(pycurl.HTTP_CODE),'content':b.getvalue()}


