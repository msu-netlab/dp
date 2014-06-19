"""
<Program>
  repyimporter

<Date Started>
  Dec 11, 2009

<Author>
  Justin Samuel

<Purpose>
  A module to allow importing repy modules without cluttering the calling
  code's namespace. The issue is that when using repy code in regular
  python programming environments, lots of stuff gets imported into the
  global scope both by the import as well as by repyportability.
"""

from repyportability import *
import repyhelper

def import_repy_module(repy_module_name):
  """
  <Arguments>
    repy_module_name
      The name of the repy file without the ".repy" on the end.
  """
  return __import__(repyhelper.translate(repy_module_name + ".repy"))
