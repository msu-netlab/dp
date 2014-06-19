"""
<Program Name>
  experimentlib.py

<Authors>
  Justin Samuel

<Date Started>
  December 1, 2009 

<Purpose>
  A library for conducting experiments using Seattle vessels. The functions in
  this library allow for communicating with vessels (e.g. to upload files and
  run programs) as well as for communicating with SeattleGENI (e.g. to obtain
  vessels to run experiments on).
  
<Usage>
  Ensure that this file is in a directory containing the seattlelib files as
  well as the seattleclearinghouse_xmlrpc.py module. In your own script, add:
  
    import experimentlib
    
  then call the methods desired.
  
  Note that if your script resides outside of the directory that contains the
  seattlelib files,  experimentlib.py, and seattlegeni_client.py, then you'll
  need to set that directory/those directories in your python path. For example,
  if you downloaded an installer (even if you haven't installed Seattle on the
  machine this script resides on, the path will be to the seattle_repy directory
  that was among the extracted installer files. To set the path directly in your
  script rather than through environment variables, you can use something like:

    import sys
    sys.path.append("/path/to/seattle_repy") 
    
  You would need to do the above *before* your line that says:

    import experimentlib

  For examples of using this experimentlib, see the examples/ directory.

  Please also see the following wiki page for usage information and how to
  obtain the latest version of this experiment library:
  
    https://seattle.cs.washington.edu/wiki/ExperimentLibrary

<Notes>

  Object Definitions:
      
    * identity: a dictionary that minimally contains a public key but may also
      contain the related private key and the username of a corresponding
      SeattleGENI account. When one wants to perform any operation that would
      require a public key, private key, or username, an identity must be
      provided. An identity can be created using the functions named
      create_identity_from_*.
  
    * vesselhandle: a vesselhandle is a string that contains the information
      required to uniquely identify a vessel, regardless of the current
      location (IP address) of the node the vessel is on. This is in the format
      of "nodeid:vesselname".

    * nodeid: a string that contains the information required to uniquely
      identify a node, regardless of its current location.
      
    * vesselname: a string containing the name of a vessel. This name will
      be unique on any given node, but the same name is likely is used for
      vessels on other nodes. Thus, this does not uniquely identify a vessel,
      in general. To uniquely identify a vessel, a vesselhandle is needed.

    * nodelocation: a string containing the location of a node. This will not
      always be "ip:port". It could, for example, be "NATid:port" in the case
      of a node that is accessible through a NAT forwarder.
      
    * vesseldict: a dictionary of details related to a given vessel. The keys
      that will always be present are 'vesselhandle', 'nodelocation',
      'vesselname', and 'nodeid'. Additional keys will be present depending on
      the function that returns the vesseldict. See the individual function
      docstring for details.
  
  Exceptions:
  
    All exceptions raised by functions in this module will either be or extend:
      * SeattleExperimentError
      * SeattleClearinghouseError
      
    The SeattleClearinghouseError* exceptions will only be raised by the functions whose
    names are seattlegeni_*. Any of the seattlegeni_* functions may raise the
    following in addition to specific exceptions described in the function
    docstrings (these are all subclasses of SeattleClearinghouseError):
      * SeattleClearinghouseCommunicationError
      * SeattleClearinghouseAuthenticationError
      * SeattleClearinghouseInvalidRequestError
      * SeattleClearinghouseInternalError
      
    In the case of invalid arguments to functions, the following may be
    raised (these will not always be documented for each function):
      * TypeError
      * ValueError
      * IOError (if the function involves reading/writing files and the
                 filename provided is missing/unreadable/unwritable)
      
    For the specific exceptions raised by a given function, see the function's
    docstring.
"""

import os
import random
import time
import traceback
import xmlrpclib

import seattleclearinghouse_xmlrpc

# We use a helper module to do repy module imports so that we don't import
# unexpected items into this module's namespace. This helps reduce errors
# because editors/pylint make it clear when an unknown identifier is used
# and it also makes other things easier for developers, such as using ipython's
# tab completion and not causing unexpected imports if someone using this
# module decides to use "from experimentlib import *"
import repyimporter

import fastnmclient
repytime = repyimporter.import_repy_module("time")
rsa = repyimporter.import_repy_module("rsa")
parallelize = repyimporter.import_repy_module("parallelize")
advertise = repyimporter.import_repy_module("advertise")

# The maximum number of node locations to return from a call to lookup_node_locations.
max_lookup_results = 1024 * 1024

# The timeout to use for communication, both in advertisement lookups and for
# contacting nodes directly.
defaulttimeout = 10

# The number of worker threads to use for each parallelized operation.
num_worker_threads = 5

# Whether additional information and debugging messages should be printed
# to stderr by this library.
print_debug_messages = True

# OpenDHT can be slow/hang, which isn't fun if the experimentlib is being used
# interactively. So, let's default to central advertise server lookups here
# until we're sure all issues with OpenDHT are resolved.
# A value of None indicates the default of ['opendht', 'central'].
#advertise_lookup_types = None
advertise_lookup_types = ['central']

# A few options to be passed along to the SeattleGENI xmlrpc client.
# None means the default.
SEATTLECLEARINGHOUSE_XMLRPC_URL = None
SEATTLECLEARINGHOUSE_ALLOW_SSL_INSECURE = None # Set to True to allow insecure SSL.
SEATTLECLEARINGHOUSE_CA_CERTS_FILES = None

# These constants can be used as the type argument to seattlegeni_acquire_vessels.
SEATTLECLEARINGHOUSE_VESSEL_TYPE_WAN = "wan"
SEATTLECLEARINGHOUSE_VESSEL_TYPE_LAN = "lan"
SEATTLECLEARINGHOUSE_VESSEL_TYPE_NAT = "nat"
SEATTLECLEARINGHOUSE_VESSEL_TYPE_RAND = "rand"

# Some of these vessel status explanations are from:
# https://seattle.cs.washington.edu/wiki/NodeManagerDesign

# Fresh: has never been started.
VESSEL_STATUS_FRESH = "Fresh"

# Started: has been started and is running when last checked.
VESSEL_STATUS_STARTED = "Started"

# Stopped: was running but stopped by NM command
VESSEL_STATUS_STOPPED = "Stopped"

# Stale: it last reported a start of "Started" but significant time has
# elapsed, likely due to a system crash (what does "system crash" mean?).
VESSEL_STATUS_STALE = "Stale"

# Terminated (the vessel stopped of its own volition, possibly due to an error)
VESSEL_STATUS_TERMINATED = "Terminated"

# The node is not advertising
VESSEL_STATUS_NO_SUCH_NODE = "NO_SUCH_NODE"

# The node can be communicated with but the specified vessel doesn't exist
# on the node. This will also be used when the vessel exists on the node but
# the identity being used is not a user or the owner of the vessel.
VESSEL_STATUS_NO_SUCH_VESSEL = "NO_SUCH_VESSEL"

# The node can't be communicated with or communication fails.
VESSEL_STATUS_NODE_UNREACHABLE = "NODE_UNREACHABLE"

