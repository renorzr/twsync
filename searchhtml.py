import sgmllib

class MyParser(sgmllib.SGMLParser):
  def parse(self,s):
    self.feed(s)
    self.close()

  def __init__(self,verbose=0):
    sgmllib.SGMLParser.__init__(self,verbose)
    self.url=None

  def start_img(self,attr):
    found=False
    for name,value in attr:
      if name=="id" and value=="mainImage":
        found=True
      elif name=="src":
        self.url=value
    if found:
      self.setnomoretags()
      return

def picplzImage(content):
  parser=MyParser()
  parser.parse(content)
  return parser.url
