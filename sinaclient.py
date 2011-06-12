from weibopy.auth import OAuthHandler, BasicAuthHandler
from weibopy.api import API

class SinaClient:
    def __init__(self, key, secret):
        self.auth=OAuthHandler(key,secret)

    def get_auth_url(self):
        return self.auth.get_authorization_url()

    def set_access_token(self,token):
        key,secret=token.split('|')
        self.auth.setToken(key,secret)
        self.api=API(self.auth)

    def get_access_token(self):
        token=self.auth.access_token
        return token.key+'|'+token.secret

    def set_verifier(self,verifier):
        self.auth.get_access_token(verifier)
        self.api=API(self.auth)

    def send_msg(self,msg,coord=None):
        lat,long=self.get_lat_long(coord)
        msg=msg.encode('utf-8')
        status=self.api.update_status(status=msg,lat=lat,long=long)
        return status

    def send_pic(self,msg,pic,coord=None):
        lat,long=self.get_lat_long(coord)
        msg=msg.encode('utf-8')
        status=self.api.upload(pic,status=msg,lat=lat,long=long)
        
        return status

    def get_timeline(self):
        return self.request(SINA_USER_TIMELINE_URL)

    def get_lat_long(self,coord):
        if not coord:
          return (None,None)

        return map(lambda x:str(x),coord)
