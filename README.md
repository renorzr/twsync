INTRODUCTION
============

1. sync sina-weibo with twitter
1. multi-user supported
1. parse pic link in twitter and upload the pic to sina-weibo (instagram, picplz, flickr and foursquare supported)
1. update with geo coordinates as well

PREREQUISITE
============

1. register as sina weibo developer and get your app key
1. Python 2.6 or above installed
1. required python libs: PyYAML, pycurl

USAGE
=====

1. extract all files
1. copy config.yaml.example as config.yaml
1. edit config.yaml setup app key/secret, proxy, etc.
1. To add sync accounts, run command: python users.py add <twitter-username>
1. Start sync daemon, run command: python twsync.py -d
1. your weibo is now synced with twitter
1. run python users.py to manage users in the future.
