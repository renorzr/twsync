import sgmllib

class MyParser(sgmllib.SGMLParser):
  def parse(self,s):
    self.site=None
    if s.find('picplzthumbs')!=-1:
      self.site='picplz'
    elif s.find('staticflickr.com')!=-1:
      self.site='flickr'
    elif s.find('instagram-static')!=-1:
      self.site='instagram'
    elif s.find('<meta content="foursquare')!=-1:
      self.site='4sq'
    elif s.find('twitpic.com/show/')!=-1:
      self.site='twitpic'

    self.feed(s)
    self.close()

  def __init__(self,verbose=0):
    sgmllib.SGMLParser.__init__(self,verbose)
    self.url=None

  def start_img(self,attr):
    found=False
    for name,value in attr:
      if (self.site=='picplz' and name=="id" and value=="mainImage") or \
         (self.site=='instagram' and name=="class" and value=="photo") or \
         (self.site=='flickr' and name=="alt" and value=="photo") or \
         (self.site=='4sq' and name=="class" and value=="mainPhoto") or \
         (self.site=='twitpic' and name=='id' and value=='photo-display'):
        found=True
      elif name=="src":
        self.url=value
    if found:
      self.setnomoretags()
      return
    self.url=None

def searchImage(content):
  parser=MyParser()

  try:
    parser.parse(content)
  except:
    pass

  return parser.url
