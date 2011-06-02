import sgmllib

class MyParser(sgmllib.SGMLParser):
  def parse(self,url,s):
    self.site=None
    if url.find('picplz.com')!=-1:
      self.site='picplz'
    elif url.find('flic.kr')!=-1:
      self.site='flickr'
    elif url.find('instagr.am')!=-1:
      self.site='instagram'

    self.feed(s)
    self.close()

  def __init__(self,verbose=0):
    sgmllib.SGMLParser.__init__(self,verbose)
    self.url=None

  def start_img(self,attr):
    found=False
    for name,value in attr:
      if (self.site=='picplz' and name=="id" and value=="mainImage") or(self.site=='instagram' and name=="class" and value=="photo") or (self.site=='flickr' and name=="alt" and value=="photo"):
        found=True
      elif name=="src":
        self.url=value
    if found:
      self.setnomoretags()
      return

def searchImage(url, content):
  parser=MyParser()
  parser.parse(url,content)
  return parser.url