# For convenience we define two sets of vessel status constants that include
# all possible statuses grouped by whether the status indicates the vessel is
# usable/active or whether it is unusable/inactive.
VESSEL_STATUS_SET_ACTIVE = set([VESSEL_STATUS_FRESH, VESSEL_STATUS_STARTED,
                                VESSEL_STATUS_STOPPED, VESSEL_STATUS_STALE,
                                VESSEL_STATUS_TERMINATED])
VESSEL_STATUS_SET_INACTIVE = set([VESSEL_STATUS_NO_SUCH_NODE, VESSEL_STATUS_NO_SUCH_VESSEL,
                                  VESSEL_STATUS_NODE_UNREACHABLE])

# Whether _initialize_time() has been called.
_initialize_time_called = False

# Keys are node locations (a string of "host:port"), values are nmhandles.
# Note that this method of caching nmhandles will cause problems if multiple
# identities/keys are being used to contact the name node.
_nmhandle_cache = {}

# Keys are nodeids, values are nodelocations.
_node_location_cache = {}





class SeattleExperimentError(Exception):
  """Base class for other exceptions."""



class UnexpectedVesselStatusError(SeattleExperimentError):
  """
  When a vessel status is reported by a node and that status is something
  we don't understand. Mostly this is something we care about because we
  want to definitely tell users what to expect in their code in terms of
  status, so we should be very clear about the possibly values and never
  have to raise this exception.
  """



class NodeCommunicationError(SeattleExperimentError):
  """Unable to perform a requested action on/communication with a node/vessel."""



class NodeLocationLookupError(SeattleExperimentError):
  """
  Unable to determine the location of a node based on its nodeid or unable
  to successfully perform an advertisement lookup.
  """
  
  

class NodeLocationNotAdvertisedError(NodeLocationLookupError):
  """
  A lookup was successful but no node locations are being advertised under a
  nodeid.
  """
  
  

class UnableToPerformLookupError(NodeLocationLookupError):
  """
  Something is wrong with performing lookups. Either none of the lookup
  services that were tried were successful or there's a bug in some underlying
  code being used by this module.
  """


  
class IdentityInformationMissingError(SeattleExperimentError):
  """
  The information that is part of an identity object is incomplete. For
  example, if only the public key is in the identity but the identity is
  used in a way that requires a private key, this exception would be
  raised.
  """


#This is the base class for all SeattleGENI errors. We make this available
#in the namespace of the experimentlib so that clients do not have to import
#seattleclearinghouse_xmlrpc to catch these.
SeattleClearinghouseError = seattleclearinghouse_xmlrpc.SeattleClearinghouseError

# We make these available, as well, in case users find them useful. We prefix
# all of these error names with SeattleGENI.
SeattleClearinghouseCommunicationError = seattleclearinghouse_xmlrpc.CommunicationError
SeattleClearinghouseInternalError = seattleclearinghouse_xmlrpc.InternalError
SeattleClearinghouseAuthenticationError = seattleclearinghouse_xmlrpc.AuthenticationError
SeattleClearinghouseInvalidRequestError = seattleclearinghouse_xmlrpc.InvalidRequestError
SeattleClearinghouseNotEnoughCreditsError = seattleclearinghouse_xmlrpc.NotEnoughCreditsError
SeattleClearinghouseUnableToAcquireResourcesError = seattleclearinghouse_xmlrpc.UnableToAcquireResourcesError





def _validate_vesselhandle(vesselhandle):
  if not isinstance(vesselhandle, basestring):
    raise TypeError("vesselhandle must be a string, not a " + str(type(vesselhandle)))
  
  parts = vesselhandle.split(':')
  if len(parts) != 2:
    raise ValueError("invalid vesselhandle '" + vesselhandle + "', should be nodeid:vesselname")





def _validate_vesselhandle_list(vesselhandle_list):
  if not isinstance(vesselhandle_list, list):
    raise TypeError("vesselhandle list must be a list, not a " + str(type(vesselhandle_list)))

  for vesselhandle in vesselhandle_list:
    _validate_vesselhandle(vesselhandle)





def _validate_nodelocation(nodelocation):
  if not isinstance(nodelocation, basestring):
    raise TypeError("nodelocation must be a string, not a " + str(type(nodelocation)))
  
  parts = nodelocation.split(':')
  if len(parts) != 2:
    raise ValueError("nodelocation '" + nodelocation + "' invalid, should be host:port")





def _validate_nodelocation_list(nodelocation_list):
  if not isinstance(nodelocation_list, list):
    raise TypeError("nodelocation list must be a list, not a " + str(type(nodelocation_list)))

  for nodelocation in nodelocation_list:
    _validate_nodelocation(nodelocation)





def _validate_identity(identity, require_private_key=False, require_username=False):
  if not isinstance(identity, dict):
    raise TypeError("identity must be a dict, not a " + str(type(identity)))

  if 'publickey_str' not in identity:
    raise TypeError("identity dict doesn't have a 'publickey_str' key, so it's not an identity.")

  if require_private_key:
    if 'privatekey_str' not in identity:
      raise IdentityInformationMissingError("identity must have a private key for the requested operation.")

  if require_username:
    if 'username' not in identity:
      raise IdentityInformationMissingError("identity must have a username for the requested operation.")





def _initialize_time():
  """
  Does its best to call time_updatetime() and raises a SeattleExperimentError
  if it doesn't succeed after many tries.
  """
  global _initialize_time_called
  
  if not _initialize_time_called:
    
    max_attempts = 10
    possible_ports = range(10000, 60001)
    
    # Ports to use for UDP listening when doing a time update.
    portlist = random.sample(possible_ports, max_attempts) 
    
    for localport in portlist:
      try:
        repytime.time_updatetime(localport)
        _initialize_time_called = True
        return
      except repytime.TimeError:
        error_message = traceback.format_exc()
    
    raise SeattleExperimentError("Failed to perform time_updatetime(): " + error_message)





def _create_list_from_key_in_dictlist(dictlist, key):
  """
  List comprehensions are verboten by our coding style guide (generally for
  good reason). Otherwise, we wouldn't have this function and would just write
  the following wherever needed:
    [x[key] for x in dictlist]
  """
  new_list = []
  for dictitem in dictlist:
    new_list.append(dictitem[key])
  return new_list





def _get_nmhandle(nodelocation, identity=None):
  """
  Get an nmhandle for the nodelocation and identity, if provided. This will look
  use a cache of nmhandles and only create a new one if the requested nmhandle
  has not previously been requested.
  """
  
  # Call _initialize_time() here because time must be updated at least once before
  # nmhandles are used.
  _initialize_time()
  
  host, port = nodelocation.split(':')
  port = int(port)
  
  if identity is None:
    identitystring = "None"
  else:
    identitystring = identity['publickey_str']
    
  if identitystring not in _nmhandle_cache:
    _nmhandle_cache[identitystring] = {}

  if nodelocation not in _nmhandle_cache[identitystring]:
    try:
      if identity is None:
        nmhandle = fastnmclient.nmclient_createhandle(host, port, timeout=defaulttimeout)
      elif 'privatekey_dict' in identity:
        nmhandle = fastnmclient.nmclient_createhandle(host, port, privatekey=identity['privatekey_dict'],
                                           publickey=identity['publickey_dict'], timeout=defaulttimeout)
      else:
        nmhandle = fastnmclient.nmclient_createhandle(host, port, publickey=identity['publickey_dict'],
                                                  timeout=defaulttimeout)
    except fastnmclient.NMClientException, e:
      raise NodeCommunicationError(str(e))
    
    _nmhandle_cache[identitystring][nodelocation] = nmhandle
    
  return _nmhandle_cache[identitystring][nodelocation]





