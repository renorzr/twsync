import sys
import yaml
from sinaclient import SinaClient

def add(username):
  users=load_users()
  sina=SinaClient(config['sina']['key'],config['sina']['secret'])
  url=sina.get_auth_url()
  verifier=raw_input('goto '+url+' get pin code:')
  sina.set_verifier(verifier)
  token=sina.get_access_token()
  users[username]={'sina_token':token,'last_tweet':None}
  if not save_users(users):
    print 'add user failed'

def rm(username):
  users=load_users()
  if (users.has_key(username)):
    del(users[username])
  save_users(users)

def ls():
  users=load_users()
  print "\n".join(users.keys())

def help():
  print 'usage: python users {add|rm|ls} arg'
  print 'options:'
  print 'add username  : add a user'
  print 'rm username   : remove user'
  print 'ls            : list all users'

def load_users():
  users={}
  try:
    f=file('users.yaml','r')
    users=yaml.load(f.read())
    f.close()
  except:
    users={}
  return users

def save_users(users):
  try:
    f=file('users.yaml','w')
    f.write(yaml.dump(users))
    f.close()
    return True
  except:
    return False

####################
# main starts here
####################
f=file('config.yaml','r')
config=yaml.load(f.read())
f.close()
option=len(sys.argv)>1 and sys.argv[1]
if option=='add':
  username=len(sys.argv)>2 and sys.argv[2]
  if username:
    add(username)
  else:
    help()
elif option=='rm':
  username=len(sys.argv)>2 and sys.argv[2]
  if username:
    rm(username)
  else:
    help()
elif option=='ls':
  ls()
else:
  help()
