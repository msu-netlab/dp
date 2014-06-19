"""
This script will attempt to set the user keys on vessels of a specific name to
the list of keys defined in USERKEY_LIST.

Note: this example is only useful if you are the owner of vessels. If
you have obtained your vessels through SeattleGENI, then you are a user of
the vessels, not the owner. You may be the owner of vessels if you are running
your own Seattle testbed.
"""

import sys

# If this script resides outside of the directory that contains the seattlelib
# files and experimentlib.py, then you'll need to set that path here. If you
# downloaded an installer (even if you haven't installed seattle on the machine
# this script resides on), the path will be to the seattle_repy directory from
# the extracted installer. 
#PATH_TO_SEATTLE_REPY = "/path/to/seattle_repy"
#sys.path.append(PATH_TO_SEATTLE_REPY)

import experimentlib

PUBLICKEY_FILENAME = "/path/to/user.publickey"
PRIVATEKEY_FILENAME = "/path/to/user.privatekey"

VESSELNAME_TO_SET_USER_KEYS_ON = "v100"

# The user keys to set on all vessels owned by this user. This should be a list
# of keys in string format. If the list is empty, the keys will be removed
USERKEY_LIST = []





def main():

  identity = experimentlib.create_identity_from_key_files(PUBLICKEY_FILENAME, PRIVATEKEY_FILENAME)

  nodelocation_list = experimentlib.lookup_node_locations_by_identity(identity)

  print("Number of advertising nodes: " + str(len(nodelocation_list)))

  browse_successlist, browse_failurelist = experimentlib.run_parallelized(nodelocation_list,
                                                                          experimentlib.browse_node, identity)

  vesseldict_list = []
  for (nodeid, vesseldicts_of_node) in browse_successlist:
    vesseldict_list += vesseldicts_of_node

  print("Good vessels: " + str(len(vesseldict_list)))

  set_keys_successlist, set_keys_failure_list = experimentlib.run_parallelized(vesseldict_list, set_keys, identity)
  print("Vessels with proper user keys: " + str(len(set_keys_successlist)))
  print("Vessels that failed user key setting: " + str(len(set_keys_failure_list)))

  print("Done.")





def set_keys(vessel, identity):
  """
  The first argument will be a vesseldict rather than a vesselhandle because we
  passed the result of get_vessels_on_nodes to run_parallelized.
  """

  if vessel['vesselname'] != VESSELNAME_TO_SET_USER_KEYS_ON:
    msg = "[" + vessel['nodelocation'] + "] Skipping: vesselname is not: " + VESSELNAME_TO_SET_USER_KEYS_ON
    print(msg)
    raise Exception(msg)

  # convert the list of keys to a list of strings for comparison purposes...
  existingkeystringlist  = []
  for thiskey in vessel['userkeys']:
    existingkeystringlist.append(rsa_publickey_to_string(thiskey))

  if existingkeystringlist != USERKEY_LIST:
    print("[" + vessel['nodelocation'] + "] Setting user keys.")
    try:
      experimentlib.set_vessel_users(vessel['vesselhandle'], identity, USERKEY_LIST)
    except Exception, e:
      msg = "[" + vessel['nodelocation'] + "] Failure: " + str(e)
      print(msg)
      import traceback
      traceback.print_exc()
      raise Exception(msg)
    else:
      print("[" + vessel['nodelocation'] + "] Success.")
  else:
    print("[" + vessel['nodelocation'] + "] Already had correct user keys.")





if __name__ == "__main__":
  main()