def run_parallelized(targetlist, func, *args):
  """
  <Purpose>
    Parallelize the calling of a given function using multiple threads.
  <Arguments>
    targetlist
      a list what will be the first argument to func each time it is called.
    func
      the function to be called once for each item in targetlist.
    *args
      (optional) every additional argument will be passed to func after an
      item from targetlist. That is, these will be the second, third, etc.
      argument to func, if provided. These are not required a.
  <Exceptions>
    SeattleExperimentError
      Raised if there is a problem performing parallel processing. This will
      not be raised just because func raises exceptions. If func raises
      exceptions when it is called, that exception information will be
      available through the run_parallelized's return value.
  <Side Effects>
    Up to num_worker_threads (a global variable) threads will be spawned to
    call func once for every item in targetlist.
  <Returns>
    A tuple of:
      (successlist, failurelist)
    where successlist is a list of tuples of the format:
      (target, return_value_from_func)
    and failurelist is a list of tuples of the format:
      (target, exception_string)
    Note that exception_string will not contain a full traceback, but rather
    only the string representation of the exception.
  """
  
  try:
    phandle = parallelize.parallelize_initfunction(targetlist, func, num_worker_threads, *args)
  
    while not parallelize.parallelize_isfunctionfinished(phandle):
      # TODO: Give up after a timeout? This seems risky as run_parallelized may
      # be used with functions that take a long time to complete and very large
      # lists of targets. It would be a shame to break a user's program because
      # of an assumption here. Maybe it should be an optional argument to 
      # run_parallelized.
      time.sleep(.1)
    
    results = parallelize.parallelize_getresults(phandle)
  except parallelize.ParallelizeError:
    raise SeattleExperimentError("Error occurred in run_parallelized: " + 
                                 traceback.format_exc())
  finally:
    parallelize.parallelize_closefunction(phandle)

  # These are lists of tuples. The first is a list of (target, retval), the
  # second is a list of (target, errormsg)
  return results['returned'], results['exception']

    
  



def create_identity_from_key_files(publickey_fn, privatekey_fn=None):
  """
  <Purpose>
    Create an identity from key files.
  <Arguments>
    publickey_fn
      The full path, including filename, to the public key this identity
      should represent. Note that the identity's username will be assumed
      to be the part of the base filename before the first period (or the
      entire base filename if there is no period). So, to indicate a username
      of "joe", the filename should be, for example, "joe.publickey".
    privatekey_fn
      (optional) The full path, including filename, to the private key that
      corresponds to publickey_fn. If this is not provided, then the identity
      will not be able to be used for operations the require a private key.
  <Exceptions>
    IOError
      if the files do not exist or are not readable.
    ValueError
      if the files do not contain valid keys.
  <Returns>
    An identity object to be used with other functions in this module.
  """
  identity = {}
  identity["username"] = os.path.basename(publickey_fn).split(".")[0]
  identity["publickey_fn"] = publickey_fn
  try:
    identity["publickey_dict"] = rsa.rsa_file_to_publickey(publickey_fn)
    identity["publickey_str"] = rsa.rsa_publickey_to_string(identity["publickey_dict"])
    
    if privatekey_fn is not None:
      identity["privatekey_fn"] = privatekey_fn
      identity["privatekey_dict"] = rsa.rsa_file_to_privatekey(privatekey_fn)
      identity["privatekey_str"] = rsa.rsa_privatekey_to_string(identity["privatekey_dict"])
  except IOError:
    raise
  except ValueError:
    raise

  return identity





def create_identity_from_key_strings(publickey_string, privatekey_string=None, username=None):
  """
  <Purpose>
    Create an identity from key strings.
  <Arguments>
    publickey_string
      The string containing the public key this identity should represent. The
      string must consists of the modulus, followed by a space, followed by
      the public exponent. This will be the same as the contents of a public
      key file.
    privatekey_string
      (optional) The full path, including filename, to the private key that
      corresponds to publickey_fn. If this is not provided, then the identity
      will not be able to be used for operations the require a private key.
    username
      (optional) A string containing the username to associate with this
      identity. This is only necessary if using this identity with the
      seattlegeni_* functions.
  <Exceptions>
    ValueError
      if the strings do not contain valid keys.
  <Returns>
    An identity object to be used with other functions in this module.
  """
  identity = {}
  identity["username"] = username
  try:
    identity["publickey_dict"] = rsa.rsa_string_to_publickey(publickey_string)
    identity["publickey_str"] = rsa.rsa_publickey_to_string(identity["publickey_dict"])
    
    if privatekey_string is not None:
      identity["privatekey_dict"] = rsa.rsa_string_to_privatekey(privatekey_string)
      identity["privatekey_str"] = rsa.rsa_privatekey_to_string(identity["privatekey_dict"])
  except IOError:
    # Raised if there is a problem reading the file.
    raise
  except ValueError:
    # Raised by the repy rsa module when the key is invald.
    raise

  return identity





def _lookup_node_locations(keystring, lookuptype=None):
  """Does the actual work of an advertise lookup."""
  
  keydict = rsa.rsa_string_to_publickey(keystring)
  try:
    if lookuptype is not None:
      nodelist = advertise.advertise_lookup(keydict, maxvals=max_lookup_results, timeout=defaulttimeout, lookuptype=lookuptype)
    else:
      nodelist = advertise.advertise_lookup(keydict, maxvals=max_lookup_results, timeout=defaulttimeout)
  except advertise.AdvertiseError, e:
    raise UnableToPerformLookupError("Failure when trying to perform advertise lookup: " + 
                                     traceback.format_exc())

  # If there are no vessels for a user, the lookup may return ''.
  for nodename in nodelist[:]:
    if nodename == '':
      nodelist.remove(nodename)

  return nodelist





def lookup_node_locations_by_identity(identity):
  """
  <Purpose>
    Lookup the locations of nodes that are advertising their location under a
    specific identity's public key.
  <Arguments>
    identity
      The identity whose public key should be used to lookup nodelocations.
  <Exceptions>
    UnableToPerformLookupError
      If a failure occurs when trying lookup advertised node locations.
  <Returns>
    A list of nodelocations.
  """
  _validate_identity(identity)
  keystring = str(identity['publickey_str'])
  return _lookup_node_locations(keystring, lookuptype=advertise_lookup_types)





