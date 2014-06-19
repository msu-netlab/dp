"""
This script will look up all active nodes that are part of a testbed managed
by SeattleGENI and determine which vessels on those nodes are available.
This information could be used in various ways, one of them being to gather
information about those node locations, such as latency from a certain
location, and decide which vessels to acquire based on that information.

Note: This script can result in a large amount of of node communication.
Specifically, it will try to communicate with every node that is part of
the testbed.

Example output of this script:

Number of advertising nodes: 452
DEBUG: only looking at 5 nodes.
Failure on NAT$2dfeca92a68744eb493cf5ba5559cdcee03684c5v2:1224: Connection Refused! ['[Errno 111] Connection refused']
On 1.1.1.1:1224 found 6 available vessels
On 4.4.4.4:1224 found 6 available vessels
On 3.3.3.3:1224 found 5 available vessels
Failure on 2.2.2.2:1224: timed out
Number of nodes that SeattleGENI vessels are available on: 3
"""

import sys
import traceback

# If this script resides outside of the directory that contains the seattlelib
# files and experimentlib.py, then you'll need to set that path here.
EXPERIMENTLIB_DIRECTORY = "./experimentlibrary/"
sys.path.append(EXPERIMENTLIB_DIRECTORY)

import experimentlib

# This can be used to adjust how many threads are used for concurrently
# contacting nodes when experimentlib.run_parallelized() is called.
#experimentlib.num_worker_threads = 10

# The public key that all seattlegeni nodes advertise under.
SEATTLECLEARINGHOUSE_PUBLICKEY_FILENAME = "seattlegeni_advertisement.publickey"

# Useful for development. Only contact this many nodes.
MAX_NODES_TO_LOOK_AT = 5





def main():

  identity = experimentlib.create_identity_from_key_files(SEATTLECLEARINGHOUSE_PUBLICKEY_FILENAME)

  nodelocation_list = experimentlib.lookup_node_locations_by_identity(identity)
  print("Number of advertising nodes: " + str(len(nodelocation_list)))

  if MAX_NODES_TO_LOOK_AT is not None:
    print("DEBUG: only looking at " + str(MAX_NODES_TO_LOOK_AT) + " nodes.")
    nodelocation_list = nodelocation_list[:MAX_NODES_TO_LOOK_AT]

  # Talk to each nodemanager to find out vessel information.
  browse_successlist, failurelist = \
      experimentlib.run_parallelized(nodelocation_list, browse_node_for_available_vessels)

  # Create a dictionary whose keys are the nodeids and values are lists of
  # vesseldicts of the available vessels on that node.
  available_vesseldicts_by_node = {}
  for (nodeid, available_vesseldicts) in browse_successlist:
    if available_vesseldicts:
      available_vesseldicts_by_node[nodeid] = available_vesseldicts

  print("Number of nodes that SeattleGENI vessels are available on: " + 
        str(len(available_vesseldicts_by_node.keys())))





def browse_node_for_available_vessels(nodelocation):
  """
  Contact the node at nodelocation and return a list of vesseldicts
  for each vessel on the node.
  """
  try:
    # Ask the node for information about the vessels on it.
    vesseldict_list = experimentlib.browse_node(nodelocation)
  
    # Gather up a list of vesseldicts of the available vessels.
    available_vesseldict_list = []
    for vesseldict in vesseldict_list:
      if is_vessel_available(vesseldict):
        available_vesseldict_list.append(vesseldict)
  
    # Just so we can watch the progress, print some output.
    # We display the nodelocation rather than the nodeid because it's more
    # interesting to look at, even though nodes can change location and this
    # isn't a unique identifier of the node.
    print("On " + nodelocation + " found " +
          str(len(available_vesseldict_list)) + " available vessels")
  
    return available_vesseldict_list

  except experimentlib.NodeCommunicationError, e:
    print("Failure on " + nodelocation + ": " + str(e))

  except:
    traceback.print_exc()





def is_vessel_available(vesseldict):
  """
  This returns True or False depending on whether the vesseldict indicates an
  an available vessel. That is, one that can be acquired through SeattleGENI.
  """
  if vesseldict['vesselname'] == 'v2':
    # v2 is a special vessel that will never be available from SeattleGENI.
    return False
  else:
    # If there are no userkeys, the vessel is available.
    return len(vesseldict['userkeys']) == 0





if __name__ == "__main__":
  main()
