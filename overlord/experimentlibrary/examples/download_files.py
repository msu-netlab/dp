"""
This script will download all of the files on each of a user's active vessels
and save them to separate directories whose names are of the format:
  host_port_vesselname
where host will likely be either an IP address or NAT identifier used by
NAT forwarders.
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

# The directory which each vessels directory will be created in.
DOWNLOAD_DIRECTORY = '.'





def main():

  identity = experimentlib.create_identity_from_key_files(PUBLICKEY_FILENAME, PRIVATEKEY_FILENAME)

  nodelocation_list = experimentlib.lookup_node_locations_by_identity(identity)

  print("Number of advertising nodes: " + str(len(nodelocation_list)))

  vesselhandle_list = experimentlib.find_vessels_on_nodes(identity, nodelocation_list)

  print("Number of active vessels: " + str(len(vesselhandle_list)))

  for vesselhandle in vesselhandle_list:
    try:
      # Generate the vessel directory name with format: host_port_vesselname
      nodeid, vesselname = experimentlib.get_nodeid_and_vesselname(vesselhandle)
      nodelocation = experimentlib.get_node_location(nodeid)
      host, port = experimentlib.get_host_and_port(nodelocation)
      dirname = host + "_" + str(port) + "_" + vesselname
      
      # Create the vessel directory if it doesn't already exist.
      vessel_directory = os.path.join(DOWNLOAD_DIRECTORY, dirname)
      if not os.path.exists(vessel_directory):
        os.mkdir(vessel_directory)
        
      # Get a list of files on the vessel.
      filelist = experimentlib.get_vessel_file_list(vesselhandle, identity)
      
      print("Files on " + nodelocation + " " + vesselname + ": " + str(filelist))
      
      for remote_filename in filelist:
        local_filename = os.path.join(vessel_directory, remote_filename)
        experimentlib.download_file_from_vessel(vesselhandle, identity, remote_filename, local_filename)
        print("Downloaded " + local_filename)
        
    except experimentlib.SeattleExperimentError, e:
      print("Failure on vessel " + vesselhandle + ". Error was: " + str(e))

  print("Done.")






if __name__ == "__main__":
  main()
