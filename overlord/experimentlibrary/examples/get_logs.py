"""
This script will print the log from each of a user's active vessels.
"""

import os
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





def main():

  identity = experimentlib.create_identity_from_key_files(PUBLICKEY_FILENAME, PRIVATEKEY_FILENAME)

  nodelocation_list = experimentlib.lookup_node_locations_by_identity(identity)

  print("Number of advertising nodes: " + str(len(nodelocation_list)))

  vesselhandle_list = experimentlib.find_vessels_on_nodes(identity, nodelocation_list)

  print("Number of active vessels: " + str(len(vesselhandle_list)))

  for vesselhandle in vesselhandle_list:
    try:
      nodeid, vesselname = experimentlib.get_nodeid_and_vesselname(vesselhandle)
      nodelocation = experimentlib.get_node_location(nodeid)
      
      print("====================================================================")
      print("Log from " + nodelocation + " " + vesselname)
      logcontents = experimentlib.get_vessel_log(vesselhandle, identity)
      print(logcontents)
        
    except experimentlib.SeattleExperimentError, e:
      print("Failure on vessel " + vesselhandle + ". Error was: " + str(e))

  print("Done.")






if __name__ == "__main__":
  main()