def lookup_node_locations_by_nodeid(nodeid):
  """
  <Purpose>
    Lookup the locations that a specific node has advertised under. There may
    be multiple locations advertised if the node has recently changed location.
  <Arguments>
    nodeid
      The nodeid of the node whose advertised locations are to be looked up.
  <Exceptions>
    UnableToPerformLookupError
      If a failure occurs when trying lookup advertised node locations.
  <Returns>
    A list of nodelocations.
  """
  return _lookup_node_locations(nodeid, lookuptype=advertise_lookup_types)





def find_vessels_on_nodes(identity, nodelocation_list):
  """
  <Purpose>
    Contact one or more nodes and determine which vessels on those nodes are
    usable by a given identity.
  <Arguments>
    identity
      The identity whose vessels we are interested in. This can be the identity
      of either the vessel owner or a vessel user.
    nodelocation_list
      A list of nodelocations that should be contacted. This can be an empty
      list (which will result in an empty list of vesselhandles returned).
  <Exceptions>
    SeattleExperimentError
      If an error occurs performing a parallelized operation.
  <Returns>
    A list of vesselhandles.
  """
  _validate_identity(identity)
  _validate_nodelocation_list(nodelocation_list)
  
  successlist, failurelist = run_parallelized(nodelocation_list, browse_node, identity)

  vesseldicts = []
  
  for (nodeid, vesseldicts_of_node) in successlist:
    vesseldicts += vesseldicts_of_node

  return _create_list_from_key_in_dictlist(vesseldicts, "vesselhandle")





def browse_node(nodelocation, identity=None):
  """
  <Purpose>
    Contact an individual node to gather detailed information about all of the
    vessels on the node that are usable by a given identity.
  <Arguments>
    nodelocation
      The nodelocation of the node that should be browsed. 
    identity
      (optional) The identity whose vessels we are interested in. This can be
      the identity of either the vessel owner or a vessel user. If None,
      then the vesseldicts for all vessels on the node will be returned.
  <Exceptions>
    NodeCommunicationError
      If the communication with the node fails for any reason, including the
      node not being reachable, timeout in communicating with the node, the
      node rejecting the 
  <Returns>
    A list of vesseldicts. Each vesseldict contains the additional keys:
      'status'
        The status string of the vessel.
      'ownerkey'
        The vessel's owner key (in dict format).
      'userkeys'
        A list of the vessel's user keys (each in dict format).
  """
  try:
    _validate_nodelocation(nodelocation)
    if identity is not None:
      _validate_identity(identity)
    
    nmhandle = _get_nmhandle(nodelocation, identity)
    try:
      nodeinfo = fastnmclient.nmclient_getvesseldict(nmhandle)
    except fastnmclient.NMClientException, e:
      raise NodeCommunicationError("Failed to communicate with node " + nodelocation + ": " + str(e))
  
    # We do our own looking through the nodeinfo rather than use the function
    # nmclient_listaccessiblevessels() as we don't want to contact the node a
    # second time.
    usablevessels = []
    for vesselname in nodeinfo['vessels']:
      if identity is None:
        usablevessels.append(vesselname)
      elif identity['publickey_dict'] == nodeinfo['vessels'][vesselname]['ownerkey']:
        usablevessels.append(vesselname)
      elif 'userkeys' in nodeinfo['vessels'][vesselname] and \
          identity['publickey_dict'] in nodeinfo['vessels'][vesselname]['userkeys']:
        usablevessels.append(vesselname)
  
    nodeid = rsa.rsa_publickey_to_string(nodeinfo['nodekey'])
    # For efficiency, let's update the _node_location_cache with this info.
    # This can prevent individual advertise lookups of each nodeid by other
    # functions in the experimentlib that may be called later.
    _node_location_cache[nodeid] = nodelocation

    vesseldict_list = []
    for vesselname in usablevessels:
      vesseldict = {}
      # Required keys in vesseldicts (see the module comments for more info).
      vesseldict['vesselhandle'] = nodeid + ":" + vesselname
      vesseldict['nodelocation'] = nodelocation
      vesseldict['vesselname'] = vesselname
      vesseldict['nodeid'] = nodeid
      # Additional keys that browse_node provides.
      vesseldict['status'] = nodeinfo['vessels'][vesselname]['status']
      vesseldict['ownerkey'] = nodeinfo['vessels'][vesselname]['ownerkey']
      vesseldict['userkeys'] = nodeinfo['vessels'][vesselname]['userkeys']
      vesseldict['version'] = nodeinfo['version']
      vesseldict_list.append(vesseldict)
  
    return vesseldict_list
  
  except Exception, e:
    # Useful for debugging during development of the experimentlib.
    #traceback.print_exc()
    raise





def get_vessel_status(vesselhandle, identity):
  """
  <Purpose>
    Determine the status of a vessel.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel whose status is to be checked.
    identity
      The identity of the owner or a user of the vessel.
  <Exceptions>
    UnexpectedVesselStatusError
      If the status returned by the node for the vessel is not a status value
      that this experimentlib expects.
  <Side Effects>
    The node the vessel is on is communicated with.
  <Returns>
    A string that is one of the VESSEL_STATUS_* constants.
  """
  _validate_vesselhandle(vesselhandle)
  _validate_identity(identity)
    
  # Determine the last known location of the node. 
  nodeid, vesselname = vesselhandle.split(":")
  try:
    # This will get a cached node location if one exists.
    nodelocation = get_node_location(nodeid)
  except NodeLocationNotAdvertisedError, e:
    return VESSEL_STATUS_NO_SUCH_NODE
  
  try:
    vesselinfolist = browse_node(nodelocation, identity)
  except NodeCommunicationError:
    # Do a non-cache lookup of the nodeid to see if the node moved.
    try:
      nodelocation = get_node_location(nodeid, ignorecache=True)
    except NodeLocationNotAdvertisedError, e:
      return VESSEL_STATUS_NO_SUCH_NODE

    # Try to communicate again.
    try:
      vesselinfolist = browse_node(nodelocation, identity)
    except NodeCommunicationError, e:
      return VESSEL_STATUS_NODE_UNREACHABLE

  for vesselinfo in vesselinfolist:
    if vesselinfo['vesselhandle'] == vesselhandle:
      # The node is up and the vessel must have the identity's key as the owner
      # or a user, but the status returned isn't one of the statuses we
      # expect. If this does occur, it may indicate a bug in the experiment
      # library where it doesn't know about all possible status a nodemanager
      # may return for a vessel.
      if vesselinfo['status'] not in VESSEL_STATUS_SET_ACTIVE:
        raise UnexpectedVesselStatusError(vesselinfo['status'])
      else:
        return vesselinfo['status']
  else:
    # The node is up but this vessel doesn't exist.
    return VESSEL_STATUS_NO_SUCH_VESSEL
      




def _do_public_node_request(nodeid, requestname, *args):
  nodelocation = get_node_location(nodeid)
  nmhandle = _get_nmhandle(nodelocation)
  
  try:
    return fastnmclient.nmclient_rawsay(nmhandle, requestname, *args)
  except fastnmclient.NMClientException, e:
    raise NodeCommunicationError(str(e))





