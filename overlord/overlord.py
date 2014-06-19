"""
<Program Name>
  Overlord Deployment and Monitoring Library

<Author>
  Evan Meagher
  Alan Loh

<Date Started>
  May 1, 2010

<Description>
  A class for deploying an arbitrary repy program on a number of vessels.
  Built on top of the Experiment Library, Overlord persistently manages a
  user-defined number of vessels, ensuring that the specified service is up
  and running.

  The behavior of an Overlord object can be customized to fit the
  user's needs. They can be overriden with the user's own functions, although
  certain restrictions on behavior and argument passing still apply.
  Details, along with the default function's coding, are listed near the end.

<Requirements>
  An instance of the Experiment Library must exist in a subdirectory named
  'experimentlibrary'. This directory can be setup by following the
  instructions on the Seattle wiki:
  https://seattle.cs.washington.edu/wiki/ExperimentLibrary

  Also note that Overlord requires a secure connection to SeattleGENI.
  To perform secure SSL communication with SeattleGENI, you must:
    * Have M2Crypto installed (http://chandlerproject.org/Projects/MeTooCrypto)
    * Have a PEM file, cacert.pem, containing CA certificates in the
      experimentlibrary directory. One such file can be found at
      http://curl.haxx.se/ca/cacert.pem

  For more inforation on SSL communication with SeattleGENI, see
  https://seattle.cs.washington.edu/wiki/SeattleGeniClientLib
  
<Usage>
  To create an Overlord client, simply import it:

    import overlord

  and then initiate an Overlord object with your desired parameters and execute
  its 'run()' function.
  For example, to deploy time servers on 10 wan vessels:

    import overlord
    time_server = overlord.Overlord(GENI_USERNAME, 10, 'wan', 'time_server.repy')
    time_server.run(time_server.config['geni_port'])

  Note that time_server.repy requires a port number as an argument, so the user's
  GENI port is passed to the run() function.
    
  For more examples of using this experimentlib, see the examples/ directory.

  Please also see the following wiki page for usage information and how to
  obtain the latest version of this library:
  https://seattle.cs.washington.edu/wiki/Overlord


  AL: CUSTOMIZING OVERLORD'S LOGGING BEHAVIOR

  By default, Overlord will log directly to console screen without saving a log
  file if no filename was passed for the argument 'log_filename' during
  initialization. In order to log to both a file and to console screen, in 
  addition to passing the filename of the log file during initialization, a
  console logger needs to be added to the Overlord instances logger like so:

    import logging
    import overlord
    # Initialization of Overlord instance that logs to test_log.log
    overl_instance = overlord.Overlord(GENI_USERNAME, 10, "wan", "test.repy", "test_log.log")
    # Initialization of a log stream to console
    consoleLog = logging.StreamHandler()
    consoleLog.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%H:%M:%S'))
    # Adding the console logger to Overlord's logging behavior,
    # thus allowing it to log both to file and to console
    overl_instance.logger.addHandler(consoleLog)



  AL: CUSTOMIZING OVERLORD'S RUN OPERATIONS

  After initialization of the overlord's instance as an object, the default
  functions can be overriden by simply setting the respective variables listed
  below with the name of the user's own functions.

  For example, to have Overlord just print 'foo' instead of performing its default
  start-up procedure, after initiating an instance of overlord but before running it:
  
    # Overriding run()'s start-up operations to just print "foo"
    time_server.init_overlord_func = print_foo
    ...
    # The coding for the method, taking the required overlord instance argument
    def print_foo(overlord):
      print "foo"
    ...

  Further details on the functions that make up run(), a brief description of
  their purpose, and requirements and restrictions are user's override methods
  are listed as follows:

  Note: In addition to taking in arguments specified in the notes that follows,
  each function is expected to take in an Overlord object for access to
  the particular instance's variables.

  init_overlord_func : How you want overlord's run() operations to start-up.
                       By default, it will automatically release any vessels
                       currently owned by the SeattleGENI identity.
                       Should not return anything at the end of its function.

  acquire_vessels_func : How you want overlord to acquire vessels.
                         By default, acquires up to the amount specified in 
                         config['vessel_count'] of the type specified in 
                         config['vessel_type'], but no more than what the 
                         user's vessel credit allows them to have.
                         Should take in a list of vesselhandles to keep track of
                         any changes in the list of vessels owned, and return
                         a list of newly acquired vesselhandles, if any.

  init_vessels_func : How you want overlord to set-up the vessels upon acquisition.
                      By default, uploads and runs the program specified in
                      config['program_filename'], and releases any vessels that 
                      failed during the process
                      Should take in a list of newly acquired vesselhandles and
                      a list of currently owned vesselhandles. Should return a
                      newly updated list of vesselhandles that includes ones
                      currently owned and new vessels that were successfully
                      initialized
 
  remove_vessels_func : How you want overlord to deal with vessels of
                        certain status.
                        By default, releases any vessels that have any status
                        other than 'Started'
                        Should take in and return a list of vessels that the
                        SeattleGENI identity currently owns.

  maintenance_func : How you want overlord to maintain the vessels
                     By default, renews the vessels automatically every 2 days at
                     minimum, and does a polling loop every 15 minutes.
                     Should take in a timedelta object to keep track of renewal
                     delay and the time of last renewal, and return the updated
                     time of renewal

  UNMODIFABLE BEHAVIOR 
  There are some behavior in the overlord's run function that cannot be modified,
  and they are listed in the following:
  - Retrieval of identity's current list of vessels, regardless
      of start-up function
  - Setting the time of last renewal to be the current time of
      its execution
  - The creation of a timedelta object from VESSEL_RENEWAL_PERIOD
  - 'Sleeping' Overlord's process at the end of each loop for the amount of time
      specified in VESSEL_RENEWAL_PERIOD
"""

