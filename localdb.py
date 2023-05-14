import json
import os


class LocalReplitDB:

  def __init__(self, filename='db.json'):
    self.filename = filename
    if not os.path.isfile(self.filename):
      with open(self.filename, 'w') as f:
        json.dump({}, f)
    with open(self.filename, 'r') as f:
      self.db = json.load(f)

  def __getitem__(self, key):
    return self.db.get(key)

  def __setitem__(self, key, value):
    self.db[key] = value
    with open(self.filename, 'w') as f:
      json.dump(self.db, f)

  def __delitem__(self, key):
    if key in self.db:
      del self.db[key]
      with open(self.filename, 'w') as f:
        json.dump(self.db, f)

  def keys(self):
    return list(self.db.keys())

  def prefix(self, prefix):
    return [key for key in self.db if key.startswith(prefix)]


# usage example

# from localdb import LocalReplitDB

# db = LocalReplitDB()

# # Set a key to a value
# db['key'] = 'value'

# # Get a key's value
# print(db['key'])

# # Delete a key
# del db['key']

# # List all keys
# print(db.keys())

# # List keys with a prefix
# print(db.prefix('prefix'))
