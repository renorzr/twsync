import time
from StringIO import StringIO
import pycurl
import base64

def url_fetch(url,post=None,headers=None,proxy=None,retry=3):
  b=StringIO()
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
      c.perform()
      retry=0
    except:
      pass

    time.sleep(1)

  return {'status_code':c.getinfo(pycurl.HTTP_CODE),'content':b.getvalue()}

def pic_multiple_body(msg,pic):
  body="""Content-type: multipart/form-data, boundary=AaB03x

--AaB03x
content-disposition: form-data; name="status"

%s
--AaB03x
content-disposition: form-data; name="pic"
Content-Type: image/jpg
Content-Transfer-Encoding: base64

%s
--AaB03x--
"""
  return body%(msg,base64.b64encode(pic))
