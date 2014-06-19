"""
<Program>
  vesselstatusmonitor.py

<Author>
  Justin Samuel
  
<Date Started>
  December 11, 2009
  
<Usage>

  See examples/monitor_vessel_status.py for an example of using this module.

  Object Definitions:
        
    * monitorhandle: an object that can be provided to various functions to
      update or modify a previously created vessel status monitor.
      
    * All other objects are the same as provided/used by experimentlib.py
  
<Purpose>
  Provides a callback-based vessel status monitoring system. One registers a
  callback (what is essentially an observer) that is called whenever the status
  of a watched vessel changes.
  
  This is a module that may be directly useful in some situations and also
  provides an example of building functionality on top of the experimentlib,
  which this uses.
  
  Note that even though a given monitor will never overlap with the run of the
  that monitor, but different monitors may run at the same time. Additionally,
  even though a single monitor will only contact a given vessel once in a
  single run, the monitor isn't implemented to recognize that two vessels are
  on the same node. Either of these factors (multiple monitors or multiple
  vessels on the same node) can result in a single node being contacted by
  multiple threads simultaneously. The nodemanager on the node may drop
  connections from this client, in that case.
"""

import random
import sys
import threading
import traceback

import experimentlib

import repyimporter

# A few repy api functions we use.
settimer = repyimporter.settimer
canceltimer = repyimporter.canceltimer





# Keys are monitor ids we generate. Values are dicts with the following keys:
#    'vesselhandle_list': the list of vesselhandles this monitor is registered for.
#    'vessels': stored data related to individual vessels.
#    'waittime': the number of seconds between initiating processing of vessels.
#    'callback': a the registered callback function
#    'timerhandle': a timer handle for the registered callback
#    'concurrency': the number of threads to use to process vessels.
_vessel_monitors = {}

_monitor_lock = threading.Lock()





def _debug_print(msg):
  print >> sys.stderr, msg






def _run_monitor(monitordict):
  """Performs the actual monitoring of vessels."""
  # Copy the vesselhandle_list so that changes made to the list can't happen
  # while the parallelized call is being done.
  vesselhandle_list = monitordict['vesselhandle_list'][:]
  
  experimentlib.run_parallelized(vesselhandle_list, _check_vessel_status_change, monitordict)
  
  # We finished the last run, now schedule another.
  monitordict['timerhandle'] = settimer(monitordict['waittime'], _run_monitor, [monitordict])





def _check_vessel_status_change(vesselhandle, monitordict):
  """
  Checks the status of an individual vessel and calls the registered
  callback function for the monitor if the vessel's status has changed since
  the last time it was checked.
  """
  try:
    # When the monitor is removed/canceled, the parallelized function isn't
    # aborted and we instead just have each of these calls immediately return.
    if monitordict['canceled']:
      return
    
    datadict = monitordict['vessels'][vesselhandle]
    if 'status' not in datadict:
      datadict['status'] = ''
      
    old_data = datadict.copy()
    
    status = experimentlib.get_vessel_status(vesselhandle, monitordict['identity'])
    datadict['status'] = status
    
    # No matter where the above try block returned from, we want to see if
    # the vessel data changed and call the user's callback if it has.
    new_data = datadict.copy()
    
    # Note that by not letting the lock go before we call the user's callback
    # function, the processing of all of the vessels will slow down but we
    # avoid requiring the user to handle locking to protect against another
    # call to the callback for the same vessel.
    if old_data['status'] != new_data['status']:
      try:
        # TODO: make sure that exception's from the user's code end up
        # somewhere where the user has access to them. For now, we leave it to
        # the user to make sure they handle exceptions rather than let them
        # escape their callback and this is documented in the docstring of
        # the function register_vessel_status_monitor.
        monitordict['callback'](vesselhandle, old_data['status'], new_data['status'])
      
      except Exception:
        _debug_print("Exception occurred in vessel status change callback:")
        _debug_print(traceback.format_exc())
  
    # In order to prevent repeating failures, we remove the vesselhandle
    # from the monitor's list if the status indicates a positive response.
    # This means that scripts should occasionally add their known active
    # vessels to the monitor to prevent temporary failures from causing the
    # vessel to be subsequently ignored forever.
    if status in experimentlib.VESSEL_STATUS_SET_INACTIVE:
      _monitor_lock.acquire()
      try:
        monitordict['vesselhandle_list'].remove(vesselhandle)
        # We don't "del monitordict['vessels'][vesselhandle]" because it
        # doesn't hurt anything to leave it other than taking up a bit of
        # space, and it feels safer to leave it there just in case, for
        # example, this code got changed to put the "remove" call in the
        # try block above when access to the vessel's lock is still needed.
      finally:
        _monitor_lock.release()
      
  except Exception:
    _debug_print(traceback.format_exc())






