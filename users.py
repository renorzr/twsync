import sys
import yaml
from sinaclient import SinaClient
from urllib import urlencode
import os
import random

###############################
## initialize
###############################
dirname=os.path.dirname(os.path.realpath(__file__))
f=file(dirname+'/config.yaml','r')
config=yaml.load(f.read())
f.close()

def upgrade():
  users=load_users()
  new_users={}
  sina=get_sina_client()
  for username in users:
    u=users[username]
    print 'sina_token:',u['sina_token']
    sina.set_access_token(u['sina_token'])
    sinauser=sina.get_user()
    new_users[str(sinauser.id)]={'sina_id':sinauser.id,'sina_name':sinauser.screen_name,'twitter_name':username,'sina_token':u['sina_token'],'last_tweet':u['last_tweet'],'activated':u['activated']}
  save_users(new_users)

def apply(callback):
  sina=get_sina_client()
  url=sina.get_auth_url()
  if callback:
    url+='&'+urlencode({'oauth_callback':callback})

  return (url,sina.get_request_token())

def add(token,verifier,twitter_name=None):
  sina=get_sina_client()
  sina.set_request_token(token)
  sina.set_verifier(verifier)
  token=sina.get_access_token()
  sinauser=sina.get_user()
  users=load_users()
  userid=str(sinauser.id)
  user=users.get(userid, {'activated': False})
  user['sina_id']=sinauser.id
  user['sina_name']=sinauser.screen_name
  user['sina_token']=token
  user['session']='%08X'%(random.random()*0xffffffff)
  user['activated']=user.get('activated',True)
  users[userid]=user
  if save_users(users):
    return (True, user)
  else:
    return (False, user)

def register(twitter_name):
  sina=get_sina_client()
  users=load_users()
  url=sina.get_auth_url()
  verifier=raw_input('goto '+url+' get pin code:')
  succ,user=add(sina.get_request_token(),verifier,twitter_name)
  print 'register '+(succ and 'ok' or 'fail')
  print format_user(user)

def rm(userid):
  users=load_users()
  if (users.has_key(userid)):
    user=users[userid]
    del(users[userid])
    return (save_users(users),user)
  return (False,None)

def ls():
  users=load_users()
  print '\n'.join(map(lambda u:format_user(u),users.values()))

def act(userid,active):
  users=load_users()
  if (users.has_key(userid)):
    users[userid]['activated']=active
    return (save_users(users),users[userid])
  return (False,None)

def get(userid):
  return load_users.get(userid)
  
def format_user(u):
  return "%s\t%s\t%s\t%s"%(u['sina_id'],u['sina_name'].ljust(20),u.get('twitter_name','').ljust(20),(u['activated'] and 'activated' or 'non-activated'))

def help():
  print """Usage: python users.py options args
options:
apply [callback url]                    : apply for add user
add <token> <verifier> <twitter name>   : add a user
register <twitter name>                 : register a user
rm <userid>                             : remove user
act <userid> <1|0>                      : activate(1) or deactivate(0) a user
ls                                      : list all users
"""

def load_users():
  users={}
  try:
    f=file(dirname+'/users.yaml','r')
    users=yaml.load(f.read())
    f.close()
  except:
    users={}
  return users

def save_users(users):
  try:
    f=file(dirname+'/users.yaml','w')
    yaml.dump(users,stream=f)
    f.close()
    return True
  except:
    return False

def get_sina_client():
  return SinaClient(config['sina']['key'],config['sina']['secret'])

####################
# main starts here
####################
if __name__ == "__main__":
  option=len(sys.argv)>1 and sys.argv[1]
  if option=='add':
    if len(sys.argv)>4:
      succ,user=add(sys.argv[2],sys.argv[3],sys.argv[4])
      print 'add user '+(succ and 'ok' or 'failed')
      print format_user(user)
    else:
      help()
  elif option=='apply':
    url,token=apply(len(sys.argv)>2 and sys.argv[2])
    print url
    print token
  elif option=='register':
    username=len(sys.argv)>2 and sys.argv[2]
    if username:
      register(username)
    else:
      help()
  elif option=='rm':
    username=len(sys.argv)>2 and sys.argv[2]
    if username:
      succ,user=rm(username)
      print 'delete user '+(succ and 'ok' or 'failed')
      print format_user(user)
    else:
      help()
  elif option=='act':
    username=len(sys.argv)>2 and sys.argv[2]
    active=len(sys.argv)==4 and sys.argv[3]
    if username and active:
      succ,user=act(username,active=='1')
      print 'user '+(succ and '' or 'not ')+(active and 'activated' or 'deactivated')
      print format_user(user)
    else:
      help()
  elif option=='ls':
    ls()
  elif option=='upgrade':
    upgrade()
  else:
    help()