def _do_signed_vessel_request(identity, vesselhandle, requestname, *args):
  _validate_identity(identity, require_private_key=True)
  
  nodeid, vesselname = vesselhandle.split(':')
  nodelocation = get_node_location(nodeid)
  nmhandle = _get_nmhandle(nodelocation, identity)
  
  try:
    return fastnmclient.nmclient_signedsay(nmhandle, requestname, vesselname, *args)
  except fastnmclient.NMClientException, e:
    raise NodeCommunicationError(str(e))





def get_node_offcut_resources(nodeid):
  """
  <Purpose>
    Obtain information about offcut resources on a node.
  <Arguments>
    nodeid
      The nodeid of the node whose offcut resources are to be queried.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    None
  <Returns>
    A string containing information about the node's offcut resources.
  """
  # TODO: This function might be more useful if it processed the string
  # returned by the nodemanager and return it from this function as some
  # well-defined data structure.
  return _do_public_node_request(nodeid, "GetOffcutResources")
  




def get_vessel_resources(vesselhandle):
  """
  <Purpose>
    Obtain vessel resource/restrictions information.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessels whose restrictions/resources info are to
      be returned.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    None
  <Returns>
    A string containing the vessel resource/restrictions information.
  """
  # TODO: This function might be more useful if it processed the string
  # returned by the nodemanager and return it from this function as some
  # well-defined data structure.
  nodeid, vesselname = get_nodeid_and_vesselname(vesselhandle)
  return _do_public_node_request(nodeid, "GetVesselResources", vesselhandle)
  




def get_vessel_log(vesselhandle, identity):
  """
  <Purpose>
    Read the vessel log.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel whose log is to be read.
    identity
      The identity of either the owner or a user of the vessel.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    None
  <Returns>
    A string containing the data in the vessel log.
  """
  _validate_vesselhandle(vesselhandle)
  return _do_signed_vessel_request(identity, vesselhandle, "ReadVesselLog")





def get_vessel_file_list(vesselhandle, identity):
  """
  <Purpose>
    Get a list of files that are on the vessel.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel whose file list is to be obtained.
    identity
      The identity of either the owner or a user of the vessel.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    None
  <Returns>
    A list of filenames (strings).
  """
  _validate_vesselhandle(vesselhandle)
  file_list_string = _do_signed_vessel_request(identity, vesselhandle, "ListFilesInVessel")
  if not file_list_string:
    return []
  else:
    return file_list_string.split(' ')





def upload_file_to_vessel(vesselhandle, identity, local_filename, remote_filename=None):
  """
  <Purpose>
    Upload a file to a vessel.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel that the file is to be uploaded to.
    identity
      The identity of either the owner or a user of the vessel.
    local_filename
      The name of the local file to be uploaded. That can include a directory
      path.
    remote_filename
      (optional) The filename to use when storing the file on the vessel. If
      not provided, this will be the same as the basename of local_filename.
      Note that the remote_filename is subject to filename restrictions imposed
      on all vessels.
      TODO: describe the filename restrictions.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The file has been uploaded to the vessel.
  <Returns>
    None
  """
  _validate_vesselhandle(vesselhandle)
  
  if remote_filename is None:
    remote_filename = os.path.basename(local_filename)

  fileobj = open(local_filename, "r")
  filedata = fileobj.read()
  fileobj.close()
  
  _do_signed_vessel_request(identity, vesselhandle, "AddFileToVessel", remote_filename, filedata)





def download_file_from_vessel(vesselhandle, identity, remote_filename, local_filename=None,
                              add_location_suffix=False, return_file_contents=False):
  """
  <Purpose>
    Download a file from a vessel.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel that the file is to be downloaded from.
    identity
      The identity of either the owner or a user of the vessel.
    remote_filename
      The file to be downloaded.
    local_filename
      (optional) The filename to use when saving the downloaded file locally.
      This can include a directory path.
    add_location_suffix
      (optional) Whether the nodelocation and vesselname should be suffixed to
      the end of the local filename when saving the file.
    local_filename
      (optional) If True, the downloaded file will not be saved locally and
      instead will be returned as a string instead of the local filename.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The file has been downloaded and, if return_file_contents is False, it has
    been saved to the local filesystem.
  <Returns>
    If return_file_contents is False:
      The full filename where this file was ultimately saved to. This will be in
      the current working directory unless local_filename_prefix included a path
      to a different directory.
    If return_file_contents is True:
      The contents of the remote file as a string.
  """
  _validate_vesselhandle(vesselhandle)
  
  if not return_file_contents:
    if local_filename is None:
      local_filename = remote_filename
    if add_location_suffix:
      nodeid, vesselname = vesselhandle.split(':')
      nodelocation = get_node_location(nodeid)
      suffix = "_".join(nodelocation.split(':') + [vesselname])
      local_filename += "_" + suffix
  
  retrieveddata = _do_signed_vessel_request(identity, vesselhandle, "RetrieveFileFromVessel", remote_filename)
  
  if return_file_contents:
    return retrieveddata
  else:
    fileobj = open(local_filename, "w")
    fileobj.write(retrieveddata)
    fileobj.close()
    return local_filename





def delete_file_in_vessel(vesselhandle, identity, filename):
  """
  <Purpose>
    Delete a file from a vessel.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel that the file is to be deleted from.
    identity
      The identity of either the owner or a user of the vessel.
    filename
      The name of the file to be deleted from the vessel.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The file has been deleted from the vessel.
  <Returns>
    None
 """
  _validate_vesselhandle(vesselhandle)
  _do_signed_vessel_request(identity, vesselhandle, "DeleteFileInVessel", filename)





def reset_vessel(vesselhandle, identity):
  """
  <Purpose>
    Stop the vessel if it is running and reset it to a fresh state. This will
    delete all files from the vessel.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel that is to be reset.
    identity
      The identity of either the owner or a user of the vessel.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The vessel has been reset. No program is running, no files exist on the
    vessel, and the vessel status is VESSEL_STATUS_FRESH.
  <Returns>
    None
  """
  _validate_vesselhandle(vesselhandle)
  _do_signed_vessel_request(identity, vesselhandle, "ResetVessel")





def start_vessel(vesselhandle, identity, program_file, arg_list=None):
  """
  <Purpose>
    Start a program running on a vessel.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel that is to be started.
    identity
      The identity of either the owner or a user of the vessel.
    program_file
      The name of the file that already exists on the vessel that is to be
      run on the vessel.
    arg_list
      (optional) A list of arguments to be passed to the program when it is
      started.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The vessel has been started, running the specified program.
  <Returns>
    None
  """
  _validate_vesselhandle(vesselhandle)
  arg_string = program_file
  if arg_list is not None:
    arg_string += " " + " ".join(arg_list)
  _do_signed_vessel_request(identity, vesselhandle, "StartVessel", arg_string)
  





