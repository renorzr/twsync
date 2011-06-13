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
    elif url.find('4sq.com')!=-1:
      self.site='4sq'

    self.feed(s)
    self.close()

  def __init__(self,verbose=0):
    sgmllib.SGMLParser.__init__(self,verbose)

  def start_img(self,attr):
    found=False
    self.url=None
    for name,value in attr:
      if (self.site=='picplz' and name=="id" and value=="mainImage") or(self.site=='instagram' and name=="class" and value=="photo") or (self.site=='flickr' and name=="alt" and value=="photo") or (self.site=='4sq' and name=="class" and value=="mainPhoto"):
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
