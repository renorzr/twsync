import sgmllib

class MyParser(sgmllib.SGMLParser):
  def parse(self,s):
    self.feed(s)
    self.close()

  def __init__(self,verbose=0):
    sgmllib.SGMLParser.__init__(self,verbose)
    self.url=None

  def start_img(self,attributes):
    for name,value in attributes:
      if name=="id" and value=="mainImage":
        self.url=attributes.get("src")
        return

def picplzImage(content):
  parser=MyParser()
  parser.parse(content)
  return parser.url