def register_vessel_status_monitor(identity, vesselhandle_list, callback, waittime=300, concurrency=10):
  """
  <Purpose>
    Registers a vessel status monitor. Once registered, a monitor occassionally
    checks the status of each vessel. If the vessel's status has changed or was
    never checked before, the provided callback function is called with
    information about the status change.
  <Arguments>
    identity
      The identity to be used when looking checking vessel status. This is
      mostly needed to determine whether the vessel exists but no longer is
      usable by the identity (that is, if the public key of the identity is
      no longer neither the owner or a user of the vessel).
    vesselhandle_list
      A list of vesselhandles of the vessels to be monitored.
    callback
      The callback function. This should accept three arguments:
        (vesselhandle, oldstatus, newstatus)
      where oldstatus and newstatus are both strings. Any exceptions raised by
      the callback will be silently ignored, so the callback should implement
      exception handling.
    waittime
      How many seconds to wait between status checks. This will be the time
      between finishing a check of all vessels and starting another round of
      checking.
    concurrency
      The number of threads to use for communicating with nodes. This will be
      the maximum number of vessels that can be checked simultaneously.
  <Exceptions>
    None
  <Side Effects>
    Immediately starts a vessel monitor running.
  <Returns>
    A monitorhandle which can be used to update or cancel this monitor.
  """
  experimentlib._validate_vesselhandle_list(vesselhandle_list)
  experimentlib._validate_identity(identity)
  
  # We copy the vesselhandle_list so that the user doesn't directly modify.
  vesselhandle_list = vesselhandle_list[:]
  
  _monitor_lock.acquire()
  try:
    # Create a new monitor key in the the _vessel_monitors dict.
    for attempt in range(10):
      id = "MONITOR_" + str(random.random())
      if id not in _vessel_monitors:
        break
    else:
      # I don't intend users to need to worry about this exception. I also
      # don't know of a more specific built-in exception to use and I don't
      # feel this should raise a SeattleExperimentException. Therefore,
      # intentionally raising a generic Exception here.
      raise Exception("Can't generate a unique vessel monitor id. " + 
                      "This probably means a bug in experimentlib.py")
    _vessel_monitors[id] = {}
    
    _vessel_monitors[id]['vesselhandle_list'] = vesselhandle_list
    _vessel_monitors[id]['waittime'] = waittime
    _vessel_monitors[id]['callback'] = callback
    _vessel_monitors[id]['concurrency'] = concurrency
    _vessel_monitors[id]['identity'] = identity
    # Whether the monitor was canceled/removed. Used to indicate to a running
    # monitor that it should stop doing work.
    _vessel_monitors[id]['canceled'] = False
    
    # Keeps track of the status of individual vessels. This is used by
    # vessel monitors to determine when the status has changed.
    _vessel_monitors[id]['vessels'] = {}
    for handle in vesselhandle_list:
      _vessel_monitors[id]['vessels'][handle] = {}
    
    # The first time we run it we don't delay. Storing the timer handle is a
    # bit useless in this case but we do it for consistency.
    _vessel_monitors[id]['timerhandle'] = settimer(0, _run_monitor, [_vessel_monitors[id]])
    
    return id
  
  finally:
    _monitor_lock.release()

  



def remove_vessel_status_monitor(monitorhandle):
  """
  <Purpose>
    Cancel a monitor that was created through register_vessel_status_monitor.
    Note that this will not terminate any already active run of the monitor
    (a run is a pass through contacting all relevant nodes to determine
    vessel status), but it will prevent future runs from starting.
  <Arguments>
    monitorhandle
      A monitorhandle returned by register_vessel_status_monitor.
  <Exceptions>
    ValueError
      If no such monitorhandle exists (including if it was already removed).
  <Side Effects>
    Stops future runs of the monitor and signals to any currently running
    monitor to stop. It is still possible that the registered callback for
    the monitor will be called after this function returns.
  <Returns>
    None
  """
  _monitor_lock.acquire()
  try:
    # Ensure the monitorhandle is valid.
    if not monitorhandle in _vessel_monitors:
      raise ValueError("The provided monitorhandle is invalid: " + str(monitorhandle))
    
    # Not using parallelize_abortfunction() because I didn't want to complicate
    # things by needing a way to get a hold of the parellelizehandle. Instead,
    # individual calls to _check_vessel_status_change will check if the monitor
    # was removed/canceled before doing any work.
    _vessel_monitors[monitorhandle]['canceled'] = True
    
    # Ignore the return value from canceltimer. If the user wants to ensure
    # that no further actions are taken in their own code due to this monitor,
    # they can do so by ignoring calls to their provided callback.
    canceltimer(_vessel_monitors[monitorhandle]['timerhandle'])
    
    del _vessel_monitors[monitorhandle]
    
  finally:
    _monitor_lock.release()





def add_to_vessel_status_monitor(monitorhandle, vesselhandle_list):
  """
  <Purpose>
    Adds the vesselhandles in vesselhandle_list to the specified monitor. If
    any already are watched by the monitor, they are silently ignored. There
    is no removal of previously added vesselhandles other than automatic
    removal done when vessels are unreachable or otherwise invalid.
    
    One intention of this function is that new vessels found via a
    lookup_node_locations_by_identity and then find_vessels_on_nodes can be
    passed to this function as a way of making sure the monitor knows about
    new vessels that a user has just obtained access to or which have recently
    come online. 
  <Arguments>
    monitorhandle
      A monitorhandle returned by register_vessel_status_monitor.
    vesselhandle_list
      A list of vesselhandles to add to the monitor.
  <Side Effects>
    The next run of the monitor will include the provided vesselhandles.
  <Exceptions>
    ValueError
      If no such monitorhandle exists (including if it was already removed).
  <Returns>
    None
  """
  experimentlib._validate_vesselhandle_list(vesselhandle_list)
  
  _monitor_lock.acquire()
  try:
    # Ensure the monitorhandle is valid.
    if not monitorhandle in _vessel_monitors:
      raise ValueError("The provided monitorhandle is invalid: " + str(monitorhandle))
    
    for vesselhandle in vesselhandle_list:
      if vesselhandle not in _vessel_monitors[monitorhandle]['vesselhandle_list']:
        _vessel_monitors[monitorhandle]['vesselhandle_list'].append(vesselhandle)
        _vessel_monitors[monitorhandle]['vessels'][vesselhandle] = {}
    
  finally:
    _monitor_lock.release()
