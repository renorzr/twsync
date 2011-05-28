import getpass
import yaml

def query_yn(question, default=None):
  valid={'y':True,'yes':True,'n':False,'no':False}
  while 1:
    choice=prompt(question,default).lower()
    if default is not None and choice=='':
      return default
    elif choice in valid.keys():
      return valid[choice]
    else:
      pass

def prompt(text,default=None):
    if default:
      text=text%('['+str(default)+']')
    else:
      text=text%''
    return raw_input(text) or default

  
####################
# main starts here
####################
defaults={
    'proxy': {'host': None, 'port': None, 'type': 'socks5'},
    'sina': {'username': None, 'password': None, 'appkey': None, 'use_proxy': False},
    'twitter': {'username': None, 'use_proxy': True},
}
CONFIG_FILE='config.yaml'
config=None
try:
  f=file(CONFIG_FILE,'r')
  doc=f.read()
  f.close()
  config=yaml.load(doc)
except:
  pass

config = config or defaults

sina_user=prompt('sina username%s:', config['sina']['username'])
sina_appkey=prompt('sina api appkey%s:', config['sina']['appkey'])
use_proxy_sina=query_yn('use proxy on sina? (yes/no)%s:',(config['sina']['use_proxy'] and 'yes' or 'no'))
twitter_user=prompt('twitter username%s:', config['twitter']['username'])
use_proxy_twitter=query_yn('use proxy on twitter? (yes/no)%s:',(config['twitter']['use_proxy'] and 'yes' or 'no'))
use_proxy=(use_proxy_sina or use_proxy_twitter)

if use_proxy:
  host=prompt('proxy host%s:',config['proxy']['host'])
  port=prompt('proxy port%s:',config['proxy']['port'])
  t=prompt('proxy type (http/socks4/socks5)%s:',config['proxy']['type'])
else:
  host=port=t=''

config={
    'proxy': {'host': host, 'port': port, 'type': t},
    'sina': {'username': sina_user, 'appkey': sina_appkey, 'use_proxy': use_proxy_sina},
    'twitter': {'username': twitter_user, 'use_proxy': use_proxy_twitter},
}

doc=yaml.dump(config)
f=file(CONFIG_FILE,'w')
f.write(doc)
f.close()

print ''
print 'setup completed.'
