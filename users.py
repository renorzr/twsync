import sys
import yaml
from sinaclient import SinaClient

def add(username):
  users=load_users()
  if (users.has_key(username)):
    print 'user '+username+' exists'
    return
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
  else:
    print 'user '+username+" doesn't exist"
  save_users(users)

def ls():
  users=load_users()
  print "\n".join(users.keys())

def mv(u1,u2):
  users=load_users()
  if users.has_key(u2):
    print 'user '+u2+' exists'
    return
  if not users.has_key(u1):
    print 'user '+u1+' does\'nt exist'
    return
  users[u2]=users[u1]
  del(users[u1])

def help():
  print """Usage: python users.py options args
options:
add <username>     : add a user
rm <username>      : remove user
mv <user1> <user2> : rename user1 to user2
ls                 : list all users

Note: username should be the same with twitter username.
"""

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
    yaml.dump(users,stream=f)
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
elif option=='mv':
  u1,u2=len(sys.argv)>3 and sys.argv[2:4] or (None,None)
  if u1 and u2:
    mv(u1,u2)
  else:
    help()
else:
  help()