import logging
import os
import os.path
import sys
import time
from datetime import datetime, timedelta

# We assume that the experiment library files exist in the 'experimentlibrary'
# subdirectory of the current directory.
sys.path.append(os.path.join(os.path.dirname(__file__), 'experimentlibrary'))
import experimentlib as explib


class Overlord:
  
  # CONFIGURATION
  # Behavior can be modified through the Overlord instance object before
  # executing run()

  # The timeout threshold for communicating with vessels, in seconds. We use a
  # larger value here because program uploads may take a while.
  explib.defaulttimeout = 90

  # How often vessel status should be polled, in seconds. More specifically, the
  # time to sleep before starting a new polling loop.
  VESSEL_POLLING_PERIOD = 15 * 60

  # The minimum time between vessel renewals, in seconds. The time may be longer
  # in practice because of the time it takes to run through the polling loop.
  # Note: 86400 seconds = 1 day
  VESSEL_RENEWAL_PERIOD = 2 * 86400

  # The default log level. For example, logging.INFO or logging.DEBUG
  DEFAULT_LOG_LEVEL = logging.DEBUG



  # Configuration info, to be populated as overlord runs.
  config = {
    'identity': None,
    'geni_port': None,
    'vessel_count': None,
    'vessel_type': None,
    'program_filename': None,
    }



  # LOGGING

  # Obtain the root logger and set the default logging level.
  logger = logging.getLogger('')
  logger.setLevel(DEFAULT_LOG_LEVEL)


  
  # OVERRIDABLE RUN() FUNCTIONS

  init_overlord_func = None
  acquire_vessels_func = None
  init_vessels_func = None
  remove_vessels_func = None
  maintenance_func = None



  def __init__(self, geni_username, vessel_count, vessel_type, program_filename, log_filename=None):
    """
    <Purpose>
      Initializes an instance of Overlord for the deployment of an arbitrary service.
      Populates the instance's configuration dictionary, which can be accessed from
      the object if data is needed for the run() function

    <Arguments>
      geni_username
        SeattleGENI username. Used to locate and handle public and private key
        files.
      vesselcount
        The number of vessels on which to deploy.
      vesseltype
        The type of vessel to acquire, based on the SEATTLECLEARINGHOUSE_VESSEL_TYPE_*
        constants within experimentlib.py
      program_filename
        The filename of the program to deploy and monitor on vessels.
      log_filename
        The file the user wants overlord to log to. If None, logs directly to
        console

    <Exceptions>
      ValueError
        Raised if argument vesseltype doesn't match one of the experimentlib
        SEATTLECLEARINGHOUSE_VESSEL_TYPE_* constants, if argument program file does not
        exist, or if argument number of vessels on which to deploy exceeds the
        user's number of vessel credits.

    <Side Effects>
      Initializes certain global variables.
      Removes 'stop' file from directory if it exists
      Sets the functions that makes up run() to the default methods listed at the
      end of the code.
    
    <Returns>
      None
    """
    # If a stop file still exists, delete it for the user
    if os.path.isfile("./stop"):
      os.remove(os.path.expanduser("./stop"))

    # List of valid vessel types.
    vessel_types = [explib.SEATTLECLEARINGHOUSE_VESSEL_TYPE_WAN,
                    explib.SEATTLECLEARINGHOUSE_VESSEL_TYPE_LAN,
                    explib.SEATTLECLEARINGHOUSE_VESSEL_TYPE_NAT,
                    explib.SEATTLECLEARINGHOUSE_VESSEL_TYPE_RAND]
  
    if vessel_type not in vessel_types:
      raise ValueError("Invalid vessel type specified. Argument 'vessel_type' must be one of " +
                        "the SEATTLECLEARINGHOUSE_VESSEL_TYPE_* constants defined in 'experimentlib.py'")
    
    self.config['vessel_type'] = vessel_type


    # If a program file isn't passed, assume user will handle the issue
    if program_filename:
      # Verify that program file exists
      if not os.path.isfile(program_filename):
        raise ValueError("Specified program file '" + program_filename + "' does not exist")
    
      self.config['program_filename'] = program_filename


    # Setup explib identity object and GENI details
    self.config['identity'] = explib.create_identity_from_key_files(geni_username + '.publickey',
                                                             geni_username + '.privatekey')
    self.config['geni_port'] = explib.seattlegeni_user_port(self.config['identity'])


    # Ensure that the user has enough credits to acquire the specified number of vessels.
    num_vessel_credits = explib.seattlegeni_max_vessels_allowed(self.config['identity'])
  
    if vessel_count > num_vessel_credits:
      raise ValueError("Invalid number of vessels specified. The number of deployed vessels must " +
                      "be less than or equal to the user's number of vessel credits.")
                      
    self.config['vessel_count'] = vessel_count


    # Set up the logger according to passed arguments
    if log_filename:
      # Add the file logger.
      fileLog = logging.FileHandler(log_filename, 'w')
      fileLog.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S'))
      self.logger.addHandler(fileLog)
    else:
      # Add the console logger.
      consoleLog = logging.StreamHandler()
      consoleLog.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%H:%M:%S'))
      self.logger.addHandler(consoleLog)
      

    # Setting the functions of 'run' to default
    self.init_overlord_func = default_init_overlord
    self.acquire_vessels_func = default_acquire_vessels
    self.init_vessels_func = default_initiate_vessels
    self.remove_vessels_func = default_remove_vessels
    self.maintenance_func = default_maintenance




  def run(self, *args):
    """
    <Purpose>
      Starts the deployment and monitoring of a service on a number of vessels.
      Handles all acquisition of, uploading to, starting, and release of vessels.
      Contains the main loop of this program, and is thus the final function to
      call in all client programs. 
    <Arguments>
      *args: 
        Optional arguments that well be passed when starting the uploaded
        program file, by default

    <Exceptions>
      Common SeattleGENI exceptions described in the module comments.

    <Side Effects>
      Unless overridden beforehand, persistently logs to overlord_instance.log and
      console
      Returns if a 'stop' file is found in directory of the program importing the API

    <Returns>
      None
    """
    # Log setup information for user reference.
    self.logger.info("Performing actions as GENI user '" + self.config['identity']['username'] + "'")
    self.logger.info('Vessel status will be polled every ' + str(self.VESSEL_POLLING_PERIOD) + ' seconds')
    self.logger.info('Vessels will be renewed every ' + str(self.VESSEL_RENEWAL_PERIOD) + ' seconds')

  

    # Run the start-up function for overlord
    self.init_overlord_func(self)
  
    # Retrieve the current list of vessel handles owned by identity, regardless
    # of the results of overlord's start-up function
    vessel_handlers = explib.seattlegeni_get_acquired_vessels(self.config['identity'])

    # If there are still vessels allocated to the identity, renew them to keep
    # renewal periods consistent with newly acquired vessels later on
    if vessel_handlers:
      self.logger.info('Renewing ' + str(len(vessel_handlers)) + ' vessels')
      explib.seattlegeni_renew_vessels(self.config['identity'], vessel_handlers)

    # Turn VESSEL_RENEWAL_PERIOD into a timedelta object.
    renewal_delay = timedelta(seconds=self.VESSEL_RENEWAL_PERIOD)
  
    # Assume that the vessels have been renewed.
    last_renewal = datetime.utcnow()

  
    # Main loop
    while True:

      # End operations if "stop" file is found in same directory as overlord.py
      if os.path.isfile("./stop"):
        self.logger.info("Stop file found; Discontinuing operations.")
        return

      # Call the acquire vessels function and set the list of the handles of the
      # newly acquired vessels
      fresh_handlers = self.acquire_vessels_func(self, vessel_handlers)

      # If the list is not empty, call the initiate vessel function, and an updated
      # list of currently owned vessel handles that includes the newly acquired ones
      # should be returned
      if fresh_handlers:
        vessel_handlers = self.init_vessels_func(self, fresh_handlers, vessel_handlers, *args)

      # Weed out any vessels based on the remove vessels function
      vessel_handlers = self.remove_vessels_func(self, vessel_handlers)

      # Perform any maintenance on the vessels, including renewals if needed,
      # and return the relevant information needed for next maintenance.
      # Currently coded to fit with default behavior, but should somehow be made a
      # little more flexible for user's function overrides?
      last_renewal = self.maintenance_func(self, renewal_delay, last_renewal, vessel_handlers)

      # If the list of running vessels does not match the requested vessel count,
      # repeat the loop until it does
      if not len(vessel_handlers) == self.config['vessel_count']:
        continue
      

      # Sleep between polling vessel statuses.
      time.sleep(self.VESSEL_POLLING_PERIOD)
    
    


