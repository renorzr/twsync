"""
The MIT License

Copyright (c) 2007 Leah Culver

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Example consumer. This is not recommended for production.
Instead, you'll want to create your own subclass of OAuthClient
or find one that works with your web framework.
"""

import httplib
import time
import oauth

# settings for the local test consumer
SERVER = 'api.t.sina.com.cn'
PORT = 80

# fake urls for the test server (matches ones in server.py)
REQUEST_TOKEN_URL = 'http://api.t.sina.com.cn/oauth/request_token'
ACCESS_TOKEN_URL = 'http://api.t.sina.com.cn/oauth/access_token'
AUTHORIZATION_URL = 'http://api.t.sina.com.cn/oauth/authorize'
CALLBACK_URL = ''
SINA_USER_TIMELINE_URL = 'http://api.t.sina.com.cn/statuses/user_timeline.json'
SINA_UPDATE_URL = 'http://api.t.sina.com.cn/statuses/update.json'

# key and secret granted by the service provider for this consumer application - same as the MockOAuthDataStore
CONSUMER_KEY = '792169767'
CONSUMER_SECRET = '62928e39eed71eb8544eb57e7ce9c39d'

# example client using httplib with headers
class SimpleOAuthClient(oauth.OAuthClient):

    def __init__(self, server, port=httplib.HTTP_PORT, request_token_url='', access_token_url='', authorization_url=''):
        self.server = server
        self.port = port
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.connection = httplib.HTTPConnection("%s:%d" % (self.server, self.port))

    def fetch_request_token(self, oauth_request):
        # via headers
        # -> OAuthToken
        self.connection.request(oauth_request.http_method, self.request_token_url, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def fetch_access_token(self, oauth_request):
        # via headers
        # -> OAuthToken
        self.connection.request(oauth_request.http_method, self.access_token_url, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def authorize_token(self, oauth_request):
        # via url
        # -> typically just some okay response
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
        response = self.connection.getresponse()
        return response.read()

    def access_resource(self, url, oauth_request):
        # via post body
        # -> some protected resources
        headers = {'Content-Type' :'application/x-www-form-urlencoded'}
        self.connection.request('POST', url, body=oauth_request.to_postdata(), headers=headers)
        response = self.connection.getresponse()
        text=response.read()
        return {'status_code':response.status,'text':text}

class SinaClient:
    def __init__(self, key, secret):
        self.client = SimpleOAuthClient(SERVER, request_token_url=REQUEST_TOKEN_URL, access_token_url=ACCESS_TOKEN_URL, authorization_url=AUTHORIZATION_URL)
        self.consumer = oauth.OAuthConsumer(key, secret)
        self.signature_method_plaintext = oauth.OAuthSignatureMethod_PLAINTEXT()
        self.signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.request_token=None

    def gen_request_token(self):
        if self.request_token:
          return
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, callback=CALLBACK_URL, http_url=self.client.request_token_url)
        oauth_request.sign_request(self.signature_method_plaintext, self.consumer, None)
        self.request_token = self.client.fetch_request_token(oauth_request)
        
    def get_auth_url(self):
        self.gen_request_token()
        return '%s?oauth_token=%s'%(self.client.authorization_url,str(self.request_token.key))

    def set_access_token(self,token):
        key,secret=token.split('|')
        self.access_token=oauth.OAuthToken(key,secret)

    def get_access_token(self):
        return self.access_token.key+'|'+self.access_token.secret

    def set_verifier(self,verifier):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=self.request_token, verifier=verifier, http_url=self.client.access_token_url)
        oauth_request.sign_request(self.signature_method_plaintext, self.consumer, self.request_token)
        self.access_token = self.client.fetch_access_token(oauth_request)
        
    def request(self,url,params=None):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=self.access_token, http_method='POST', http_url=url, parameters=params)
        oauth_request.sign_request(self.signature_method_hmac_sha1, self.consumer, self.access_token)
        return self.client.access_resource(url,oauth_request)

    def send_msg(self,msg):
        return self.request(SINA_UPDATE_URL,{'status':msg})

    def get_timeline(self):
        return self.request(SINA_USER_TIMELINE_URL)
