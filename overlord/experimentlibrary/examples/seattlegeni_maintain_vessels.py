"""
This example looks for any vessels that are acquired through SeattleGENI
which are unusable/offline/unreachable. It then releases those vessels
and acquires new ones.

This script assumes that all nodelocations advertised under a user's key
(that is, the user's identity) are for nodes that were obtained through
SeattleGENI. This will be the case if you are not running your own,
private Seattle testbed.
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

# Whether to allow insecure ssl when communicating with seattlegeni.
# True, False, or None (None indicates to use the default)
experimentlib.SEATTLECLEARINGHOUSE_ALLOW_SSL_INSECURE = None

# If using secure ssl communication with seattlegeni, then this is the path
# to the CA certs file. See the file seattleclearinghouse_xmlrpc.py for details.
# This should be a path to the pem file or None (None indicates to use the default)
experimentlib.SEATTLECLEARINGHOUSE_CA_CERTS_FILES = None

# The seattlegeni username will be derived from the filename.
PUBLICKEY_FILENAME = "/path/to/your.publickey"
PRIVATEKEY_FILENAME = "/path/to/your.privatekey"

# Any number of usable vessels less than this number will result in trying to
# acquire a total of this number of vessels up to the maximum number of vessels
# that SeattleGENI will allow the account to acquire. (To increase the maximum
# number of vessels SeattleGENI will let your account have, you need to donate
# more resources.)
MIN_VESSELS_TO_KEEP = 4





def main():
  
  identity = experimentlib.create_identity_from_key_files(PUBLICKEY_FILENAME, PRIVATEKEY_FILENAME)

  # Get a list of nodes advertising under the public key. Some of these
  # nodes may be unreachable or may have gone offline since they advertised.
  # This won't try to communicate with the actual nodes.
  nodelocation_list = experimentlib.lookup_node_locations_by_identity(identity)
  
  print("nodelocation_list:" + str(nodelocation_list))
  
  # Talk to each advertising node to find out which vessels we have on each.
  # We get back a list of dictionaries, where each dictionary describes a
  # vessel. There may be multiple vessels from any single node in this list.
  active_vesselhandle_list = experimentlib.find_vessels_on_nodes(identity, nodelocation_list)
  
  print("active_vesselhandle_list:" + str(active_vesselhandle_list))

  # Now we want to find out which vessels we've acquired through seattlegeni
  # that are not in our list. We may, for example, want to release those
  # vessels because we consider them unusable.
  
  try:
    expected_vesselhandle_list = experimentlib.seattlegeni_get_acquired_vessels(identity)
   
    print("expected_vesselhandle_list:" + str(expected_vesselhandle_list))
   
    # If we already have enough usable vessels, we're done.
    if len(active_vesselhandle_list) >= MIN_VESSELS_TO_KEEP:
      print("There are already " + str(len(active_vesselhandle_list)) + " active vessels " + 
            "and our MIN_VESSELS_TO_KEEP is " + str(MIN_VESSELS_TO_KEEP))
      return
 
    # We assume all of our vessels come from seattlegeni, so if any vessels we
    # should have access to according to seattlegeni aren't accessible or
    # otherwise usable, then release them.
    vesselhandles_to_release = []
    for vesselhandle in expected_vesselhandle_list:
      if vesselhandle not in active_vesselhandle_list:
        vesselhandles_to_release.append(vesselhandle)
  
    if vesselhandles_to_release:
      print(str(len(vesselhandles_to_release)) + " vessels were inaccessible, so will try to release them:" +
            str(vesselhandles_to_release))
      try:
        experimentlib.seattlegeni_release_vessels(identity, vesselhandles_to_release)
      except experimentlib.SeattleClearinghouseError, e:
        print("Failed to release vessels: " + str(e))
      else:
        print("Vessels successfully released.")

    # Determine the maximum number of vessels we can acquire through seattlegeni.
    max_vessels_allowed = experimentlib.seattlegeni_max_vessels_allowed(identity)
    print("max_vessels_allowed: " + str(max_vessels_allowed)) 
    
    # Determine the number of vessels we already have acquired through seattlegeni.
    num_currently_acquired = len(experimentlib.seattlegeni_get_acquired_vessels(identity))
    print("currently_acquired_count: " + str(num_currently_acquired))    

    # Let's try to get as close to MIN_VESSELS_TO_KEEP without requesting more
    # than is allowed by this account.
    num_vessels_to_request = min(max_vessels_allowed, MIN_VESSELS_TO_KEEP) - num_currently_acquired

    if num_vessels_to_request <= 0:
      print("This account doesn't have enough vessel credits to request more vessels.")
      return
    else:
      print("Will try to acquire " + str(num_vessels_to_request) + " vessels.")

    vessel_type = experimentlib.SEATTLECLEARINGHOUSE_VESSEL_TYPE_WAN
    acquired_vessels = experimentlib.seattlegeni_acquire_vessels(identity, vessel_type, num_vessels_to_request)
    
    print("Acquired " + str(num_vessels_to_request) + " vessels: " + str(acquired_vessels))

  except experimentlib.SeattleClearinghouseError, e:
    # This isn't very useful error handling, but is here to demonstrate catching
    # errors raised by the seattlegeni_* functions of the experimentlib.
    print("An error occurred with a request to SeattleGENI: " + str(e))
    raise

  
  
if __name__ == "__main__":
  main()