# HELPER FUNCTIONS

  def acquire_vessels(self,vessel_count):  
    """
    <Purpose>
      Acquire an argument number of vessels via SeattleGENI. Vessel type is
      obtained from the config dictionary. This function is a wrapper around the
      Experiment Library function seattlegeni_acquire_vessels, with logging
      support.

    <Arguments>
      number
        The number of vessels to acquire.

    <Exceptions>
      None

    <Side Effects>
      Renews the vessels upon acquisition to extend expiration time
    
    <Returns>
      A list of vesselhandles of freshly-acquired vessels. On failure, returns an
      empty list.
    """
    self.logger.info('Acquiring ' + str(vessel_count) + ' vessels')

    try:
      vessel_handlers = explib.seattlegeni_acquire_vessels(self.config['identity'], self.config['vessel_type'], vessel_count)
    
    except explib.SeattleClearinghouseError, e:
      self.logger.error('Error while acquiring vessels: ' + str(e))
      return []
    
    else:
      self.logger.debug('Successfully acquired ' + str(vessel_count) + ' vessels')

    # Renew vessels to extend their expiration time.
    self.logger.debug('Renewing ' + str(len(vessel_handlers)) + ' newly acquired vessels')
    explib.seattlegeni_renew_vessels(self.config['identity'], vessel_handlers)
  
    return vessel_handlers





  def upload_to_vessels(self, vessel_handlers, filename_list):
    """
    <Purpose>
      Uploads a list of file to a set of vessels. A batch wrapper around the Experiment
      Library function upload_file_to_vessel, with logging and parallelization support.

    <Arguments>
      vesselhandle_list
        A list of vesselhandles of vessels to which the file is to be uploaded.
      filename
        The filename of the file to be uploaded.

    <Exceptions>
      None

    <Side Effects>
      None
    
    <Returns>
      A list of vessels to which the upload succeeded.
    """
    self.logger.info("Uploading '" + str(filename_list) + "' to " + str(len(vessel_handlers)) + " vessels")
  
    # Clear the list of successful_handlers for a new operation
    self.successful_handlers = []
  
    explib.run_parallelized(vessel_handlers, self._upload_to_vessels_helper, filename_list)

    return self.successful_handlers
    

  # Helper function to upload_to_vessels in order to make use of Experiment
  # Library's run_parallelized()
  def _upload_to_vessels_helper(self, vessel, filename_list):
    for filename in filename_list:  
      try:
        explib.upload_file_to_vessel(vessel, self.config['identity'], filename)
      
      except explib.NodeCommunicationError:
        self.logger.error("Failed to upload '" + filename + "' to vessel " + self.vessel_location(vessel))
      
      else:
        self.logger.debug("Successfully uploaded '" + filename + "' to vessel " + self.vessel_location(vessel))
        self.successful_handlers.append(vessel)
  



  def run_on_vessels(self, vessel_handlers, filename, *vessel_args):
    """
    <Purpose>
      Runs a program on a set of vessels. A batch wrapper around the Experiment
      Library function run_parallelized, with logging and parallelization support.

    <Arguments>
      vesselhandle_list
        A list of vesselhandles of vessels to which a file is to be uploaded.
      filename
        The filename of the program to run.
      *vessel_args
        Optional additional arguments required by the program to be run on
        vessels.

    <Exceptions>
      None

    <Side Effects>
      Logger will make an entry for each successful and failed start-ups
      Process is parallelized

    <Returns>
      A list of vesselhandles of vessels that started the program successfully
    """
    self.logger.info("Starting '" + filename + "' on " + str(len(vessel_handlers)) + " vessels")

    # Clear the list of successful_handlers for a new operation
    self.successful_handlers = []

    explib.run_parallelized(vessel_handlers, self._run_on_vessels, filename, *vessel_args)

    return self.successful_handlers



  # Helper function to upload_to_vessels in order to make use of Experiment
  # Library's run_parallelized()
  def _run_on_vessels(self, vessel, filename, *vessel_args):
    try:
      vessel_args = [str(arg) for arg in list(vessel_args)]
      explib.start_vessel(vessel, self.config['identity'], filename, vessel_args)
      
    except explib.SeattleExperimentError:
      self.logger.error("Failed to start '" + filename + "' on vessel " + self.vessel_location(vessel))
      
    else:
      self.logger.debug("Successfully started '" + filename + "' on vessel " + self.vessel_location(vessel))
      self.successful_handlers.append(vessel)
      





  def release_vessels(self, vessel_handlers):
    """
    <Purpose>
      Releases a set of vessels. A batch wrapper around the Experiment Library
      function run_parallelized, with logging support. Logs log_string as the
      reason for releasing vessels.

    <Arguments>
      vessel_handlers:
        List of vesselhandles of vessels to be released

    <Exceptions>
      None

    <Side Effects>
      None

    <Returns>
      None.
    """
    if len(vessel_handlers) == 0:
      return
  
    try:
      explib.seattlegeni_release_vessels(self.config['identity'], vessel_handlers)
    except explib.SeattleClearinghouseError, e:
      self.logger.error('Error while releasing vessels: ' + str(e))





  def list_difference(self, list1, list2):
    """
    Returns the difference (set operation) of list1 - list2.
    """
    return list(set(list1) - set(list2))





  def vessel_location(self, vessel_handler):
    """
    <Purpose>
      Determine the node location of the given vessel handle

    <Arguments>
      vessel_handler:
        The vesselhandle of the vessel whose location information
        is needed

    <Exceptions>
      None

    <Side Effects>
      None
    
    <Returns>
      A nodelocation
    """
    node_id = explib.get_nodeid_and_vesselname(vessel_handler)[0]
    return explib.get_node_location(node_id)
  
    