def stop_vessel(vesselhandle, identity):
  """
  <Purpose>
    Stop the currently running program on a vessel, if there is one.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel that is to be stopped.
    identity
      The identity of either the owner or a user of the vessel.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    If a program was running on the vessel, it has been stopped. The vessel
    state is either VESSEL_STATUS_STOPPED or VESSEL_STATUS_TERMINATED.
    TODO: verify this is the case and describe when these will happen.
  <Returns>
    None
  """
  _validate_vesselhandle(vesselhandle)
  _do_signed_vessel_request(identity, vesselhandle, "StopVessel")



  
  
def split_vessel(vesselhandle, identity, resourcedata):
  """
  <Purpose>
    Split a vessel into two new vessels.
    
    THIS OPERATION IS ONLY AVAILABLE TO THE OWNER OF THE VESSEL.
    If you have acquired the vessel through SeattleGENI, you are a user of the
    vessel, not an owner.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel that is to be split.
    identity
      The identity of the owner of the vessel.
    resourcedata
      The resourcedata that describes one of the vessels to be split from the
      original. The other vessel will have the remainder of the resources
      minus some overhead from the split.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The original vessel no longer exists (meaning that the vesselhandle passed
    in as an argument is no longer valid). The node instead has two new vessels.
  <Returns>
    A tuple of the two new vesselhandles that resulted from the split. The
    first element of the tuple is the vesselhandle of the vessel that has the
    leftover resources from the split. The second element of the tuple is the
    vesselhandle of the vessel that has the exact resources specified in the
    resourcedata.
  """
  _validate_vesselhandle(vesselhandle)
  return _do_signed_vessel_request(identity, vesselhandle, "SplitVessel", resourcedata)





def join_vessels(identity, vesselhandle1, vesselhandle2):
  """
  <Purpose>
    Join (combine) two vessels on the same node into one, larger vessel.
    
    THIS OPERATION IS ONLY AVAILABLE TO THE OWNER OF THE VESSEL.
    If you have acquired the vessel through SeattleGENI, you are a user of the
    vessel, not an owner.
  <Arguments>
    identity
      The identity of the owner of the vessel.
    vesselhandle1
      The vesselhandle of the one of the vessels to be comined.
    vesselhandle2
      The vesselhandle of the the other vessel to be combined.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    Neither of the original two vessel exist (meaning that neither vesselhandle1
    nor vesselhandle2 are valid anymore). The node has one new vessel whose
    resources are the combination of the resource of the original two vessels
    plus some additional resources because of less overhead from less splits.
  <Returns>
    The vesselhandle of the newly created vessel.
  """
  _validate_vesselhandle(vesselhandle1)
  _validate_vesselhandle(vesselhandle2)
  vesselname2 = vesselhandle2.split(":")[1]
  return _do_signed_vessel_request(identity, vesselhandle1, "JoinVessels", vesselname2)





def set_vessel_owner(vesselhandle, identity, new_owner_identity):
  """
  <Purpose>
    Change the owner of a vessel.
    
    THIS OPERATION IS ONLY AVAILABLE TO THE OWNER OF THE VESSEL.
    If you have acquired the vessel through SeattleGENI, you are a user of the
    vessel, not an owner.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel whose owner is to be changed.
    identity
      The identity of the current owner of the vessel. This identity must have
      a private key.
    new_owner_identity
      The identity that the owner of the vessel is to be changed to. This
      identity only needs to have a public key.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The owner of the vessel has been changed.
  <Returns>
    None
  """
  _validate_vesselhandle(vesselhandle)
  _do_signed_vessel_request(identity, vesselhandle, "ChangeOwner", new_owner_identity['publickey_str'])
  
  



def set_vessel_advertise(vesselhandle, identity, advertise_enabled):
  """
  <Purpose>
    Set whether the vessel should be advertising or not.
    
    THIS OPERATION IS ONLY AVAILABLE TO THE OWNER OF THE VESSEL.
    If you have acquired the vessel through SeattleGENI, you are a user of the
    vessel, not an owner.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel whose advertise status is to be set.
    identity
      The identity of the owner of the vessel.
    advertise_enabled
      True if the vessel should be advertising, False if it should not be.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The vessel either will be advertising or will not be.
  <Returns>
    None
  """
  _validate_vesselhandle(vesselhandle)
  
  if not isinstance(advertise_enabled, bool):
    raise TypeError("advertise_enabled must be a boolean.")

  _do_signed_vessel_request(identity, vesselhandle, "ChangeAdvertise", str(advertise_enabled))
  
  



def set_vessel_ownerinfo(vesselhandle, identity, ownerinfo):
  """
  <Purpose>
    Set the owner info of a vessel.
    
    THIS OPERATION IS ONLY AVAILABLE TO THE OWNER OF THE VESSEL.
    If you have acquired the vessel through SeattleGENI, you are a user of the
    vessel, not an owner.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel whose advertise status is to be set.
    identity
      The identity of the owner of the vessel.
    ownerinfo
      The ownerinfo to be set on the vessel.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The ownerinfo of the vessel has been set.
  <Returns>
    None
  """
  _validate_vesselhandle(vesselhandle)
  _do_signed_vessel_request(identity, vesselhandle, "ChangeOwnerInformation", ownerinfo)


  


def set_vessel_users(vesselhandle, identity, userkeystringlist):
  """
  <Purpose>
    Change the owner of a vessel.
    
    THIS OPERATION IS ONLY AVAILABLE TO THE OWNER OF THE VESSEL.
    If you have acquired the vessel through SeattleGENI, you are a user of the
    vessel, not an owner.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel whose users are to be set.
    identity
      The identity of the owner of the vessel.
    userkeystringlist
      A list of key strings. The key strings must be in the format of the data
      stored in key files. That is, each should be a string that consists of
      the modulus, followed by a space, followed by the public exponent.
  <Exceptions>
    NodeCommunicationError
      If communication with the node failed, either because the node is down,
      the communication timed out, the signature was invalid, or the identity
      unauthorized for this action.
  <Side Effects>
    The user keys in userkeystringlist are the only users of the vessel.
  <Returns>
    None
  """
  _validate_vesselhandle(vesselhandle)
  # TODO: Arguably the argument should be a list of identities rather than a
  # list of key strings.
  formatteduserkeys = '|'.join(userkeystringlist)
  _do_signed_vessel_request(identity, vesselhandle, "ChangeUsers", formatteduserkeys)
  




def get_nodeid_and_vesselname(vesselhandle):
  """
  <Purpose>
    Given a vesselhandle, returns the nodeid and vesselname.
  <Arguments>
    vesselhandle
      The vesselhandle of the vessel whose nodeid and vesselname are to be
      returned.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A tuple of (nodeid, vesselname)
  """
  _validate_vesselhandle(vesselhandle)
  return vesselhandle.split(":")





def get_vesselhandle(nodeid, vesselname):
  """
  <Purpose>
    Given a nodeid and vesselname, returns a vesselhandle that represents the
    vessel.
  <Arguments>
    nodeid
      The nodeid of the node that the vessel is on.
    vesselname
      The name of the vessel.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A vesselhandle.
  """
  return nodeid + ":" + vesselname





