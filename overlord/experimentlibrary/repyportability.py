
# I'm importing these so I can neuter the calls so that they aren't 
# restricted...
import nanny
import restrictions
import emulfile


# JAC: Save the calls in case I want to restore them.   This is useful if 
# repy ends up wanting to use either repyportability or repyhelper...
# This is also useful if a user wants to enforce restrictions on the repy
# code they import via repyhelper (they must use 
# restrictions.init_restriction_tables(filename) as well)...
oldrestrictioncalls = {}
oldrestrictioncalls['nanny.tattle_quantity'] = nanny.tattle_quantity
oldrestrictioncalls['nanny.tattle_add_item'] = nanny.tattle_add_item
oldrestrictioncalls['nanny.tattle_remove_item'] = nanny.tattle_remove_item
oldrestrictioncalls['nanny.tattle_check'] = nanny.tattle_check
oldrestrictioncalls['restrictions.assertisallowed'] = restrictions.assertisallowed
oldrestrictioncalls['emulfile._assert_is_allowed_filename'] = emulfile._assert_is_allowed_filename


def _do_nothing(*args):
  pass

# Overwrite the calls so that I don't have restrictions (the default)
def override_restrictions():
  """
   <Purpose>
      Turns off restrictions.   Resource use will be unmetered after making
      this call.   (note that CPU / memory / disk space will never be metered
      by repyhelper or repyportability)

   <Arguments>
      None.
         
   <Exceptions>
      None.

   <Side Effects>
      Resource use is unmetered / calls are unrestricted.

   <Returns>
      None
  """
  nanny.tattle_quantity = _do_nothing
  nanny.tattle_add_item = _do_nothing
  nanny.tattle_remove_item = _do_nothing
  nanny.tattle_check = _do_nothing
  restrictions.assertisallowed = _do_nothing
  emulfile._assert_is_allowed_filename = _do_nothing


# Sets up restrictions for the program
# THIS IS ONLY METERED FOR REPY CALLS AND DOES NOT INCLUDE CPU / MEM / DISK 
# SPACE
def initialize_restrictions(restrictionsfn):
  """
   <Purpose>
      Sets up restrictions.   This allows some resources to be metered 
      despite the use of repyportability / repyhelper.   CPU / memory / disk 
      space will not be metered.   Call restrictions will also be enabled.

   <Arguments>
      restrictionsfn:
        The file name of the restrictions file.
         
   <Exceptions>
      None.

   <Side Effects>
      Enables restrictions.

   <Returns>
      None
  """
  restrictions.init_restriction_tables(restrictionsfn)
  nanny.initialize_consumed_resource_tables()
  enable_restrictions()

def enable_restrictions():
  """
   <Purpose>
      Turns on restrictions.   There must have previously been a call to
      initialize_restrictions().  CPU / memory / disk space will not be 
      metered.   Call restrictions will also be enabled.

   <Arguments>
      None.
         
   <Exceptions>
      None.

   <Side Effects>
      Enables call restrictions / resource metering.

   <Returns>
      None
  """
  # JAC: THIS WILL NOT ENABLE CPU / MEMORY / DISK SPACE
  nanny.tattle_quantity = oldrestrictioncalls['nanny.tattle_quantity']
  nanny.tattle_add_item = oldrestrictioncalls['nanny.tattle_add_item'] 
  nanny.tattle_remove_item = oldrestrictioncalls['nanny.tattle_remove_item'] 
  nanny.tattle_check = oldrestrictioncalls['nanny.tattle_check'] 
  restrictions.assertisallowed = oldrestrictioncalls['restrictions.assertisallowed'] 
  emulfile._assert_is_allowed_filename = oldrestrictioncalls['emulfile._assert_is_allowed_filename']
  
from virtual_namespace import VirtualNamespace
from emulmisc import *
from emulcomm import *
from emulfile import *
from emultimer import *

# This is needed because otherwise we're using the old versions of file and
# open.   We should change the names of these functions when we design
# repy 0.2
originalopen = open
originalfile = file
open = emulated_open
file = emulated_open

# Override by default!
override_restrictions()