###########################
## DEFAULT RUN FUNCTIONS ##
###########################

# DEFAULT OVERLORD START-UP 
def default_init_overlord(overlord):
  # Release any pre-allocated vessels
  vessel_handlers = explib.seattlegeni_get_acquired_vessels(overlord.config['identity'])
  
  overlord.logger.info('Releasing ' + str(len(vessel_handlers)) + ' pre-allocated vessels')
  overlord.release_vessels(vessel_handlers)




# DEFAULT ACQUIRE VESSELS
def default_acquire_vessels(overlord, vessel_handlers):
  # Process of acquiring vessels should be the same in each overlord instance
  overlord.logger.debug('Checking for unused vessels')
  
  # Calculate how many additional vessels we are allowed to acquire.
  unused_vessel_count = overlord.config['vessel_count'] - len(vessel_handlers)
  
  fresh_handlers = []

  # Acquire more vessels if we are allowed.
  if unused_vessel_count > 0:      
    fresh_handlers = overlord.acquire_vessels(unused_vessel_count)
    
  return fresh_handlers



# DEFAULT INITIATE VESSEL
def default_initiate_vessels(overlord, fresh_handlers, vessel_handlers, *args):

  successful_handlers = overlord.upload_to_vessels(fresh_handlers, [overlord.config['program_filename']])
  successful_handlers = overlord.run_on_vessels(successful_handlers, overlord.config['program_filename'], *args)
      
      
  # Identify and release any failed vessels.
  failed_handlers = overlord.list_difference(fresh_handlers, successful_handlers)
      
  if len(failed_handlers) > 0:
    overlord.logger.info("Releasing " + str(len(failed_handlers)) + " vessels because '" +
                      overlord.config['program_filename'] + "' failed to upload or run")
                   
    for vessel in failed_handlers:
      try:
        vessel_log = explib.get_vessel_log(vessel, overlord.config['identity'])
            
        if vessel_log == '':
          vessel_log = '[empty vessel log]'
      except:
        vessel_log = '[no vessel log available]'
        
      overlord.logger.error('Vessel ' + overlord.vessel_location(vessel) + ' failed: ' + vessel_log)
      
      
    # Release all the failed vessels.
    overlord.release_vessels(failed_handlers)  
        
  # Merge the fresh vessels into the overall list.
  vessel_handlers.extend(successful_handlers)

  return vessel_handlers




