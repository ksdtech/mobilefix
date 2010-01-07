#!/usr/bin/env python
"""
This software is free for your use.
Copyright 2009 Kentfield School District.
Original author: Peter Zingg, pzingg@kentfieldschools.org
"""

import os, re, time

def parse_user_record(dirid):
  """Split up the key: value pairs printed by nicl . -read."""
  r_attr = re.compile(r"([A-Za-z_]+):\s*(.+)")
  attrs = dict()
  current_key = None
  value = None
  fout = os.popen('/usr/bin/nicl . -read %s' % dirid, 'r')
  for line in fout.readlines():
    line = line.rstrip()
    m = r_attr.match(line)
    if m:
      current_key = m.group(1)
      val = m.group(2)
      attrs[current_key] = val
    else:
      if current_key is not None:
        attrs[current_key] += "\n"
        attrs[current_key] += line
  fout.close()
  return attrs
  
def sort_tuple_1_desc(x, y):
  """Sort a list of tuples by the second member (descending)."""
  if x[1] < y[1]:
    return 1
  elif x[1] == y[1]:
    return 0
  return -1

def get_userdirs_to_remove(shortname, dirids):
  """Given a list of NetInfo directory nodes, analyze and 
  return the node ids that should be deleted, if any.
  """
  r_local = re.compile(r"LocalCachedUser;")
  dirs_to_remove = [ ]
  dirs_to_save   = [ ]
  is_mobile_account = False
  for dirid in dirids:
    attrs = parse_user_record(dirid)
    authority = attrs.get("authentication_authority")
    if authority is not None and r_local.search(authority):
      is_mobile_account = True
    home_dir = attrs.get("home")
    if home_dir is not None:
      timestamp = attrs.get("copy_timestamp");
      if timestamp is None:
        timestamp = "2000-01-01T12:00:00Z"
      dirs_to_save.append((dirid, timestamp))
    else:
      dirs_to_remove.append(dirid)

  if not is_mobile_account:
    print "cannot resolve %s, no mobile account found" % shortname
  else:
    number_to_save = len(dirs_to_save)
    if number_to_save > 1:
      dirs_to_save.sort(sort_tuple_1_desc)
      print "resolving %s (%d records) according to copy_timestamp" % (shortname, number_to_save)
      i = 0
      for dirid, timestamp in dirs_to_save:
        i += 1
        print "[%d] %s copy_timestamp %s" % (i, dirid, timestamp)
        if i > 1:
          dirs_to_remove.append(dirid)
          number_to_save -= 1
    if number_to_save == 1:
      number_to_remove = len(dirs_to_remove)
      if number_to_remove == 0:
        print "cannot resolve %s, no users to remove" % (shortname)
  return dirs_to_remove

def resolve_multiple_mobile_users(users):
  """Given a dict of usernames and their NetInfo directory node ids,
  clean up any with multiple nodes, if possible.
  """
  dirs_removed = 0
  for shortname in users.keys():
    if len(users[shortname]) > 1:
      print "multiple netinfo user records for %s!" % shortname
      dirs_to_remove = get_userdirs_to_remove(shortname, users[shortname])
      print "removing %s" % dirs_to_remove
      for dirid in dirs_to_remove:
        fout = os.popen('/usr/bin/nicl . -delete %s' % dirid, 'r')
        result = fout.read()
        exitcode = fout.close()
        print "removed %s, exit code = %d, result = %s" % (dirid, exitcode, result)
        if exitcode == 0:
          dirs_removed += 1
  return dirs_removed
  
def find_netinfo_users():
  """Return a dict with usernames as keys and list of NetInfo directory
  nodes as values.
  """
  users = dict()

  fout = os.popen('/usr/bin/nicl . -list /users', 'r')
  for line in fout.readlines():
    line = line.rstrip()
    list3 = line.split(None, 2)
    if len(list3) > 1:
      dirid = list3[0]
      shortname = list3[1]
      if not shortname in users:
        users[shortname] = list()
      users[shortname].append(dirid)
  fout.close()
  return users
  
# start of script
if __name__ == "__main__":
  print "acctcheck.py running at %s" % time.asctime(time.localtime())
  if not os.access('/usr/bin/nicl', os.X_OK):
    print "no nicl on this machine. leopard?"
  else:
    users = find_netinfo_users()
    resolve_multiple_mobile_users(users)