def get_host_and_port(nodelocation):
  """
  <Purpose>
    Given a nodelocation, returns the host and port of the node. 
  <Arguments>
    nodelocation
      The nodelocation of the node whose host and port are to be returned.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    A tuple of (host, port), where host is a string and port is an int.
    The host may be an IP address or an identifier used by NAT forwarders.
  """
  _validate_nodelocation(nodelocation)
  host, portstr = nodelocation.split(":")
  return host, int(portstr)





def get_node_location(nodeid, ignorecache=False):
  """
  <Purpose>
    Determine a nodelocation given a nodeid.
  <Arguments>
    nodeid
      The nodeid of the node whose location is to be determined.
    ignorecache
      (optional, default is False) Whether to ignore cached values for this
      node's location, forcing an advertise lookup and possibly also
      attempting to contact potential nodelocations.
  <Exceptions>
    NodeLocationLookupError
      If no node locations are being advertised under the nodeid or if a
    NodeCommunicationError
      If multiple node locations are being advertised under the nodeid but
      successful communication cannot be performed with any of the locations.
  <Side Effects>
    If the node location isn't already known (or if ignorecache is True),
    then an advertise lookup of the nodeid is done. In that case, if
    multiple nodelocations are advertised under the nodeid, then each location
    will be contacted until one is determined to be a valid nodelocation
    that can be communicated with.
  <Returns>
    A nodelocation. This nodelocation may or may not have been communicated
    with and is instead only the most likely location of a node at the time
    this function was called.
  """
  if ignorecache or nodeid not in _node_location_cache:
    locationlist = lookup_node_locations_by_nodeid(nodeid)
    if not locationlist:
      raise NodeLocationLookupError("Nothing advertised under node's key.")
    # If there is more than one advertised location, we need to figure out
    # which one is valid. For example, if a node moves then there will be
    # a period of time in which the old advertised location and the new
    # one are both returned. We need to determine the correct one.
    elif len(locationlist) > 1:
      for possiblelocation in locationlist:
        host, portstr = possiblelocation.split(':')
        try:
          # We create an nmhandle directly because we want to use it to test
          # basic communication, which is done when an nmhandle is created.
          nmhandle = fastnmclient.nmclient_createhandle(host, int(portstr))
        except fastnmclient.NMClientException, e:
          continue
        else:
          fastnmclient.nmclient_destroyhandle(nmhandle)
          _node_location_cache[nodeid] = possiblelocation
          break
      else:
        raise NodeCommunicationError("Multiple node locations advertised but none " + 
                                     "can be communicated with: " + str(locationlist))
    else:
      _node_location_cache[nodeid] = locationlist[0]
      
  return _node_location_cache[nodeid]





def get_nodeid(nodelocation):
  """
  <Purpose>
    Determine a nodelocation given a nodeid. Note that if you have already
    obtained a vesselhandle for a vessel on the node, you can get the nodeid
    using get_nodeid_and_vesselname(vesselhandle), which would avoid having
    to contact the node.
  <Arguments>
    nodelocation
      The nodelocation of the node whose nodeid is to be determined.
  <Exceptions>
    NodeCommunicationError
      If a failure occurs in communicating with the node.
  <Side Effects>
    None
  <Returns>
    A nodeid.
  """
  # We assume at least one vessel on the node. This is a safe assumption
  # unless there's something very wrong with the node.
  return browse_node(nodelocation)[0]['nodeid']

  


  
def _call_seattlegeni_func(func, *args, **kwargs):
  """
  Helper function to limit the potential errors raised by seattlegeni_*
  functions to SeattleClearinghouseError or classes that extend it. The seattleclearinghouse_xmlrpc
  module doesn't catch ProtocolError or unexpected xmlrpc faults. At the level
  of the experimentlib, though, we just consider these generic failures for the
  purpose of simlifying error handling when using the experimentlib.
  """
  try:
    return func(*args, **kwargs)
  except xmlrpclib.ProtocolError:
    raise SeattleClearinghouseError("Failed to communicate with SeattleGENI. " +
                           "Are you using the correct xmlrpc url? " + traceback.format_exc())
  except xmlrpclib.Fault:
    raise SeattleClearinghouseError("Unexpected XML-RPC fault when talking to SeattleGENI. " +
                           "Are you using a current version of experimentlib.py and " +
                           "seattleclearinghouse_xmlrpc.py? " + traceback.format_exc())

  



def _get_seattlegeni_client(identity):
  
  if "seattlegeniclient" not in identity:
    _validate_identity(identity, require_private_key=True, require_username=True)
    private_key_string = rsa.rsa_privatekey_to_string(identity["privatekey_dict"])
    # We use _call_seattlegeni_func because the SeattleClearinghouseClient constructor
    # may attempt to communicate with SeattleClearinghouse.
    client = _call_seattlegeni_func(seattleclearinghouse_xmlrpc.SeattleClearinghouseClient,
                                    identity['username'],
                                    private_key_string=private_key_string,
                                    xmlrpc_url=SEATTLECLEARINGHOUSE_XMLRPC_URL,
                                    allow_ssl_insecure=SEATTLECLEARINGHOUSE_ALLOW_SSL_INSECURE,
                                    ca_certs_file=SEATTLECLEARINGHOUSE_CA_CERTS_FILES)
    identity["seattlegeniclient"] = client
    
  return identity["seattlegeniclient"]

  
  

  
def _seattlegeni_cache_node_locations(seattlegeni_vessel_list):
  """
  This takes a list of vessel dicts that aren't the standard vesseldict this
  module normally deals with. Instead, these are dicts with the keys that are
  directly returned by the seattlegeni xmlrpc api.
  """
  for seattlegeni_vessel in seattlegeni_vessel_list:
    nodeid = seattlegeni_vessel['node_id']
    ip = seattlegeni_vessel['node_ip']
    portstr = str(seattlegeni_vessel['node_port'])
    _node_location_cache[nodeid] = ip + ':' + portstr





def seattlegeni_acquire_vessels(identity, vesseltype, number):
  """
  <Purpose>
    Acquire vessels of a certain type from SeattleGENI. This is an
    all-or-nothing request. Either the number requested will be acquired or
    no vessels will be acquired.
  <Arguments>
    identity
      The identity to use for communicating with SeattleGENI.
    vesseltype
      The type of vessels to be acquired. This must be one of the constants
      named SEATTLECLEARINGHOUSE_VESSEL_TYPE_*
    number
      The number of vessels to be acquired.
  <Exceptions>
    The common SeattleGENI exceptions described in the module comments, as well as:
    SeattleClearinghouseNotEnoughCreditsError
      If the account does not have enough available vessel credits to fulfill
      the request.
  <Side Effects>
    Either the full number of vessels requested are acquired or none are.
  <Returns>
    A list of vesselhandles of the acquired vessels.
  """
  client = _get_seattlegeni_client(identity)
  seattlegeni_vessel_list = _call_seattlegeni_func(client.acquire_resources, vesseltype, number)

  _seattlegeni_cache_node_locations(seattlegeni_vessel_list)
  
  return _create_list_from_key_in_dictlist(seattlegeni_vessel_list, "handle")