# DEFAULT REMOVE STOPPED VESSELS
def default_remove_vessels(overlord, vessel_handlers):
  overlord.logger.debug('Checking for stopped vessels')

  # Remove any stopped vessels.
  stopped_vessels = []
  
  for vessel in vessel_handlers:
    try:
      vessel_status = explib.get_vessel_status(vessel, overlord.config['identity'])
    except:
      stopped_vessels.append(vessel)
    else:
      if vessel_status != explib.VESSEL_STATUS_STARTED:
        stopped_vessels.append(vessel)

  if len(stopped_vessels) > 0:
    overlord.logger.info('Releasing ' + str(len(stopped_vessels)) + ' stopped vessels')
    overlord.release_vessels(stopped_vessels)

    # Remove released vessels from the list.
    vessel_handlers = overlord.list_difference(vessel_handlers, stopped_vessels)

  # Log the current number of running vessels.
  overlord.logger.info('Currently have ' + str(len(vessel_handlers)) + ' running vessels')

  return vessel_handlers




# DEFAULT MAINTENANCE
def default_maintenance(overlord, renewal_delay, last_renewal, vessel_handlers):
  # Renew vessels periodically.
  time_elapsed = datetime.utcnow() - last_renewal
  
  if time_elapsed > renewal_delay:
    # Perform the vessel renewal.
    overlord.logger.info('Renewing ' + str(len(vessel_handlers)) + ' vessels')
    explib.seattlegeni_renew_vessels(overlord.config['identity'], vessel_handlers)
      
    # Reset the time.
    last_renewal = datetime.utcnow()
    
    
  return last_renewal
