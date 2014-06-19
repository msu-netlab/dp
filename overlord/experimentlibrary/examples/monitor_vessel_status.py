"""
This is an example of a vessel status monitor. This script will lookup the
locations of nodes that are advertising under the provided public key, then
it will find the vessels on each node and register a monitor that watches
their status. The callback function registered for status changes will
print a message whenever a status change occurs and will also maintain a
list of currently active vessels (that is, vessels that the key has access
to and which are on reachable nodes). Occasionally a fresh lookup of
locations is done and new vessels found and added to the vessel status monitor.
This ensures that new vessels that come online or that become usable by the
key will be monitored.
"""

import sys
import time
import traceback

# If this script resides outside of the directory that contains the seattlelib
# files and experimentlib.py, then you'll need to set that path here. If you
# downloaded an installer (even if you haven't installed seattle on the machine
# this script resides on), the path will be to the seattle_repy directory from
# the extracted installer. 
#PATH_TO_SEATTLE_REPY = "/path/to/seattle_repy"
#sys.path.append(PATH_TO_SEATTLE_REPY)

import experimentlib
import vesselstatusmonitor

PUBLICKEY_FILENAME = "user.publickey"
# The private key isn't needed for just the status monitor.
#PRIVATEKEY_FILENAME = "user.privatekey"

# The number of seconds to sleep between loops of looking up advertising node
# locations and contacting the nodes to look for new vessels. This is only
# to identify new vessels that have become available as well as to rediscover
# vessels that were temporarily offline and were automatically removed from
# the vessel status monitor.
LOOKUP_SLEEP_SECONDS = 900

# This is the amount of time to wait between runs of the vessel status monitor.
# Setting this too low will not cause multiple runs of the monitor to be active
# at the same time but may cause unnecessary burden on nodes, depending on the
# number of vessels on different nodes. For example, if there's only 1 vessel
# and the sleep seconds is 0, the node that the one vessel is on will be
# continuously (and very rapidly) contacted for status updates.
MONITOR_SLEEP_SECONDS = 300

# We maintain a list of currently active/usable vessels based on calls to
# our vessel status monitor callback.
current_vessels = []





def get_node_location_or_unknown(vesselhandle):
  """
  A helper function that will return the location of the node a vessel is on or
  the string "Unknown" if the location of a vessel cannot be determined.
  """
  nodeid, vesselname = experimentlib.get_nodeid_and_vesselname(vesselhandle)
  try:
    return experimentlib.get_node_location(nodeid)
  except experimentlib.NodeLocationNotAdvertisedError, e:
    print(str(e))
    return "Unknown"





def vessel_status_callback(vesselhandle, oldstatus, newstatus):
  """
  This is the callback function will which be called by the vessel status
  monitor anytime a vessel's status changes.
  """
  try:
    if newstatus in experimentlib.VESSEL_STATUS_SET_ACTIVE:
      if vesselhandle not in current_vessels:
        current_vessels.append(vesselhandle)
    else:
      if vesselhandle in current_vessels:
        current_vessels.remove(vesselhandle)
  
    nodelocation = get_node_location_or_unknown(vesselhandle)
  
    print("vessel: ..." + str(vesselhandle)[-20:] + " @ " + nodelocation +
          " / old status: " + oldstatus + " / new status: " + newstatus)
  
    print("Currently active vessels:")
    for i in range(len(current_vessels)):
      nodelocation = get_node_location_or_unknown(current_vessels[i])
      print("    " + str(i + 1) + ") ..." + str(current_vessels[i])[-20:] + " @ " + nodelocation)
      
  except:
    traceback.print_exc()




def main():

  monitorhandle = None
 
  while True: 
    identity = experimentlib.create_identity_from_key_files(PUBLICKEY_FILENAME)

    # Get a list of nodes advertising under the public key. Some of these
    # nodes may be unreachable or may have gone offline since they advertised.
    # This won't try to communicate with the actual nodes.
    nodelocation_list = experimentlib.lookup_node_locations_by_identity(identity)
    
    # Contact each node and find out which vessels are usable by this identity/key. 
    vesselhandle_list = experimentlib.find_vessels_on_nodes(identity, nodelocation_list)
  
    print("Lookup and vessel discovery shows " + str(len(vesselhandle_list)) + " active vessels.")

    # Either register a monitor if this is the first time through the loop or
    # just add the vesselhandles to the existing monitor. Adding the vesselhandles
    # will not remove the old one and duplicates will be ignored.
    if monitorhandle is None:
      monitorhandle = vesselstatusmonitor.register_vessel_status_monitor(identity, vesselhandle_list, vessel_status_callback,
                                                                         waittime=MONITOR_SLEEP_SECONDS)
      print("Vessel status monitor registered.")
    else:
      vesselstatusmonitor.add_to_vessel_status_monitor(monitorhandle, vesselhandle_list)  

    time.sleep(LOOKUP_SLEEP_SECONDS)





if __name__ == "__main__":
  main()
