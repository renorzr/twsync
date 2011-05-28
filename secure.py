from Crypto.Cipher import AES
import base64
import os

BLOCK_SIZE=32
PADDING='['
PPRE='plain:'
CPRE='crypto!'

def pad(s):
  return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

def encode(c,s):
  s=PPRE+s
  return CPRE+base64.b64encode(c.encrypt(pad(s)))

def decode(c,e):
  e=e[len(CPRE):]
  d=c.decrypt(base64.b64decode(e)).rstrip(PADDING)
  if d.startswith(PPRE):
    return d[len(PPRE):]
  return None

def getcipher(pwd):
  return AES.new(pad(pwd))