def seattlegeni_acquire_specific_vessels(identity, vesselhandle_list):
  """
  <Purpose>
    Acquire specific vessels from SeattleGENI. This is not an all-or-nothing
    request.
  <Arguments>
    identity
      The identity to use for communicating with SeattleGENI.
    vesselhandle_list
      A list of vesselhandles. Even though the request may be only partially
      fulfilled, the size of this list must not be greater than the number of
      vessels the account has available to acquire.
  <Exceptions>
    The common SeattleGENI exceptions described in the module comments, as well as:
    SeattleClearinghouseNotEnoughCreditsError
      If the account does not have enough available vessel credits to fulfill
      the request.
  <Side Effects>
    If successful, zero or more vessels from handlelist have been acquired.
  <Returns>
    A list of vesselhandles of the acquired vessels.
  """
  client = _get_seattlegeni_client(identity)
  seattlegeni_vessel_list = _call_seattlegeni_func(client.acquire_specific_vessels, vesselhandle_list)
  
  _seattlegeni_cache_node_locations(seattlegeni_vessel_list)
  
  return _create_list_from_key_in_dictlist(seattlegeni_vessel_list, "handle")





def seattlegeni_release_vessels(identity, vesselhandle_list):
  """
  <Purpose>
    Release vessels from SeattleGENI.
  <Arguments>
    identity
      The identity to use for communicating with SeattleGENI.
    vesselhandle_list
      The vessels to be released.
  <Exceptions>
    The common SeattleGENI exceptions described in the module comments.
  <Side Effects>
    The vessels are released from the SeattleGENI account.
  <Returns>
    None
  """
  _validate_vesselhandle_list(vesselhandle_list)
  
  client = _get_seattlegeni_client(identity)
  _call_seattlegeni_func(client.release_resources, vesselhandle_list)





def seattlegeni_renew_vessels(identity, vesselhandle_list):
  """
  <Purpose>
    Renew vessels previously acquired from SeattleGENI.
  <Arguments>
    identity
      The identity to use for communicating with SeattleGENI.
    vesselhandle_list
      The vessels to be renewed.
  <Exceptions>
    The common SeattleGENI exceptions described in the module comments, as well as:
    SeattleGENINotEnoughCredits
      If the account is currently over its vessel credit limit, then vessels
      cannot be renewed until the account is no longer over its credit limit.
  <Side Effects>
    The expiration time of the vessels is is reset to the maximum.
  <Returns>
    None
  """
  _validate_vesselhandle_list(vesselhandle_list)
  
  client = _get_seattlegeni_client(identity)
  _call_seattlegeni_func(client.renew_resources, vesselhandle_list)





def seattlegeni_get_acquired_vessels(identity):
  """
  <Purpose>
    Obtain a list of vesselhandles corresponding to the vessels acquired through
    SeattleGENI.
  
    In order to return a data format that is most useful with the other functions
    in this module, this function drops some potentially useful info. Therefore,
    there's a separate function:
      seattlegeni_get_acquired_vessels_details()
    for obtaining all of the vessel information returned by seattlegeni.
  <Arguments>
    identity
      The identity to use for communicating with SeattleGENI.
  <Exceptions>
    The common SeattleGENI exceptions described in the module comments.
  <Side Effects>
    None
  <Returns>
    A list of vesselhandles.
  """  
  vesseldict_list = seattlegeni_get_acquired_vessels_details(identity)

  # We look for the vesselhandle key rather than 'handle' because these
  # are vesseldicts, by our definition of them, not the raw dictionaries
  # that seattlegeni hands back. 
  return _create_list_from_key_in_dictlist(vesseldict_list, "vesselhandle")





def seattlegeni_get_acquired_vessels_details(identity):
  """
  <Purpose>
    Obtain a list of vesseldicts corresponding to the the vessels acquired
    through SeattleGENI.
  <Arguments>
    identity
      The identity to use for communicating with SeattleGENI.
  <Exceptions>
    The common SeattleGENI exceptions described in the module comments.
  <Side Effects>
    None
  <Returns>
    A list of vesseldicts that have the additional key 'expires_in_seconds'.
  """  
  client = _get_seattlegeni_client(identity)
  seattlegeni_vessel_list = _call_seattlegeni_func(client.get_resource_info)
  
  _seattlegeni_cache_node_locations(seattlegeni_vessel_list)

  # Convert these dicts into dicts that have the required keys for us to
  # consider them "vesseldicts", by the definition given in the module
  # comments.
  vesseldict_list = []
  for seattlegeni_vessel in seattlegeni_vessel_list:
    vesseldict = {}
    vesseldict_list.append(vesseldict)

    nodeid = seattlegeni_vessel['node_id']
    ip = seattlegeni_vessel['node_ip']
    portstr = str(seattlegeni_vessel['node_port'])
    vesselname = seattlegeni_vessel['vessel_id']
    
    # Required keys in vesseldicts (see the module comments for more info).
    vesseldict['vesselhandle'] = nodeid + ":" + vesselname
    vesseldict['nodelocation'] = ip + ':' + portstr
    vesseldict['vesselname'] = vesselname
    vesseldict['nodeid'] = nodeid
    # Additional keys that browse_node provides.
    vesseldict['expires_in_seconds'] = seattlegeni_vessel['expires_in_seconds']

  return vesseldict_list





def seattlegeni_max_vessels_allowed(identity):
  """
  <Purpose>
    Determine the maximum number of vessels that can be acquired by this
    account through SeattleGENI, regardless of the number currently acquired.
    That is, this is an absolute maximum, not the number that can still be
    acquired based on the number already acquired.
  <Arguments>
    identity
      The identity to use for communicating with SeattleGENI.
  <Exceptions>
    The common SeattleGENI exceptions described in the module comments.
  <Side Effects>
    None
  <Returns>
    The maximum number of vessels the account can acquire (an integer).
  """  
  client = _get_seattlegeni_client(identity)
  # We can't cache this value because it may change as the user's donations
  # come online and go offline.
  return _call_seattlegeni_func(client.get_account_info)['max_vessels']





def seattlegeni_user_port(identity):
  """
  <Purpose>
    Determine the port which SeattleGENI guarantees will be usable by the
    account on all acquired vessels.
  <Arguments>
    identity
      The identity to use for communicating with SeattleGENI.
  <Exceptions>
    The common SeattleGENI exceptions described in the module comments.
  <Side Effects>
    None
  <Returns>
    The port number (an integer).
  """  
  client = _get_seattlegeni_client(identity)
  # The user port won't change, so let's not make a new seattlegeni request
  # each time just in case someone uses this a lot in their program. We'll go
  # ahead and keep in this in the identity. It's not a documented part of
  # the identity so nobody should be trying to access it directly.
  if 'user_port' not in identity:
    identity['user_port'] = _call_seattlegeni_func(client.get_account_info)['user_port']
  return identity['user_port']
