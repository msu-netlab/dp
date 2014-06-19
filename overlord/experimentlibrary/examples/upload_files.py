"""
This script will upload a list of files to each of a user's active vessels.
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

# The list of local files to upload. These can contain directory paths.
FILES_TO_UPLOAD = ['file1.txt', 'file2.txt']






def main():

  identity = experimentlib.create_identity_from_key_files(PUBLICKEY_FILENAME, PRIVATEKEY_FILENAME)

  nodelocation_list = experimentlib.lookup_node_locations_by_identity(identity)

  print("Number of advertising nodes: " + str(len(nodelocation_list)))

  vesselhandle_list = experimentlib.find_vessels_on_nodes(identity, nodelocation_list)

  print("Number of active vessels: " + str(len(vesselhandle_list)))

  # Note that we could use experimentlib.run_parallelized() to parallelize the
  # uploading of files and speed things up, but for simplicity we do each
  # upload sequentially.

  for vesselhandle in vesselhandle_list:
    try:
      nodeid, vesselname = experimentlib.get_nodeid_and_vesselname(vesselhandle)
      nodelocation = experimentlib.get_node_location(nodeid)
      
      for local_filename in FILES_TO_UPLOAD:
        experimentlib.upload_file_to_vessel(vesselhandle, identity, local_filename)
        print("Uploaded " + local_filename + " to " + nodelocation + " vessel " + vesselname)
      
    except experimentlib.SeattleExperimentError, e:
      print("Failure on vessel " + vesselhandle + ". Error was: " + str(e))

  print("Done.")






if __name__ == "__main__":
  main()
