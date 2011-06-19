import sys
import yaml
from sinaclient import SinaClient

def upgrade():
  users=load_users()
  new_users={}
  sina=SinaClient(config['sina']['key'],config['sina']['secret'])
  for username in users:
    u=users[username]
    print 'sina_token:',u['sina_token']
    sina.set_access_token(u['sina_token'])
    sinauser=sina.get_user()
    new_users[sinauser.id]={'sina_id':sinauser.id,'sina_name':sinauser.screen_name,'twitter_name':username,'sina_token':u['sina_token'],'last_tweet':u['last_tweet'],'activated':u['activated']}
  save_users(new_users)

def add(twitter_name):
  users=load_users()
  sina=SinaClient(config['sina']['key'],config['sina']['secret'])
  url=sina.get_auth_url()
  verifier=raw_input('goto '+url+' get pin code:')
  sina.set_verifier(verifier)
  token=sina.get_access_token()
  sinauser=sina.get_user()
  users[sinauser.id]={'sina_id':sinauser.id,'sina_name':sinauser.screen_name,'twitter_name':twitter_name,'sina_token':token,'last_tweet':None,'activated':True}
  if not save_users(users):
    print 'add user failed'

def rm(sina_id):
  users=load_users()
  if (users.has_key(sina_id)):
    print 'delete user '+format_user(users[sina_id])
    del(users[sina_id])
  else:
    print 'user '+sina_id+" doesn't exist"
  save_users(users)

def ls():
  users=load_users()
  print '\n'.join(map(lambda u:format_user(u),users.values()))

def mv(u1,u2):
  users=load_users()
  if users.has_key(u2):
    print 'user '+u2+' exists:'
    print format_user(users[u2])
    return
  if not users.has_key(u1):
    print 'user '+u1+' does\'nt exist'
    return
  users[u2]=users[u1]
  del(users[u1])

def act(username,active):
  users=load_users()
  if (users.has_key(username)):
    users[username]['activated']=active
  else:
    print 'user '+username+" doesn't exist"
  save_users(users)
  
def format_user(u):
  return "%s\t%s\t%s\t%s"%(u['sina_id'],u['sina_name'],u['twitter_name'],(u['activated'] and 'activated' or 'non-activated'))

def help():
  print """Usage: python users.py options args
options:
add <username>       : add a user
rm <username>        : remove user
mv <user1> <user2>   : rename user1 as user2
act <username> <1|0> : activate(1) or deactivate(0) a user
ls                   : list all users

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
elif option=='act':
  username=len(sys.argv)>2 and sys.argv[2]
  active=len(sys.argv)==4 and sys.argv[3]
  if username and active:
    act(username,active=='1')
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
elif option=='upgrade':
  upgrade()
else:
  help()
