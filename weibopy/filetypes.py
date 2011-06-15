def guess_file_type(data):
  if data[:3]=='GIF':
    return 'image/gif'
  if data[:4]=='.PNG':
    return 'image/png'
  if data[6:10]=='JFIF':
    return 'image/gif'
